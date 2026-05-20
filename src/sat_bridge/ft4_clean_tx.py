from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, replace
import logging
from pathlib import Path
import socket
import subprocess
from typing import Iterable

from .config import Ft4CleanTxConfig
from .models import AdapterFeedback
from .udp_capture_tools import ReplayPacket, ReplaySequence, load_udp_replay_sequence

LOGGER = logging.getLogger(__name__)


PRINTABLE_MIN = 0x20
PRINTABLE_MAX = 0x7E


@dataclass(slots=True)
class Ft4TextField:
    start: int
    end: int
    original_text: str

    @property
    def length(self) -> int:
        return self.end - self.start


class Ft4ReplayTemplate:
    def __init__(self, sequence: ReplaySequence, *, transmission_index: int = 0) -> None:
        self._sequence = sequence
        self._transmission_index = transmission_index
        self._marker_indexes = [
            index for index, packet in enumerate(sequence.packets) if packet.tag == "ft4_mode_marker"
        ]
        if not self._marker_indexes:
            raise ValueError(f"Replay sequence {sequence.source_capture!r} has no FT4 mode markers")
        if transmission_index < 0 or transmission_index >= len(self._marker_indexes):
            raise ValueError(
                f"Transmission index {transmission_index} is out of range for {len(self._marker_indexes)} markers"
            )
        marker_packet = sequence.packets[self._marker_indexes[transmission_index]]
        self._text_field = self._detect_text_field(bytes.fromhex(marker_packet.payload_hex))

    @classmethod
    def from_path(cls, path: str | Path, *, transmission_index: int = 0) -> "Ft4ReplayTemplate":
        return cls(load_udp_replay_sequence(path), transmission_index=transmission_index)

    def build_transmission(self, payload: str) -> ReplaySequence:
        packets = self._extract_transmission_packets()
        rendered_packets = [self._patch_packet(packet, payload) for packet in packets]
        if not rendered_packets:
            raise ValueError("Replay template did not produce any packets")

        return ReplaySequence(
            source_capture=self._sequence.source_capture,
            mode="FT4",
            destination_host=self._sequence.destination_host,
            destination_port=self._sequence.destination_port,
            packets=rendered_packets,
        )

    def _extract_transmission_packets(self) -> list[ReplayPacket]:
        current_marker_index = self._marker_indexes[self._transmission_index]
        current_offset = self._sequence.packets[current_marker_index].timestamp_offset_ms
        previous_offset = 0
        if self._transmission_index > 0:
            previous_marker_index = self._marker_indexes[self._transmission_index - 1]
            previous_offset = self._sequence.packets[previous_marker_index].timestamp_offset_ms

        last_packet_offset = self._sequence.packets[-1].timestamp_offset_ms + 1
        next_offset = last_packet_offset
        if self._transmission_index + 1 < len(self._marker_indexes):
            next_marker_index = self._marker_indexes[self._transmission_index + 1]
            next_offset = self._sequence.packets[next_marker_index].timestamp_offset_ms

        start_boundary = 0 if self._transmission_index == 0 else (previous_offset + current_offset) // 2
        end_boundary = last_packet_offset if next_offset == last_packet_offset else (current_offset + next_offset) // 2

        selected = [
            packet
            for packet in self._sequence.packets
            if start_boundary <= packet.timestamp_offset_ms < end_boundary
        ]
        if not selected:
            return []

        base_offset = selected[0].timestamp_offset_ms
        return [
            replace(packet, timestamp_offset_ms=packet.timestamp_offset_ms - base_offset)
            for packet in selected
        ]

    def _patch_packet(self, packet: ReplayPacket, payload: str) -> ReplayPacket:
        if packet.tag != "ft4_mode_marker":
            return replace(packet)

        raw = bytearray(bytes.fromhex(packet.payload_hex))
        rendered_payload = _render_ascii_payload(payload, self._text_field.length)
        raw[self._text_field.start : self._text_field.end] = rendered_payload
        return replace(packet, payload_hex=bytes(raw).hex(" "))

    @staticmethod
    def _detect_text_field(payload: bytes) -> Ft4TextField:
        best_start = -1
        best_end = -1
        run_start = -1

        for index, value in enumerate(payload[:-2]):
            is_printable = PRINTABLE_MIN <= value <= PRINTABLE_MAX
            if is_printable:
                if run_start == -1:
                    run_start = index
                continue
            if run_start != -1:
                if index - run_start > best_end - best_start:
                    best_start, best_end = run_start, index
                run_start = -1

        if run_start != -1 and len(payload[:-2]) - run_start > best_end - best_start:
            best_start, best_end = run_start, len(payload[:-2])

        if best_start == -1 or best_end - best_start < 8:
            raise ValueError("Could not detect ASCII text field in FT4 mode marker packet")

        original_text = payload[best_start:best_end].decode("ascii", errors="replace")
        return Ft4TextField(start=best_start, end=best_end, original_text=original_text)


