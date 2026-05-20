from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE_ROOT = ROOT / "uvk5cec-0.3q"


class Uvk5CecSourceHygieneTests(unittest.TestCase):
    def test_active_source_headers_do_not_use_windows_include_separators(self) -> None:
        source_roots = [
            FIRMWARE_ROOT,
            FIRMWARE_ROOT / "app",
            FIRMWARE_ROOT / "driver",
            FIRMWARE_ROOT / "helper",
            FIRMWARE_ROOT / "ui",
        ]

        offenders: list[str] = []
        for base in source_roots:
            if not base.exists():
                continue
            for path in base.rglob("*.[ch]"):
                if "external" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(text.splitlines(), start=1):
                    if '#include "' in line and "\\" in line:
                        offenders.append(f"{path.relative_to(ROOT)}:{line_no}:{line.strip()}")

        self.assertEqual(offenders, [], "Found Windows-style include paths:\n" + "\n".join(offenders))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
