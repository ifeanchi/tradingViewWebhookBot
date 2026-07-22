from datetime import datetime, timezone

import pytest

from position_manager import PositionManager, Side
from position_manager.events import PositionOpened
from position_manager.exceptions import (
    InvalidAveragePrice,
    QuantityMismatch,
)


@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_open_rejects_invalid_quantity(quantity):
    manager = PositionManager()

    event = PositionOpened(
        timestamp=datetime.now(timezone.utc),
        symbol="MNQ",
        side=Side.LONG,
        quantity=quantity,
        price=18000.25,
    )

    with pytest.raises(QuantityMismatch):
        manager.apply(event)


@pytest.mark.parametrize("price", [0.0, -1.0, -100.0])
def test_open_rejects_invalid_price(price):
    manager = PositionManager()

    event = PositionOpened(
        timestamp=datetime.now(timezone.utc),
        symbol="MNQ",
        side=Side.LONG,
        quantity=1,
        price=price,
    )

    with pytest.raises(InvalidAveragePrice):
        manager.apply(event)


def test_open_rejects_flat_side():
    manager = PositionManager()

    event = PositionOpened(
        timestamp=datetime.now(timezone.utc),
        symbol="MNQ",
        side=Side.FLAT,
        quantity=1,
        price=18000.25,
    )

    with pytest.raises(ValueError, match="LONG or SHORT"):
        manager.apply(event)