from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # type: ignore

from sat_bridge.reverse_tools import try_unpack_uvk5_packed_firmware


FT4_PRIMARY_SOURCES = [
    {
        "title": "FT4 and FT8 Communication Protocols",
        "url": "https://wsjt.sourceforge.io/FT4_FT8_QEX.pdf",
        "notes": "WSJT-X authors' protocol paper. FT4 is a 7.5 s T/R, 4-GFSK mode with much shorter symbol timing than FT8.",
    }
]


@dataclass(slots=True)
class CapstoneWindow:
    label: str
    center_offset: int
    start_offset: int
    end_offset: int
    lines: list[str]


def analyze_cec_ft8_scheme(
    *,
    firmware_path: Path,
    digimanager_summary_path: Path | None = None,
    timing_report_path: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, Any]:
    firmware_bytes = firmware_path.read_bytes()
    unpacked = try_unpack_uvk5_packed_firmware(firmware_bytes)
    if not unpacked.get("ok"):
        raise ValueError("Could not unpack the real packed firmware for FT8 scheme analysis.")

    raw_bytes: bytes = unpacked["raw_bytes"]
    windows = [
        disassemble_window(raw_bytes, 3496, label="retune_candidate_branch"),
        disassemble_window(raw_bytes, 34788, label="freq_format_reference_pool"),
        disassemble_window(raw_bytes, 38976, label="dig_plus_reference_pool"),
        disassemble_window(raw_bytes, 55208, label="lock_reference_pool"),
    ]
    command_hits = find_immediate_hits(raw_bytes, 0x32)

    digimanager_summary = (
        json.loads(digimanager_summary_path.read_text(encoding="utf-8"))
        if digimanager_summary_path and digimanager_summary_path.exists()
        else {}
    )
    timing_summary = (
        json.loads(timing_report_path.read_text(encoding="utf-8"))
        if timing_report_path and timing_report_path.exists()
        else {}
    )
    public_fsk_reference = analyze_public_fsk_reference(source_root) if source_root and source_root.exists() else {}

    report = {
        "inputs": {
            "firmware_path": str(firmware_path),
            "digimanager_summary_path": str(digimanager_summary_path) if digimanager_summary_path else None,
            "timing_report_path": str(timing_report_path) if timing_report_path else None,
            "source_root": str(source_root) if source_root else None,
        },
        "firmware": {
            "embedded_version": unpacked.get("embedded_version"),
            "raw_size_bytes": len(raw_bytes),
            "capstone_windows": [
                {
                    "label": item.label,
                    "center_offset": item.center_offset,
                    "start_offset": item.start_offset,
                    "end_offset": item.end_offset,
                    "lines": item.lines,
                }
                for item in windows
            ],
            "command_0x32_immediate_hits": command_hits,
        },
        "digimanager_summary": digimanager_summary,
        "timing_summary": timing_summary,
        "public_fsk_reference": public_fsk_reference,
        "ft4_primary_sources": FT4_PRIMARY_SOURCES,
    }
    report["judgement"] = infer_judgement(report)
    return report


def disassemble_window(raw_bytes: bytes, center_offset: int, *, label: str, before: int = 128, after: int = 96) -> CapstoneWindow:
    start = max(0, center_offset - before)
    end = min(len(raw_bytes), center_offset + after)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    lines: list[str] = []
    for ins in md.disasm(raw_bytes[start:end], start | 1):
        if ins.address < center_offset - 64:
            continue
        if ins.address >= center_offset + 40:
            break
        lines.append(f"{ins.address:#06x} {ins.mnemonic} {ins.op_str}".rstrip())
    return CapstoneWindow(label=label, center_offset=center_offset, start_offset=start, end_offset=end, lines=lines)


def find_immediate_hits(raw_bytes: bytes, immediate: int, *, limit: int = 12) -> list[dict[str, Any]]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    hits: list[dict[str, Any]] = []
    needle_a = f"#{immediate}"
    needle_b = f"#0x{immediate:x}"
    for ins in md.disasm(raw_bytes, 1):
        text = f"{ins.mnemonic} {ins.op_str}"
        if needle_a not in text and needle_b not in text:
            continue
        hits.append({"offset": ins.address, "instruction": text})
        if len(hits) >= limit:
            break
    return hits


