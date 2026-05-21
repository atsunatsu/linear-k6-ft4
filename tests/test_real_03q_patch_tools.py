from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.real_03q_patch_tools import (  # noqa: E402
    apply_patch_manifest,
    build_patch_workspace,
    repack_uvk5_packed_firmware,
)
from sat_bridge.reverse_tools import try_unpack_uvk5_packed_firmware


class Real03qPatchToolsTests(unittest.TestCase):
    def test_repack_uvk5_packed_firmware_round_trips_raw_bytes(self) -> None:
        raw = bytes(range(256)) * 40
        packed = repack_uvk5_packed_firmware(raw, "CEC_0.3QP1")
        unpacked = try_unpack_uvk5_packed_firmware(packed)

        self.assertTrue(unpacked["ok"])
        self.assertTrue(unpacked["crc_ok"])
        self.assertEqual(unpacked["embedded_version"], "CEC_0.3QP1")
        self.assertEqual(unpacked["raw_bytes"], raw)

    def test_build_patch_workspace_emits_anchor_manifest_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            firmware_path = Path(tmp_dir) / "real-0.3q.packed.bin"
            raw = bytearray(b"\x00" * 70000)
            raw[56096:56106] = b" CEC_0.3Q\x00"
            raw[57462:57468] = b"DIG.M\x00"
            raw[60286:60299] = b"FREQ:%u.%05u"
            raw[60299:60300] = b"\x00"
            raw[60532:60537] = b"DIG+\x00"
            firmware_path.write_bytes(repack_uvk5_packed_firmware(bytes(raw), "*KD8CEC_FROM_SOU"))

            workspace = build_patch_workspace(firmware_path)

        self.assertEqual(workspace.embedded_version, "*KD8CEC_FROM_SOU")
        self.assertTrue(any(anchor["text"] == "DIG.M" for anchor in workspace.anchors))
        self.assertEqual(workspace.manifest_template["patches"][0]["name"], "digital_mode_retune_gate_candidate")

    def test_apply_patch_manifest_updates_ascii_banner_and_repackages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            firmware_path = tmp / "real-0.3q.packed.bin"
            raw = bytearray(b"\x00" * 70000)
            raw[56096:56106] = b" CEC_0.3Q\x00"
            firmware_path.write_bytes(repack_uvk5_packed_firmware(bytes(raw), "*KD8CEC_FROM_SOU"))

            manifest = {
                "source_firmware_sha256": __import__("hashlib").sha256(firmware_path.read_bytes()).hexdigest(),
                "source_embedded_version": "*KD8CEC_FROM_SOU",
                "output_embedded_version": "CEC_0.3QP1",
                "patches": [
                    {
                        "name": "patched_version_banner",
                        "enabled": True,
                        "kind": "replace_ascii",
                        "offset": 56096,
                        "expect_ascii": " CEC_0.3Q",
                        "replace_ascii": " CEC_3QPB",
                    }
                ],
            }
            manifest_path = tmp / "patch.json"
            output_path = tmp / "patched.packed.bin"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = apply_patch_manifest(firmware_path, manifest_path, output_path)
            unpacked = try_unpack_uvk5_packed_firmware(output_path.read_bytes())
            output_exists = output_path.exists()

        self.assertEqual(report["output_embedded_version"], "CEC_0.3QP1")
        self.assertTrue(output_exists)
        self.assertEqual(unpacked["embedded_version"], "CEC_0.3QP1")
        self.assertIn(b" CEC_3QPB", unpacked["raw_bytes"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
