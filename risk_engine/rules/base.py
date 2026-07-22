from __future__ import annotations

from abc import ABC, abstractmethod

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision


class RiskRule(ABC):
    """
    Base contract implemented by every GTAP risk rule.

    Returning None means evaluation may continue.

    Returning a RiskDecision means the rule has produced a terminal
    decision and evaluation must stop.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision | None:
        raise NotImplementedError