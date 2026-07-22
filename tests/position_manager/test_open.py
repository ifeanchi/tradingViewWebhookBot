from datetime import datetime, timezone

import pytest

from position_manager import PositionManager, Side
from position_manager.events import PositionOpened
from position_manager.exceptions import PositionAlreadyOpen


def test_open_long_position():
    manager = PositionManager()

    event = PositionOpened(
        timestamp=datetime.now(timezone.utc),
        symbol="MNQ",
        side=Side.LONG,
        quantity=1,
        price=18000.25,
    )

    snapshot = manager.apply(event)

    assert snapshot.symbol == "MNQ"
    assert snapshot.side == Side.LONG
    assert snapshot.quantity == 1
    assert snapshot.average_price == 18000.25
    assert snapshot.realized_pnl == 0.0
    assert snapshot.unrealized_pnl == 0.0
    assert manager.is_long() is True
    assert manager.is_flat() is False


def test_open_short_position():
    manager = PositionManager()

    event = PositionOpened(
        timestamp=datetime.now(timezone.utc),
        symbol="MNQ",
        side=Side.SHORT,
        quantity=2,
        price=18010.50,
    )

    snapshot = manager.apply(event)

    assert snapshot.side == Side.SHORT
    assert snapshot.quantity == 2
    assert snapshot.average_price == 18010.50
    assert manager.is_short() is True


def test_open_rejects_when_position_already_exists():
    manager = PositionManager()

    opened_at = datetime.now(timezone.utc)

    manager.apply(
        PositionOpened(
            timestamp=opened_at,
            symbol="MNQ",
            side=Side.LONG,
            quantity=1,
            price=18000.25,
        )
    )

    with pytest.raises(PositionAlreadyOpen):
        manager.apply(
            PositionOpened(
                timestamp=opened_at,
                symbol="MNQ",
                side=Side.LONG,
                quantity=1,
                price=18005.00,
            )
        )