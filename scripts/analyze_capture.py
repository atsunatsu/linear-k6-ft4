from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a WSJT-X <-> DigiManager JSONL capture log.")
    parser.add_argument("log_path", help="Path to the JSONL capture log.")
    args = parser.parse_args(argv)

    path = Path(args.log_path)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        print("No capture records found.")
        return 0

    scenario_counts = Counter(record["scenario"] for record in records)
    direction_counts = Counter(record["direction"] for record in records)
    ascii_like_count = sum(_looks_ascii(record["bytes_ascii"]) for record in records)
    ascii_ratio = ascii_like_count / len(records)

    print(f"records: {len(records)}")
    print(f"directions: {dict(direction_counts)}")
    print(f"scenarios: {dict(scenario_counts)}")
    print(f"ascii_like_ratio: {ascii_ratio:.2f}")
    print(f"first_timestamp_ms: {records[0]['timestamp_ms']}")
    print(f"last_timestamp_ms: {records[-1]['timestamp_ms']}")
    print("sample_records:")
    for record in records[:10]:
        print(
            f"- {record['timestamp_ms']} {record['direction']} "
            f"hex={record['bytes_hex']} ascii={record['bytes_ascii']}"
        )
    return 0


def _looks_ascii(rendered_ascii: str) -> bool:
    if not rendered_ascii:
        return False
    printable = sum(char.isalnum() or char in " .,:;_-/\\[](){}<>+=*?&|!@#$%^~`'\"\t\\nr" for char in rendered_ascii)
    return printable / max(1, len(rendered_ascii)) > 0.8


if __name__ == "__main__":
    raise SystemExit(main())
