from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from broker_app import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    Starts and stops the FastAPI application lifecycle
    for every test.

    This ensures broker_app startup initializes the
    ExecutionService before endpoints are called.
    """
    with TestClient(app) as test_client:
        yield test_client


def test_broker_health(
    client: TestClient,
) -> None:
    response = client.get("/broker/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["broker"] == "mock"
    assert data["allowed_symbol"] == "MNQ1!"
    assert data["allowed_timeframe"] == "15"


def test_trading_disabled_by_default(
    client: TestClient,
) -> None:
    # Reset state so this test does not depend on another test.
    reset_response = client.post("/broker/reset")
    assert reset_response.status_code == 200

    response = client.post(
        "/broker/test-signal",
        json={
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "timeframe": "15",
            "price": 30000,
            "timestamp": "2026-07-15T15:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["risk_code"] == "TRADING_DISABLED"
    assert data["fill"] is None


def test_long_and_close_flow(
    client: TestClient,
) -> None:
    reset_response = client.post("/broker/reset")
    assert reset_response.status_code == 200

    entry_response = client.post(
        "/broker/test-signal",
        params={
            "execution_enabled": "true",
        },
        json={
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "timeframe": "15",
            "price": 30000,
            "timestamp": "2026-07-15T15:00:00Z",
        },
    )

    assert entry_response.status_code == 200

    entry_data = entry_response.json()

    assert entry_data["status"] == "filled"
    assert entry_data["risk_code"] == "APPROVED_ENTRY"
    assert entry_data["fill"] is not None
    assert entry_data["fill"]["side"] == "BUY"
    assert entry_data["fill"]["quantity"] == 1
    assert entry_data["fill"]["fill_price"] == 30000

    position_response = client.get(
        "/broker/positions"
    )

    assert position_response.status_code == 200

    positions = position_response.json()[
        "positions"
    ]

    assert len(positions) == 1
    assert positions[0]["symbol"] == "MNQ1!"
    assert positions[0]["side"] == "LONG"
    assert positions[0]["quantity"] == 1
    assert positions[0]["average_price"] == 30000

    close_response = client.post(
        "/broker/test-signal",
        params={
            "execution_enabled": "true",
        },
        json={
            "source": "Greedy Futures Strategy",
            "action": "CLOSE_ALL",
            "symbol": "MNQ1!",
            "timeframe": "15",
            "price": 30020,
            "timestamp": "2026-07-15T15:15:00Z",
            "order_id": "Trail Long",
            "order_comment": "Trail Long",
        },
    )

    assert close_response.status_code == 200

    close_data = close_response.json()

    assert close_data["status"] == "filled"
    assert close_data["risk_code"] == "APPROVED_CLOSE"
    assert close_data["fill"] is not None
    assert close_data["fill"]["side"] == "SELL"
    assert close_data["fill"]["fill_price"] == 30020

    position_response = client.get(
        "/broker/positions"
    )

    assert position_response.status_code == 200
    assert (
        position_response.json()["positions"]
        == []
    )