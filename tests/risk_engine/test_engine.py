from risk_engine import RiskEngine
from risk_engine.rules import RiskRule


class PassThroughRule(RiskRule):
    def evaluate(self, context):
        return None
    


def test_engine_rejects_when_no_rule_returns_a_decision(
    settings,
    long_signal,
):
    engine = RiskEngine(
        settings=settings,
        rules=[PassThroughRule()],
    )

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
    )

    assert decision.allowed is False
    assert decision.code == "RISK_EVALUATION_INCOMPLETE"
    assert (
        decision.reason
        == "Risk evaluation completed without producing a final decision."
    )


def test_new_entry_is_approved(
    settings,
    long_signal,
):

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
    )

def test_new_long_entry_is_approved(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"


def test_new_short_entry_is_approved(
    settings,
    short_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=short_signal,
        current_position=None,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"
