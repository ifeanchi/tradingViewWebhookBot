from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class AllowedTimeframeRule(RiskRule):
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        signal = context.signal
        settings = context.settings

        if signal.timeframe == settings.allowed_timeframe:
            return None

        return RiskDecision.reject(
            code="TIMEFRAME_NOT_ALLOWED",
            reason=(
                f"Timeframe {signal.timeframe!r} "
                "is not allowed."
            ),
        )