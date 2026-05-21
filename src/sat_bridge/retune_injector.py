from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Any

from sat_bridge.udp_capture_tools import (
    ReplayPacket,
    ReplaySequence,
    load_udp_replay_sequence,
    render_replay_dry_run,
    replay_udp_sequence,
)


FREQUENCY_FIELD_OFFSET = -12
FREQUENCY_FIELD_SIZE = 4
PLAUSIBLE_FREQUENCY_MIN_HZ = 100_000_000
PLAUSIBLE_FREQUENCY_MAX_HZ = 500_000_000
DEFAULT_REPLAY_JSON = Path("samples/replay/ft8-replay.json")
DEFAULT_ACTIONS_PATH = Path("reverse/input/dynamic/actions.json")


@dataclass(slots=True)
class RetuneEvent:
    requested_at_ms: int
    frequency_hz: int


@dataclass(slots=True)
class AppliedRetuneEvent:
    requested_at_ms: int
    applied_at_ms: int
    frequency_hz: int
    packet_index: int


def parse_retune_events(text: str) -> list[RetuneEvent]:
    events: list[RetuneEvent] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        try:
            when_text, freq_text = item.split(":", 1)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(
                "Retune events must use the format '<offset_ms>:<frequency_hz>,...'"
            ) from exc
        events.append(
            RetuneEvent(
                requested_at_ms=int(when_text.strip()),
                frequency_hz=int(freq_text.strip()),
            )
        )
    if not events:
        raise ValueError("At least one retune event is required.")
    events.sort(key=lambda item: item.requested_at_ms)
    return events


def filter_sequence_for_profile(sequence: ReplaySequence, profile: str) -> ReplaySequence:
    if profile == "tx":
        return sequence
    packets = [packet for packet in sequence.packets if packet.tag == "business_packet"]
    return replace(sequence, packets=packets)


def normalize_sequence_timestamps(sequence: ReplaySequence, gap_ms: int) -> ReplaySequence:
    if gap_ms <= 0:
        return sequence
    packets = [
        replace(packet, timestamp_offset_ms=index * gap_ms)
        for index, packet in enumerate(sequence.packets)
    ]
    return replace(sequence, packets=packets)


def apply_retune_schedule(
    sequence: ReplaySequence,
    events: list[RetuneEvent],
) -> tuple[ReplaySequence, list[AppliedRetuneEvent]]:
    packets: list[ReplayPacket] = []
    pending = list(events)
    current_frequency_hz: int | None = None
    applied_events: list[AppliedRetuneEvent] = []

    for packet_index, packet in enumerate(sequence.packets):
        mutable_frequency_hz = extract_embedded_frequency_hz(packet)
        if mutable_frequency_hz is None:
            packets.append(packet)
            continue

        if current_frequency_hz is None:
            current_frequency_hz = mutable_frequency_hz

        while pending and packet.timestamp_offset_ms >= pending[0].requested_at_ms:
            next_event = pending.pop(0)
            current_frequency_hz = next_event.frequency_hz
            applied_events.append(
                AppliedRetuneEvent(
                    requested_at_ms=next_event.requested_at_ms,
                    applied_at_ms=packet.timestamp_offset_ms,
                    frequency_hz=next_event.frequency_hz,
                    packet_index=packet_index,
                )
            )

        packets.append(patch_packet_frequency(packet, current_frequency_hz))

    if not packets:
        raise ValueError("The selected replay sequence contains no packets.")
    if not applied_events:
        raise ValueError("No retune events were applied. Use later offsets or a longer replay sequence.")

    for missing in pending:
        applied_events.append(
            AppliedRetuneEvent(
                requested_at_ms=missing.requested_at_ms,
                applied_at_ms=-1,
                frequency_hz=missing.frequency_hz,
                packet_index=-1,
            )
        )

    return replace(sequence, packets=packets), applied_events


def extract_embedded_frequency_hz(packet: ReplayPacket) -> int | None:
    if packet.tag != "business_packet":
        return None
    payload = bytes.fromhex(packet.payload_hex)
    if len(payload) < abs(FREQUENCY_FIELD_OFFSET) + FREQUENCY_FIELD_SIZE:
        return None
    frequency_hz = int.from_bytes(
        payload[FREQUENCY_FIELD_OFFSET : FREQUENCY_FIELD_OFFSET + FREQUENCY_FIELD_SIZE],
        "little",
    )
    if PLAUSIBLE_FREQUENCY_MIN_HZ <= frequency_hz <= PLAUSIBLE_FREQUENCY_MAX_HZ:
        return frequency_hz
    return None


def patch_packet_frequency(packet: ReplayPacket, frequency_hz: int) -> ReplayPacket:
    payload = bytearray(bytes.fromhex(packet.payload_hex))
    payload[FREQUENCY_FIELD_OFFSET : FREQUENCY_FIELD_OFFSET + FREQUENCY_FIELD_SIZE] = frequency_hz.to_bytes(4, "little")
    return replace(packet, payload_hex=payload.hex(" "), payload_len=len(payload))


def write_actions_file(
    actions_path: Path,
    *,
    capture_kind: str,
    capture_path: str,
    description: str,
    applied_events: list[AppliedRetuneEvent],
) -> Path:
    if actions_path.exists():
        payload: dict[str, Any] = json.loads(actions_path.read_text(encoding="utf-8"))
    else:
        payload = {
            "radio_observation": {
                "idle_frequency_change": "unknown",
                "tx_frequency_change": "unknown",
                "notes": "",
            }
        }

    key = f"{capture_kind}_capture"
    payload[key] = {
        "path": capture_path,
        "retune_events_ms": [event.applied_at_ms for event in applied_events if event.applied_at_ms >= 0],
        "description": description,
    }

    actions_path.parent.mkdir(parents=True, exist_ok=True)
    actions_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return actions_path


