from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.real_03q_patch_tools import apply_patch_manifest
from sat_bridge.reverse_tools import find_reverse_assets


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(__file__).resolve().parents[1]
    assets = find_reverse_assets(root)
    if assets.firmware is None:
        raise SystemExit("No real 0.3q firmware bin found. Place it in the repo root or reverse/input/firmware first.")

    manifest_path = Path(args[0]) if args else (root / "reverse" / "patches" / "real-03q-bench.template.json")
    if not manifest_path.is_absolute():
        manifest_path = (root / manifest_path).resolve()
    output_path = root / "outputs" / "patched-0.3q-bench.packed.bin"
    report = apply_patch_manifest(assets.firmware, manifest_path, output_path)
    print(f"patched_firmware={report['output_firmware']}")
    print(f"output_embedded_version={report['output_embedded_version']}")
    print(f"applied_patches={len(report['applied_patches'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
