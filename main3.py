#!/usr/bin/env python3
"""
TradingView Webhook Bot - Greedy Strategy Edition
Receives LONG/SHORT/LONG_ADD/SHORT_ADD/CLOSE_ALL alerts from TradingView indicator
Logs them to SQLite + CSV and calculates forward-test performance with position stacking.
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

app = FastAPI(
    title="TradingView Webhook Bot - Greedy Strategy",
    description="Receives and logs Greedy Strategy alerts from TradingView",
    version="2.0.0",
    lifespan=lifespan
)

# === Pydantic Models ===

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
        # Updated for Greedy Strategy Indicator
        allowed = {'LONG', 'SHORT', 'LONG_ADD', 'SHORT_ADD', 'CLOSE_ALL'}
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

# === Database Functions ===

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
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON signals(received_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_hash ON signals(duplicate_hash, received_at)")
    
    conn.commit()
    conn.close()
    
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'received_at', 'source', 'action', 'symbol', 
                'price', 'timeframe', 'exchange', 'alert_timestamp', 'raw_payload'
            ])

def generate_duplicate_hash(action: str, symbol: str, timeframe: str, price: str) -> str:
    data = f"{action}:{symbol}:{timeframe}:{price}"
    return hashlib.md5(data.encode()).hexdigest()

def is_duplicate(action: str, symbol: str, timeframe: str, price: str) -> bool:
    duplicate_hash = generate_duplicate_hash(action, symbol, timeframe, price)
    cutoff_time = (datetime.now(timezone.utc) - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)).isoformat()
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM signals WHERE duplicate_hash = ? AND received_at > ?", (duplicate_hash, cutoff_time))
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def log_to_database(payload: WebhookPayload, raw_payload: str) -> int:
    received_at = datetime.now(timezone.utc).isoformat()
    duplicate_hash = generate_duplicate_hash(payload.action, payload.symbol, payload.timeframe, payload.price)
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO signals 
        (received_at, source, action, symbol, price, timeframe, exchange, alert_timestamp, raw_payload, duplicate_hash)
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
    received_at = datetime.now(timezone.utc).isoformat()
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            signal_id, received_at, payload.source, payload.action,
            payload.symbol, payload.price, payload.timeframe,
            payload.exchange, payload.timestamp, raw_payload
        ])

# === API Endpoints ===

@app.post("/webhook", status_code=status.HTTP_201_CREATED)
async def receive_webhook(request: Request):
    try:
        raw_body = await request.body()
        raw_payload = raw_body.decode('utf-8')
        
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        if data.get('secret') != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")
        
        try:
            payload = WebhookPayload(**data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
        
        if is_duplicate(payload.action, payload.symbol, payload.timeframe, payload.price):
            return JSONResponse(status_code=200, content={"status": "ignored", "reason": "duplicate_detected"})
        
        signal_id = log_to_database(payload, raw_payload)
        append_to_csv(signal_id, payload, raw_payload)
        
        return JSONResponse(status_code=201, content={
            "status": "success", "id": signal_id, "action": payload.action,
            "symbol": payload.symbol, "message": "Signal logged successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")

@app.get("/signals")
async def get_signals(limit: int = 100):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY received_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return {"signals": [dict(row) for row in rows], "count": len(rows)}

# === Stats + Performance Helpers ===

# Futures multipliers (USD per point)
SYMBOL_MULTIPLIERS = {
    "MNQ1!": 2, "NQ1!": 20, "MES1!": 5, "ES1!": 50, 
    "RTY1!": 50, "M2K1!": 5, "MYM1!": 0.50, "YM1!": 5,
}

def get_multiplier(symbol: str) -> float:
    return SYMBOL_MULTIPLIERS.get(symbol.upper(), 1)

@app.get("/stats")
async def get_stats():
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

        cursor.execute("SELECT * FROM signals ORDER BY received_at DESC LIMIT 1")
        last = cursor.fetchone()
        conn.close()

        return {
            "status": "ok",
            "total_signals": total_signals,
            "long_signals": action_counts.get("LONG", 0),
            "short_signals": action_counts.get("SHORT", 0),
            "long_add_signals": action_counts.get("LONG_ADD", 0),
            "short_add_signals": action_counts.get("SHORT_ADD", 0),
            "close_all_signals": action_counts.get("CLOSE_ALL", 0),
            "symbols": symbols,
            "last_signal": dict(last) if last else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

def write_performance_csv(closed_trades):
    with open(PERFORMANCE_CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trade_id", "symbol", "timeframe", "side", "contracts",
            "entry_price", "exit_price", "points", "multiplier", "pnl",
            "entry_time", "exit_time"
        ])
        for idx, trade in enumerate(closed_trades, start=1):
            writer.writerow([
                idx, trade["symbol"], trade["timeframe"], trade["side"], trade["contracts"],
                trade["entry_price"], trade["exit_price"], trade["points"],
                trade["multiplier"], trade["pnl"], trade["entry_time"], trade["exit_time"]
            ])

def write_performance_json(closed_trades):
    pnl_values = [float(t["pnl"]) for t in closed_trades]
    wins = [p for p in pnl_values if p > 0]
    losses = [p for p in pnl_values if p < 0]

    closed_count = len(closed_trades)
    net_profit = round(sum(pnl_values), 2)
    win_rate = round((len(wins) / closed_count) * 100, 2) if closed_count > 0 else 0

    trade_list = []
    for idx, trade in enumerate(closed_trades, start=1):
        pnl = float(trade["pnl"])
        result = "WIN" if pnl > 0 else "LOSS" if pnl < 0 else "BREAKEVEN"
        trade_list.append({
            "trade_id": idx, "symbol": trade["symbol"], "timeframe": trade["timeframe"],
            "side": trade["side"], "contracts": trade["contracts"],
            "entry_price": float(trade["entry_price"]), "exit_price": float(trade["exit_price"]),
            "points": round(float(trade["points"]), 2), "multiplier": trade["multiplier"],
            "pnl": round(pnl, 2), "result": result,
            "entry_time": trade["entry_time"], "exit_time": trade["exit_time"]
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "closed_trades": closed_count, "wins": len(wins), "losses": len(losses),
            "win_rate": win_rate, "net_profit": net_profit
        },
        "trades": trade_list
    }

    with open(PERFORMANCE_JSON_FILE, "w") as f:
        json.dump(report, f, indent=4)

@app.get("/performance/export")
async def export_performance_csv():
    if not os.path.exists(PERFORMANCE_CSV_FILE): write_performance_csv([])
    return FileResponse(PERFORMANCE_CSV_FILE, media_type="text/csv", filename=PERFORMANCE_CSV_FILE)

@app.get("/performance/json")
async def export_performance_json():
    if not os.path.exists(PERFORMANCE_JSON_FILE): write_performance_json([])
    return FileResponse(PERFORMANCE_JSON_FILE, media_type="application/json", filename=PERFORMANCE_JSON_FILE)

@app.get("/performance")
async def get_performance(symbol: Optional[str] = None, timeframe: Optional[str] = None, limit: int = 100):
    """
    Reconstruct simulated trades handling GREEDY STACKING (LONG_ADD/SHORT_ADD).
    Calculates average entry price and multiplies PnL by total stacked contracts.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM signals WHERE 1=1"
        params = []
        if symbol: query += " AND symbol = ?"; params.append(symbol)
        if timeframe: query += " AND timeframe = ?"; params.append(timeframe)
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

            # --- LONG ENTRIES & STACKING ---
            if action in ["LONG", "LONG_ADD"]:
                if key not in open_positions:
                    open_positions[key] = {
                        "symbol": sym, "timeframe": tf, "side": "LONG",
                        "contracts": 0, "total_entry_value": 0.0, "entry_time": received_at
                    }
                elif open_positions[key]["side"] != "LONG":
                    # Force close SHORT if flipped without CLOSE_ALL signal
                    pos = open_positions.pop(key)
                    contracts = pos["contracts"]
                    avg_entry = pos["total_entry_value"] / contracts
                    mult = get_multiplier(sym)
                    pnl = (avg_entry - price) * contracts * mult
                    closed_trades.append({
                        "symbol": sym, "timeframe": tf, "side": "SHORT", "contracts": contracts,
                        "entry_price": round(avg_entry, 4), "exit_price": price,
                        "points": round(avg_entry - price, 4), "multiplier": mult,
                        "pnl": round(pnl, 2), "entry_time": pos["entry_time"], "exit_time": received_at
                    })
                    open_positions[key] = {
                        "symbol": sym, "timeframe": tf, "side": "LONG",
                        "contracts": 0, "total_entry_value": 0.0, "entry_time": received_at
                    }
                
                open_positions[key]["contracts"] += 1
                open_positions[key]["total_entry_value"] += price

            # --- SHORT ENTRIES & STACKING ---
            elif action in ["SHORT", "SHORT_ADD"]:
                if key not in open_positions:
                    open_positions[key] = {
                        "symbol": sym, "timeframe": tf, "side": "SHORT",
                        "contracts": 0, "total_entry_value": 0.0, "entry_time": received_at
                    }
                elif open_positions[key]["side"] != "SHORT":
                    # Force close LONG if flipped without CLOSE_ALL signal
                    pos = open_positions.pop(key)
                    contracts = pos["contracts"]
                    avg_entry = pos["total_entry_value"] / contracts
                    mult = get_multiplier(sym)
                    pnl = (price - avg_entry) * contracts * mult
                    closed_trades.append({
                        "symbol": sym, "timeframe": tf, "side": "LONG", "contracts": contracts,
                        "entry_price": round(avg_entry, 4), "exit_price": price,
                        "points": round(price - avg_entry, 4), "multiplier": mult,
                        "pnl": round(pnl, 2), "entry_time": pos["entry_time"], "exit_time": received_at
                    })
                    open_positions[key] = {
                        "symbol": sym, "timeframe": tf, "side": "SHORT",
                        "contracts": 0, "total_entry_value": 0.0, "entry_time": received_at
                    }

                open_positions[key]["contracts"] += 1
                open_positions[key]["total_entry_value"] += price

            # --- EXITS (CLOSE_ALL) ---
            elif action == "CLOSE_ALL":
                if key in open_positions:
                    position = open_positions.pop(key)
                    contracts = position["contracts"]
                    avg_entry = position["total_entry_value"] / contracts
                    side = position["side"]
                    multiplier = get_multiplier(sym)

                    if side == "LONG":
                        points = price - avg_entry
                    else:
                        points = avg_entry - price

                    # PnL = Points * Total Stacked Contracts * Futures Multiplier
                    pnl = points * contracts * multiplier

                    closed_trades.append({
                        "symbol": sym, "timeframe": tf, "side": side, "contracts": contracts,
                        "entry_price": round(avg_entry, 4), "exit_price": price,
                        "points": round(points, 4), "multiplier": multiplier,
                        "pnl": round(pnl, 2), "entry_time": position["entry_time"], "exit_time": received_at
                    })

        # === Calculate Summary Stats ===
        pnl_values = [t["pnl"] for t in closed_trades]
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p < 0]

        closed_count = len(closed_trades)
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        net_profit = gross_profit + gross_loss

        win_rate = (len(wins) / closed_count * 100) if closed_count > 0 else 0
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else None
        
        by_symbol = {}
        for trade in closed_trades:
            sym = trade["symbol"]
            if sym not in by_symbol: by_symbol[sym] = {"closed_trades": 0, "net_profit": 0, "wins": 0}
            by_symbol[sym]["closed_trades"] += 1
            by_symbol[sym]["net_profit"] += trade["pnl"]
            if trade["pnl"] > 0: by_symbol[sym]["wins"] += 1

        for sym, data in by_symbol.items():
            data["win_rate"] = (data["wins"] / data["closed_trades"] * 100) if data["closed_trades"] > 0 else 0
            del data["wins"]

        open_positions_list = list(open_positions.values())
        write_performance_csv(closed_trades)
        write_performance_json(closed_trades)

        return {
            "status": "ok",
            "summary": {
                "closed_trades": closed_count, "open_trades": len(open_positions_list),
                "wins": len(wins), "losses": len(losses), "win_rate": round(win_rate, 2),
                "gross_profit": round(gross_profit, 2), "gross_loss": round(gross_loss, 2),
                "net_profit": round(net_profit, 2),
                "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
                "best_trade": round(max(pnl_values), 2) if pnl_values else 0,
                "worst_trade": round(min(pnl_values), 2) if pnl_values else 0
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