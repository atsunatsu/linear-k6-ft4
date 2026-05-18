from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AdapterFeedback:
    status: str = "ok"
    detail: str = ""

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    @classmethod
    def ok(cls, detail: str = "") -> "AdapterFeedback":
        return cls("ok", detail)

    @classmethod
    def congested(cls, detail: str = "") -> "AdapterFeedback":
        return cls("congested", detail)

    @classmethod
    def timeout(cls, detail: str = "") -> "AdapterFeedback":
        return cls("timeout", detail)

    @classmethod
    def failed(cls, detail: str = "") -> "AdapterFeedback":
        return cls("failed", detail)


@dataclass(slots=True)
class BridgeSnapshot:
    rx_frequency_hz: int
    tx_frequency_hz: int
    radio_frequency_hz: int
    mode: str
    ptt: bool = False
    split_enabled: bool = True
    pending_target_tx_hz: int | None = None
    last_applied_tx_hz: int | None = None
    last_apply_monotonic: float = 0.0
    retune_mode: str = "immediate"
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_role: str = "bridge"
    last_source: str = "bootstrap"