class Ft4PacketBackend(abc.ABC):
    async def open(self) -> None:
        return None

    async def close(self) -> None:
        return None

    @abc.abstractmethod
    async def set_tx_frequency(self, frequency_hz: int) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def set_ptt(self, enabled: bool) -> AdapterFeedback:
        raise NotImplementedError

    @abc.abstractmethod
    async def send_packet(self, payload: bytes) -> AdapterFeedback:
        raise NotImplementedError


class UdpFt4Backend(Ft4PacketBackend):
    def __init__(self, config: Ft4CleanTxConfig) -> None:
        self._config = config
        self._socket: socket.socket | None = None

    async def open(self) -> None:
        if self._config.transport == "udp":
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    async def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    async def set_tx_frequency(self, frequency_hz: int) -> AdapterFeedback:
        return await _run_hook(
            self._config.commands.set_tx_frequency,
            timeout_seconds=self._config.command_timeout_seconds,
            frequency_hz=frequency_hz,
        )

    async def set_ptt(self, enabled: bool) -> AdapterFeedback:
        return await _run_hook(
            self._config.commands.set_ptt,
            timeout_seconds=self._config.command_timeout_seconds,
            ptt=int(enabled),
        )

    async def send_packet(self, payload: bytes) -> AdapterFeedback:
        if self._config.transport == "command":
            return await _run_hook(
                self._config.commands.send_packet,
                timeout_seconds=self._config.command_timeout_seconds,
                payload_hex=payload.hex(" "),
            )

        if self._socket is None:
            return AdapterFeedback.failed("UDP FT4 backend is not open")
        try:
            await asyncio.to_thread(
                self._socket.sendto,
                payload,
                (self._config.destination_host, self._config.destination_port),
            )
        except OSError as exc:
            return AdapterFeedback.failed(str(exc))
        return AdapterFeedback.ok()


class RecordingFt4Backend(Ft4PacketBackend):
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

    async def set_tx_frequency(self, frequency_hz: int) -> AdapterFeedback:
        self.events.append(("set_tx_frequency", frequency_hz))
        return self._next_feedback("set_tx_frequency")

    async def set_ptt(self, enabled: bool) -> AdapterFeedback:
        self.events.append(("set_ptt", enabled))
        return self._next_feedback("set_ptt")

    async def send_packet(self, payload: bytes) -> AdapterFeedback:
        self.events.append(("send_packet", payload))
        return self._next_feedback("send_packet")