def render_retune_plan(
    sequence: ReplaySequence,
    patched_sequence: ReplaySequence,
    applied_events: list[AppliedRetuneEvent],
    *,
    profile: str,
) -> str:
    lines = [
        f"profile: {profile}",
        f"source_capture: {sequence.source_capture}",
        f"mode: {sequence.mode}",
        f"destination: {sequence.destination_host}:{sequence.destination_port}",
        f"original_packets: {len(sequence.packets)}",
        f"patched_packets: {len(patched_sequence.packets)}",
        "applied_retunes:",
    ]
    for event in applied_events:
        if event.applied_at_ms >= 0:
            lines.append(
                f"- requested_ms={event.requested_at_ms} applied_ms={event.applied_at_ms} "
                f"freq_hz={event.frequency_hz} packet_index={event.packet_index}"
            )
        else:
            lines.append(
                f"- requested_ms={event.requested_at_ms} applied_ms=not_applied "
                f"freq_hz={event.frequency_hz}"
            )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inject retune events into a DigiManager replay sequence so you can test digital-mode lock behavior without separate retune software."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_REPLAY_JSON),
        help="Replay JSON to use as the base traffic. Defaults to samples/replay/ft8-replay.json.",
    )
    parser.add_argument(
        "--profile",
        choices=["idle", "tx"],
        default="tx",
        help="Use 'idle' to send only business packets, or 'tx' to replay the full sequence.",
    )
    parser.add_argument(
        "--retune-events",
        required=True,
        help="Comma-separated retune schedule in the form '<offset_ms>:<frequency_hz>,...'.",
    )
    parser.add_argument(
        "--timing",
        choices=["original_timing", "fast_replay"],
        default="original_timing",
        help="How to schedule packet sending during replay.",
    )
    parser.add_argument(
        "--normalize-gap-ms",
        type=int,
        default=100,
        help="Rewrite the replay timestamps to a dense fixed gap before applying retune events. Use 0 to keep the original offsets.",
    )
    parser.add_argument("--fast-replay", action="store_true", help="Alias for --timing fast_replay.")
    parser.add_argument("--dry-run", action="store_true", help="Print the retune plan without sending UDP.")
    parser.add_argument("--output-sequence", help="Optional path for the patched replay JSON.")
    parser.add_argument("--destination-host", default="127.0.0.1", help="Override the destination host.")
    parser.add_argument("--destination-port", type=int, default=5957, help="Override the destination port.")
    parser.add_argument(
        "--actions-output",
        help="Optional actions.json path to update automatically with the applied retune timestamps.",
    )
    parser.add_argument(
        "--capture-kind",
        choices=["idle", "tx"],
        help="Which section to update inside actions.json when --actions-output is used.",
    )
    parser.add_argument(
        "--capture-path",
        help="Capture file path to write into actions.json when --actions-output is used.",
    )
    parser.add_argument(
        "--description",
        default="Retune injection generated by inject_retune_sequence.py",
        help="Description to store in actions.json when --actions-output is used.",
    )
    return parser


def injector_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sequence = load_udp_replay_sequence(args.input)
    filtered_sequence = filter_sequence_for_profile(sequence, args.profile)
    normalized_sequence = normalize_sequence_timestamps(filtered_sequence, args.normalize_gap_ms)
    retune_events = parse_retune_events(args.retune_events)
    patched_sequence, applied_events = apply_retune_schedule(normalized_sequence, retune_events)
    patched_sequence = replace(
        patched_sequence,
        destination_host=args.destination_host,
        destination_port=args.destination_port,
    )

    if args.output_sequence:
        output_path = Path(args.output_sequence)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(_sequence_to_dict(patched_sequence), indent=2, ensure_ascii=False), encoding="utf-8")

    if args.actions_output:
        if not args.capture_kind or not args.capture_path:
            raise SystemExit("--actions-output requires both --capture-kind and --capture-path.")
        write_actions_file(
            Path(args.actions_output),
            capture_kind=args.capture_kind,
            capture_path=args.capture_path,
            description=args.description,
            applied_events=applied_events,
        )

    timing_mode = "fast_replay" if args.fast_replay else args.timing
    packets = replay_udp_sequence(
        patched_sequence,
        timing_mode=timing_mode,
        dry_run=args.dry_run,
        destination_host_override=args.destination_host,
        destination_port_override=args.destination_port,
    )
    print(render_retune_plan(normalized_sequence, patched_sequence, applied_events, profile=args.profile))
    if args.dry_run:
        print()
        print(render_replay_dry_run(patched_sequence, packets))
    else:
        print()
        print(f"replayed_packets: {len(packets)}")
        print(f"destination: {args.destination_host}:{args.destination_port}")
    return 0


def _sequence_to_dict(sequence: ReplaySequence) -> dict[str, Any]:
    return {
        "source_capture": sequence.source_capture,
        "mode": sequence.mode,
        "destination_host": sequence.destination_host,
        "destination_port": sequence.destination_port,
        "packets": [
            {
                "timestamp_offset_ms": packet.timestamp_offset_ms,
                "dst_port": packet.dst_port,
                "payload_hex": packet.payload_hex,
                "payload_len": packet.payload_len,
                "tag": packet.tag,
                "source_capture": packet.source_capture,
                "mode": packet.mode,
            }
            for packet in sequence.packets
        ],
    }
