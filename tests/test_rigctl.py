from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.adapters import RecordingAdapter
from sat_bridge.bridge import BridgeController
from sat_bridge.rigctl import RigctlServer, ServerRole


class RigctlServerTests(unittest.IsolatedAsyncioTestCase):
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
        self.server = RigctlServer(
            role=ServerRole.SATELLITE,
            bind_host="127.0.0.1",
            bind_port=0,
            controller=self.controller,
        )
        await self.server.start()
        sockets = self.server._server.sockets  # type: ignore[union-attr]
        self.port = sockets[0].getsockname()[1]
        self.server_task = asyncio.create_task(self.server.serve_forever())
        await asyncio.sleep(0)

    async def asyncTearDown(self) -> None:
        await self.server.close()
        self.server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.server_task
        await self.controller.stop()

    async def test_satellite_port_updates_split_frequencies(self) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"I 435123000\n")
        await writer.drain()
        self.assertEqual((await reader.readline()).decode().strip(), "RPRT 0")

        writer.write(b"X 145955000\n")
        await writer.drain()
        self.assertEqual((await reader.readline()).decode().strip(), "RPRT 0")

        writer.write(b"i\nx\n")
        await writer.drain()
        self.assertEqual((await reader.readline()).decode().strip(), "435123000")
        self.assertEqual((await reader.readline()).decode().strip(), "145955000")
        writer.close()
        await writer.wait_closed()

    async def test_wsjtx_port_ignores_frequency_writes_but_handles_ptt(self) -> None:
        wsjtx_server = RigctlServer(
            role=ServerRole.WSJTX,
            bind_host="127.0.0.1",
            bind_port=0,
            controller=self.controller,
        )
        await wsjtx_server.start()
        sockets = wsjtx_server._server.sockets  # type: ignore[union-attr]
        port = sockets[0].getsockname()[1]
        wsjtx_task = asyncio.create_task(wsjtx_server.serve_forever())
        await asyncio.sleep(0)

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(b"F 999\n")
            writer.write(b"T 1\n")
            writer.write(b"t\n")
            await writer.drain()

            self.assertEqual((await reader.readline()).decode().strip(), "RPRT 0")
            self.assertEqual((await reader.readline()).decode().strip(), "RPRT 0")
            self.assertEqual((await reader.readline()).decode().strip(), "1")

            snapshot = await self.controller.snapshot()
            self.assertEqual(snapshot.rx_frequency_hz, 435_000_000)
            self.assertTrue(snapshot.ptt)
            writer.close()
            await writer.wait_closed()
        finally:
            await wsjtx_server.close()
            wsjtx_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await wsjtx_task
