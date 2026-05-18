from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import socket
import struct
import time


WSJTX_MAGIC = bytes.fromhex("ad bc cb da")
MODE_CANDIDATES = ("FT4", "FT8", "FST4", "FST4W")
INTERESTING_PORTS = (2237, 4532, 5957)


@dataclass(slots=True)
class UdpPacketEvent:
    timestamp_ms: int
    src_host: str
    src_port: int
    dst_host: str
    dst_port: int
    payload: bytes


@dataclass(slots=True)
class ReplayPacket:
    timestamp_offset_ms: int
    dst_port: int
    payload_hex: str
    payload_len: int
    tag: str
    source_capture: str
    mode: str


@dataclass(slots=True)
class ReplaySequence:
    source_capture: str
    mode: str
    destination_host: str
    destination_port: int
    packets: list[ReplayPacket]


def parse_pcapng_udp_events(path: str | Path) -> list[UdpPacketEvent]:
    raw = Path(path).read_bytes()
    offset = 0
    interfaces: list[int] = []
    events: list[UdpPacketEvent] = []

    while offset + 12 <= len(raw):
        block_type, block_len = struct.unpack_from("<II", raw, offset)
        if block_len < 12 or offset + block_len > len(raw):
            break
        body = raw[offset + 8 : offset + block_len - 4]

        if block_type == 0x00000001 and len(body) >= 8:  # IDB
            linktype, _reserved, _snaplen = struct.unpack_from("<HHi", body, 0)
            interfaces.append(linktype)
        elif block_type == 0x00000006 and len(body) >= 20:  # EPB
            iface_id, ts_high, ts_low, cap_len, _orig_len = struct.unpack_from("<IIIII", body, 0)
            if iface_id >= len(interfaces):
                offset += block_len
                continue
            packet = body[20 : 20 + cap_len]
            timestamp_ms = int((((ts_high << 32) | ts_low) / 1000))
            event = _decode_udp_packet(interfaces[iface_id], packet, timestamp_ms)
            if event is not None:
                events.append(event)

        offset += block_len

    return events


def analyze_udp_capture(path: str | Path) -> dict[str, object]:
    capture_path = Path(path)
    events = parse_pcapng_udp_events(capture_path)
    interesting_events = [event for event in events if event.dst_port in INTERESTING_PORTS]

    by_dest = Counter(event.dst_port for event in interesting_events)
    wsjtx_events = [event for event in interesting_events if event.dst_port == 2237]
    hamlib_events = [event for event in interesting_events if event.dst_port == 4532]
    digimanager_events = [event for event in interesting_events if event.dst_port == 5957]

    wsjtx_message_types = Counter()
    wsjtx_mode_string_counts = Counter()
    for event in wsjtx_events:
        message_type = _parse_wsjtx_message_type(event.payload)
        if message_type is not None:
            wsjtx_message_types[str(message_type)] += 1
        for mode_string in _find_mode_strings(event.payload):
            wsjtx_mode_string_counts[mode_string] += 1

    payload_len_distribution = Counter(len(event.payload) for event in digimanager_events)
    prefix_counts = Counter(_payload_prefix(event.payload) for event in digimanager_events)
    tag_counts = Counter(_classify_5957_tag(event.payload) for event in digimanager_events)

    hamlib_json_count = sum(1 for event in hamlib_events if event.payload.startswith(b'{"app":"Hamlib"'))
    summary = {
        "source_capture": capture_path.name,
        "interesting_ports": list(INTERESTING_PORTS),
        "total_udp_events": len(events),
        "interesting_port_counts": {str(port): by_dest.get(port, 0) for port in INTERESTING_PORTS},
        "wsjtx_2237": {
            "count": len(wsjtx_events),
            "message_types": dict(wsjtx_message_types),
            "mode_strings": dict(wsjtx_mode_string_counts),
            "timeline": [_render_timeline_event(event) for event in wsjtx_events[:12]],
        },
        "hamlib_4532": {
            "count": len(hamlib_events),
            "hamlib_json_count": hamlib_json_count,
            "looks_like_hamlib_broadcast": bool(hamlib_json_count),
            "timeline": [_render_timeline_event(event) for event in hamlib_events[:8]],
        },
        "digimanager_5957": {
            "count": len(digimanager_events),
            "payload_len_distribution": {str(length): count for length, count in payload_len_distribution.items()},
            "prefix_counts": dict(prefix_counts),
            "tag_counts": dict(tag_counts),
            "timeline": [_render_timeline_event(event, include_tag=True) for event in digimanager_events[:16]],
        },
        "conclusions": {
            "ft4_reaches_5957": prefix_counts.get("59 57 04 00", 0) > 0,
            "ft8_reaches_5957": prefix_counts.get("59 57 08 00", 0) > 0,
            "shared_5957_business_packets_present": prefix_counts.get("59 57 f4 00", 0) > 0,
            "port_4532_looks_like_hamlib_broadcast": bool(hamlib_json_count),
        },
    }
    return summary


