from risk_engine import RiskEngine


def test_daily_loss_limit(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
        current_daily_pnl=-500.0,
    )

    assert decision.allowed is False
    assert decision.code == "DAILY_LOSS_LIMIT"


def test_daily_loss_below_limit_is_approved(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
        current_daily_pnl=-499.99,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"


def test_positive_daily_pnl_is_approved(
    settings,
    long_signal,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=long_signal,
        current_position=None,
        current_daily_pnl=250.0,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"