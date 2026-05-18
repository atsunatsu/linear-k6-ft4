from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.adapters import RecordingAdapter
from sat_bridge.bridge import BridgeController
from sat_bridge.models import AdapterFeedback


class BridgeControllerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.adapter = RecordingAdapter()
        self.controller = BridgeController(
            adapter=self.adapter,
            initial_rx_frequency_hz=435_000_000,
            initial_tx_frequency_hz=145_950_000,
            initial_mode="FT4",
            tx_min_step_hz=10,
            tx_rate_limit_hz=5.0,
            tx_rate_limit_window_ms=200,
        )
        await self.controller.start()
        await self.controller.initialize()

    async def asyncTearDown(self) -> None:
        await self.controller.stop()

    async def test_initialize_pushes_bootstrap_state(self) -> None:
        self.assertEqual(
            self.adapter.events[:4],
            [
                ("set_rx_frequency", 435_000_000),
                ("set_tx_frequency", 145_950_000),
                ("set_radio_frequency", 435_000_000),
                ("set_mode", "FT4"),
            ],
        )

    async def test_tx_frequency_updates_apply_during_ptt(self) -> None:
        self.adapter.events.clear()
        await self.controller.set_ptt(True, role="wsjtx", source="T 1")
        await self.controller.set_tx_frequency(145_955_500, role="satellite", source="X 145955500")
        await asyncio.sleep(0.05)

        snapshot = await self.controller.snapshot()
        self.assertEqual(snapshot.radio_frequency_hz, 145_955_500)
        self.assertIn(("set_radio_frequency", 145_955_500), self.adapter.events)

    async def test_small_tx_frequency_changes_are_ignored(self) -> None:
        self.adapter.events.clear()
        await self.controller.set_ptt(True, role="wsjtx", source="T 1")
        await self.controller.set_tx_frequency(145_950_005, role="satellite", source="X 145950005")
        await asyncio.sleep(0.05)

        radio_events = [event for event in self.adapter.events if event[0] == "set_radio_frequency"]
        self.assertEqual(radio_events, [("set_radio_frequency", 145_950_000)])

    async def test_rate_limited_mode_keeps_latest_target(self) -> None:
        self.adapter.events.clear()
        await self.controller.set_ptt(True, role="wsjtx", source="T 1")
        self.adapter.push_feedback("set_radio_frequency", AdapterFeedback.timeout("simulated timeout"))
        await self.controller.set_tx_frequency(145_955_000, role="satellite", source="X 145955000")
        await asyncio.sleep(0.05)
        await self.controller.set_tx_frequency(145_956_000, role="satellite", source="X 145956000")
        await self.controller.set_tx_frequency(145_957_000, role="satellite", source="X 145957000")
        await asyncio.sleep(0.30)

        radio_events = [value for action, value in self.adapter.events if action == "set_radio_frequency"]
        self.assertIn(145_957_000, radio_events)
        self.assertNotIn(145_956_000, radio_events)

    async def test_ptt_off_returns_to_rx_frequency(self) -> None:
        self.adapter.events.clear()
        await self.controller.set_ptt(True, role="wsjtx", source="T 1")
        await self.controller.set_tx_frequency(145_955_500, role="satellite", source="X 145955500")
        await asyncio.sleep(0.05)
        await self.controller.set_ptt(False, role="wsjtx", source="T 0")

        snapshot = await self.controller.snapshot()
        self.assertFalse(snapshot.ptt)
        self.assertEqual(snapshot.radio_frequency_hz, 435_000_000)
        self.assertEqual(
            self.adapter.events[-2:],
            [("set_rx_frequency", 435_000_000), ("set_radio_frequency", 435_000_000)],
        )

    async def test_wsjtx_reads_active_radio_frequency(self) -> None:
        await self.controller.set_ptt(True, role="wsjtx", source="T 1")
        self.assertEqual(await self.controller.visible_frequency_for("wsjtx"), 145_950_000)
        await self.controller.set_ptt(False, role="wsjtx", source="T 0")
        self.assertEqual(await self.controller.visible_frequency_for("wsjtx"), 435_000_000)

    async def test_split_cannot_be_disabled(self) -> None:
        with self.assertRaises(ValueError):
            await self.controller.set_split_enabled(False, role="satellite", source="S 0")
