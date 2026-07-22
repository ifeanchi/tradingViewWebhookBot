from dataclasses import replace

from risk_engine import RiskEngine


def test_position_conflict(
    settings,
    short_signal,
    long_position,
):
    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=short_signal,
        current_position=long_position,
    )

    assert decision.allowed is False
    assert decision.code == "POSITION_CONFLICT"


def test_long_add_is_approved(
    settings,
    long_signal,
    long_position,
):
    signal = replace(
        long_signal,
        action="LONG_ADD",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=long_position,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ADD"


def test_short_add_is_approved(
    settings,
    short_signal,
    short_position,
):
    signal = replace(
        short_signal,
        action="SHORT_ADD",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=short_position,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ADD"


def test_max_contracts_rejects_add(
    make_settings,
    long_signal,
    long_position,
):
    settings = make_settings(
        max_contracts=1,
    )

    signal = replace(
        long_signal,
        action="LONG_ADD",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=long_position,
    )

    assert decision.allowed is False
    assert decision.code == "MAX_CONTRACTS"


def test_long_add_without_position_is_approved_as_entry(
    settings,
    long_signal,
):
    signal = replace(
        long_signal,
        action="LONG_ADD",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"


def test_short_add_without_position_is_approved_as_entry(
    settings,
    short_signal,
):
    signal = replace(
        short_signal,
        action="SHORT_ADD",
    )

    engine = RiskEngine(settings)

    decision = engine.evaluate(
        signal=signal,
        current_position=None,
    )

    assert decision.allowed is True
    assert decision.code == "APPROVED_ENTRY"