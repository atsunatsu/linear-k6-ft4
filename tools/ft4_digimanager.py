#!/usr/bin/env python3
"""
FT4 DigiManager - Custom serial bridge for UV-K5 FT4 firmware.

Flow: WSJT-X -> UDP:5957 -> this script -> serial -> UV-K5 (0x0701)

Usage:
  python ft4_digimanager.py --port COM3
  python ft4_digimanager.py --port /dev/ttyUSB0 -v

Prerequisites:
  1. Flash ft4-firmware-packed-v3.bin
  2. Menu -> DataMd -> ON
  3. Long-press M -> FT8 STANDBY
  4. WSJT-X UDP output to localhost:5957
"""

from __future__ import annotations

import argparse
import binascii
import logging
import socket
import struct
import sys
import time

LOGGER = logging.getLogger("ft4-dm")

# CEC UART Protocol
HDR = 0xCDAB
FTR = 0xBADC
CMD_HELLO = 0x0514
CMD_START = 0x0701
CMD_FREQ = 0x0703
CMD_STOP = 0x0705
REP_VER = 0x0515

STATUS = {0: "OK", 1: "BUSY", 2: "NOT_ACTIVE", 3: "TX_NOT_READY", 4: "PAYLOAD_TOO_LONG"}


def crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0)


def build_frame(cid: int, body: bytes) -> bytes:
    inner = struct.pack("<HH", cid, len(body)) + body
    c = crc16(inner)
    return (
        struct.pack("<HH", HDR, len(inner))
        + inner
        + struct.pack("<H", c)
        + struct.pack("<HH", 0xFFFF, FTR)
    )


def rd(ser, n: int) -> bytes:
    d = ser.read(n)
    if not d or len(d) < n:
        raise TimeoutError("read %d bytes" % n)
    return d


def read_frame(ser) -> bytes:
    h = rd(ser, 4)
    oid, sz = struct.unpack("<HH", h)
    if oid != HDR:
        raise ValueError("bad hdr 0x%04x" % oid)
    pay = rd(ser, sz)
    rd(ser, 2)  # crc
    f = rd(ser, 4)
    _, fid = struct.unpack("<HH", f)
    if fid != FTR:
        raise ValueError("bad ftr 0x%04x" % fid)
    return pay


class Radio:
    def __init__(self, port: str, baud: int = 38400, timeout: float = 3.0):
        import serial
        self.s = serial.Serial(
            port=port, baudrate=baud, timeout=timeout, write_timeout=timeout
        )
        self.ts = 0

    def close(self):
        if self.s:
            self.s.close()
            self.s = None

    def hello(self) -> str:
        self.ts = int(time.time()) & 0xFFFFFFFF
        self.s.write(build_frame(CMD_HELLO, struct.pack("<I", self.ts)))
        self.s.flush()
        r = read_frame(self.s)
        rid, dsz = struct.unpack("<HH", r[:4])
        if rid == REP_VER and len(r) >= 4 + 16:
            return r[4 : 4 + 16].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        return "?"

    def start_tx(self, tones, freq: int) -> dict:
        if len(tones) > 64:
            tones = tones[:64]
        body = struct.pack("<IIB3x", self.ts, freq, len(tones)) + bytes(tones)
        self.s.write(build_frame(CMD_START, body))
        self.s.flush()
        return self._parse_reply(read_frame(self.s))

    def stop_tx(self) -> dict:
        self.s.write(build_frame(CMD_STOP, struct.pack("<I", self.ts)))
        self.s.flush()
        return self._parse_reply(read_frame(self.s))

    def _parse_reply(self, r: bytes) -> dict:
        if len(r) < 4:
            return {"error": "short"}
        rid, dsz = struct.unpack("<HH", r[:4])
        if dsz >= 20 and len(r) >= 24:
            d = r[4:24]
            st, act, rm, _ = struct.unpack("<BBBB", d[:4])
            cf, lf, pf = struct.unpack("<III", d[4:16])
            fs, fq = struct.unpack("<HH", d[16:20])
            return {
                "status": STATUS.get(st, str(st)),
                "active": bool(act),
                "freq": cf,
                "frames": fs,
            }
        return {"rid": "0x%04x" % rid}


def parse_udp(data: bytes):
    if len(data) < 8 or data[0] != 0x59 or data[1] != 0x57:
        return None
    if data[2] != 0x04:
        return None
    freq = struct.unpack_from("<I", data, 4)[0]
    tones = list(data[8:])
    if not tones or any(t > 3 for t in tones):
        return None
    return tones, freq


def main():
    ap = argparse.ArgumentParser(description="FT4 DigiManager for UV-K5")
    ap.add_argument("--port", required=True, help="Serial port (COM3, /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=38400, help="Baudrate (default 38400)")
    ap.add_argument("--freq", type=int, default=14074000, help="Default TX freq Hz")
    ap.add_argument("--udp-port", type=int, default=5957, help="UDP port (default 5957)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    LOGGER.info("Connecting to %s ...", a.port)
    try:
        r = Radio(a.port, a.baud)
    except Exception as e:
        LOGGER.error("Serial failed: %s", e)
        sys.exit(1)

    LOGGER.info("Bootstrapping session...")
    try:
        ver = r.hello()
        LOGGER.info("Firmware: %s, timestamp=%d", ver, r.ts)
    except Exception as e:
        LOGGER.error("Bootstrap failed: %s", e)
        r.close()
        sys.exit(1)

    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.settimeout(1.0)
    try:
        sk.bind(("127.0.0.1", a.udp_port))
    except OSError as e:
        LOGGER.error("UDP bind failed: %s", e)
        r.close()
        sys.exit(1)

    LOGGER.info("=" * 50)
    LOGGER.info("FT4 DigiManager Ready!")
    LOGGER.info("UDP: 127.0.0.1:%d  Default freq: %d Hz", a.udp_port, a.freq)
    LOGGER.info("Waiting for WSJT-X FT4 data...")
    LOGGER.info("Press Ctrl+C to quit")
    LOGGER.info("=" * 50)

    active = False
    try:
        while True:
            try:
                data, _ = sk.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            result = parse_udp(data)
            if not result:
                continue

            tones, pf = result
            freq = pf if 1_000_000 <= pf <= 100_000_000 else a.freq
            LOGGER.info("FT4: %d tones, %d Hz", len(tones), freq)

            if active:
                try:
                    r.stop_tx()
                except Exception:
                    pass
                active = False

            try:
                rep = r.start_tx(tones, freq)
                st = rep.get("status", "?")
                LOGGER.info("TX: %s", st)
                if st == "OK":
                    active = True
                elif st == "TX_NOT_READY":
                    LOGGER.warning("Radio not ready! DataMd=ON? Long-press M?")
                elif st == "BUSY":
                    LOGGER.warning("Radio busy")
            except Exception as e:
                LOGGER.error("TX failed: %s", e)

    except KeyboardInterrupt:
        pass
    finally:
        if active:
            try:
                r.stop_tx()
            except Exception:
                pass
        sk.close()
        r.close()
        LOGGER.info("Bye.")


if __name__ == "__main__":
    main()
