from dataclasses import replace

from risk_engine import RiskEngine


def test_invalid_source(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        source="Unknown",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert decision.allowed is False
    assert decision.code == "SOURCE_NOT_ALLOWED"