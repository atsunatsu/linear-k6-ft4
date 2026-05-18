from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sat_bridge.udp_observe import parse_netstat_udp, parse_wsjtx_ini, render_text_report, UdpBinding, UdpObservation


class UdpObserveTests(unittest.TestCase):
    def test_parse_wsjtx_ini_extracts_relevant_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "WSJT-X.ini"
            path.write_text(
                "\n".join(
                    [
                        "[Configuration]",
                        "PTTMethod=VOX",
                        "Rig=None",
                        "UDPServerPort=2237",
                        "SendSymPort=5957",
                        "UnrelatedKey=ignore-me",
                    ]
                ),
                encoding="utf-8",
            )
            values = parse_wsjtx_ini(path)

        self.assertEqual(values["wsjtx_ptt_method"], "VOX")
        self.assertEqual(values["wsjtx_rig"], "None")
        self.assertEqual(values["wsjtx_udp_server_port"], "2237")
        self.assertEqual(values["wsjtx_send_sym_port"], "5957")
        self.assertNotIn("UnrelatedKey", values)

    def test_parse_netstat_udp_filters_interesting_ports(self) -> None:
        sample = "\n".join(
            [
                "  UDP    0.0.0.0:53             *:*                                    9856",
                "  UDP    0.0.0.0:4532           *:*                                    26008",
                "  UDP    127.0.0.1:5957         *:*                                    11111",
            ]
        )

        bindings = parse_netstat_udp(sample, {4532, 5957})

        self.assertEqual(
            bindings,
            [
                ("UDP", "0.0.0.0", 4532, 26008),
                ("UDP", "127.0.0.1", 5957, 11111),
            ],
        )

    def test_render_text_report_includes_ports_and_bindings(self) -> None:
        observation = UdpObservation(
            wsjtx_ini_path="C:/Users/test/AppData/Local/WSJT-X/WSJT-X.ini",
            wsjtx_ini_values={"wsjtx_udp_server_port": "2237", "wsjtx_send_sym_port": "5957"},
            interesting_ports=[2237, 4532, 5957],
            bindings=[UdpBinding(protocol="UDP", local_host="0.0.0.0", local_port=4532, pid=26008, process_name="wsjtx.exe")],
        )

        text = render_text_report(observation)

        self.assertIn("2237, 4532, 5957", text)
        self.assertIn("wsjtx_udp_server_port: 2237", text)
        self.assertIn("0.0.0.0:4532 pid=26008 process=wsjtx.exe", text)
