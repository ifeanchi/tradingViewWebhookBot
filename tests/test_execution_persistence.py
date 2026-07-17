from pathlib import Path

import pytest

from broker.mock import MockBroker
from config import settings
from models.signal_models import NormalizedSignal
from repository import ExecutionRepository
from risk_engine import RiskEngine
from services.execution_service import ExecutionService


@pytest.mark.asyncio
async def test_long_and_close_are_persisted(
    tmp_path: Path,
) -> None:
    repository = ExecutionRepository(
        database_path=(
            tmp_path / "execution_test.db"
        )
    )

    broker = MockBroker()
    risk_engine = RiskEngine(settings)

    service = ExecutionService(
        broker=broker,
        risk_engine=risk_engine,
        repository=repository,
    )

    await service.initialize()

    long_signal = NormalizedSignal.from_dict(
        {
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "timeframe": "15",
            "price": 22000.00,
            "timestamp": (
                "2026-07-17T14:00:00Z"
            ),
            "order_id": "entry-001",
            "order_comment": "LONG ENTRY",
        }
    )

    close_signal = NormalizedSignal.from_dict(
        {
            "source": "Greedy Futures Strategy",
            "action": "CLOSE_ALL",
            "symbol": "MNQ1!",
            "timeframe": "15",
            "price": 22020.00,
            "timestamp": (
                "2026-07-17T14:15:00Z"
            ),
            "order_id": "exit-001",
            "order_comment": "CLOSE LONG",
        }
    )

    long_result = await service.execute_signal(
        signal=long_signal,
        execution_enabled=True,
    )

    close_result = await service.execute_signal(
        signal=close_signal,
        execution_enabled=True,
    )

    assert long_result.status == "filled"
    assert close_result.status == "filled"

    orders = repository.list_orders(
        symbol="MNQ1!",
        limit=20,
    )

    fills = repository.list_fills(
        symbol="MNQ1!",
        limit=20,
    )

    risk_events = (
        repository.list_risk_events(
            limit=20
        )
    )

    audit_events = (
        repository.list_audit_events(
            limit=50
        )
    )

    position = repository.get_position(
        "MNQ1!"
    )

    assert len(orders) == 2
    assert len(fills) == 2
    assert len(risk_events) == 2

    assert position is not None
    assert position["status"] == "CLOSED"
    assert position["side"] == "FLAT"
    assert position["quantity"] == 0

    order_actions = {
        order["action"]
        for order in orders
    }

    assert order_actions == {
        "LONG",
        "CLOSE_ALL",
    }

    assert all(
        order["status"] == "FILLED"
        for order in orders
    )

    risk_decisions = {
        event["decision"]
        for event in risk_events
    }

    assert risk_decisions == {
        "APPROVED"
    }

    audit_types = {
        event["event_type"]
        for event in audit_events
    }

    assert {
        "SIGNAL_RECEIVED",
        "RISK_APPROVED",
        "ORDER_CREATED",
        "ORDER_SUBMITTED",
        "ORDER_FILLED",
        "POSITION_OPENED",
        "POSITION_CLOSED",
    }.issubset(audit_types)

    summary = repository.get_summary()

    assert summary["orders"] == 2
    assert summary["fills"] == 2
    assert summary["risk_events"] == 2
    assert summary["open_positions"] == 0
    assert summary["rejected_risk_events"] == 0


@pytest.mark.asyncio
async def test_rejected_signal_is_persisted(
    tmp_path: Path,
) -> None:
    repository = ExecutionRepository(
        database_path=(
            tmp_path / "execution_test.db"
        )
    )

    broker = MockBroker()
    risk_engine = RiskEngine(settings)

    service = ExecutionService(
        broker=broker,
        risk_engine=risk_engine,
        repository=repository,
    )

    await service.initialize()

    invalid_signal = NormalizedSignal.from_dict(
        {
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "timeframe": "1",
            "price": 22000.00,
            "timestamp": (
                "2026-07-17T14:00:00Z"
            ),
            "order_id": "invalid-001",
            "order_comment": "INVALID TF",
        }
    )

    result = await service.execute_signal(
        signal=invalid_signal,
        execution_enabled=True,
    )

    assert result.status == "rejected"
    assert (
        result.risk_code
        == "TIMEFRAME_NOT_ALLOWED"
    )

    orders = repository.list_orders()
    fills = repository.list_fills()

    rejected_events = (
        repository.list_risk_events(
            decision="REJECTED"
        )
    )

    audit_events = (
        repository.list_audit_events()
    )

    assert orders == []
    assert fills == []
    assert len(rejected_events) == 1

    rejected_event = rejected_events[0]

    assert (
        rejected_event["risk_code"]
        == "TIMEFRAME_NOT_ALLOWED"
    )

    audit_types = {
        event["event_type"]
        for event in audit_events
    }

    assert "SIGNAL_RECEIVED" in audit_types
    assert "RISK_REJECTED" in audit_types
    assert "ORDER_CREATED" not in audit_types

    summary = repository.get_summary()

    assert summary["orders"] == 0
    assert summary["fills"] == 0
    assert summary["risk_events"] == 1
    assert summary["rejected_risk_events"] == 1