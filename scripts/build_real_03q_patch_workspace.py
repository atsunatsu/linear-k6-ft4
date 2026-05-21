from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.real_03q_patch_tools import build_patch_workspace, write_patch_workspace
from sat_bridge.reverse_tools import find_reverse_assets


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assets = find_reverse_assets(root)
    if assets.firmware is None:
        raise SystemExit("No real 0.3q firmware bin found. Place it in the repo root or reverse/input/firmware first.")

    workspace = build_patch_workspace(assets.firmware)
    json_path, md_path, manifest_path = write_patch_workspace(
        workspace,
        root / "logs" / "reverse",
        manifest_path=root / "reverse" / "patches" / "real-03q-bench.template.json",
    )
    print(f"patch_workspace_json={json_path}")
    print(f"patch_workspace_md={md_path}")
    print(f"patch_manifest_template={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
