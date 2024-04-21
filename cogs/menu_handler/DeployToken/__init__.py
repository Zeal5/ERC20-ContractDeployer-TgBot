from enum import Enum
from dataclasses import dataclass


class Chain(Enum):
    Base = 8453
    Polygon = 1

@dataclass
class TokenArgs:
    buy_tax: int
    sell_tax: int
    owner_address: str
@dataclass
class Token:
    name: str
    symbol: str
    supply: int

@dataclass
class TokenLiqAdded:
    token : str
    token_added : int
    WETH_added : int

@dataclass
class TokenInfo:
    token_address: str
    pool_address: str
    owner: str
    name: str
    symbol: str
    buyTax: float
    sellTax: float

@dataclass
class TxnHash:
    blockNumber: int
    _from: str
    to: str