def analyze_public_fsk_reference(source_root: Path) -> dict[str, Any]:
    aircopy_text = (source_root / "app" / "aircopy.c").read_text(encoding="utf-8", errors="ignore")
    bk_text = (source_root / "driver" / "bk4819.c").read_text(encoding="utf-8", errors="ignore")
    radio_text = (source_root / "radio.c").read_text(encoding="utf-8", errors="ignore")

    reference = {
        "aircopy_uses_sendfskdata": "BK4819_SendFSKData(g_FSK_Buffer);" in aircopy_text,
        "aircopy_packet_words": 36 if "uint16_t g_FSK_Buffer[36];" in aircopy_text else None,
        "aircopy_reg72_baud_1200": "BK4819_WriteRegister(BK4819_REG_72, 0x3065);" in bk_text,
        "aircopy_reg58_fsk_enable": "BK4819_WriteRegister(BK4819_REG_58, 0x00C1);" in bk_text,
        "aircopy_reg5d_length_72_bytes": "BK4819_WriteRegister(BK4819_REG_5D, 0x4700);" in bk_text,
        "aircopy_comments": extract_matching_lines(
            bk_text,
            [
                r"Tone2 baudrate 1200",
                r"FSK Enable, FSK 1\.2K RX Bandwidth",
                r"FSK Data Length 72 Bytes",
            ],
        ),
        "radio_supports_baseband_modes": all(
            token in radio_text
            for token in ("MODULATION_USB", "BK4819_AF_BASEBAND2", "MODULATION_RAW", "BK4819_AF_BASEBAND1")
        ),
        "radio_baseband_lines": extract_matching_lines(
            radio_text,
            [
                r"MODULATION_USB",
                r"BK4819_AF_BASEBAND2",
                r"MODULATION_RAW",
                r"BK4819_AF_BASEBAND1",
            ],
        ),
    }
    return reference


def extract_matching_lines(text: str, patterns: list[str]) -> list[str]:
    results: list[str] = []
    for line in text.splitlines():
        for pattern in patterns:
            if re.search(pattern, line):
                results.append(line.strip())
                break
    return results


def infer_judgement(report: dict[str, Any]) -> dict[str, Any]:
    timing = report.get("timing_summary", {})
    digimanager = report.get("digimanager_summary", {})
    public_fsk = report.get("public_fsk_reference", {})

    ft4_gate_open = any(
        patch.get("name") == "udpdatacheck_ft4_forward_gate"
        for patch in digimanager.get("applied_patches", [])
    )
    same_slow_behavior_on_both = True
    if timing:
        comparison = timing.get("comparison", {})
        same_slow_behavior_on_both = comparison.get("same_payload_shape", False) is False

    conclusion_lines = [
        "真实 0.3q 的 FT8/数字发射链更像“主机准备业务节拍 + 固件走 CEC 洁净数字发射底座”，而不像直接复用 BK4819 的 packet FSK 硬件调制器。",
        "BK4819 公开 FSK 链在源码里明确配置为 1200 baud / 72-byte packet 模式，这和 FT4 的短符号、高速 4-tone 节拍并不匹配。",
        "patched DigiManager 只放通 protocol 4 以后，原版固件和 patched 固件都能起 FT4 发射，但都出现慢节拍，说明当前主矛盾先看 DigiManager 发送节拍更合理。",
        "因此：单纯依靠 BK4819 packet FSK + 现有 CEC 路线，不太可能直接发出合格 FT4；但沿用 CEC 的“洁净数字注入”思路，改写 FT4 专用发送节拍，原则上是可行的。",
    ]

    return {
        "ft4_gate_open_via_digimanager_patch": ft4_gate_open,
        "public_bk4819_packet_fsk_fit_for_ft4": "unlikely",
        "likely_author_ft8_tx_scheme": "custom_digital_sender_chain_plus_clean_baseband_or_custom_cec_tx",
        "current_best_direction": "treat_digimanager_sender_timing_as_primary_ft4_fix_target",
        "confidence": "medium",
        "same_slow_behavior_on_stock_and_patched_firmware": same_slow_behavior_on_both,
        "summary_lines": conclusion_lines,
        "recommended_next_step": (
            "不要再把 FT4 只当成纯固件门控问题；先修 DigiManager 的 FT4 专用发送节拍，"
            "把固定频点 FT4 做到可被第二接收机正常解码，再回接 patched 固件测试改频。"
        ),
        "evidence": {
            "aircopy_uses_packet_fsk": public_fsk.get("aircopy_uses_sendfskdata"),
            "aircopy_packet_words": public_fsk.get("aircopy_packet_words"),
            "aircopy_reg72_baud_1200": public_fsk.get("aircopy_reg72_baud_1200"),
            "radio_supports_baseband_modes": public_fsk.get("radio_supports_baseband_modes"),
            "timing_diagnosis": timing.get("diagnosis", {}),
            "digimanager_applied_patches": [patch.get("name") for patch in digimanager.get("applied_patches", [])],
        },
    }


