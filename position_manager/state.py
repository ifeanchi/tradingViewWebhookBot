from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from position_manager.enums import Side


@dataclass(frozen=True)
class PositionState:
    trade_id: UUID

    symbol: str

    side: Side

    quantity: int

    average_price: float

    realized_pnl: float = 0.0

    unrealized_pnl: float = 0.0

    opened_at: datetime | None = None

    updated_at: datetime | None = None