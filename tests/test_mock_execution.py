import asyncio

from broker.mock import MockBroker
from config import Settings
from models.signal_models import NormalizedSignal
from risk_engine import RiskEngine
from services.execution_service import ExecutionService


def build_test_settings() -> Settings:
    return Settings(
        broker_mode="mock",
        trading_enabled=True,
        allowed_source="Greedy Futures Strategy",
        allowed_symbol="MNQ1!",
        allowed_timeframe="15",
        max_contracts=1,
        daily_loss_limit=100.0,
        tradovate_env="demo",
        tradovate_username="",
        tradovate_api_password="",
        tradovate_cid="",
        tradovate_sec="",
        tradovate_app_id="GreedyBot",
        tradovate_app_version="1.0",
    )


def test_long_entry_and_close() -> None:
    async def run_test() -> None:
        settings = build_test_settings()
        broker = MockBroker()
        risk_engine = RiskEngine(settings)

        service = ExecutionService(
            broker=broker,
            risk_engine=risk_engine,
        )

        await service.initialize()

        long_signal = NormalizedSignal(
            source="Greedy Futures Strategy",
            action="LONG",
            symbol="MNQ1!",
            timeframe="15",
            price=30_000.00,
            timestamp="2026-07-14T15:00:00Z",
            order_id="Long",
            order_comment="Long",
        )

        entry_result = (
            await service.execute_signal(
                signal=long_signal,
            )
        )

        assert entry_result.status == "filled"
        assert entry_result.fill is not None
        assert entry_result.fill.side == "BUY"

        positions = await broker.get_positions()

        assert len(positions) == 1
        assert positions[0].side == "LONG"
        assert positions[0].quantity == 1

        close_signal = NormalizedSignal(
            source="Greedy Futures Strategy",
            action="CLOSE_ALL",
            symbol="MNQ1!",
            timeframe="15",
            price=30_010.00,
            timestamp="2026-07-14T15:15:00Z",
            order_id="Trail Long",
            order_comment="Trail Long",
        )

        close_result = (
            await service.execute_signal(
                signal=close_signal,
            )
        )

        assert close_result.status == "filled"
        assert close_result.fill is not None
        assert close_result.fill.side == "SELL"

        positions = await broker.get_positions()

        assert positions == []

    asyncio.run(run_test())


def test_rejects_one_minute_signal() -> None:
    async def run_test() -> None:
        settings = build_test_settings()
        broker = MockBroker()
        risk_engine = RiskEngine(settings)

        service = ExecutionService(
            broker=broker,
            risk_engine=risk_engine,
        )

        await service.initialize()

        signal = NormalizedSignal(
            source="Greedy Futures Strategy",
            action="LONG",
            symbol="MNQ1!",
            timeframe="1",
            price=30_000.00,
            timestamp="2026-07-14T15:00:00Z",
        )

        result = await service.execute_signal(
            signal=signal,
        )

        assert result.status == "rejected"
        assert (
            result.risk_code
            == "TIMEFRAME_NOT_ALLOWED"
        )

    asyncio.run(run_test())


def test_rejects_second_contract() -> None:
    async def run_test() -> None:
        settings = build_test_settings()
        broker = MockBroker()
        risk_engine = RiskEngine(settings)

        service = ExecutionService(
            broker=broker,
            risk_engine=risk_engine,
        )

        await service.initialize()

        first_signal = NormalizedSignal(
            source="Greedy Futures Strategy",
            action="LONG",
            symbol="MNQ1!",
            timeframe="15",
            price=30_000.00,
            timestamp="2026-07-14T15:00:00Z",
        )

        second_signal = NormalizedSignal(
            source="Greedy Futures Strategy",
            action="LONG_ADD",
            symbol="MNQ1!",
            timeframe="15",
            price=30_010.00,
            timestamp="2026-07-14T15:15:00Z",
        )

        first_result = (
            await service.execute_signal(
                signal=first_signal,
            )
        )

        second_result = (
            await service.execute_signal(
                signal=second_signal,
            )
        )

        assert first_result.status == "filled"
        assert second_result.status == "rejected"
        assert (
            second_result.risk_code
            == "MAX_CONTRACTS"
        )

    asyncio.run(run_test())