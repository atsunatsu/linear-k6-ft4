from pathlib import Path
from shutil import copyfile
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.digimanager_patch_tools import (
    PATCHED_DIGIMANAGER_DIAGNOSTIC_FILENAME,
    PATCHED_DIGIMANAGER_DIAGNOSTIC_PROFILE_FILENAME,
    PATCHED_DIGIMANAGER_FILENAME,
    apply_digimanager_patch_manifest,
    write_digimanager_patch_manifest,
)
from sat_bridge.ft4_timing_tools import write_mode_cadence_report
from sat_bridge.reverse_tools import find_reverse_assets


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assets = find_reverse_assets(root)
    if assets.digimanager is None:
        raise SystemExit("No UVK5DigManager.exe found. Place it in the repo root or reverse/input/digimanager first.")

    manifest_path = root / "reverse" / "patches" / "patch-manifest.digimanager-ft4-forward.json"
    write_digimanager_patch_manifest(assets.digimanager, manifest_path)

    output_path = root / "outputs" / PATCHED_DIGIMANAGER_FILENAME
    report = apply_digimanager_patch_manifest(assets.digimanager, manifest_path, output_path)
    diagnostic_exe = root / "outputs" / PATCHED_DIGIMANAGER_DIAGNOSTIC_FILENAME
    copyfile(output_path, diagnostic_exe)

    diagnostic_profile = root / "outputs" / PATCHED_DIGIMANAGER_DIAGNOSTIC_PROFILE_FILENAME
    ft4_sample = root / "samples" / "replay" / "ft4-replay.json"
    ft8_sample = root / "samples" / "replay" / "ft8-replay.json"
    timing_report = None
    if ft4_sample.exists() and ft8_sample.exists():
        timing_report = write_mode_cadence_report(
            ft4_sample,
            ft8_sample,
            output_json=diagnostic_profile,
            output_text=diagnostic_profile.with_suffix(".txt"),
        )

    summary_path = root / "outputs" / "patched-digimanager-summary.json"
    summary = {
        **report,
        "diagnostic_exe": str(diagnostic_exe),
        "diagnostic_profile": str(diagnostic_profile) if timing_report is not None else None,
        "diagnostic_profile_available": timing_report is not None,
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"patched_exe={report['output_binary']}")
    print(f"diagnostic_exe={diagnostic_exe}")
    print(f"source_sha256={report['source_sha256']}")
    print(f"output_sha256={report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
