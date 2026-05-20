from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BuildWorkflowTests(unittest.TestCase):
    def test_toolchain_check_script_emits_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/check_uvk5cec_toolchain.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        report = json.loads(completed.stdout)
        self.assertIn("required_tools", report)
        self.assertIn("ready_for_windows_build", report)
        self.assertIn("python_packages", report)
        self.assertIn("pyserial", report["python_packages"])
        self.assertIn("ready_for_offline_uart_bench", report)

    def test_build_script_reports_missing_tools_or_artifacts(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/build_uvk5cec_firmware.py", "--target", "windows"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn("build_target=windows", completed.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
