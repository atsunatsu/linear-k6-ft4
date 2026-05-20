from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass(slots=True)
class BridgeConfig:
    mode: str
    rx_frequency_hz: int
    tx_frequency_hz: int
    adapter_timeout_seconds: float
    tx_min_step_hz: int
    tx_rate_limit_hz: float
    tx_rate_limit_window_ms: int


@dataclass(slots=True)
class ServerConfig:
    host: str
    port: int


@dataclass(slots=True)
class HookCommands:
    set_rx_frequency: list[str] = field(default_factory=list)
    set_tx_frequency: list[str] = field(default_factory=list)
    set_radio_frequency: list[str] = field(default_factory=list)
    set_mode: list[str] = field(default_factory=list)
    set_ptt: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SerialFrontendConfig:
    enabled: bool
    port: str
    baudrate: int
    read_timeout_seconds: float
    read_chunk_size: int


@dataclass(slots=True)
class SerialCommandTemplates:
    set_rx_frequency: str | None = None
    set_tx_frequency: str | None = None
    set_radio_frequency: str | None = None
    set_mode: str | None = None
    set_ptt: str | None = None


@dataclass(slots=True)
class SerialBackendConfig:
    enabled: bool
    port: str
    baudrate: int
    read_timeout_seconds: float
    write_timeout_seconds: float
    response_timeout_seconds: float
    command_terminator: str
    response_terminator: str
    expect_response: bool
    protocol: str
    commands: SerialCommandTemplates


@dataclass(slots=True)
class AdapterConfig:
    kind: str
    commands: HookCommands


@dataclass(slots=True)
class Ft4CleanTxCommands:
    set_tx_frequency: list[str] = field(default_factory=list)
    set_ptt: list[str] = field(default_factory=list)
    send_packet: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Ft4CleanTxConfig:
    enabled: bool
    template_path: str
    default_payload: str
    transmission_index: int
    timing_mode: str
    transport: str
    destination_host: str
    destination_port: int
    command_timeout_seconds: float
    tx_min_step_hz: int
    tx_rate_limit_hz: float
    tx_rate_limit_window_ms: int
    commands: Ft4CleanTxCommands


@dataclass(slots=True)
class AppConfig:
    bridge: BridgeConfig
    satellite_server: ServerConfig
    wsjtx_server: ServerConfig
    adapter: AdapterConfig
    wsjtx_serial_frontend: SerialFrontendConfig
    digimanager_serial_backend: SerialBackendConfig
    ft4_clean_tx: Ft4CleanTxConfig


