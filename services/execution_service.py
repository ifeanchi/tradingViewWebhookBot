from __future__ import annotations

from dataclasses import dataclass

from broker.base import (
    BrokerClient,
    BrokerFill,
    BrokerPosition,
    BrokerSide,
)
from models.signal_models import NormalizedSignal
from risk_engine import RiskDecision, RiskEngine


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    signal_action: str
    risk_code: str
    message: str
    fill: BrokerFill | None = None


class ExecutionService:
    def __init__(
        self,
        *,
        broker: BrokerClient,
        risk_engine: RiskEngine,
    ) -> None:
        self.broker = broker
        self.risk_engine = risk_engine
        self.account_id: str | None = None

    async def initialize(self) -> None:
        authenticated = (
            await self.broker.authenticate()
        )

        if not authenticated:
            raise RuntimeError(
                "Broker authentication failed."
            )

        accounts = await self.broker.get_accounts()

        active_accounts = [
            account
            for account in accounts
            if account.active
        ]

        if not active_accounts:
            raise RuntimeError(
                "No active broker account was found."
            )

        self.account_id = (
            active_accounts[0].account_id
        )

    async def execute_signal(
        self,
        *,
        signal: NormalizedSignal,
        current_daily_pnl: float = 0.0,
        execution_enabled: bool | None = None,
    ) -> ExecutionResult:
        if self.account_id is None:
            raise RuntimeError(
                "Execution service is not initialized."
            )

        current_position = (
            await self._get_position(
                signal.symbol
            )
        )

        decision = self.risk_engine.evaluate(
            signal=signal,
            current_position=current_position,
            current_daily_pnl=current_daily_pnl,
            execution_enabled=execution_enabled,
        )

        if not decision.allowed:
            return ExecutionResult(
                status="rejected",
                signal_action=signal.action,
                risk_code=decision.code,
                message=decision.reason,
                fill=None,
            )

        if signal.action == "CLOSE_ALL":
            fill = await self.broker.close_position(
                account_id=self.account_id,
                symbol=signal.symbol,
                reference_price=signal.price,
            )

            if fill is None:
                return ExecutionResult(
                    status="ignored",
                    signal_action=signal.action,
                    risk_code="NO_POSITION",
                    message=(
                        "No broker position was available "
                        "to close."
                    ),
                    fill=None,
                )

            return ExecutionResult(
                status="filled",
                signal_action=signal.action,
                risk_code=decision.code,
                message="Position closed successfully.",
                fill=fill,
            )

        side: BrokerSide = (
            "BUY"
            if signal.action in {
                "LONG",
                "LONG_ADD",
            }
            else "SELL"
        )

        fill = await self.broker.place_market_order(
            account_id=self.account_id,
            symbol=signal.symbol,
            side=side,
            quantity=1,
            reference_price=signal.price,
        )

        return ExecutionResult(
            status="filled",
            signal_action=signal.action,
            risk_code=decision.code,
            message="Mock market order filled.",
            fill=fill,
        )

    async def _get_position(
        self,
        symbol: str,
    ) -> BrokerPosition | None:
        positions = (
            await self.broker.get_positions()
        )

        return next(
            (
                position
                for position in positions
                if position.symbol == symbol
            ),
            None,
        )