def compare_udp_capture_analyses(analyses: list[dict[str, object]]) -> dict[str, object]:
    comparison: dict[str, object] = {
        "captures": [analysis["source_capture"] for analysis in analyses],
        "shared_5957_prefixes": [],
        "unique_5957_prefixes": {},
    }
    if len(analyses) < 2:
        return comparison

    prefix_sets = []
    for analysis in analyses:
        digimanager = analysis["digimanager_5957"]  # type: ignore[index]
        prefixes = set(digimanager["prefix_counts"].keys())  # type: ignore[index]
        prefix_sets.append(prefixes)

    shared = set.intersection(*prefix_sets) if prefix_sets else set()
    comparison["shared_5957_prefixes"] = sorted(shared)

    unique: dict[str, list[str]] = {}
    for analysis, prefixes in zip(analyses, prefix_sets):
        others = set().union(*(candidate for candidate in prefix_sets if candidate is not prefixes))
        unique[str(analysis["source_capture"])] = sorted(prefixes - others)
    comparison["unique_5957_prefixes"] = unique
    return comparison


def render_udp_capture_analysis_text(analysis: dict[str, object]) -> str:
    wsjtx = analysis["wsjtx_2237"]  # type: ignore[index]
    hamlib = analysis["hamlib_4532"]  # type: ignore[index]
    digimanager = analysis["digimanager_5957"]  # type: ignore[index]
    conclusions = analysis["conclusions"]  # type: ignore[index]
    lines = [
        f"capture: {analysis['source_capture']}",
        f"total_udp_events: {analysis['total_udp_events']}",
        f"interesting_port_counts: {analysis['interesting_port_counts']}",
        "2237 / WSJT-X:",
        f"- count: {wsjtx['count']}",
        f"- message_types: {wsjtx['message_types']}",
        f"- mode_strings: {wsjtx['mode_strings']}",
        "5957 / DigiManager:",
        f"- count: {digimanager['count']}",
        f"- payload_len_distribution: {digimanager['payload_len_distribution']}",
        f"- prefix_counts: {digimanager['prefix_counts']}",
        f"- tag_counts: {digimanager['tag_counts']}",
        "4532 / Hamlib:",
        f"- count: {hamlib['count']}",
        f"- hamlib_json_count: {hamlib['hamlib_json_count']}",
        "conclusions:",
        f"- ft4_reaches_5957: {conclusions['ft4_reaches_5957']}",
        f"- ft8_reaches_5957: {conclusions['ft8_reaches_5957']}",
        f"- shared_5957_business_packets_present: {conclusions['shared_5957_business_packets_present']}",
        f"- port_4532_looks_like_hamlib_broadcast: {conclusions['port_4532_looks_like_hamlib_broadcast']}",
    ]
    return "\n".join(lines)


def render_udp_capture_comparison_text(comparison: dict[str, object]) -> str:
    lines = [
        f"comparison_captures: {comparison['captures']}",
        f"shared_5957_prefixes: {comparison['shared_5957_prefixes']}",
        "unique_5957_prefixes:",
    ]
    for capture_name, prefixes in comparison["unique_5957_prefixes"].items():  # type: ignore[union-attr]
        lines.append(f"- {capture_name}: {prefixes}")
    return "\n".join(lines)


def export_udp_replay_sequence(
    input_path: str | Path,
    *,
    mode: str,
    output_path: str | Path,
) -> ReplaySequence:
    capture_path = Path(input_path)
    mode_label = mode.upper()
    events = [event for event in parse_pcapng_udp_events(capture_path) if event.dst_port == 5957]
    if not events:
        raise ValueError(f"No UDP packets to port 5957 found in {capture_path}")

    base_timestamp = events[0].timestamp_ms
    packets = [
        ReplayPacket(
            timestamp_offset_ms=event.timestamp_ms - base_timestamp,
            dst_port=event.dst_port,
            payload_hex=event.payload.hex(" "),
            payload_len=len(event.payload),
            tag=_classify_5957_tag(event.payload),
            source_capture=capture_path.name,
            mode=mode_label,
        )
        for event in events
    ]
    sequence = ReplaySequence(
        source_capture=capture_path.name,
        mode=mode_label,
        destination_host="127.0.0.1",
        destination_port=5957,
        packets=packets,
    )
    Path(output_path).write_text(json.dumps(_replay_sequence_to_dict(sequence), indent=2, ensure_ascii=False), encoding="utf-8")
    return sequence


