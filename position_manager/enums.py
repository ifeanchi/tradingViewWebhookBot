from enum import Enum


class Side(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"