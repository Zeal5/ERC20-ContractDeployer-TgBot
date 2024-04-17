import json
import os

current_dir = os.path.dirname(__file__)

with open(f"{current_dir}/BasuFactory.json", "r") as f:
    factory = json.load(f)
    FACTORY_ABI = factory["abi"]


with open(f"{current_dir}/BasuToken.json", "r") as f:
    _toke = json.load(f)
    TOKEN_ABI = _toke["abi"]


with open(f"{current_dir}/IUniswapV2Router02.json", "r") as f:
    router_abi = json.load(f)
    UNISWAP_ROUTER_ABI= router_abi["abi"]


with open(f"{current_dir}/UNCX.json", "r") as f:
    uncx = json.load(f)
    UNXC_ABI = uncx
