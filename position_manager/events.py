from dataclasses import dataclass
from datetime import datetime

from position_manager.enums import Side


@dataclass(frozen=True)
class PositionEvent:
    timestamp: datetime


@dataclass(frozen=True)
class PositionOpened(PositionEvent):
    symbol: str
    side: Side
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionAdded(PositionEvent):
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionReduced(PositionEvent):
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionClosed(PositionEvent):
    price: float