class Ft4CleanTransmitter:
    def __init__(
        self,
        *,
        template: Ft4ReplayTemplate,
        backend: Ft4PacketBackend,
        tx_min_step_hz: int,
        tx_rate_limit_hz: float,
        tx_rate_limit_window_ms: int,
        timing_mode: str = "original_timing",
    ) -> None:
        self._template = template
        self._backend = backend
        self._tx_min_step_hz = tx_min_step_hz
        self._tx_rate_limit_hz = tx_rate_limit_hz
        self._tx_rate_limit_window_ms = tx_rate_limit_window_ms
        self._timing_mode = timing_mode
        self._lock = asyncio.Lock()
        self._retune_event = asyncio.Event()
        self._retune_task: asyncio.Task[None] | None = None
        self._replay_task: asyncio.Task[None] | None = None
        self._replay_error: RuntimeError | None = None
        self._active = False
        self._pending_target_hz: int | None = None
        self._last_applied_tx_hz: int | None = None
        self._last_apply_monotonic = 0.0
        self._retune_mode = "immediate"
        self._consecutive_successes = 0
        self._consecutive_failures = 0

    async def open(self) -> None:
        await self._backend.open()
        if self._retune_task is None:
            self._retune_task = asyncio.create_task(self._retune_loop())

    async def close(self) -> None:
        await self.stop_tx()
        if self._retune_task is not None:
            task = self._retune_task
            self._retune_task = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await self._backend.close()

    async def start_ft4_tx(self, payload: str, tx_frequency_hz: int) -> None:
        await self.stop_tx()
        sequence = self._template.build_transmission(payload)

        frequency_feedback = await self._backend.set_tx_frequency(tx_frequency_hz)
        await self._apply_feedback(frequency_feedback)
        if not frequency_feedback.is_ok:
            raise RuntimeError(f"FT4 clean TX failed to set start frequency: {frequency_feedback.detail}")
        ptt_feedback = await self._backend.set_ptt(True)
        await self._apply_feedback(ptt_feedback)
        if not ptt_feedback.is_ok:
            raise RuntimeError(f"FT4 clean TX failed to enable PTT: {ptt_feedback.detail}")

        async with self._lock:
            self._active = True
            self._replay_error = None
            self._pending_target_hz = None
            self._last_applied_tx_hz = tx_frequency_hz
            self._last_apply_monotonic = asyncio.get_running_loop().time()
            self._retune_mode = "immediate"
            self._consecutive_successes = 0
            self._consecutive_failures = 0
            self._replay_task = asyncio.create_task(self._run_sequence(sequence))

    async def stop_tx(self) -> None:
        replay_task = None
        async with self._lock:
            replay_task = self._replay_task
            self._replay_task = None
            self._replay_error = None
            was_active = self._active
            self._active = False
            self._pending_target_hz = None
            self._last_applied_tx_hz = None
            self._last_apply_monotonic = 0.0
            self._retune_mode = "immediate"
            self._consecutive_successes = 0
            self._consecutive_failures = 0

        if replay_task is not None:
            replay_task.cancel()
            try:
                await replay_task
            except asyncio.CancelledError:
                pass

        if was_active:
            feedback = await self._backend.set_ptt(False)
            await self._apply_feedback(feedback)

    async def wait_for_idle(self) -> None:
        replay_task = None
        async with self._lock:
            replay_task = self._replay_task
        if replay_task is None:
            async with self._lock:
                replay_error = self._replay_error
            if replay_error is not None:
                raise replay_error
            return
        try:
            await replay_task
        except asyncio.CancelledError:
            pass
        async with self._lock:
            replay_error = self._replay_error
        if replay_error is not None:
            raise replay_error

    async def update_tx_frequency(self, tx_frequency_hz: int) -> None:
        async with self._lock:
            if not self._active:
                feedback = await self._backend.set_tx_frequency(tx_frequency_hz)
                await self._apply_feedback(feedback)
                self._last_applied_tx_hz = tx_frequency_hz
                self._last_apply_monotonic = asyncio.get_running_loop().time()
                return

            reference_hz = self._last_applied_tx_hz or tx_frequency_hz
            if abs(tx_frequency_hz - reference_hz) < self._tx_min_step_hz:
                return
            self._pending_target_hz = tx_frequency_hz
            self._retune_event.set()

    async def _run_sequence(self, sequence: ReplaySequence) -> None:
        try:
            previous_offset = 0
            for packet in sequence.packets:
                delay_ms = 0
                if self._timing_mode == "original_timing":
                    delay_ms = max(0, packet.timestamp_offset_ms - previous_offset)
                if delay_ms:
                    await asyncio.sleep(delay_ms / 1000.0)
                feedback = await self._backend.send_packet(bytes.fromhex(packet.payload_hex))
                await self._apply_feedback(feedback)
                if not feedback.is_ok:
                    raise RuntimeError(f"FT4 clean TX packet send failed: {feedback.detail}")
                previous_offset = packet.timestamp_offset_ms
        except RuntimeError as exc:
            async with self._lock:
                self._replay_error = exc
        finally:
            async with self._lock:
                self._active = False
                self._replay_task = None
                self._pending_target_hz = None
                self._last_applied_tx_hz = None
                self._last_apply_monotonic = 0.0
            feedback = await self._backend.set_ptt(False)
            await self._apply_feedback(feedback)

    async def _retune_loop(self) -> None:
        while True:
            await self._retune_event.wait()
            self._retune_event.clear()

            while True:
                maybe_apply = await self._next_tx_apply()
                if maybe_apply is None:
                    break
                wait_seconds, target_hz = maybe_apply
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                    continue
                feedback = await self._backend.set_tx_frequency(target_hz)
                async with self._lock:
                    self._last_apply_monotonic = asyncio.get_running_loop().time()
                    if feedback.is_ok:
                        self._last_applied_tx_hz = target_hz
                await self._apply_feedback(feedback)

    async def _next_tx_apply(self) -> tuple[float, int] | None:
        async with self._lock:
            if not self._active:
                self._pending_target_hz = None
                return None

            target_hz = self._pending_target_hz
            if target_hz is None:
                return None

            reference_hz = self._last_applied_tx_hz or target_hz
            if abs(target_hz - reference_hz) < self._tx_min_step_hz:
                self._pending_target_hz = None
                return None

            if self._retune_mode == "rate_limited":
                elapsed = asyncio.get_running_loop().time() - self._last_apply_monotonic
                minimum_gap = self._tx_rate_limit_window_ms / 1000.0
                if elapsed < minimum_gap:
                    return (minimum_gap - elapsed, target_hz)

            self._pending_target_hz = None
            return (0.0, target_hz)

    async def _apply_feedback(self, feedback: AdapterFeedback) -> None:
        async with self._lock:
            if feedback.is_ok:
                self._consecutive_successes += 1
                self._consecutive_failures = 0
                if self._retune_mode == "rate_limited" and self._consecutive_successes >= 3:
                    self._retune_mode = "immediate"
                return

            LOGGER.warning("FT4 clean transmitter backend returned %s: %s", feedback.status, feedback.detail)
            self._consecutive_failures += 1
            self._consecutive_successes = 0
            self._retune_mode = "rate_limited"


