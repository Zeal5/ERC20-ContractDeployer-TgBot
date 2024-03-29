from enum import Enum
from dataclasses import dataclass


class Chain(Enum):
    Base = 8453
    Polygon = 1

@dataclass
class TokenInfo:
    token_address : str
    owner : str 
    pool_address : str

@dataclass
class TxnHash:
    blockNumber : int
    gasUsed: int
    gasPrice: int
    _from: str 
    to : str

