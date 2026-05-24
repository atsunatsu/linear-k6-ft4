from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.ft4_timing_tools import (  # noqa: E402
    compare_mode_cadence,
    summarize_replay_cadence,
    write_mode_cadence_report,
)


def _write_replay(path: Path, *, mode: str, offsets: list[int], tags: list[str]) -> None:
    packets = []
    for index, (offset, tag) in enumerate(zip(offsets, tags, strict=True)):
        prefix = {
            "business_packet": "59 57 f4 00",
            "ft4_mode_marker": "59 57 04 00",
            "ft8_mode_marker": "59 57 08 00",
        }[tag]
        packets.append(
            {
                "timestamp_offset_ms": offset,
                "dst_port": 5957,
                "payload_hex": prefix + " " + "00 " * 252,
                "payload_len": 256,
                "tag": tag,
                "source_capture": f"{mode.lower()}-test.pcapng",
                "mode": mode,
            }
        )
    path.write_text(
        json.dumps(
            {
                "source_capture": f"{mode.lower()}-test.pcapng",
                "mode": mode,
                "destination_host": "127.0.0.1",
                "destination_port": 5957,
                "packets": packets,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class Ft4TimingToolsTests(unittest.TestCase):
    def test_summarize_replay_cadence_reports_intervals_and_batches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            replay = Path(tmp_dir) / "ft4.json"
            _write_replay(
                replay,
                mode="FT4",
                offsets=[0, 100, 200, 700],
                tags=["business_packet", "business_packet", "ft4_mode_marker", "business_packet"],
            )
            summary = summarize_replay_cadence(replay)

        self.assertEqual(summary["packet_count"], 4)
        self.assertEqual(summary["interval_stats"]["count"], 3)
        self.assertEqual(summary["tag_counts"]["business_packet"], 3)
        self.assertEqual(summary["batches"][1]["tag"], "ft4_mode_marker")

    def test_compare_mode_cadence_prefers_pc_side_when_ft4_is_slower(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ft4 = Path(tmp_dir) / "ft4.json"
            ft8 = Path(tmp_dir) / "ft8.json"
            _write_replay(
                ft4,
                mode="FT4",
                offsets=[0, 1000, 2000, 3000],
                tags=["business_packet", "business_packet", "business_packet", "ft4_mode_marker"],
            )
            _write_replay(
                ft8,
                mode="FT8",
                offsets=[0, 300, 600, 900],
                tags=["business_packet", "business_packet", "business_packet", "ft8_mode_marker"],
            )
            report = compare_mode_cadence(ft4, ft8)

        self.assertEqual(report["diagnosis"]["likely_timing_owner"], "pc_side_sender_chain")
        self.assertGreater(report["comparison"]["duration_ratio_ft4_over_ft8"], 1.3)

    def test_write_mode_cadence_report_writes_json_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ft4 = tmp / "ft4.json"
            ft8 = tmp / "ft8.json"
            report_json = tmp / "timing.json"
            report_text = tmp / "timing.txt"
            _write_replay(
                ft4,
                mode="FT4",
                offsets=[0, 400, 800],
                tags=["business_packet", "business_packet", "ft4_mode_marker"],
            )
            _write_replay(
                ft8,
                mode="FT8",
                offsets=[0, 200, 400],
                tags=["business_packet", "business_packet", "ft8_mode_marker"],
            )

            report = write_mode_cadence_report(ft4, ft8, output_json=report_json, output_text=report_text)

            self.assertTrue(report_json.exists())
            self.assertTrue(report_text.exists())
            self.assertEqual(report["ft4"]["mode"], "FT4")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
