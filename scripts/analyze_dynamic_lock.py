from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.dynamic_reverse_tools import (  # noqa: E402
    analyze_dynamic_lock_behavior,
    write_dynamic_lock_report,
)


DEFAULT_OUTPUT_DIR = Path("logs/reverse")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze minimal dynamic retune validation captures for the real 0.3q digital-mode lock investigation."
    )
    parser.add_argument("--actions", default=None, help="Path to reverse/input/dynamic/actions.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    actions_path = Path(args.actions) if args.actions else None
    report = analyze_dynamic_lock_behavior(root, actions_path=actions_path)
    json_path, md_path = write_dynamic_lock_report(report, Path(args.output_dir))

    print(f"digimanager_continuous_retune={report.get('digimanager_continuous_retune', 'unclear')}")
    print(f"firmware_applies_retune_in_digital_mode={report.get('firmware_applies_retune_in_digital_mode', 'unclear')}")
    print(f"lock_owner={report.get('lock_owner', 'still_unclear')}")
    print(f"JSON report written to {json_path}")
    print(f"Markdown report written to {md_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
