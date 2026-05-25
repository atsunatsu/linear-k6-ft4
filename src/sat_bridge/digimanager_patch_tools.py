from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import struct
from typing import Any

try:
    import dnfile  # type: ignore
except Exception:  # pragma: no cover
    dnfile = None


UDPDATACHECK_TOKEN = "0x06000007"
UDPDATACHECK_RVA = 0x2208
UDPDATACHECK_PATCH_SITE_IL_OFFSET = 0x0034
UDPDATACHECK_PATCH_SITE_EXPECT = bytes.fromhex("02 7b 0c 00 00 04 1e 33 6b")
UDPDATACHECK_PATCH_SITE_REPLACE = bytes.fromhex("02 14 28 19 00 00 06 2c 6b")
UDPDATACHECK_FALLTHROUGH_IL_OFFSET = 0x00A8
UDPDATACHECK_LENGTH_PATCH_IL_OFFSET = 0x0090
UDPDATACHECK_LENGTH_PATCH_EXPECT = bytes.fromhex("1f 4f")
UDPDATACHECK_LENGTH_PATCH_REPLACE = bytes.fromhex("04 00")

SETDIGITALDATA2_TOKEN = "0x06000014"
SETDIGITALDATA2_RVA = 0x2AE8
SETDIGITALDATA2_MODE_PATCH_IL_OFFSET = 0x002B
SETDIGITALDATA2_MODE_PATCH_EXPECT = bytes.fromhex("06 18 16 9c 06 19 16 9c 06 1a 03 9c")
SETDIGITALDATA2_MODE_PATCH_REPLACE = bytes.fromhex("06 18 03 9c 06 19 16 9c 06 1a 03 9c")

HELPER_TOKEN = "0x06000019"
HELPER_RVA = 0x31EC
HELPER_EXPECT = bytes.fromhex("03 72 e3 00 00 70 1a 28 5f 00 00 0a 1c fe 01 2a")
HELPER_REPLACE = bytes.fromhex("02 7b 0c 00 00 04 25 1a 2e 03 1e fe 01 2a 26 2a")

PATCHED_DIGIMANAGER_FILENAME = "patched-UVK5DigManager.exe"
PATCHED_DIGIMANAGER_DIAGNOSTIC_FILENAME = "patched-UVK5DigManager-diagnostic.exe"
PATCHED_DIGIMANAGER_DIAGNOSTIC_PROFILE_FILENAME = "patched-UVK5DigManager-diagnostic-profile.json"


@dataclass(slots=True)
class ManagedMethod:
    token: str
    rva: int
    file_offset: int
    header_size: int
    code_size: int
    max_size_until_next_method: int
    body_header: bytes
    code_bytes: bytes
    tiny_header: bool


