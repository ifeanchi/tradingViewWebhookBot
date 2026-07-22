from dataclasses import replace

from risk_engine import RiskEngine


def test_unknown_action_is_rejected(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        action="INVALID_ACTION",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert decision.allowed is False
    assert decision.code == "UNKNOWN_ACTION"