def render_cec_ft8_scheme_markdown(report: dict[str, Any]) -> str:
    judgement = report["judgement"]
    firmware = report["firmware"]
    public_fsk = report.get("public_fsk_reference", {})
    lines = [
        "# CEC 0.3q FT8 发射方案与 FT4 可行性分析",
        "",
        "## 核心判断",
        f"- 作者当前的 FT8 发射方案更像：`{judgement['likely_author_ft8_tx_scheme']}`",
        f"- BK4819 公开 packet FSK 硬件链是否适合直接做 FT4：`{judgement['public_bk4819_packet_fsk_fit_for_ft4']}`",
        f"- 当前最应该优先修的方向：`{judgement['current_best_direction']}`",
        f"- 置信度：`{judgement['confidence']}`",
        "",
        "## 结论说明",
    ]
    for item in judgement["summary_lines"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## FT4 正式制式要点（来源：WSJT-X 作者协议论文）",
            "- FT4 是比 FT8 更快的短周期数字模式，属于 4-GFSK / 4-tone 家族。",
            "- 它不是简单把 FT8 的门控打开就能得到的模式；它要求不同的符号时长、不同的发送节拍和不同的模式组织方式。",
            "- 因此，任何“只让 FT4 走进 FT8 发送器”的改法，都可能出现能起发射但节拍不合规的问题。",
        ]
    )
    for source in report.get("ft4_primary_sources", []):
        lines.append(f"- 参考：[{source['title']}]({source['url']})")

    lines.extend(
        [
            "",
            "## 公开源码里 BK4819 FSK 硬件链告诉了我们什么",
            f"- `AIRCOPY` 是否直接调用 `BK4819_SendFSKData`：`{public_fsk.get('aircopy_uses_sendfskdata')}`",
            f"- `AIRCOPY` 缓冲区是否是固定 36 个 16-bit word：`{public_fsk.get('aircopy_packet_words')}`",
            f"- `BK4819_REG_72` 是否明确写了 1200 baud：`{public_fsk.get('aircopy_reg72_baud_1200')}`",
            f"- `BK4819_REG_58` 是否明确打开了 FSK packet 模式：`{public_fsk.get('aircopy_reg58_fsk_enable')}`",
            f"- `BK4819_REG_5D` 是否明确写死 72 Bytes 数据长度：`{public_fsk.get('aircopy_reg5d_length_72_bytes')}`",
            "",
            "这说明公开源码里的 BK4819 FSK 硬件链，本质上是一个固定包长、固定速率的 packet FSK 发送器，",
            "它更像空口拷贝 / 分组数据链，而不像 FT4/FT8 这种超慢速、窄间隔、多音调数字模式的标准发送器。",
            "",
            "## 为什么我们怀疑作者的 FT8 不是走这条 packet FSK 硬件链",
            "- 真实系统里，patched DigiManager 放通 FT4 后，原版固件和 patched 固件都能起发射，但都出现慢节拍。",
            "- 这更像‘把 FT4 塞进了一个本来给 FT8 用的发送时序器’，而不像 BK4819 硬件 packet FSK 自己决定了 FT4 节拍。",
            "- 公开源码同时又保留了 `BASEBAND1 / BASEBAND2` 这类 baseband AF 路径，说明芯片并不只会 packet FSK 一条路。",
            "- 因而更合理的解释是：作者的 FT8 方案是主机和固件配合走一条自定义数字发送链，BK4819 只负责比较干净的射频/基带输出，不是直接让它按 packet FSK 协议发 FT8。",
            "",
            "## capstone 观察到的真实固件锚点",
            f"- embedded version: `{firmware['embedded_version']}`",
            "- 关键反汇编窗口已经输出到 JSON/Markdown 报告，可供后续协作者继续追。",
            "- 当前这些窗口更能证明‘数字模式、锁频、频率显示、命令入口都是真实存在的’，但还不足以单靠固件一侧证明 FT8 就是 packet FSK 发射。",
            "",
            "## 对‘K6 芯片的 FSK 发射结合 CEC 方案能不能做 FT4’的判断",
            "### 不能直接成立的版本",
            "- 如果这里说的 ‘FSK 发射’ 指的是 `BK4819_SendFSKData` 这条 1200/2400 packet FSK 硬件链，",
            "  那它大概率不能直接发出**合格 FT4**。",
            "- 原因不是它完全发不出东西，而是它的速率、包结构、工作方式都和 FT4 不匹配。",
            "",
            "### 有希望成立的版本",
            "- 如果这里说的 ‘结合 CEC 方案’ 指的是：保留 CEC 当前‘洁净数字注入、避免 K5 模拟音频缺陷’的总体思路，",
            "  但把 `FT4` 的**专用时序 / 分帧 / 发送节拍**重新做对，",
            "  那原则上是可行的。",
            "- 换句话说，真正可行的方向不是‘让 BK4819 packet FSK 直接承担 FT4’，",
            "  而是‘让 DigiManager / CEC 的数字发送链学会正确的 FT4 节拍，再继续利用 BK4819 的干净发射底座’。",
            "",
            "## 当前主线建议",
            f"- {judgement['recommended_next_step']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_cec_ft8_scheme_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cec-ft8-ft4-feasibility.json"
    md_path = output_dir / "cec-ft8-ft4-feasibility.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_cec_ft8_scheme_markdown(report), encoding="utf-8")
    return json_path, md_path
