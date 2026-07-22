from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class AllowedSourceRule(RiskRule):
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        signal = context.signal
        settings = context.settings

        if signal.source == settings.allowed_source:
            return None

        return RiskDecision.reject(
            code="SOURCE_NOT_ALLOWED",
            reason=(
                f"Source {signal.source!r} is not allowed."
            ),
        )