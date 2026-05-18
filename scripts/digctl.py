from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("logs") / "digctl-events.log"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Placeholder DigiManager control shim for sat-bridge integration tests."
    )
    parser.add_argument("action", choices=["set-rx", "set-tx", "set-active", "set-mode", "set-ptt"])
    parser.add_argument("value")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"{timestamp} action={args.action} value={args.value}"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
