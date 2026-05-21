from pathlib import Path
import json
from hashlib import sha256
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.real_03q_patch_tools import (  # noqa: E402
    VARIANT_SPECS,
    apply_patch_manifest,
    write_variant_manifests,
)
from sat_bridge.reverse_tools import find_reverse_assets


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assets = find_reverse_assets(root)
    if assets.firmware is None:
        raise SystemExit("No real 0.3q firmware bin found.")

    template_path = root / "reverse" / "patches" / "real-03q-bench.template.json"
    template_manifest = json.loads(template_path.read_text(encoding="utf-8"))
    manifests = write_variant_manifests(template_manifest, root / "reverse" / "patches")

    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict[str, str | int | bool]] = {}

    for variant_name, manifest_path in manifests.items():
        output_path = outputs_dir / VARIANT_SPECS[variant_name]["output_filename"]
        report = apply_patch_manifest(assets.firmware, manifest_path, output_path)
        output_bytes = output_path.read_bytes()
        summary[variant_name] = {
            "manifest": str(manifest_path),
            "output_firmware": str(output_path),
            "sha256": sha256(output_bytes).hexdigest(),
            "size_bytes": len(output_bytes),
            "structural_only": True,
        }
        print(f"{variant_name}={report['output_firmware']}")

    bench_target = outputs_dir / "patched-0.3q-bench.packed.bin"
    combined_target = outputs_dir / VARIANT_SPECS["combined"]["output_filename"]
    bench_target.write_bytes(combined_target.read_bytes())
    summary["bench"] = {
        "output_firmware": str(bench_target),
        "sha256": sha256(bench_target.read_bytes()).hexdigest(),
        "size_bytes": bench_target.stat().st_size,
        "alias_of": str(combined_target),
        "structural_only": True,
    }
    (outputs_dir / "patch-build-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"bench={bench_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
