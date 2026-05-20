from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.config import load_config
from sat_bridge.ft4_clean_tx import Ft4CleanTransmitter, Ft4ReplayTemplate, UdpFt4Backend


def _parse_retune(value: str) -> tuple[int, int]:
    try:
        frequency_text, delay_text = value.split("@", 1)
        return int(frequency_text), int(delay_text)
    except ValueError as exc:  # pragma: no cover - argparse-facing
        raise argparse.ArgumentTypeError("Retune items must look like 145950100@1200") from exc


async def _run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    ft4_config = config.ft4_clean_tx
    template = Ft4ReplayTemplate.from_path(
        ft4_config.template_path,
        transmission_index=ft4_config.transmission_index,
    )
    transmitter = Ft4CleanTransmitter(
        template=template,
        backend=UdpFt4Backend(ft4_config),
        tx_min_step_hz=ft4_config.tx_min_step_hz,
        tx_rate_limit_hz=ft4_config.tx_rate_limit_hz,
        tx_rate_limit_window_ms=ft4_config.tx_rate_limit_window_ms,
        timing_mode=args.timing,
    )

    await transmitter.open()
    try:
        payload = args.payload or ft4_config.default_payload
        print(f"starting_ft4_clean_tx payload={payload!r} tx_frequency_hz={args.tx_frequency_hz} timing={args.timing}")
        await transmitter.start_ft4_tx(payload, args.tx_frequency_hz)
        for frequency_hz, delay_ms in args.retune:
            await asyncio.sleep(delay_ms / 1000.0)
            print(f"retune tx_frequency_hz={frequency_hz} after_ms={delay_ms}")
            await transmitter.update_tx_frequency(frequency_hz)
        await transmitter.wait_for_idle()
        print("ft4_clean_tx_complete")
    finally:
        await transmitter.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the experimental FT4 clean transmitter bench sequence.")
    parser.add_argument("--config", default="sat_bridge.example.toml", help="Path to TOML config.")
    parser.add_argument("--payload", help="ASCII text to place into the FT4 mode-marker packets.")
    parser.add_argument("--tx-frequency-hz", type=int, required=True, help="Starting TX frequency in Hz.")
    parser.add_argument(
        "--timing",
        choices=["fast_replay", "original_timing"],
        default=None,
        help="How quickly to replay the extracted FT4 transmission window.",
    )
    parser.add_argument(
        "--retune",
        type=_parse_retune,
        action="append",
        default=[],
        metavar="FREQ@DELAY_MS",
        help="Schedule a TX retune after DELAY_MS milliseconds.",
    )
    args = parser.parse_args(argv)
    if args.timing is None:
        if args.retune:
            args.timing = "original_timing"
        else:
            config = load_config(args.config)
            args.timing = config.ft4_clean_tx.timing_mode
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
