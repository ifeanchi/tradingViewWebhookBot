from risk_engine import RiskEngine


def test_execution_disabled(
    make_settings,
    long_signal,
):
    settings = make_settings(
        trading_enabled=False,
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
    )

    assert decision.allowed is False
    assert decision.code == "TRADING_DISABLED"


def test_runtime_execution_override_disables_trading(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
        execution_enabled=False,
    )

    assert decision.allowed is False
    assert decision.code == "TRADING_DISABLED"


def test_runtime_execution_enabled_allows_evaluation(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
        execution_enabled=True,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"