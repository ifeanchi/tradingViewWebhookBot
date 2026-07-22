from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import pytest

from config import Settings
from models.signal_models import NormalizedSignal
from broker.base import BrokerPosition


def build_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "broker_mode": "mock",
        "tradovate_env": "demo",
        "tradovate_username": "unit-test-user",
        "tradovate_api_password": "unit-test-password",
        "tradovate_cid": "unit-test-cid",
        "tradovate_sec": "unit-test-secret",
        "tradovate_app_id": "GTAP-TEST",
        "tradovate_app_version": "1.0",
        "trading_enabled": True,
        "allowed_source": "TV",
        "allowed_symbol": "MNQ",
        "allowed_timeframe": "5m",
        "daily_loss_limit": 500.0,
        "max_contracts": 5,
    }

    values.update(overrides)

    return Settings(**values)


@pytest.fixture
def make_settings() -> Callable[..., Settings]:
    return build_settings


@pytest.fixture
def settings(
    make_settings: Callable[..., Settings],
) -> Settings:
    return make_settings()

@pytest.fixture
def long_signal():
    return NormalizedSignal(
        source="TV",
        symbol="MNQ",
        timeframe="5m",
        action="LONG",
        price=18000.25,
        timestamp=datetime.now(timezone.utc),
    )

@pytest.fixture
def short_signal():
    return NormalizedSignal(
        source="TV",
        symbol="MNQ",
        timeframe="5m",
        action="SHORT",
        price=18000.25,
        timestamp=datetime.now(timezone.utc),
    )

from broker.base import BrokerPosition


@pytest.fixture
def long_position():
    return BrokerPosition(
        account_id="TEST_ACCOUNT",
        symbol="MNQ",
        average_price=18000.25,
        side="LONG",
        quantity=1,
    )

@pytest.fixture
def short_position():
    return BrokerPosition(
        account_id="TEST_ACCOUNT",
        symbol="MNQ",
        average_price=18000.25,
        side="SHORT",
        quantity=1,
    )