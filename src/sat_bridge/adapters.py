from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import HookCommands, SerialBackendConfig
from .models import AdapterFeedback, BridgeSnapshot

LOGGER = logging.getLogger(__name__)


class DigiAdapter(abc.ABC):
    """Radio-side adapter.

    This boundary exists to preserve the clean CEC/DigiManager transmit path.
    Implementations must forward control into that digital chain and must not
    synthesize analog SSB audio as a substitute.
    """

    async def open(self) -> None:
        """Optional adapter startup hook."""

    async def close(self) -> None:
        """Optional adapter shutdown hook."""

    @abc.abstractmethod
    async def set_rx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_tx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_radio_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_mode(self, mode: str, snapshot: BridgeSnapshot) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_ptt(self, enabled: bool, snapshot: BridgeSnapshot) -> AdapterFeedback:
        raise NotImplementedError


class NullAdapter(DigiAdapter):
    """No-op adapter for local testing."""

    async def set_rx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return AdapterFeedback.ok()

    async def set_tx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return AdapterFeedback.ok()

    async def set_radio_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return AdapterFeedback.ok()

    async def set_mode(self, mode: str, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return AdapterFeedback.ok()

    async def set_ptt(self, enabled: bool, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return AdapterFeedback.ok()


class HookAdapter(DigiAdapter):
    """Adapter that runs local helper commands for each radio action."""

    def __init__(self, commands: HookCommands, timeout_seconds: float = 5.0) -> None:
        self._commands = commands
        self._timeout_seconds = timeout_seconds

    async def set_rx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._run(
            self._commands.set_rx_frequency,
            frequency_hz=frequency_hz,
            snapshot=snapshot,
        )

    async def set_tx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._run(
            self._commands.set_tx_frequency,
            frequency_hz=frequency_hz,
            snapshot=snapshot,
        )

    async def set_radio_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._run(
            self._commands.set_radio_frequency,
            frequency_hz=frequency_hz,
            snapshot=snapshot,
        )

    async def set_mode(self, mode: str, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._run(self._commands.set_mode, mode=mode, snapshot=snapshot)

    async def set_ptt(self, enabled: bool, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._run(self._commands.set_ptt, ptt=int(enabled), snapshot=snapshot)

    async def _run(
        self,
        template: Iterable[str],
        *,
        snapshot: BridgeSnapshot,
        frequency_hz: int | None = None,
        mode: str | None = None,
        ptt: int | None = None,
    ) -> AdapterFeedback:
        argv = list(template)
        if not argv:
            return AdapterFeedback.ok()

        formatted = [
            token.format(
                frequency_hz=frequency_hz if frequency_hz is not None else "",
                mode=mode if mode is not None else snapshot.mode,
                ptt=ptt if ptt is not None else int(snapshot.ptt),
                role=snapshot.last_role,
                source=snapshot.last_source,
                rx_frequency_hz=snapshot.rx_frequency_hz,
                tx_frequency_hz=snapshot.tx_frequency_hz,
                active_frequency_hz=snapshot.radio_frequency_hz,
            )
            for token in argv
        ]
        LOGGER.debug("Running hook command: %s", formatted)
        process = await asyncio.create_subprocess_exec(
            *formatted,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path.cwd()),
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self._timeout_seconds)
        except TimeoutError:
            process.kill()
            await process.communicate()
            return AdapterFeedback.timeout(f"Adapter command timed out: {formatted!r}")

        if process.returncode != 0:
            return AdapterFeedback.failed(
                "Adapter command failed: "
                f"{formatted!r} exit={process.returncode} stderr={stderr.decode(errors='replace').strip()}"
            )
        if stdout:
            LOGGER.debug("Hook command stdout: %s", stdout.decode(errors="replace").strip())
        return AdapterFeedback.ok()


class SerialAdapter(DigiAdapter):
    """Adapter that writes control commands to DigiManager's input COM port."""

    def __init__(self, config: SerialBackendConfig) -> None:
        self._config = config
        self._serial = None
        self._lock = asyncio.Lock()

    async def open(self) -> None:
        if not self._config.enabled:
            return
        self._serial = await _open_serial_port(
            self._config.port,
            self._config.baudrate,
            self._config.read_timeout_seconds,
            self._config.write_timeout_seconds,
        )

    async def close(self) -> None:
        if self._serial is None:
            return
        serial_port = self._serial
        self._serial = None
        await asyncio.to_thread(serial_port.close)

    async def set_rx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._send("set_rx_frequency", snapshot, frequency_hz=frequency_hz)

    async def set_tx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._send("set_tx_frequency", snapshot, frequency_hz=frequency_hz)

    async def set_radio_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._send("set_radio_frequency", snapshot, frequency_hz=frequency_hz)

    async def set_mode(self, mode: str, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._send("set_mode", snapshot, mode=mode)

    async def set_ptt(self, enabled: bool, snapshot: BridgeSnapshot) -> AdapterFeedback:
        return await self._send("set_ptt", snapshot, ptt=int(enabled))

    async def _send(
        self,
        action: str,
        snapshot: BridgeSnapshot,
        *,
        frequency_hz: int | None = None,
        mode: str | None = None,
        ptt: int | None = None,
    ) -> AdapterFeedback:
        if not self._config.enabled:
            return AdapterFeedback.ok("serial backend disabled")
        if self._serial is None:
            return AdapterFeedback.failed("serial backend not open")

        payload = self._render_command(
            action,
            snapshot,
            frequency_hz=frequency_hz,
            mode=mode,
            ptt=ptt,
        )
        if payload is None:
            return AdapterFeedback.ok("no command for action")

        async with self._lock:
            try:
                await asyncio.to_thread(self._serial.write, payload)
                await asyncio.to_thread(self._serial.flush)
            except Exception as exc:  # pragma: no cover - hardware specific
                return AdapterFeedback.failed(str(exc))

            if not self._config.expect_response:
                return AdapterFeedback.ok()

            try:
                raw = await asyncio.wait_for(
                    asyncio.to_thread(
                        _read_until_terminator,
                        self._serial,
                        self._config.response_terminator.encode("ascii"),
                    ),
                    timeout=self._config.response_timeout_seconds,
                )
            except TimeoutError:
                return AdapterFeedback.timeout("serial response timeout")
            except Exception as exc:  # pragma: no cover - hardware specific
                return AdapterFeedback.failed(str(exc))

        if not raw:
            return AdapterFeedback.timeout("empty serial response")
        return AdapterFeedback.ok(raw.decode(errors="replace").strip())

    def _render_command(
        self,
        action: str,
        snapshot: BridgeSnapshot,
        *,
        frequency_hz: int | None = None,
        mode: str | None = None,
        ptt: int | None = None,
    ) -> bytes | None:
        template = getattr(self._config.commands, action)
        if template is None:
            template = _default_serial_template(self._config.protocol, action)
        if template is None:
            return None
        rendered = template.format(
            frequency_hz=frequency_hz if frequency_hz is not None else "",
            mode=mode if mode is not None else snapshot.mode,
            ptt=ptt if ptt is not None else int(snapshot.ptt),
            rx_frequency_hz=snapshot.rx_frequency_hz,
            tx_frequency_hz=snapshot.tx_frequency_hz,
            active_frequency_hz=snapshot.radio_frequency_hz,
        )
        if not rendered.endswith(self._config.command_terminator):
            rendered += self._config.command_terminator
        return rendered.encode("ascii")


class RecordingAdapter(DigiAdapter):
    """Test adapter that records all bridge actions."""

    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self._feedbacks: dict[str, list[AdapterFeedback]] = {}

    def push_feedback(self, action: str, feedback: AdapterFeedback) -> None:
        self._feedbacks.setdefault(action, []).append(feedback)

    def _next_feedback(self, action: str) -> AdapterFeedback:
        queue = self._feedbacks.get(action)
        if queue:
            return queue.pop(0)
        return AdapterFeedback.ok()

    async def set_rx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        self.events.append(("set_rx_frequency", frequency_hz))
        return self._next_feedback("set_rx_frequency")

    async def set_tx_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        self.events.append(("set_tx_frequency", frequency_hz))
        return self._next_feedback("set_tx_frequency")

    async def set_radio_frequency(self, frequency_hz: int, snapshot: BridgeSnapshot) -> AdapterFeedback:
        self.events.append(("set_radio_frequency", frequency_hz))
        return self._next_feedback("set_radio_frequency")

    async def set_mode(self, mode: str, snapshot: BridgeSnapshot) -> AdapterFeedback:
        self.events.append(("set_mode", mode))
        return self._next_feedback("set_mode")

    async def set_ptt(self, enabled: bool, snapshot: BridgeSnapshot) -> AdapterFeedback:
        self.events.append(("set_ptt", enabled))
        return self._next_feedback("set_ptt")


async def _open_serial_port(port: str, baudrate: int, read_timeout: float, write_timeout: float):
    try:
        import serial  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency-specific
        raise RuntimeError("pyserial is required for serial adapter support") from exc

    return await asyncio.to_thread(
        serial.Serial,
        port=port,
        baudrate=baudrate,
        timeout=read_timeout,
        write_timeout=write_timeout,
    )


def _read_until_terminator(serial_port, terminator: bytes) -> bytes:
    buffer = bytearray()
    while True:
        chunk = serial_port.read(1)
        if not chunk:
            return bytes(buffer)
        buffer.extend(chunk)
        if buffer.endswith(terminator):
            return bytes(buffer)


def _default_serial_template(protocol: str, action: str) -> str | None:
    if protocol != "rigctl":
        return None
    templates = {
        "set_rx_frequency": "I {frequency_hz}",
        "set_tx_frequency": "X {frequency_hz}",
        "set_radio_frequency": "F {frequency_hz}",
        "set_mode": "M {mode}",
        "set_ptt": "T {ptt}",
    }
    return templates.get(action)
