from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer. Received: {value!r}"
        ) from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a number. Received: {value!r}"
        ) from exc


@dataclass(frozen=True)
class Settings:
    broker_mode: str
    trading_enabled: bool

    allowed_source: str
    allowed_symbol: str
    allowed_timeframe: str

    max_contracts: int
    daily_loss_limit: float

    tradovate_env: str
    tradovate_username: str
    tradovate_api_password: str
    tradovate_cid: str
    tradovate_sec: str
    tradovate_app_id: str
    tradovate_app_version: str

    @classmethod
    def from_env(cls) -> "Settings":
        broker_mode = os.getenv(
            "BROKER_MODE",
            "mock",
        ).strip().lower()

        if broker_mode not in {
            "mock",
            "tradovate",
        }:
            raise ValueError(
                "BROKER_MODE must be 'mock' or 'tradovate'."
            )

        tradovate_env = os.getenv(
            "TRADOVATE_ENV",
            "demo",
        ).strip().lower()

        if tradovate_env not in {
            "demo",
            "live",
        }:
            raise ValueError(
                "TRADOVATE_ENV must be 'demo' or 'live'."
            )

        max_contracts = _get_int(
            "MAX_CONTRACTS",
            1,
        )

        if max_contracts < 1:
            raise ValueError(
                "MAX_CONTRACTS must be at least 1."
            )

        daily_loss_limit = _get_float(
            "DAILY_LOSS_LIMIT",
            100.0,
        )

        if daily_loss_limit <= 0:
            raise ValueError(
                "DAILY_LOSS_LIMIT must be greater than zero."
            )

        return cls(
            broker_mode=broker_mode,
            trading_enabled=_get_bool(
                "TRADING_ENABLED",
                False,
            ),
            allowed_source=os.getenv(
                "ALLOWED_SOURCE",
                "Greedy Futures Strategy",
            ).strip(),
            allowed_symbol=os.getenv(
                "ALLOWED_SYMBOL",
                "MNQ1!",
            ).strip(),
            allowed_timeframe=os.getenv(
                "ALLOWED_TIMEFRAME",
                "15",
            ).strip(),
            max_contracts=max_contracts,
            daily_loss_limit=daily_loss_limit,
            tradovate_env=tradovate_env,
            tradovate_username=os.getenv(
                "TRADOVATE_USERNAME",
                "",
            ).strip(),
            tradovate_api_password=os.getenv(
                "TRADOVATE_API_PASSWORD",
                "",
            ).strip(),
            tradovate_cid=os.getenv(
                "TRADOVATE_CID",
                "",
            ).strip(),
            tradovate_sec=os.getenv(
                "TRADOVATE_SEC",
                "",
            ).strip(),
            tradovate_app_id=os.getenv(
                "TRADOVATE_APP_ID",
                "GreedyBot",
            ).strip(),
            tradovate_app_version=os.getenv(
                "TRADOVATE_APP_VERSION",
                "1.0",
            ).strip(),
        )

    def tradovate_credentials_configured(self) -> bool:
        return all(
            [
                self.tradovate_username,
                self.tradovate_api_password,
                self.tradovate_cid,
                self.tradovate_sec,
            ]
        )


settings = Settings.from_env()