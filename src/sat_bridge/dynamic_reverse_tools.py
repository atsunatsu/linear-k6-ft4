from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sat_bridge.udp_capture_tools import parse_pcapng_udp_events


RETUNE_WINDOW_MS = 1500
OBSERVED_VALUES = {"yes", "no", "temporary", "unknown"}


@dataclass(slots=True)
class DynamicCapturePlan:
    capture_path: Path
    retune_events_ms: list[int]
    description: str


def find_dynamic_inputs(root: Path) -> dict[str, Path | None]:
    dynamic_dir = root / "reverse" / "input" / "dynamic"
    return {
        "actions": (dynamic_dir / "actions.json") if (dynamic_dir / "actions.json").exists() else None,
    }


def analyze_dynamic_lock_behavior(
    root: Path,
    *,
    actions_path: Path | None = None,
) -> dict[str, Any]:
    actions_file = actions_path or find_dynamic_inputs(root)["actions"]
    if actions_file is None:
        return {
            "present": False,
            "status": "missing_dynamic_inputs",
            "summary": "Add reverse/input/dynamic/actions.json and the matching pcapng files to run the minimal dynamic validation.",
        }

    payload = json.loads(actions_file.read_text(encoding="utf-8"))
    idle_plan = _parse_capture_plan(root, payload.get("idle_capture"))
    tx_plan = _parse_capture_plan(root, payload.get("tx_capture"))
    observation = _normalize_observation(payload.get("radio_observation", {}))

    idle_summary = analyze_dynamic_capture(idle_plan) if idle_plan else None
    tx_summary = analyze_dynamic_capture(tx_plan) if tx_plan else None

    digimanager_continuous_retune = infer_digimanager_continuous_retune(idle_summary, tx_summary)
    firmware_applies = infer_firmware_applies_retune(digimanager_continuous_retune, observation)
    lock_owner = infer_lock_owner(digimanager_continuous_retune, firmware_applies)

    return {
        "present": True,
        "actions_path": str(actions_file),
        "idle_capture": idle_summary,
        "tx_capture": tx_summary,
        "radio_observation": observation,
        "digimanager_continuous_retune": digimanager_continuous_retune,
        "firmware_applies_retune_in_digital_mode": firmware_applies,
        "lock_owner": lock_owner,
    }


def analyze_dynamic_capture(plan: DynamicCapturePlan) -> dict[str, Any]:
    events = parse_pcapng_udp_events(plan.capture_path)
    events_5957 = [event for event in events if event.dst_port == 5957]
    payload_hexes = [event.payload.hex(" ") for event in events_5957]
    unique_payload_count = len(set(payload_hexes))

    windows: list[dict[str, Any]] = []
    packet_windows_with_activity = 0
    windows_with_payload_change = 0
    for retune_ms in plan.retune_events_ms:
        start_ms = retune_ms - RETUNE_WINDOW_MS
        end_ms = retune_ms + RETUNE_WINDOW_MS
        window_events = [event for event in events_5957 if start_ms <= event.timestamp_ms <= end_ms]
        unique_payloads = len({event.payload.hex(" ") for event in window_events})
        if window_events:
            packet_windows_with_activity += 1
        if unique_payloads > 1:
            windows_with_payload_change += 1
        windows.append(
            {
                "retune_event_ms": retune_ms,
                "window_start_ms": start_ms,
                "window_end_ms": end_ms,
                "packet_count_5957": len(window_events),
                "unique_payload_count_5957": unique_payloads,
            }
        )

    return {
        "path": str(plan.capture_path),
        "description": plan.description,
        "retune_events_ms": plan.retune_events_ms,
        "total_5957_packets": len(events_5957),
        "unique_5957_payload_count": unique_payload_count,
        "retune_windows": windows,
        "retune_windows_with_activity": packet_windows_with_activity,
        "retune_windows_with_payload_change": windows_with_payload_change,
    }


