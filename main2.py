#!/usr/bin/env python3
"""
TradingView Webhook Bot
Receives BUY/SELL/EXIT alerts from TradingView indicator and logs them to SQLite + CSV
"""

import os
import json
import csv
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable is required")

DATABASE_FILE = "signals.db"
CSV_FILE = "trade_signals.csv"
PERFORMANCE_CSV_FILE = "performance_trades.csv"
PERFORMANCE_JSON_FILE = "performance_trades.json"
DUPLICATE_WINDOW_SECONDS = 10

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_database()
    yield
    # Cleanup (if needed) on shutdown

app = FastAPI(
    title="TradingView Webhook Bot",
    description="Receives and logs BUY/SELL/EXIT alerts from TradingView",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic Models
class WebhookPayload(BaseModel):
    secret: str
    source: str
    action: str
    symbol: str
    price: str
    timeframe: str
    exchange: str
    timestamp: str
    
    @validator('action')
    def validate_action(cls, v):
        allowed = {'BUY', 'SELL', 'EXIT'}
        if v.upper() not in allowed:
            raise ValueError(f'action must be one of: {allowed}')
        return v.upper()

class SignalResponse(BaseModel):
    id: int
    received_at: str
    source: str
    action: str
    symbol: str
    price: str
    timeframe: str
    exchange: str
    alert_timestamp: str

class HealthResponse(BaseModel):
    status: str

# Database Functions
def init_database():
    """Initialize SQLite database with signals table"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT NOT NULL,
            source TEXT NOT NULL,
            action TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            exchange TEXT NOT NULL,
            alert_timestamp TEXT NOT NULL,
            raw_payload TEXT NOT NULL,
            duplicate_hash TEXT NOT NULL
        )
    """)
    
    # Index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_received_at 
        ON signals(received_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_duplicate_hash 
        ON signals(duplicate_hash, received_at)
    """)
    
    conn.commit()
    conn.close()
    
    # Initialize CSV file with headers if it doesn't exist
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'received_at', 'source', 'action', 'symbol', 
                'price', 'timeframe', 'exchange', 'alert_timestamp', 'raw_payload'
            ])

def generate_duplicate_hash(action: str, symbol: str, timeframe: str, price: str) -> str:
    """Generate hash for duplicate detection"""
    data = f"{action}:{symbol}:{timeframe}:{price}"
    return hashlib.md5(data.encode()).hexdigest()

def is_duplicate(action: str, symbol: str, timeframe: str, price: str) -> bool:
    """Check if similar signal received within duplicate window"""
    duplicate_hash = generate_duplicate_hash(action, symbol, timeframe, price)
    cutoff_time = (datetime.now(timezone.utc) - 
                   timedelta(seconds=DUPLICATE_WINDOW_SECONDS)).isoformat()
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM signals 
        WHERE duplicate_hash = ? AND received_at > ?
    """, (duplicate_hash, cutoff_time))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def log_to_database(payload: WebhookPayload, raw_payload: str) -> int:
    """Log signal to SQLite database"""
    received_at = datetime.now(timezone.utc).isoformat()
    duplicate_hash = generate_duplicate_hash(
        payload.action, payload.symbol, payload.timeframe, payload.price
    )
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO signals 
        (received_at, source, action, symbol, price, timeframe, exchange, 
         alert_timestamp, raw_payload, duplicate_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        received_at, payload.source, payload.action, payload.symbol,
        payload.price, payload.timeframe, payload.exchange,
        payload.timestamp, raw_payload, duplicate_hash
    ))
    
    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return signal_id

def append_to_csv(signal_id: int, payload: WebhookPayload, raw_payload: str):
    """Append signal to CSV backup"""
    received_at = datetime.now(timezone.utc).isoformat()
    
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            signal_id, received_at, payload.source, payload.action,
            payload.symbol, payload.price, payload.timeframe,
            payload.exchange, payload.timestamp, raw_payload
        ])

# API Endpoints
@app.post("/webhook", status_code=status.HTTP_201_CREATED)
async def receive_webhook(request: Request):
    """
    Receive webhook alerts from TradingView
    Validates secret, checks for duplicates, logs to SQLite and CSV
    """
    try:
        # Parse raw body first for logging
        raw_body = await request.body()
        raw_payload = raw_body.decode('utf-8')
        
        # Parse JSON
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate secret
        if 'secret' not in data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing secret"
            )
        
        if data['secret'] != WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret"
            )
        
        # Validate payload with Pydantic
        try:
            payload = WebhookPayload(**data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {str(e)}"
            )
        
        # Check for duplicates
        if is_duplicate(payload.action, payload.symbol, payload.timeframe, payload.price):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ignored",
                    "reason": "duplicate_detected",
                    "message": "Similar signal received within 10 seconds"
                }
            )
        
        # Log to database
        signal_id = log_to_database(payload, raw_payload)
        
        # Append to CSV
        append_to_csv(signal_id, payload, raw_payload)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "id": signal_id,
                "action": payload.action,
                "symbol": payload.symbol,
                "message": "Signal logged successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")

