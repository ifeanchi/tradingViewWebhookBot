from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from repository.execution_repository import ExecutionRepository


@pytest.fixture
def repository(tmp_path):
    db_path = tmp_path / "execution.db"
    return ExecutionRepository(database_path=db_path)


@pytest.fixture
def order(repository):
    return repository.create_order(
        signal_id="signal-1",
        broker_name="MockBroker",
        source="TradingView",
        symbol="MNQ",
        timeframe="15m",
        action="BUY",
        side="LONG",
        quantity=1,
        requested_price=20000.0,
    )


def create_sample_trade(repository, order, **kwargs):
    now = datetime.now(timezone.utc)
    later = now + timedelta(minutes=5)

    defaults = dict(
        signal_id="signal-1",
        order_id=order["order_id"],
        broker_name="MockBroker",
        source="TradingView",
        symbol="MNQ",
        timeframe="15m",
        side="LONG",
        contracts=1,
        entry_price=20000.0,
        exit_price=20020.0,
        points=20.0,
        multiplier=2.0,
        gross_pnl=40.0,
        commission=2.0,
        net_pnl=38.0,
        result="WIN",
        entry_time=now.isoformat(),
        exit_time=later.isoformat(),
        duration_seconds=300.0,
    )

    defaults.update(kwargs)

    return repository.create_trade(**defaults)


# ==========================================================
# CREATE
# ==========================================================


def test_create_trade(repository, order):
    trade = create_sample_trade(repository, order)

    assert trade["symbol"] == "MNQ"
    assert trade["result"] == "WIN"
    assert trade["net_pnl"] == 38.0


# ==========================================================
# GET
# ==========================================================


def test_get_trade(repository, order):
    trade = create_sample_trade(repository, order)

    fetched = repository.get_trade(trade["trade_id"])

    assert fetched is not None
    assert fetched["trade_id"] == trade["trade_id"]


# ==========================================================
# LIST
# ==========================================================


def test_list_trades(repository, order):
    create_sample_trade(repository, order)

    trades = repository.list_trades()

    assert len(trades) == 1


def test_list_trades_by_symbol(repository, order):
    create_sample_trade(repository, order)

    trades = repository.list_trades(symbol="MNQ")

    assert len(trades) == 1


def test_list_trades_by_result(repository, order):
    create_sample_trade(repository, order)

    wins = repository.list_trades(result="WIN")

    assert len(wins) == 1


def test_list_trades_by_side(repository, order):
    create_sample_trade(repository, order)

    longs = repository.list_trades(side="LONG")

    assert len(longs) == 1

def test_list_trades_sorted_by_exit_time_ascending(repository, order):
    create_sample_trade(
        repository,
        order,
        exit_time="2026-01-01T10:00:00+00:00",
    )

    create_sample_trade(
        repository,
        order,
        exit_time="2026-01-01T11:00:00+00:00",
    )

    trades = repository.list_trades(
        order_by="exit_time",
        ascending=True,
    )

    assert trades[0]["exit_time"] < trades[1]["exit_time"]


def test_list_trades_sorted_by_exit_time_descending(repository, order):
    create_sample_trade(
        repository,
        order,
        exit_time="2026-01-01T10:00:00+00:00",
    )

    create_sample_trade(
        repository,
        order,
        exit_time="2026-01-01T11:00:00+00:00",
    )

    trades = repository.list_trades(
        order_by="exit_time",
        ascending=False,
    )

    assert trades[0]["exit_time"] > trades[1]["exit_time"]


def test_list_trades_sorted_by_net_pnl(repository, order):
    create_sample_trade(
        repository,
        order,
        net_pnl=100,
    )

    create_sample_trade(
        repository,
        order,
        net_pnl=25,
    )

    trades = repository.list_trades(
        order_by="net_pnl",
        ascending=False,
    )

    assert trades[0]["net_pnl"] == 100


def test_invalid_order_field(repository):
    with pytest.raises(ValueError):
        repository.list_trades(
            order_by="drop_table",
        )


# ==========================================================
# DELETE
# ==========================================================


def test_delete_trade(repository, order):
    trade = create_sample_trade(repository, order)

    repository.delete_trade(trade["trade_id"])

    assert repository.get_trade(trade["trade_id"]) is None


# ==========================================================
# VALIDATION
# ==========================================================


def test_invalid_side(repository, order):
    with pytest.raises(ValueError):
        create_sample_trade(
            repository,
            order,
            side="UP",
        )


def test_invalid_result(repository, order):
    with pytest.raises(ValueError):
        create_sample_trade(
            repository,
            order,
            result="GOOD",
        )


def test_invalid_contracts(repository, order):
    with pytest.raises(ValueError):
        create_sample_trade(
            repository,
            order,
            contracts=0,
        )


def test_missing_order(repository):
    with pytest.raises(KeyError):
        repository.create_trade(
            signal_id="signal",
            order_id="missing-order",
            broker_name="MockBroker",
            source="TradingView",
            symbol="MNQ",
            timeframe="15m",
            side="LONG",
            contracts=1,
            entry_price=1,
            exit_price=2,
            points=1,
            multiplier=2,
            gross_pnl=2,
            commission=0,
            net_pnl=2,
            result="WIN",
            entry_time="2026-01-01",
            exit_time="2026-01-01",
            duration_seconds=60,
        )


# ==========================================================
# SUMMARY
# ==========================================================


def test_summary_counts_trades(repository, order):
    create_sample_trade(repository, order)

    summary = repository.get_summary()

    assert summary["trades"] == 1