from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import median
from typing import Any


@dataclass(slots=True)
class ReplayPacket:
    timestamp_offset_ms: int
    payload: bytes
    tag: str
    mode: str


@dataclass(slots=True)
class ReplayCapture:
    source_capture: str
    mode: str
    destination_port: int
    packets: list[ReplayPacket]


def load_replay_capture(path: Path) -> ReplayCapture:
    raw = json.loads(path.read_text(encoding="utf-8"))
    packets = [
        ReplayPacket(
            timestamp_offset_ms=int(item["timestamp_offset_ms"]),
            payload=bytes.fromhex(item["payload_hex"]),
            tag=str(item["tag"]),
            mode=str(item["mode"]),
        )
        for item in raw.get("packets", [])
    ]
    return ReplayCapture(
        source_capture=str(raw.get("source_capture", path.name)),
        mode=str(raw.get("mode", path.stem)),
        destination_port=int(raw.get("destination_port", 0)),
        packets=packets,
    )


def summarize_capture(capture: ReplayCapture) -> dict[str, Any]:
    marker_packets = [packet for packet in capture.packets if packet.tag.endswith("mode_marker")]
    business_packets = [packet for packet in capture.packets if packet.tag == "business_packet"]
    intervals = [
        second.timestamp_offset_ms - first.timestamp_offset_ms
        for first, second in zip(capture.packets, capture.packets[1:])
    ]
    nonzero_tail_examples = [_nonzero_tail(packet.payload) for packet in business_packets[:8]]
    marker_payloads = [_marker_summary(packet.payload) for packet in marker_packets]

    return {
        "source_capture": capture.source_capture,
        "mode": capture.mode,
        "destination_port": capture.destination_port,
        "packet_count": len(capture.packets),
        "marker_count": len(marker_packets),
        "business_count": len(business_packets),
        "interval_median_ms": median(intervals) if intervals else None,
        "interval_min_ms": min(intervals) if intervals else None,
        "interval_max_ms": max(intervals) if intervals else None,
        "marker_payloads": marker_payloads,
        "business_nonzero_tail_examples": nonzero_tail_examples,
    }


def compare_upstream_and_forwarding(ft4_capture: ReplayCapture, ft8_capture: ReplayCapture) -> dict[str, Any]:
    ft4_marker = _first_marker_payload(ft4_capture)
    ft8_marker = _first_marker_payload(ft8_capture)

    ft4_upstream = _marker_summary(ft4_marker) if ft4_marker else None
    ft8_upstream = _marker_summary(ft8_marker) if ft8_marker else None

    ft4_stock_header = build_setdigitaldata2_header(ft4_marker, preserve_mode_hint=False) if ft4_marker else None
    ft8_stock_header = build_setdigitaldata2_header(ft8_marker, preserve_mode_hint=False) if ft8_marker else None
    ft4_patched_header = build_setdigitaldata2_header(ft4_marker, preserve_mode_hint=True) if ft4_marker else None
    ft8_patched_header = build_setdigitaldata2_header(ft8_marker, preserve_mode_hint=True) if ft8_marker else None

    return {
        "upstream": {
            "ft4": ft4_upstream,
            "ft8": ft8_upstream,
            "distinct_upstream_modes": bool(ft4_upstream and ft8_upstream and ft4_upstream != ft8_upstream),
        },
        "stock_setdigitaldata2_headers": {
            "ft4": _hex_or_none(ft4_stock_header),
            "ft8": _hex_or_none(ft8_stock_header),
            "headers_identical_except_length": _same_except_length(ft4_stock_header, ft8_stock_header),
        },
        "patched_setdigitaldata2_headers": {
            "ft4": _hex_or_none(ft4_patched_header),
            "ft8": _hex_or_none(ft8_patched_header),
            "headers_still_share_same_command_path": True,
        },
        "judgement": build_flow_judgement(
            ft4_upstream=ft4_upstream,
            ft8_upstream=ft8_upstream,
            ft4_stock_header=ft4_stock_header,
            ft8_stock_header=ft8_stock_header,
            ft4_patched_header=ft4_patched_header,
            ft8_patched_header=ft8_patched_header,
        ),
    }


def build_setdigitaldata2_header(marker_payload: bytes, *, preserve_mode_hint: bool) -> bytes:
    if len(marker_payload) < 7:
        raise ValueError("Mode marker payload is too short to build SetDigitalData2 header.")

    length = marker_payload[4]
    subfreq_high = marker_payload[5]
    subfreq_low = marker_payload[6]
    header_byte2 = length if preserve_mode_hint else 0
    return bytes([subfreq_high, subfreq_low, header_byte2, 0, length])


def build_flow_report(ft4_path: Path, ft8_path: Path) -> dict[str, Any]:
    ft4_capture = load_replay_capture(ft4_path)
    ft8_capture = load_replay_capture(ft8_path)
    return {
        "captures": {
            "ft4": summarize_capture(ft4_capture),
            "ft8": summarize_capture(ft8_capture),
        },
        "comparison": compare_upstream_and_forwarding(ft4_capture, ft8_capture),
        "next_step": (
            "上游 WSJT-X -> DigiManager 的 FT4 数据已经与 FT8 明显不同；"
            "当前主要风险在 DigiManager 继续把 FT4 送进同一个 command 0x35 发送路径。"
            "下一步应优先继续拆 DigiManager 的发送节拍，而不是先怀疑 WSJT-X 输出本身。"
        ),
    }


