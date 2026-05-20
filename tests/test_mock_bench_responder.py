from __future__ import annotations

import importlib.util
from pathlib import Path
from threading import Lock, Thread
import unittest

from sat_bridge.uvk5cec_uart import FT4TX_STATUS_OK, Uvk5CecSerialClient


ROOT = Path(__file__).resolve().parents[1]
RESPONDER_PATH = ROOT / "scripts" / "mock_uvk5cec_ft4_responder.py"


def _load_responder_module():
    spec = importlib.util.spec_from_file_location("mock_uvk5cec_ft4_responder", RESPONDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load mock responder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MockBenchResponderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import serial  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("pyserial is not installed")

        module = _load_responder_module()
        cls._module = module
        cls._server = module.MockResponderServer(("127.0.0.1", 0), module.MockState(lock=Lock(), version="TESTMOCK"))
        cls._thread = Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        cls._port = cls._server.server_address[1]

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "_server"):
            cls._server.shutdown()
            cls._server.server_close()
        if hasattr(cls, "_thread"):
            cls._thread.join(timeout=2)

    def test_client_can_run_full_offline_session_against_mock_responder(self) -> None:
        timestamp = 0x12345678
        port = f"socket://127.0.0.1:{self._port}"

        with Uvk5CecSerialClient(port, timeout_seconds=2.0) as client:
            version = client.bootstrap(timestamp)
            config = client.configure_session(timestamp)
            start = client.start_ft4_tx(timestamp, 145950000, "CQ TEST OO00")
            retune = client.update_tx_frequency(timestamp, 145950100)
            stop = client.stop_tx(timestamp)

        self.assertEqual(version.version, "TESTMOCK")
        self.assertEqual(config.version, "TESTMOCK")
        self.assertEqual(start.status, FT4TX_STATUS_OK)
        self.assertTrue(start.active)
        self.assertEqual(start.current_tx_frequency_hz, 145950000)
        self.assertEqual(retune.status, FT4TX_STATUS_OK)
        self.assertEqual(retune.last_applied_tx_frequency_hz, 145950100)
        self.assertEqual(stop.status, FT4TX_STATUS_OK)
        self.assertFalse(stop.active)

