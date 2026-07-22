from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from position_manager.enums import Side


@dataclass(frozen=True)
class PositionSnapshot:
    trade_id: UUID

    symbol: str

    side: Side

    quantity: int

    average_price: float

    realized_pnl: float

    unrealized_pnl: float

    opened_at: datetime | None

    updated_at: datetime | None