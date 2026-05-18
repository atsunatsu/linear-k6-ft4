from __future__ import annotations

import asyncio
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.capture import JsonlCaptureWriter, MemoryByteStream, SerialCaptureProxy


class CaptureProxyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.wsjtx = MemoryByteStream()
        self.digimanager = MemoryByteStream()
        self.buffer = StringIO()
        self.writer = JsonlCaptureWriter(self.buffer)
        self.proxy = SerialCaptureProxy(
            wsjtx_stream=self.wsjtx,
            digimanager_stream=self.digimanager,
            writer=self.writer,
            scenario="ptt_on",
            wsjtx_port_name="COM_A",
            digimanager_port_name="COM_B",
        )
        await self.proxy.start()

    async def asyncTearDown(self) -> None:
        await self.proxy.close()

    async def test_proxy_forwards_and_logs_wsjtx_direction(self) -> None:
        self.wsjtx.feed(b"F 145950000\n")
        await asyncio.sleep(0.05)

        self.assertEqual(self.digimanager.take_written(), b"F 145950000\n")
        record = json.loads(self.buffer.getvalue().splitlines()[0])
        self.assertEqual(record["direction"], "WSJT-X->DigiManager")
        self.assertEqual(record["bytes_ascii"], "F 145950000\\n")
        self.assertEqual(record["scenario"], "ptt_on")
        self.assertEqual(record["port_name"], "COM_A")

    async def test_proxy_forwards_and_logs_reverse_direction(self) -> None:
        self.digimanager.feed(b"RPRT 0\n")
        await asyncio.sleep(0.05)

        self.assertEqual(self.wsjtx.take_written(), b"RPRT 0\n")
        record = json.loads(self.buffer.getvalue().splitlines()[0])
        self.assertEqual(record["direction"], "DigiManager->WSJT-X")
        self.assertEqual(record["bytes_ascii"], "RPRT 0\\n")
        self.assertEqual(record["port_name"], "COM_B")
