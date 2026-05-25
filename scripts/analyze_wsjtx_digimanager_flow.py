from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sat_bridge.wsjtx_digimanager_flow_tools import build_flow_report, render_flow_report_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="分析 WSJT-X -> DigiManager 的 FT4/FT8 上游数据与 DigiManager sender 头字段压平问题。"
    )
    parser.add_argument(
        "--ft4",
        default=str(ROOT / "samples" / "replay" / "ft4-replay.json"),
        help="FT4 replay JSON 路径。",
    )
    parser.add_argument(
        "--ft8",
        default=str(ROOT / "samples" / "replay" / "ft8-replay.json"),
        help="FT8 replay JSON 路径。",
    )
    parser.add_argument(
        "--json-output",
        default=str(ROOT / "logs" / "reverse" / "wsjtx-digimanager-flow.json"),
        help="JSON 输出路径。",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(ROOT / "logs" / "reverse" / "wsjtx-digimanager-flow.md"),
        help="Markdown 输出路径。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_flow_report(Path(args.ft4), Path(args.ft8))

    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    markdown_path = Path(args.markdown_output)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_flow_report_markdown(report), encoding="utf-8")

    print(f"JSON report written to {json_path}")
    print(f"Markdown report written to {markdown_path}")
    print(report["comparison"]["judgement"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
