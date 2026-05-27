from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean
from typing import Any

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # type: ignore
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC  # type: ignore

from sat_bridge.reverse_tools import try_unpack_uvk5_packed_firmware

try:
    import dnfile  # type: ignore
    from dncil.cil.body.reader import read_method_body_from_bytes  # type: ignore
except Exception:  # pragma: no cover
    dnfile = None
    read_method_body_from_bytes = None


SETCECMESSAGE2_NAME = "SetCECMessage2"
SETDIGITALDATA2_NAME = "SetDigitalData2"
UDPDATACHECK_NAME = "UDPDataCheck"
CTOR_NAME = ".ctor"

COMMAND_SCAN_VALUES = [0x30, 0x32, 0x33, 0x35]
STRING_ANCHORS = ["DIG.M", "DIG+", "LOCK", "FREQ:%u.%05u"]
MODE_STRING_PATTERNS = {
    "FT8": b"FT8",
    "FT4": b"FT4",
    "APRS": b"APRS",
    "WSPR": b"WSPR",
    "SCAN": b"SCAN",
    "RECV": b"RECV",
    "AUTO": b"AUTO",
}
DESCRIPTOR_INTERESTING_STRINGS = {
    "FT8",
    "FT4",
    "APRS",
    "WSPR",
    "SCAN",
    "RECV",
    "AUTO",
    "VOX",
    "DIG+",
    "DIG.M",
    "LOCK\nKEYPAD",
    "FM",
    "CT",
    "DCS",
    "DCR",
}
KNOWN_DISPATCH_SEEDS = [3496]
KNOWN_PUBLIC_OBCFUSCATION = bytes.fromhex("166c14e62e910d402135d5401303e980")
GENERIC_PARSE_DISPATCH_BASE = 0x028E
GENERIC_PARSE_HELPER_TARGET = 0x0280
DISPATCH_RUNTIME_VALUES = {
    0x20000094: "state_cell_primary",
    0x20000740: "guard_or_context_block",
    0x7FFFFFFF: "signed_saturation_sentinel",
}


@dataclass(slots=True)
class CapstoneHit:
    offset: int
    instruction: str


@dataclass(slots=True)
class CapstoneWindow:
    label: str
    center_offset: int
    start_offset: int
    end_offset: int
    lines: list[str]


def analyze_command35_path(
    *,
    firmware_path: Path,
    digimanager_path: Path,
    ft4_replay_path: Path,
    ft8_replay_path: Path,
) -> dict[str, Any]:
    firmware_bytes = firmware_path.read_bytes()
    unpacked = try_unpack_uvk5_packed_firmware(firmware_bytes)
    if not unpacked.get("ok"):
        raise ValueError("Could not unpack the real 0.3q packed firmware.")

    raw_firmware: bytes = unpacked["raw_bytes"]
    digimanager_methods = _load_digimanager_methods(digimanager_path)
    command35_layout = infer_command35_layout(digimanager_methods)
    replay_stats = _analyze_replay_business_packets(ft4_replay_path, ft8_replay_path)

    immediate_hits = {
        f"0x{value:02x}": [
            {"offset": hit.offset, "instruction": hit.instruction}
            for hit in find_exact_immediate_hits(raw_firmware, value)
        ]
        for value in COMMAND_SCAN_VALUES
    }
    compare_hits = {
        f"0x{value:02x}": [
            {"offset": hit.offset, "instruction": hit.instruction}
            for hit in find_exact_compare_hits(raw_firmware, value)
        ]
        for value in COMMAND_SCAN_VALUES
    }
    validated_compare_hits = {
        key: validate_compare_hits(raw_firmware, hits)
        for key, hits in compare_hits.items()
    }
    seeded_compare_hits = {
        f"0x{value:02x}": [
            {"offset": hit.offset, "instruction": hit.instruction}
            for hit in find_exact_compare_hits_in_windows(raw_firmware, value, KNOWN_DISPATCH_SEEDS)
        ]
        for value in COMMAND_SCAN_VALUES
    }
    validated_seeded_compare_hits = {
        key: validate_compare_hits(raw_firmware, hits)
        for key, hits in seeded_compare_hits.items()
    }

    firmware_frame_matches = find_firmware_frame_family_matches(raw_firmware, command35_layout)
    digital_mode_strings = find_digital_mode_strings(raw_firmware)
    constant_cluster = describe_constant_cluster(raw_firmware, cluster_offset=0xDE94)
    pointer_tables = find_string_pointer_tables(raw_firmware)
    literal_targets: list[int] = list(DISPATCH_RUNTIME_VALUES)
    for item in pointer_tables:
        if not item.get("contains_interesting_strings"):
            continue
        literal_targets.append(item["offset"])
        literal_targets.extend(entry["entry_offset"] for entry in item["entries"])
    literal_pool_refs = find_literal_pool_refs_to_values(raw_firmware, literal_targets)
    dispatcher_runtime_refs = find_literal_pool_refs_in_windows(
        raw_firmware,
        list(DISPATCH_RUNTIME_VALUES),
        KNOWN_DISPATCH_SEEDS,
    )
    candidate_windows = _build_candidate_windows(raw_firmware, compare_hits, seeded_compare_hits)
    string_windows = _build_string_windows(raw_firmware)
    dispatcher_hypothesis = infer_dispatcher_hypothesis()
    generic_parse_profiles = decode_generic_parse_profiles(raw_firmware)

    report = {
        "inputs": {
            "firmware_path": str(firmware_path),
            "digimanager_path": str(digimanager_path),
            "ft4_replay_path": str(ft4_replay_path),
            "ft8_replay_path": str(ft8_replay_path),
        },
        "firmware": {
            "embedded_version": unpacked.get("embedded_version"),
            "command_immediate_hits": immediate_hits,
            "command_compare_hits": compare_hits,
            "command_compare_hits_validated": validated_compare_hits,
            "command_compare_hits_seeded": seeded_compare_hits,
            "command_compare_hits_seeded_validated": validated_seeded_compare_hits,
            "frame_family_matches": firmware_frame_matches,
            "digital_mode_strings": digital_mode_strings,
            "constant_cluster": constant_cluster,
            "string_pointer_tables": pointer_tables,
            "literal_pool_refs": literal_pool_refs,
            "dispatcher_runtime_refs": dispatcher_runtime_refs,
            "dispatcher_hypothesis": dispatcher_hypothesis,
            "generic_parse_profiles": generic_parse_profiles,
            "candidate_dispatch_windows": [
                {
                    "label": item.label,
                    "center_offset": item.center_offset,
                    "start_offset": item.start_offset,
                    "end_offset": item.end_offset,
                    "lines": item.lines,
                }
                for item in candidate_windows
            ],
            "string_anchor_windows": [
                {
                    "label": item.label,
                    "center_offset": item.center_offset,
                    "start_offset": item.start_offset,
                    "end_offset": item.end_offset,
                    "lines": item.lines,
                }
                for item in string_windows
            ],
        },
        "digimanager": {
            "managed_methods": digimanager_methods,
            "command35_layout": command35_layout,
        },
        "replay": replay_stats,
    }
    report["judgement"] = infer_command35_judgement(report)
    return report


