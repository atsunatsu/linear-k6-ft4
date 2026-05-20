from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.reverse_tools import (  # noqa: E402
    analyze_digimanager_binary,
    analyze_firmware_bin,
    analyze_reverse_targets,
    extract_ascii_strings,
    extract_utf16le_strings,
    find_reverse_assets,
    try_unpack_uvk5_packed_firmware,
    write_reverse_report,
)


class ReverseToolsTests(unittest.TestCase):
    def test_extract_string_helpers_find_ascii_and_utf16(self) -> None:
        payload = b"\x00DIG.M\x00\x00D\x00I\x00G\x00I\x00T\x00A\x00L\x00"
        self.assertIn("DIG.M", extract_ascii_strings(payload))
        self.assertIn("DIGITAL", extract_utf16le_strings(payload))

    def test_analyze_firmware_bin_reports_strings_and_frequency_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "real-0.3q.bin"
            data = bytearray()
            data.extend((b"\x00" * 4))
            data.extend((145_950_000).to_bytes(4, "little"))
            data.extend((145_950_000).to_bytes(4, "little"))
            data.extend(b"BOOT\x00DIG.M\x00FT8\x00LOCK\x00")
            data.extend("DIGITAL".encode("utf-16le"))
            data.extend(bytes.fromhex("59 57 04 00"))
            path.write_bytes(bytes(data))

            summary = analyze_firmware_bin(path)

        self.assertTrue(summary["present"])
        self.assertIn("DIG.M", summary["interesting_strings"])
        self.assertTrue(any(item["text"] == "DIG.M" for item in summary["interesting_string_offsets"]))
        self.assertTrue(any(item["value_hz"] == 145_950_000 for item in summary["frequency_literals_hz"]))
        self.assertEqual(summary["marker_counts"]["ft4_mode_marker"], 1)

    def test_unpack_uvk5_packed_firmware_recovers_raw_payload(self) -> None:
        raw = bytes(range(256)) * 40
        version = b"*CEC_0.3Q TEST"
        version = version[:16].ljust(16, b"\x00")
        from sat_bridge.reverse_tools import PACK_OBFUSCATION  # local import keeps test close to real packing rules

        inserted = raw[:0x2000] + version + raw[0x2000:]
        packed = bytes(
            byte ^ PACK_OBFUSCATION[index % len(PACK_OBFUSCATION)]
            for index, byte in enumerate(inserted)
        )
        crc = __import__("binascii").crc_hqx(packed, 0).to_bytes(2, "little")
        result = try_unpack_uvk5_packed_firmware(packed + crc)

        self.assertTrue(result["ok"])
        self.assertTrue(result["crc_ok"])
        self.assertEqual(result["embedded_version"].rstrip("\x00"), "*CEC_0.3Q TEST")
        self.assertEqual(result["raw_bytes"], raw)

    def test_analyze_digimanager_binary_accepts_zip_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "UVK5DigManager_v1.0.zip"
            exe_bytes = b"MZ" + b"UVK5DigManager\x005957\x002237\x00FT8\x00WSJT-X\x00" + bytes.fromhex("59 57 08 00")
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("UVK5DigManager.exe", exe_bytes)

            summary = analyze_digimanager_binary(zip_path)

        self.assertTrue(summary["present"])
        self.assertEqual(summary["container_kind"], "zip")
        self.assertEqual(summary["port_mentions"]["5957"], 1)
        self.assertEqual(summary["marker_counts"]["ft8_mode_marker"], 1)

    def test_analyze_reverse_targets_handles_missing_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "samples" / "replay").mkdir(parents=True)

            report = analyze_reverse_targets(root)

        self.assertEqual(report["digital_mode_entry"]["status"], "missing_real_assets")
        self.assertEqual(report["recommended_next_step"]["kind"], "collect_real_assets")

    def test_find_reverse_assets_accepts_root_level_drop_in_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "cec_0.3QB.packed.bin").write_bytes(b"demo")
            (root / "UVK5DigManager.exe").write_bytes(b"MZdemo")
            (root / "samples" / "replay").mkdir(parents=True)

            assets = find_reverse_assets(root)

        self.assertIsNotNone(assets.firmware)
        self.assertIsNotNone(assets.digimanager)
        self.assertEqual(assets.firmware.name, "cec_0.3QB.packed.bin")
        self.assertEqual(assets.digimanager.name, "UVK5DigManager.exe")

    def test_analyze_reverse_targets_writes_report_with_assets_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            firmware_dir = root / "reverse" / "input" / "firmware"
            digimanager_dir = root / "reverse" / "input" / "digimanager"
            replay_dir = root / "samples" / "replay"
            output_dir = root / "logs" / "reverse"
            firmware_dir.mkdir(parents=True)
            digimanager_dir.mkdir(parents=True)
            replay_dir.mkdir(parents=True)

            firmware_path = firmware_dir / "real-0.3q.bin"
            firmware_path.write_bytes(
                b"DIG.M\x00FT8\x00" + (145_950_000).to_bytes(4, "little") * 2 + bytes.fromhex("59 57 04 00")
            )

            digimanager_zip = digimanager_dir / "UVK5DigManager_v1.0.zip"
            with zipfile.ZipFile(digimanager_zip, "w") as archive:
                archive.writestr(
                    "UVK5DigManager.exe",
                    b"MZUVK5DigManager\x00FT4\x00FT8\x005957\x002237\x00UdpClient\x00SetCmdFreqMod\x00"
                    + bytes.fromhex("59 57 f4 00 59 57 08 00"),
                )

            replay_path = replay_dir / "ft4-replay.json"
            replay_path.write_text(
                json.dumps(
                    {
                        "source_capture": "ft4-only.pcapng",
                        "mode": "FT4",
                        "destination_host": "127.0.0.1",
                        "destination_port": 5957,
                        "packets": [
                            {"timestamp_offset_ms": 0, "dst_port": 5957, "payload_hex": "59 57 f4 00", "payload_len": 4, "tag": "business_packet"},
                            {"timestamp_offset_ms": 1000, "dst_port": 5957, "payload_hex": "59 57 04 00", "payload_len": 4, "tag": "ft4_mode_marker"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = analyze_reverse_targets(
                root,
                firmware_path=firmware_path,
                digimanager_path=digimanager_zip,
                replay_json_paths=[replay_path],
            )
            json_path, md_path = write_reverse_report(report, output_dir)
            json_exists = json_path.exists()
            md_exists = md_path.exists()
            md_text = md_path.read_text(encoding="utf-8")

        self.assertEqual(report["recommended_next_step"]["kind"], "static_anchor_review_then_targeted_dynamic")
        self.assertEqual(report["digital_mode_entry"]["status"], "candidate_firmware_strings_found")
        self.assertEqual(report["external_retune_capability"]["status"], "digimanager_looks_capable_of_external_retune")
        self.assertTrue(json_exists)
        self.assertTrue(md_exists)
        self.assertIn("lock_frequency_owner", md_text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
