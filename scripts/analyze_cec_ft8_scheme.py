from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sat_bridge.cec_ft8_scheme_tools import analyze_cec_ft8_scheme, write_cec_ft8_scheme_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze the real 0.3q FT8 transmit scheme and FT4 feasibility.")
    parser.add_argument(
        "--firmware",
        default="reverse/input/firmware/cec_0.3QB.packed.bin",
        help="Path to the real packed 0.3q firmware.",
    )
    parser.add_argument(
        "--digimanager-summary",
        default="outputs/patched-digimanager-summary.json",
        help="Path to the patched DigiManager build summary.",
    )
    parser.add_argument(
        "--timing-report",
        default="logs/reverse/ft4-ft8-timing-report.json",
        help="Path to the FT4/FT8 timing comparison report.",
    )
    parser.add_argument(
        "--source-root",
        default="uvk5cec-0.3q",
        help="Path to the public-source reference tree.",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/reverse",
        help="Directory to receive the generated report.",
    )
    args = parser.parse_args()

    report = analyze_cec_ft8_scheme(
        firmware_path=Path(args.firmware),
        digimanager_summary_path=Path(args.digimanager_summary) if args.digimanager_summary else None,
        timing_report_path=Path(args.timing_report) if args.timing_report else None,
        source_root=Path(args.source_root) if args.source_root else None,
    )
    json_path, md_path = write_cec_ft8_scheme_report(report, Path(args.output_dir))
    print(f"json_report={json_path}")
    print(f"markdown_report={md_path}")
    print(f"likely_author_ft8_tx_scheme={report['judgement']['likely_author_ft8_tx_scheme']}")
    print(f"bk4819_packet_fsk_fit_for_ft4={report['judgement']['public_bk4819_packet_fsk_fit_for_ft4']}")
    print(f"current_best_direction={report['judgement']['current_best_direction']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