def infer_dispatcher_hypothesis() -> dict[str, Any]:
    return {
        "dispatcher_root_offset": 0x0D90,
        "generic_parse_entry_offset": 0x0DBE,
        "generic_parse_helper_call_offset": 0x0DC4,
        "generic_parse_helper_target": GENERIC_PARSE_HELPER_TARGET,
        "generic_parse_input_source": "uxtb r0, r2",
        "direct_command_cases": {
            "0x32": {
                "compare_offset": 0x0D90,
                "branch_offset": 0x0D92,
                "target_offset": 0x0E1A,
            },
            "0x33": {
                "compare_offset": 0x0DFC,
                "branch_offset": 0x0DFE,
                "target_offset": 0x0E00,
            },
        },
        "command_0x35_flow": [
            "0x0D90: cmp r0, #0x32",
            "0x0D94: bgt 0x0DF8 when command > 0x32",
            "0x0DFC: cmp r0, #0x33",
            "0x0DFE: bne 0x0DBE when command != 0x33",
            "0x0DBE: generic parse branch",
            "0x0DC4: call helper 0x0280",
        ],
        "command_0x35_interpretation": (
            "0x35 currently looks more like a generic parser family member than a "
            "direct top-level compare case, and the helper is fed from r2 rather than "
            "the original top-level command byte."
        ),
        "generic_parse_outputs": [
            "sp+0x0c length_or_count_a",
            "sp+0x10 length_or_count_b",
        ],
        "contextual_function_hint": {
            "window_start": 0x0D02,
            "window_end": 0x0E0C,
            "context_bytes_written": ["base+0x7d", "base+0x7e", "base+0x7f"],
            "classification_helper": 0x888C,
            "range_helpers": [0x7618, 0x7714],
            "interpretation": (
                "The surrounding function looks more like a UI or mode-state handler that "
                "updates a bounded selector/context block before any deeper digital send path."
            ),
        },
    }


def decode_generic_parse_profiles(raw_firmware: bytes) -> dict[str, Any]:
    subcode_cases: dict[str, Any] = {}
    for subcode in [0x04, 0x08, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x47]:
        entry = raw_firmware[GENERIC_PARSE_DISPATCH_BASE + subcode]
        target = GENERIC_PARSE_DISPATCH_BASE + entry * 2
        profile = {
            "jump_table_entry": entry,
            "target_offset": target,
            "derived_outputs": infer_generic_case_outputs(target),
        }
        subcode_cases[f"0x{subcode:02X}"] = profile
    return {
        "dispatch_base": GENERIC_PARSE_DISPATCH_BASE,
        "helper_target": GENERIC_PARSE_HELPER_TARGET,
        "helper_input_is": "u8(r2)",
        "subcode_cases": subcode_cases,
    }


def infer_generic_case_outputs(target_offset: int) -> dict[str, Any]:
    # This decoder is intentionally narrow: it only documents the currently
    # observed immediate-output stubs that feed the second-stage parser.
    if target_offset == 0x02E6:
        return {"out_a": 0, "out_b": 0x32, "meaning_hint": "single immediate output path"}
    if target_offset == 0x02EA:
        return {"out_a": 0, "out_b": 0x03, "meaning_hint": "generic small-class selector"}
    if target_offset == 0x02EE:
        return {"out_a": 0x1E, "out_b": 0x78, "meaning_hint": "paired length/value profile"}
    if target_offset == 0x02F6:
        return {"out_a": 0x05, "out_b": 0x64, "meaning_hint": "paired length/value profile"}
    if target_offset == 0x0302:
        return {"out_a": 0, "out_b": 0x17, "meaning_hint": "single immediate output path"}
    if target_offset == 0x0306:
        return {"out_a": 0, "out_b": 0x07, "meaning_hint": "single immediate output path"}
    if target_offset == 0x030A:
        return {"out_a": 0x01, "out_b": 0x0A, "meaning_hint": "tiny paired profile"}
    if target_offset == 0x0312:
        return {"out_a": 0, "out_b": 0xD0, "meaning_hint": "single immediate output path"}
    if target_offset == 0x0316:
        return {"out_a": 0, "out_b": 0x01, "meaning_hint": "single immediate output path"}
    if target_offset == 0x031A:
        return {"out_a": 0, "out_b": 0x05, "meaning_hint": "single immediate output path"}
    if target_offset == 0x031E:
        return {"out_a": -1, "out_b": 0xA9, "meaning_hint": "special direct command family"}
    if target_offset == 0x0328:
        return {"out_a": 0, "out_b": 0x04, "meaning_hint": "single immediate output path"}
    if target_offset == 0x032C:
        return {"out_a": 0, "out_b": 0x02, "meaning_hint": "single immediate output path"}
    if target_offset == 0x0330:
        return {"out_a": -0x32, "out_b": 0x32, "meaning_hint": "signed profile"}
    if target_offset == 0x0336:
        return {"out_a": 0x640, "out_b": "literal_loaded", "meaning_hint": "large paired profile"}
    if target_offset == 0x0340:
        return {"out_a": 0, "out_b": 0x09, "meaning_hint": "single immediate output path"}
    if target_offset == 0x0344:
        return {"return": -1, "meaning_hint": "out-of-range / invalid command"}
    return {"meaning_hint": "unknown_case_stub"}


