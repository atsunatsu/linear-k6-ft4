from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.firmware_command35_tools import (
    _analyze_single_replay,
    analyze_command35_path,
    find_exact_immediate_hits,
    infer_command35_judgement,
)


class FirmwareCommand35ToolsTests(unittest.TestCase):
    def test_find_exact_immediate_hits_is_exact(self) -> None:
        raw = bytes.fromhex("32 20 33 21 35 22")
        hits_32 = find_exact_immediate_hits(raw, 0x32, limit=4)
        hits_35 = find_exact_immediate_hits(raw, 0x35, limit=4)
        self.assertEqual([item.offset for item in hits_32], [1])
        self.assertEqual([item.offset for item in hits_35], [5])

    def test_analyze_single_replay_marks_sparse_business_packets(self) -> None:
        report = _analyze_single_replay(Path("samples/replay/ft4-replay.json"))
        self.assertEqual(report["business_packet_count"], 66)
        self.assertGreater(report["business_packet_nonzero_summary"]["mean"], 8.0)
        self.assertLess(report["business_packet_nonzero_summary"]["mean"], 10.0)
        self.assertIn(244, report["business_packet_hotspots"])

    def test_infer_command35_judgement_prefers_second_stage_model_without_direct_35(self) -> None:
        report = {
            "firmware": {
                "command_immediate_hits": {
                    "0x30": [],
                    "0x32": [{"offset": 0x02E7, "instruction": "movs r3, #0x32"}],
                    "0x33": [],
                    "0x35": [{"offset": 0x04F5, "instruction": "adds r3, #0x35"}],
                },
                "command_compare_hits": {
                    "0x30": [],
                    "0x32": [{"offset": 0x0D91, "instruction": "cmp r0, #0x32"}],
                    "0x33": [{"offset": 0x0DFD, "instruction": "cmp r0, #0x33"}],
                    "0x35": [],
                },
                "frame_family_matches": {
                    "obfuscation_offsets": [0xDB10],
                    "stx_offsets": [0xDEA4],
                    "etx_offsets": [0xDEA8],
                },
                "digital_mode_strings": {
                    "FT8": [0xD61E],
                    "FT4": [],
                    "APRS": [0xD624],
                    "WSPR": [0xD629],
                },
            },
            "replay": {
                "ft4": {"business_packet_nonzero_summary": {"mean": 8.7}},
                "ft8": {"business_packet_nonzero_summary": {"mean": 8.7}},
            },
        }
        judgement = infer_command35_judgement(report)
        self.assertEqual(judgement["command35_frame_kind"], "sparse_control_frame")
        self.assertEqual(judgement["firmware_direct_cmp_0x35"], "no")
        self.assertEqual(judgement["likely_handler_model"], "adjacent_command_dispatch_seen_but_0x35_not_literal")
        self.assertTrue(judgement["firmware_frame_family"]["stx_found"])
        self.assertTrue(judgement["firmware_frame_family"]["obfuscation_found"])
        self.assertTrue(judgement["firmware_mode_strings"]["ft8_present"])
        self.assertFalse(judgement["firmware_mode_strings"]["ft4_present"])

    def test_real_assets_show_shared_frame_family_constants(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        frame_matches = report["firmware"]["frame_family_matches"]
        self.assertIn(0xDB10, frame_matches["obfuscation_offsets"])
        self.assertIn(0xDEA4, frame_matches["stx_offsets"])
        self.assertIn(0xDEA8, frame_matches["etx_offsets"])
        self.assertTrue(report["firmware"]["digital_mode_strings"]["FT8"])
        self.assertFalse(report["firmware"]["digital_mode_strings"]["FT4"])
        cluster_labels = [item.get("points_to_ascii") for item in report["firmware"]["constant_cluster"]["entries"]]
        self.assertIn("FM", cluster_labels)
        self.assertIn("CT", cluster_labels)
        self.assertIn("DCS", cluster_labels)
        self.assertIn("DCR", cluster_labels)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
