from __future__ import annotations

import argparse
import asyncio
import logging

from .adapters import DigiAdapter, HookAdapter, NullAdapter, SerialAdapter
from .bridge import BridgeController
from .config import AppConfig, load_config
from .rigctl import RigctlServer, ServerRole
from .serial_frontend import PySerialByteStream, SerialRigctlFrontend

LOGGER = logging.getLogger(__name__)


def build_adapter(config: AppConfig) -> DigiAdapter:
    if config.adapter.kind == "null":
        return NullAdapter()
    if config.adapter.kind == "hooks":
        return HookAdapter(
            config.adapter.commands,
            timeout_seconds=config.bridge.adapter_timeout_seconds,
        )
    if config.adapter.kind == "serial":
        return SerialAdapter(config.digimanager_serial_backend)
    raise ValueError(f"Unsupported adapter kind: {config.adapter.kind}")


async def run(config: AppConfig) -> None:
    adapter = build_adapter(config)
    controller = BridgeController(
        adapter=adapter,
        initial_rx_frequency_hz=config.bridge.rx_frequency_hz,
        initial_tx_frequency_hz=config.bridge.tx_frequency_hz,
        initial_mode=config.bridge.mode,
        tx_min_step_hz=config.bridge.tx_min_step_hz,
        tx_rate_limit_hz=config.bridge.tx_rate_limit_hz,
        tx_rate_limit_window_ms=config.bridge.tx_rate_limit_window_ms,
    )

    satellite_server = RigctlServer(
        role=ServerRole.SATELLITE,
        bind_host=config.satellite_server.host,
        bind_port=config.satellite_server.port,
        controller=controller,
    )
    wsjtx_server = RigctlServer(
        role=ServerRole.WSJTX,
        bind_host=config.wsjtx_server.host,
        bind_port=config.wsjtx_server.port,
        controller=controller,
    )
    serial_frontend = None
    if config.wsjtx_serial_frontend.enabled:
        serial_frontend = SerialRigctlFrontend(
            stream=PySerialByteStream(config.wsjtx_serial_frontend),
            controller=controller,
        )

    await adapter.open()
    try:
        await controller.start()
        await controller.initialize()
        await asyncio.gather(
            satellite_server.start(),
            wsjtx_server.start(),
        )
        if serial_frontend is not None:
            await serial_frontend.start()
        LOGGER.info(
            "sat-bridge running: satellite=%s:%s wsjtx=%s:%s",
            config.satellite_server.host,
            config.satellite_server.port,
            config.wsjtx_server.host,
            config.wsjtx_server.port,
        )
        tasks = [
            satellite_server.serve_forever(),
            wsjtx_server.serve_forever(),
        ]
        if serial_frontend is not None:
            tasks.append(serial_frontend.wait_closed())
        await asyncio.gather(*tasks)
    finally:
        await asyncio.gather(
            satellite_server.close(),
            wsjtx_server.close(),
            return_exceptions=True,
        )
        if serial_frontend is not None:
            await serial_frontend.close()
        await controller.stop()
        await adapter.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Linear-satellite split-control bridge for uvk5cec DigiManager.")
    parser.add_argument("--config", default="sat_bridge.example.toml", help="Path to bridge TOML config.")
    parser.add_argument("--log-level", default="INFO", help="Logging level.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    try:
        asyncio.run(run(config))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted, shutting down.")
    return 0