@app.get("/signals")
async def get_signals(limit: int = 100):
    """
    Retrieve latest signals from database
    Default: 100 most recent signals
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, received_at, source, action, symbol, price, 
               timeframe, exchange, alert_timestamp
        FROM signals
        ORDER BY received_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    signals = [
        {
            "id": row["id"],
            "received_at": row["received_at"],
            "source": row["source"],
            "action": row["action"],
            "symbol": row["symbol"],
            "price": row["price"],
            "timeframe": row["timeframe"],
            "exchange": row["exchange"],
            "alert_timestamp": row["alert_timestamp"]
        }
        for row in rows
    ]
    
    return JSONResponse(content={"signals": signals, "count": len(signals)})



# === Stats + Performance Helpers ===

SYMBOL_MULTIPLIERS = {
    "MNQ1!": 2,
    "NQ1!": 20,
    "MES1!": 5,
    "ES1!": 50,
    "RTY1!": 50,
    "M2K1!": 5,
    "MYM1!": 0.50,
    "YM1!": 5,
}


def get_multiplier(symbol: str) -> float:
    return SYMBOL_MULTIPLIERS.get(symbol.upper(), 1)


@app.get("/stats")
async def get_stats():
    """Return summary statistics of all logged signals"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM signals")
        total_signals = cursor.fetchone()["count"]

        cursor.execute("SELECT action, COUNT(*) as count FROM signals GROUP BY action")
        action_counts = {row["action"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("SELECT symbol, COUNT(*) as count FROM signals GROUP BY symbol")
        symbols = {row["symbol"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("SELECT timeframe, COUNT(*) as count FROM signals GROUP BY timeframe")
        timeframes = {row["timeframe"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT received_at, symbol, action, price, timeframe
            FROM signals
            ORDER BY received_at DESC
            LIMIT 1
        """)
        last = cursor.fetchone()
        conn.close()

        last_signal = None
        if last:
            last_signal = {
                "received_at": last["received_at"],
                "symbol": last["symbol"],
                "action": last["action"],
                "price": last["price"],
                "timeframe": last["timeframe"]
            }

        return {
            "status": "ok",
            "total_signals": total_signals,
            "buy_signals": action_counts.get("BUY", 0),
            "sell_signals": action_counts.get("SELL", 0),
            "exit_signals": action_counts.get("EXIT", 0),
            "symbols": symbols,
            "timeframes": timeframes,
            "last_signal": last_signal
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
    


def write_performance_csv(closed_trades):
    with open(PERFORMANCE_CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trade_id",
            "symbol",
            "timeframe",
            "side",
            "entry_price",
            "exit_price",
            "points",
            "multiplier",
            "pnl",
            "entry_time",
            "exit_time"
        ])

        for idx, trade in enumerate(closed_trades, start=1):
            writer.writerow([
                idx,
                trade["symbol"],
                trade["timeframe"],
                trade["side"],
                trade["entry_price"],
                trade["exit_price"],
                trade["points"],
                trade["multiplier"],
                trade["pnl"],
                trade["entry_time"],
                trade["exit_time"]
            ])



def write_performance_json(closed_trades):
    """
    Save reconstructed trades and summary as JSON.
    """

    pnl_values = [float(t["pnl"]) for t in closed_trades]

    wins = [p for p in pnl_values if p > 0]
    losses = [p for p in pnl_values if p < 0]

    closed_count = len(closed_trades)
    wins_count = len(wins)
    losses_count = len(losses)

    net_profit = round(sum(pnl_values), 2)

    win_rate = (
        round((wins_count / closed_count) * 100, 2)
        if closed_count > 0
        else 0
    )

    trade_list = []

    for idx, trade in enumerate(closed_trades, start=1):

        pnl = float(trade["pnl"])

        result = (
            "WIN"
            if pnl > 0
            else "LOSS"
            if pnl < 0
            else "BREAKEVEN"
        )

        trade_list.append({
            "trade_id": idx,
            "symbol": trade["symbol"],
            "timeframe": trade["timeframe"],
            "side": trade["side"],
            "entry_price": float(trade["entry_price"]),
            "exit_price": float(trade["exit_price"]),
            "points": round(float(trade["points"]), 2),
            "multiplier": trade["multiplier"],
            "pnl": round(pnl, 2),
            "result": result,
            "entry_time": trade["entry_time"],
            "exit_time": trade["exit_time"]
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "closed_trades": closed_count,
            "wins": wins_count,
            "losses": losses_count,
            "win_rate": win_rate,
            "net_profit": net_profit
        },
        "trades": trade_list
    }

    with open(PERFORMANCE_JSON_FILE, "w") as f:
        json.dump(report, f, indent=4)




@app.get("/performance/export")
async def export_performance_csv():
    if not os.path.exists(PERFORMANCE_CSV_FILE):
        write_performance_csv([])

    return FileResponse(
        PERFORMANCE_CSV_FILE,
        media_type="text/csv",
        filename=PERFORMANCE_CSV_FILE
    )

@app.get("/performance/json")
async def export_performance_json():

    if not os.path.exists(PERFORMANCE_JSON_FILE):
        write_performance_json([])

    return FileResponse(
        PERFORMANCE_JSON_FILE,
        media_type="application/json",
        filename=PERFORMANCE_JSON_FILE
    )


@app.get("/performance")
async def get_performance(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = 100
):
    """
    Reconstruct simulated trades from BUY/SELL/EXIT signals
    and calculate forward-test performance.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT id, received_at, source, action, symbol, price,
                   timeframe, exchange, alert_timestamp
            FROM signals
            WHERE 1=1
        """
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)

        query += " ORDER BY received_at ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        open_positions: Dict[str, Dict[str, Any]] = {}
        closed_trades = []

        for row in rows:
            action = row["action"]
            sym = row["symbol"]
            tf = row["timeframe"]
            key = f"{sym}:{tf}"

            try:
                price = float(row["price"])
            except:
                continue

            received_at = row["received_at"]

            if action == "BUY":
                if key not in open_positions:
                    open_positions[key] = {
                        "symbol": sym,
                        "timeframe": tf,
                        "side": "LONG",
                        "entry_price": price,
                        "entry_time": received_at
                    }

            elif action == "SELL":
                if key not in open_positions:
                    open_positions[key] = {
                        "symbol": sym,
                        "timeframe": tf,
                        "side": "SHORT",
                        "entry_price": price,
                        "entry_time": received_at
                    }

            elif action == "EXIT":
                if key in open_positions:
                    position = open_positions.pop(key)
                    entry_price = position["entry_price"]
                    side = position["side"]
                    multiplier = get_multiplier(sym)

                    if side == "LONG":
                        points = price - entry_price
                    else:
                        points = entry_price - price

                    pnl = points * multiplier

                    closed_trades.append({
                        "symbol": sym,
                        "timeframe": tf,
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": price,
                        "points": points,
                        "multiplier": multiplier,
                        "pnl": pnl,
                        "entry_time": position["entry_time"],
                        "exit_time": received_at
                    })

        pnl_values = [t["pnl"] for t in closed_trades]
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p < 0]

        closed_count = len(closed_trades)
        wins_count = len(wins)
        losses_count = len(losses)

        gross_profit = sum(wins)
        gross_loss = sum(losses)
        net_profit = gross_profit + gross_loss

        win_rate = (wins_count / closed_count * 100) if closed_count > 0 else 0
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else None
        average_trade = (net_profit / closed_count) if closed_count > 0 else 0
        average_winner = (gross_profit / wins_count) if wins_count > 0 else 0
        average_loser = (gross_loss / losses_count) if losses_count > 0 else 0
        best_trade = max(pnl_values) if pnl_values else 0
        worst_trade = min(pnl_values) if pnl_values else 0

        by_symbol = {}
        for trade in closed_trades:
            sym = trade["symbol"]
            if sym not in by_symbol:
                by_symbol[sym] = {
                    "closed_trades": 0,
                    "net_profit": 0,
                    "wins": 0
                }

            by_symbol[sym]["closed_trades"] += 1
            by_symbol[sym]["net_profit"] += trade["pnl"]
            if trade["pnl"] > 0:
                by_symbol[sym]["wins"] += 1

        for sym, data in by_symbol.items():
            data["win_rate"] = (
                data["wins"] / data["closed_trades"] * 100
                if data["closed_trades"] > 0 else 0
            )
            del data["wins"]

        open_positions_list = list(open_positions.values())
        write_performance_csv(closed_trades)
        write_performance_json(closed_trades)

        return {
            "status": "ok",
            "summary": {
                "closed_trades": closed_count,
                "open_trades": len(open_positions_list),
                "wins": wins_count,
                "losses": losses_count,
                "win_rate": round(win_rate, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2),
                "net_profit": round(net_profit, 2),
                "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
                "average_trade": round(average_trade, 2),
                "average_winner": round(average_winner, 2),
                "average_loser": round(average_loser, 2),
                "best_trade": round(best_trade, 2),
                "worst_trade": round(worst_trade, 2)
            },
            "by_symbol": by_symbol,
            "open_positions": open_positions_list,
            "closed_trades_list": closed_trades[-limit:]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance error: {str(e)}")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