def render_flow_report_markdown(report: dict[str, Any]) -> str:
    ft4 = report["captures"]["ft4"]
    ft8 = report["captures"]["ft8"]
    comparison = report["comparison"]
    lines = [
        "# WSJT-X -> DigiManager FT4 数据流分析",
        "",
        "## 结论",
        "- WSJT-X 给 DigiManager 的 FT4 上游数据与 FT8 明显不同，不是假 FT4。",
        "- DigiManager 原始 SetDigitalData2 头字段会把 FT4/FT8 的差异大量压平，只剩长度差异。",
        "- 当前 patched DigiManager 已经保留更多模式提示，但仍然走同一条 command 0x35 发送路径。",
        "- 因此现在最该继续查的是 DigiManager 的发送节拍，而不是先怀疑 WSJT-X 输出。",
        "",
        "## 抓包摘要",
        f"- FT4: {ft4['packet_count']} 包，marker {ft4['marker_count']} 个，中位间隔 {ft4['interval_median_ms']} ms",
        f"- FT8: {ft8['packet_count']} 包，marker {ft8['marker_count']} 个，中位间隔 {ft8['interval_median_ms']} ms",
        "",
        "## 上游模式包",
        f"- FT4 marker: {comparison['upstream']['ft4']}",
        f"- FT8 marker: {comparison['upstream']['ft8']}",
        "",
        "## SetDigitalData2 头字段对照",
        f"- 原始路径 FT4: {comparison['stock_setdigitaldata2_headers']['ft4']}",
        f"- 原始路径 FT8: {comparison['stock_setdigitaldata2_headers']['ft8']}",
        f"- 现补丁路径 FT4: {comparison['patched_setdigitaldata2_headers']['ft4']}",
        f"- 现补丁路径 FT8: {comparison['patched_setdigitaldata2_headers']['ft8']}",
        "",
        "## 判断",
        f"- {comparison['judgement']}",
        "",
        "## 下一步",
        f"- {report['next_step']}",
    ]
    return "\n".join(lines) + "\n"


def build_flow_judgement(
    *,
    ft4_upstream: dict[str, Any] | None,
    ft8_upstream: dict[str, Any] | None,
    ft4_stock_header: bytes | None,
    ft8_stock_header: bytes | None,
    ft4_patched_header: bytes | None,
    ft8_patched_header: bytes | None,
) -> str:
    if not ft4_upstream or not ft8_upstream:
        return "缺少上游模式包，暂时无法判断。"
    if ft4_upstream == ft8_upstream:
        return "上游模式包没有显著差异，这与当前已有证据不一致，需要重新检查样本。"
    if ft4_stock_header and ft8_stock_header and _same_except_length(ft4_stock_header, ft8_stock_header):
        if ft4_patched_header and ft8_patched_header and ft4_patched_header != ft8_patched_header:
            return (
                "WSJT-X 上游已经提供了真实 FT4/FT8 差异，但 DigiManager 原始 sender 头字段几乎把差异压平成同一路径。"
                "当前补丁只是在同一 command 0x35 路径里保留更多模式提示，仍不能证明时序已经正确。"
            )
        return (
            "WSJT-X 上游已经提供了真实 FT4/FT8 差异，但 DigiManager 原始 sender 头字段把差异压平成近乎同一路径。"
        )
    return "上游差异存在，而且 sender 头字段也保留了部分差异；当前更该继续看发送节拍而不是怀疑 WSJT-X 本身。"


def _first_marker_payload(capture: ReplayCapture) -> bytes | None:
    for packet in capture.packets:
        if packet.tag.endswith("mode_marker"):
            return packet.payload
    return None


def _marker_summary(payload: bytes) -> dict[str, Any]:
    return {
        "prefix_hex": payload[:8].hex(" "),
        "length_byte": payload[4],
        "subfreq_raw": int.from_bytes(payload[5:7], "big"),
        "bytes_7_to_15_hex": payload[7:16].hex(" "),
        "first_32_hex": payload[:32].hex(" "),
    }


def _nonzero_tail(payload: bytes) -> dict[str, Any]:
    nonzero_offsets = [index for index, byte in enumerate(payload) if byte != 0]
    tail = payload[-16:]
    return {
        "nonzero_count": len(nonzero_offsets),
        "first_nonzero_offsets": nonzero_offsets[:12],
        "tail_hex": tail.hex(" "),
    }


def _same_except_length(left: bytes | None, right: bytes | None) -> bool:
    if not left or not right or len(left) != 5 or len(right) != 5:
        return False
    return left[:2] == right[:2] and left[2:4] == right[2:4]


def _hex_or_none(value: bytes | None) -> str | None:
    return value.hex(" ") if value else None