def write_command35_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "command35-path.json"
    md_path = output_dir / "command35-path.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_command35_markdown(report), encoding="utf-8")
    return json_path, md_path


def find_exact_immediate_hits(raw_firmware: bytes, immediate: int, *, limit: int = 12) -> list[CapstoneHit]:
    hits: list[CapstoneHit] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    decimal = str(immediate)
    hexa = f"0x{immediate:x}"
    for ins in md.disasm(raw_firmware, 0):
        operands = [operand.strip() for operand in ins.op_str.split(",") if operand.strip()]
        if not any(operand == f"#{decimal}" or operand == f"#{hexa}" for operand in operands):
            continue
        hits.append(CapstoneHit(offset=ins.address, instruction=f"{ins.mnemonic} {ins.op_str}".rstrip()))
        if len(hits) >= limit:
            break
    return hits


def find_exact_compare_hits(raw_firmware: bytes, immediate: int, *, limit: int = 12) -> list[CapstoneHit]:
    hits: list[CapstoneHit] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    decimal = str(immediate)
    hexa = f"0x{immediate:x}"
    for ins in md.disasm(raw_firmware, 0):
        if not ins.mnemonic.startswith("cmp"):
            continue
        operands = [operand.strip() for operand in ins.op_str.split(",") if operand.strip()]
        if not any(operand == f"#{decimal}" or operand == f"#{hexa}" for operand in operands):
            continue
        hits.append(CapstoneHit(offset=ins.address, instruction=f"{ins.mnemonic} {ins.op_str}".rstrip()))
        if len(hits) >= limit:
            break
    return hits


def find_exact_compare_hits_in_windows(
    raw_firmware: bytes,
    immediate: int,
    centers: list[int],
    *,
    before: int = 96,
    after: int = 96,
) -> list[CapstoneHit]:
    hits: list[CapstoneHit] = []
    decimal = str(immediate)
    hexa = f"0x{immediate:x}"
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    seen_offsets: set[int] = set()
    for center in centers:
        start = max(0, center - before)
        end = min(len(raw_firmware), center + after)
        for ins in md.disasm(raw_firmware[start:end], start):
            if not ins.mnemonic.startswith("cmp"):
                continue
            operands = [operand.strip() for operand in ins.op_str.split(",") if operand.strip()]
            if not any(operand == f"#{decimal}" or operand == f"#{hexa}" for operand in operands):
                continue
            if ins.address in seen_offsets:
                continue
            seen_offsets.add(ins.address)
            hits.append(CapstoneHit(offset=ins.address, instruction=f"{ins.mnemonic} {ins.op_str}".rstrip()))
    return sorted(hits, key=lambda item: item.offset)


