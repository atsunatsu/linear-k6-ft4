from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import binascii
import json
from pathlib import Path
import re
import struct
from typing import Any
import zipfile

from sat_bridge.dynamic_reverse_tools import analyze_dynamic_lock_behavior

try:
    import dnfile  # type: ignore
    from dncil.cil.body.reader import read_method_body_from_bytes  # type: ignore
except Exception:  # pragma: no cover - optional dependency on some machines
    dnfile = None
    read_method_body_from_bytes = None


INTERESTING_KEYWORDS = [
    "DIG",
    "DIG.M",
    "DIGI",
    "DIGITAL",
    "FT4",
    "FT8",
    "WSJT",
    "BK4819",
    "UART",
    "AIRCOPY",
    "LOCK",
    "FREQ",
    "FREQUENCY",
    "CEC",
    "VOX",
    "UDP",
    "5957",
    "2237",
    "4532",
]

PORT_HINTS = [2237, 4532, 5957]
MARKER_PATTERNS = {
    "business_packet": bytes.fromhex("59 57 f4 00"),
    "ft4_mode_marker": bytes.fromhex("59 57 04 00"),
    "ft8_mode_marker": bytes.fromhex("59 57 08 00"),
}

PACK_OBFUSCATION = bytes(
    [
        0x47, 0x22, 0xC0, 0x52, 0x5D, 0x57, 0x48, 0x94, 0xB1, 0x60, 0x60, 0xDB, 0x6F, 0xE3, 0x4C, 0x7C,
        0xD8, 0x4A, 0xD6, 0x8B, 0x30, 0xEC, 0x25, 0xE0, 0x4C, 0xD9, 0x00, 0x7F, 0xBF, 0xE3, 0x54, 0x05,
        0xE9, 0x3A, 0x97, 0x6B, 0xB0, 0x6E, 0x0C, 0xFB, 0xB1, 0x1A, 0xE2, 0xC9, 0xC1, 0x56, 0x47, 0xE9,
        0xBA, 0xF1, 0x42, 0xB6, 0x67, 0x5F, 0x0F, 0x96, 0xF7, 0xC9, 0x3C, 0x84, 0x1B, 0x26, 0xE1, 0x4E,
        0x3B, 0x6F, 0x66, 0xE6, 0xA0, 0x6A, 0xB0, 0xBF, 0xC6, 0xA5, 0x70, 0x3A, 0xBA, 0x18, 0x9E, 0x27,
        0x1A, 0x53, 0x5B, 0x71, 0xB1, 0x94, 0x1E, 0x18, 0xF2, 0xD6, 0x81, 0x02, 0x22, 0xFD, 0x5A, 0x28,
        0x91, 0xDB, 0xBA, 0x5D, 0x64, 0xC6, 0xFE, 0x86, 0x83, 0x9C, 0x50, 0x1C, 0x73, 0x03, 0x11, 0xD6,
        0xAF, 0x30, 0xF4, 0x2C, 0x77, 0xB2, 0x7D, 0xBB, 0x3F, 0x29, 0x28, 0x57, 0x22, 0xD6, 0x92, 0x8B,
    ]
)

REFERENCE_FUNCTION_NAMES = [
    "BK4819_SetFrequency",
    "RADIO_SetTxParameters",
    "BK4819_PrepareTransmit",
    "BK4819_SendFSKData",
    "UART_HandleCommand",
]

REFERENCE_UART_COMMAND_RE = re.compile(r"0x[0-9A-Fa-f]{4}")
STRING_LITERAL_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')


@dataclass(slots=True)
class AssetSelection:
    firmware: Path | None
    digimanager: Path | None
    replay_jsons: list[Path]


def find_reverse_assets(root: Path) -> AssetSelection:
    firmware_dir = root / "reverse" / "input" / "firmware"
    digimanager_dir = root / "reverse" / "input" / "digimanager"
    replay_dir = root / "samples" / "replay"

    firmware = _pick_first(firmware_dir, ["*.bin"]) or _pick_first(root, ["*0.3q*.bin", "*0.3Q*.bin", "*.packed.bin"])
    digimanager = _pick_first(digimanager_dir, ["*.zip", "*.exe"]) or _pick_first(root, ["*DigManager*.zip", "*DigManager*.exe", "*UVK5DigManager*.exe"])
    replay_jsons = sorted(replay_dir.glob("*.json")) if replay_dir.exists() else []

    return AssetSelection(firmware=firmware, digimanager=digimanager, replay_jsons=replay_jsons)


