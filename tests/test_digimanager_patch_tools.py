from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.digimanager_patch_tools import (  # noqa: E402
    HELPER_EXPECT,
    HELPER_REPLACE,
    SETDIGITALDATA2_MODE_PATCH_EXPECT,
    SETDIGITALDATA2_MODE_PATCH_REPLACE,
    UDPDATACHECK_LENGTH_PATCH_EXPECT,
    UDPDATACHECK_LENGTH_PATCH_REPLACE,
    UDPDATACHECK_PATCH_SITE_EXPECT,
    UDPDATACHECK_PATCH_SITE_REPLACE,
    _patch_setdigitaldata2_mode_hint,
    _write_method_code,
    _patch_confirmation_helper,
    _patch_udpdatacheck_ft4_forward_gate,
    _patch_udpdatacheck_variable_symbol_length,
)


class DigiManagerPatchToolsTests(unittest.TestCase):
    def test_udpdatacheck_gate_patch_rewrites_exact_compare_window(self) -> None:
        header = bytearray(b"\x13\x30\x07\x00") + (0x1E7).to_bytes(4, "little") + b"\x04\x00\x00\x11"
        code = bytearray(b"\x00" * 0x1E7)
        site_index = 0x0034 - 0x000C
        code[site_index : site_index + len(UDPDATACHECK_PATCH_SITE_EXPECT)] = UDPDATACHECK_PATCH_SITE_EXPECT
        binary = bytearray(header + code + b"\x00" * 0x200)

        class FakeMethod:
            token = "0x06000007"
            rva = 0x2208
            file_offset = 0
            header_size = 12
            code_size = 0x1E7
            max_size_until_next_method = 0x400
            body_header = bytes(header)
            code_bytes = bytes(code)
            tiny_header = False

        report = _patch_udpdatacheck_ft4_forward_gate(binary, FakeMethod())
        patched_code = bytes(binary[12 : 12 + 0x1E7])
        self.assertEqual(
            patched_code[site_index : site_index + len(UDPDATACHECK_PATCH_SITE_REPLACE)],
            UDPDATACHECK_PATCH_SITE_REPLACE,
        )
        self.assertEqual(report["name"], "udpdatacheck_ft4_forward_gate")
        self.assertEqual(report["replace_hex"], UDPDATACHECK_PATCH_SITE_REPLACE.hex(" "))

    def test_confirmation_helper_patch_rewrites_exact_tiny_method_body(self) -> None:
        binary = bytearray(bytes([0x42]) + HELPER_EXPECT + b"\x00" * 0x10)

        class FakeMethod:
            token = "0x06000019"
            rva = 0x31EC
            file_offset = 0
            header_size = 1
            code_size = len(HELPER_EXPECT)
            max_size_until_next_method = len(HELPER_EXPECT)
            body_header = b"\x42"
            code_bytes = HELPER_EXPECT
            tiny_header = True

        report = _patch_confirmation_helper(binary, FakeMethod())
        self.assertEqual(binary[0], 0x42)
        self.assertEqual(bytes(binary[1 : 1 + len(HELPER_REPLACE)]), HELPER_REPLACE)
        self.assertEqual(report["name"], "confirmation_helper_repurpose")

    def test_udpdatacheck_length_patch_reuses_payload_length_slot(self) -> None:
        header = bytearray(b"\x13\x30\x07\x00") + (0x1E7).to_bytes(4, "little") + b"\x04\x00\x00\x11"
        code = bytearray(b"\x00" * 0x1E7)
        site_index = 0x0090 - 0x000C
        code[site_index : site_index + len(UDPDATACHECK_LENGTH_PATCH_EXPECT)] = UDPDATACHECK_LENGTH_PATCH_EXPECT
        binary = bytearray(header + code + b"\x00" * 0x200)

        class FakeMethod:
            token = "0x06000007"
            rva = 0x2208
            file_offset = 0
            header_size = 12
            code_size = 0x1E7
            max_size_until_next_method = 0x400
            body_header = bytes(header)
            code_bytes = bytes(code)
            tiny_header = False

        report = _patch_udpdatacheck_variable_symbol_length(binary, FakeMethod())
        patched_code = bytes(binary[12 : 12 + 0x1E7])
        self.assertEqual(
            patched_code[site_index : site_index + len(UDPDATACHECK_LENGTH_PATCH_REPLACE)],
            UDPDATACHECK_LENGTH_PATCH_REPLACE,
        )
        self.assertEqual(report["name"], "udpdatacheck_variable_symbol_length")
        self.assertEqual(report["replace_hex"], UDPDATACHECK_LENGTH_PATCH_REPLACE.hex(" "))

    def test_setdigitaldata2_mode_patch_copies_arg1_into_header_byte2(self) -> None:
        header = bytearray(b"\x13\x30\x01\x00") + (0x3C).to_bytes(4, "little") + b"\x04\x00\x00\x11"
        code = bytearray(b"\x00" * 0x3C)
        site_index = 0x002B - 0x000C
        code[site_index : site_index + len(SETDIGITALDATA2_MODE_PATCH_EXPECT)] = SETDIGITALDATA2_MODE_PATCH_EXPECT
        binary = bytearray(header + code + b"\x00" * 0x40)

        class FakeMethod:
            token = "0x06000014"
            rva = 0x2AE8
            file_offset = 0
            header_size = 12
            code_size = 0x3C
            max_size_until_next_method = 0x80
            body_header = bytes(header)
            code_bytes = bytes(code)
            tiny_header = False

        report = _patch_setdigitaldata2_mode_hint(binary, FakeMethod())
        patched_code = bytes(binary[12 : 12 + 0x3C])
        self.assertEqual(
            patched_code[site_index : site_index + len(SETDIGITALDATA2_MODE_PATCH_REPLACE)],
            SETDIGITALDATA2_MODE_PATCH_REPLACE,
        )
        self.assertEqual(report["name"], "setdigitaldata2_mode_hint_from_length")
        self.assertEqual(report["replace_hex"], SETDIGITALDATA2_MODE_PATCH_REPLACE.hex(" "))

    def test_write_method_code_updates_tiny_header_size(self) -> None:
        image = bytearray(bytes([0x42]) + b"\x00" * 16 + b"\x00" * 4)

        class FakeMethod:
            file_offset = 0
            header_size = 1
            code_size = 16
            max_size_until_next_method = 20
            body_header = b"\x42"
            tiny_header = True
            token = "0x06000019"

        _write_method_code(image, FakeMethod(), b"\x2A" * 8)
        self.assertEqual(image[0], (8 << 2) | 0x2)
        self.assertEqual(bytes(image[1:9]), b"\x2A" * 8)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
