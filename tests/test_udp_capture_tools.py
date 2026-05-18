from __future__ import annotations

import asyncio
import json
from pathlib import Path
import socket
import struct
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.udp_capture_tools import (
    analyze_udp_capture,
    compare_udp_capture_analyses,
    export_udp_replay_sequence,
    load_udp_replay_sequence,
    render_replay_dry_run,
    replay_udp_sequence,
)


def _build_loopback_udp_packet(src_port: int, dst_port: int, payload: bytes) -> bytes:
    udp_len = 8 + len(payload)
    total_len = 20 + udp_len
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_len,
        0,
        0,
        64,
        17,
        0,
        socket.inet_aton("127.0.0.1"),
        socket.inet_aton("127.0.0.1"),
    )
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_len, 0)
    return bytes.fromhex("02 00 00 00") + ip_header + udp_header + payload


def _pad4(payload: bytes) -> bytes:
    remainder = len(payload) % 4
    if remainder == 0:
        return payload
    return payload + (b"\x00" * (4 - remainder))


def _build_block(block_type: int, body: bytes) -> bytes:
    padded_body = _pad4(body)
    block_len = 12 + len(padded_body)
    return struct.pack("<II", block_type, block_len) + padded_body + struct.pack("<I", block_len)


def _build_pcapng(packets: list[tuple[int, bytes]]) -> bytes:
    shb_body = struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1)
    idb_body = struct.pack("<HHi", 0, 0, 262144)
    parts = [_build_block(0x0A0D0D0A, shb_body), _build_block(0x00000001, idb_body)]
    for timestamp_ms, packet in packets:
        ts_us = timestamp_ms * 1000
        ts_high = (ts_us >> 32) & 0xFFFFFFFF
        ts_low = ts_us & 0xFFFFFFFF
        body = struct.pack("<IIIII", 0, ts_high, ts_low, len(packet), len(packet)) + _pad4(packet)
        parts.append(_build_block(0x00000006, body))
    return b"".join(parts)


def _write_capture(path: Path, *, mode_marker_prefix: bytes, include_shutdown: bool) -> None:
    wsjtx_status = bytes.fromhex("ad bc cb da 00 00 00 02 00 00 00 01 00 00 00 06") + b"WSJT-X\x00\x00\x00\x00FT4\x00FT8"
    wsjtx_bootstrap = bytes.fromhex("ad bc cb da 00 00 00 02 00 00 00 00 00 00 00 06") + b"WSJT-X\x00\x00\x00\x03\x00\x00\x00\x052.6.1"
    wsjtx_shutdown = bytes.fromhex("ad bc cb da 00 00 00 02 00 00 00 06 00 00 00 06") + b"WSJT-X"
    business = bytes.fromhex("59 57 f4 00") + (b"\x00" * 252)
    marker = mode_marker_prefix + bytes.fromhex("67 05 dc 00 00 00 00 01 03 02 01 00 03 03 01 01 02 03 03 00") + (b"\x00" * 232)
    hamlib = b'{"app":"Hamlib","version":"1.0"}'
    packets = [
        (1000, _build_loopback_udp_packet(55589, 2237, wsjtx_bootstrap)),
        (2000, _build_loopback_udp_packet(55589, 2237, wsjtx_status)),
        (2500, _build_loopback_udp_packet(55590, 5957, business)),
        (2600, _build_loopback_udp_packet(55591, 5957, marker)),
        (2700, _build_loopback_udp_packet(55594, 4532, hamlib)),
    ]
    if include_shutdown:
        packets.append((3000, _build_loopback_udp_packet(55589, 2237, wsjtx_shutdown)))
    path.write_bytes(_build_pcapng(packets))


