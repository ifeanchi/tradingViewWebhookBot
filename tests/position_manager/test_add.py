from datetime import datetime, timedelta, timezone

import pytest

from position_manager import PositionManager, Side
from position_manager.events import PositionAdded, PositionOpened
from position_manager.exceptions import (
    InvalidAveragePrice,
    PositionNotOpen,
    QuantityMismatch,
)


def open_position(
    manager: PositionManager,
    *,
    side: Side,
    quantity: int,
    price: float,
    timestamp: datetime,
) -> None:
    manager.apply(
        PositionOpened(
            timestamp=timestamp,
            symbol="MNQ",
            side=side,
            quantity=quantity,
            price=price,
        )
    )


def test_add_to_long_recalculates_weighted_average_price():
    manager = PositionManager()
    opened_at = datetime.now(timezone.utc)
    added_at = opened_at + timedelta(minutes=1)

    open_position(
        manager,
        side=Side.LONG,
        quantity=1,
        price=100.0,
        timestamp=opened_at,
    )

    snapshot = manager.apply(
        PositionAdded(
            timestamp=added_at,
            quantity=1,
            price=110.0,
        )
    )

    assert snapshot.side == Side.LONG
    assert snapshot.quantity == 2
    assert snapshot.average_price == pytest.approx(105.0)
    assert snapshot.opened_at == opened_at
    assert snapshot.updated_at == added_at


def test_add_multiple_contracts_to_long():
    manager = PositionManager()
    opened_at = datetime.now(timezone.utc)

    open_position(
        manager,
        side=Side.LONG,
        quantity=2,
        price=100.0,
        timestamp=opened_at,
    )

    snapshot = manager.apply(
        PositionAdded(
            timestamp=opened_at + timedelta(minutes=1),
            quantity=3,
            price=120.0,
        )
    )

    assert snapshot.quantity == 5
    assert snapshot.average_price == pytest.approx(112.0)


def test_add_to_short_recalculates_weighted_average_price():
    manager = PositionManager()
    opened_at = datetime.now(timezone.utc)

    open_position(
        manager,
        side=Side.SHORT,
        quantity=2,
        price=120.0,
        timestamp=opened_at,
    )

    snapshot = manager.apply(
        PositionAdded(
            timestamp=opened_at + timedelta(minutes=1),
            quantity=1,
            price=90.0,
        )
    )

    assert snapshot.side == Side.SHORT
    assert snapshot.quantity == 3
    assert snapshot.average_price == pytest.approx(110.0)


def test_add_preserves_trade_identity_and_realized_pnl():
    manager = PositionManager()
    opened_at = datetime.now(timezone.utc)

    original = manager.apply(
        PositionOpened(
            timestamp=opened_at,
            symbol="MNQ",
            side=Side.LONG,
            quantity=1,
            price=100.0,
        )
    )

    updated = manager.apply(
        PositionAdded(
            timestamp=opened_at + timedelta(minutes=1),
            quantity=1,
            price=110.0,
        )
    )

    assert updated.trade_id == original.trade_id
    assert updated.symbol == original.symbol
    assert updated.realized_pnl == original.realized_pnl
    assert updated.unrealized_pnl == original.unrealized_pnl
    assert updated.opened_at == original.opened_at


def test_add_rejects_when_position_is_flat():
    manager = PositionManager()

    event = PositionAdded(
        timestamp=datetime.now(timezone.utc),
        quantity=1,
        price=100.0,
    )

    with pytest.raises(PositionNotOpen):
        manager.apply(event)


@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_add_rejects_invalid_quantity(quantity):
    manager = PositionManager()
    timestamp = datetime.now(timezone.utc)

    open_position(
        manager,
        side=Side.LONG,
        quantity=1,
        price=100.0,
        timestamp=timestamp,
    )

    event = PositionAdded(
        timestamp=timestamp + timedelta(minutes=1),
        quantity=quantity,
        price=110.0,
    )

    with pytest.raises(QuantityMismatch):
        manager.apply(event)


@pytest.mark.parametrize("price", [0.0, -1.0, -100.0])
def test_add_rejects_invalid_price(price):
    manager = PositionManager()
    timestamp = datetime.now(timezone.utc)

    open_position(
        manager,
        side=Side.LONG,
        quantity=1,
        price=100.0,
        timestamp=timestamp,
    )

    event = PositionAdded(
        timestamp=timestamp + timedelta(minutes=1),
        quantity=1,
        price=price,
    )

    with pytest.raises(InvalidAveragePrice):
        manager.apply(event)