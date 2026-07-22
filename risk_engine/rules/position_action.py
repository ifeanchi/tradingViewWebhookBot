from __future__ import annotations

from risk_engine.context import RiskContext
from risk_engine.decision import RiskDecision
from risk_engine.rules.base import RiskRule


class PositionActionRule(RiskRule):
    """
    Evaluates signal action and current broker position.

    This remains one rule during the first refactor so the existing
    position behavior is moved safely without changing its semantics.

    It can later be separated into:
    - ClosePositionRule
    - PositionConflictRule
    - MaxContractsRule
    - EntryApprovalRule
    - AddApprovalRule
    """

    def evaluate(
        self,
        context: RiskContext,
    ) -> RiskDecision:
        signal = context.signal
        position = context.current_position
        settings = context.settings

        if signal.action == "CLOSE_ALL":
            if position is None:
                return RiskDecision.reject(
                    code="NO_POSITION",
                    reason=(
                        "There is no broker position "
                        "to close."
                    ),
                )

            return RiskDecision.approve(
                code="APPROVED_CLOSE",
                reason="Position close approved.",
            )

        requested_side = context.requested_side

        if requested_side is None:
            return RiskDecision.reject(
                code="UNKNOWN_ACTION",
                reason=(
                    f"Unsupported action: {signal.action}"
                ),
            )

        if position is None:
            return RiskDecision.approve(
                code="APPROVED_ENTRY",
                reason=(
                    f"New {requested_side} entry approved."
                ),
            )

        if position.side != requested_side:
            return RiskDecision.reject(
                code="POSITION_CONFLICT",
                reason=(
                    f"Broker is currently "
                    f"{position.side}; "
                    f"requested action is "
                    f"{requested_side}."
                ),
            )

        if position.quantity >= settings.max_contracts:
            return RiskDecision.reject(
                code="MAX_CONTRACTS",
                reason=(
                    f"Maximum position size of "
                    f"{settings.max_contracts} "
                    "contract(s) has been reached."
                ),
            )

        return RiskDecision.approve(
            code="APPROVED_ADD",
            reason=(
                f"Additional {requested_side} "
                "contract approved."
            ),
        )