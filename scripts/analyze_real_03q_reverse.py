from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.reverse_tools import (  # noqa: E402
    analyze_reverse_targets,
    find_reverse_assets,
    write_reverse_report,
)


DEFAULT_OUTPUT_DIR = Path("logs/reverse")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a two-sided reverse-engineering map for the real 0.3q firmware bin and UVK5DigManager binary."
    )
    parser.add_argument("--firmware", default=None, help="Path to the real 0.3q firmware .bin. Default: first file under reverse/input/firmware.")
    parser.add_argument("--digimanager", default=None, help="Path to UVK5DigManager .exe or .zip. Default: first file under reverse/input/digimanager.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    defaults = find_reverse_assets(root)

    firmware_path = Path(args.firmware) if args.firmware else defaults.firmware
    digimanager_path = Path(args.digimanager) if args.digimanager else defaults.digimanager

    report = analyze_reverse_targets(
        root,
        firmware_path=firmware_path,
        digimanager_path=digimanager_path,
        replay_json_paths=defaults.replay_jsons,
    )
    json_path, md_path = write_reverse_report(report, Path(args.output_dir))

    print(f"firmware_bin={firmware_path if firmware_path else 'missing'}")
    print(f"digimanager_binary={digimanager_path if digimanager_path else 'missing'}")
    print(f"digital_mode_entry={report['digital_mode_entry']['status']}")
    print(f"frequency_set_call_chain={report['frequency_set_call_chain']['status']}")
    print(f"lock_frequency_owner={report['lock_frequency_owner']['status']}")
    print(f"external_retune_capability={report['external_retune_capability']['status']}")
    print(f"recommended_next_step={report['recommended_next_step']['kind']}")
    print(f"JSON report written to {json_path}")
    print(f"Markdown report written to {md_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
