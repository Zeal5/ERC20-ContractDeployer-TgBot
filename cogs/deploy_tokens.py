from web3 import AsyncWeb3, Account

from ABI import factory_abi
from . import Chain, TxnHash


chainID = {8453: "0xc5a5C42992dECbae36851359345FE25997F5C42d"}


class AsyncDeployer:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider("http://127.0.0.1:8545"))
        self.factory_address = chainID.get(8453)

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
        contract = self.w3.eth.contract(address=self.factory_address, abi=factory_abi)
        # print(await contract.functions.owner().call())
        # Deploy token contract

        account = self.get_account()

        # Gas estimate
        gas_estimate = await contract.functions.owner().estimate_gas(
            {"from": account.address}
        )
        print(f"Gas estimate: {gas_estimate}")

        new_token = await contract.functions.DeployToken(
            supply * 10**18,
            name,
            symbol,
            buy_tax,
            sell_tax,
            owner_tax_share,
            owner_tax_address,
            basu_tax_address,
        ).transact({"from": account.address, "gas" : gas_estimate + 10000000})

        print(f"token deployment hash {new_token.hex()}")
        return new_token.hex()

    def get_account(self):
        pk = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
        account = Account.from_key(pk)
        print(account.address)
        return account

    async def get_token_info(self):
        # self.w3.eth.contract(address= , abi= )
        pass

    async def wait_for_tx_hash(self, tx_hash: str):
        receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
        print(f"recipt = {receipt}")
        txn_hash = TxnHash(
            receipt.blockNumber,
            receipt.cumulativeGasUsed,
            receipt.effectiveGasPrice,
            receipt["from"],
            receipt.to,
        )
        self.token_address = receipt.to
        return txn_hash