def load_udp_replay_sequence(path: str | Path) -> ReplaySequence:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    packets = [
        ReplayPacket(
            timestamp_offset_ms=int(item["timestamp_offset_ms"]),
            dst_port=int(item["dst_port"]),
            payload_hex=str(item["payload_hex"]),
            payload_len=int(item["payload_len"]),
            tag=str(item["tag"]),
            source_capture=str(item["source_capture"]),
            mode=str(item["mode"]),
        )
        for item in payload["packets"]
    ]
    return ReplaySequence(
        source_capture=str(payload["source_capture"]),
        mode=str(payload["mode"]),
        destination_host=str(payload.get("destination_host", "127.0.0.1")),
        destination_port=int(payload.get("destination_port", 5957)),
        packets=packets,
    )


def render_replay_dry_run(sequence: ReplaySequence, packets: list[ReplayPacket]) -> str:
    lines = [
        f"source_capture: {sequence.source_capture}",
        f"mode: {sequence.mode}",
        f"destination: {sequence.destination_host}:{sequence.destination_port}",
        f"packets: {len(packets)}",
    ]
    for index, packet in enumerate(packets):
        lines.append(
            f"- index={index} offset_ms={packet.timestamp_offset_ms} "
            f"dst_port={packet.dst_port} len={packet.payload_len} tag={packet.tag} "
            f"prefix={packet.payload_hex[:11]}"
        )
    return "\n".join(lines)


def replay_udp_sequence(
    sequence: ReplaySequence,
    *,
    timing_mode: str = "original_timing",
    dry_run: bool = False,
    single_packet_index: int | None = None,
    single_packet_tag: str | None = None,
    destination_host_override: str | None = None,
    destination_port_override: int | None = None,
) -> list[ReplayPacket]:
    packets = list(sequence.packets)
    if single_packet_index is not None:
        packets = [packets[single_packet_index]]
    elif single_packet_tag is not None:
        matching = [packet for packet in packets if packet.tag == single_packet_tag]
        if not matching:
            raise ValueError(f"No packet with tag {single_packet_tag!r}")
        packets = [matching[0]]

    if dry_run or not packets:
        return packets

    destination_host = destination_host_override or sequence.destination_host
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        previous_offset = 0
        for packet in packets:
            if timing_mode == "original_timing":
                delay_ms = max(0, packet.timestamp_offset_ms - previous_offset)
                if delay_ms:
                    time.sleep(delay_ms / 1000.0)
                previous_offset = packet.timestamp_offset_ms
            payload = bytes.fromhex(packet.payload_hex)
            destination_port = destination_port_override or packet.dst_port
            udp_socket.sendto(payload, (destination_host, destination_port))
    return packets


def build_analyze_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze WSJT-X / DigiManager UDP packets from one or more pcapng files.")
    parser.add_argument("pcapng", nargs="+", help="One or more pcapng files to analyze.")
    return parser


def build_export_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export 5957 UDP packets from a pcapng file into a replay JSON sequence.")
    parser.add_argument("--input", required=True, help="Path to the source pcapng file.")
    parser.add_argument("--mode", required=True, choices=["FT4", "FT8"], help="Mode label for the exported sequence.")
    parser.add_argument("--output", required=True, help="Where to write the replay JSON file.")
    return parser


def build_replay_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay an exported UDP packet sequence toward DigiManager on localhost.")
    parser.add_argument("--input", required=True, help="Path to the exported replay JSON file.")
    parser.add_argument(
        "--timing",
        choices=["original_timing", "fast_replay"],
        default="original_timing",
        help="How to schedule packets during replay.",
    )
    parser.add_argument("--fast-replay", action="store_true", help="Alias for --timing fast_replay.")
    parser.add_argument("--dry-run", action="store_true", help="Print the packet sequence without sending it.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--single-packet-index", type=int, help="Replay only one packet by zero-based index.")
    group.add_argument("--single-packet-tag", help="Replay only the first packet with the given tag.")
    return parser


