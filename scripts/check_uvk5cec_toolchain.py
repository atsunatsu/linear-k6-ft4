from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys


REQUIRED_WINDOWS_TOOLS = [
    "arm-none-eabi-gcc",
    "make",
    "python",
]

OPTIONAL_TOOLS = [
    "docker",
]


def main() -> int:
    pyserial_installed = importlib.util.find_spec("serial") is not None
    report = {
        "firmware_dir": str(Path("uvk5cec-0.3q").resolve()),
        "required_tools": {name: shutil.which(name) for name in REQUIRED_WINDOWS_TOOLS},
        "optional_tools": {name: shutil.which(name) for name in OPTIONAL_TOOLS},
        "python_packages": {
            "pyserial": pyserial_installed,
        },
    }

    missing_required = [name for name, path in report["required_tools"].items() if path is None]
    report["ready_for_windows_build"] = not missing_required
    report["ready_for_docker_build"] = report["optional_tools"]["docker"] is not None
    report["ready_for_offline_uart_bench"] = report["required_tools"]["python"] is not None and pyserial_installed
    report["missing_required"] = missing_required

    print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0 if not missing_required else 1


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
