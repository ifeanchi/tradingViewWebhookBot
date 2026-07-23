from datetime import datetime, timedelta, timezone

import pytest

from position_manager import PositionManager, Side
from position_manager.events import (
    PositionOpened,
    PositionReduced,
)
from position_manager.exceptions import (
    InvalidAveragePrice,
    OverReduction,
    PositionNotOpen,
    QuantityMismatch,
)


def open_position(manager, side, qty, price):
    manager.apply(
        PositionOpened(
            timestamp=datetime.now(timezone.utc),
            symbol="MNQ",
            side=side,
            quantity=qty,
            price=price,
        )
    )


def test_reduce_long_updates_quantity():
    manager = PositionManager()

    open_position(manager, Side.LONG, 5, 100)

    snapshot = manager.apply(
        PositionReduced(
            timestamp=datetime.now(timezone.utc),
            quantity=2,
            price=110,
        )
    )

    assert snapshot.quantity == 3
    assert snapshot.average_price == 100
    assert snapshot.realized_pnl == 20


def test_reduce_short_updates_quantity():
    manager = PositionManager()

    open_position(manager, Side.SHORT, 5, 120)

    snapshot = manager.apply(
        PositionReduced(
            timestamp=datetime.now(timezone.utc),
            quantity=2,
            price=110,
        )
    )

    assert snapshot.quantity == 3
    assert snapshot.average_price == 120
    assert snapshot.realized_pnl == 20


def test_reduce_rejects_over_reduction():
    manager = PositionManager()

    open_position(manager, Side.LONG, 3, 100)

    with pytest.raises(OverReduction):
        manager.apply(
            PositionReduced(
                timestamp=datetime.now(timezone.utc),
                quantity=4,
                price=110,
            )
        )


def test_reduce_rejects_flat_position():
    manager = PositionManager()

    with pytest.raises(PositionNotOpen):
        manager.apply(
            PositionReduced(
                timestamp=datetime.now(timezone.utc),
                quantity=1,
                price=100,
            )
        )


@pytest.mark.parametrize("qty", [0, -1])
def test_reduce_rejects_invalid_quantity(qty):
    manager = PositionManager()

    open_position(manager, Side.LONG, 3, 100)

    with pytest.raises(QuantityMismatch):
        manager.apply(
            PositionReduced(
                timestamp=datetime.now(timezone.utc),
                quantity=qty,
                price=100,
            )
        )


@pytest.mark.parametrize("price", [0, -1])
def test_reduce_rejects_invalid_price(price):
    manager = PositionManager()

    open_position(manager, Side.LONG, 3, 100)

    with pytest.raises(InvalidAveragePrice):
        manager.apply(
            PositionReduced(
                timestamp=datetime.now(timezone.utc),
                quantity=1,
                price=price,
            )
        )


def test_reduce_entire_position_is_not_yet_supported():
    manager = PositionManager()

    open_position(manager, Side.LONG, 3, 100)

    with pytest.raises(
        NotImplementedError,
        match="Full position close",
    ):
        manager.apply(
            PositionReduced(
                timestamp=datetime.now(timezone.utc),
                quantity=3,
                price=110,
            )
        )