def analyze_main(argv: list[str] | None = None) -> int:
    parser = build_analyze_parser()
    args = parser.parse_args(argv)
    analyses = [analyze_udp_capture(path) for path in args.pcapng]
    for analysis in analyses:
        print(render_udp_capture_analysis_text(analysis))
        print()
    if len(analyses) > 1:
        comparison = compare_udp_capture_analyses(analyses)
        print(render_udp_capture_comparison_text(comparison))
    return 0


def export_main(argv: list[str] | None = None) -> int:
    parser = build_export_parser()
    args = parser.parse_args(argv)
    sequence = export_udp_replay_sequence(args.input, mode=args.mode, output_path=args.output)
    print(f"exported_packets: {len(sequence.packets)}")
    print(f"output: {args.output}")
    return 0


def replay_main(argv: list[str] | None = None) -> int:
    parser = build_replay_parser()
    args = parser.parse_args(argv)
    sequence = load_udp_replay_sequence(args.input)
    timing_mode = "fast_replay" if args.fast_replay else args.timing
    packets = replay_udp_sequence(
        sequence,
        timing_mode=timing_mode,
        dry_run=args.dry_run,
        single_packet_index=args.single_packet_index,
        single_packet_tag=args.single_packet_tag,
    )
    if args.dry_run:
        print(render_replay_dry_run(sequence, packets))
    else:
        print(f"replayed_packets: {len(packets)}")
        print(f"destination: {sequence.destination_host}:{sequence.destination_port}")
    return 0


def _decode_udp_packet(linktype: int, packet: bytes, timestamp_ms: int) -> UdpPacketEvent | None:
    ip_packet: bytes | None
    if linktype == 0:
        if len(packet) < 4:
            return None
        ip_packet = packet[4:]
    elif linktype == 1:
        if len(packet) < 14:
            return None
        ether_type = struct.unpack_from("!H", packet, 12)[0]
        if ether_type != 0x0800:
            return None
        ip_packet = packet[14:]
    else:
        return None

    if len(ip_packet) < 20:
        return None
    version = ip_packet[0] >> 4
    if version != 4:
        return None
    protocol = ip_packet[9]
    if protocol != 17:
        return None
    header_len = (ip_packet[0] & 0x0F) * 4
    if len(ip_packet) < header_len + 8:
        return None

    src_host = ".".join(str(value) for value in ip_packet[12:16])
    dst_host = ".".join(str(value) for value in ip_packet[16:20])
    src_port, dst_port, udp_len, _checksum = struct.unpack_from("!HHHH", ip_packet, header_len)
    payload = ip_packet[header_len + 8 : header_len + udp_len]
    return UdpPacketEvent(
        timestamp_ms=timestamp_ms,
        src_host=src_host,
        src_port=src_port,
        dst_host=dst_host,
        dst_port=dst_port,
        payload=payload,
    )


def _parse_wsjtx_message_type(payload: bytes) -> int | None:
    if len(payload) < 12 or not payload.startswith(WSJTX_MAGIC):
        return None
    return struct.unpack_from("!I", payload, 8)[0]


def _find_mode_strings(payload: bytes) -> list[str]:
    return [candidate for candidate in MODE_CANDIDATES if candidate.encode("ascii") in payload]


def _payload_prefix(payload: bytes) -> str:
    if not payload:
        return "<empty>"
    return payload[:4].hex(" ")


def _classify_5957_tag(payload: bytes) -> str:
    if payload.startswith(bytes.fromhex("59 57 04 00")):
        return "ft4_mode_marker"
    if payload.startswith(bytes.fromhex("59 57 08 00")):
        return "ft8_mode_marker"
    if payload.startswith(bytes.fromhex("59 57 f4 00")):
        return "business_packet"
    return "unknown_5957_packet"


def _render_timeline_event(event: UdpPacketEvent, *, include_tag: bool = False) -> dict[str, object]:
    rendered = {
        "timestamp_ms": event.timestamp_ms,
        "src_port": event.src_port,
        "dst_port": event.dst_port,
        "payload_len": len(event.payload),
        "payload_prefix": _payload_prefix(event.payload),
    }
    if include_tag:
        rendered["tag"] = _classify_5957_tag(event.payload)
    return rendered


def _replay_sequence_to_dict(sequence: ReplaySequence) -> dict[str, object]:
    return {
        "source_capture": sequence.source_capture,
        "mode": sequence.mode,
        "destination_host": sequence.destination_host,
        "destination_port": sequence.destination_port,
        "packets": [asdict(packet) for packet in sequence.packets],
    }