def build_digimanager_patch_manifest(binary_path: Path) -> dict[str, Any]:
    method = load_managed_method(binary_path, UDPDATACHECK_TOKEN)
    helper = load_managed_method(binary_path, HELPER_TOKEN)
    sender = load_managed_method(binary_path, SETDIGITALDATA2_TOKEN)
    return {
        "source_sha256": sha256(binary_path.read_bytes()).hexdigest(),
        "source_binary": binary_path.name,
        "patch_kind": "ft4-forward-with-variable-length-and-mode-hint",
        "method_token": method.token,
        "method_rva": method.rva,
        "helper_token": helper.token,
        "helper_rva": helper.rva,
        "sender_token": sender.token,
        "sender_rva": sender.rva,
        "notes": [
            "Patch UDPDataCheck so protocol 4 reuses the existing protocol 8 forward path.",
            "Repurpose the currently unreferenced Confirmation method as a tiny bool helper that returns true for protocol 8 or protocol 4.",
            "Replace the hard-coded FT8 payload length of 79 symbols with the already-captured payload[4] value so FT4 can forward its longer symbol stream instead of being truncated.",
            "Patch SetDigitalData2 so the forwarded 5-byte header carries a second FT4/FT8 hint in byte[2] by mirroring the already-forwarded symbol count there. FT8 keeps its known-good 79-length path while FT4 no longer collapses into an all-zero mode field.",
        ],
        "patches": [
            {
                "name": "udpdatacheck_ft4_forward_gate",
                "enabled": True,
                "kind": "rewrite_gate_with_helper_call",
                "il_offset": UDPDATACHECK_PATCH_SITE_IL_OFFSET,
                "expect_hex": UDPDATACHECK_PATCH_SITE_EXPECT.hex(" "),
                "replace_hex": UDPDATACHECK_PATCH_SITE_REPLACE.hex(" "),
                "anchor_hint": "RecvProtocol == 8 compare in UDPDataCheck",
                "notes": "Replace the protocol-8-only branch with a helper call that returns true for protocol 8 or protocol 4.",
            },
            {
                "name": "confirmation_helper_repurpose",
                "enabled": True,
                "kind": "rewrite_unused_tiny_method",
                "il_offset": 0x0001,
                "expect_hex": HELPER_EXPECT.hex(" "),
                "replace_hex": HELPER_REPLACE.hex(" "),
                "anchor_hint": "Unreferenced Confirmation method body",
                "notes": "Turn Confirmation into a 16-byte helper: return (RecvProtocol == 4 || RecvProtocol == 8).",
            },
            {
                "name": "udpdatacheck_variable_symbol_length",
                "enabled": True,
                "kind": "reuse_payload_length_field",
                "il_offset": UDPDATACHECK_LENGTH_PATCH_IL_OFFSET,
                "expect_hex": UDPDATACHECK_LENGTH_PATCH_EXPECT.hex(" "),
                "replace_hex": UDPDATACHECK_LENGTH_PATCH_REPLACE.hex(" "),
                "anchor_hint": "Hard-coded 79-symbol length passed into SetDigitalData2",
                "notes": "Reuse the existing payload[4] value (already stored into method arg2) so FT8 keeps 79 while FT4 can forward its larger symbol count.",
            },
            {
                "name": "setdigitaldata2_mode_hint_from_length",
                "enabled": True,
                "kind": "reuse_header_byte2_for_mode_hint",
                "il_offset": SETDIGITALDATA2_MODE_PATCH_IL_OFFSET,
                "expect_hex": SETDIGITALDATA2_MODE_PATCH_EXPECT.hex(" "),
                "replace_hex": SETDIGITALDATA2_MODE_PATCH_REPLACE.hex(" "),
                "anchor_hint": "SetDigitalData2 writes zero into header byte[2]",
                "notes": "Mirror arg1 into header byte[2] while leaving byte[3] zero and byte[4] unchanged. This gives downstream code a visible FT4/FT8 discriminator without changing method size or the existing command 0x35 framing.",
            },
        ],
    }


