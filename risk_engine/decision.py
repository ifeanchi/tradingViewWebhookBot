from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    """
    Final result produced by the Risk Engine.

    The current boolean-based contract is preserved so existing
    application code does not need to change during this refactor.
    """

    allowed: bool
    code: str
    reason: str

    @classmethod
    def approve(
        cls,
        *,
        code: str,
        reason: str,
    ) -> "RiskDecision":
        return cls(
            allowed=True,
            code=code,
            reason=reason,
        )

    @classmethod
    def reject(
        cls,
        *,
        code: str,
        reason: str,
    ) -> "RiskDecision":
        return cls(
            allowed=False,
            code=code,
            reason=reason,
        )