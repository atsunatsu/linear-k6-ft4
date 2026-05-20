from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.uvk5cec_uart import (  # noqa: E402
    FT4TX_STATUS_OK,
    FT4TX_STATUS_NAMES,
    SessionContext,
    Uvk5CecSerialClient,
    default_session_timestamp,
    load_session_context,
    save_session_context,
)


DEFAULT_SESSION_FILE = Path("logs/uvk5cec-ft4-session.json")


def _parse_retune(value: str) -> tuple[int, int]:
    try:
        freq_text, delay_text = value.split("@", 1)
        return int(freq_text), int(delay_text)
    except ValueError as exc:  # pragma: no cover - argparse-facing
        raise argparse.ArgumentTypeError("Retune items must look like 145950100@1200") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bench-control helper for the experimental uvk5cec FT4 clean TX UART commands."
    )
    parser.add_argument("--session-file", default=str(DEFAULT_SESSION_FILE))

    subparsers = parser.add_subparsers(dest="command", required=True)

    send = subparsers.add_parser("send-ft4", help="Start an FT4 bench TX session.")
    send.add_argument("--port", required=True)
    send.add_argument("--baudrate", type=int, default=38400)
    send.add_argument("--timeout-seconds", type=float, default=2.0)
    send.add_argument("--text", required=True)
    send.add_argument("--freq", type=int, required=True)
    send.add_argument("--timestamp", type=int, default=None)
    send.add_argument("--retune", action="append", default=[], type=_parse_retune)
    send.add_argument("--stop-when-done", action="store_true")

    retune = subparsers.add_parser("retune", help="Send one retune update to the active FT4 bench session.")
    retune.add_argument("--freq", type=int, required=True)
    retune.add_argument("--port", default=None)
    retune.add_argument("--baudrate", type=int, default=None)
    retune.add_argument("--timeout-seconds", type=float, default=2.0)

    stop = subparsers.add_parser("stop-tx", help="Stop the active FT4 bench session.")
    stop.add_argument("--port", default=None)
    stop.add_argument("--baudrate", type=int, default=None)
    stop.add_argument("--timeout-seconds", type=float, default=2.0)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    session_file = Path(args.session_file)

    if args.command == "send-ft4":
        timestamp = args.timestamp if args.timestamp is not None else default_session_timestamp()
        session = SessionContext(port=args.port, baudrate=args.baudrate, timestamp=timestamp)
        with Uvk5CecSerialClient(args.port, baudrate=args.baudrate, timeout_seconds=args.timeout_seconds) as client:
            version = client.bootstrap(timestamp)
            config_version = client.configure_session(timestamp)
            reply = client.start_ft4_tx(timestamp, args.freq, args.text)
            print(f"session_version={version.version} config_version={config_version.version}")
            print(
                f"start_ft4_tx status={reply.status}({FT4TX_STATUS_NAMES.get(reply.status, 'UNKNOWN')}) active={int(reply.active)} "
                f"freq={reply.current_tx_frequency_hz} frames_sent={reply.frames_sent}"
            )
            if reply.status != FT4TX_STATUS_OK:
                return 1

            save_session_context(session_file, session)

            for frequency_hz, delay_ms in args.retune:
                time.sleep(delay_ms / 1000.0)
                retune_reply = client.update_tx_frequency(timestamp, frequency_hz)
                print(
                    f"retune status={retune_reply.status}({FT4TX_STATUS_NAMES.get(retune_reply.status, 'UNKNOWN')}) requested={frequency_hz} "
                    f"applied={retune_reply.last_applied_tx_frequency_hz} "
                    f"pending={retune_reply.pending_tx_frequency_hz} mode={retune_reply.retune_mode}"
                )
                if retune_reply.status != FT4TX_STATUS_OK:
                    return 1

            if args.stop_when_done:
                stop_reply = client.stop_tx(timestamp)
                print(f"stop_tx status={stop_reply.status}({FT4TX_STATUS_NAMES.get(stop_reply.status, 'UNKNOWN')}) active={int(stop_reply.active)}")
                if session_file.exists():
                    session_file.unlink()
                if stop_reply.status != FT4TX_STATUS_OK:
                    return 1
                print("session_closed=1")
                return 0

        print(f"session_saved={session_file}")
        return 0

    if session_file.exists():
        session = load_session_context(session_file)
    else:
        parser.error(f"Session file {session_file} does not exist. Run send-ft4 first.")

    port = args.port or session.port
    baudrate = args.baudrate or session.baudrate
    timestamp = session.timestamp

    with Uvk5CecSerialClient(port, baudrate=baudrate, timeout_seconds=args.timeout_seconds) as client:
        client.bootstrap(timestamp)
        if args.command == "retune":
            reply = client.update_tx_frequency(timestamp, args.freq)
            print(
                f"retune status={reply.status}({FT4TX_STATUS_NAMES.get(reply.status, 'UNKNOWN')}) requested={args.freq} "
                f"applied={reply.last_applied_tx_frequency_hz} pending={reply.pending_tx_frequency_hz}"
            )
            return 0 if reply.status == FT4TX_STATUS_OK else 1

        if args.command == "stop-tx":
            reply = client.stop_tx(timestamp)
            print(f"stop_tx status={reply.status}({FT4TX_STATUS_NAMES.get(reply.status, 'UNKNOWN')}) active={int(reply.active)}")
            if reply.status == FT4TX_STATUS_OK and session_file.exists():
                session_file.unlink()
            return 0 if reply.status == FT4TX_STATUS_OK else 1

    return 1


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
