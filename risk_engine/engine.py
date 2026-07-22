from __future__ import annotations

from collections.abc import Sequence

from broker.base import BrokerPosition
from config import Settings
from models.signal_models import NormalizedSignal
from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules import (
    AllowedSourceRule,
    AllowedSymbolRule,
    AllowedTimeframeRule,
    DailyLossRule,
    PositionActionRule,
    RiskRule,
    TradingEnabledRule,
)


class RiskEngine:
    """
    Coordinates the ordered execution of GTAP risk rules.

    The engine does not contain individual risk policies. Each policy
    is implemented by a dedicated RiskRule.
    """

    def __init__(
        self,
        settings: Settings,
        rules: Sequence[RiskRule] | None = None,
    ) -> None:
        self.settings = settings
        self.rules = tuple(
            rules
            if rules is not None
            else self._build_default_rules()
        )

    @staticmethod
    def _build_default_rules() -> tuple[RiskRule, ...]:
        """
        Construct rules in the canonical evaluation order.

        Rule order is significant and must not be changed casually.
        """

        return (
            TradingEnabledRule(),
            AllowedSourceRule(),
            AllowedSymbolRule(),
            AllowedTimeframeRule(),
            DailyLossRule(),
            PositionActionRule(),
        )

    def evaluate(
        self,
        *,
        signal: NormalizedSignal,
        current_position: BrokerPosition | None,
        current_daily_pnl: float = 0.0,
        execution_enabled: bool | None = None,
    ) -> RiskDecision:
        context = RiskContext(
            settings=self.settings,
            signal=signal,
            current_position=current_position,
            current_daily_pnl=current_daily_pnl,
            execution_enabled=execution_enabled,
        )

        for rule in self.rules:
            decision = rule.evaluate(context)

            if decision is not None:
                return decision

        # Defensive fallback. The default final rule should always
        # produce a terminal decision.
        return RiskDecision.reject(
            code="RISK_EVALUATION_INCOMPLETE",
            reason=(
                "Risk evaluation completed without producing "
                "a final decision."
            ),
        )