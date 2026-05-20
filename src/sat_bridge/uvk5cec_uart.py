from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import struct
import time
from typing import BinaryIO

import binascii


OUTER_HEADER_ID = 0xCDAB
OUTER_FOOTER_ID = 0xBADC

CMD_SESSION_HELLO = 0x0514
CMD_SESSION_CONFIG = 0x052F
CMD_START_FT4_TX = 0x0701
CMD_UPDATE_TX_FREQ = 0x0703
CMD_STOP_TX = 0x0705

REPLY_VERSION = 0x0515
REPLY_START_FT4_TX = 0x0702
REPLY_UPDATE_TX_FREQ = 0x0704
REPLY_STOP_TX = 0x0706

FT4TX_STATUS_OK = 0
FT4TX_STATUS_BUSY = 1
FT4TX_STATUS_NOT_ACTIVE = 2
FT4TX_STATUS_TX_NOT_READY = 3
FT4TX_STATUS_PAYLOAD_TOO_LONG = 4

MAX_FT4_PAYLOAD_BYTES = 64

FT4TX_STATUS_NAMES = {
    FT4TX_STATUS_OK: "OK",
    FT4TX_STATUS_BUSY: "BUSY",
    FT4TX_STATUS_NOT_ACTIVE: "NOT_ACTIVE",
    FT4TX_STATUS_TX_NOT_READY: "TX_NOT_READY",
    FT4TX_STATUS_PAYLOAD_TOO_LONG: "PAYLOAD_TOO_LONG",
}


@dataclass(slots=True)
class SessionContext:
    port: str
    baudrate: int
    timestamp: int


@dataclass(slots=True)
class VersionReply:
    version: str
    has_custom_aes_key: bool
    is_in_lock_screen: bool
    challenge: tuple[int, int, int, int]


@dataclass(slots=True)
class Ft4BenchReply:
    reply_id: int
    status: int
    active: bool
    retune_mode: int
    current_tx_frequency_hz: int
    last_applied_tx_frequency_hz: int
    pending_tx_frequency_hz: int
    frames_sent: int
    frame_sequence: int


@dataclass(slots=True)
class ParsedCommand:
    command_id: int
    body: bytes


def crc16_ccitt(data: bytes) -> int:
    return binascii.crc_hqx(data, 0)


def build_host_frame(command_id: int, body: bytes) -> bytes:
    inner = struct.pack("<HH", command_id, len(body)) + body
    crc = crc16_ccitt(inner)
    return _build_outer_frame(inner, crc)


def build_reply_frame(reply_id: int, data: bytes) -> bytes:
    inner = struct.pack("<HH", reply_id, len(data)) + data
    crc = crc16_ccitt(inner)
    return _build_outer_frame(inner, crc)


def build_session_hello(timestamp: int) -> bytes:
    return build_host_frame(CMD_SESSION_HELLO, struct.pack("<I", timestamp))


def build_session_config(timestamp: int) -> bytes:
    return build_host_frame(CMD_SESSION_CONFIG, struct.pack("<I", timestamp))


def build_start_ft4_tx(timestamp: int, tx_frequency_hz: int, payload_text: str) -> bytes:
    payload = render_ascii_payload(payload_text, MAX_FT4_PAYLOAD_BYTES)
    body = struct.pack("<II", timestamp, tx_frequency_hz) + struct.pack("<B3x", len(payload.rstrip(b" "))) + payload
    return build_host_frame(CMD_START_FT4_TX, body)


def build_update_tx_frequency(timestamp: int, tx_frequency_hz: int) -> bytes:
    return build_host_frame(CMD_UPDATE_TX_FREQ, struct.pack("<II", timestamp, tx_frequency_hz))


def build_stop_tx(timestamp: int) -> bytes:
    return build_host_frame(CMD_STOP_TX, struct.pack("<I", timestamp))


def render_ascii_payload(payload_text: str, width: int) -> bytes:
    normalized = payload_text.upper()
    safe = "".join(character if 0x20 <= ord(character) <= 0x7E else " " for character in normalized)
    return safe[:width].ljust(width).encode("ascii")


def read_frame(stream: BinaryIO) -> bytes:
    header = _read_exact(stream, 4)
    outer_id, size = struct.unpack("<HH", header)
    if outer_id != OUTER_HEADER_ID:
        raise ValueError(f"Unexpected outer header id 0x{outer_id:04x}")
    payload = _read_exact(stream, size)
    crc = _read_exact(stream, 2)
    footer = _read_exact(stream, 4)
    padding, footer_id = struct.unpack("<HH", footer)
    if footer_id != OUTER_FOOTER_ID:
        raise ValueError(f"Unexpected outer footer id 0x{footer_id:04x}")
    if padding != 0xFFFF:
        raise ValueError(f"Unexpected footer padding 0x{padding:04x}")

    inner = payload + crc
    expected_crc = crc16_ccitt(payload)
    actual_crc = struct.unpack("<H", crc)[0]
    if expected_crc != actual_crc:
        raise ValueError(f"CRC mismatch expected=0x{expected_crc:04x} actual=0x{actual_crc:04x}")
    return inner


