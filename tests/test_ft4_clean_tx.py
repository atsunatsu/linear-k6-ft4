from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.ft4_clean_tx import Ft4CleanTransmitter, Ft4ReplayTemplate, RecordingFt4Backend
from sat_bridge.models import AdapterFeedback
from sat_bridge.udp_capture_tools import ReplayPacket, ReplaySequence


def _make_sequence() -> ReplaySequence:
    marker_payload = (
        b"YW\x04\x00"
        + b"\x00" * 8
        + b"\x01" * 16
        + b"CQ PLACEHOLDER OO00".ljust(37, b" ")
        + b"\x00" * 12
        + b"JX"
    )
    business_payload = b"YW\xf4\x00" + (b"\x00" * 250) + b"JX"
    packets = [
        ReplayPacket(
            timestamp_offset_ms=0,
            dst_port=5957,
            payload_hex=business_payload.hex(" "),
            payload_len=len(business_payload),
            tag="business_packet",
            source_capture="unit-ft4.pcapng",
            mode="FT4",
        ),
        ReplayPacket(
            timestamp_offset_ms=20,
            dst_port=5957,
            payload_hex=marker_payload.hex(" "),
            payload_len=len(marker_payload),
            tag="ft4_mode_marker",
            source_capture="unit-ft4.pcapng",
            mode="FT4",
        ),
        ReplayPacket(
            timestamp_offset_ms=40,
            dst_port=5957,
            payload_hex=business_payload.hex(" "),
            payload_len=len(business_payload),
            tag="business_packet",
            source_capture="unit-ft4.pcapng",
            mode="FT4",
        ),
    ]
    return ReplaySequence(
        source_capture="unit-ft4.pcapng",
        mode="FT4",
        destination_host="127.0.0.1",
        destination_port=5957,
        packets=packets,
    )


class Ft4CleanTxTests(unittest.IsolatedAsyncioTestCase):
    def test_template_patches_ascii_payload_and_avoids_double_tx_window(self) -> None:
        template = Ft4ReplayTemplate.from_path("samples/replay/ft4-replay.json", transmission_index=0)
        rendered = template.build_transmission("CQ TEST OO00")

        self.assertEqual(len([packet for packet in rendered.packets if packet.tag == "ft4_mode_marker"]), 1)
        mode_packet = next(packet for packet in rendered.packets if packet.tag == "ft4_mode_marker")
        payload = bytes.fromhex(mode_packet.payload_hex)
        self.assertIn(b"CQ TEST OO00", payload)
        self.assertLess(len(rendered.packets), 68)

    async def test_transmitter_runs_single_sequence_and_turns_ptt_off(self) -> None:
        backend = RecordingFt4Backend()
        transmitter = Ft4CleanTransmitter(
            template=Ft4ReplayTemplate(_make_sequence()),
            backend=backend,
            tx_min_step_hz=10,
            tx_rate_limit_hz=5.0,
            tx_rate_limit_window_ms=20,
        )
        await transmitter.open()
        try:
            await transmitter.start_ft4_tx("CQ TEST OO00", 145_950_000)
            await transmitter.wait_for_idle()
        finally:
            await transmitter.close()

        self.assertEqual(backend.events[0], ("set_tx_frequency", 145_950_000))
        self.assertEqual(backend.events[1], ("set_ptt", True))
        self.assertEqual([action for action, _ in backend.events].count("send_packet"), 3)
        self.assertEqual(backend.events[-1], ("set_ptt", False))

    async def test_transmitter_keeps_latest_frequency_after_timeout(self) -> None:
        backend = RecordingFt4Backend()
        transmitter = Ft4CleanTransmitter(
            template=Ft4ReplayTemplate(_make_sequence()),
            backend=backend,
            tx_min_step_hz=10,
            tx_rate_limit_hz=5.0,
            tx_rate_limit_window_ms=20,
        )
        await transmitter.open()
        try:
            await transmitter.start_ft4_tx("CQ TEST OO00", 145_950_000)
            backend.push_feedback("set_tx_frequency", AdapterFeedback.timeout("simulated timeout"))
            await transmitter.update_tx_frequency(145_955_000)
            await transmitter.update_tx_frequency(145_956_000)
            await asyncio.sleep(0.05)
            await transmitter.wait_for_idle()
        finally:
            await transmitter.close()

        set_freq_events = [value for action, value in backend.events if action == "set_tx_frequency"]
        self.assertIn(145_956_000, set_freq_events)
        self.assertNotIn(145_955_000, set_freq_events[1:])
