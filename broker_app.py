from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from broker.mock import MockBroker
from config import settings
from models.signal_models import NormalizedSignal
from repository import ExecutionRepository
from risk_engine import RiskEngine
from services.execution_service import ExecutionService


EXECUTION_DATABASE_PATH = Path("execution.db")


class TestSignalRequest(BaseModel):
    source: str
    action: str
    symbol: str
    timeframe: str
    price: float = Field(gt=0)
    timestamp: str
    order_id: str | None = None
    order_comment: str | None = None


execution_repository = ExecutionRepository(
    database_path=EXECUTION_DATABASE_PATH,
)

mock_broker = MockBroker()
risk_engine = RiskEngine(settings)

execution_service = ExecutionService(
    broker=mock_broker,
    risk_engine=risk_engine,
    repository=execution_repository,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await execution_service.initialize()
    yield


app = FastAPI(
    title="Greedy Mock Broker API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/broker/health")
async def broker_health() -> dict:
    execution_summary = (
        execution_repository.get_summary()
    )

    return {
        "status": "ok",
        "broker": "mock",
        "broker_mode": settings.broker_mode,
        "configured_trading_enabled": (
            settings.trading_enabled
        ),
        "allowed_source": settings.allowed_source,
        "allowed_symbol": settings.allowed_symbol,
        "allowed_timeframe": (
            settings.allowed_timeframe
        ),
        "max_contracts": settings.max_contracts,
        "daily_loss_limit": (
            settings.daily_loss_limit
        ),
        "execution_database": str(
            EXECUTION_DATABASE_PATH
        ),
        "execution_summary": execution_summary,
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
                "average_price": (
                    position.average_price
                ),
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


@app.get("/broker/execution-summary")
async def broker_execution_summary() -> dict:
    return {
        "status": "ok",
        "database": str(
            EXECUTION_DATABASE_PATH
        ),
        "summary": (
            execution_repository.get_summary()
        ),
    }


@app.get("/broker/execution-orders")
async def broker_execution_orders(
    symbol: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> dict:
    orders = execution_repository.list_orders(
        symbol=symbol,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(orders),
        "orders": orders,
    }


@app.get("/broker/execution-fills")
async def broker_execution_fills(
    symbol: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> dict:
    fills = execution_repository.list_fills(
        symbol=symbol,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(fills),
        "fills": fills,
    }


@app.get("/broker/risk-events")
async def broker_risk_events(
    decision: str | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> dict:
    risk_events = (
        execution_repository.list_risk_events(
            decision=decision,
            limit=limit,
        )
    )

    return {
        "status": "ok",
        "count": len(risk_events),
        "risk_events": risk_events,
    }


@app.get("/broker/audit-events")
async def broker_audit_events(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> dict:
    audit_events = (
        execution_repository.list_audit_events(
            limit=limit,
        )
    )

    return {
        "status": "ok",
        "count": len(audit_events),
        "audit_events": audit_events,
    }


@app.post("/broker/test-signal")
async def broker_test_signal(
    payload: TestSignalRequest,
    execution_enabled: bool = Query(
        default=False
    ),
    current_daily_pnl: float = Query(
        default=0.0
    ),
) -> dict:
    try:
        signal = NormalizedSignal.from_dict(
            payload.model_dump()
        )

        result = (
            await execution_service.execute_signal(
                signal=signal,
                current_daily_pnl=(
                    current_daily_pnl
                ),
                execution_enabled=(
                    execution_enabled
                ),
            )
        )

        fill_payload = None

        if result.fill is not None:
            fill_payload = {
                "fill_id": result.fill.fill_id,
                "order_id": result.fill.order_id,
                "account_id": (
                    result.fill.account_id
                ),
                "symbol": result.fill.symbol,
                "side": result.fill.side,
                "quantity": result.fill.quantity,
                "fill_price": (
                    result.fill.fill_price
                ),
                "filled_at": (
                    result.fill.filled_at
                ),
            }

        return {
            "status": result.status,
            "signal_action": (
                result.signal_action
            ),
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
        repository=execution_repository,
    )

    await execution_service.initialize()

    return {
        "status": "ok",
        "message": (
            "Mock broker state reset. "
            "Execution history was preserved."
        ),
        "execution_summary": (
            execution_repository.get_summary()
        ),
    }