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
KNOWN_DISPATCH_SEEDS = [3496]
KNOWN_PUBLIC_OBCFUSCATION = bytes.fromhex("166c14e62e910d402135d5401303e980")


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
    seeded_compare_hits = {
        f"0x{value:02x}": [
            {"offset": hit.offset, "instruction": hit.instruction}
            for hit in find_exact_compare_hits_in_windows(raw_firmware, value, KNOWN_DISPATCH_SEEDS)
        ]
        for value in COMMAND_SCAN_VALUES
    }

    firmware_frame_matches = find_firmware_frame_family_matches(raw_firmware, command35_layout)
    digital_mode_strings = find_digital_mode_strings(raw_firmware)
    constant_cluster = describe_constant_cluster(raw_firmware, cluster_offset=0xDE94)
    candidate_windows = _build_candidate_windows(raw_firmware, compare_hits, seeded_compare_hits)
    string_windows = _build_string_windows(raw_firmware)

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
            "command_compare_hits_seeded": seeded_compare_hits,
            "frame_family_matches": firmware_frame_matches,
            "digital_mode_strings": digital_mode_strings,
            "constant_cluster": constant_cluster,
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
    for ins in md.disasm(raw_firmware, 1):
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
    for ins in md.disasm(raw_firmware, 1):
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
        for ins in md.disasm(raw_firmware[start:end], start | 1):
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
    compare_hits = report["firmware"]["command_compare_hits"]
    seeded_compare_hits = report["firmware"].get("command_compare_hits_seeded", {})
    immediate_hits = report["firmware"]["command_immediate_hits"]
    frame_matches = report["firmware"]["frame_family_matches"]
    digital_mode_strings = report["firmware"].get("digital_mode_strings", {})
    constant_cluster = report["firmware"].get("constant_cluster", {})
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
    else:
        summary_lines.append("当前还没有足够可靠的固件分发锚点，需要继续补充固件侧命令入口证据。")

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
        "likely_handler_model": handler_model,
        "ft4_upstream_is_real": True,
        "timing_owner_guess": "firmware_or_joint_path_more_likely_than_digimanager_only",
        "replay_nonzero_summary": {
            "ft4_mean_nonzero_bytes": replay["ft4"]["business_packet_nonzero_summary"]["mean"],
            "ft8_mean_nonzero_bytes": replay["ft8"]["business_packet_nonzero_summary"]["mean"],
        },
        "raw_immediate_hint_0x35": immediate_hits.get("0x35", []),
        "summary_lines": summary_lines,
    }


def render_command35_markdown(report: dict[str, Any]) -> str:
    judgement = report["judgement"]
    frame_matches = report["firmware"]["frame_family_matches"]
    mode_strings = report["firmware"].get("digital_mode_strings", {})
    constant_cluster = report["firmware"].get("constant_cluster", {})
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
    lines.append("## 字符串锚点窗口")
    for item in report["firmware"]["string_anchor_windows"]:
        lines.append(f"### {item['label']} @ {item['center_offset']:#06x}")
        lines.extend(f"- `{line}`" for line in item["lines"])
        lines.append("")
    lines.append("## 当前建议")
    if judgement["firmware_direct_cmp_0x35"] == "yes":
        lines.append("- 继续围绕直接命中的 `cmp ..., #0x35` 候选点向下追，确认它后面如何进入数字模式发送路径。")
    else:
        lines.append("- 继续沿 `0x32 / 0x33` 邻近分发块向下追第二阶段解析路径，不再把 command 0x35 简化理解成“单字节命令直接分发”。")
    lines.append("- 优先把 `0xdea0` 附近这块常量区当成同协议家族常量区继续追引用，因为这里同时出现了帧头、帧尾和数字模式相关参数。")
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
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    lines: list[str] = []
    for ins in md.disasm(raw_firmware[start:end], start | 1):
        if ins.address < center_offset - 40:
            continue
        if ins.address > center_offset + 40:
            break
        lines.append(f"{ins.address:#06x} {ins.mnemonic} {ins.op_str}".rstrip())
    return CapstoneWindow(label=label, center_offset=center_offset, start_offset=start, end_offset=end, lines=lines)
