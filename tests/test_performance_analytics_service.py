from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from repository.execution_repository import ExecutionRepository
from services.performance_analytics_service import (
    PerformanceAnalyticsService,
)


@pytest.fixture
def repository(tmp_path):
    return ExecutionRepository(
        database_path=tmp_path / "execution.db"
    )


@pytest.fixture
def analytics_service(repository):
    return PerformanceAnalyticsService(repository)


def create_order(
    repository,
    *,
    signal_id: str,
    symbol: str = "MNQ",
    side: str = "LONG",
):
    action = "BUY" if side == "LONG" else "SELL"

    return repository.create_order(
        signal_id=signal_id,
        broker_name="MockBroker",
        source="TradingView",
        symbol=symbol,
        timeframe="15m",
        action=action,
        side=side,
        quantity=1,
        requested_price=20000.0,
    )


def create_trade(
    repository,
    *,
    signal_id: str,
    result: str,
    net_pnl: float,
    gross_pnl: float,
    commission: float,
    points: float,
    symbol: str = "MNQ",
    side: str = "LONG",
    entry_time: datetime | None = None,
    exit_time: datetime | None = None,
):
    order = create_order(
        repository,
        signal_id=signal_id,
        symbol=symbol,
        side=side,
    )

    if entry_time is None:
        entry_time = datetime.now(timezone.utc)

    if exit_time is None:
        exit_time = entry_time + timedelta(minutes=5)

    if side == "LONG":
        entry_price = 20000.0
        exit_price = entry_price + points
    else:
        entry_price = 20000.0
        exit_price = entry_price - points

    return repository.create_trade(
        signal_id=signal_id,
        order_id=order["order_id"],
        broker_name="MockBroker",
        source="TradingView",
        symbol=symbol,
        timeframe="15m",
        side=side,
        contracts=1,
        entry_price=entry_price,
        exit_price=exit_price,
        points=points,
        multiplier=2.0,
        gross_pnl=gross_pnl,
        commission=commission,
        net_pnl=net_pnl,
        result=result,
        entry_time=entry_time.isoformat(),
        exit_time=exit_time.isoformat(),
        duration_seconds=300.0,
    )


def seed_sample_trades(repository):
    create_trade(
        repository,
        signal_id="signal-win-1",
        result="WIN",
        net_pnl=38.0,
        gross_pnl=40.0,
        commission=2.0,
        points=20.0,
        side="LONG",
    )

    create_trade(
        repository,
        signal_id="signal-win-2",
        result="WIN",
        net_pnl=58.0,
        gross_pnl=60.0,
        commission=2.0,
        points=30.0,
        side="SHORT",
    )

    create_trade(
        repository,
        signal_id="signal-loss",
        result="LOSS",
        net_pnl=-22.0,
        gross_pnl=-20.0,
        commission=2.0,
        points=-10.0,
        side="LONG",
    )

    create_trade(
        repository,
        signal_id="signal-breakeven",
        result="BREAKEVEN",
        net_pnl=-2.0,
        gross_pnl=0.0,
        commission=2.0,
        points=0.0,
        side="LONG",
    )


# ==========================================================
# EMPTY SUMMARY
# ==========================================================


def test_empty_summary_returns_zero_values(
    analytics_service,
):
    summary = analytics_service.generate_summary()

    assert summary.total_trades == 0
    assert summary.winning_trades == 0
    assert summary.losing_trades == 0
    assert summary.breakeven_trades == 0
    assert summary.win_rate == 0.0
    assert summary.net_profit == 0.0
    assert summary.profit_factor is None


# ==========================================================
# COMPLETE SUMMARY
# ==========================================================


