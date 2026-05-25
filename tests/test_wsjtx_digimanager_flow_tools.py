from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.wsjtx_digimanager_flow_tools import (  # noqa: E402
    build_flow_report,
    build_setdigitaldata2_header,
    load_replay_capture,
)


def _write_replay(path: Path, *, mode: str, marker_prefix: str, length_byte: int) -> None:
    packets = [
        {
            "timestamp_offset_ms": 0,
            "dst_port": 5957,
            "payload_hex": "59 57 f4 00 " + "00 " * 251 + "4a 58",
            "payload_len": 256,
            "tag": "business_packet",
            "source_capture": f"{mode.lower()}-test.pcapng",
            "mode": mode,
        },
        {
            "timestamp_offset_ms": 1000,
            "dst_port": 5957,
            "payload_hex": (
                f"{marker_prefix} "
                f"{length_byte:02x} 05 dc 00 00 00 03 01 04 00 06 05 "
                + "00 " * (256 - 13)
            ),
            "payload_len": 256,
            "tag": f"{mode.lower()}_mode_marker",
            "source_capture": f"{mode.lower()}-test.pcapng",
            "mode": mode,
        },
    ]
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


class WsjtxDigimanagerFlowToolsTests(unittest.TestCase):
    def test_build_setdigitaldata2_header_matches_stock_and_patched_layouts(self) -> None:
        marker = bytes.fromhex("59 57 04 00 67 05 dc 00 00 00 00 01")
        self.assertEqual(build_setdigitaldata2_header(marker, preserve_mode_hint=False), bytes.fromhex("05 dc 00 00 67"))
        self.assertEqual(build_setdigitaldata2_header(marker, preserve_mode_hint=True), bytes.fromhex("05 dc 67 00 67"))

    def test_flow_report_flags_upstream_distinction_and_sender_flattening(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            ft4 = root / "ft4.json"
            ft8 = root / "ft8.json"
            _write_replay(ft4, mode="FT4", marker_prefix="59 57 04 00", length_byte=0x67)
            _write_replay(ft8, mode="FT8", marker_prefix="59 57 08 00", length_byte=0x4F)

            report = build_flow_report(ft4, ft8)

        self.assertTrue(report["comparison"]["upstream"]["distinct_upstream_modes"])
        self.assertTrue(report["comparison"]["stock_setdigitaldata2_headers"]["headers_identical_except_length"])
        self.assertIn("压平", report["comparison"]["judgement"])

    def test_load_replay_capture_reads_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            replay = Path(tmp_dir) / "ft4.json"
            _write_replay(replay, mode="FT4", marker_prefix="59 57 04 00", length_byte=0x67)
            capture = load_replay_capture(replay)

        self.assertEqual(capture.mode, "FT4")
        self.assertEqual(capture.destination_port, 5957)
        self.assertEqual(len(capture.packets), 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
