from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias
from uuid import uuid4

from position_manager.enums import Side
from position_manager.events import (
    PositionAdded,
    PositionEvent,
    PositionOpened,
    PositionReduced,
)

from position_manager.exceptions import (
    InvalidAveragePrice,
    OverReduction,
    PositionAlreadyOpen,
    PositionNotOpen,
    QuantityMismatch,
)

from position_manager.snapshot import PositionSnapshot
from position_manager.state import PositionState




EventHandler: TypeAlias = Callable[[PositionEvent], PositionSnapshot]


class PositionManager:
    """
    Maintains GTAP's broker-agnostic internal position state.

    Position events are dispatched through a handler registry so new event
    types can be added without growing a long conditional chain.
    """

    def __init__(self) -> None:
        self._state: PositionState | None = None

        self._handlers: dict[type[PositionEvent], EventHandler] = {
            PositionOpened: self._apply_open,
            PositionAdded: self._apply_add,
            PositionReduced: self._apply_reduce,
        }


    def _calculate_realized_pnl(
        self,
        side: Side,
        average_price: float,
        exit_price: float,
        quantity: int,
    ) -> float:

        if side == Side.LONG:
            return (exit_price - average_price) * quantity

        return (average_price - exit_price) * quantity
    


    @property
    def state(self) -> PositionState | None:
        return self._state

    def apply(self, event: PositionEvent) -> PositionSnapshot:
        handler = self._handlers.get(type(event))

        if handler is None:
            raise TypeError(
                f"Unsupported position event: {type(event).__name__}"
            )

        return handler(event)

    def _apply_open(self, event: PositionEvent) -> PositionSnapshot:
        if not isinstance(event, PositionOpened):
            raise TypeError(
                f"_apply_open expected PositionOpened, "
                f"received {type(event).__name__}"
            )

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
    
    def _apply_add(self, event: PositionEvent) -> PositionSnapshot:
        if not isinstance(event, PositionAdded):
            raise TypeError(
                f"_apply_add expected PositionAdded, "
                f"received {type(event).__name__}"
            )

        if self._state is None:
            raise PositionNotOpen(
                "Cannot add to a position while flat."
            )

        if event.quantity <= 0:
            raise QuantityMismatch(
                "Added quantity must be greater than zero."
            )

        if event.price <= 0:
            raise InvalidAveragePrice(
                "Added price must be greater than zero."
            )

        current_quantity = self._state.quantity
        new_quantity = current_quantity + event.quantity

        weighted_average_price = (
            (self._state.average_price * current_quantity)
            + (event.price * event.quantity)
        ) / new_quantity

        self._state = PositionState(
            trade_id=self._state.trade_id,
            symbol=self._state.symbol,
            side=self._state.side,
            quantity=new_quantity,
            average_price=weighted_average_price,
            realized_pnl=self._state.realized_pnl,
            unrealized_pnl=self._state.unrealized_pnl,
            opened_at=self._state.opened_at,
            updated_at=event.timestamp,
        )

        return self.snapshot()
    
    def _apply_reduce(
    self,
    event: PositionEvent,
    ) -> PositionSnapshot:
        if not isinstance(event, PositionReduced):
            raise TypeError(
                f"_apply_reduce expected PositionReduced, "
                f"received {type(event).__name__}"
            )

        if self._state is None:
            raise PositionNotOpen(
                "Cannot reduce a position while flat."
            )

        if event.quantity <= 0:
            raise QuantityMismatch(
                "Reduction quantity must be greater than zero."
            )

        if event.price <= 0:
            raise InvalidAveragePrice(
                "Reduction price must be greater than zero."
            )

        if event.quantity > self._state.quantity:
            raise OverReduction(
                "Reduction quantity cannot exceed the active "
                "position quantity."
            )

        if event.quantity == self._state.quantity:
            raise NotImplementedError(
                "Full position close will be implemented "
                "in the next sprint."
            )

        realized_pnl_delta = self._calculate_realized_pnl(
            side=self._state.side,
            average_price=self._state.average_price,
            exit_price=event.price,
            quantity=event.quantity,
        )

        self._state = PositionState(
            trade_id=self._state.trade_id,
            symbol=self._state.symbol,
            side=self._state.side,
            quantity=self._state.quantity - event.quantity,
            average_price=self._state.average_price,
            realized_pnl=(
                self._state.realized_pnl + realized_pnl_delta
            ),
            unrealized_pnl=self._state.unrealized_pnl,
            opened_at=self._state.opened_at,
            updated_at=event.timestamp,
        )

        return self.snapshot()

    @staticmethod
    def _calculate_realized_pnl(
        side: Side,
        average_price: float,
        exit_price: float,
        quantity: int,
    ) -> float:
        if side == Side.LONG:
            return (exit_price - average_price) * quantity

        if side == Side.SHORT:
            return (average_price - exit_price) * quantity

        raise ValueError(
            "Realized P&L can only be calculated for "
            "LONG or SHORT positions."
        )

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