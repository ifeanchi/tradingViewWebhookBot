from __future__ import annotations

from datetime import datetime
from typing import Any

from models.analytics import (
    DrawdownSummary,    
    EquityCurvePoint,
    PerformanceSummary,
    StreakSummary,
)

from repository.execution_repository import ExecutionRepository


class PerformanceAnalyticsService:
    """
    Calculate trading-performance analytics from completed trades.

    The service reads immutable completed-trade records from
    ExecutionRepository and converts them into analytics models.
    """

    EQUITY_CURVE_LIMIT = 100_000

    def __init__(
        self,
        repository: ExecutionRepository,
    ) -> None:
        self.repository = repository


    def _get_trades(
        self,
        symbol: str | None = None,
        side: str | None = None,
        result: str | None = None,
        limit: int | None = None,
    ):
        
        kwargs = {
        "symbol": symbol,
        "side": side,
        "result": result,
        "order_by": "exit_time",
        "ascending": True,
        }

        if limit is not None:
            kwargs["limit"] = limit
        
        return self.repository.list_trades(
            **kwargs,
        )

    # ==========================================================
    # Performance summary
    # ==========================================================

    def generate_summary(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        result: str | None = None,
    ) -> PerformanceSummary:
        """
        Generate aggregate performance statistics.

        Optional filters may restrict the calculation by:

        - symbol
        - trade side
        - trade result
        """

        trades = self._get_trades(
            symbol=symbol,
            side=side,
            result=result,
        )

        total_trades = len(trades)

        winning_trades = [
            trade
            for trade in trades
            if trade.get("result") == "WIN"
        ]

        losing_trades = [
            trade
            for trade in trades
            if trade.get("result") == "LOSS"
        ]

        breakeven_trades = [
            trade
            for trade in trades
            if trade.get("result") == "BREAKEVEN"
        ]

        net_pnl_values = [
            self._to_float(trade.get("net_pnl"))
            for trade in trades
        ]

        winning_net_pnl_values = [
            self._to_float(trade.get("net_pnl"))
            for trade in winning_trades
        ]

        losing_net_pnl_values = [
        self._to_float(trade.get("net_pnl"))
        for trade in losing_trades
        ]

        winning_gross_pnl_values = [
            self._to_float(trade.get("gross_pnl"))
            for trade in winning_trades
        ]


        losing_gross_pnl_values = [
            self._to_float(trade.get("gross_pnl"))
            for trade in losing_trades
        ]

        gross_profit = sum(winning_gross_pnl_values)
        gross_loss = abs(sum(losing_gross_pnl_values))


        total_commission = sum(
            self._to_float(trade.get("commission"))
            for trade in trades
        )

        net_profit = sum(net_pnl_values)

        total_points = sum(
            self._to_float(trade.get("points"))
            for trade in trades
        )

        largest_winner = (
            max(winning_net_pnl_values)
            if winning_net_pnl_values
            else 0.0
        )

        largest_loser = (
            min(losing_net_pnl_values)
            if losing_net_pnl_values
            else 0.0
        )

        average_trade = self._average(
            net_pnl_values
        )

        average_winner = self._average(
            winning_net_pnl_values
        )

        average_loser = self._average(
            losing_net_pnl_values
        )

        average_points = self._average(
            [
                self._to_float(trade.get("points"))
                for trade in trades
            ]
        )

        return PerformanceSummary(
                total_trades=total_trades,
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                breakeven_trades=len(breakeven_trades),
                win_rate=self._percentage(
                    len(winning_trades),
                    total_trades,
                ),
                loss_rate=self._percentage(
                    len(losing_trades),
                    total_trades,
                ),
                breakeven_rate=self._percentage(
                    len(breakeven_trades),
                    total_trades,
                ),
                gross_profit=self._round_money(
                    gross_profit
                ),
                gross_loss=self._round_money(
                    gross_loss
                ),
                total_commission=self._round_money(
                    total_commission
                ),
                net_profit=self._round_money(
                    net_profit
                ),
                average_trade=self._round_money(
                    average_trade
                ),
                average_winner=self._round_money(
                    average_winner
                ),
                average_loser=self._round_money(
                    average_loser
                ),
                largest_winner=self._round_money(
                    largest_winner
                ),
                largest_loser=self._round_money(
                    largest_loser
                ),
                profit_factor=self._profit_factor(
                    gross_profit=gross_profit,
                    gross_loss=gross_loss,
                ),
                expectancy=self._round_money(
                    average_trade
                ),
                total_points=round(
                    total_points,
                    2,
                ),
                average_points=round(
                    average_points,
                    2,
                ),
            )
    
    def generate_equity_curve(
    self,
    *,
    symbol: str | None = None,
    side: str | None = None,
    result: str | None = None,
    ) -> list[EquityCurvePoint]:
        """
        Generate a cumulative equity curve from completed trades.

        Trades are processed chronologically by exit time.

        Drawdown is represented as a negative value:

            drawdown = cumulative_pnl - peak_equity

        A value of zero means the equity curve is currently at a peak.
        """

        trades = self._get_trades(
            symbol=symbol,
            side=side,
            result=result,
            limit=self.EQUITY_CURVE_LIMIT,
        )

        equity_curve: list[EquityCurvePoint] = []

        cumulative_pnl = 0.0
        peak_equity = 0.0

        for trade_number, trade in enumerate(
            trades,
            start=1,
        ):
            trade_pnl = self._to_float(
                trade.get("net_pnl")
            )

            cumulative_pnl += trade_pnl

            peak_equity = max(
                peak_equity,
                cumulative_pnl,
            )

            drawdown = cumulative_pnl - peak_equity

            drawdown_percent = self._drawdown_percentage(
                drawdown=drawdown,
                peak_equity=peak_equity,
            )

            equity_curve.append(
                EquityCurvePoint(
                    trade_number=trade_number,
                    trade_id=str(trade["trade_id"]),
                    timestamp=self._parse_datetime(
                        trade.get("exit_time")
                    ),
                    trade_pnl=self._round_money(
                        trade_pnl
                    ),
                    cumulative_pnl=self._round_money(
                        cumulative_pnl
                    ),
                    peak_equity=self._round_money(
                        peak_equity
                    ),
                    drawdown=self._round_money(
                        drawdown
                    ),
                    drawdown_percent=round(
                        drawdown_percent,
                        2,
                    ),
                )
            )

        return equity_curve
    


    def generate_streak_summary(
    self,
    symbol: str | None = None,
    side: str | None = None,
    ) -> StreakSummary:
        """
        Generate streak statistics from closed trades.
        """

        trades = self._get_trades(
            symbol=symbol,
            side=side,
        )

        if not trades:
            return StreakSummary(
                current_winning_streak=0,
                current_losing_streak=0,
                longest_winning_streak=0,
                longest_losing_streak=0,
                total_win_streaks=0,
                total_loss_streaks=0,
            )

        current_win = 0
        current_loss = 0

        longest_win = 0
        longest_loss = 0

        total_win_streaks = 0
        total_loss_streaks = 0

        previous_result: str | None = None 

        for trade in trades:
            result = str(trade["result"]).upper()

            if result == "WIN":
                current_win += 1
                current_loss = 0

                if previous_result != "WIN":
                    total_win_streaks += 1

                longest_win = max(longest_win, current_win)

            elif result == "LOSS":
                current_loss += 1
                current_win = 0

                if previous_result != "LOSS":
                    total_loss_streaks += 1

                longest_loss = max(longest_loss, current_loss)

            else:
                current_win = 0
                current_loss = 0

            previous_result = result

        return StreakSummary(
            current_winning_streak=current_win,
            current_losing_streak=current_loss,
            longest_winning_streak=longest_win,
            longest_losing_streak=longest_loss,
            total_win_streaks=total_win_streaks,
            total_loss_streaks=total_loss_streaks,
        )
    


    def generate_drawdown_summary(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        result: str | None = None,
    ) -> DrawdownSummary:
        """
        Generate drawdown statistics from the cumulative equity curve.

        Drawdown values are negative because the equity curve calculates:

            drawdown = cumulative_pnl - peak_equity

        A drawdown value of zero means the equity curve is currently
        at a new or existing peak.
        """

        equity_curve = self.generate_equity_curve(
            symbol=symbol,
            side=side,
            result=result,
        )

        if not equity_curve:
            return DrawdownSummary(
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                current_drawdown=0.0,
                current_drawdown_percent=0.0,
                longest_drawdown_trades=0,
                current_drawdown_trades=0,
                is_in_drawdown=False,
            )

        max_drawdown = 0.0
        max_drawdown_percent = 0.0

        longest_drawdown_trades = 0
        current_drawdown_streak = 0

        for point in equity_curve:
            max_drawdown = min(
                max_drawdown,
                point.drawdown,
            )

            max_drawdown_percent = min(
                max_drawdown_percent,
                point.drawdown_percent,
            )

            if point.drawdown < 0:
                current_drawdown_streak += 1

                longest_drawdown_trades = max(
                    longest_drawdown_trades,
                    current_drawdown_streak,
                )
            else:
                current_drawdown_streak = 0

        latest_point = equity_curve[-1]

        current_drawdown = latest_point.drawdown
        current_drawdown_percent = latest_point.drawdown_percent

        is_in_drawdown = current_drawdown < 0

        return DrawdownSummary(
            max_drawdown=self._round_money(
                max_drawdown
            ),
            max_drawdown_percent=round(
                max_drawdown_percent,
                2,
            ),
            current_drawdown=self._round_money(
                current_drawdown
            ),
            current_drawdown_percent=round(
                current_drawdown_percent,
                2,
            ),
            longest_drawdown_trades=longest_drawdown_trades,
            current_drawdown_trades=current_drawdown_streak,
            is_in_drawdown=is_in_drawdown,
        )



    

    # ==========================================================
    # Trade loading
    # ==========================================================

    def _load_trades(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        result: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Load completed trades using repository filters.
        """

        return self.repository.list_trades(
            symbol=symbol,
            side=side,
            result=result,
            limit=self.EQUITY_CURVE_LIMIT,
        )

    # ==========================================================
    # Calculation helpers
    # ==========================================================

    @staticmethod
    def _average(
        values: list[float],
    ) -> float:
        """
        Return the arithmetic mean or zero for an empty list.
        """

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _percentage(
        value: int,
        total: int,
    ) -> float:
        """
        Convert a count into a percentage.
        """

        if total == 0:
            return 0.0

        return round(
            (value / total) * 100,
            2,
        )

    @staticmethod
    def _drawdown_percentage(
        *,
        drawdown: float,
        peak_equity: float,
    ) -> float:
        """
        Calculate drawdown as a percentage of peak equity.

        Drawdown remains negative so its direction matches the
        monetary drawdown value.

        A zero or negative peak returns zero because there is no
        positive equity peak to use as the percentage denominator.
        """

        if peak_equity <= 0:
            return 0.0

        return (drawdown / peak_equity) * 100

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        """
        Convert repository datetime values into datetime objects.
        """

        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            raise ValueError(
                "Expected trade timestamp to be a datetime "
                f"or ISO-formatted string, received {value!r}"
            )

        normalized_value = value.strip()

        if normalized_value.endswith("Z"):
            normalized_value = normalized_value[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(normalized_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid trade timestamp: {value!r}"
            ) from exc

    @staticmethod
    def _profit_factor(
        *,
        gross_profit: float,
        gross_loss: float,
    ) -> float | None:
        """
        Calculate gross profit divided by absolute gross loss.

        Returns:
            None when there are no winning or losing trades.
            None when there are profits but no losses.
            0.0 when there are losses but no profits.
        """

        absolute_gross_loss = abs(gross_loss)

        if gross_profit == 0 and absolute_gross_loss == 0:
            return None

        if absolute_gross_loss == 0:
            return None

        if gross_profit == 0:
            return 0.0

        return round(
            gross_profit / absolute_gross_loss,
            2,
        )

    @staticmethod
    def _round_money(
        value: float,
    ) -> float:
        """
        Round monetary values to two decimal places.
        """

        return round(value, 2)

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:
        """
        Safely convert repository values into floats.
        """

        if value is None:
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Unable to convert analytics value to float: {value!r}"
            ) from exc