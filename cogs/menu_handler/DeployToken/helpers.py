from dataclasses import dataclass
from typing import Optional
from . import Token,TokenArgs
def clean_token_args(_args: str) -> Optional[Token]:
    try:
        name, ticker, supply = _args.strip().split()
        return Token(name, ticker, int(supply))
    except Exception as e:
        return None

def clean_token_tax_info(_info: str):
    try:
        buy_tax, sell_tax, owner = _info.strip().split()
        if not owner.startswith("0x") or len(owner) != 42:
            return False

        return TokenArgs(int(buy_tax), int(sell_tax), str(owner))
    except Exception as e:
        print(f"exception in cleaning tax info {str(e)}")
        return None