class UdpCaptureToolsTests(unittest.TestCase):
    def test_analyze_udp_capture_reports_ft4_and_ft8_mode_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            ft4_path = tmp_path / "ft4-only.pcapng"
            ft8_path = tmp_path / "ft8-only.pcapng"
            _write_capture(ft4_path, mode_marker_prefix=bytes.fromhex("59 57 04 00"), include_shutdown=True)
            _write_capture(ft8_path, mode_marker_prefix=bytes.fromhex("59 57 08 00"), include_shutdown=False)

            ft4 = analyze_udp_capture(ft4_path)
            ft8 = analyze_udp_capture(ft8_path)

        self.assertEqual(ft4["interesting_port_counts"]["5957"], 2)
        self.assertEqual(ft8["interesting_port_counts"]["5957"], 2)
        self.assertIn("59 57 04 00", ft4["digimanager_5957"]["prefix_counts"])
        self.assertIn("59 57 08 00", ft8["digimanager_5957"]["prefix_counts"])
        self.assertTrue(ft4["conclusions"]["ft4_reaches_5957"])
        self.assertTrue(ft8["conclusions"]["ft8_reaches_5957"])
        self.assertTrue(ft4["conclusions"]["port_4532_looks_like_hamlib_broadcast"])

        comparison = compare_udp_capture_analyses([ft4, ft8])
        self.assertIn("59 57 f4 00", comparison["shared_5957_prefixes"])
        self.assertEqual(comparison["unique_5957_prefixes"]["ft4-only.pcapng"], ["59 57 04 00"])
        self.assertEqual(comparison["unique_5957_prefixes"]["ft8-only.pcapng"], ["59 57 08 00"])

    def test_export_udp_replay_sequence_tags_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            ft4_path = tmp_path / "ft4-only.pcapng"
            output_path = tmp_path / "ft4-replay.json"
            _write_capture(ft4_path, mode_marker_prefix=bytes.fromhex("59 57 04 00"), include_shutdown=True)

            sequence = export_udp_replay_sequence(ft4_path, mode="FT4", output_path=output_path)
            loaded = load_udp_replay_sequence(output_path)

        self.assertEqual(sequence.mode, "FT4")
        self.assertEqual(len(sequence.packets), 2)
        self.assertEqual(sequence.packets[0].tag, "business_packet")
        self.assertEqual(sequence.packets[1].tag, "ft4_mode_marker")
        self.assertEqual(loaded.packets[1].tag, "ft4_mode_marker")
        self.assertEqual(loaded.packets[1].payload_len, 256)

    def test_render_replay_dry_run_and_actual_replay(self) -> None:
        packets = []
        received = []
        ready = threading.Event()

        def server() -> None:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.bind(("127.0.0.1", 0))
                packets.append(udp_socket.getsockname()[1])
                ready.set()
                for _ in range(2):
                    payload, _addr = udp_socket.recvfrom(4096)
                    received.append(payload)

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        ready.wait(2)
        port = packets[0]

        sequence = load_udp_replay_sequence(
            _write_replay_json(
                [
                    {"timestamp_offset_ms": 0, "dst_port": port, "payload_hex": "59 57 f4 00", "payload_len": 4, "tag": "business_packet", "source_capture": "sample.pcapng", "mode": "FT8"},
                    {"timestamp_offset_ms": 5, "dst_port": port, "payload_hex": "59 57 08 00", "payload_len": 4, "tag": "ft8_mode_marker", "source_capture": "sample.pcapng", "mode": "FT8"},
                ]
            )
        )

        dry_run = render_replay_dry_run(sequence, sequence.packets)
        self.assertIn("packets: 2", dry_run)
        self.assertIn("ft8_mode_marker", dry_run)

        replay_udp_sequence(sequence, timing_mode="fast_replay", destination_port_override=port)
        thread.join(2)
        self.assertEqual(received, [bytes.fromhex("59 57 f4 00"), bytes.fromhex("59 57 08 00")])


def _write_replay_json(packets: list[dict[str, object]]) -> Path:
    tmp_dir = tempfile.mkdtemp()
    path = Path(tmp_dir) / "replay.json"
    payload = {
        "source_capture": "sample.pcapng",
        "mode": "FT8",
        "destination_host": "127.0.0.1",
        "destination_port": 5957,
        "packets": packets,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