def analyze_reverse_targets(
    root: Path,
    *,
    firmware_path: Path | None = None,
    digimanager_path: Path | None = None,
    replay_json_paths: list[Path] | None = None,
) -> dict[str, Any]:
    replay_paths = replay_json_paths if replay_json_paths is not None else find_reverse_assets(root).replay_jsons

    firmware_summary = analyze_firmware_bin(firmware_path) if firmware_path else _missing_asset("firmware_bin")
    digimanager_summary = analyze_digimanager_binary(digimanager_path) if digimanager_path else _missing_asset("digimanager_binary")
    auxiliary_summary = analyze_auxiliary_replays(replay_paths)
    reference_summary = analyze_public_source_reference(root / "uvk5cec-0.3q")
    dynamic_summary = analyze_dynamic_lock_behavior(root)

    report = {
        "inputs": {
            "firmware_bin": str(firmware_path) if firmware_path else None,
            "digimanager_binary": str(digimanager_path) if digimanager_path else None,
            "replay_jsons": [str(path) for path in replay_paths],
        },
        "firmware": firmware_summary,
        "digimanager": digimanager_summary,
        "auxiliary_replays": auxiliary_summary,
        "public_source_reference": reference_summary,
        "dynamic_validation": dynamic_summary,
    }
    report["digital_mode_entry"] = _infer_digital_mode_entry(report)
    report["frequency_set_call_chain"] = _infer_frequency_set_call_chain(report)
    report["lock_frequency_owner"] = _infer_lock_frequency_owner(report)
    report["external_retune_capability"] = _infer_external_retune_capability(report)
    report["ft4_tx_gate"] = _infer_ft4_tx_gate(report)
    report["recommended_next_step"] = _recommend_next_step(report)
    report["digimanager_continuous_retune"] = dynamic_summary.get("digimanager_continuous_retune", "unclear")
    report["firmware_applies_retune_in_digital_mode"] = dynamic_summary.get("firmware_applies_retune_in_digital_mode", "unclear")
    report["lock_owner"] = dynamic_summary.get("lock_owner", "still_unclear")
    return report


