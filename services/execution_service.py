from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from broker.base import (
    BrokerClient,
    BrokerFill,
    BrokerPosition,
    BrokerSide,
)
from models.signal_models import NormalizedSignal
from repository import ExecutionRepository
from risk_engine import RiskEngine


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
        repository: ExecutionRepository | None = None,
    ) -> None:
        self.broker = broker
        self.risk_engine = risk_engine
        self.repository = repository
        self.account_id: str | None = None

    async def initialize(self) -> None:
        authenticated = await self.broker.authenticate()

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

        signal_id = self._get_signal_id(signal)

        self._create_audit_event(
            signal_id=signal_id,
            event_type="SIGNAL_RECEIVED",
            status="SUCCESS",
            message=(
                "Signal entered the execution pipeline."
            ),
            metadata={
                "source": signal.source,
                "symbol": signal.symbol,
                "timeframe": signal.timeframe,
                "action": signal.action,
                "price": signal.price,
                "timestamp": signal.timestamp,
            },
        )

        current_position = await self._get_position(
            signal.symbol
        )

        decision = self.risk_engine.evaluate(
            signal=signal,
            current_position=current_position,
            current_daily_pnl=current_daily_pnl,
            execution_enabled=execution_enabled,
        )

        if not decision.allowed:
            self._create_risk_event(
                signal_id=signal_id,
                signal=signal,
                order_id=None,
                risk_code=decision.code,
                decision="REJECTED",
                reason=decision.reason,
                daily_pnl=current_daily_pnl,
            )

            self._create_audit_event(
                signal_id=signal_id,
                event_type="RISK_REJECTED",
                status="REJECTED",
                message=decision.reason,
                metadata={
                    "risk_code": decision.code,
                    "daily_pnl": current_daily_pnl,
                },
            )

            return ExecutionResult(
                status="rejected",
                signal_action=signal.action,
                risk_code=decision.code,
                message=decision.reason,
                fill=None,
            )

        self._create_audit_event(
            signal_id=signal_id,
            event_type="RISK_APPROVED",
            status="SUCCESS",
            message=decision.reason,
            metadata={
                "risk_code": decision.code,
                "daily_pnl": current_daily_pnl,
            },
        )

        if signal.action == "CLOSE_ALL":
            return await self._execute_close(
                signal=signal,
                signal_id=signal_id,
                current_position=current_position,
                risk_code=decision.code,
                risk_reason=decision.reason,
                current_daily_pnl=current_daily_pnl,
            )

        return await self._execute_entry(
            signal=signal,
            signal_id=signal_id,
            risk_code=decision.code,
            risk_reason=decision.reason,
            current_daily_pnl=current_daily_pnl,
        )

    async def _execute_entry(
        self,
        *,
        signal: NormalizedSignal,
        signal_id: str,
        risk_code: str,
        risk_reason: str,
        current_daily_pnl: float,
    ) -> ExecutionResult:
        side: BrokerSide = (
            "BUY"
            if signal.action in {
                "LONG",
                "LONG_ADD",
            }
            else "SELL"
        )

        quantity = 1

        order = self._create_order(
            signal_id=signal_id,
            signal=signal,
            side=side,
            quantity=quantity,
        )

        order_id = (
            order["order_id"]
            if order is not None
            else None
        )

        self._create_risk_event(
            signal_id=signal_id,
            signal=signal,
            order_id=order_id,
            risk_code=risk_code,
            decision="APPROVED",
            reason=risk_reason,
            daily_pnl=current_daily_pnl,
        )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="ORDER_CREATED",
            status="SUCCESS",
            message="Execution order created.",
            metadata={
                "side": side,
                "quantity": quantity,
                "requested_price": signal.price,
            },
        )

        try:
            if order_id is not None:
                self.repository.update_order_status(
                    order_id,
                    "SUBMITTED",
                    submitted_at=self._signal_timestamp(
                        signal
                    ),
                )

            self._create_audit_event(
                signal_id=signal_id,
                order_id=order_id,
                event_type="ORDER_SUBMITTED",
                status="SUCCESS",
                message=(
                    "Market order submitted to broker."
                ),
                metadata={
                    "account_id": self.account_id,
                    "broker": self._broker_name(),
                },
            )

            fill = await self.broker.place_market_order(
                account_id=self.account_id,
                symbol=signal.symbol,
                side=side,
                quantity=quantity,
                reference_price=signal.price,
            )

        except Exception as exc:
            self._record_order_failure(
                signal_id=signal_id,
                order_id=order_id,
                exc=exc,
            )
            raise

        self._persist_fill(
            order_id=order_id,
            signal=signal,
            fill=fill,
            fallback_side=side,
            fallback_quantity=quantity,
        )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="ORDER_FILLED",
            status="SUCCESS",
            message="Broker filled the market order.",
            metadata=self._fill_metadata(fill),
        )

        await self._synchronize_position(
            signal=signal,
            signal_id=signal_id,
            order_id=order_id,
        )

        return ExecutionResult(
            status="filled",
            signal_action=signal.action,
            risk_code=risk_code,
            message="Mock market order filled.",
            fill=fill,
        )

    async def _execute_close(
        self,
        *,
        signal: NormalizedSignal,
        signal_id: str,
        current_position: BrokerPosition | None,
        risk_code: str,
        risk_reason: str,
        current_daily_pnl: float,
    ) -> ExecutionResult:
        close_side = self._get_close_side(
            current_position
        )

        close_quantity = self._get_position_quantity(
            current_position
        )

        order = self._create_order(
            signal_id=signal_id,
            signal=signal,
            side=close_side,
            quantity=close_quantity,
        )

        order_id = (
            order["order_id"]
            if order is not None
            else None
        )

        self._create_risk_event(
            signal_id=signal_id,
            signal=signal,
            order_id=order_id,
            risk_code=risk_code,
            decision="APPROVED",
            reason=risk_reason,
            daily_pnl=current_daily_pnl,
        )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="ORDER_CREATED",
            status="SUCCESS",
            message="Close-position order created.",
            metadata={
                "side": close_side,
                "quantity": close_quantity,
                "requested_price": signal.price,
            },
        )

        try:
            if order_id is not None:
                self.repository.update_order_status(
                    order_id,
                    "SUBMITTED",
                    submitted_at=self._signal_timestamp(
                        signal
                    ),
                )

            self._create_audit_event(
                signal_id=signal_id,
                order_id=order_id,
                event_type="ORDER_SUBMITTED",
                status="SUCCESS",
                message=(
                    "Close-position request submitted "
                    "to broker."
                ),
                metadata={
                    "account_id": self.account_id,
                    "broker": self._broker_name(),
                },
            )

            fill = await self.broker.close_position(
                account_id=self.account_id,
                symbol=signal.symbol,
                reference_price=signal.price,
            )

        except Exception as exc:
            self._record_order_failure(
                signal_id=signal_id,
                order_id=order_id,
                exc=exc,
            )
            raise

        if fill is None:
            if (
                self.repository is not None
                and order_id is not None
            ):
                self.repository.update_order_status(
                    order_id,
                    "IGNORED",
                )

            self._create_audit_event(
                signal_id=signal_id,
                order_id=order_id,
                event_type="ORDER_IGNORED",
                status="IGNORED",
                message=(
                    "No broker position was available "
                    "to close."
                ),
                metadata={
                    "symbol": signal.symbol,
                },
            )

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

        self._persist_fill(
            order_id=order_id,
            signal=signal,
            fill=fill,
            fallback_side=close_side,
            fallback_quantity=close_quantity,
        )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="ORDER_FILLED",
            status="SUCCESS",
            message=(
                "Broker filled the close-position order."
            ),
            metadata=self._fill_metadata(fill),
        )

        await self._synchronize_position(
            signal=signal,
            signal_id=signal_id,
            order_id=order_id,
        )

        return ExecutionResult(
            status="filled",
            signal_action=signal.action,
            risk_code=risk_code,
            message="Position closed successfully.",
            fill=fill,
        )

    def _create_order(
        self,
        *,
        signal_id: str,
        signal: NormalizedSignal,
        side: BrokerSide,
        quantity: int,
    ) -> dict[str, Any] | None:
        if self.repository is None:
            return None

        return self.repository.create_order(
            signal_id=signal_id,
            broker_name=self._broker_name(),
            source=signal.source,
            symbol=signal.symbol,
            timeframe=str(signal.timeframe),
            action=signal.action,
            side=side,
            quantity=max(quantity, 1),
            requested_price=signal.price,
            status="APPROVED",
            order_comment=getattr(
                signal,
                "order_comment",
                None,
            ),
            raw_payload=self._signal_metadata(signal),
        )

    def _create_risk_event(
        self,
        *,
        signal_id: str,
        signal: NormalizedSignal,
        order_id: str | None,
        risk_code: str,
        decision: str,
        reason: str,
        daily_pnl: float,
    ) -> None:
        if self.repository is None:
            return

        self.repository.create_risk_event(
            signal_id=signal_id,
            order_id=order_id,
            source=signal.source,
            symbol=signal.symbol,
            timeframe=str(signal.timeframe),
            action=signal.action,
            risk_code=risk_code,
            decision=decision,
            reason=reason,
            daily_pnl=current_float(daily_pnl),
            requested_quantity=1,
            raw_payload=self._signal_metadata(signal),
        )

    def _create_audit_event(
        self,
        *,
        signal_id: str,
        event_type: str,
        status: str,
        message: str,
        order_id: str | None = None,
        metadata: Any = None,
    ) -> None:
        if self.repository is None:
            return

        self.repository.create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type=event_type,
            status=status,
            message=message,
            metadata=metadata,
        )

    def _persist_fill(
        self,
        *,
        order_id: str | None,
        signal: NormalizedSignal,
        fill: BrokerFill,
        fallback_side: BrokerSide,
        fallback_quantity: int,
    ) -> None:
        if (
            self.repository is None
            or order_id is None
        ):
            return

        fill_price = float(
            getattr(
                fill,
                "fill_price",
                signal.price,
            )
        )

        quantity = int(
            getattr(
                fill,
                "quantity",
                fallback_quantity,
            )
        )

        fill_side = str(
            getattr(
                fill,
                "side",
                fallback_side,
            )
        ).upper()

        filled_at = getattr(
            fill,
            "filled_at",
            None,
        )

        broker_fill_id = getattr(
            fill,
            "fill_id",
            None,
        )

        self.repository.create_fill(
            order_id=order_id,
            symbol=signal.symbol,
            side=fill_side,
            quantity=max(quantity, 1),
            fill_price=fill_price,
            filled_at=(
                str(filled_at)
                if filled_at is not None
                else None
            ),
            broker_fill_id=(
                str(broker_fill_id)
                if broker_fill_id is not None
                else None
            ),
            raw_payload=self._fill_metadata(fill),
        )

    async def _synchronize_position(
        self,
        *,
        signal: NormalizedSignal,
        signal_id: str,
        order_id: str | None,
    ) -> None:
        if self.repository is None:
            return

        broker_position = await self._get_position(
            signal.symbol
        )

        if broker_position is None:
            stored_position = (
                self.repository.get_position(
                    signal.symbol
                )
            )

            if stored_position is not None:
                self.repository.close_position(
                    signal.symbol
                )

            self._create_audit_event(
                signal_id=signal_id,
                order_id=order_id,
                event_type="POSITION_CLOSED",
                status="SUCCESS",
                message=(
                    "Execution position synchronized "
                    "as flat."
                ),
                metadata={
                    "symbol": signal.symbol,
                },
            )

            return

        quantity = self._get_position_quantity(
            broker_position
        )

        if quantity == 0:
            stored_position = (
                self.repository.get_position(
                    signal.symbol
                )
            )

            if stored_position is not None:
                self.repository.close_position(
                    signal.symbol
                )

            self._create_audit_event(
                signal_id=signal_id,
                order_id=order_id,
                event_type="POSITION_CLOSED",
                status="SUCCESS",
                message=(
                    "Execution position synchronized "
                    "as flat."
                ),
                metadata={
                    "symbol": signal.symbol,
                },
            )

            return

        side = self._normalize_position_side(
            broker_position
        )

        average_price = float(
            getattr(
                broker_position,
                "average_price",
                signal.price,
            )
        )

        opened_at = getattr(
            broker_position,
            "opened_at",
            None,
        )

        self.repository.upsert_position(
            symbol=signal.symbol,
            broker_name=self._broker_name(),
            quantity=quantity,
            side=side,
            average_price=average_price,
            status="OPEN",
            opened_at=(
                str(opened_at)
                if opened_at is not None
                else self._signal_timestamp(signal)
            ),
            closed_at=None,
        )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="POSITION_OPENED",
            status="SUCCESS",
            message=(
                "Execution position synchronized "
                "with broker state."
            ),
            metadata={
                "symbol": signal.symbol,
                "side": side,
                "quantity": quantity,
                "average_price": average_price,
            },
        )

    def _record_order_failure(
        self,
        *,
        signal_id: str,
        order_id: str | None,
        exc: Exception,
    ) -> None:
        if (
            self.repository is not None
            and order_id is not None
        ):
            self.repository.update_order_status(
                order_id,
                "FAILED",
            )

        self._create_audit_event(
            signal_id=signal_id,
            order_id=order_id,
            event_type="BROKER_ERROR",
            status="FAILED",
            message=f"{type(exc).__name__}: {exc}",
        )

    async def _get_position(
        self,
        symbol: str,
    ) -> BrokerPosition | None:
        positions = await self.broker.get_positions()

        return next(
            (
                position
                for position in positions
                if position.symbol == symbol
            ),
            None,
        )

    @staticmethod
    def _get_signal_id(
        signal: NormalizedSignal,
    ) -> str:
        existing_signal_id = getattr(
            signal,
            "signal_id",
            None,
        )

        if existing_signal_id:
            return str(existing_signal_id)

        strategy_order_id = getattr(
            signal,
            "order_id",
            None,
        )

        if strategy_order_id:
            return (
                f"{strategy_order_id}-"
                f"{uuid.uuid4().hex}"
            )

        return str(uuid.uuid4())

    @staticmethod
    def _get_position_quantity(
        position: BrokerPosition | None,
    ) -> int:
        if position is None:
            return 1

        quantity = int(
            getattr(
                position,
                "quantity",
                1,
            )
        )

        return max(abs(quantity), 1)

    @staticmethod
    def _get_close_side(
        position: BrokerPosition | None,
    ) -> BrokerSide:
        if position is None:
            return "SELL"

        position_side = str(
            getattr(
                position,
                "side",
                "",
            )
        ).upper()

        if position_side in {
            "SHORT",
            "SELL",
        }:
            return "BUY"

        return "SELL"

    @staticmethod
    def _normalize_position_side(
        position: BrokerPosition,
    ) -> str:
        side = str(
            getattr(
                position,
                "side",
                "",
            )
        ).upper()

        if side in {
            "BUY",
            "LONG",
        }:
            return "LONG"

        if side in {
            "SELL",
            "SHORT",
        }:
            return "SHORT"

        quantity = int(
            getattr(
                position,
                "quantity",
                0,
            )
        )

        return (
            "LONG"
            if quantity > 0
            else "SHORT"
        )

    def _broker_name(self) -> str:
        broker_class_name = (
            self.broker.__class__.__name__
        )

        return broker_class_name.upper()

    @staticmethod
    def _signal_timestamp(
        signal: NormalizedSignal,
    ) -> str | None:
        timestamp = getattr(
            signal,
            "timestamp",
            None,
        )

        if timestamp is None:
            return None

        return str(timestamp)

    @staticmethod
    def _signal_metadata(
        signal: NormalizedSignal,
    ) -> dict[str, Any]:
        return {
            "source": signal.source,
            "action": signal.action,
            "symbol": signal.symbol,
            "timeframe": signal.timeframe,
            "price": signal.price,
            "timestamp": signal.timestamp,
            "order_id": getattr(
                signal,
                "order_id",
                None,
            ),
            "order_comment": getattr(
                signal,
                "order_comment",
                None,
            ),
        }

    @staticmethod
    def _fill_metadata(
        fill: BrokerFill,
    ) -> dict[str, Any]:
        return {
            "fill_id": getattr(
                fill,
                "fill_id",
                None,
            ),
            "order_id": getattr(
                fill,
                "order_id",
                None,
            ),
            "symbol": getattr(
                fill,
                "symbol",
                None,
            ),
            "side": getattr(
                fill,
                "side",
                None,
            ),
            "quantity": getattr(
                fill,
                "quantity",
                None,
            ),
            "fill_price": getattr(
                fill,
                "fill_price",
                None,
            ),
            "filled_at": getattr(
                fill,
                "filled_at",
                None,
            ),
        }


def current_float(value: float | int) -> float:
    return float(value)