async def _run_hook(
    template: Iterable[str],
    *,
    timeout_seconds: float,
    frequency_hz: int | None = None,
    ptt: int | None = None,
    payload_hex: str | None = None,
) -> AdapterFeedback:
    argv = list(template)
    if not argv:
        return AdapterFeedback.ok()

    formatted = [
        token.format(
            frequency_hz=frequency_hz if frequency_hz is not None else "",
            ptt=ptt if ptt is not None else "",
            payload_hex=payload_hex if payload_hex is not None else "",
        )
        for token in argv
    ]
    try:
        completed = await asyncio.wait_for(
            asyncio.to_thread(
                subprocess.run,
                formatted,
                capture_output=True,
                text=True,
                cwd=str(Path.cwd()),
                check=False,
            ),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        return AdapterFeedback.timeout(f"FT4 clean TX hook timed out: {formatted!r}")

    if completed.returncode != 0:
        return AdapterFeedback.failed(
            f"FT4 clean TX hook failed: {formatted!r} exit={completed.returncode} "
            f"stderr={completed.stderr.strip()}"
        )
    if completed.stdout:
        LOGGER.debug("FT4 clean TX hook stdout: %s", completed.stdout.strip())
    return AdapterFeedback.ok()


def _render_ascii_payload(payload: str, width: int) -> bytes:
    normalized = payload.upper()
    safe = "".join(character if PRINTABLE_MIN <= ord(character) <= PRINTABLE_MAX else " " for character in normalized)
    rendered = safe[:width].ljust(width)
    return rendered.encode("ascii", errors="replace")
