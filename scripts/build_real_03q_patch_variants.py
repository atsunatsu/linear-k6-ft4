from pathlib import Path
import json
from hashlib import sha256
from shutil import copyfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.digimanager_patch_tools import (  # noqa: E402
    PATCHED_DIGIMANAGER_DIAGNOSTIC_FILENAME,
    PATCHED_DIGIMANAGER_DIAGNOSTIC_PROFILE_FILENAME,
    PATCHED_DIGIMANAGER_FILENAME,
    apply_digimanager_patch_manifest,
    write_digimanager_patch_manifest,
)
from sat_bridge.ft4_timing_tools import write_mode_cadence_report  # noqa: E402
from sat_bridge.real_03q_patch_tools import (  # noqa: E402
    VARIANT_SPECS,
    apply_patch_manifest,
    build_patch_workspace,
    write_patch_workspace,
    write_variant_manifests,
)
from sat_bridge.reverse_tools import find_reverse_assets


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assets = find_reverse_assets(root)
    if assets.firmware is None:
        raise SystemExit("No real 0.3q firmware bin found.")
    if assets.digimanager is None:
        raise SystemExit("No UVK5DigManager.exe found.")

    workspace = build_patch_workspace(assets.firmware)
    _json_path, _md_path, template_path = write_patch_workspace(
        workspace,
        root / "logs" / "reverse",
        manifest_path=root / "reverse" / "patches" / "real-03q-bench.template.json",
    )
    template_manifest = json.loads(template_path.read_text(encoding="utf-8"))
    manifests = write_variant_manifests(template_manifest, root / "reverse" / "patches")
    digimanager_manifest = write_digimanager_patch_manifest(
        assets.digimanager,
        root / "reverse" / "patches" / "patch-manifest.digimanager-ft4-forward.json",
    )

    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict[str, str | int | bool | list[str]]] = {}

    for variant_name, manifest_path in manifests.items():
        output_path = outputs_dir / VARIANT_SPECS[variant_name]["output_filename"]
        report = apply_patch_manifest(assets.firmware, manifest_path, output_path)
        output_bytes = output_path.read_bytes()
        summary[variant_name] = {
            "manifest": str(manifest_path),
            "output_firmware": str(output_path),
            "sha256": sha256(output_bytes).hexdigest(),
            "size_bytes": len(output_bytes),
            "structural_only": False,
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
        "structural_only": False,
    }
    digimanager_output = outputs_dir / PATCHED_DIGIMANAGER_FILENAME
    digimanager_report = apply_digimanager_patch_manifest(assets.digimanager, digimanager_manifest, digimanager_output)
    diagnostic_digimanager_output = outputs_dir / PATCHED_DIGIMANAGER_DIAGNOSTIC_FILENAME
    copyfile(digimanager_output, diagnostic_digimanager_output)
    diagnostic_profile = outputs_dir / PATCHED_DIGIMANAGER_DIAGNOSTIC_PROFILE_FILENAME
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
    summary["digimanager-ft4-forward"] = {
        "manifest": str(digimanager_manifest),
        "output_binary": str(digimanager_output),
        "sha256": str(digimanager_report["output_sha256"]),
        "source_sha256": str(digimanager_report["source_sha256"]),
        "applied_patch_names": [str(item["name"]) for item in digimanager_report["applied_patches"]],
        "structural_only": False,
    }
    summary["digimanager-diagnostic"] = {
        "output_binary": str(diagnostic_digimanager_output),
        "sha256": sha256(diagnostic_digimanager_output.read_bytes()).hexdigest(),
        "alias_of": str(digimanager_output),
        "diagnostic_profile": str(diagnostic_profile) if timing_report is not None else None,
        "structural_only": False,
    }
    (outputs_dir / "patch-build-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"bench={bench_target}")
    print(f"digimanager={digimanager_output}")
    print(f"digimanager_diagnostic={diagnostic_digimanager_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
