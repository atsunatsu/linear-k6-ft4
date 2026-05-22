from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.digimanager_patch_tools import (
    PATCHED_DIGIMANAGER_FILENAME,
    apply_digimanager_patch_manifest,
    write_digimanager_patch_manifest,
)
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
    summary_path = root / "outputs" / "patched-digimanager-summary.json"
    summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"patched_exe={report['output_binary']}")
    print(f"source_sha256={report['source_sha256']}")
    print(f"output_sha256={report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
