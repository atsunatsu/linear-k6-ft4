from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.ft4_timing_tools import render_mode_cadence_text, write_mode_cadence_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Compare FT4 and FT8 replay timing so maintainers can judge whether the send cadence still looks FT8-like."
    )
    parser.add_argument(
        "--ft4",
        default=str(root / "samples" / "replay" / "ft4-replay.json"),
        help="Path to the FT4 replay JSON.",
    )
    parser.add_argument(
        "--ft8",
        default=str(root / "samples" / "replay" / "ft8-replay.json"),
        help="Path to the FT8 replay JSON.",
    )
    parser.add_argument(
        "--output-json",
        default=str(root / "logs" / "reverse" / "ft4-ft8-timing-report.json"),
        help="Where to write the timing comparison JSON report.",
    )
    parser.add_argument(
        "--output-text",
        default=str(root / "logs" / "reverse" / "ft4-ft8-timing-report.txt"),
        help="Where to write the human-readable timing comparison summary.",
    )
    args = parser.parse_args()

    report = write_mode_cadence_report(
        args.ft4,
        args.ft8,
        output_json=args.output_json,
        output_text=args.output_text,
    )
    print(render_mode_cadence_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
