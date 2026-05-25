from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.firmware_command35_tools import (  # noqa: E402
    analyze_command35_path,
    write_command35_report,
)


DEFAULT_OUTPUT_DIR = Path("logs/reverse")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze how DigiManager command 0x35 likely reaches the real 0.3q firmware handling path."
    )
    parser.add_argument("--firmware", default="reverse/input/firmware/cec_0.3QB.packed.bin")
    parser.add_argument("--digimanager", default="reverse/input/digimanager/UVK5DigManager.exe")
    parser.add_argument("--ft4-replay", default="samples/replay/ft4-replay.json")
    parser.add_argument("--ft8-replay", default="samples/replay/ft8-replay.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    report = analyze_command35_path(
        firmware_path=Path(args.firmware),
        digimanager_path=Path(args.digimanager),
        ft4_replay_path=Path(args.ft4_replay),
        ft8_replay_path=Path(args.ft8_replay),
    )
    json_path, md_path = write_command35_report(report, Path(args.output_dir))

    judgement = report["judgement"]
    print(f"command35_frame_kind={judgement['command35_frame_kind']}")
    print(f"firmware_direct_cmp_0x35={judgement['firmware_direct_cmp_0x35']}")
    print(f"likely_handler_model={judgement['likely_handler_model']}")
    print(f"timing_owner_guess={judgement['timing_owner_guess']}")
    print(f"JSON report written to {json_path}")
    print(f"Markdown report written to {md_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