def analyze_firmware_bin(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    is_packed_candidate = path.name.lower().endswith(".packed.bin") or ".packed." in path.name.lower()
    unpacked = try_unpack_uvk5_packed_firmware(data) if is_packed_candidate else None
    analysis_bytes = unpacked["raw_bytes"] if unpacked and unpacked.get("ok") else data

    ascii_strings = extract_ascii_strings(analysis_bytes)
    utf16_strings = extract_utf16le_strings(analysis_bytes)
    keyword_hits = _collect_keyword_hits(ascii_strings + utf16_strings)
    keyword_offsets = collect_keyword_offsets(analysis_bytes)
    frequency_literals = scan_frequency_literals(analysis_bytes)
    marker_counts = {name: analysis_bytes.count(pattern) for name, pattern in MARKER_PATTERNS.items()}

    return {
        "kind": "firmware_bin",
        "path": str(path),
        "present": True,
        "is_packed_candidate": is_packed_candidate,
        "size_bytes": len(data),
        "sha256": sha256(data).hexdigest(),
        "unpack": {
            "attempted": bool(is_packed_candidate),
            "ok": bool(unpacked and unpacked.get("ok")),
            "embedded_version": unpacked.get("embedded_version") if unpacked else None,
            "crc_ok": unpacked.get("crc_ok") if unpacked else None,
            "raw_size_bytes": len(analysis_bytes),
        },
        "interesting_strings": keyword_hits,
        "interesting_string_offsets": keyword_offsets,
        "frequency_literals_hz": frequency_literals,
        "frequency_literal_reliability": "normal" if unpacked and unpacked.get("ok") else ("low" if is_packed_candidate else "normal"),
        "marker_counts": marker_counts,
        "command_id_byte_hits": {
            "0514": analysis_bytes.count(bytes.fromhex("14 05")),
            "052f": analysis_bytes.count(bytes.fromhex("2f 05")),
            "2237": analysis_bytes.count(struct.pack("<I", 2237)),
            "4532": analysis_bytes.count(struct.pack("<I", 4532)),
            "5957": analysis_bytes.count(struct.pack("<I", 5957)),
        },
    }


def analyze_digimanager_binary(path: Path) -> dict[str, Any]:
    container_kind = path.suffix.lower().lstrip(".")
    if path.suffix.lower() == ".zip":
        exe_name, exe_data = _load_first_exe_from_zip(path)
        payload_path = f"{path}!/{exe_name}" if exe_name else str(path)
        container_kind = "zip"
    else:
        exe_name = path.name
        exe_data = path.read_bytes()
        payload_path = str(path)
        container_kind = "exe"

    ascii_strings = extract_ascii_strings(exe_data)
    utf16_strings = extract_utf16le_strings(exe_data)
    keyword_hits = _collect_keyword_hits(ascii_strings + utf16_strings)
    keyword_offsets = collect_keyword_offsets(exe_data)
    imports = parse_pe_imports(exe_data)
    marker_counts = {name: exe_data.count(pattern) for name, pattern in MARKER_PATTERNS.items()}
    string_keys = {value.lower() for value in keyword_hits}
    has_udp_string_hint = any(hint in string_keys for hint in {"udpclient", "udpreceiver", "frmudprecv", "setcmdfreqmod", "targetfreq", "sendsubfreq"})
    has_serial_string_hint = any(hint in string_keys for hint in {"serialport", "createfile", "setcommstate"})
    is_managed_dotnet = "mscoree.dll" in {name.lower() for name in imports}

    return {
        "kind": "digimanager_binary",
        "path": str(path),
        "payload_path": payload_path,
        "present": True,
        "container_kind": container_kind,
        "exe_name": exe_name,
        "size_bytes": len(exe_data),
        "sha256": sha256(exe_data).hexdigest(),
        "interesting_strings": keyword_hits,
        "interesting_string_offsets": keyword_offsets,
        "port_mentions": {str(port): _count_number_mentions(ascii_strings + utf16_strings, str(port)) for port in PORT_HINTS},
        "marker_counts": marker_counts,
        "imports": imports,
        "api_hints": {
            "has_udp_api": _imports_contain(imports, ["sendto", "recvfrom", "WSASendTo", "WSARecvFrom"]) or has_udp_string_hint,
            "has_serial_api": _imports_contain(imports, ["CreateFileA", "CreateFileW", "WriteFile", "ReadFile", "SetCommState"]) or has_serial_string_hint,
            "is_managed_dotnet": is_managed_dotnet,
        },
        "managed_behavior": analyze_digimanager_managed_behavior(path if path.suffix.lower() == ".exe" else None, exe_data),
    }


def analyze_auxiliary_replays(paths: list[Path]) -> dict[str, Any]:
    if not paths:
        return {"present": False, "files": []}

    files: list[dict[str, Any]] = []
    shared_prefixes: set[str] | None = None
    unique_by_file: dict[str, list[str]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        packet_prefixes = Counter(_prefix_from_packet(packet["payload_hex"]) for packet in payload.get("packets", []))
        files.append(
            {
                "path": str(path),
                "mode": payload.get("mode"),
                "destination_port": payload.get("destination_port"),
                "packet_count": len(payload.get("packets", [])),
                "prefix_counts": dict(packet_prefixes),
                "tags": sorted({packet.get("tag") for packet in payload.get("packets", [])}),
            }
        )
        prefixes = set(packet_prefixes)
        shared_prefixes = prefixes if shared_prefixes is None else shared_prefixes & prefixes

    for file_summary in files:
        prefixes = set(file_summary["prefix_counts"])
        unique_by_file[Path(file_summary["path"]).name] = sorted(prefixes - (shared_prefixes or set()))

    return {
        "present": True,
        "files": files,
        "shared_prefixes": sorted(shared_prefixes or set()),
        "unique_prefixes_by_file": unique_by_file,
    }


def analyze_public_source_reference(source_root: Path) -> dict[str, Any]:
    if not source_root.exists():
        return {"present": False}

    function_hits: dict[str, list[str]] = defaultdict(list)
    command_ids: Counter[str] = Counter()
    interesting_strings: Counter[str] = Counter()

    for path in source_root.rglob("*.[ch]"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = str(path.relative_to(source_root))
        for function_name in REFERENCE_FUNCTION_NAMES:
            if function_name in text:
                function_hits[function_name].append(relative_path)
        if path.name == "uart.c":
            for match in REFERENCE_UART_COMMAND_RE.findall(text):
                command_ids[match.lower()] += 1
        for string_match in STRING_LITERAL_RE.findall(text):
            for keyword in INTERESTING_KEYWORDS:
                if keyword in string_match.upper():
                    interesting_strings[string_match] += 1
                    break

    return {
        "present": True,
        "reference_function_hits": {name: paths for name, paths in sorted(function_hits.items())},
        "uart_command_id_counts": dict(command_ids),
        "interesting_string_literals": dict(interesting_strings.most_common(20)),
    }


def render_reverse_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Real 0.3q Reverse Map",
        "",
        "## Inputs",
        f"- firmware bin: {report['inputs']['firmware_bin'] or 'missing'}",
        f"- DigiManager binary: {report['inputs']['digimanager_binary'] or 'missing'}",
        f"- replay JSONs: {', '.join(report['inputs']['replay_jsons']) if report['inputs']['replay_jsons'] else 'none'}",
        "",
        "## digital_mode_entry",
        f"- status: {report['digital_mode_entry']['status']}",
        f"- summary: {report['digital_mode_entry']['summary']}",
        "- evidence:",
    ]
    lines.extend(f"  - {item}" for item in report["digital_mode_entry"]["evidence"])
    lines.extend(
        [
            "",
            "## frequency_set_call_chain",
            f"- status: {report['frequency_set_call_chain']['status']}",
            f"- summary: {report['frequency_set_call_chain']['summary']}",
            "- evidence:",
        ]
    )
    lines.extend(f"  - {item}" for item in report["frequency_set_call_chain"]["evidence"])
    lines.extend(
        [
            "",
            "## lock_frequency_owner",
            f"- status: {report['lock_frequency_owner']['status']}",
            f"- summary: {report['lock_frequency_owner']['summary']}",
            "- evidence:",
        ]
    )
    lines.extend(f"  - {item}" for item in report["lock_frequency_owner"]["evidence"])
    lines.extend(
        [
            "",
            "## external_retune_capability",
            f"- status: {report['external_retune_capability']['status']}",
            f"- summary: {report['external_retune_capability']['summary']}",
            "- evidence:",
        ]
    )
    lines.extend(f"  - {item}" for item in report["external_retune_capability"]["evidence"])
    lines.extend(
        [
            "",
            "## ft4_tx_gate",
            f"- status: {report['ft4_tx_gate']['status']}",
            f"- summary: {report['ft4_tx_gate']['summary']}",
            "- evidence:",
        ]
    )
    lines.extend(f"  - {item}" for item in report["ft4_tx_gate"]["evidence"])
    lines.extend(
        [
            "",
            "## dynamic_validation",
            f"- digimanager_continuous_retune: {report.get('digimanager_continuous_retune', 'unclear')}",
            f"- firmware_applies_retune_in_digital_mode: {report.get('firmware_applies_retune_in_digital_mode', 'unclear')}",
            f"- lock_owner: {report.get('lock_owner', 'still_unclear')}",
            "",
            "## recommended_next_step",
            f"- kind: {report['recommended_next_step']['kind']}",
            f"- reason: {report['recommended_next_step']['reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_reverse_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "reverse-map.json"
    md_path = output_dir / "reverse-map.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_reverse_markdown(report), encoding="utf-8")
    return json_path, md_path


def extract_ascii_strings(data: bytes, *, min_length: int = 4) -> list[str]:
    strings: list[str] = []
    current: list[str] = []
    for byte in data:
        if 32 <= byte <= 126:
            current.append(chr(byte))
            continue
        if len(current) >= min_length:
            strings.append("".join(current))
        current = []
    if len(current) >= min_length:
        strings.append("".join(current))
    return strings


def extract_utf16le_strings(data: bytes, *, min_length: int = 4) -> list[str]:
    strings: list[str] = []
    current: list[str] = []
    for index in range(0, len(data) - 1, 2):
        first = data[index]
        second = data[index + 1]
        if second == 0 and 32 <= first <= 126:
            current.append(chr(first))
            continue
        if len(current) >= min_length:
            strings.append("".join(current))
        current = []
    if len(current) >= min_length:
        strings.append("".join(current))
    return strings


def collect_keyword_offsets(data: bytes, *, limit: int = 40) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for text, offset in _iter_ascii_strings_with_offsets(data):
        upper_text = text.upper()
        for keyword in INTERESTING_KEYWORDS:
            if keyword in upper_text:
                hits.append({"text": text, "offset": offset, "encoding": "ascii"})
                break
    for text, offset in _iter_utf16_strings_with_offsets(data):
        upper_text = text.upper()
        for keyword in INTERESTING_KEYWORDS:
            if keyword in upper_text:
                hits.append({"text": text, "offset": offset, "encoding": "utf16le"})
                break
    return hits[:limit]


def scan_frequency_literals(data: bytes) -> list[dict[str, int]]:
    counts: Counter[int] = Counter()
    for index in range(0, len(data) - 3):
        value = struct.unpack_from("<I", data, index)[0]
        if 10_000_000 <= value <= 1_000_000_000:
            counts[value] += 1
    return [{"value_hz": value, "count": count} for value, count in counts.most_common(12) if count >= 2]


def try_unpack_uvk5_packed_firmware(data: bytes) -> dict[str, Any]:
    if len(data) < 0x2010 + 2:
        return {"ok": False, "reason": "file_too_small"}

    packed = data[:-2]
    expected_crc = struct.unpack("<H", data[-2:])[0]
    actual_crc = binascii.crc_hqx(packed, 0)

    deobfuscated = bytes(byte ^ PACK_OBFUSCATION[index % len(PACK_OBFUSCATION)] for index, byte in enumerate(packed))
    embedded_version_raw = deobfuscated[0x2000:0x2010]
    embedded_version = embedded_version_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
    raw_bytes = deobfuscated[:0x2000] + deobfuscated[0x2010:]

    return {
        "ok": True,
        "crc_ok": expected_crc == actual_crc,
        "embedded_version": embedded_version,
        "raw_bytes": raw_bytes,
    }


def analyze_digimanager_managed_behavior(path: Path | None, exe_data: bytes) -> dict[str, Any]:
    if dnfile is None or read_method_body_from_bytes is None:
        return {"available": False, "reason": "dnfile_or_dncil_missing"}

    try:
        pe = dnfile.dnPE(name=str(path) if path else "memory.exe", data=exe_data)
        method_texts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for index, row in enumerate(pe.net.mdtables.MethodDef.rows, start=1):
            if not row.Rva:
                continue
            try:
                body = read_method_body_from_bytes(pe.get_data(row.Rva, 4096))
            except Exception:
                continue
            rendered = "\n".join(
                f"{ins.offset:04x} {ins.opcode} {ins.operand}"
                for ins in body.instructions
            )
            method_texts[str(row.Name)].append(
                {
                    "token": f"0x{0x06000000 + index:08x}",
                    "rva": row.Rva,
                    "text": rendered,
                }
            )

        protocol_8_forwarded = False
        protocol_244_forwarded = False
        protocol_4_forwarded = False
        protocol_compare_values: list[int] = []

        for item in method_texts.get("UDPDataCheck", []):
            lines = item["text"].splitlines()
            compare_blocks: list[tuple[int, int]] = []
            for idx, line in enumerate(lines):
                if "ldfld token(0x0400000C)" not in line:
                    continue
                compare_value = None
                for probe in lines[idx + 1 : idx + 5]:
                    if "ldc.i4.8" in probe:
                        compare_value = 8
                        break
                    if "ldc.i4.s 123" in probe:
                        compare_value = 123
                        break
                    if "ldc.i4.s 121" in probe:
                        compare_value = 121
                        break
                    if "ldc.i4 244" in probe:
                        compare_value = 244
                        break
                    if "ldc.i4.4" in probe:
                        compare_value = 4
                        break
                if compare_value is not None:
                    compare_blocks.append((idx, compare_value))
                    protocol_compare_values.append(compare_value)

            for block_index, (start_idx, compare_value) in enumerate(compare_blocks):
                end_idx = compare_blocks[block_index + 1][0] if block_index + 1 < len(compare_blocks) else len(lines)
                block_text = "\n".join(lines[start_idx:end_idx])
                if compare_value == 8 and "call token(0x06000014)" in block_text:
                    protocol_8_forwarded = True
                if compare_value == 244 and "call token(0x06000012)" in block_text:
                    protocol_244_forwarded = True
                if compare_value == 4 and "call token(0x06000014)" in block_text:
                    protocol_4_forwarded = True
        protocol_4_seen_in_ui = any(
            "ldfld token(0x0400000C)" in item["text"] and "ldc.i4.4" in item["text"]
            for item in method_texts.get("tmrRecv_Tick", [])
        )

        return {
            "available": True,
            "udpdatacheck_methods": [
                {"token": item["token"], "rva": item["rva"]}
                for item in method_texts.get("UDPDataCheck", [])
            ],
            "tmrrecv_methods": [
                {"token": item["token"], "rva": item["rva"]}
                for item in method_texts.get("tmrRecv_Tick", [])
            ],
            "protocol_8_forwarded": protocol_8_forwarded,
            "protocol_244_forwarded": protocol_244_forwarded,
            "protocol_4_forwarded": protocol_4_forwarded,
            "protocol_4_seen_in_ui": protocol_4_seen_in_ui,
            "protocol_compare_values": protocol_compare_values,
        }
    except Exception as exc:
        return {"available": False, "reason": f"managed_parse_failed:{exc.__class__.__name__}"}


def parse_pe_imports(data: bytes) -> dict[str, list[str]]:
    try:
        if data[:2] != b"MZ":
            return {}
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_offset : pe_offset + 4] != b"PE\x00\x00":
            return {}
        number_of_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
        optional_header_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
        optional_offset = pe_offset + 24
        magic = struct.unpack_from("<H", data, optional_offset)[0]
        if magic == 0x10B:
            data_directory_offset = optional_offset + 96
        elif magic == 0x20B:
            data_directory_offset = optional_offset + 112
        else:
            return {}
        import_rva, import_size = struct.unpack_from("<II", data, data_directory_offset + 8)
        if not import_rva or not import_size:
            return {}

        section_offset = optional_offset + optional_header_size
        sections = []
        for section_index in range(number_of_sections):
            entry_offset = section_offset + (40 * section_index)
            name = data[entry_offset : entry_offset + 8].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
            virtual_size, virtual_address, raw_size, raw_ptr = struct.unpack_from("<IIII", data, entry_offset + 8)
            sections.append(
                {
                    "name": name,
                    "virtual_size": virtual_size,
                    "virtual_address": virtual_address,
                    "raw_size": raw_size,
                    "raw_ptr": raw_ptr,
                }
            )

        imports: dict[str, list[str]] = {}
        descriptor_offset = _rva_to_offset(import_rva, sections)
        if descriptor_offset is None:
            return {}

        while descriptor_offset + 20 <= len(data):
            original_first_thunk, _time, _fwd, name_rva, first_thunk = struct.unpack_from("<IIIII", data, descriptor_offset)
            if original_first_thunk == 0 and name_rva == 0 and first_thunk == 0:
                break
            name_offset = _rva_to_offset(name_rva, sections)
            dll_name = _read_c_string(data, name_offset) if name_offset is not None else f"rva_{name_rva:08x}"
            thunk_rva = original_first_thunk or first_thunk
            thunk_offset = _rva_to_offset(thunk_rva, sections)
            function_names: list[str] = []
            if thunk_offset is not None:
                while True:
                    thunk_value = struct.unpack_from("<I", data, thunk_offset)[0]
                    if thunk_value == 0:
                        break
                    if thunk_value & 0x80000000 == 0:
                        hint_name_offset = _rva_to_offset(thunk_value, sections)
                        if hint_name_offset is not None and hint_name_offset + 2 < len(data):
                            function_names.append(_read_c_string(data, hint_name_offset + 2))
                    thunk_offset += 4
            imports[dll_name] = function_names
            descriptor_offset += 20
        return imports
    except Exception:
        return {}


def _infer_digital_mode_entry(report: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    firmware_strings = report["firmware"].get("interesting_strings", {}) if report["firmware"].get("present") else {}
    digimanager_strings = report["digimanager"].get("interesting_strings", {}) if report["digimanager"].get("present") else {}
    auxiliary = report["auxiliary_replays"]

    if firmware_strings:
        for key in sorted(firmware_strings):
            if "DIG" in key or "FT" in key:
                evidence.append(f"firmware string hit: {key} ({firmware_strings[key]})")
    if digimanager_strings:
        for key in sorted(digimanager_strings):
            if "DIG" in key or "FT" in key or "WSJT" in key:
                evidence.append(f"digimanager string hit: {key} ({digimanager_strings[key]})")
    if auxiliary.get("present"):
        for file_summary in auxiliary["files"]:
            evidence.append(
                f"replay {Path(file_summary['path']).name} mode={file_summary['mode']} prefixes={', '.join(sorted(file_summary['prefix_counts']))}"
            )

    if report["firmware"].get("present") and any("DIG" in key or "FT" in key for key in firmware_strings):
        return {
            "status": "candidate_firmware_strings_found",
            "summary": "The real firmware bin contains digital-mode-related strings, so static string anchors exist for a menu/state-machine hunt.",
            "evidence": evidence or ["No direct evidence captured."],
        }
    if report["digimanager"].get("present") and evidence:
        return {
            "status": "digimanager_side_confirms_digital_mode_context",
            "summary": "Firmware strings are still weak or missing, but DigiManager and replay evidence confirm the digital-mode ecosystem is present.",
            "evidence": evidence,
        }
    return {
        "status": "missing_real_assets",
        "summary": "Need the real 0.3q firmware bin and DigiManager binary before digital-mode entry can be pinned down.",
        "evidence": evidence or ["Place the real assets under reverse/input first."],
    }


def _infer_frequency_set_call_chain(report: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    reference_hits = report["public_source_reference"].get("reference_function_hits", {})
    if reference_hits:
        for function_name, paths in reference_hits.items():
            evidence.append(f"public-source reference: {function_name} in {', '.join(paths)}")
    if report["firmware"].get("present"):
        if report["firmware"].get("is_packed_candidate"):
            evidence.append("firmware asset is a packed image, so raw frequency constants and call sites are not directly trustworthy yet")
        for item in report["firmware"].get("frequency_literals_hz", []):
            evidence.append(f"firmware frequency literal candidate: {item['value_hz']} Hz count={item['count']}")

    if report["firmware"].get("present") and report["firmware"].get("is_packed_candidate") and not report["firmware"].get("unpack", {}).get("ok"):
        return {
            "status": "packed_firmware_limits_static_scan",
            "summary": "The available firmware asset is a packed image. Public-source names are still useful anchors, but the real set-frequency call chain should be mapped from an unpacked or raw app image.",
            "evidence": evidence,
        }
    if report["firmware"].get("present") and report["firmware"].get("is_packed_candidate") and report["firmware"].get("unpack", {}).get("ok"):
        evidence.append(f"packed firmware unpacked locally with embedded version {report['firmware']['unpack'].get('embedded_version')}")
    if reference_hits:
        return {
            "status": "public_source_anchor_only",
            "summary": "The public source still provides likely set-frequency anchor names, but the real 0.3q call chain must be mapped from the binary, not assumed from this tree.",
            "evidence": evidence,
        }
    return {
        "status": "no_call_chain_anchor",
        "summary": "No reliable call-chain anchor is available yet. Real-bin disassembly is required next.",
        "evidence": evidence or ["No public-source or firmware anchors found."],
    }


def _infer_lock_frequency_owner(report: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    auxiliary = report["auxiliary_replays"]
    if auxiliary.get("present"):
        unique = auxiliary.get("unique_prefixes_by_file", {})
        for file_name, prefixes in unique.items():
            evidence.append(f"replay unique prefixes for {file_name}: {', '.join(prefixes) if prefixes else 'none'}")

    digimanager = report["digimanager"]
    if digimanager.get("present"):
        marker_counts = digimanager.get("marker_counts", {})
        for name, count in marker_counts.items():
            if count:
                evidence.append(f"digimanager binary contains marker {name} count={count}")

    firmware_present = report["firmware"].get("present")
    digimanager_present = digimanager.get("present")
    if firmware_present and digimanager_present:
        return {
            "status": "not_yet_proven_static_only",
            "summary": "Static evidence is enough to frame both sides, but not yet enough to prove whether DigiManager stops sending retunes or firmware overwrites them in digital mode.",
            "evidence": evidence or ["Need tighter code/data anchors from the real assets."],
        }
    return {
        "status": "insufficient_assets",
        "summary": "Cannot attribute frequency locking until both the real firmware bin and DigiManager binary are present.",
        "evidence": evidence or ["Both real binaries are required."],
    }


def _infer_external_retune_capability(report: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    digimanager = report["digimanager"]
    if digimanager.get("present"):
        imports = digimanager.get("imports", {})
        if imports:
            evidence.append("digimanager imports: " + ", ".join(sorted(imports)))
        api_hints = digimanager.get("api_hints", {})
        evidence.append(f"has_udp_api={int(bool(api_hints.get('has_udp_api')))} has_serial_api={int(bool(api_hints.get('has_serial_api')))}")
        managed_behavior = digimanager.get("managed_behavior", {})
        if managed_behavior.get("available"):
            evidence.append(
                "managed IL: protocol_244_forwarded="
                + ("yes" if managed_behavior.get("protocol_244_forwarded") else "no")
            )
        for port, count in digimanager.get("port_mentions", {}).items():
            if count:
                evidence.append(f"port mention {port}: {count}")

    firmware = report["firmware"]
    if firmware.get("present"):
        for command_id, count in firmware.get("command_id_byte_hits", {}).items():
            if count:
                evidence.append(f"firmware byte hit {command_id}: {count}")

    if digimanager.get("present") and firmware.get("present"):
        api_hints = digimanager.get("api_hints", {})
        if api_hints.get("has_udp_api"):
            return {
                "status": "digimanager_looks_capable_of_external_retune",
                "summary": "DigiManager exposes strong UDP/frequency-control hints, so an external retune path probably exists on the PC side. The remaining question is whether digital mode still forwards it to firmware.",
                "evidence": evidence,
            }
        return {
            "status": "candidate_external_entry_needs_confirmation",
            "summary": "There are enough protocol and API hints to justify looking for an external retune path, but static-only evidence does not yet prove whether digital mode still honors it.",
            "evidence": evidence,
        }
    return {
        "status": "missing_real_assets",
        "summary": "External retune capability cannot be judged until both real sides are available for analysis.",
        "evidence": evidence or ["Need both firmware and DigiManager binaries."],
    }


def _infer_ft4_tx_gate(report: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    digimanager = report.get("digimanager", {})
    managed_behavior = digimanager.get("managed_behavior", {})
    auxiliary = report.get("auxiliary_replays", {})

    if auxiliary.get("present"):
        for file_summary in auxiliary.get("files", []):
            evidence.append(
                f"replay {Path(file_summary['path']).name} prefixes={', '.join(sorted(file_summary['prefix_counts']))}"
            )

    if managed_behavior.get("available"):
        evidence.append("managed IL: protocol_8_forwarded=" + ("yes" if managed_behavior.get("protocol_8_forwarded") else "no"))
        evidence.append("managed IL: protocol_244_forwarded=" + ("yes" if managed_behavior.get("protocol_244_forwarded") else "no"))
        evidence.append("managed IL: protocol_4_forwarded=" + ("yes" if managed_behavior.get("protocol_4_forwarded") else "no"))
        evidence.append("managed IL: protocol_4_seen_in_ui=" + ("yes" if managed_behavior.get("protocol_4_seen_in_ui") else "no"))

        if managed_behavior.get("protocol_8_forwarded") and not managed_behavior.get("protocol_4_forwarded"):
            return {
                "status": "pc_side_gate_likely",
                "summary": "DigiManager appears to forward protocol 8 packets into the device path, while protocol 4 is only visible in UI/status handling. The first FT4 TX gate therefore looks PC-side before firmware even gets a chance to transmit.",
                "evidence": evidence,
            }

    return {
        "status": "still_unclear",
        "summary": "FT4 TX gating is not proven yet. More targeted DigiManager or firmware tracing is still needed.",
        "evidence": evidence or ["No managed IL evidence was available."],
    }


def _recommend_next_step(report: dict[str, Any]) -> dict[str, str]:
    firmware_present = report["firmware"].get("present")
    digimanager_present = report["digimanager"].get("present")
    dynamic_summary = report.get("dynamic_validation", {})
    if not firmware_present and not digimanager_present:
        return {
            "kind": "collect_real_assets",
            "reason": "Place the real 0.3q firmware bin and UVK5DigManager binary under reverse/input first.",
        }
    if not firmware_present:
        return {
            "kind": "add_real_firmware_bin",
            "reason": "The real 0.3q firmware bin is still missing, so the lock-frequency owner cannot be located.",
        }
    if not digimanager_present:
        return {
            "kind": "add_digimanager_binary",
            "reason": "The firmware side can be scanned, but two-sided lock-frequency attribution still needs the real DigiManager binary.",
        }
    if dynamic_summary.get("present") and dynamic_summary.get("lock_owner") == "pc_side":
        return {
            "kind": "black_box_retune_injection",
            "reason": "Dynamic validation suggests DigiManager does not continuously retune in digital mode, so the next step is a black-box retune injection path.",
        }
    if dynamic_summary.get("present") and dynamic_summary.get("lock_owner") == "firmware_side":
        return {
            "kind": "firmware_lock_patch_plan",
            "reason": "Dynamic validation suggests DigiManager does continuously retune but firmware does not honor it in digital mode, so the next step is a firmware lock patch plan.",
        }
    if report["firmware"].get("is_packed_candidate") and not report["firmware"].get("unpack", {}).get("ok"):
        return {
            "kind": "obtain_raw_or_unpacked_firmware_image",
            "reason": "The current firmware asset is a packed image. To locate the real lock-frequency owner inside digital mode, the next best step is to obtain or derive an unpacked/raw app image before deeper static work.",
        }
    return {
        "kind": "static_anchor_review_then_targeted_dynamic",
        "reason": "With both binaries present, the next step is to review string/import anchors and then do the narrowest possible dynamic check around digital-mode retune behavior.",
    }


def _missing_asset(kind: str) -> dict[str, Any]:
    return {"kind": kind, "present": False}


def _pick_first(directory: Path, patterns: list[str]) -> Path | None:
    if not directory.exists():
        return None
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(sorted(directory.glob(pattern)))
    return matches[0] if matches else None


def _collect_keyword_hits(strings: list[str]) -> dict[str, int]:
    hits: Counter[str] = Counter()
    for value in strings:
        upper_value = value.upper()
        for keyword in INTERESTING_KEYWORDS:
            if keyword in upper_value:
                hits[value] += 1
                break
    return dict(hits.most_common(40))


def _iter_ascii_strings_with_offsets(data: bytes, *, min_length: int = 4) -> list[tuple[str, int]]:
    strings: list[tuple[str, int]] = []
    current: list[str] = []
    start = 0
    for index, byte in enumerate(data):
        if 32 <= byte <= 126:
            if not current:
                start = index
            current.append(chr(byte))
            continue
        if len(current) >= min_length:
            strings.append(("".join(current), start))
        current = []
    if len(current) >= min_length:
        strings.append(("".join(current), start))
    return strings


def _iter_utf16_strings_with_offsets(data: bytes, *, min_length: int = 4) -> list[tuple[str, int]]:
    strings: list[tuple[str, int]] = []
    current: list[str] = []
    start = 0
    for index in range(0, len(data) - 1, 2):
        first = data[index]
        second = data[index + 1]
        if second == 0 and 32 <= first <= 126:
            if not current:
                start = index
            current.append(chr(first))
            continue
        if len(current) >= min_length:
            strings.append(("".join(current), start))
        current = []
    if len(current) >= min_length:
        strings.append(("".join(current), start))
    return strings


def _count_number_mentions(strings: list[str], needle: str) -> int:
    return sum(1 for value in strings if needle in value)


def _prefix_from_packet(payload_hex: str) -> str:
    payload = bytes.fromhex(payload_hex)
    return " ".join(f"{byte:02x}" for byte in payload[:4])


def _load_first_exe_from_zip(path: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".exe"):
                return name, archive.read(name)
    raise FileNotFoundError(f"No .exe payload found in {path}")


def _imports_contain(imports: dict[str, list[str]], function_names: list[str]) -> bool:
    wanted = {name.lower() for name in function_names}
    for imported_names in imports.values():
        for imported_name in imported_names:
            if imported_name.lower() in wanted:
                return True
    return False


def _read_c_string(data: bytes, offset: int | None) -> str:
    if offset is None or offset >= len(data):
        return ""
    end = data.find(b"\x00", offset)
    if end == -1:
        end = len(data)
    return data[offset:end].decode("ascii", errors="ignore")


def _rva_to_offset(rva: int, sections: list[dict[str, int | str]]) -> int | None:
    for section in sections:
        start = int(section["virtual_address"])
        size = max(int(section["virtual_size"]), int(section["raw_size"]))
        end = start + size
        if start <= rva < end:
            return int(section["raw_ptr"]) + (rva - start)
    return None