def parse_command_frame(frame: bytes) -> ParsedCommand:
    if len(frame) < 6:
        raise ValueError("Command frame is too short")
    command_id, body_size = struct.unpack("<HH", frame[:4])
    body = frame[4:-2]
    if len(body) != body_size:
        raise ValueError(f"Command body size mismatch expected={body_size} actual={len(body)}")
    return ParsedCommand(command_id=command_id, body=body)


def parse_version_reply(frame: bytes) -> VersionReply:
    reply_id, data_size = struct.unpack("<HH", frame[:4])
    if reply_id != REPLY_VERSION:
        raise ValueError(f"Expected version reply, got 0x{reply_id:04x}")
    if data_size < 36:
        raise ValueError(f"Version reply too short: {data_size}")
    data = frame[4 : 4 + data_size]
    version = data[:16].split(b"\x00", 1)[0].decode("ascii", errors="replace")
    challenge = struct.unpack("<IIII", data[20:36])
    return VersionReply(
        version=version,
        has_custom_aes_key=bool(data[16]),
        is_in_lock_screen=bool(data[17]),
        challenge=challenge,
    )


def parse_ft4_bench_reply(frame: bytes) -> Ft4BenchReply:
    reply_id, data_size = struct.unpack("<HH", frame[:4])
    if reply_id not in {REPLY_START_FT4_TX, REPLY_UPDATE_TX_FREQ, REPLY_STOP_TX}:
        raise ValueError(f"Unexpected FT4 reply id 0x{reply_id:04x}")
    if data_size != 20:
        raise ValueError(f"Unexpected FT4 reply size {data_size}")
    data = frame[4 : 4 + data_size]
    status, active, retune_mode, _padding = struct.unpack("<BBBB", data[:4])
    current_tx_frequency_hz, last_applied_tx_frequency_hz, pending_tx_frequency_hz = struct.unpack("<III", data[4:16])
    frames_sent, frame_sequence = struct.unpack("<HH", data[16:20])
    return Ft4BenchReply(
        reply_id=reply_id,
        status=status,
        active=bool(active),
        retune_mode=retune_mode,
        current_tx_frequency_hz=current_tx_frequency_hz,
        last_applied_tx_frequency_hz=last_applied_tx_frequency_hz,
        pending_tx_frequency_hz=pending_tx_frequency_hz,
        frames_sent=frames_sent,
        frame_sequence=frame_sequence,
    )


def load_session_context(path: str | Path) -> SessionContext:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return SessionContext(
        port=str(raw["port"]),
        baudrate=int(raw["baudrate"]),
        timestamp=int(raw["timestamp"]),
    )


def save_session_context(path: str | Path, session: SessionContext) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(session), indent=2), encoding="utf-8")


def default_session_timestamp() -> int:
    return int(time.time()) & 0xFFFFFFFF


class Uvk5CecSerialClient:
    def __init__(self, port: str, *, baudrate: int = 38400, timeout_seconds: float = 2.0):
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment-specific
            raise RuntimeError("pyserial is required for UART bench control") from exc
        self._serial_module = serial
        self.port = port
        self.baudrate = baudrate
        self.timeout_seconds = timeout_seconds
        self._serial = None

    def __enter__(self) -> "Uvk5CecSerialClient":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if self._serial is not None:
            return
        open_kwargs = {
            "baudrate": self.baudrate,
            "timeout": self.timeout_seconds,
            "write_timeout": self.timeout_seconds,
        }
        if "://" in self.port:
            self._serial = self._serial_module.serial_for_url(self.port, **open_kwargs)
        else:
            self._serial = self._serial_module.Serial(self.port, **open_kwargs)

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def bootstrap(self, timestamp: int) -> VersionReply:
        self.send_raw(build_session_hello(timestamp))
        return parse_version_reply(self.read_reply())

    def configure_session(self, timestamp: int) -> VersionReply:
        self.send_raw(build_session_config(timestamp))
        return parse_version_reply(self.read_reply())

    def start_ft4_tx(self, timestamp: int, tx_frequency_hz: int, payload_text: str) -> Ft4BenchReply:
        self.send_raw(build_start_ft4_tx(timestamp, tx_frequency_hz, payload_text))
        return parse_ft4_bench_reply(self.read_reply())

    def update_tx_frequency(self, timestamp: int, tx_frequency_hz: int) -> Ft4BenchReply:
        self.send_raw(build_update_tx_frequency(timestamp, tx_frequency_hz))
        return parse_ft4_bench_reply(self.read_reply())

    def stop_tx(self, timestamp: int) -> Ft4BenchReply:
        self.send_raw(build_stop_tx(timestamp))
        return parse_ft4_bench_reply(self.read_reply())

    def send_raw(self, payload: bytes) -> None:
        if self._serial is None:
            raise RuntimeError("serial port is not open")
        self._serial.write(payload)
        self._serial.flush()

    def read_reply(self) -> bytes:
        if self._serial is None:
            raise RuntimeError("serial port is not open")
        return read_frame(self._serial)


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    data = stream.read(size)
    if data is None or len(data) != size:
        raise TimeoutError(f"Timed out while reading {size} bytes from UART")
    return data


def _build_outer_frame(inner: bytes, crc: int) -> bytes:
    outer = struct.pack("<HH", OUTER_HEADER_ID, len(inner))
    footer = struct.pack("<HH", 0xFFFF, OUTER_FOOTER_ID)
    return outer + inner + struct.pack("<H", crc) + footer
