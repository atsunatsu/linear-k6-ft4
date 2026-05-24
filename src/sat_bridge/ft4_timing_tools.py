from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

from sat_bridge.udp_capture_tools import ReplayPacket, ReplaySequence, load_udp_replay_sequence


@dataclass(slots=True)
class IntervalStats:
    count: int
    min_ms: int | None
    max_ms: int | None
    mean_ms: float | None
    median_ms: float | None


def summarize_replay_cadence(path_or_sequence: str | Path | ReplaySequence) -> dict[str, Any]:
    sequence = _load_sequence(path_or_sequence)
    offsets = [packet.timestamp_offset_ms for packet in sequence.packets]
    packet_lengths = [packet.payload_len for packet in sequence.packets]
    tag_counts = Counter(packet.tag for packet in sequence.packets)
    intervals = [
        current.timestamp_offset_ms - previous.timestamp_offset_ms
        for previous, current in zip(sequence.packets, sequence.packets[1:])
    ]
    batches = _group_tag_batches(sequence.packets)

    return {
        "source_capture": sequence.source_capture,
        "mode": sequence.mode,
        "destination_port": sequence.destination_port,
        "packet_count": len(sequence.packets),
        "duration_ms": offsets[-1] - offsets[0] if len(offsets) >= 2 else 0,
        "first_packet_ms": offsets[0] if offsets else None,
        "last_packet_ms": offsets[-1] if offsets else None,
        "payload_len_distribution": dict(Counter(packet_lengths)),
        "tag_counts": dict(tag_counts),
        "interval_stats": _interval_stats(intervals),
        "first_intervals_ms": intervals[:12],
        "last_intervals_ms": intervals[-12:],
        "batches": batches,
        "marker_offsets_ms": {
            tag: [packet.timestamp_offset_ms for packet in sequence.packets if packet.tag == tag]
            for tag in sorted(tag_counts)
            if tag != "business_packet"
        },
    }


def compare_mode_cadence(
    ft4_path_or_sequence: str | Path | ReplaySequence,
    ft8_path_or_sequence: str | Path | ReplaySequence,
) -> dict[str, Any]:
    ft4 = summarize_replay_cadence(ft4_path_or_sequence)
    ft8 = summarize_replay_cadence(ft8_path_or_sequence)

    ft4_median = ft4["interval_stats"]["median_ms"]
    ft8_median = ft8["interval_stats"]["median_ms"]
    duration_ratio = _safe_ratio(ft4["duration_ms"], ft8["duration_ms"])
    median_ratio = _safe_ratio(ft4_median, ft8_median)

    return {
        "ft4": ft4,
        "ft8": ft8,
        "comparison": {
            "packet_count_delta": ft4["packet_count"] - ft8["packet_count"],
            "duration_ratio_ft4_over_ft8": duration_ratio,
            "median_interval_ratio_ft4_over_ft8": median_ratio,
            "tag_count_delta": {
                key: ft4["tag_counts"].get(key, 0) - ft8["tag_counts"].get(key, 0)
                for key in sorted(set(ft4["tag_counts"]) | set(ft8["tag_counts"]))
            },
            "same_payload_shape": ft4["payload_len_distribution"] == ft8["payload_len_distribution"],
        },
        "diagnosis": _diagnose_comparison(ft4, ft8),
    }


def render_mode_cadence_text(report: dict[str, Any]) -> str:
    ft4 = report["ft4"]
    ft8 = report["ft8"]
    comparison = report["comparison"]
    diagnosis = report["diagnosis"]
    lines = [
        f"FT4 source: {ft4['source_capture']}",
        f"FT8 source: {ft8['source_capture']}",
        "FT4 summary:",
        f"- packet_count: {ft4['packet_count']}",
        f"- duration_ms: {ft4['duration_ms']}",
        f"- interval_stats: {ft4['interval_stats']}",
        f"- tag_counts: {ft4['tag_counts']}",
        "FT8 summary:",
        f"- packet_count: {ft8['packet_count']}",
        f"- duration_ms: {ft8['duration_ms']}",
        f"- interval_stats: {ft8['interval_stats']}",
        f"- tag_counts: {ft8['tag_counts']}",
        "Comparison:",
        f"- packet_count_delta: {comparison['packet_count_delta']}",
        f"- duration_ratio_ft4_over_ft8: {comparison['duration_ratio_ft4_over_ft8']}",
        f"- median_interval_ratio_ft4_over_ft8: {comparison['median_interval_ratio_ft4_over_ft8']}",
        f"- same_payload_shape: {comparison['same_payload_shape']}",
        "Diagnosis:",
        f"- likely_timing_owner: {diagnosis['likely_timing_owner']}",
        f"- confidence: {diagnosis['confidence']}",
        f"- summary: {diagnosis['summary']}",
    ]
    return "\n".join(lines)


