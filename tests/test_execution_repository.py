from pathlib import Path

import pytest

from repository.execution_repository import (
    ExecutionRepository,
)


@pytest.fixture
def repository(
    tmp_path: Path,
) -> ExecutionRepository:
    database_path = (
        tmp_path / "test_execution.db"
    )

    return ExecutionRepository(
        database_path=database_path
    )


def test_repository_creates_database(
    repository: ExecutionRepository,
) -> None:
    assert repository.database_path.exists()

    summary = repository.get_summary()

    assert summary["orders"] == 0
    assert summary["fills"] == 0
    assert summary["risk_events"] == 0
    assert summary["audit_events"] == 0
    assert summary["open_positions"] == 0


def test_create_and_fill_order(
    repository: ExecutionRepository,
) -> None:
    order = repository.create_order(
        signal_id="signal-001",
        broker_name="MOCK",
        source="Greedy Futures Strategy",
        symbol="MNQ1!",
        timeframe="15",
        action="LONG",
        side="BUY",
        quantity=1,
        requested_price=22000.25,
        status="APPROVED",
    )

    assert order["status"] == "APPROVED"
    assert order["quantity"] == 1
    assert order["symbol"] == "MNQ1!"

    fill = repository.create_fill(
        order_id=order["order_id"],
        symbol="MNQ1!",
        side="BUY",
        quantity=1,
        fill_price=22000.50,
        commission=2.50,
    )

    assert fill["order_id"] == order["order_id"]
    assert fill["fill_price"] == 22000.50

    updated_order = repository.get_order(
        order["order_id"]
    )

    assert updated_order is not None
    assert updated_order["status"] == "FILLED"

    summary = repository.get_summary()

    assert summary["orders"] == 1
    assert summary["fills"] == 1


def test_position_persists_and_closes(
    repository: ExecutionRepository,
) -> None:
    opened_position = (
        repository.upsert_position(
            symbol="MNQ1!",
            broker_name="MOCK",
            quantity=1,
            side="LONG",
            average_price=22000.50,
            status="OPEN",
            opened_at=(
                "2026-07-17T14:00:00+00:00"
            ),
        )
    )

    assert opened_position["status"] == "OPEN"
    assert opened_position["quantity"] == 1

    open_positions = (
        repository.list_positions(
            open_only=True
        )
    )

    assert len(open_positions) == 1

    closed_position = (
        repository.close_position(
            "MNQ1!",
            realized_pnl=40.0,
        )
    )

    assert closed_position["status"] == "CLOSED"
    assert closed_position["side"] == "FLAT"
    assert closed_position["quantity"] == 0
    assert closed_position["realized_pnl"] == 40.0

    assert (
        repository.list_positions(
            open_only=True
        )
        == []
    )


def test_risk_rejection_is_persisted(
    repository: ExecutionRepository,
) -> None:
    event = repository.create_risk_event(
        signal_id="signal-002",
        source="Greedy Futures Strategy",
        symbol="MNQ1!",
        timeframe="1",
        action="LONG",
        risk_code="TIMEFRAME_NOT_ALLOWED",
        decision="REJECTED",
        reason=(
            "Only the 15-minute timeframe "
            "is allowed."
        ),
        requested_quantity=1,
    )

    assert (
        event["risk_code"]
        == "TIMEFRAME_NOT_ALLOWED"
    )
    assert event["decision"] == "REJECTED"

    rejected_events = (
        repository.list_risk_events(
            decision="REJECTED"
        )
    )

    assert len(rejected_events) == 1
    assert (
        rejected_events[0]["risk_code"]
        == "TIMEFRAME_NOT_ALLOWED"
    )

    summary = repository.get_summary()

    assert summary["risk_events"] == 1
    assert (
        summary["rejected_risk_events"]
        == 1
    )


def test_execution_audit_trail(
    repository: ExecutionRepository,
) -> None:
    order = repository.create_order(
        signal_id="signal-003",
        broker_name="MOCK",
        source="Greedy Futures Strategy",
        symbol="MNQ1!",
        timeframe="15",
        action="SHORT",
        side="SELL",
        quantity=1,
        requested_price=21990.00,
    )

    repository.create_audit_event(
        signal_id="signal-003",
        order_id=order["order_id"],
        event_type="SIGNAL_RECEIVED",
        status="SUCCESS",
        message="Signal entered execution pipeline.",
    )

    repository.create_audit_event(
        signal_id="signal-003",
        order_id=order["order_id"],
        event_type="RISK_APPROVED",
        status="SUCCESS",
        message="Risk engine approved signal.",
    )

    repository.create_audit_event(
        signal_id="signal-003",
        order_id=order["order_id"],
        event_type="BROKER_FILLED",
        status="SUCCESS",
        message="Mock broker filled order.",
    )

    events = repository.list_audit_events(
        order_id=order["order_id"],
    )

    assert len(events) == 3

    event_types = {
        event["event_type"]
        for event in events
    }

    assert event_types == {
        "SIGNAL_RECEIVED",
        "RISK_APPROVED",
        "BROKER_FILLED",
    }


def test_fill_requires_existing_order(
    repository: ExecutionRepository,
) -> None:
    with pytest.raises(
        KeyError,
        match="Order not found",
    ):
        repository.create_fill(
            order_id="missing-order",
            symbol="MNQ1!",
            side="BUY",
            quantity=1,
            fill_price=22000.00,
        )


def test_invalid_order_quantity_rejected(
    repository: ExecutionRepository,
) -> None:
    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        repository.create_order(
            signal_id="signal-004",
            broker_name="MOCK",
            source="Greedy Futures Strategy",
            symbol="MNQ1!",
            timeframe="15",
            action="LONG",
            side="BUY",
            quantity=0,
            requested_price=22000.00,
        )