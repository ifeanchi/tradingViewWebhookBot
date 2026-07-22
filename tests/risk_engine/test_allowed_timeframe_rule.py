from dataclasses import replace

from risk_engine import RiskEngine


def test_invalid_timeframe(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        timeframe="1m",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert not decision.allowed
    assert decision.code == "TIMEFRAME_NOT_ALLOWED"