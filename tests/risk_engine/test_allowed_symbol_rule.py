from dataclasses import replace

from risk_engine import RiskEngine


def test_invalid_symbol(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        symbol="MES",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert not decision.allowed
    assert decision.code == "SYMBOL_NOT_ALLOWED"