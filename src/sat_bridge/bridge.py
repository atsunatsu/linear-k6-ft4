from __future__ import annotations

import asyncio
from dataclasses import replace
import logging
from typing import Awaitable, Callable

from .adapters import DigiAdapter
from .models import AdapterFeedback, BridgeSnapshot

AdapterCall = Callable[[BridgeSnapshot], Awaitable[None]]
LOGGER = logging.getLogger(__name__)


class BridgeController:
    """Shared FT4-first radio state for TCP and serial control frontends."""

    def __init__(
        self,
        *,
        adapter: DigiAdapter,
        initial_rx_frequency_hz: int,
        initial_tx_frequency_hz: int,
        initial_mode: str,
        tx_min_step_hz: int,
        tx_rate_limit_hz: float,
        tx_rate_limit_window_ms: int,
    ) -> None:
        self._adapter = adapter
        self._tx_min_step_hz = tx_min_step_hz
        self._tx_rate_limit_hz = tx_rate_limit_hz
        self._tx_rate_limit_window_ms = tx_rate_limit_window_ms
        self._lock = asyncio.Lock()
        self._retune_event = asyncio.Event()
        self._retune_task: asyncio.Task[None] | None = None
        self._snapshot = BridgeSnapshot(
            rx_frequency_hz=initial_rx_frequency_hz,
            tx_frequency_hz=initial_tx_frequency_hz,
            radio_frequency_hz=initial_rx_frequency_hz,
            mode=initial_mode.upper(),
        )

    async def start(self) -> None:
        if self._retune_task is None:
            self._retune_task = asyncio.create_task(self._tx_retune_loop())

    async def stop(self) -> None:
        if self._retune_task is None:
            return
        task = self._retune_task
        self._retune_task = None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def initialize(self) -> BridgeSnapshot:
        return await self._apply_changes(
            "bootstrap",
            "bridge",
            lambda state: [
                self._call("set_rx_frequency", state.rx_frequency_hz),
                self._call("set_tx_frequency", state.tx_frequency_hz),
                self._call("set_radio_frequency", state.radio_frequency_hz),
                self._call("set_mode", state.mode),
            ],
            mutate_state=False,
        )

    async def snapshot(self) -> BridgeSnapshot:
        async with self._lock:
            return replace(self._snapshot)

    async def set_mode(self, mode: str, *, role: str, source: str) -> BridgeSnapshot:
        normalized = mode.upper()
        if normalized not in {"FT4", "FT8", "TUNE"}:
            raise ValueError(f"Unsupported mode: {mode}")

        def mutate(state: BridgeSnapshot) -> list[AdapterCall]:
            if normalized == state.mode:
                return []
            state.mode = normalized
            return [self._call("set_mode", normalized)]

        return await self._apply_changes(role, source, mutate)

    async def set_rx_frequency(self, frequency_hz: int, *, role: str, source: str) -> BridgeSnapshot:
        self._validate_frequency(frequency_hz)

        def mutate(state: BridgeSnapshot) -> list[AdapterCall]:
            state.rx_frequency_hz = frequency_hz
            actions = [self._call("set_rx_frequency", frequency_hz)]
            if not state.ptt:
                state.radio_frequency_hz = frequency_hz
                actions.append(self._call("set_radio_frequency", frequency_hz))
            return actions

        return await self._apply_changes(role, source, mutate)

    async def set_tx_frequency(self, frequency_hz: int, *, role: str, source: str) -> BridgeSnapshot:
        self._validate_frequency(frequency_hz)

        def mutate(state: BridgeSnapshot) -> list[AdapterCall]:
            state.tx_frequency_hz = frequency_hz
            actions = [self._call("set_tx_frequency", frequency_hz)]
            if state.ptt:
                state.pending_target_tx_hz = frequency_hz
            return actions

        snapshot = await self._apply_changes(role, source, mutate)
        if snapshot.ptt:
            self._retune_event.set()
        return snapshot

    async def set_split_enabled(self, enabled: bool, *, role: str, source: str) -> BridgeSnapshot:
        if not enabled:
            raise ValueError("Split mode is required for satellite operation.")

        def mutate(state: BridgeSnapshot) -> list[AdapterCall]:
            state.split_enabled = True
            return []

        return await self._apply_changes(role, source, mutate)

    async def set_ptt(self, enabled: bool, *, role: str, source: str) -> BridgeSnapshot:
        def mutate(state: BridgeSnapshot) -> list[AdapterCall]:
            if state.ptt == enabled:
                return []

            actions: list[AdapterCall] = []
            if enabled:
                state.radio_frequency_hz = state.tx_frequency_hz
                state.ptt = True
                state.last_applied_tx_hz = state.tx_frequency_hz
                state.last_apply_monotonic = asyncio.get_running_loop().time()
                state.pending_target_tx_hz = None
                state.retune_mode = "immediate"
                state.consecutive_successes = 0
                state.consecutive_failures = 0
                actions.append(self._call("set_radio_frequency", state.tx_frequency_hz))
                actions.append(self._call("set_ptt", True))
                return actions

            state.ptt = False
            state.pending_target_tx_hz = None
            state.last_applied_tx_hz = None
            state.last_apply_monotonic = 0.0
            state.retune_mode = "immediate"
            state.consecutive_successes = 0
            state.consecutive_failures = 0
            actions.append(self._call("set_ptt", False))
            state.radio_frequency_hz = state.rx_frequency_hz
            actions.append(self._call("set_rx_frequency", state.rx_frequency_hz))
            actions.append(self._call("set_radio_frequency", state.radio_frequency_hz))
            return actions

        snapshot = await self._apply_changes(role, source, mutate)
        if not enabled:
            self._retune_event.set()
        return snapshot

    async def visible_frequency_for(self, role: str) -> int:
        snapshot = await self.snapshot()
        if role == "satellite":
            return snapshot.rx_frequency_hz
        return snapshot.radio_frequency_hz

    async def _apply_changes(
        self,
        role: str,
        source: str,
        mutate: Callable[[BridgeSnapshot], list[AdapterCall]],
        *,
        mutate_state: bool = True,
    ) -> BridgeSnapshot:
        async with self._lock:
            working = replace(self._snapshot)
            working.last_role = role
            working.last_source = source
            actions = mutate(working)
            if mutate_state:
                self._snapshot = working
                snapshot = replace(self._snapshot)
            else:
                snapshot = replace(working)

        for action in actions:
            await action(snapshot)
        return snapshot

    def _call(self, name: str, value: int | str | bool) -> AdapterCall:
        async def run(snapshot: BridgeSnapshot) -> None:
            adapter_method = getattr(self._adapter, name)
            feedback = await adapter_method(value, snapshot)
            await self._apply_feedback(name, feedback)

        return run

    async def _apply_feedback(self, action: str, feedback: AdapterFeedback) -> None:
        if feedback.is_ok:
            async with self._lock:
                self._snapshot.consecutive_successes += 1
                self._snapshot.consecutive_failures = 0
                if self._snapshot.retune_mode == "rate_limited" and self._snapshot.consecutive_successes >= 3:
                    self._snapshot.retune_mode = "immediate"
            return

        LOGGER.warning("Adapter action %s returned %s: %s", action, feedback.status, feedback.detail)
        async with self._lock:
            self._snapshot.consecutive_failures += 1
            self._snapshot.consecutive_successes = 0
            self._snapshot.retune_mode = "rate_limited"

    async def _tx_retune_loop(self) -> None:
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
                await self._apply_tx_target(target_hz)

    async def _next_tx_apply(self) -> tuple[float, int] | None:
        async with self._lock:
            snapshot = replace(self._snapshot)
            if not snapshot.ptt:
                self._snapshot.pending_target_tx_hz = None
                return None

            target_hz = snapshot.pending_target_tx_hz
            if target_hz is None:
                return None

            reference_hz = snapshot.last_applied_tx_hz or snapshot.radio_frequency_hz
            if abs(target_hz - reference_hz) < self._tx_min_step_hz:
                self._snapshot.pending_target_tx_hz = None
                return None

            if snapshot.retune_mode == "rate_limited":
                elapsed = asyncio.get_running_loop().time() - snapshot.last_apply_monotonic
                minimum_gap = self._tx_rate_limit_window_ms / 1000.0
                if elapsed < minimum_gap:
                    return (minimum_gap - elapsed, target_hz)

            self._snapshot.pending_target_tx_hz = None
            self._snapshot.radio_frequency_hz = target_hz
            return (0.0, target_hz)

    async def _apply_tx_target(self, target_hz: int) -> None:
        snapshot = await self.snapshot()
        feedback = await self._adapter.set_radio_frequency(target_hz, snapshot)
        async with self._lock:
            self._snapshot.last_apply_monotonic = asyncio.get_running_loop().time()
            if feedback.is_ok:
                self._snapshot.last_applied_tx_hz = target_hz
            else:
                self._snapshot.retune_mode = "rate_limited"
        await self._apply_feedback("set_radio_frequency", feedback)
        async with self._lock:
            if self._snapshot.pending_target_tx_hz is not None:
                self._retune_event.set()

    @staticmethod
    def _validate_frequency(frequency_hz: int) -> None:
        if frequency_hz <= 0:
            raise ValueError(f"Frequency must be positive, got {frequency_hz}")
