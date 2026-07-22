from __future__ import annotations

from uuid import uuid4

from position_manager.enums import Side
from position_manager.events import PositionEvent, PositionOpened
from position_manager.exceptions import (
    InvalidAveragePrice,
    PositionAlreadyOpen,
    QuantityMismatch,
)
from position_manager.snapshot import PositionSnapshot
from position_manager.state import PositionState


class PositionManager:
    """
    Maintains GTAP's broker-agnostic internal position state.
    """

    def __init__(self) -> None:
        self._state: PositionState | None = None

    @property
    def state(self) -> PositionState | None:
        return self._state

    def apply(self, event: PositionEvent) -> PositionSnapshot:
        if isinstance(event, PositionOpened):
            return self._apply_open(event)

        raise TypeError(
            f"Unsupported position event: {type(event).__name__}"
        )

    def _apply_open(self, event: PositionOpened) -> PositionSnapshot:
        if self._state is not None:
            raise PositionAlreadyOpen(
                "Cannot open a position while another position is active."
            )

        if event.side not in {Side.LONG, Side.SHORT}:
            raise ValueError(
                "PositionOpened side must be LONG or SHORT."
            )

        if event.quantity <= 0:
            raise QuantityMismatch(
                "Opening quantity must be greater than zero."
            )

        if event.price <= 0:
            raise InvalidAveragePrice(
                "Opening price must be greater than zero."
            )

        self._state = PositionState(
            trade_id=uuid4(),
            symbol=event.symbol,
            side=event.side,
            quantity=event.quantity,
            average_price=event.price,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            opened_at=event.timestamp,
            updated_at=event.timestamp,
        )

        return self.snapshot()

    def snapshot(self) -> PositionSnapshot:
        if self._state is None:
            raise RuntimeError("No active position.")

        return PositionSnapshot(
            trade_id=self._state.trade_id,
            symbol=self._state.symbol,
            side=self._state.side,
            quantity=self._state.quantity,
            average_price=self._state.average_price,
            realized_pnl=self._state.realized_pnl,
            unrealized_pnl=self._state.unrealized_pnl,
            opened_at=self._state.opened_at,
            updated_at=self._state.updated_at,
        )

    def is_flat(self) -> bool:
        return self._state is None

    def is_long(self) -> bool:
        return (
            self._state is not None
            and self._state.side == Side.LONG
        )

    def is_short(self) -> bool:
        return (
            self._state is not None
            and self._state.side == Side.SHORT
        )

    def has_position(self) -> bool:
        return self._state is not None