def test_generate_summary_counts_trades(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.total_trades == 4
    assert summary.winning_trades == 2
    assert summary.losing_trades == 1
    assert summary.breakeven_trades == 1


def test_generate_summary_calculates_rates(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.win_rate == 50.0
    assert summary.loss_rate == 25.0
    assert summary.breakeven_rate == 25.0


def test_generate_summary_calculates_profit(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.gross_profit == 100.0
    assert summary.gross_loss == 20.0
    assert summary.total_commission == 8.0
    assert summary.net_profit == 72.0


def test_generate_summary_calculates_averages(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.average_trade == 18.0
    assert summary.average_winner == 48.0
    assert summary.average_loser == -22.0
    assert summary.expectancy == 18.0


def test_generate_summary_calculates_extremes(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.largest_winner == 58.0
    assert summary.largest_loser == -22.0


def test_generate_summary_calculates_profit_factor(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.profit_factor == 5.0


def test_generate_summary_calculates_points(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary()

    assert summary.total_points == 40.0
    assert summary.average_points == 10.0


def test_drawdown_percentage_and_datetime_helpers():
    assert (
        PerformanceAnalyticsService._drawdown_percentage(
            drawdown=-20.0,
            peak_equity=100.0,
        )
        == -20.0
    )
    assert (
        PerformanceAnalyticsService._drawdown_percentage(
            drawdown=-10.0,
            peak_equity=0.0,
        )
        == 0.0
    )

    parsed_datetime = PerformanceAnalyticsService._parse_datetime(
        "2024-01-02T03:04:05Z"
    )

    assert parsed_datetime == datetime(
        2024,
        1,
        2,
        3,
        4,
        5,
        tzinfo=timezone.utc,
    )




# ==========================================================
# EQUITY CURVE
# ==========================================================


def test_generate_equity_curve_returns_empty_list(
    analytics_service,
):
    curve = analytics_service.generate_equity_curve()

    assert curve == []


def test_generate_equity_curve_calculates_values(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    curve = analytics_service.generate_equity_curve()

    assert len(curve) == 4

    assert curve[0].trade_number == 1
    assert curve[0].trade_pnl == 38.0
    assert curve[0].cumulative_pnl == 38.0
    assert curve[0].peak_equity == 38.0
    assert curve[0].drawdown == 0.0
    assert curve[0].drawdown_percent == 0.0

    assert curve[1].trade_number == 2
    assert curve[1].trade_pnl == 58.0
    assert curve[1].cumulative_pnl == 96.0
    assert curve[1].peak_equity == 96.0
    assert curve[1].drawdown == 0.0
    assert curve[1].drawdown_percent == 0.0

    assert curve[2].trade_number == 3
    assert curve[2].trade_pnl == -22.0
    assert curve[2].cumulative_pnl == 74.0
    assert curve[2].peak_equity == 96.0
    assert curve[2].drawdown == -22.0
    assert curve[2].drawdown_percent == pytest.approx(
        -22.92,
        abs=0.01,
    )

    assert curve[3].trade_number == 4
    assert curve[3].trade_pnl == -2.0
    assert curve[3].cumulative_pnl == 72.0
    assert curve[3].peak_equity == 96.0
    assert curve[3].drawdown == -24.0
    assert curve[3].drawdown_percent == -25.0


def test_generate_equity_curve_orders_trades_by_exit_time(
    repository,
    analytics_service,
):
    base_time = datetime(
        2024,
        1,
        1,
        9,
        30,
        tzinfo=timezone.utc,
    )

    later_trade = create_trade(
        repository,
        signal_id="later-trade",
        result="WIN",
        net_pnl=20.0,
        gross_pnl=22.0,
        commission=2.0,
        points=10.0,
        entry_time=base_time + timedelta(minutes=10),
        exit_time=base_time + timedelta(minutes=15),
    )

    earlier_trade = create_trade(
        repository,
        signal_id="earlier-trade",
        result="WIN",
        net_pnl=10.0,
        gross_pnl=12.0,
        commission=2.0,
        points=5.0,
        entry_time=base_time,
        exit_time=base_time + timedelta(minutes=5),
    )

    curve = analytics_service.generate_equity_curve()

    assert len(curve) == 2

    assert curve[0].trade_id == str(
        earlier_trade["trade_id"]
    )
    assert curve[0].trade_pnl == 10.0
    assert curve[0].cumulative_pnl == 10.0

    assert curve[1].trade_id == str(
        later_trade["trade_id"]
    )
    assert curve[1].trade_pnl == 20.0
    assert curve[1].cumulative_pnl == 30.0


def test_generate_equity_curve_filters_by_symbol(
    repository,
    analytics_service,
):
    create_trade(
        repository,
        signal_id="mnq-trade",
        result="WIN",
        net_pnl=38.0,
        gross_pnl=40.0,
        commission=2.0,
        points=20.0,
        symbol="MNQ",
    )

    create_trade(
        repository,
        signal_id="mes-trade",
        result="WIN",
        net_pnl=23.0,
        gross_pnl=25.0,
        commission=2.0,
        points=5.0,
        symbol="MES",
    )

    curve = analytics_service.generate_equity_curve(
        symbol="MES"
    )

    assert len(curve) == 1
    assert curve[0].trade_pnl == 23.0
    assert curve[0].cumulative_pnl == 23.0

# ==========================================================
# STREAK SUMMARY
# ==========================================================



def test_generate_streak_summary_returns_zero_values(
    analytics_service,
):
    summary = analytics_service.generate_streak_summary()

    assert summary.current_winning_streak == 0
    assert summary.current_losing_streak == 0
    assert summary.longest_winning_streak == 0
    assert summary.longest_losing_streak == 0
    assert summary.total_win_streaks == 0
    assert summary.total_loss_streaks == 0



def test_generate_streak_summary_calculates_streaks(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    create_trade(
        repository,
        signal_id="streak-001",
        result="WIN",
        net_pnl=18.0,
        gross_pnl=20.0,
        commission=2.0,
        points=10.0,
        exit_time=base,
    )

    create_trade(
        repository,
        signal_id="streak-002",
        result="WIN",
        net_pnl=22.0,
        gross_pnl=24.0,
        commission=2.0,
        points=12.0,
        exit_time=base + timedelta(minutes=1),
    )

    create_trade(
        repository,
        signal_id="streak-003",
        result="LOSS",
        net_pnl=-12.0,
        gross_pnl=-10.0,
        commission=2.0,
        points=-5.0,
        exit_time=base + timedelta(minutes=2),
    )

    create_trade(
        repository,
        signal_id="streak-004",
        result="LOSS",
        net_pnl=-16.0,
        gross_pnl=-14.0,
        commission=2.0,
        points=-7.0,
        exit_time=base + timedelta(minutes=3),
    )

    create_trade(
        repository,
        signal_id="streak-005",
        result="WIN",
        net_pnl=26.0,
        gross_pnl=28.0,
        commission=2.0,
        points=14.0,
        exit_time=base + timedelta(minutes=4),
    )

    summary = analytics_service.generate_streak_summary()

    assert summary.current_winning_streak == 1
    assert summary.current_losing_streak == 0

    assert summary.longest_winning_streak == 2
    assert summary.longest_losing_streak == 2

    assert summary.total_win_streaks == 2
    assert summary.total_loss_streaks == 1


def test_generate_streak_summary_all_wins(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    for i in range(5):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"all-win-{i}",
            result="WIN",
            net_pnl=18.0,
            gross_pnl=20.0,
            commission=2.0,
            points=10.0,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_streak_summary()

    assert summary.current_winning_streak == 5
    assert summary.current_losing_streak == 0

    assert summary.longest_winning_streak == 5
    assert summary.longest_losing_streak == 0

    assert summary.total_win_streaks == 1
    assert summary.total_loss_streaks == 0


def test_generate_streak_summary_all_losses(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    for i in range(5):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"all-loss-{i}",
            result="LOSS",
            net_pnl=-18.0,
            gross_pnl=-16.0,
            commission=2.0,
            points=-10.0,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_streak_summary()

    assert summary.current_winning_streak == 0
    assert summary.current_losing_streak == 5

    assert summary.longest_winning_streak == 0
    assert summary.longest_losing_streak == 5

    assert summary.total_win_streaks == 0
    assert summary.total_loss_streaks == 1


def test_generate_streak_summary_breakeven_resets_streak(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    trades = [
        ("WIN", 20.0, 22.0, 10.0),
        ("WIN", 20.0, 22.0, 10.0),
        ("BREAKEVEN", 0.0, 2.0, 0.0),
        ("WIN", 20.0, 22.0, 10.0),
    ]

    for i, (result, net, gross, points) in enumerate(trades):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"breakeven-{i}",
            result=result,
            net_pnl=net,
            gross_pnl=gross,
            commission=2.0,
            points=points,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_streak_summary()

    assert summary.current_winning_streak == 1
    assert summary.current_losing_streak == 0

    assert summary.longest_winning_streak == 2
    assert summary.longest_losing_streak == 0

    assert summary.total_win_streaks == 2
    assert summary.total_loss_streaks == 0


def test_generate_streak_summary_filters_by_symbol(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    create_trade(
        repository,
        signal_id="mnq-1",
        symbol="MNQ",
        result="WIN",
        net_pnl=20,
        gross_pnl=22,
        commission=2,
        points=10,
        entry_time=base - timedelta(minutes=5),
        exit_time=base,
    )

    create_trade(
        repository,
        signal_id="mes-1",
        symbol="MES",
        result="LOSS",
        net_pnl=-10,
        gross_pnl=-8,
        commission=2,
        points=-5,
        entry_time=base + timedelta(minutes=1) - timedelta(minutes=5),
        exit_time=base + timedelta(minutes=1),
    )

    summary = analytics_service.generate_streak_summary(symbol="MNQ")

    assert summary.current_winning_streak == 1
    assert summary.current_losing_streak == 0
    assert summary.longest_winning_streak == 1
    assert summary.total_win_streaks == 1

def test_generate_streak_summary_filters_by_side(
    analytics_service,
    repository,
):
    base = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

    create_trade(
        repository,
        signal_id="long-1",
        side="LONG",
        result="WIN",
        net_pnl=20,
        gross_pnl=22,
        commission=2,
        points=10,
        entry_time=base - timedelta(minutes=5),
        exit_time=base,
    )

    create_trade(
        repository,
        signal_id="short-1",
        side="SHORT",
        result="LOSS",
        net_pnl=-10,
        gross_pnl=-8,
        commission=2,
        points=-5,
        entry_time=base + timedelta(minutes=1) - timedelta(minutes=5),
        exit_time=base + timedelta(minutes=1),
    )

    summary = analytics_service.generate_streak_summary(side="LONG")

    assert summary.current_winning_streak == 1
    assert summary.current_losing_streak == 0
    assert summary.longest_winning_streak == 1
    assert summary.total_win_streaks == 1


# ==========================================================
# DRAWDOWN SUMMARY
# ==========================================================


def test_generate_drawdown_summary_returns_zero_values(
    analytics_service,
):
    summary = analytics_service.generate_drawdown_summary()

    assert summary.max_drawdown == 0.0
    assert summary.max_drawdown_percent == 0.0

    assert summary.current_drawdown == 0.0
    assert summary.current_drawdown_percent == 0.0

    assert summary.longest_drawdown_trades == 0
    assert summary.current_drawdown_trades == 0

    assert summary.is_in_drawdown is False


def test_generate_drawdown_summary_with_no_drawdown(
    analytics_service,
    repository,
):
    """
    A continuously rising equity curve should never enter drawdown.
    """

    base = datetime(
        2026,
        7,
        20,
        9,
        30,
        tzinfo=timezone.utc,
    )

    pnl_values = [
        20.0,
        10.0,
        40.0,
        15.0,
    ]

    for i, net_pnl in enumerate(pnl_values):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"no-drawdown-{i}",
            result="WIN",
            net_pnl=net_pnl,
            gross_pnl=net_pnl + 2.0,
            commission=2.0,
            points=net_pnl,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_drawdown_summary()

    assert summary.max_drawdown == 0.0
    assert summary.max_drawdown_percent == 0.0

    assert summary.current_drawdown == 0.0
    assert summary.current_drawdown_percent == 0.0

    assert summary.longest_drawdown_trades == 0
    assert summary.current_drawdown_trades == 0

    assert summary.is_in_drawdown is False


def test_generate_drawdown_summary_ends_in_drawdown(
    analytics_service,
    repository,
):
    """
    Equity sequence:

        20 -> 50 -> 10 -> 0

    Peak equity is 50, so the final drawdown is -50.
    """

    base = datetime(
        2026,
        7,
        20,
        9,
        30,
        tzinfo=timezone.utc,
    )

    trades = [
        ("WIN", 20.0),
        ("WIN", 30.0),
        ("LOSS", -40.0),
        ("LOSS", -10.0),
    ]

    for i, (result, net_pnl) in enumerate(trades):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"ending-drawdown-{i}",
            result=result,
            net_pnl=net_pnl,
            gross_pnl=net_pnl + 2.0,
            commission=2.0,
            points=net_pnl,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_drawdown_summary()

    assert summary.max_drawdown == -50.0
    assert summary.max_drawdown_percent == -100.0

    assert summary.current_drawdown == -50.0
    assert summary.current_drawdown_percent == -100.0

    assert summary.longest_drawdown_trades == 2
    assert summary.current_drawdown_trades == 2

    assert summary.is_in_drawdown is True

def test_generate_drawdown_summary_recovers_from_drawdown(
    analytics_service,
    repository,
):
    """
    Equity sequence:

        20 -> 10 -> 0 -> 40

    The account enters drawdown for two trades and then reaches
    a new equity peak.
    """

    base = datetime(
        2026,
        7,
        20,
        9,
        30,
        tzinfo=timezone.utc,
    )

    trades = [
        ("WIN", 20.0),
        ("LOSS", -10.0),
        ("LOSS", -10.0),
        ("WIN", 40.0),
    ]

    for i, (result, net_pnl) in enumerate(trades):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"drawdown-recovery-{i}",
            result=result,
            net_pnl=net_pnl,
            gross_pnl=net_pnl + 2.0,
            commission=2.0,
            points=net_pnl,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_drawdown_summary()

    assert summary.max_drawdown == -20.0
    assert summary.max_drawdown_percent == -100.0

    assert summary.current_drawdown == 0.0
    assert summary.current_drawdown_percent == 0.0

    assert summary.longest_drawdown_trades == 2
    assert summary.current_drawdown_trades == 0

    assert summary.is_in_drawdown is False

def test_generate_drawdown_summary_handles_multiple_drawdowns(
    analytics_service,
    repository,
):
    """
    Equity sequence:

        20 -> 15 -> 25 -> 10 -> 5 -> 25

    Drawdown periods:

        First drawdown:  1 trade, maximum -5
        Second drawdown: 2 trades, maximum -20

    The final trade recovers to the existing equity peak.
    """

    base = datetime(
        2026,
        7,
        20,
        9,
        30,
        tzinfo=timezone.utc,
    )

    trades = [
        ("WIN", 20.0),
        ("LOSS", -5.0),
        ("WIN", 10.0),
        ("LOSS", -15.0),
        ("LOSS", -5.0),
        ("WIN", 20.0),
    ]

    for i, (result, net_pnl) in enumerate(trades):
        exit_time = base + timedelta(minutes=i)

        create_trade(
            repository,
            signal_id=f"multiple-drawdowns-{i}",
            result=result,
            net_pnl=net_pnl,
            gross_pnl=net_pnl + 2.0,
            commission=2.0,
            points=net_pnl,
            entry_time=exit_time - timedelta(minutes=5),
            exit_time=exit_time,
        )

    summary = analytics_service.generate_drawdown_summary()

    assert summary.max_drawdown == -20.0
    assert summary.max_drawdown_percent == -80.0

    assert summary.current_drawdown == 0.0
    assert summary.current_drawdown_percent == 0.0

    assert summary.longest_drawdown_trades == 2
    assert summary.current_drawdown_trades == 0

    assert summary.is_in_drawdown is False


# ==========================================================
# FILTERS
# ==========================================================


def test_generate_summary_filters_by_side(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary(
        side="SHORT"
    )

    assert summary.total_trades == 1
    assert summary.winning_trades == 1
    assert summary.net_profit == 58.0


def test_generate_summary_filters_by_result(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    summary = analytics_service.generate_summary(
        result="LOSS"
    )

    assert summary.total_trades == 1
    assert summary.losing_trades == 1
    assert summary.net_profit == -22.0


def test_generate_summary_filters_by_symbol(
    repository,
    analytics_service,
):
    seed_sample_trades(repository)

    create_trade(
        repository,
        signal_id="signal-mes",
        result="WIN",
        net_pnl=23.0,
        gross_pnl=25.0,
        commission=2.0,
        points=5.0,
        symbol="MES",
        side="LONG",
    )

    summary = analytics_service.generate_summary(
        symbol="MES"
    )

    assert summary.total_trades == 1
    assert summary.winning_trades == 1
    assert summary.net_profit == 23.0


# ==========================================================
# PROFIT FACTOR EDGE CASES
# ==========================================================


def test_profit_factor_is_none_with_only_wins(
    repository,
    analytics_service,
):
    create_trade(
        repository,
        signal_id="only-win",
        result="WIN",
        net_pnl=38.0,
        gross_pnl=40.0,
        commission=2.0,
        points=20.0,
    )

    summary = analytics_service.generate_summary()

    assert summary.profit_factor is None


def test_profit_factor_is_zero_with_only_losses(
    repository,
    analytics_service,
):
    create_trade(
        repository,
        signal_id="only-loss",
        result="LOSS",
        net_pnl=-22.0,
        gross_pnl=-20.0,
        commission=2.0,
        points=-10.0,
    )

    summary = analytics_service.generate_summary()

    assert summary.profit_factor == 0.0