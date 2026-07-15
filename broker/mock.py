from __future__ import annotations

import uuid
from datetime import datetime, timezone

from broker.base import (
    BrokerAccount,
    BrokerClient,
    BrokerFill,
    BrokerOrder,
    BrokerPosition,
    BrokerSide,
)


class MockBroker(BrokerClient):
    """
    Local in-memory broker simulator.

    It does not connect to Tradovate and cannot place
    real or external paper orders.
    """

    def __init__(
        self,
        starting_balance: float = 50_000.0,
    ) -> None:
        self._authenticated = False

        self._account = BrokerAccount(
            account_id="MOCK-DEMO-001",
            name="Greedy Mock Paper",
            environment="mock",
            balance=starting_balance,
            active=True,
        )

        self._positions: dict[
            str,
            BrokerPosition,
        ] = {}

        self._orders: list[BrokerOrder] = []
        self._fills: list[BrokerFill] = []

    async def authenticate(self) -> bool:
        self._authenticated = True
        return True

    def _require_authenticated(self) -> None:
        if not self._authenticated:
            raise RuntimeError(
                "Mock broker is not authenticated."
            )

    async def get_accounts(
        self,
    ) -> list[BrokerAccount]:
        self._require_authenticated()
        return [self._account]

    async def get_positions(
        self,
    ) -> list[BrokerPosition]:
        self._require_authenticated()
        return list(self._positions.values())

    async def get_orders(
        self,
    ) -> list[BrokerOrder]:
        self._require_authenticated()
        return list(self._orders)

    async def place_market_order(
        self,
        *,
        account_id: str,
        symbol: str,
        side: BrokerSide,
        quantity: int,
        reference_price: float,
    ) -> BrokerFill:
        self._require_authenticated()

        if account_id != self._account.account_id:
            raise ValueError(
                f"Unknown mock account: {account_id}"
            )

        if quantity < 1:
            raise ValueError(
                "Order quantity must be at least 1."
            )

        if reference_price <= 0:
            raise ValueError(
                "Reference price must be greater than zero."
            )

        order_id = str(uuid.uuid4())
        submitted_at = datetime.now(
            timezone.utc
        ).isoformat()

        order = BrokerOrder(
            order_id=order_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type="MARKET",
            status="FILLED",
            submitted_at=submitted_at,
        )

        fill = BrokerFill(
            fill_id=str(uuid.uuid4()),
            order_id=order_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            fill_price=reference_price,
            filled_at=submitted_at,
        )

        self._orders.append(order)
        self._fills.append(fill)

        self._apply_fill(fill)

        return fill

    async def close_position(
        self,
        *,
        account_id: str,
        symbol: str,
        reference_price: float,
    ) -> BrokerFill | None:
        self._require_authenticated()

        position = self._positions.get(symbol)

        if position is None:
            return None

        closing_side: BrokerSide = (
            "SELL"
            if position.side == "LONG"
            else "BUY"
        )

        return await self.place_market_order(
            account_id=account_id,
            symbol=symbol,
            side=closing_side,
            quantity=position.quantity,
            reference_price=reference_price,
        )

    def _apply_fill(
        self,
        fill: BrokerFill,
    ) -> None:
        current = self._positions.get(fill.symbol)

        incoming_direction = (
            1
            if fill.side == "BUY"
            else -1
        )

        if current is None:
            self._positions[fill.symbol] = (
                BrokerPosition(
                    account_id=fill.account_id,
                    symbol=fill.symbol,
                    side=(
                        "LONG"
                        if incoming_direction > 0
                        else "SHORT"
                    ),
                    quantity=fill.quantity,
                    average_price=fill.fill_price,
                )
            )
            return

        current_direction = (
            1
            if current.side == "LONG"
            else -1
        )

        signed_current = (
            current.quantity
            * current_direction
        )

        signed_incoming = (
            fill.quantity
            * incoming_direction
        )

        resulting_quantity = (
            signed_current
            + signed_incoming
        )

        if resulting_quantity == 0:
            del self._positions[fill.symbol]
            return

        if (
            current_direction
            == incoming_direction
        ):
            total_quantity = (
                current.quantity
                + fill.quantity
            )

            weighted_price = (
                (
                    current.average_price
                    * current.quantity
                )
                + (
                    fill.fill_price
                    * fill.quantity
                )
            ) / total_quantity

            self._positions[fill.symbol] = (
                BrokerPosition(
                    account_id=fill.account_id,
                    symbol=fill.symbol,
                    side=current.side,
                    quantity=total_quantity,
                    average_price=weighted_price,
                )
            )
            return

        resulting_side = (
            "LONG"
            if resulting_quantity > 0
            else "SHORT"
        )

        self._positions[fill.symbol] = (
            BrokerPosition(
                account_id=fill.account_id,
                symbol=fill.symbol,
                side=resulting_side,
                quantity=abs(resulting_quantity),
                average_price=fill.fill_price,
            )
        )