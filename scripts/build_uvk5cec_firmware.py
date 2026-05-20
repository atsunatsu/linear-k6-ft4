from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


FIRMWARE_DIR = Path("uvk5cec-0.3q")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unified build entrypoint for the uvk5cec FT4 clean-TX firmware bench build.")
    parser.add_argument("--target", choices=["auto", "windows", "docker"], default="auto")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--firmware-dir", default=str(FIRMWARE_DIR))
    args = parser.parse_args(argv)

    firmware_dir = Path(args.firmware_dir)
    if not firmware_dir.exists():
        print(f"error=firmware_dir_missing path={firmware_dir}")
        return 1

    resolved_target = _resolve_target(args.target)
    print(f"build_target={resolved_target}")

    if resolved_target == "windows":
        missing = [tool for tool in ("arm-none-eabi-gcc", "make") if shutil.which(tool) is None]
        if missing:
            print(json.dumps({"build_target": "windows", "missing_tools": missing}, indent=2, ensure_ascii=False))
            return 1
        command = ["cmd", "/c", "win_make.bat"] if args.clean else ["cmd", "/c", "win_make.bat"]
        completed = subprocess.run(
            command,
            cwd=str(firmware_dir),
            text=True,
            capture_output=True,
            check=False,
        )
    else:
        if shutil.which("docker") is None:
            print(json.dumps({"build_target": "docker", "missing_tools": ["docker"]}, indent=2, ensure_ascii=False))
            return 1
        script_name = "compile-with-docker.bat"
        completed = subprocess.run(
            ["cmd", "/c", script_name],
            cwd=str(firmware_dir),
            text=True,
            capture_output=True,
            check=False,
        )

    artifacts = _collect_artifacts(firmware_dir)
    summary = {
        "target": resolved_target,
        "returncode": completed.returncode,
        "artifacts": artifacts,
        "stdout_tail": _tail_lines(completed.stdout),
        "stderr_tail": _tail_lines(completed.stderr),
        "feature_enabled_hint": "ENABLE_FT4_CLEAN_TX ?= 1",
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if completed.returncode == 0 and artifacts else 1


def _resolve_target(raw_target: str) -> str:
    if raw_target != "auto":
        return raw_target
    if shutil.which("arm-none-eabi-gcc") and shutil.which("make"):
        return "windows"
    return "docker"


def _collect_artifacts(firmware_dir: Path) -> list[dict[str, object]]:
    artifact_paths = []
    for candidate in sorted(firmware_dir.glob("firmware*")):
        if candidate.is_file():
            artifact_paths.append(
                {
                    "path": str(candidate.resolve()),
                    "size_bytes": candidate.stat().st_size,
                }
            )
    compiled_dir = firmware_dir / "compiled-firmware"
    if compiled_dir.exists():
        for candidate in sorted(compiled_dir.glob("firmware*")):
            if candidate.is_file():
                artifact_paths.append(
                    {
                        "path": str(candidate.resolve()),
                        "size_bytes": candidate.stat().st_size,
                    }
                )
    return artifact_paths


def _tail_lines(text: str, max_lines: int = 12) -> list[str]:
    if not text:
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