def write_digimanager_patch_manifest(binary_path: Path, output_path: Path) -> Path:
    manifest = build_digimanager_patch_manifest(binary_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def apply_digimanager_patch_manifest(binary_path: Path, manifest_path: Path, output_path: Path) -> dict[str, Any]:
    if dnfile is None:
        raise RuntimeError("dnfile is required to patch UVK5DigManager.exe")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_sha = sha256(binary_path.read_bytes()).hexdigest()
    if manifest.get("source_sha256") and manifest["source_sha256"] != source_sha:
        raise ValueError("Source DigiManager SHA256 does not match the manifest.")

    enabled = [item for item in manifest.get("patches", []) if item.get("enabled")]
    if not enabled:
        raise ValueError("No enabled DigiManager patches found in the manifest.")

    image = bytearray(binary_path.read_bytes())
    method = load_managed_method(binary_path, UDPDATACHECK_TOKEN)
    helper = load_managed_method(binary_path, HELPER_TOKEN)
    sender = load_managed_method(binary_path, SETDIGITALDATA2_TOKEN)

    patch_reports = [
        _patch_udpdatacheck_ft4_forward_gate(image, method),
        _patch_confirmation_helper(image, helper),
        _patch_udpdatacheck_variable_symbol_length(image, method),
        _patch_setdigitaldata2_mode_hint(image, sender),
    ]

    patched_bytes = bytes(image)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(patched_bytes)

    return {
        "source_binary": str(binary_path),
        "manifest": str(manifest_path),
        "output_binary": str(output_path),
        "source_sha256": source_sha,
        "output_sha256": sha256(patched_bytes).hexdigest(),
        "applied_patches": patch_reports,
    }


def load_managed_method(binary_path: Path, token: str) -> ManagedMethod:
    if dnfile is None:
        raise RuntimeError("dnfile is required to inspect UVK5DigManager.exe")

    pe = dnfile.dnPE(str(binary_path))
    method_index = int(token, 16) - 0x06000000
    row = pe.net.mdtables.MethodDef.rows[method_index - 1]
    rva = int(row.Rva)
    file_offset = int(pe.get_offset_from_rva(rva))
    next_rvas = [
        int(other.Rva)
        for other in pe.net.mdtables.MethodDef.rows
        if getattr(other, "Rva", 0) and int(other.Rva) > rva
    ]
    next_rva = min(next_rvas) if next_rvas else len(pe.get_memory_mapped_image())

    image = binary_path.read_bytes()
    first_byte = image[file_offset]
    tiny_header = (first_byte & 0x3) == 0x2
    if tiny_header:
        header_size = 1
        code_size = first_byte >> 2
        body_header = image[file_offset : file_offset + header_size]
    else:
        flags_size = int.from_bytes(image[file_offset : file_offset + 2], "little")
        header_dwords = (flags_size >> 12) & 0xF
        header_size = header_dwords * 4
        code_size = int.from_bytes(image[file_offset + 4 : file_offset + 8], "little")
        body_header = image[file_offset : file_offset + header_size]
    code_bytes = image[file_offset + header_size : file_offset + header_size + code_size]
    max_size_until_next_method = int(pe.get_offset_from_rva(next_rva) - file_offset - header_size)
    return ManagedMethod(
        token=token,
        rva=rva,
        file_offset=file_offset,
        header_size=header_size,
        code_size=code_size,
        max_size_until_next_method=max_size_until_next_method,
        body_header=body_header,
        code_bytes=code_bytes,
        tiny_header=tiny_header,
    )


def _patch_udpdatacheck_ft4_forward_gate(image: bytearray, method: ManagedMethod) -> dict[str, Any]:
    code = bytearray(method.code_bytes)
    code_start_il = method.header_size
    site_index = UDPDATACHECK_PATCH_SITE_IL_OFFSET - code_start_il
    actual = bytes(code[site_index : site_index + len(UDPDATACHECK_PATCH_SITE_EXPECT)])
    if actual != UDPDATACHECK_PATCH_SITE_EXPECT:
        raise ValueError(
            "UDPDataCheck patch site no longer matches expected bytes: "
            f"expected={UDPDATACHECK_PATCH_SITE_EXPECT.hex(' ')} actual={actual.hex(' ')}"
        )

    code[site_index : site_index + len(UDPDATACHECK_PATCH_SITE_EXPECT)] = UDPDATACHECK_PATCH_SITE_REPLACE
    _write_method_code(image, method, code)
    return {
        "name": "udpdatacheck_ft4_forward_gate",
        "method_token": method.token,
        "method_rva": method.rva,
        "patch_site_il_offset": UDPDATACHECK_PATCH_SITE_IL_OFFSET,
        "expect_hex": UDPDATACHECK_PATCH_SITE_EXPECT.hex(" "),
        "replace_hex": UDPDATACHECK_PATCH_SITE_REPLACE.hex(" "),
        "notes": "Replace the protocol-8-only test with a call into the repurposed helper and branch to the original fallthrough when false.",
    }


def _patch_confirmation_helper(image: bytearray, method: ManagedMethod) -> dict[str, Any]:
    actual = bytes(method.code_bytes)
    if actual != HELPER_EXPECT:
        raise ValueError(
            "Confirmation helper body no longer matches expected bytes: "
            f"expected={HELPER_EXPECT.hex(' ')} actual={actual.hex(' ')}"
        )

    _write_method_code(image, method, HELPER_REPLACE)
    return {
        "name": "confirmation_helper_repurpose",
        "method_token": method.token,
        "method_rva": method.rva,
        "patch_site_il_offset": 0x0001,
        "expect_hex": HELPER_EXPECT.hex(" "),
        "replace_hex": HELPER_REPLACE.hex(" "),
        "notes": "Repurpose the currently unreferenced Confirmation method so it returns true for protocol 4 or 8.",
    }


def _patch_udpdatacheck_variable_symbol_length(image: bytearray, method: ManagedMethod) -> dict[str, Any]:
    code = bytearray(method.code_bytes)
    code_start_il = method.header_size
    site_index = UDPDATACHECK_LENGTH_PATCH_IL_OFFSET - code_start_il
    actual = bytes(code[site_index : site_index + len(UDPDATACHECK_LENGTH_PATCH_EXPECT)])
    if actual != UDPDATACHECK_LENGTH_PATCH_EXPECT:
        raise ValueError(
            "UDPDataCheck length patch site no longer matches expected bytes: "
            f"expected={UDPDATACHECK_LENGTH_PATCH_EXPECT.hex(' ')} actual={actual.hex(' ')}"
        )

    code[site_index : site_index + len(UDPDATACHECK_LENGTH_PATCH_EXPECT)] = UDPDATACHECK_LENGTH_PATCH_REPLACE
    _write_method_code(image, method, code)
    return {
        "name": "udpdatacheck_variable_symbol_length",
        "method_token": method.token,
        "method_rva": method.rva,
        "patch_site_il_offset": UDPDATACHECK_LENGTH_PATCH_IL_OFFSET,
        "expect_hex": UDPDATACHECK_LENGTH_PATCH_EXPECT.hex(" "),
        "replace_hex": UDPDATACHECK_LENGTH_PATCH_REPLACE.hex(" "),
        "notes": "Replace the hard-coded 79-symbol length with ldarg.2/nop so the sender uses payload[4] as the forwarded symbol count.",
    }


def _patch_setdigitaldata2_mode_hint(image: bytearray, method: ManagedMethod) -> dict[str, Any]:
    code = bytearray(method.code_bytes)
    code_start_il = method.header_size
    site_index = SETDIGITALDATA2_MODE_PATCH_IL_OFFSET - code_start_il
    actual = bytes(code[site_index : site_index + len(SETDIGITALDATA2_MODE_PATCH_EXPECT)])
    if actual != SETDIGITALDATA2_MODE_PATCH_EXPECT:
        raise ValueError(
            "SetDigitalData2 mode-hint patch site no longer matches expected bytes: "
            f"expected={SETDIGITALDATA2_MODE_PATCH_EXPECT.hex(' ')} actual={actual.hex(' ')}"
        )

    code[site_index : site_index + len(SETDIGITALDATA2_MODE_PATCH_EXPECT)] = SETDIGITALDATA2_MODE_PATCH_REPLACE
    _write_method_code(image, method, code)
    return {
        "name": "setdigitaldata2_mode_hint_from_length",
        "method_token": method.token,
        "method_rva": method.rva,
        "patch_site_il_offset": SETDIGITALDATA2_MODE_PATCH_IL_OFFSET,
        "expect_hex": SETDIGITALDATA2_MODE_PATCH_EXPECT.hex(" "),
        "replace_hex": SETDIGITALDATA2_MODE_PATCH_REPLACE.hex(" "),
        "notes": "Replace header byte[2]=0 with header byte[2]=arg1 so FT4 carries a downstream-visible mode hint while preserving byte[3]=0 and byte[4]=arg1.",
    }


def _write_method_code(image: bytearray, method: ManagedMethod, new_code: bytes | bytearray) -> None:
    if len(new_code) > method.max_size_until_next_method:
        raise ValueError(
            f"Patched method {method.token} would overlap the next managed method: "
            f"new_code={len(new_code)} max={method.max_size_until_next_method}"
        )

    start = method.file_offset
    if method.tiny_header:
        if len(new_code) > 63:
            raise ValueError("Tiny managed method cannot exceed 63 bytes.")
        image[start] = ((len(new_code) << 2) | 0x2) & 0xFF
    else:
        new_header = bytearray(method.body_header)
        new_header[4:8] = struct.pack("<I", len(new_code))
        image[start : start + method.header_size] = new_header

    code_start = start + method.header_size
    image[code_start : code_start + len(new_code)] = new_code
    if len(new_code) < method.code_size:
        image[code_start + len(new_code) : code_start + method.code_size] = b"\x00" * (method.code_size - len(new_code))