def write_mode_cadence_report(
    ft4_path_or_sequence: str | Path | ReplaySequence,
    ft8_path_or_sequence: str | Path | ReplaySequence,
    *,
    output_json: str | Path,
    output_text: str | Path | None = None,
) -> dict[str, Any]:
    report = compare_mode_cadence(ft4_path_or_sequence, ft8_path_or_sequence)
    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if output_text is not None:
        output_text_path = Path(output_text)
        output_text_path.parent.mkdir(parents=True, exist_ok=True)
        output_text_path.write_text(render_mode_cadence_text(report), encoding="utf-8")
    return report


def _load_sequence(path_or_sequence: str | Path | ReplaySequence) -> ReplaySequence:
    if isinstance(path_or_sequence, ReplaySequence):
        return path_or_sequence
    return load_udp_replay_sequence(path_or_sequence)


def _interval_stats(intervals: list[int]) -> dict[str, int | float | None]:
    if not intervals:
        return {
            "count": 0,
            "min_ms": None,
            "max_ms": None,
            "mean_ms": None,
            "median_ms": None,
        }
    return {
        "count": len(intervals),
        "min_ms": min(intervals),
        "max_ms": max(intervals),
        "mean_ms": round(mean(intervals), 3),
        "median_ms": round(median(intervals), 3),
    }


def _group_tag_batches(packets: list[ReplayPacket]) -> list[dict[str, Any]]:
    if not packets:
        return []
    batches: list[dict[str, Any]] = []
    current_tag = packets[0].tag
    current_packets = [packets[0]]
    for packet in packets[1:]:
        if packet.tag == current_tag:
            current_packets.append(packet)
            continue
        batches.append(_batch_summary(current_tag, current_packets))
        current_tag = packet.tag
        current_packets = [packet]
    batches.append(_batch_summary(current_tag, current_packets))
    return batches


def _batch_summary(tag: str, packets: list[ReplayPacket]) -> dict[str, Any]:
    start = packets[0].timestamp_offset_ms
    end = packets[-1].timestamp_offset_ms
    intervals = [
        current.timestamp_offset_ms - previous.timestamp_offset_ms
        for previous, current in zip(packets, packets[1:])
    ]
    return {
        "tag": tag,
        "packet_count": len(packets),
        "start_ms": start,
        "end_ms": end,
        "duration_ms": end - start,
        "interval_stats": _interval_stats(intervals),
        "payload_lengths": sorted({packet.payload_len for packet in packets}),
    }


def _safe_ratio(left: int | float | None, right: int | float | None) -> float | None:
    if left is None or right in (None, 0):
        return None
    return round(float(left) / float(right), 6)


def _diagnose_comparison(ft4: dict[str, Any], ft8: dict[str, Any]) -> dict[str, Any]:
    duration_ratio = _safe_ratio(ft4["duration_ms"], ft8["duration_ms"])
    median_ratio = _safe_ratio(ft4["interval_stats"]["median_ms"], ft8["interval_stats"]["median_ms"])
    if duration_ratio is not None and duration_ratio > 1.3:
        return {
            "likely_timing_owner": "pc_side_sender_chain",
            "confidence": "medium",
            "summary": "FT4 total send duration is significantly longer than FT8 while payload shape still matches, which is more consistent with DigiManager-side pacing than a fixed-frequency-only firmware gate.",
        }
    if median_ratio is not None and median_ratio > 1.3:
        return {
            "likely_timing_owner": "pc_side_sender_chain",
            "confidence": "medium",
            "summary": "FT4 packet-to-packet cadence is noticeably slower than FT8, pointing first to the PC-side send chain or batching strategy.",
        }
    return {
        "likely_timing_owner": "still_unclear",
        "confidence": "low",
        "summary": "The replay timing difference is not yet large enough to pin on one side from these captures alone.",
    }

