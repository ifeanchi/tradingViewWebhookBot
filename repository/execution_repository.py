from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now_iso() -> str:
    """
    Return a timezone-aware UTC timestamp in ISO-8601 format.
    """
    return datetime.now(timezone.utc).isoformat()


class ExecutionRepository:
    """
    SQLite persistence layer for broker execution data.

    Stores:
    - orders
    - fills
    - positions
    - completed trades
    - risk events
    - execution audit events

    This repository is broker-independent. It can be used by:
    - MockBroker
    - TradovateBroker
    - replay utilities
    - execution dashboards
    """

    def __init__(
        self,
        database_path: str | Path = "execution.db",
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._write_lock = threading.RLock()

        self.initialize()

    @contextmanager
    def connection(
        self,
    ) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON;"
            )
            connection.execute(
                "PRAGMA busy_timeout = 30000;"
            )

            yield connection

        finally:
            connection.close()

    def initialize(self) -> None:
        """
        Create all execution tables and indexes.
        """

        schema = """
        CREATE TABLE IF NOT EXISTS execution_orders (
            order_id TEXT PRIMARY KEY,
            signal_id TEXT,
            broker_name TEXT NOT NULL,
            broker_order_id TEXT,
            source TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT,
            action TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            requested_price REAL,
            status TEXT NOT NULL,
            order_comment TEXT,
            submitted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            raw_payload TEXT
        );

        CREATE TABLE IF NOT EXISTS execution_fills (
            fill_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            broker_fill_id TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            fill_price REAL NOT NULL,
            commission REAL NOT NULL DEFAULT 0,
            filled_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            raw_payload TEXT,

            FOREIGN KEY(order_id)
                REFERENCES execution_orders(order_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS execution_positions (
            symbol TEXT PRIMARY KEY,
            broker_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            side TEXT NOT NULL,
            average_price REAL NOT NULL,
            realized_pnl REAL NOT NULL DEFAULT 0,
            unrealized_pnl REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            opened_at TEXT,
            closed_at TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS execution_risk_events (
            risk_event_id TEXT PRIMARY KEY,
            signal_id TEXT,
            order_id TEXT,
            source TEXT,
            symbol TEXT,
            timeframe TEXT,
            action TEXT,
            risk_code TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT,
            daily_pnl REAL,
            requested_quantity INTEGER,
            created_at TEXT NOT NULL,
            raw_payload TEXT,

            FOREIGN KEY(order_id)
                REFERENCES execution_orders(order_id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS execution_audit_events (
            audit_event_id TEXT PRIMARY KEY,
            signal_id TEXT,
            order_id TEXT,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT,

            FOREIGN KEY(order_id)
                REFERENCES execution_orders(order_id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS execution_trades (
            trade_id TEXT PRIMARY KEY,

            signal_id TEXT,
            order_id TEXT,

            broker_name TEXT,
            source TEXT,

            symbol TEXT NOT NULL,
            timeframe TEXT,

            side TEXT NOT NULL,

            contracts INTEGER NOT NULL,

            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,

            points REAL NOT NULL,

            multiplier REAL NOT NULL DEFAULT 1,

            gross_pnl REAL NOT NULL,
            commission REAL NOT NULL DEFAULT 0,

            net_pnl REAL NOT NULL,

            result TEXT NOT NULL,

            entry_time TEXT NOT NULL,
            exit_time TEXT NOT NULL,

            duration_seconds REAL NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY(order_id)
                REFERENCES execution_orders(order_id)
                ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS
            idx_execution_orders_created_at
        ON execution_orders(created_at DESC);

        CREATE INDEX IF NOT EXISTS
            idx_execution_orders_symbol
        ON execution_orders(symbol);

        CREATE INDEX IF NOT EXISTS
            idx_execution_orders_status
        ON execution_orders(status);

        CREATE INDEX IF NOT EXISTS
            idx_execution_orders_signal_id
        ON execution_orders(signal_id);

        CREATE INDEX IF NOT EXISTS
            idx_execution_fills_order_id
        ON execution_fills(order_id);

        CREATE INDEX IF NOT EXISTS
            idx_execution_fills_filled_at
        ON execution_fills(filled_at DESC);

        CREATE INDEX IF NOT EXISTS
            idx_execution_risk_created_at
        ON execution_risk_events(created_at DESC);

        CREATE INDEX IF NOT EXISTS
            idx_execution_risk_code
        ON execution_risk_events(risk_code);

        CREATE INDEX IF NOT EXISTS
            idx_execution_audit_created_at
        ON execution_audit_events(created_at DESC);

        CREATE INDEX IF NOT EXISTS
            idx_execution_audit_order_id
        ON execution_audit_events(order_id);

        CREATE INDEX IF NOT EXISTS
            idx_execution_trades_exit_time
        ON execution_trades(exit_time DESC);

        CREATE INDEX IF NOT EXISTS
            idx_execution_trades_symbol
        ON execution_trades(symbol);

        CREATE INDEX IF NOT EXISTS
            idx_execution_trades_result
        ON execution_trades(result);

        CREATE INDEX IF NOT EXISTS
            idx_execution_trades_side
        ON execution_trades(side);

        """

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    "PRAGMA journal_mode = WAL;"
                )
                connection.executescript(schema)
                connection.commit()

    @staticmethod
    def _json_dump(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        return json.dumps(
            value,
            default=str,
            separators=(",", ":"),
        )

    @staticmethod
    def _row_to_dict(
        row: sqlite3.Row | None,
    ) -> dict[str, Any] | None:
        if row is None:
            return None

        return dict(row)

    # =========================================================
    # Orders
    # =========================================================

    def create_order(
        self,
        *,
        signal_id: str | None,
        broker_name: str,
        source: str,
        symbol: str,
        timeframe: str | None,
        action: str,
        side: str,
        quantity: int,
        requested_price: float | None,
        status: str = "CREATED",
        order_type: str = "MARKET",
        broker_order_id: str | None = None,
        order_comment: str | None = None,
        submitted_at: str | None = None,
        raw_payload: Any = None,
        order_id: str | None = None,
    ) -> dict[str, Any]:
        if quantity < 1:
            raise ValueError(
                "Order quantity must be at least 1."
            )

        generated_order_id = (
            order_id or str(uuid.uuid4())
        )

        now = utc_now_iso()

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_orders (
                        order_id,
                        signal_id,
                        broker_name,
                        broker_order_id,
                        source,
                        symbol,
                        timeframe,
                        action,
                        side,
                        order_type,
                        quantity,
                        requested_price,
                        status,
                        order_comment,
                        submitted_at,
                        created_at,
                        updated_at,
                        raw_payload
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        generated_order_id,
                        signal_id,
                        broker_name,
                        broker_order_id,
                        source,
                        symbol,
                        timeframe,
                        action.upper(),
                        side.upper(),
                        order_type.upper(),
                        quantity,
                        requested_price,
                        status.upper(),
                        order_comment,
                        submitted_at,
                        now,
                        now,
                        self._json_dump(raw_payload),
                    ),
                )

                connection.commit()

        order = self.get_order(generated_order_id)

        if order is None:
            raise RuntimeError(
                "Order was created but could not be read."
            )

        return order

    def update_order_status(
        self,
        order_id: str,
        status: str,
        *,
        broker_order_id: str | None = None,
        submitted_at: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()

        assignments = [
            "status = ?",
            "updated_at = ?",
        ]

        values: list[Any] = [
            status.upper(),
            now,
        ]

        if broker_order_id is not None:
            assignments.append(
                "broker_order_id = ?"
            )
            values.append(broker_order_id)

        if submitted_at is not None:
            assignments.append(
                "submitted_at = ?"
            )
            values.append(submitted_at)

        values.append(order_id)

        with self._write_lock:
            with self.connection() as connection:
                cursor = connection.execute(
                    f"""
                    UPDATE execution_orders
                    SET {", ".join(assignments)}
                    WHERE order_id = ?
                    """,
                    values,
                )

                if cursor.rowcount == 0:
                    raise KeyError(
                        f"Order not found: {order_id}"
                    )

                connection.commit()

        updated_order = self.get_order(order_id)

        if updated_order is None:
            raise RuntimeError(
                "Order was updated but could not be read."
            )

        return updated_order

    def get_order(
        self,
        order_id: str,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_orders
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_orders(
        self,
        *,
        symbol: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError(
                "Limit must be at least 1."
            )

        conditions: list[str] = []
        values: list[Any] = []

        if symbol is not None:
            conditions.append("symbol = ?")
            values.append(symbol)

        if status is not None:
            conditions.append("status = ?")
            values.append(status.upper())

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        values.append(limit)

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM execution_orders
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                values,
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # Fills
    # =========================================================

    def create_fill(
        self,
        *,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        fill_price: float,
        filled_at: str | None = None,
        commission: float = 0.0,
        broker_fill_id: str | None = None,
        raw_payload: Any = None,
        fill_id: str | None = None,
    ) -> dict[str, Any]:
        if quantity < 1:
            raise ValueError(
                "Fill quantity must be at least 1."
            )

        if self.get_order(order_id) is None:
            raise KeyError(
                f"Cannot create fill. "
                f"Order not found: {order_id}"
            )

        generated_fill_id = (
            fill_id or str(uuid.uuid4())
        )

        now = utc_now_iso()
        fill_timestamp = filled_at or now

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_fills (
                        fill_id,
                        order_id,
                        broker_fill_id,
                        symbol,
                        side,
                        quantity,
                        fill_price,
                        commission,
                        filled_at,
                        created_at,
                        raw_payload
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        generated_fill_id,
                        order_id,
                        broker_fill_id,
                        symbol,
                        side.upper(),
                        quantity,
                        fill_price,
                        commission,
                        fill_timestamp,
                        now,
                        self._json_dump(raw_payload),
                    ),
                )

                connection.execute(
                    """
                    UPDATE execution_orders
                    SET status = ?,
                        updated_at = ?
                    WHERE order_id = ?
                    """,
                    (
                        "FILLED",
                        now,
                        order_id,
                    ),
                )

                connection.commit()

        fill = self.get_fill(generated_fill_id)

        if fill is None:
            raise RuntimeError(
                "Fill was created but could not be read."
            )

        return fill

    def get_fill(
        self,
        fill_id: str,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_fills
                WHERE fill_id = ?
                """,
                (fill_id,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_fills(
        self,
        *,
        order_id: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError(
                "Limit must be at least 1."
            )

        conditions: list[str] = []
        values: list[Any] = []

        if order_id is not None:
            conditions.append("order_id = ?")
            values.append(order_id)

        if symbol is not None:
            conditions.append("symbol = ?")
            values.append(symbol)

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        values.append(limit)

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM execution_fills
                {where_clause}
                ORDER BY filled_at DESC
                LIMIT ?
                """,
                values,
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # Positions
    # =========================================================

    def upsert_position(
        self,
        *,
        symbol: str,
        broker_name: str,
        quantity: int,
        side: str,
        average_price: float,
        status: str,
        realized_pnl: float = 0.0,
        unrealized_pnl: float = 0.0,
        opened_at: str | None = None,
        closed_at: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_positions (
                        symbol,
                        broker_name,
                        quantity,
                        side,
                        average_price,
                        realized_pnl,
                        unrealized_pnl,
                        status,
                        opened_at,
                        closed_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(symbol)
                    DO UPDATE SET
                        broker_name = excluded.broker_name,
                        quantity = excluded.quantity,
                        side = excluded.side,
                        average_price = excluded.average_price,
                        realized_pnl = excluded.realized_pnl,
                        unrealized_pnl = excluded.unrealized_pnl,
                        status = excluded.status,
                        opened_at = excluded.opened_at,
                        closed_at = excluded.closed_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        symbol,
                        broker_name,
                        quantity,
                        side.upper(),
                        average_price,
                        realized_pnl,
                        unrealized_pnl,
                        status.upper(),
                        opened_at,
                        closed_at,
                        now,
                    ),
                )

                connection.commit()

        position = self.get_position(symbol)

        if position is None:
            raise RuntimeError(
                "Position was saved but could not be read."
            )

        return position

    def close_position(
        self,
        symbol: str,
        *,
        realized_pnl: float = 0.0,
        closed_at: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        close_timestamp = closed_at or now

        with self._write_lock:
            with self.connection() as connection:
                cursor = connection.execute(
                    """
                    UPDATE execution_positions
                    SET quantity = 0,
                        side = 'FLAT',
                        status = 'CLOSED',
                        realized_pnl = ?,
                        unrealized_pnl = 0,
                        closed_at = ?,
                        updated_at = ?
                    WHERE symbol = ?
                    """,
                    (
                        realized_pnl,
                        close_timestamp,
                        now,
                        symbol,
                    ),
                )

                if cursor.rowcount == 0:
                    raise KeyError(
                        f"Position not found: {symbol}"
                    )

                connection.commit()

        position = self.get_position(symbol)

        if position is None:
            raise RuntimeError(
                "Position was closed but could not be read."
            )

        return position

    def get_position(
        self,
        symbol: str,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_positions
                WHERE symbol = ?
                """,
                (symbol,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_positions(
        self,
        *,
        open_only: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT *
            FROM execution_positions
        """

        if open_only:
            query += """
                WHERE status = 'OPEN'
                  AND quantity != 0
            """

        query += """
            ORDER BY updated_at DESC
        """

        with self.connection() as connection:
            rows = connection.execute(
                query
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # Risk events
    # =========================================================

    def create_risk_event(
        self,
        *,
        risk_code: str,
        decision: str,
        signal_id: str | None = None,
        order_id: str | None = None,
        source: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        action: str | None = None,
        reason: str | None = None,
        daily_pnl: float | None = None,
        requested_quantity: int | None = None,
        raw_payload: Any = None,
        risk_event_id: str | None = None,
    ) -> dict[str, Any]:
        generated_id = (
            risk_event_id or str(uuid.uuid4())
        )

        now = utc_now_iso()

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_risk_events (
                        risk_event_id,
                        signal_id,
                        order_id,
                        source,
                        symbol,
                        timeframe,
                        action,
                        risk_code,
                        decision,
                        reason,
                        daily_pnl,
                        requested_quantity,
                        created_at,
                        raw_payload
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        generated_id,
                        signal_id,
                        order_id,
                        source,
                        symbol,
                        timeframe,
                        action.upper()
                        if action
                        else None,
                        risk_code.upper(),
                        decision.upper(),
                        reason,
                        daily_pnl,
                        requested_quantity,
                        now,
                        self._json_dump(raw_payload),
                    ),
                )

                connection.commit()

        risk_event = self.get_risk_event(
            generated_id
        )

        if risk_event is None:
            raise RuntimeError(
                "Risk event was created but "
                "could not be read."
            )

        return risk_event

    def get_risk_event(
        self,
        risk_event_id: str,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_risk_events
                WHERE risk_event_id = ?
                """,
                (risk_event_id,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_risk_events(
        self,
        *,
        decision: str | None = None,
        risk_code: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError(
                "Limit must be at least 1."
            )

        conditions: list[str] = []
        values: list[Any] = []

        if decision is not None:
            conditions.append("decision = ?")
            values.append(decision.upper())

        if risk_code is not None:
            conditions.append("risk_code = ?")
            values.append(risk_code.upper())

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        values.append(limit)

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM execution_risk_events
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                values,
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # Audit events
    # =========================================================

    def create_audit_event(
        self,
        *,
        event_type: str,
        status: str,
        signal_id: str | None = None,
        order_id: str | None = None,
        message: str | None = None,
        metadata: Any = None,
        audit_event_id: str | None = None,
    ) -> dict[str, Any]:
        generated_id = (
            audit_event_id or str(uuid.uuid4())
        )

        now = utc_now_iso()

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_audit_events (
                        audit_event_id,
                        signal_id,
                        order_id,
                        event_type,
                        status,
                        message,
                        created_at,
                        metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        generated_id,
                        signal_id,
                        order_id,
                        event_type.upper(),
                        status.upper(),
                        message,
                        now,
                        self._json_dump(metadata),
                    ),
                )

                connection.commit()

        event = self.get_audit_event(
            generated_id
        )

        if event is None:
            raise RuntimeError(
                "Audit event was created but "
                "could not be read."
            )

        return event

    def get_audit_event(
        self,
        audit_event_id: str,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_audit_events
                WHERE audit_event_id = ?
                """,
                (audit_event_id,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_audit_events(
        self,
        *,
        order_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError(
                "Limit must be at least 1."
            )

        conditions: list[str] = []
        values: list[Any] = []

        if order_id is not None:
            conditions.append("order_id = ?")
            values.append(order_id)

        if event_type is not None:
            conditions.append("event_type = ?")
            values.append(event_type.upper())

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        values.append(limit)

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM execution_audit_events
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                values,
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
    

    # =========================================================
    # Trades
    # =========================================================

    def create_trade(
        self,
        *,
        symbol: str,
        side: str,
        contracts: int,
        entry_price: float,
        exit_price: float,
        points: float,
        gross_pnl: float,
        net_pnl: float,
        result: str,
        entry_time: str,
        exit_time: str,
        duration_seconds: float,
        multiplier: float = 1.0,
        commission: float = 0.0,
        signal_id: str | None = None,
        order_id: str | None = None,
        broker_name: str | None = None,
        source: str | None = None,
        timeframe: str | None = None,
        trade_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Persist one completed trade.

        Completed trades are treated as immutable records.
        """

        normalized_side = side.upper()
        normalized_result = result.upper()

        if contracts < 1:
            raise ValueError(
                "Trade contracts must be at least 1."
            )

        if multiplier <= 0:
            raise ValueError(
                "Trade multiplier must be greater than 0."
            )

        if commission < 0:
            raise ValueError(
                "Trade commission cannot be negative."
            )

        if duration_seconds < 0:
            raise ValueError(
                "Trade duration cannot be negative."
            )

        if normalized_side not in {"LONG", "SHORT"}:
            raise ValueError(
                "Trade side must be LONG or SHORT."
            )

        if normalized_result not in {
            "WIN",
            "LOSS",
            "BREAKEVEN",
        }:
            raise ValueError(
                "Trade result must be WIN, LOSS, or BREAKEVEN."
            )

        if order_id is not None:
            if self.get_order(order_id) is None:
                raise KeyError(
                    f"Cannot create trade. "
                    f"Order not found: {order_id}"
                )

        generated_trade_id = (
            trade_id or str(uuid.uuid4())
        )

        now = utc_now_iso()

        with self._write_lock:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO execution_trades (
                        trade_id,
                        signal_id,
                        order_id,
                        broker_name,
                        source,
                        symbol,
                        timeframe,
                        side,
                        contracts,
                        entry_price,
                        exit_price,
                        points,
                        multiplier,
                        gross_pnl,
                        commission,
                        net_pnl,
                        result,
                        entry_time,
                        exit_time,
                        duration_seconds,
                        created_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        generated_trade_id,
                        signal_id,
                        order_id,
                        broker_name,
                        source,
                        symbol,
                        timeframe,
                        normalized_side,
                        contracts,
                        entry_price,
                        exit_price,
                        points,
                        multiplier,
                        gross_pnl,
                        commission,
                        net_pnl,
                        normalized_result,
                        entry_time,
                        exit_time,
                        duration_seconds,
                        now,
                    ),
                )

                connection.commit()

        trade = self.get_trade(generated_trade_id)

        if trade is None:
            raise RuntimeError(
                "Trade was created but could not be read."
            )

        return trade

    def get_trade(
        self,
        trade_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve one completed trade by ID.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM execution_trades
                WHERE trade_id = ?
                """,
                (trade_id,),
            ).fetchone()

        return self._row_to_dict(row)

    def list_trades(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        result: str | None = None,
        limit: int = 100,
        order_by: str = "exit_time",
        ascending: bool = False,
    ) -> list[dict[str, Any]]:
        """
        List completed trades with optional filtering and ordering.
        """

        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        allowed_order_fields = {
            "entry_time",
            "exit_time",
            "symbol",
            "side",
            "result",
            "gross_pnl",
            "net_pnl",
            "points",
            "duration_seconds",
        }

        if order_by not in allowed_order_fields:
            raise ValueError(
                f"Invalid trade order field: {order_by}"
            )

        order_direction = "ASC" if ascending else "DESC"

        conditions: list[str] = []
        values: list[Any] = []

        if symbol is not None:
            conditions.append("symbol = ?")
            values.append(symbol)

        if side is not None:
            normalized_side = side.upper()

            if normalized_side not in {"LONG", "SHORT"}:
                raise ValueError(
                    "Trade side must be LONG or SHORT."
                )

            conditions.append("side = ?")
            values.append(normalized_side)

        if result is not None:
            normalized_result = result.upper()

            if normalized_result not in {
                "WIN",
                "LOSS",
                "BREAKEVEN",
            }:
                raise ValueError(
                    "Trade result must be WIN, LOSS, or BREAKEVEN."
                )

            conditions.append("result = ?")
            values.append(normalized_result)

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        values.append(limit)

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM execution_trades
                {where_clause}
                ORDER BY {order_by} {order_direction}
                LIMIT ?
                """,
                values,
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
    


    

    def delete_trade(
        self,
        trade_id: str,
    ) -> None:
        """
        Delete a completed trade.

        Intended primarily for tests and administrative cleanup.
        """

        with self._write_lock:
            with self.connection() as connection:
                cursor = connection.execute(
                    """
                    DELETE FROM execution_trades
                    WHERE trade_id = ?
                    """,
                    (trade_id,),
                )

                if cursor.rowcount == 0:
                    raise KeyError(
                        f"Trade not found: {trade_id}"
                    )

                connection.commit()




    # =========================================================
    # Summary
    # =========================================================

    def get_summary(self) -> dict[str, Any]:
        with self.connection() as connection:
            order_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_orders
                """
            ).fetchone()[0]

            fill_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_fills
                """
            ).fetchone()[0]

            risk_event_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_risk_events
                """
            ).fetchone()[0]

            audit_event_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_audit_events
                """
            ).fetchone()[0]

            open_position_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_positions
                WHERE status = 'OPEN'
                  AND quantity != 0
                """
            ).fetchone()[0]

            rejected_risk_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_risk_events
                WHERE decision = 'REJECTED'
                """
            ).fetchone()[0]

            trade_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM execution_trades
                """
            ).fetchone()[0]

        return {
            "database_path": str(
                self.database_path.resolve()
            ),
            "orders": order_count,
            "fills": fill_count,
            "risk_events": risk_event_count,
            "audit_events": audit_event_count,
            "trades": trade_count,
            "open_positions": open_position_count,
            "rejected_risk_events": (
                rejected_risk_count
            ),
        }