from __future__ import annotations

import argparse
import csv
from pathlib import Path


HEADERS = [
    "COM号",
    "谁在打开",
    "用途",
    "是否为虚拟串口",
    "配对对象",
    "串口参数",
    "当前是否工作",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List local serial ports and generate a topology worksheet.")
    parser.add_argument(
        "--csv",
        default="logs/serial-topology-template.csv",
        help="Where to write the editable topology worksheet.",
    )
    args = parser.parse_args(argv)

    rows = list(_probe_ports())
    for row in rows:
        print(f"{row['COM号']}: {row['用途']}")

    output_path = Path(args.csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        if not rows:
            writer.writerow({header: "" for header in HEADERS})

    print(f"Topology worksheet written to {output_path}")
    return 0


def _probe_ports():
    try:
        from serial.tools import list_ports  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency specific
        raise RuntimeError("pyserial is required for serial topology discovery") from exc

    for port in list_ports.comports():
        description = getattr(port, "description", "") or ""
        yield {
            "COM号": port.device,
            "谁在打开": "",
            "用途": description,
            "是否为虚拟串口": "是" if _looks_virtual(description) else "",
            "配对对象": "",
            "串口参数": "",
            "当前是否工作": "",
        }


def _looks_virtual(description: str) -> bool:
    text = description.lower()
    return any(keyword in text for keyword in ["com0com", "virtual", "vcp", "null-modem"])


if __name__ == "__main__":
    raise SystemExit(main())
