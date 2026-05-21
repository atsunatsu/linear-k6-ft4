from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.retune_injector import (  # noqa: E402
    apply_retune_schedule,
    extract_embedded_frequency_hz,
    filter_sequence_for_profile,
    load_udp_replay_sequence,
    normalize_sequence_timestamps,
    parse_retune_events,
    write_actions_file,
)


def _write_replay_json(path: Path) -> None:
    payload = {
        "source_capture": "sample.pcapng",
        "mode": "FT8",
        "destination_host": "127.0.0.1",
        "destination_port": 5957,
        "packets": [
            {
                "timestamp_offset_ms": 1000,
                "dst_port": 5957,
                "payload_hex": _business_packet_hex(145000000),
                "payload_len": 256,
                "tag": "business_packet",
                "source_capture": "sample.pcapng",
                "mode": "FT8",
            },
            {
                "timestamp_offset_ms": 2000,
                "dst_port": 5957,
                "payload_hex": _business_packet_hex(144174000),
                "payload_len": 256,
                "tag": "business_packet",
                "source_capture": "sample.pcapng",
                "mode": "FT8",
            },
            {
                "timestamp_offset_ms": 2500,
                "dst_port": 5957,
                "payload_hex": ("59 57 08 00 " + "00 " * 252).strip(),
                "payload_len": 256,
                "tag": "ft8_mode_marker",
                "source_capture": "sample.pcapng",
                "mode": "FT8",
            },
            {
                "timestamp_offset_ms": 4000,
                "dst_port": 5957,
                "payload_hex": _business_packet_hex(144174000),
                "payload_len": 256,
                "tag": "business_packet",
                "source_capture": "sample.pcapng",
                "mode": "FT8",
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _business_packet_hex(frequency_hz: int) -> str:
    payload = bytearray(bytes.fromhex("59 57 f4 00") + (b"\x00" * 252))
    payload[-12:-8] = frequency_hz.to_bytes(4, "little")
    return payload.hex(" ")


class RetuneInjectorTests(unittest.TestCase):
    def test_parse_retune_events_sorts_offsets(self) -> None:
        events = parse_retune_events("4000:145950500,1000:145950000")
        self.assertEqual([event.requested_at_ms for event in events], [1000, 4000])
        self.assertEqual([event.frequency_hz for event in events], [145950000, 145950500])

    def test_idle_profile_keeps_only_business_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "replay.json"
            _write_replay_json(path)
            sequence = load_udp_replay_sequence(path)

        idle_sequence = filter_sequence_for_profile(sequence, "idle")
        self.assertEqual([packet.tag for packet in idle_sequence.packets], ["business_packet", "business_packet", "business_packet"])

    def test_apply_retune_schedule_patches_frequency_field_and_records_applied_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "replay.json"
            _write_replay_json(path)
            sequence = filter_sequence_for_profile(load_udp_replay_sequence(path), "idle")

        patched, applied = apply_retune_schedule(
            normalize_sequence_timestamps(sequence, 1000),
            parse_retune_events("500:145950000,1500:145950500"),
        )

        self.assertEqual([event.applied_at_ms for event in applied[:2]], [1000, 2000])
        patched_freqs = [extract_embedded_frequency_hz(packet) for packet in patched.packets if packet.tag == "business_packet"]
        self.assertEqual(patched_freqs, [145000000, 145950000, 145950500])

    def test_normalize_sequence_timestamps_rewrites_offsets_to_fixed_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "replay.json"
            _write_replay_json(path)
            sequence = load_udp_replay_sequence(path)

        normalized = normalize_sequence_timestamps(sequence, 250)
        self.assertEqual([packet.timestamp_offset_ms for packet in normalized.packets], [0, 250, 500, 750])

    def test_write_actions_file_merges_idle_and_tx_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            actions_path = Path(tmp_dir) / "actions.json"
            write_actions_file(
                actions_path,
                capture_kind="idle",
                capture_path="reverse/input/dynamic/idle-retune.pcapng",
                description="idle check",
                applied_events=[
                    type("Applied", (), {"applied_at_ms": 2200})(),
                    type("Applied", (), {"applied_at_ms": 4200})(),
                ],
            )
            write_actions_file(
                actions_path,
                capture_kind="tx",
                capture_path="reverse/input/dynamic/tx-retune.pcapng",
                description="tx check",
                applied_events=[
                    type("Applied", (), {"applied_at_ms": 5100})(),
                ],
            )
            payload = json.loads(actions_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["idle_capture"]["retune_events_ms"], [2200, 4200])
        self.assertEqual(payload["tx_capture"]["retune_events_ms"], [5100])
        self.assertEqual(payload["radio_observation"]["idle_frequency_change"], "unknown")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
