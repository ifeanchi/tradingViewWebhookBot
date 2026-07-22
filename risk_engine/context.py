from __future__ import annotations

from dataclasses import dataclass

from broker.base import BrokerPosition
from config import Settings
from models.signal_models import NormalizedSignal


@dataclass(frozen=True)
class RiskContext:
    """
    Immutable input provided to every risk rule.

    New risk-related information can be added here without expanding
    the RiskEngine.evaluate() signature indefinitely.
    """

    settings: Settings
    signal: NormalizedSignal
    current_position: BrokerPosition | None
    current_daily_pnl: float = 0.0
    execution_enabled: bool | None = None

    @property
    def trading_enabled(self) -> bool:
        """
        Return the request-level execution setting when supplied.

        Otherwise, use the platform-wide configuration value.
        """

        if self.execution_enabled is not None:
            return self.execution_enabled

        return self.settings.trading_enabled

    @property
    def requested_side(self) -> str | None:
        """
        Translate supported signal actions into a normalized side.
        """

        if self.signal.action in {
            "LONG",
            "LONG_ADD",
        }:
            return "LONG"

        if self.signal.action in {
            "SHORT",
            "SHORT_ADD",
        }:
            return "SHORT"

        return None