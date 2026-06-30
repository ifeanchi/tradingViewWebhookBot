import csv
import sqlite3
import hashlib

DATABASE_FILE = "signals.db"
CSV_FILE = "trade_signals.csv"

def make_hash(source, action, symbol, timeframe, price):
    return hashlib.md5(f"{source}:{action}:{symbol}:{timeframe}:{price}".encode()).hexdigest()

conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        duplicate_hash = make_hash(
            row["source"],
            row["action"],
            row["symbol"],
            row["timeframe"],
            row["price"]
        )

        cursor.execute("""
            INSERT OR IGNORE INTO signals
            (id, received_at, source, action, symbol, price, timeframe, exchange,
             alert_timestamp, raw_payload, duplicate_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(row["id"]),
            row["received_at"],
            row["source"],
            row["action"],
            row["symbol"],
            row["price"],
            row["timeframe"],
            row["exchange"],
            row["alert_timestamp"],
            row["raw_payload"],
            duplicate_hash
        ))

conn.commit()
conn.close()

print("Seed complete.")