def load_config(path: str | Path) -> AppConfig:
    file_path = Path(path)
    with file_path.open("rb") as handle:
        raw = tomllib.load(handle)

    bridge = raw.get("bridge", {})
    satellite_server = raw.get("satellite_server", {})
    wsjtx_server = raw.get("wsjtx_server", {})
    adapter = raw.get("adapter", {})
    commands = raw.get("adapter", {}).get("commands", {})
    frontend = raw.get("wsjtx_serial_frontend", {})
    backend = raw.get("digimanager_serial_backend", {})
    backend_commands = backend.get("commands", {})
    ft4_clean_tx = raw.get("ft4_clean_tx", {})
    ft4_commands = ft4_clean_tx.get("commands", {})

    return AppConfig(
        bridge=BridgeConfig(
            mode=str(bridge.get("mode", "FT4")).upper(),
            rx_frequency_hz=int(bridge.get("rx_frequency_hz", 435_000_000)),
            tx_frequency_hz=int(bridge.get("tx_frequency_hz", 145_950_000)),
            adapter_timeout_seconds=float(bridge.get("adapter_timeout_seconds", 5.0)),
            tx_min_step_hz=int(bridge.get("tx_min_step_hz", 10)),
            tx_rate_limit_hz=float(bridge.get("tx_rate_limit_hz", 5.0)),
            tx_rate_limit_window_ms=int(bridge.get("tx_rate_limit_window_ms", 200)),
        ),
        satellite_server=ServerConfig(
            host=str(satellite_server.get("host", "127.0.0.1")),
            port=int(satellite_server.get("port", 4533)),
        ),
        wsjtx_server=ServerConfig(
            host=str(wsjtx_server.get("host", "127.0.0.1")),
            port=int(wsjtx_server.get("port", 4534)),
        ),
        adapter=AdapterConfig(
            kind=str(adapter.get("kind", "null")).lower(),
            commands=HookCommands(
                set_rx_frequency=_read_command(commands.get("set_rx_frequency")),
                set_tx_frequency=_read_command(commands.get("set_tx_frequency")),
                set_radio_frequency=_read_command(commands.get("set_radio_frequency")),
                set_mode=_read_command(commands.get("set_mode")),
                set_ptt=_read_command(commands.get("set_ptt")),
            ),
        ),
        wsjtx_serial_frontend=SerialFrontendConfig(
            enabled=bool(frontend.get("enabled", False)),
            port=str(frontend.get("port", "COM11")),
            baudrate=int(frontend.get("baudrate", 9600)),
            read_timeout_seconds=float(frontend.get("read_timeout_seconds", 0.1)),
            read_chunk_size=int(frontend.get("read_chunk_size", 256)),
        ),
        digimanager_serial_backend=SerialBackendConfig(
            enabled=bool(backend.get("enabled", False)),
            port=str(backend.get("port", "COM12")),
            baudrate=int(backend.get("baudrate", 9600)),
            read_timeout_seconds=float(backend.get("read_timeout_seconds", 0.1)),
            write_timeout_seconds=float(backend.get("write_timeout_seconds", 0.5)),
            response_timeout_seconds=float(backend.get("response_timeout_seconds", 0.3)),
            command_terminator=str(backend.get("command_terminator", "\n")),
            response_terminator=str(backend.get("response_terminator", "\n")),
            expect_response=bool(backend.get("expect_response", False)),
            protocol=str(backend.get("protocol", "rigctl")).lower(),
            commands=SerialCommandTemplates(
                set_rx_frequency=_read_template(backend_commands.get("set_rx_frequency")),
                set_tx_frequency=_read_template(backend_commands.get("set_tx_frequency")),
                set_radio_frequency=_read_template(backend_commands.get("set_radio_frequency")),
                set_mode=_read_template(backend_commands.get("set_mode")),
                set_ptt=_read_template(backend_commands.get("set_ptt")),
            ),
        ),
        ft4_clean_tx=Ft4CleanTxConfig(
            enabled=bool(ft4_clean_tx.get("enabled", True)),
            template_path=str(ft4_clean_tx.get("template_path", "samples/replay/ft4-replay.json")),
            default_payload=str(ft4_clean_tx.get("default_payload", "CQ FT4 BENCH OO00")),
            transmission_index=int(ft4_clean_tx.get("transmission_index", 0)),
            timing_mode=str(ft4_clean_tx.get("timing_mode", "fast_replay")).lower(),
            transport=str(ft4_clean_tx.get("transport", "udp")).lower(),
            destination_host=str(ft4_clean_tx.get("destination_host", "127.0.0.1")),
            destination_port=int(ft4_clean_tx.get("destination_port", 5957)),
            command_timeout_seconds=float(ft4_clean_tx.get("command_timeout_seconds", 5.0)),
            tx_min_step_hz=int(ft4_clean_tx.get("tx_min_step_hz", bridge.get("tx_min_step_hz", 10))),
            tx_rate_limit_hz=float(ft4_clean_tx.get("tx_rate_limit_hz", bridge.get("tx_rate_limit_hz", 5.0))),
            tx_rate_limit_window_ms=int(
                ft4_clean_tx.get("tx_rate_limit_window_ms", bridge.get("tx_rate_limit_window_ms", 200))
            ),
            commands=Ft4CleanTxCommands(
                set_tx_frequency=_read_command(ft4_commands.get("set_tx_frequency")),
                set_ptt=_read_command(ft4_commands.get("set_ptt")),
                send_packet=_read_command(ft4_commands.get("send_packet")),
            ),
        ),
    )


def _read_command(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    raise TypeError(f"Adapter commands must be arrays of strings, got {type(value)!r}")


def _read_template(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
