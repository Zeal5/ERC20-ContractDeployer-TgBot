from web3 import AsyncWeb3, Account

# Uncomment later
# from ABI import factory_abi
# from . import Chain, TxnHash

# Delete later
import json
import os

current_dir = os.path.dirname(__file__)

with open(f"{current_dir}/BasuFactory.json", "r") as f:
    factory = json.load(f)
    factory_abi = factory["abi"]

with open(f"{current_dir}/BasuToken.json", "r") as f:
    _toke = json.load(f)
    token_abi = _toke["abi"]

import asyncio
from enum import Enum
from dataclasses import dataclass


class Chain(Enum):
    Base = 8453
    Polygon = 1


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


chainID = {8453: "0xc5a5C42992dECbae36851359345FE25997F5C42d"}


class AsyncDeployer:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider("http://127.0.0.1:8545"))
        self.factory_address = chainID.get(8453)
        self.factory = self.w3.eth.contract(
            address=self.factory_address, abi=factory_abi
        )

    async def deploy(
        self,
        supply: int,
        name: str,
        symbol: str,
        buy_tax: int,
        sell_tax: int,
        owner_tax_share: int,
        owner_tax_address: str,
        basu_tax_address: str,
    ):
        print(await self.w3.is_connected())
        # print(await contract.functions.owner().call())
        # Deploy token contract

        account = self.get_account()

        # Gas estimate
        gas_estimate = await self.factory.functions.DeployToken(
            supply * 10**18,
            name,
            symbol,
            buy_tax,
            sell_tax,
            owner_tax_share,
            owner_tax_address,
            basu_tax_address,
        ).estimate_gas({"from": account.address})
        print(f"Gas estimate: {gas_estimate}")

        new_token = await self.factory.functions.DeployToken(
            supply * 10**18,
            name,
            symbol,
            buy_tax,
            sell_tax,
            owner_tax_share,
            owner_tax_address,
            basu_tax_address,
        ).transact({"from": account.address, "gas": gas_estimate})

        print(f"token deployment hash {new_token.hex()}")
        return new_token.hex()

    def get_account(self):
        # pk = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
        pk = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        account = Account.from_key(pk)
        print(account.address)
        return account

    async def get_token_info(self):
        # self.w3.eth.contract(address= , abi= )
        pass

    async def wait_for_tx_hash(self, tx_hash: str):
        counter = 0
        while counter < 5:
            await asyncio.sleep(counter + (counter * 3))
            print(f"sleeping for {counter + counter * 3}")
            try:
                receipt = await self.w3.eth.get_transaction_receipt(tx_hash)

                txn_hash = TxnHash(
                    receipt["blockNumber"],
                    receipt["from"],
                    receipt["to"],
                )
                return txn_hash
            except Exception as e:
                print("RAISED AN ERROR GONNA SLEEP")
                print(str(e))
                counter += 1
                # if isinstance(int) means return error

    async def wait_for_event_logs(self, txn_hash: TxnHash):
        # @DEV In case if there are miltiple token contracts deployed in same block
        # return the one who's owner is msg.sender 11 lines below this inside loop return
        counter = 0
        while counter < 3:
            try:
                logs = await self.factory.events.TokenDeployed().get_logs(
                    fromBlock=txn_hash.blockNumber
                )
                for log in logs:
                    token_contract = self.w3.eth.contract(
                        address=log.args.token, abi=token_abi
                    )

                    token_logs = await token_contract.events.TokenDeployed().get_logs(
                        fromBlock=txn_hash.blockNumber
                    )
                    for tl in token_logs:
                        return TokenInfo(
                            tl.args.token,
                            tl.args.pool,
                            tl.args.owner,
                            tl.args.name,
                            tl.args.symbol,
                            tl.args.buyTax,
                            tl.args.sellTax,
                        )

            except Exception as e:
                print("RAISE AN ERROR")
                print(str(e))
                await asyncio.sleep(counter + counter * 3)
                counter += 1


async def main():
    owner_addr = "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720"
    basu_funds_addr = "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"
    try:
        deployer = AsyncDeployer()
        token_deployment_hash = await deployer.deploy(
            10000000, "name", "SYM", 4, 5, 30, owner_addr, basu_funds_addr
        )
    except Exception as e:
        return 0
    txn_hash = await deployer.wait_for_tx_hash(token_deployment_hash)
    logs = await deployer.wait_for_event_logs(txn_hash)
    print(logs)


if __name__ == "__main__":
    asyncio.run(main())
