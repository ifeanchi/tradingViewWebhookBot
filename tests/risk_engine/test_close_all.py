from dataclasses import replace

from risk_engine import RiskEngine


def test_close_all_with_open_position_is_approved(
    settings,
    long_signal,
    long_position,
):
    signal = replace(
        long_signal,
        action="CLOSE_ALL",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=long_position,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_CLOSE"


def test_close_all_without_position_is_rejected(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        action="CLOSE_ALL",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert decision.allowed is False
    assert decision.code == "NO_POSITION"