def validate_compare_hits(raw_firmware: bytes, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for hit in hits:
        offset = int(hit["offset"])
        chunk = raw_firmware[offset:offset + 4]
        decoded = list(md.disasm(chunk, offset | 1))
        if not decoded:
            continue
        ins = decoded[0]
        rendered = f"{ins.mnemonic} {ins.op_str}".rstrip()
        if rendered != hit["instruction"]:
            continue
        validated.append(
            {
                "offset": offset,
                "instruction": rendered,
            }
        )
    return validated


def infer_command35_layout(digimanager_methods: dict[str, dict[str, Any]]) -> dict[str, Any]:
    setcec = digimanager_methods.get(SETCECMESSAGE2_NAME, {})
    setdigital = digimanager_methods.get(SETDIGITALDATA2_NAME, {})
    udpcheck = digimanager_methods.get(UDPDATACHECK_NAME, {})
    return {
        "frame_kind": "cec_private_sparse_control_frame",
        "command_id": 0x35,
        "layout": [
            "bytes[0..3] = STXBUFF",
            "byte[4] = command id",
            "bytes[5..6] = payload length (little endian)",
            "bytes[7..11] = 5-byte sender header from SetDigitalData2",
            "bytes[12..15] = ETXBUFF",
            "bytes[16..] = forwarded payload bytes",
        ],
        "managed_evidence": {
            "SetCECMessage2_token": setcec.get("token"),
            "SetDigitalData2_token": setdigital.get("token"),
            "UDPDataCheck_token": udpcheck.get("token"),
            "SetDigitalData2_calls_SetCECMessage2_with_0x35": setdigital.get("calls_command35", False),
            "UDPDataCheck_calls_SetDigitalData2_for_protocol8": udpcheck.get("protocol8_calls_setdigitaldata2", False),
        },
        "frame_constants": {
            "stx": setcec.get("stx_bytes"),
            "etx": setcec.get("etx_bytes"),
        },
    }


def find_firmware_frame_family_matches(raw_firmware: bytes, command35_layout: dict[str, Any]) -> dict[str, Any]:
    stx = bytes(command35_layout.get("frame_constants", {}).get("stx", []))
    etx = bytes(command35_layout.get("frame_constants", {}).get("etx", []))
    return {
        "obfuscation_offsets": find_all_bytes(raw_firmware, KNOWN_PUBLIC_OBCFUSCATION, limit=8),
        "stx_offsets": find_all_bytes(raw_firmware, stx, limit=8) if stx else [],
        "etx_offsets": find_all_bytes(raw_firmware, etx, limit=8) if etx else [],
    }


def find_digital_mode_strings(raw_firmware: bytes) -> dict[str, list[int]]:
    return {
        name: find_all_bytes(raw_firmware, pattern, limit=8)
        for name, pattern in MODE_STRING_PATTERNS.items()
    }


def find_string_pointer_tables(
    raw_firmware: bytes,
    *,
    min_entries: int = 2,
    max_small_value: int = 0x1000,
) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    seen_offsets: set[int] = set()
    for offset in range(0, len(raw_firmware) - 8, 4):
        if offset in seen_offsets:
            continue
        pointer = int.from_bytes(raw_firmware[offset:offset + 4], "little")
        tag_value = int.from_bytes(raw_firmware[offset + 4:offset + 8], "little")
        text = _read_short_ascii(raw_firmware, pointer)
        if not text or tag_value > max_small_value:
            continue
        entries: list[dict[str, Any]] = []
        cursor = offset
        while cursor + 8 <= len(raw_firmware):
            pointer = int.from_bytes(raw_firmware[cursor:cursor + 4], "little")
            tag_value = int.from_bytes(raw_firmware[cursor + 4:cursor + 8], "little")
            text = _read_short_ascii(raw_firmware, pointer)
            if not text or tag_value > max_small_value:
                break
            entries.append(
                {
                    "entry_offset": cursor,
                    "string_offset": pointer,
                    "text": text,
                    "tag_value": tag_value,
                }
            )
            seen_offsets.add(cursor)
            cursor += 8
        if len(entries) < min_entries:
            continue
        tables.append(
            {
                "offset": offset,
                "entry_count": len(entries),
                "entries": entries,
                "contains_interesting_strings": any(
                    item["text"] in DESCRIPTOR_INTERESTING_STRINGS for item in entries
                ),
            }
        )
    return tables


def find_literal_pool_refs_to_values(
    raw_firmware: bytes,
    target_values: list[int],
) -> list[dict[str, Any]]:
    if not target_values:
        return []

    wanted = set(target_values)
    refs: list[dict[str, Any]] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for ins in md.disasm(raw_firmware, 0):
        if ins.mnemonic != "ldr" or len(ins.operands) < 2:
            continue
        src = ins.operands[1]
        if src.type != ARM_OP_MEM or src.mem.base != ARM_REG_PC:
            continue
        literal_offset = ((ins.address + 4) & ~3) + src.mem.disp
        if literal_offset < 0 or literal_offset + 4 > len(raw_firmware):
            continue
        loaded_value = int.from_bytes(raw_firmware[literal_offset:literal_offset + 4], "little")
        if loaded_value not in wanted:
            continue
        refs.append(
            {
                "instruction_offset": ins.address,
                "instruction": f"{ins.mnemonic} {ins.op_str}".rstrip(),
                "literal_pool_offset": literal_offset,
                "loaded_value": loaded_value,
            }
        )
    return refs


def find_literal_pool_refs_in_windows(
    raw_firmware: bytes,
    target_values: list[int],
    centers: list[int],
    *,
    before: int = 128,
    after: int = 128,
) -> list[dict[str, Any]]:
    if not target_values or not centers:
        return []

    wanted = set(target_values)
    refs: list[dict[str, Any]] = []
    seen_offsets: set[tuple[int, int]] = set()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for center in centers:
        start = max(0, center - before)
        end = min(len(raw_firmware), center + after)
        for ins in md.disasm(raw_firmware[start:end], start):
            if ins.mnemonic != "ldr" or len(ins.operands) < 2:
                continue
            src = ins.operands[1]
            if src.type != ARM_OP_MEM or src.mem.base != ARM_REG_PC:
                continue
            literal_offset = ((ins.address + 4) & ~3) + src.mem.disp
            if literal_offset < 0 or literal_offset + 4 > len(raw_firmware):
                continue
            loaded_value = int.from_bytes(raw_firmware[literal_offset:literal_offset + 4], "little")
            if loaded_value not in wanted:
                continue
            key = (ins.address, loaded_value)
            if key in seen_offsets:
                continue
            seen_offsets.add(key)
            refs.append(
                {
                    "center_offset": center,
                    "instruction_offset": ins.address,
                    "instruction": f"{ins.mnemonic} {ins.op_str}".rstrip(),
                    "literal_pool_offset": literal_offset,
                    "loaded_value": loaded_value,
                    "label": DISPATCH_RUNTIME_VALUES.get(loaded_value, f"{loaded_value:#010x}"),
                }
            )
    refs.sort(key=lambda item: (item["instruction_offset"], item["loaded_value"]))
    return refs


def _read_short_ascii(raw_firmware: bytes, offset: int, *, max_len: int = 32) -> str:
    if offset < 0 or offset >= len(raw_firmware):
        return ""
    end = raw_firmware.find(b"\x00", offset)
    if end == -1 or end - offset <= 0 or end - offset > max_len:
        return ""
    chunk = raw_firmware[offset:end]
    try:
        return chunk.decode("ascii")
    except UnicodeDecodeError:
        return ""


def describe_constant_cluster(raw_firmware: bytes, *, cluster_offset: int) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for index in range(0, 0x40, 4):
        offset = cluster_offset + index
        if offset + 4 > len(raw_firmware):
            break
        value = int.from_bytes(raw_firmware[offset:offset + 4], "little")
        entry: dict[str, Any] = {
            "offset": offset,
            "value": value,
        }
        if 0 <= value < len(raw_firmware):
            raw_text = raw_firmware[value:value + 24]
            printable = raw_text.split(b"\x00")[0]
            if printable and all(32 <= byte < 127 for byte in printable):
                entry["points_to_ascii"] = printable.decode("ascii", errors="ignore")
        entries.append(entry)
    return {
        "cluster_offset": cluster_offset,
        "entries": entries,
    }


def find_all_bytes(raw_firmware: bytes, pattern: bytes, *, limit: int = 20) -> list[int]:
    if not pattern:
        return []
    hits: list[int] = []
    start = 0
    while True:
        offset = raw_firmware.find(pattern, start)
        if offset == -1:
            break
        hits.append(offset)
        if len(hits) >= limit:
            break
        start = offset + 1
    return hits


def infer_command35_judgement(report: dict[str, Any]) -> dict[str, Any]:
    compare_hits = report["firmware"].get("command_compare_hits_validated", {})
    seeded_compare_hits = report["firmware"].get("command_compare_hits_seeded_validated", {})
    raw_compare_hits = report["firmware"]["command_compare_hits"]
    immediate_hits = report["firmware"]["command_immediate_hits"]
    frame_matches = report["firmware"]["frame_family_matches"]
    digital_mode_strings = report["firmware"].get("digital_mode_strings", {})
    constant_cluster = report["firmware"].get("constant_cluster", {})
    pointer_tables = report["firmware"].get("string_pointer_tables", [])
    literal_pool_refs = report["firmware"].get("literal_pool_refs", [])
    dispatcher_runtime_refs = report["firmware"].get("dispatcher_runtime_refs", [])
    replay = report["replay"]

    effective_35 = compare_hits.get("0x35") or seeded_compare_hits.get("0x35") or []
    effective_32 = compare_hits.get("0x32") or seeded_compare_hits.get("0x32") or []
    effective_33 = compare_hits.get("0x33") or seeded_compare_hits.get("0x33") or []

    has_direct_35 = bool(effective_35)
    has_32 = bool(effective_32)
    has_33 = bool(effective_33)
    has_stx = bool(frame_matches.get("stx_offsets"))
    has_etx = bool(frame_matches.get("etx_offsets"))
    has_obfuscation = bool(frame_matches.get("obfuscation_offsets"))
    has_ft8_string = bool(digital_mode_strings.get("FT8"))
    has_ft4_string = bool(digital_mode_strings.get("FT4"))

    if has_direct_35:
        handler_model = "direct_command_dispatch_seen"
    elif has_32 or has_33:
        handler_model = "adjacent_command_dispatch_seen_but_0x35_not_literal"
    elif raw_compare_hits.get("0x32") or raw_compare_hits.get("0x33"):
        handler_model = "raw_sweep_hits_present_but_not_revalidated"
    else:
        handler_model = "no_reliable_dispatch_anchor_yet"

    summary_lines = [
        "DigiManager 发给固件的不是音频流，而是 command 0x35 私有数字控制帧。",
        "当前 replay 里的业务包平均只有 8 到 9 个非零字节，更像稀疏控制帧，不像完整音调序列。",
    ]
    if has_stx and has_etx:
        summary_lines.append(
            f"真实固件里能直接找到和 DigiManager 完全一致的 4 字节帧头/帧尾常量，位置分别在 "
            f"{', '.join(hex(item) for item in frame_matches['stx_offsets'])} / "
            f"{', '.join(hex(item) for item in frame_matches['etx_offsets'])}。"
        )
    if has_obfuscation:
        summary_lines.append(
            f"真实固件里还能找到和公开 uart.c 一样的 16 字节扰码表，位置在 "
            f"{', '.join(hex(item) for item in frame_matches['obfuscation_offsets'])}，"
            "说明它更像同一家族协议，而不是完全不同的无线侧实现。"
        )
    if has_ft8_string and not has_ft4_string:
        summary_lines.append(
            "真实固件里能看到 FT8/APRS/WSPR 等数字模式字符串，但当前还看不到 FT4 字样，"
            "这更像是固件公开知道 FT8 类路径，而 FT4 可能只是被挤进现有数字发送链。"
        )
    cluster_ascii = [item.get("points_to_ascii") for item in constant_cluster.get("entries", []) if item.get("points_to_ascii")]
    if {"FM", "CT", "DCS", "DCR"}.issubset(set(cluster_ascii)):
        summary_lines.append(
            "在 `0xDE94` 附近还能看到一个混合常量簇，前半段是 `FM/CT/DCS/DCR` 字符串指针，"
            "后半段紧接 DigiManager 同源的 STX/ETX 和一组数字参数，像是模式描述表或第二阶段解析参数表。"
        )
    interesting_tables = [item for item in pointer_tables if item.get("contains_interesting_strings")]
    if interesting_tables:
        summary_lines.append(
            "真实固件里还能识别出多张字符串指针表，其中至少有一部分被真实代码通过 "
            "PC 相对 literal pool 引用，说明固件很可能大量依赖表驱动的模式/设置描述结构。"
        )
    if has_direct_35:
        summary_lines.extend(
            [
                "真实固件里已经看到直接比较 0x35 的候选分发点，说明 command 0x35 至少有一条字面命令入口。",
                "下一步最值钱的是围绕这个 0x35 分发点继续向下追，确认它后面如何把稀疏控制帧变成实际数字发射节拍。",
            ]
        )
    elif has_32 or has_33:
        summary_lines.extend(
            [
                "真实固件里已经能看到 0x32 和 0x33 的候选分发点，但还没有直接看到字面比较 0x35 的处理点。",
                "因此更可能的情况是：0x35 不是简单单字节命令直接分发，而是进入了另一层解析，或被归入更上层命令家族处理。",
                "下一步最值钱的是继续围绕 0x32/0x33 邻近分发块，以及帧头/帧尾常量所在的数据家族，追 0x35 在固件里的第二阶段解释路径。",
            ]
        )
    elif raw_compare_hits.get("0x32") or raw_compare_hits.get("0x33"):
        summary_lines.extend(
            [
                "之前线性扫全镜像时曾命中过 0x32/0x33 比较点，但在从命中地址重新局部反汇编时没有复现，说明这些点很可能是把数据区误解成代码的假阳性。",
                "因此当前还不能把 0x32/0x33 当成可靠锚点，下一步更应该围绕 `0xDE94` 常量簇和同协议家族常量追真正的代码引用。",
            ]
        )
    else:
        summary_lines.append("当前还没有足够可靠的固件分发锚点，需要继续补充固件侧命令入口证据。")

    summary_lines.append(
        "???????????????? 0x32 ???? 0x33 ?????? 0x0DBE ???????"
        "?? 0x0280 ?? helper ? u8(r2) ??????????????????"
    )

    return {
        "command35_frame_kind": "sparse_control_frame",
        "firmware_direct_cmp_0x35": "yes" if has_direct_35 else "no",
        "firmware_adjacent_dispatchers": {
            "0x32_seen": has_32,
            "0x33_seen": has_33,
        },
        "firmware_frame_family": {
            "stx_found": has_stx,
            "etx_found": has_etx,
            "obfuscation_found": has_obfuscation,
        },
        "firmware_mode_strings": {
            "ft8_present": has_ft8_string,
            "ft4_present": has_ft4_string,
            "all_hits": digital_mode_strings,
        },
        "seeded_compare_hits": {
            "0x32": effective_32,
            "0x33": effective_33,
            "0x35": effective_35,
        },
        "raw_compare_hits": raw_compare_hits,
        "likely_handler_model": handler_model,
        "ft4_upstream_is_real": True,
        "timing_owner_guess": "firmware_or_joint_path_more_likely_than_digimanager_only",
        "replay_nonzero_summary": {
            "ft4_mean_nonzero_bytes": replay["ft4"]["business_packet_nonzero_summary"]["mean"],
            "ft8_mean_nonzero_bytes": replay["ft8"]["business_packet_nonzero_summary"]["mean"],
        },
        "raw_immediate_hint_0x35": immediate_hits.get("0x35", []),
        "dispatcher_runtime_state_model": (
            "generic_branch_looks_more_like_bounded_state_machine_than_full_symbol_stream"
            if dispatcher_runtime_refs
            else "not_enough_runtime_state_evidence"
        ),
        "summary_lines": summary_lines,
    }


def render_command35_markdown(report: dict[str, Any]) -> str:
    judgement = report["judgement"]
    frame_matches = report["firmware"]["frame_family_matches"]
    mode_strings = report["firmware"].get("digital_mode_strings", {})
    constant_cluster = report["firmware"].get("constant_cluster", {})
    pointer_tables = report["firmware"].get("string_pointer_tables", [])
    literal_pool_refs = report["firmware"].get("literal_pool_refs", [])
    dispatcher_runtime_refs = report["firmware"].get("dispatcher_runtime_refs", [])
    dispatcher_hypothesis = report["firmware"].get("dispatcher_hypothesis", {})
    generic_parse_profiles = report["firmware"].get("generic_parse_profiles", {})
    layout = report["digimanager"]["command35_layout"]
    lines = [
        "# 真实 0.3q 中 `command 0x35` 处理路径分析",
        "",
        "## 当前结论",
    ]
    lines.extend(f"- {item}" for item in judgement["summary_lines"])
    lines.extend(
        [
            "",
            "## DigiManager 侧已经确认的事实",
            f"- `SetDigitalData2 -> SetCECMessage2(0x35)`：`{layout['managed_evidence']['SetDigitalData2_calls_SetCECMessage2_with_0x35']}`",
            f"- `UDPDataCheck(protocol 8) -> SetDigitalData2`：`{layout['managed_evidence']['UDPDataCheck_calls_SetDigitalData2_for_protocol8']}`",
            f"- `STXBUFF`：`{layout['frame_constants']['stx']}`",
            f"- `ETXBUFF`：`{layout['frame_constants']['etx']}`",
            "- `command 0x35` 布局：",
        ]
    )
    lines.extend(f"  - {item}" for item in layout["layout"])
    lines.extend(
        [
            "",
            "## replay 业务包统计",
            f"- FT4 业务包平均非零字节数：`{report['replay']['ft4']['business_packet_nonzero_summary']['mean']}`",
            f"- FT8 业务包平均非零字节数：`{report['replay']['ft8']['business_packet_nonzero_summary']['mean']}`",
            f"- FT4 非零热点：`{', '.join(str(i) for i in report['replay']['ft4']['business_packet_hotspots'])}`",
            f"- FT8 非零热点：`{', '.join(str(i) for i in report['replay']['ft8']['business_packet_hotspots'])}`",
            "",
            "## 真实固件里已经能看到的同协议家族证据",
            f"- 与 DigiManager 相同的 STX 常量位置：`{', '.join(hex(x) for x in frame_matches['stx_offsets']) or '未命中'}`",
            f"- 与 DigiManager 相同的 ETX 常量位置：`{', '.join(hex(x) for x in frame_matches['etx_offsets']) or '未命中'}`",
            f"- 与公开 `uart.c` 相同的 16 字节扰码表位置：`{', '.join(hex(x) for x in frame_matches['obfuscation_offsets']) or '未命中'}`",
            "",
            "## 真实固件里的数字模式字符串",
            f"- `FT8`：`{', '.join(hex(x) for x in mode_strings.get('FT8', [])) or '未命中'}`",
            f"- `FT4`：`{', '.join(hex(x) for x in mode_strings.get('FT4', [])) or '未命中'}`",
            f"- `APRS`：`{', '.join(hex(x) for x in mode_strings.get('APRS', [])) or '未命中'}`",
            f"- `WSPR`：`{', '.join(hex(x) for x in mode_strings.get('WSPR', [])) or '未命中'}`",
            "",
            "## `0xDE94` 常量簇",
            f"- 常量簇起点：`{hex(constant_cluster.get('cluster_offset', 0))}`",
            f"- 可直接解读出的字符串指针：`{', '.join(item['points_to_ascii'] for item in constant_cluster.get('entries', []) if item.get('points_to_ascii')) or '无'}`",
            "",
            "## 固件里的字符串指针表",
            f"- 指针表总数：`{len(pointer_tables)}`",
            f"- 明显带数字模式/设置语义的表：`{', '.join(hex(item['offset']) for item in pointer_tables if item.get('contains_interesting_strings')) or '未识别'}`",
            f"- 指向这些表的 PC 相对取值引用数：`{len(literal_pool_refs)}`",
            "",
            "## 固件侧命中点",
            f"- 直接 `cmp ..., #0x35` 是否命中：`{judgement['firmware_direct_cmp_0x35']}`",
            f"- `cmp ..., #0x32` 邻近分发是否命中：`{judgement['firmware_adjacent_dispatchers']['0x32_seen']}`",
            f"- `cmp ..., #0x33` 邻近分发是否命中：`{judgement['firmware_adjacent_dispatchers']['0x33_seen']}`",
            f"- 当前更像的处理模型：`{judgement['likely_handler_model']}`",
            "",
            "## 候选分发窗口",
        ]
    )
    for item in report["firmware"]["candidate_dispatch_windows"]:
        lines.append(f"### {item['label']} @ {item['center_offset']:#06x}")
        lines.extend(f"- `{line}`" for line in item["lines"])
        lines.append("")
    lines.append("## `0x35` 通用分支推断")
    if dispatcher_hypothesis:
        lines.append(f"- 根分发区：`{dispatcher_hypothesis['dispatcher_root_offset']:#06x}`")
        lines.append(f"- 通用分支入口：`{dispatcher_hypothesis['generic_parse_entry_offset']:#06x}`")
        lines.append(
            f"- 通用 helper 调用：`{dispatcher_hypothesis['generic_parse_helper_call_offset']:#06x}` -> "
            f"`{dispatcher_hypothesis['generic_parse_helper_target']:#06x}`"
        )
        lines.append(f"- 当前判断：{dispatcher_hypothesis['command_0x35_interpretation']}")
        lines.append("- 对 `0x35` 的候选控制流：")
        lines.extend(f"  - `{item}`" for item in dispatcher_hypothesis["command_0x35_flow"])
        lines.append("- 通用 helper 输出位点：")
        lines.extend(f"  - `{item}`" for item in dispatcher_hypothesis["generic_parse_outputs"])
        context_hint = dispatcher_hypothesis.get("contextual_function_hint", {})
        if context_hint:
            lines.append(
                f"- 邻域函数窗口：`{context_hint['window_start']:#06x} ~ {context_hint['window_end']:#06x}`，"
                f"更像 `{', '.join(context_hint['context_bytes_written'])}` 这类状态字节的更新器，"
                f"并调用分类 helper `{context_hint['classification_helper']:#06x}` 与范围 helper "
                f"`{', '.join(hex(item) for item in context_hint['range_helpers'])}`。"
            )
    lines.append("")
    lines.append("## 通用 helper 跳表结果")
    if generic_parse_profiles:
        lines.append(
            f"- 跳表基址：`{generic_parse_profiles['dispatch_base']:#06x}`，helper：`{generic_parse_profiles['helper_target']:#06x}`"
        )
        for subcode, profile in generic_parse_profiles.get("subcode_cases", {}).items():
            lines.append(
                f"- `{subcode}` -> target `{profile['target_offset']:#06x}` -> `{profile['derived_outputs']}`"
            )
    lines.append("")
    lines.append("## 字符串指针表候选")
    for item in pointer_tables[:8]:
        lines.append(
            f"### table @ {item['offset']:#06x} ({item['entry_count']} entries, interesting={item['contains_interesting_strings']})"
        )
        for entry in item["entries"][:8]:
            lines.append(
                f"- `{entry['entry_offset']:#06x}` -> `{entry['text']}` (str @ {entry['string_offset']:#06x}, tag={entry['tag_value']:#x})"
            )
        lines.append("")
    lines.append("## 指向这些表的 literal pool 引用")
    for item in literal_pool_refs[:12]:
        lines.append(
            f"- `{item['instruction_offset']:#06x} {item['instruction']}` -> pool `{item['literal_pool_offset']:#06x}` => `{item['loaded_value']:#06x}`"
        )
    lines.append("")
    lines.append("## dispatcher 邻域里的运行时状态引用")
    for item in dispatcher_runtime_refs[:16]:
        lines.append(
            f"- center `{item['center_offset']:#06x}`: `{item['instruction_offset']:#06x} {item['instruction']}` -> "
            f"pool `{item['literal_pool_offset']:#06x}` => `{item['loaded_value']:#010x}` (`{item['label']}`)"
        )
    if not dispatcher_runtime_refs:
        lines.append("- 未识别到邻域运行时状态引用。")
    lines.append("")
    lines.append("## 字符串锚点窗口")
    for item in report["firmware"]["string_anchor_windows"]:
        lines.append(f"### {item['label']} @ {item['center_offset']:#06x}")
        lines.extend(f"- `{line}`" for line in item["lines"])
        lines.append("")
    lines.append("## 当前建议")
    if judgement["firmware_direct_cmp_0x35"] == "yes":
        lines.append("- 继续围绕直接命中的 `cmp ..., #0x35` 候选点向下追，确认它后面如何进入数字模式发送路径。")
    elif judgement["likely_handler_model"] == "raw_sweep_hits_present_but_not_revalidated":
        lines.append("- 之前扫出来的 `0x32 / 0x33` 命中点没有通过局部反汇编复验，当前应把它们视为低可信提示，不再继续沿它们做强结论。")
        lines.append("- 下一步改为优先追 `0xDE94 ~ 0xDEBC` 常量簇和 `FT8 / APRS / WSPR` 等模式字符串的真实代码引用。")
    else:
        lines.append("- 当前还没有可靠的命令分发锚点，优先去找 `0xDE94 ~ 0xDEBC` 常量簇和模式字符串的真实代码引用。")
    lines.append("- 这轮新增的重点是：优先跟踪‘字符串指针表 -> PC 相对 literal pool -> 真实代码入口’这条链，而不是再依赖全镜像线性反汇编扫出来的单点命中。")
    lines.append("- 优先把 `0xDE94 ~ 0xDEBC` 这块常量簇当成同协议家族常量区继续追引用，因为这里同时出现了模式字符串指针、帧头、帧尾和数字模式相关参数。")
    lines.append("- 如果后续需要现场验证，优先考虑串口层抓到实际 `0x35` 帧，再反推固件 parser。")
    return "\n".join(lines) + "\n"


def _analyze_replay_business_packets(ft4_replay_path: Path, ft8_replay_path: Path) -> dict[str, Any]:
    return {
        "ft4": _analyze_single_replay(ft4_replay_path),
        "ft8": _analyze_single_replay(ft8_replay_path),
    }


def _analyze_single_replay(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    packets = payload.get("packets", [])
    business = [bytes.fromhex(item["payload_hex"]) for item in packets if item.get("tag") == "business_packet"]
    nonzero_counts = [sum(1 for byte in item if byte) for item in business]
    hotspots = _collect_nonzero_hotspots(business)
    return {
        "path": str(path),
        "packet_count": len(packets),
        "business_packet_count": len(business),
        "business_packet_nonzero_summary": {
            "mean": round(mean(nonzero_counts), 2) if nonzero_counts else 0.0,
            "min": min(nonzero_counts) if nonzero_counts else 0,
            "max": max(nonzero_counts) if nonzero_counts else 0,
        },
        "business_packet_hotspots": hotspots,
    }


def _collect_nonzero_hotspots(packets: list[bytes], *, limit: int = 12) -> list[int]:
    counts: dict[int, int] = {}
    for packet in packets:
        for index, byte in enumerate(packet):
            if byte:
                counts[index] = counts.get(index, 0) + 1
    return [item[0] for item in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _load_digimanager_methods(binary_path: Path) -> dict[str, dict[str, Any]]:
    if dnfile is None or read_method_body_from_bytes is None:
        return {"available": False, "reason": "dnfile_or_dncil_missing"}

    pe = dnfile.dnPE(str(binary_path))
    constructor_tokens = _extract_ctor_array_tokens(pe)
    methods: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(pe.net.mdtables.MethodDef.rows, start=1):
        name = str(row.Name)
        if name not in {SETCECMESSAGE2_NAME, SETDIGITALDATA2_NAME, UDPDATACHECK_NAME}:
            continue
        try:
            body = read_method_body_from_bytes(pe.get_data(row.Rva, 4096))
        except Exception:
            continue
        lines = [f"{ins.offset:04x} {ins.opcode} {ins.operand}" for ins in body.instructions]
        method_info = {
            "token": f"0x{0x06000000 + index:08x}",
            "rva": int(row.Rva),
            "lines": lines,
            "calls_command35": any("ldc.i4.s 53" in line for line in lines) if name == SETDIGITALDATA2_NAME else False,
            "protocol8_calls_setdigitaldata2": any("ldc.i4.8" in line for line in lines) and any("call token(0x06000014)" in line for line in lines) if name == UDPDATACHECK_NAME else False,
        }
        if name == SETCECMESSAGE2_NAME:
            method_info["stx_bytes"] = _read_ctor_array_bytes(pe, constructor_tokens.get("stx"))
            method_info["etx_bytes"] = _read_ctor_array_bytes(pe, constructor_tokens.get("etx"))
        methods[name] = method_info
    return methods


def _extract_ctor_array_tokens(pe: Any) -> dict[str, int]:
    if read_method_body_from_bytes is None:
        return {}
    for row in pe.net.mdtables.MethodDef.rows:
        if str(row.Name) != CTOR_NAME:
            continue
        body = read_method_body_from_bytes(pe.get_data(row.Rva, 4096))
        tokens: list[int] = []
        for ins in body.instructions:
            op = str(ins.opcode)
            operand = str(ins.operand)
            if op == "ldtoken" and operand.startswith("token("):
                token = int(operand.split("(")[1].split(")")[0], 16)
                tokens.append(token)
        if len(tokens) >= 2:
            return {"stx": tokens[0], "etx": tokens[1]}
        return {}
    return {}


def _read_ctor_array_bytes(pe: Any, token: int | None) -> list[int]:
    if token is None or not pe.net.mdtables.FieldRva:
        return []
    index = (token & 0x00FFFFFF) - 1
    if index < 0 or index >= len(pe.net.mdtables.Field.rows):
        return []
    target_field = pe.net.mdtables.Field.rows[index]
    for row in pe.net.mdtables.FieldRva.rows:
        field = row.Field.row
        if field is target_field:
            return list(pe.get_data(row.Rva, 4))
    return []


def _build_candidate_windows(
    raw_firmware: bytes,
    command_hits: dict[str, list[dict[str, Any]]],
    seeded_compare_hits: dict[str, list[dict[str, Any]]],
) -> list[CapstoneWindow]:
    windows: list[CapstoneWindow] = []
    sources = {
        "dispatcher_near_0x32": command_hits.get("0x32") or seeded_compare_hits.get("0x32") or [],
        "dispatcher_near_0x33": command_hits.get("0x33") or seeded_compare_hits.get("0x33") or [],
        "dispatcher_near_0x35": command_hits.get("0x35") or seeded_compare_hits.get("0x35") or [],
    }
    for label, hits in sources.items():
        if not hits:
            continue
        windows.append(_disassemble_window(raw_firmware, hits[0]["offset"], label=label))
    return windows


def _build_string_windows(raw_firmware: bytes) -> list[CapstoneWindow]:
    windows: list[CapstoneWindow] = []
    for anchor in STRING_ANCHORS:
        offset = raw_firmware.find(anchor.encode("ascii"))
        if offset == -1:
            continue
        windows.append(_disassemble_window(raw_firmware, offset, label=f"string_anchor_{anchor}"))
    return windows


def _disassemble_window(raw_firmware: bytes, center_offset: int, *, label: str, before: int = 96, after: int = 96) -> CapstoneWindow:
    start = max(0, center_offset - before)
    end = min(len(raw_firmware), center_offset + after)
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    lower = center_offset - 40
    upper = center_offset + 40
    for ins in md.disasm(raw_firmware[start:end], start):
        if ins.address < lower:
            continue
        if ins.address > upper:
            break
        lines.append(f"{ins.address:#06x} {ins.mnemonic} {ins.op_str}".rstrip())
    return CapstoneWindow(label=label, center_offset=center_offset, start_offset=start, end_offset=end, lines=lines)
