from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.adapters import RecordingAdapter
from sat_bridge.bridge import BridgeController
from sat_bridge.serial_frontend import MemoryByteStream, SerialRigctlFrontend


class SerialFrontendTests(unittest.IsolatedAsyncioTestCase):
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
        self.stream = MemoryByteStream()
        self.frontend = SerialRigctlFrontend(self.stream, self.controller)
        await self.frontend.start()

    async def asyncTearDown(self) -> None:
        await self.frontend.close()
        await self.controller.stop()

    async def test_frontend_reads_and_writes_rigctl_commands(self) -> None:
        self.stream.feed_peer_data(b"f\n")
        await asyncio.sleep(0.05)
        self.assertEqual(self.stream.take_written().decode(), "435000000\n")

    async def test_frontend_handles_ptt_and_ignores_wsjtx_frequency_authority(self) -> None:
        self.stream.feed_peer_data(b"F 999\nT 1\nt\n")
        await asyncio.sleep(0.05)
        output = self.stream.take_written().decode()
        self.assertEqual(output, "RPRT 0\nRPRT 0\n1\n")

        snapshot = await self.controller.snapshot()
        self.assertEqual(snapshot.rx_frequency_hz, 435_000_000)
        self.assertTrue(snapshot.ptt)
