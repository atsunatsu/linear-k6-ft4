from __future__ import annotations

import argparse
from dataclasses import dataclass
import socketserver
from pathlib import Path
import struct
import sys
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.uvk5cec_uart import (  # noqa: E402
    CMD_SESSION_CONFIG,
    CMD_SESSION_HELLO,
    CMD_START_FT4_TX,
    CMD_STOP_TX,
    CMD_UPDATE_TX_FREQ,
    FT4TX_STATUS_BUSY,
    FT4TX_STATUS_NOT_ACTIVE,
    FT4TX_STATUS_OK,
    REPLY_START_FT4_TX,
    REPLY_STOP_TX,
    REPLY_UPDATE_TX_FREQ,
    REPLY_VERSION,
    build_reply_frame,
    parse_command_frame,
    read_frame,
)


@dataclass
class MockState:
    lock: Lock
    active: bool = False
    retune_mode: int = 0
    current_tx_frequency_hz: int = 0
    last_applied_tx_frequency_hz: int = 0
    pending_tx_frequency_hz: int = 0
    frames_sent: int = 0
    frame_sequence: int = 0
    version: str = "CEC_MOCK"


class ResponderHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            try:
                frame = read_frame(self.request.makefile("rwb", buffering=0))
            except TimeoutError:
                return
            except Exception:
                return

            command = parse_command_frame(frame)
            response = self.server.dispatch(command.command_id, command.body)  # type: ignore[attr-defined]
            self.request.sendall(response)


class MockResponderServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, state: MockState):
        super().__init__(server_address, ResponderHandler)
        self.state = state

    def dispatch(self, command_id: int, body: bytes) -> bytes:
        if command_id in {CMD_SESSION_HELLO, CMD_SESSION_CONFIG}:
            return self._build_version_reply()
        if command_id == CMD_START_FT4_TX:
            return self._handle_start(body)
        if command_id == CMD_UPDATE_TX_FREQ:
            return self._handle_retune(body)
        if command_id == CMD_STOP_TX:
            return self._handle_stop()
        return self._build_ft4_reply(REPLY_STOP_TX, FT4TX_STATUS_NOT_ACTIVE)

    def _build_version_reply(self) -> bytes:
        version = self.state.version.encode("ascii")[:16].ljust(16, b"\x00")
        data = version + bytes([0, 0]) + b"\x00\x00" + (1).to_bytes(4, "little") * 4
        return build_reply_frame(REPLY_VERSION, data)

    def _handle_start(self, body: bytes) -> bytes:
        with self.state.lock:
            if self.state.active:
                return self._build_ft4_reply(REPLY_START_FT4_TX, FT4TX_STATUS_BUSY)
            _timestamp, tx_frequency_hz = struct.unpack("<II", body[:8])
            payload_length = body[8]
            self.state.active = True
            self.state.current_tx_frequency_hz = tx_frequency_hz
            self.state.last_applied_tx_frequency_hz = tx_frequency_hz
            self.state.pending_tx_frequency_hz = 0
            self.state.retune_mode = 0
            self.state.frames_sent = max(payload_length, 1)
            self.state.frame_sequence += 1
            return self._build_ft4_reply(REPLY_START_FT4_TX, FT4TX_STATUS_OK)

    def _handle_retune(self, body: bytes) -> bytes:
        with self.state.lock:
            if not self.state.active:
                return self._build_ft4_reply(REPLY_UPDATE_TX_FREQ, FT4TX_STATUS_NOT_ACTIVE)
            _timestamp, tx_frequency_hz = struct.unpack("<II", body[:8])
            self.state.current_tx_frequency_hz = tx_frequency_hz
            self.state.last_applied_tx_frequency_hz = tx_frequency_hz
            self.state.pending_tx_frequency_hz = 0
            self.state.frames_sent += 1
            return self._build_ft4_reply(REPLY_UPDATE_TX_FREQ, FT4TX_STATUS_OK)

    def _handle_stop(self) -> bytes:
        with self.state.lock:
            self.state.active = False
            self.state.pending_tx_frequency_hz = 0
            self.state.current_tx_frequency_hz = 0
            self.state.last_applied_tx_frequency_hz = 0
            return self._build_ft4_reply(REPLY_STOP_TX, FT4TX_STATUS_OK)

    def _build_ft4_reply(self, reply_id: int, status: int) -> bytes:
        state = self.state
        data = (
            bytes([status, int(state.active), state.retune_mode, 0])
            + state.current_tx_frequency_hz.to_bytes(4, "little")
            + state.last_applied_tx_frequency_hz.to_bytes(4, "little")
            + state.pending_tx_frequency_hz.to_bytes(4, "little")
            + state.frames_sent.to_bytes(2, "little")
            + state.frame_sequence.to_bytes(2, "little")
        )
        return build_reply_frame(reply_id, data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mock uvk5cec FT4 UART responder over pyserial socket:// transport.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7001)
    parser.add_argument("--version", default="CEC_MOCK")
    args = parser.parse_args(argv)

    state = MockState(lock=Lock(), version=args.version)
    with MockResponderServer((args.host, args.port), state) as server:
        print(f"mock_responder_ready=socket://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
