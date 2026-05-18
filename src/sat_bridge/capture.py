from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import TextIO

LOGGER = logging.getLogger(__name__)


class ByteStreamEndpoint:
    async def open(self) -> None:  # pragma: no cover - interface method
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover - interface method
        raise NotImplementedError

    async def read_chunk(self) -> bytes:  # pragma: no cover - interface method
        raise NotImplementedError

    async def write(self, data: bytes) -> None:  # pragma: no cover - interface method
        raise NotImplementedError


@dataclass(slots=True)
class SerialCaptureConfig:
    wsjtx_port: str
    digimanager_port: str
    baudrate: int
    read_timeout_seconds: float
    read_chunk_size: int
    log_path: str
    scenario: str


@dataclass(slots=True)
class CaptureRecord:
    timestamp_ms: int
    direction: str
    bytes_hex: str
    bytes_ascii: str
    scenario: str
    port_name: str


class PySerialByteStream(ByteStreamEndpoint):
    def __init__(
        self,
        *,
        port: str,
        baudrate: int,
        read_timeout_seconds: float,
        read_chunk_size: int,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._read_timeout_seconds = read_timeout_seconds
        self._read_chunk_size = read_chunk_size
        self._serial = None

    async def open(self) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency specific
            raise RuntimeError("pyserial is required for serial capture support") from exc

        self._serial = await asyncio.to_thread(
            serial.Serial,
            port=self._port,
            baudrate=self._baudrate,
            timeout=self._read_timeout_seconds,
            write_timeout=self._read_timeout_seconds,
        )

    async def close(self) -> None:
        if self._serial is None:
            return
        serial_port = self._serial
        self._serial = None
        await asyncio.to_thread(serial_port.close)

    async def read_chunk(self) -> bytes:
        if self._serial is None:
            return b""
        return await asyncio.to_thread(self._serial.read, self._read_chunk_size)

    async def write(self, data: bytes) -> None:
        if self._serial is None:
            return
        await asyncio.to_thread(self._serial.write, data)
        await asyncio.to_thread(self._serial.flush)


class MemoryByteStream(ByteStreamEndpoint):
    def __init__(self) -> None:
        self._incoming: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.written = bytearray()
        self.is_open = False

    async def open(self) -> None:
        self.is_open = True

    async def close(self) -> None:
        self.is_open = False
        await self._incoming.put(None)

    async def read_chunk(self) -> bytes:
        item = await self._incoming.get()
        if item is None:
            return b""
        return item

    async def write(self, data: bytes) -> None:
        self.written.extend(data)

    def feed(self, data: bytes) -> None:
        self._incoming.put_nowait(data)

    def take_written(self) -> bytes:
        data = bytes(self.written)
        self.written.clear()
        return data


class JsonlCaptureWriter:
    def __init__(self, handle: TextIO) -> None:
        self._handle = handle
        self._lock = asyncio.Lock()

    async def write_record(
        self,
        *,
        direction: str,
        data: bytes,
        scenario: str,
        port_name: str,
    ) -> None:
        record = CaptureRecord(
            timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            direction=direction,
            bytes_hex=data.hex(" "),
            bytes_ascii=_to_printable_ascii(data),
            scenario=scenario,
            port_name=port_name,
        )
        async with self._lock:
            self._handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            self._handle.flush()


class SerialCaptureProxy:
    def __init__(
        self,
        *,
        wsjtx_stream: ByteStreamEndpoint,
        digimanager_stream: ByteStreamEndpoint,
        writer: JsonlCaptureWriter,
        scenario: str,
        wsjtx_port_name: str,
        digimanager_port_name: str,
    ) -> None:
        self._wsjtx_stream = wsjtx_stream
        self._digimanager_stream = digimanager_stream
        self._writer = writer
        self._scenario = scenario
        self._wsjtx_port_name = wsjtx_port_name
        self._digimanager_port_name = digimanager_port_name
        self._tasks: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        await self._wsjtx_stream.open()
        await self._digimanager_stream.open()
        self._tasks = [
            asyncio.create_task(
                self._pump(
                    source=self._wsjtx_stream,
                    destination=self._digimanager_stream,
                    direction="WSJT-X->DigiManager",
                    port_name=self._wsjtx_port_name,
                )
            ),
            asyncio.create_task(
                self._pump(
                    source=self._digimanager_stream,
                    destination=self._wsjtx_stream,
                    direction="DigiManager->WSJT-X",
                    port_name=self._digimanager_port_name,
                )
            ),
        ]

    async def wait(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks)

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        await self._wsjtx_stream.close()
        await self._digimanager_stream.close()

    async def _pump(
        self,
        *,
        source: ByteStreamEndpoint,
        destination: ByteStreamEndpoint,
        direction: str,
        port_name: str,
    ) -> None:
        while True:
            chunk = await source.read_chunk()
            if not chunk:
                await asyncio.sleep(0)
                continue
            await self._writer.write_record(
                direction=direction,
                data=chunk,
                scenario=self._scenario,
                port_name=port_name,
            )
            await destination.write(chunk)


async def run_capture_proxy(config: SerialCaptureConfig) -> None:
    log_path = Path(config.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        writer = JsonlCaptureWriter(handle)
        proxy = SerialCaptureProxy(
            wsjtx_stream=PySerialByteStream(
                port=config.wsjtx_port,
                baudrate=config.baudrate,
                read_timeout_seconds=config.read_timeout_seconds,
                read_chunk_size=config.read_chunk_size,
            ),
            digimanager_stream=PySerialByteStream(
                port=config.digimanager_port,
                baudrate=config.baudrate,
                read_timeout_seconds=config.read_timeout_seconds,
                read_chunk_size=config.read_chunk_size,
            ),
            writer=writer,
            scenario=config.scenario,
            wsjtx_port_name=config.wsjtx_port,
            digimanager_port_name=config.digimanager_port,
        )
        await proxy.start()
        LOGGER.info(
            "Serial capture proxy running: %s <-> %s, scenario=%s, log=%s",
            config.wsjtx_port,
            config.digimanager_port,
            config.scenario,
            config.log_path,
        )
        try:
            await proxy.wait()
        finally:
            await proxy.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transparent serial capture proxy for WSJT-X and DigiManager.")
    parser.add_argument("--wsjtx-port", required=True, help="COM port opened by WSJT-X toward the proxy.")
    parser.add_argument("--digimanager-port", required=True, help="COM port opened by DigiManager toward the proxy.")
    parser.add_argument("--baudrate", type=int, default=9600, help="Shared serial baudrate.")
    parser.add_argument("--read-timeout-seconds", type=float, default=0.1, help="Serial read timeout.")
    parser.add_argument("--read-chunk-size", type=int, default=256, help="Maximum bytes per read.")
    parser.add_argument("--scenario", default="unlabeled", help="Human-readable scenario label stored in JSONL.")
    parser.add_argument(
        "--log-path",
        default="logs/serial-capture.jsonl",
        help="Path to the JSONL capture log.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = SerialCaptureConfig(
        wsjtx_port=args.wsjtx_port,
        digimanager_port=args.digimanager_port,
        baudrate=args.baudrate,
        read_timeout_seconds=args.read_timeout_seconds,
        read_chunk_size=args.read_chunk_size,
        log_path=args.log_path,
        scenario=args.scenario,
    )
    try:
        asyncio.run(run_capture_proxy(config))
    except KeyboardInterrupt:
        LOGGER.info("Capture proxy interrupted, shutting down.")
    return 0


def _to_printable_ascii(data: bytes) -> str:
    rendered = []
    for byte in data:
        if 32 <= byte <= 126:
            rendered.append(chr(byte))
        elif byte in (9, 10, 13):
            rendered.append({9: "\\t", 10: "\\n", 13: "\\r"}[byte])
        else:
            rendered.append(".")
    return "".join(rendered)
