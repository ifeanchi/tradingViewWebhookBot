from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class TradingEnabledRule(RiskRule):
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        if context.trading_enabled:
            return None

        return RiskDecision.reject(
            code="TRADING_DISABLED",
            reason="Execution is disabled by configuration.",
        )