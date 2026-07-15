from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


BrokerSide = Literal["BUY", "SELL"]
PositionSide = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class BrokerAccount:
    account_id: str
    name: str
    environment: str
    balance: float
    active: bool = True


@dataclass(frozen=True)
class BrokerPosition:
    account_id: str
    symbol: str
    side: PositionSide
    quantity: int
    average_price: float


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str
    account_id: str
    symbol: str
    side: BrokerSide
    quantity: int
    order_type: str
    status: str
    submitted_at: str


@dataclass(frozen=True)
class BrokerFill:
    fill_id: str
    order_id: str
    account_id: str
    symbol: str
    side: BrokerSide
    quantity: int
    fill_price: float
    filled_at: str

    @staticmethod
    def now_iso() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()


class BrokerClient(ABC):
    @abstractmethod
    async def authenticate(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_accounts(
        self,
    ) -> list[BrokerAccount]:
        raise NotImplementedError

    @abstractmethod
    async def get_positions(
        self,
    ) -> list[BrokerPosition]:
        raise NotImplementedError

    @abstractmethod
    async def get_orders(
        self,
    ) -> list[BrokerOrder]:
        raise NotImplementedError

    @abstractmethod
    async def place_market_order(
        self,
        *,
        account_id: str,
        symbol: str,
        side: BrokerSide,
        quantity: int,
        reference_price: float,
    ) -> BrokerFill:
        raise NotImplementedError

    @abstractmethod
    async def close_position(
        self,
        *,
        account_id: str,
        symbol: str,
        reference_price: float,
    ) -> BrokerFill | None:
        raise NotImplementedError