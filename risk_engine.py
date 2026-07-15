from __future__ import annotations

from dataclasses import dataclass

from broker.base import BrokerPosition
from config import Settings
from models.signal_models import NormalizedSignal


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    code: str
    reason: str


class RiskEngine:
    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

    def evaluate(
        self,
        *,
        signal: NormalizedSignal,
        current_position: BrokerPosition | None,
        current_daily_pnl: float = 0.0,
        execution_enabled: bool | None = None,
    ) -> RiskDecision:
        enabled = (
            self.settings.trading_enabled
            if execution_enabled is None
            else execution_enabled
        )

        if not enabled:
            return RiskDecision(
                allowed=False,
                code="TRADING_DISABLED",
                reason=(
                    "Execution is disabled by configuration."
                ),
            )

        if signal.source != self.settings.allowed_source:
            return RiskDecision(
                allowed=False,
                code="SOURCE_NOT_ALLOWED",
                reason=(
                    f"Source {signal.source!r} is not allowed."
                ),
            )

        if signal.symbol != self.settings.allowed_symbol:
            return RiskDecision(
                allowed=False,
                code="SYMBOL_NOT_ALLOWED",
                reason=(
                    f"Symbol {signal.symbol!r} is not allowed."
                ),
            )

        if (
            signal.timeframe
            != self.settings.allowed_timeframe
        ):
            return RiskDecision(
                allowed=False,
                code="TIMEFRAME_NOT_ALLOWED",
                reason=(
                    f"Timeframe {signal.timeframe!r} "
                    "is not allowed."
                ),
            )

        if (
            current_daily_pnl
            <= -abs(self.settings.daily_loss_limit)
        ):
            return RiskDecision(
                allowed=False,
                code="DAILY_LOSS_LIMIT",
                reason=(
                    "Daily loss limit has been reached."
                ),
            )

        if signal.action == "CLOSE_ALL":
            if current_position is None:
                return RiskDecision(
                    allowed=False,
                    code="NO_POSITION",
                    reason=(
                        "There is no broker position "
                        "to close."
                    ),
                )

            return RiskDecision(
                allowed=True,
                code="APPROVED_CLOSE",
                reason="Position close approved.",
            )

        if signal.action in {
            "LONG",
            "LONG_ADD",
        }:
            requested_side = "LONG"

        elif signal.action in {
            "SHORT",
            "SHORT_ADD",
        }:
            requested_side = "SHORT"

        else:
            return RiskDecision(
                allowed=False,
                code="UNKNOWN_ACTION",
                reason=(
                    f"Unsupported action: {signal.action}"
                ),
            )

        if current_position is None:
            return RiskDecision(
                allowed=True,
                code="APPROVED_ENTRY",
                reason=(
                    f"New {requested_side} entry approved."
                ),
            )

        if current_position.side != requested_side:
            return RiskDecision(
                allowed=False,
                code="POSITION_CONFLICT",
                reason=(
                    f"Broker is currently "
                    f"{current_position.side}; "
                    f"requested action is "
                    f"{requested_side}."
                ),
            )

        if (
            current_position.quantity
            >= self.settings.max_contracts
        ):
            return RiskDecision(
                allowed=False,
                code="MAX_CONTRACTS",
                reason=(
                    f"Maximum position size of "
                    f"{self.settings.max_contracts} "
                    "contract(s) has been reached."
                ),
            )

        return RiskDecision(
            allowed=True,
            code="APPROVED_ADD",
            reason=(
                f"Additional {requested_side} "
                "contract approved."
            ),
        )