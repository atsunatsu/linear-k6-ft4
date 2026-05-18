from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass, field

from .bridge import BridgeController

LOGGER = logging.getLogger(__name__)


class ServerRole(str, enum.Enum):
    SATELLITE = "satellite"
    WSJTX = "wsjtx"


@dataclass(slots=True)
class RigctlCommandProcessor:
    role: ServerRole
    controller: BridgeController

    async def dispatch(self, request: str) -> str | None:
        parts = request.split()
        command = parts[0]
        args = parts[1:]

        if command == "q":
            return None
        if command == "_":
            return "sat-bridge\n"
        if command == "f":
            return f"{await self.controller.visible_frequency_for(self.role.value)}\n"
        if command == "i":
            return f"{(await self.controller.snapshot()).rx_frequency_hz}\n"
        if command == "x":
            return f"{(await self.controller.snapshot()).tx_frequency_hz}\n"
        if command == "t":
            return f"{int((await self.controller.snapshot()).ptt)}\n"
        if command == "m":
            snapshot = await self.controller.snapshot()
            return f"{snapshot.mode}\n0\n"
        if command == "s":
            return "1\nVFOA\n"
        if command == "v":
            return "VFOA\n"
        if command == "V":
            return "RPRT 0\n"
        if command == "S":
            enabled = _parse_bool_arg(args[0] if args else "1")
            await self.controller.set_split_enabled(enabled, role=self.role.value, source=request)
            return "RPRT 0\n"
        if command == "F":
            frequency_hz = _parse_frequency_arg(args)
            if self.role == ServerRole.SATELLITE:
                await self.controller.set_rx_frequency(frequency_hz, role=self.role.value, source=request)
            return "RPRT 0\n"
        if command == "I":
            frequency_hz = _parse_frequency_arg(args)
            if self.role == ServerRole.SATELLITE:
                await self.controller.set_rx_frequency(frequency_hz, role=self.role.value, source=request)
            return "RPRT 0\n"
        if command == "X":
            frequency_hz = _parse_frequency_arg(args)
            if self.role == ServerRole.SATELLITE:
                await self.controller.set_tx_frequency(frequency_hz, role=self.role.value, source=request)
            return "RPRT 0\n"
        if command == "M":
            if not args:
                raise ValueError("Mode is required.")
            await self.controller.set_mode(args[0], role=self.role.value, source=request)
            return "RPRT 0\n"
        if command == "T":
            enabled = _parse_bool_arg(args[0] if args else "0")
            await self.controller.set_ptt(enabled, role=self.role.value, source=request)
            return "RPRT 0\n"
        return "RPRT -11\n"


@dataclass(slots=True)
class RigctlServer:
    role: ServerRole
    bind_host: str
    bind_port: int
    controller: BridgeController
    _server: asyncio.AbstractServer | None = field(init=False, default=None, repr=False)
    _processor: RigctlCommandProcessor = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._processor = RigctlCommandProcessor(role=self.role, controller=self.controller)

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, self.bind_host, self.bind_port)

    async def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError("Server not started.")
        async with self._server:
            await self._server.serve_forever()

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername")
        LOGGER.debug("Client connected on %s from %s", self.role, peer)
        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                request = line.decode(errors="replace").strip()
                if not request:
                    continue
                try:
                    response = await self._processor.dispatch(request)
                except ValueError as exc:
                    response = f"RPRT -1 {exc}\n"
                except Exception as exc:  # pragma: no cover
                    LOGGER.exception("Unhandled request error")
                    response = f"RPRT -2 {exc}\n"

                if response is None:
                    break
                writer.write(response.encode())
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            LOGGER.debug("Client disconnected on %s from %s", self.role, peer)


def _parse_frequency_arg(args: list[str]) -> int:
    if not args:
        raise ValueError("Frequency argument is required.")
    return int(float(args[0]))


def _parse_bool_arg(value: str) -> bool:
    normalized = value.strip().upper()
    if normalized in {"1", "ON", "TRUE"}:
        return True
    if normalized in {"0", "OFF", "FALSE"}:
        return False
    raise ValueError(f"Expected boolean-like value, got {value!r}")
