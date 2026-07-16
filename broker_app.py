from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from broker.mock import MockBroker
from config import settings
from models.signal_models import NormalizedSignal
from risk_engine import RiskEngine
from services.execution_service import ExecutionService
from contextlib import asynccontextmanager



class TestSignalRequest(BaseModel):
    source: str
    action: str
    symbol: str
    timeframe: str
    price: float = Field(gt=0)
    timestamp: str
    order_id: str | None = None
    order_comment: str | None = None


mock_broker = MockBroker()
risk_engine = RiskEngine(settings)

execution_service = ExecutionService(
    broker=mock_broker,
    risk_engine=risk_engine,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await execution_service.initialize()
    yield


app = FastAPI(
    title="Greedy Mock Broker API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/broker/health")
async def broker_health() -> dict:
    return {
        "status": "ok",
        "broker": "mock",
        "broker_mode": settings.broker_mode,
        "configured_trading_enabled": settings.trading_enabled,
        "allowed_source": settings.allowed_source,
        "allowed_symbol": settings.allowed_symbol,
        "allowed_timeframe": settings.allowed_timeframe,
        "max_contracts": settings.max_contracts,
        "daily_loss_limit": settings.daily_loss_limit,
    }


@app.get("/broker/accounts")
async def broker_accounts() -> dict:
    accounts = await mock_broker.get_accounts()

    return {
        "status": "ok",
        "accounts": [
            {
                "account_id": account.account_id,
                "name": account.name,
                "environment": account.environment,
                "balance": account.balance,
                "active": account.active,
            }
            for account in accounts
        ],
    }


@app.get("/broker/positions")
async def broker_positions() -> dict:
    positions = await mock_broker.get_positions()

    return {
        "status": "ok",
        "positions": [
            {
                "account_id": position.account_id,
                "symbol": position.symbol,
                "side": position.side,
                "quantity": position.quantity,
                "average_price": position.average_price,
            }
            for position in positions
        ],
    }


@app.get("/broker/orders")
async def broker_orders() -> dict:
    orders = await mock_broker.get_orders()

    return {
        "status": "ok",
        "orders": [
            {
                "order_id": order.order_id,
                "account_id": order.account_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "order_type": order.order_type,
                "status": order.status,
                "submitted_at": order.submitted_at,
            }
            for order in orders
        ],
    }


@app.post("/broker/test-signal")
async def broker_test_signal(
    payload: TestSignalRequest,
    execution_enabled: bool = Query(default=False),
    current_daily_pnl: float = Query(default=0.0),
) -> dict:
    try:
        signal = NormalizedSignal.from_dict(
            payload.model_dump()
        )

        result = await execution_service.execute_signal(
            signal=signal,
            current_daily_pnl=current_daily_pnl,
            execution_enabled=execution_enabled,
        )

        fill_payload = None

        if result.fill is not None:
            fill_payload = {
                "fill_id": result.fill.fill_id,
                "order_id": result.fill.order_id,
                "account_id": result.fill.account_id,
                "symbol": result.fill.symbol,
                "side": result.fill.side,
                "quantity": result.fill.quantity,
                "fill_price": result.fill.fill_price,
                "filled_at": result.fill.filled_at,
            }

        return {
            "status": result.status,
            "signal_action": result.signal_action,
            "risk_code": result.risk_code,
            "message": result.message,
            "fill": fill_payload,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@app.post("/broker/reset")
async def broker_reset() -> dict:
    global mock_broker
    global risk_engine
    global execution_service

    mock_broker = MockBroker()
    risk_engine = RiskEngine(settings)

    execution_service = ExecutionService(
        broker=mock_broker,
        risk_engine=risk_engine,
    )

    await execution_service.initialize()

    return {
        "status": "ok",
        "message": "Mock broker state reset.",
    }