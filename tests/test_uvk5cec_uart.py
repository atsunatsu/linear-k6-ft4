from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from sat_bridge.uvk5cec_uart import (
    Ft4BenchReply,
    OUTER_FOOTER_ID,
    OUTER_HEADER_ID,
    REPLY_START_FT4_TX,
    REPLY_VERSION,
    SessionContext,
    build_host_frame,
    build_reply_frame,
    build_start_ft4_tx,
    crc16_ccitt,
    load_session_context,
    parse_command_frame,
    parse_ft4_bench_reply,
    parse_version_reply,
    read_frame,
    render_ascii_payload,
    save_session_context,
)


class Uvk5CecUartTests(unittest.TestCase):
    def test_build_start_ft4_tx_keeps_ascii_payload_width(self) -> None:
        frame = build_start_ft4_tx(0x11223344, 145950000, "cq ft4 oo00")
        self.assertEqual(frame[:2], b"\xab\xcd")
        self.assertIn(b"CQ FT4 OO00", frame)
        parsed = parse_command_frame(read_frame(io.BytesIO(frame)))
        self.assertEqual(parsed.command_id, 0x0701)

    def test_read_frame_round_trip(self) -> None:
        inner = b"\x15\x05\x24\x00" + (b"VERSION\x00" + b"\x00" * 29)
        crc = crc16_ccitt(inner)
        raw = (
            OUTER_HEADER_ID.to_bytes(2, "little")
            + len(inner).to_bytes(2, "little")
            + inner
            + crc.to_bytes(2, "little")
            + (0xFFFF).to_bytes(2, "little")
            + OUTER_FOOTER_ID.to_bytes(2, "little")
        )
        parsed = read_frame(io.BytesIO(raw))
        self.assertEqual(parsed, inner + crc.to_bytes(2, "little"))

    def test_parse_version_reply(self) -> None:
        version_bytes = b"CEC_0.3q\x00".ljust(16, b"\x00")
        data = version_bytes + bytes([1, 0]) + b"\x00\x00" + (1).to_bytes(4, "little") * 4
        frame = struct_frame(REPLY_VERSION, data)
        reply = parse_version_reply(frame)
        self.assertEqual(reply.version, "CEC_0.3q")
        self.assertTrue(reply.has_custom_aes_key)
        self.assertFalse(reply.is_in_lock_screen)

    def test_parse_ft4_bench_reply(self) -> None:
        data = (
            bytes([0, 1, 0, 0])
            + (145950000).to_bytes(4, "little")
            + (145950000).to_bytes(4, "little")
            + (0).to_bytes(4, "little")
            + (3).to_bytes(2, "little")
            + (4).to_bytes(2, "little")
        )
        reply = parse_ft4_bench_reply(struct_frame(REPLY_START_FT4_TX, data))
        self.assertIsInstance(reply, Ft4BenchReply)
        self.assertEqual(reply.status, 0)
        self.assertTrue(reply.active)
        self.assertEqual(reply.frames_sent, 3)
        self.assertEqual(reply.frame_sequence, 4)

    def test_build_reply_frame_round_trip(self) -> None:
        raw = build_reply_frame(REPLY_START_FT4_TX, b"\x00" * 20)
        parsed = read_frame(io.BytesIO(raw))
        reply = parse_ft4_bench_reply(parsed)
        self.assertEqual(reply.reply_id, REPLY_START_FT4_TX)

    def test_session_context_round_trip(self) -> None:
        session = SessionContext(port="COM5", baudrate=38400, timestamp=123456)
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "session.json"
            save_session_context(target, session)
            loaded = load_session_context(target)
        self.assertEqual(loaded, session)

    def test_render_ascii_payload_normalizes_non_ascii(self) -> None:
        rendered = render_ascii_payload("cq 测试 oo00", 12)
        self.assertEqual(rendered, b"CQ    OO00  ")


def struct_frame(reply_id: int, data: bytes) -> bytes:
    return reply_id.to_bytes(2, "little") + len(data).to_bytes(2, "little") + data


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
