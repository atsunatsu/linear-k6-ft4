from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.retune_injector import injector_main


if __name__ == "__main__":
    raise SystemExit(injector_main())
