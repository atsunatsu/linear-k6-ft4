from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from .bridge import BridgeController
from .config import SerialFrontendConfig
from .rigctl import RigctlCommandProcessor, ServerRole

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
class PySerialByteStream(ByteStreamEndpoint):
    config: SerialFrontendConfig

    def __post_init__(self) -> None:
        self._serial = None

    async def open(self) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency specific
            raise RuntimeError("pyserial is required for serial frontend support") from exc

        self._serial = await asyncio.to_thread(
            serial.Serial,
            port=self.config.port,
            baudrate=self.config.baudrate,
            timeout=self.config.read_timeout_seconds,
            write_timeout=self.config.read_timeout_seconds,
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
        return await asyncio.to_thread(self._serial.read, self.config.read_chunk_size)

    async def write(self, data: bytes) -> None:
        if self._serial is None:
            return
        await asyncio.to_thread(self._serial.write, data)
        await asyncio.to_thread(self._serial.flush)


class MemoryByteStream(ByteStreamEndpoint):
    def __init__(self) -> None:
        self._incoming: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.written = bytearray()

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        await self._incoming.put(None)

    async def read_chunk(self) -> bytes:
        item = await self._incoming.get()
        if item is None:
            return b""
        return item

    async def write(self, data: bytes) -> None:
        self.written.extend(data)

    def feed_peer_data(self, data: bytes) -> None:
        self._incoming.put_nowait(data)

    def take_written(self) -> bytes:
        data = bytes(self.written)
        self.written.clear()
        return data


class SerialRigctlFrontend:
    def __init__(self, stream: ByteStreamEndpoint, controller: BridgeController) -> None:
        self._stream = stream
        self._processor = RigctlCommandProcessor(role=ServerRole.WSJTX, controller=controller)
        self._buffer = bytearray()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self._stream.open()
        self._task = asyncio.create_task(self._run())

    async def wait_closed(self) -> None:
        if self._task is not None:
            await self._task

    async def close(self) -> None:
        await self._stream.close()
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            chunk = await self._stream.read_chunk()
            if not chunk:
                await asyncio.sleep(0)
                continue
            self._buffer.extend(chunk)
            while b"\n" in self._buffer:
                raw_line, _, remainder = self._buffer.partition(b"\n")
                self._buffer = bytearray(remainder)
                request = raw_line.decode(errors="replace").strip()
                if not request:
                    continue
                try:
                    response = await self._processor.dispatch(request)
                except ValueError as exc:
                    response = f"RPRT -1 {exc}\n"
                except Exception as exc:  # pragma: no cover
                    LOGGER.exception("Unhandled serial frontend request error")
                    response = f"RPRT -2 {exc}\n"
                if response is not None:
                    await self._stream.write(response.encode())
