from web3 import AsyncWeb3
from cogs.DataBase import UserInfo
from cogs.DataBase.wallet_manager import add_user_and_wallet

rpc_url = "http://127.0.0.1:8545"


def clean_token_address(_reply: str):
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    address, value = _reply.strip().split()[0:2]
    return w3.to_checksum_address(address), value

async def check_wallet_balance_from_tg_id(tg_id):
    user: UserInfo | bool = await add_user_and_wallet(tg_id)
    return await check_wallet_balance(user.address)

async def check_wallet_balance(address: str, wei = False) -> float:
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    bal = await w3.eth.get_balance(w3.to_checksum_address(address))
    if wei:
        return bal
    return w3.from_wei(bal, "ether")


async def get_gas_estimate(_from, _to, _value, w3):
    es =  await w3.eth.estimate_gas({"from": _from, "to": _to, "value": _value})
    print(f'estimate {es}')
    return es


async def transfer_eth(to_address: str, value: float, tg_id):
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    user: UserInfo | bool = await add_user_and_wallet(tg_id)
    total_balance = await check_wallet_balance(user.address,True)
    gas_estimate = await get_gas_estimate(user.address,to_address,total_balance,w3) + 20_000
    gas_price = await w3.eth.gas_price
    if value in ["all", "All", "ALL"]:
        value = total_balance - (gas_price * gas_estimate)

    # get user balance
    print(f"balance {total_balance}\t value {value}")
    if total_balance <= value:
        return False

    transaction = {
        "to": to_address,
        "value": value,
        "gas":gas_estimate,
        "gasPrice":gas_price ,
        "nonce": await w3.eth.get_transaction_count(user.address),
    }

    print(transaction)
    # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, user.secret)

    # Send the transaction
    txn_hash = await w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return txn_hash.hex()
