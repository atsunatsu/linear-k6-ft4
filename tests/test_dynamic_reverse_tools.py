from __future__ import annotations

import json
from pathlib import Path
import socket
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.dynamic_reverse_tools import (  # noqa: E402
    analyze_dynamic_lock_behavior,
    infer_digimanager_continuous_retune,
    infer_firmware_applies_retune,
    infer_lock_owner,
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


def _write_capture(path: Path, packets: list[tuple[int, bytes]]) -> None:
    path.write_bytes(_build_pcapng(packets))


class DynamicReverseToolsTests(unittest.TestCase):
    def test_infer_helpers_cover_three_way_split(self) -> None:
        self.assertEqual(infer_lock_owner("no", "unclear"), "pc_side")
        self.assertEqual(infer_lock_owner("yes", "no"), "firmware_side")
        self.assertEqual(infer_lock_owner("yes", "temporarily"), "firmware_side")
        self.assertEqual(infer_lock_owner("yes", "yes"), "still_unclear")

    def test_analyze_dynamic_lock_behavior_reports_firmware_side_when_packets_continue_but_radio_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dynamic_dir = root / "reverse" / "input" / "dynamic"
            dynamic_dir.mkdir(parents=True)

            idle_path = dynamic_dir / "idle-retune.pcapng"
            tx_path = dynamic_dir / "tx-retune.pcapng"

            idle_packets = [
                (4500, _build_loopback_udp_packet(50001, 5957, bytes.fromhex("59 57 f4 00") + b"\x00" * 252)),
                (5200, _build_loopback_udp_packet(50002, 5957, bytes.fromhex("59 57 f4 00") + b"\x01" * 252)),
            ]
            tx_packets = [
                (6800, _build_loopback_udp_packet(50003, 5957, bytes.fromhex("59 57 f4 00") + b"\x02" * 252)),
                (7400, _build_loopback_udp_packet(50004, 5957, bytes.fromhex("59 57 f4 00") + b"\x03" * 252)),
            ]
            _write_capture(idle_path, idle_packets)
            _write_capture(tx_path, tx_packets)

            actions = {
                "idle_capture": {
                    "path": "reverse/input/dynamic/idle-retune.pcapng",
                    "retune_events_ms": [5000],
                    "description": "idle test",
                },
                "tx_capture": {
                    "path": "reverse/input/dynamic/tx-retune.pcapng",
                    "retune_events_ms": [7000],
                    "description": "tx test",
                },
                "radio_observation": {
                    "idle_frequency_change": "no",
                    "tx_frequency_change": "temporary",
                },
            }
            (dynamic_dir / "actions.json").write_text(json.dumps(actions), encoding="utf-8")

            report = analyze_dynamic_lock_behavior(root)

        self.assertTrue(report["present"])
        self.assertEqual(report["digimanager_continuous_retune"], "yes")
        self.assertEqual(report["firmware_applies_retune_in_digital_mode"], "temporarily")
        self.assertEqual(report["lock_owner"], "firmware_side")

    def test_analyze_dynamic_lock_behavior_reports_pc_side_when_no_packets_near_retune(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dynamic_dir = root / "reverse" / "input" / "dynamic"
            dynamic_dir.mkdir(parents=True)

            idle_path = dynamic_dir / "idle-retune.pcapng"
            tx_path = dynamic_dir / "tx-retune.pcapng"
            _write_capture(idle_path, [(1000, _build_loopback_udp_packet(50001, 5957, bytes.fromhex("59 57 04 00") + b"\x00" * 252))])
            _write_capture(tx_path, [(1000, _build_loopback_udp_packet(50002, 5957, bytes.fromhex("59 57 08 00") + b"\x00" * 252))])

            actions = {
                "idle_capture": {
                    "path": "reverse/input/dynamic/idle-retune.pcapng",
                    "retune_events_ms": [8000],
                    "description": "idle no activity",
                },
                "tx_capture": {
                    "path": "reverse/input/dynamic/tx-retune.pcapng",
                    "retune_events_ms": [9000],
                    "description": "tx no activity",
                },
                "radio_observation": {
                    "idle_frequency_change": "no",
                    "tx_frequency_change": "no",
                },
            }
            (dynamic_dir / "actions.json").write_text(json.dumps(actions), encoding="utf-8")

            report = analyze_dynamic_lock_behavior(root)

        self.assertEqual(report["digimanager_continuous_retune"], "no")
        self.assertEqual(report["lock_owner"], "pc_side")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
