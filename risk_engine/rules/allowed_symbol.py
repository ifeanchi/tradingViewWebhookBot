from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class AllowedSymbolRule(RiskRule):
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        signal = context.signal
        settings = context.settings

        if signal.symbol == settings.allowed_symbol:
            return None

        return RiskDecision.reject(
            code="SYMBOL_NOT_ALLOWED",
            reason=(
                f"Symbol {signal.symbol!r} is not allowed."
            ),
        )