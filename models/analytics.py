from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PerformanceSummary(BaseModel):
    """
    High-level performance statistics for completed trades.
    """

    total_trades: int = Field(
        default=0,
        ge=0,
    )

    winning_trades: int = Field(
        default=0,
        ge=0,
    )

    losing_trades: int = Field(
        default=0,
        ge=0,
    )

    breakeven_trades: int = Field(
        default=0,
        ge=0,
    )

    win_rate: float = 0.0
    loss_rate: float = 0.0
    breakeven_rate: float = 0.0

    gross_profit: float = 0.0
    gross_loss: float = 0.0

    total_commission: float = 0.0
    net_profit: float = 0.0

    average_trade: float = 0.0
    average_winner: float = 0.0
    average_loser: float = 0.0

    largest_winner: float = 0.0
    largest_loser: float = 0.0

    profit_factor: float | None = None
    expectancy: float = 0.0

    average_points: float = 0.0
    total_points: float = 0.0


class DirectionPerformance(BaseModel):
    """
    Performance statistics grouped by trade direction.
    """

    side: str

    total_trades: int = Field(
        default=0,
        ge=0,
    )

    winning_trades: int = Field(
        default=0,
        ge=0,
    )

    losing_trades: int = Field(
        default=0,
        ge=0,
    )

    breakeven_trades: int = Field(
        default=0,
        ge=0,
    )

    win_rate: float = 0.0

    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0

    average_trade: float = 0.0
    average_points: float = 0.0

    profit_factor: float | None = None


class EquityCurvePoint(BaseModel):
    """
    One point in the cumulative trade equity curve.
    """

    trade_number: int = Field(
        ge=1,
    )

    trade_id: str
    timestamp: datetime

    trade_pnl: float
    cumulative_pnl: float

    peak_equity: float
    drawdown: float
    drawdown_percent: float


class DrawdownMetrics(BaseModel):
    """
    Drawdown statistics calculated from the equity curve.
    """

    maximum_drawdown: float = 0.0
    maximum_drawdown_percent: float = 0.0

    current_drawdown: float = 0.0
    current_drawdown_percent: float = 0.0

    peak_equity: float = 0.0
    ending_equity: float = 0.0

    maximum_drawdown_start: datetime | None = None
    maximum_drawdown_end: datetime | None = None

    maximum_drawdown_duration_seconds: float = 0.0


class StreakMetrics(BaseModel):
    """
    Consecutive win and loss statistics.
    """

    longest_winning_streak: int = Field(
        default=0,
        ge=0,
    )

    longest_losing_streak: int = Field(
        default=0,
        ge=0,
    )

    current_winning_streak: int = Field(
        default=0,
        ge=0,
    )

    current_losing_streak: int = Field(
        default=0,
        ge=0,
    )

    current_streak_type: str | None = None
    current_streak_length: int = Field(
        default=0,
        ge=0,
    )

class StreakSummary(BaseModel):
    current_winning_streak: int
    current_losing_streak: int

    longest_winning_streak: int
    longest_losing_streak: int

    total_win_streaks: int
    total_loss_streaks: int
    

class DrawdownSummary(BaseModel):
    max_drawdown: float
    max_drawdown_percent: float

    current_drawdown: float
    current_drawdown_percent: float

    longest_drawdown_trades: int
    current_drawdown_trades: int

    is_in_drawdown: bool


class WeekdayPerformance(BaseModel):
    """
    Performance statistics grouped by weekday.
    """

    weekday: str
    weekday_number: int = Field(
        ge=0,
        le=6,
    )

    total_trades: int = Field(
        default=0,
        ge=0,
    )

    winning_trades: int = Field(
        default=0,
        ge=0,
    )

    losing_trades: int = Field(
        default=0,
        ge=0,
    )

    breakeven_trades: int = Field(
        default=0,
        ge=0,
    )

    win_rate: float = 0.0
    net_profit: float = 0.0
    average_trade: float = 0.0


class TimeBucketPerformance(BaseModel):
    """
    Performance statistics grouped by an hour or session bucket.
    """

    bucket: str

    total_trades: int = Field(
        default=0,
        ge=0,
    )

    winning_trades: int = Field(
        default=0,
        ge=0,
    )

    losing_trades: int = Field(
        default=0,
        ge=0,
    )

    breakeven_trades: int = Field(
        default=0,
        ge=0,
    )

    win_rate: float = 0.0
    net_profit: float = 0.0
    average_trade: float = 0.0


class TradeDurationMetrics(BaseModel):
    """
    Holding-time statistics for completed trades.
    """

    minimum_duration_seconds: float = 0.0
    maximum_duration_seconds: float = 0.0
    average_duration_seconds: float = 0.0
    median_duration_seconds: float = 0.0

    average_winner_duration_seconds: float = 0.0
    average_loser_duration_seconds: float = 0.0


class PerformanceAnalyticsReport(BaseModel):
    """
    Complete analytics response returned by the analytics service.
    """

    generated_at: datetime

    symbol: str | None = None
    side: str | None = None
    result: str | None = None

    summary: PerformanceSummary

    direction_performance: list[DirectionPerformance] = Field(
        default_factory=list,
    )

    equity_curve: list[EquityCurvePoint] = Field(
        default_factory=list,
    )

    drawdown: DrawdownMetrics = Field(
        default_factory=DrawdownMetrics,
    )

    streaks: StreakMetrics = Field(
        default_factory=StreakMetrics,
    )

    weekday_performance: list[WeekdayPerformance] = Field(
        default_factory=list,
    )

    time_bucket_performance: list[TimeBucketPerformance] = Field(
        default_factory=list,
    )

    trade_duration: TradeDurationMetrics = Field(
        default_factory=TradeDurationMetrics,
    )