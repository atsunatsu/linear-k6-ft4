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
        self.assertEqual([item.offset for item in hits_32], [0])
        self.assertEqual([item.offset for item in hits_35], [4])

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
                "command_compare_hits_validated": {
                    "0x30": [],
                    "0x32": [{"offset": 0x0D91, "instruction": "cmp r0, #0x32"}],
                    "0x33": [{"offset": 0x0DFD, "instruction": "cmp r0, #0x33"}],
                    "0x35": [],
                },
                "command_compare_hits_seeded_validated": {
                    "0x30": [],
                    "0x32": [],
                    "0x33": [],
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

    def test_real_assets_currently_do_not_revalidate_32_or_33_hits(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        self.assertEqual(report["firmware"]["command_compare_hits_validated"]["0x32"], [])
        self.assertEqual(report["firmware"]["command_compare_hits_validated"]["0x33"], [])
        self.assertTrue(report["firmware"]["command_compare_hits_seeded_validated"]["0x32"])
        self.assertTrue(report["firmware"]["command_compare_hits_seeded_validated"]["0x33"])
        self.assertEqual(report["judgement"]["likely_handler_model"], "adjacent_command_dispatch_seen_but_0x35_not_literal")

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

    def test_real_assets_show_table_driven_string_structures(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        tables = report["firmware"]["string_pointer_tables"]
        interesting = [item for item in tables if item["contains_interesting_strings"]]
        self.assertTrue(any(item["offset"] == 0xD778 for item in interesting))
        dispatch_windows = {
            item["label"]: item["lines"]
            for item in report["firmware"]["candidate_dispatch_windows"]
        }
        self.assertIn("dispatcher_near_0x32", dispatch_windows)
        self.assertTrue(any("cmp r0, #0x32" in line for line in dispatch_windows["dispatcher_near_0x32"]))

    def test_real_assets_expose_generic_command35_branch_hypothesis(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        hypothesis = report["firmware"]["dispatcher_hypothesis"]
        self.assertEqual(hypothesis["dispatcher_root_offset"], 0x0D90)
        self.assertEqual(hypothesis["generic_parse_entry_offset"], 0x0DBE)
        self.assertEqual(hypothesis["generic_parse_helper_target"], 0x0280)
        self.assertTrue(any("0x0DBE" in item for item in hypothesis["command_0x35_flow"]))
        self.assertEqual(hypothesis["contextual_function_hint"]["classification_helper"], 0x888C)
        profiles = report["firmware"]["generic_parse_profiles"]["subcode_cases"]
        self.assertEqual(profiles["0x35"]["target_offset"], 0x02EA)
        self.assertEqual(profiles["0x35"]["derived_outputs"]["out_b"], 0x03)
        self.assertEqual(profiles["0x32"]["target_offset"], 0x031E)
        self.assertEqual(profiles["0x32"]["derived_outputs"]["out_b"], 0xA9)

    def test_real_assets_expose_dispatcher_runtime_state_refs(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        runtime_refs = report["firmware"]["dispatcher_runtime_refs"]
        values = {item["loaded_value"] for item in runtime_refs}
        labels = {item["label"] for item in runtime_refs}
        self.assertIn(0x20000094, values)
        self.assertIn(0x7FFFFFFF, values)
        self.assertIn("state_cell_primary", labels)
        self.assertEqual(
            report["judgement"]["dispatcher_runtime_state_model"],
            "generic_branch_looks_more_like_bounded_state_machine_than_full_symbol_stream",
        )

    def test_real_assets_expose_dispatcher_helper_call_graph(self) -> None:
        report = analyze_command35_path(
            firmware_path=Path("reverse/input/firmware/cec_0.3QB.packed.bin"),
            digimanager_path=Path("reverse/input/digimanager/UVK5DigManager.exe"),
            ft4_replay_path=Path("samples/replay/ft4-replay.json"),
            ft8_replay_path=Path("samples/replay/ft8-replay.json"),
        )
        helper_callers = report["firmware"]["helper_callers"]
        self.assertIn(0x0DC4, helper_callers["0x0280"])
        self.assertIn(0x0D7E, helper_callers["0x7618"])
        self.assertIn(0x0E0C, helper_callers["0x7714"])
        self.assertIn(0x0D34, helper_callers["0x888C"])
        self.assertIn(0x0D4A, helper_callers["0x0BD0"])
        self.assertEqual(
            report["firmware"]["helper_semantics"]["0x7714"]["role"],
            "search / selection helper",
        )
        self.assertEqual(
            report["firmware"]["helper_semantics"]["0x888C"]["role"],
            "table classifier",
        )

        window_callees = {item["target_offset"] for item in report["firmware"]["dispatcher_window_callees"]}
        self.assertTrue({0x0280, 0x7618, 0x7714, 0x888C, 0x0BD0}.issubset(window_callees))
        self.assertEqual(
            report["judgement"]["dispatcher_helper_call_graph"]["0x0280"],
            helper_callers["0x0280"],
        )

        context_hub_callees = {item["target_offset"] for item in report["firmware"]["context_hub_callees"]}
        self.assertIn(0x7714, context_hub_callees)
        self.assertIn(0x0564, helper_callers["0x76A8"])
        self.assertTrue(any(item["center_offset"] == 0x04D6 for item in report["firmware"]["context_hub_windows"]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