def infer_digimanager_continuous_retune(
    idle_summary: dict[str, Any] | None,
    tx_summary: dict[str, Any] | None,
) -> str:
    summaries = [summary for summary in (idle_summary, tx_summary) if summary]
    if not summaries:
        return "unclear"

    total_windows = sum(len(summary["retune_windows"]) for summary in summaries)
    windows_with_activity = sum(summary["retune_windows_with_activity"] for summary in summaries)
    windows_with_change = sum(summary["retune_windows_with_payload_change"] for summary in summaries)

    if total_windows == 0:
        return "unclear"
    if windows_with_activity == 0:
        return "no"
    if windows_with_change > 0:
        return "yes"
    return "unclear"


def infer_firmware_applies_retune(
    digimanager_continuous_retune: str,
    observation: dict[str, str],
) -> str:
    idle = observation.get("idle_frequency_change", "unknown")
    tx = observation.get("tx_frequency_change", "unknown")
    values = {idle, tx}

    if digimanager_continuous_retune != "yes":
        return "unclear"
    if "temporary" in values:
        return "temporarily"
    if "yes" in values and "no" not in values:
        return "yes"
    if values == {"no"} or ("no" in values and "yes" not in values and "temporary" not in values):
        return "no"
    return "unclear"


def infer_lock_owner(
    digimanager_continuous_retune: str,
    firmware_applies_retune_in_digital_mode: str,
) -> str:
    if digimanager_continuous_retune == "no":
        return "pc_side"
    if digimanager_continuous_retune == "yes" and firmware_applies_retune_in_digital_mode in {"no", "temporarily"}:
        return "firmware_side"
    return "still_unclear"


def render_dynamic_lock_report(report: dict[str, Any]) -> str:
    if not report.get("present"):
        return report["summary"] + "\n"

    lines = [
        "# Dynamic Lock Validation",
        "",
        f"- digimanager_continuous_retune: {report['digimanager_continuous_retune']}",
        f"- firmware_applies_retune_in_digital_mode: {report['firmware_applies_retune_in_digital_mode']}",
        f"- lock_owner: {report['lock_owner']}",
        "",
    ]
    for label in ("idle_capture", "tx_capture"):
        summary = report.get(label)
        if not summary:
            continue
        lines.extend(
            [
                f"## {label}",
                f"- path: {summary['path']}",
                f"- total_5957_packets: {summary['total_5957_packets']}",
                f"- unique_5957_payload_count: {summary['unique_5957_payload_count']}",
                f"- retune_windows_with_activity: {summary['retune_windows_with_activity']}",
                f"- retune_windows_with_payload_change: {summary['retune_windows_with_payload_change']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_dynamic_lock_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "dynamic-lock-report.json"
    md_path = output_dir / "dynamic-lock-report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_dynamic_lock_report(report), encoding="utf-8")
    return json_path, md_path


def _parse_capture_plan(root: Path, raw: Any) -> DynamicCapturePlan | None:
    if not isinstance(raw, dict):
        return None
    path_text = raw.get("path")
    if not path_text:
        return None
    capture_path = Path(path_text)
    if not capture_path.is_absolute():
        capture_path = (root / capture_path).resolve()
    return DynamicCapturePlan(
        capture_path=capture_path,
        retune_events_ms=[int(value) for value in raw.get("retune_events_ms", [])],
        description=str(raw.get("description", "")),
    )


def _normalize_observation(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        raw = {}
    idle = str(raw.get("idle_frequency_change", "unknown")).lower()
    tx = str(raw.get("tx_frequency_change", "unknown")).lower()
    if idle not in OBSERVED_VALUES:
        idle = "unknown"
    if tx not in OBSERVED_VALUES:
        tx = "unknown"
    return {
        "idle_frequency_change": idle,
        "tx_frequency_change": tx,
        "notes": str(raw.get("notes", "")),
    }
