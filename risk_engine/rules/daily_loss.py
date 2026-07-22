from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class DailyLossRule(RiskRule):
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        daily_loss_limit = abs(
            context.settings.daily_loss_limit
        )

        if context.current_daily_pnl > -daily_loss_limit:
            return None

        return RiskDecision.reject(
            code="DAILY_LOSS_LIMIT",
            reason="Daily loss limit has been reached.",
        )