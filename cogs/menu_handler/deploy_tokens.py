from web3 import AsyncWeb3, Account

from ABI import FACTORY_ABI, TOKEN_ABI, UNISWAP_ROUTER_ABI, UNXC_ABI
from . import Chain, TxnHash, TokenInfo, TokenLiqAdded
from cogs.Wallet import UserInfo
from cogs.Wallet.wallet_manager import add_user_and_wallet
import asyncio


chainID = {
    8453: {
        "basu_factory": "0x7969c5eD335650692Bc04293B07F5BF2e7A673C0",
        "uniswap_router": "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24",
        "UNCX_lp_locker": "0xc4E637D37113192F4F1F060DaEbD7758De7F4131",
    }
}

rpc_url = "http://127.0.0.1:8545"


async def check_wallet_balance(address: str) -> int:
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    bal = await w3.eth.get_balance(address)
    return w3.from_wei(bal, "ether")


class AsyncDeployer:
    def __init__(
        self,
        tg_id,
        supply: int,
        name: str,
        symbol: str,
        buy_tax: int,
        sell_tax: int,
        owner_tax_share: int,
        owner_tax_address: str,
        basu_tax_address: str,
    ):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self.factory_address = self.w3.to_checksum_address(
            chainID.get(8453)["basu_factory"]
        )
        self.factory = self.w3.eth.contract(
            address=self.factory_address, abi=FACTORY_ABI
        )

        self.supply = supply * 10**18
        self.name = name
        self.symbol = symbol
        self.buy_tax = buy_tax
        self.sell_tax = sell_tax
        self.owner_tax_share = owner_tax_share
        self.owner_tax_address = owner_tax_address
        self.basu_tax_address = basu_tax_address

        self.tg_id = tg_id

    async def get_account(self):
        user: UserInfo = await add_user_and_wallet(self.tg_id)
        print(user.address, user.secret)
        self.address = user.address
        self.secret = user.secret

    async def check_wallet_balance(self):
        bal: int = await self.w3.eth.get_balance(self.address)
        return self.w3.from_wei(bal, "ether")

    async def estimate_gas(self, cost: bool = False):
        """cost = True means return total cost of deployment"""
        # Gas estimate
        print("estimating gas fee")
        gas_estimate = await self.factory.functions.DeployToken(
            self.supply,
            self.name,
            self.symbol,
            self.buy_tax,
            self.sell_tax,
            self.owner_tax_share,
            self.owner_tax_address,
            self.basu_tax_address,
        ).estimate_gas({"from": self.address})
        print(gas_estimate)
        if cost:
            _gas_price = await self.w3.eth.gas_price
            print(f"gas price {_gas_price}")
            return self.w3.from_wei(gas_estimate * _gas_price, "ether")
        return gas_estimate

    async def deploy(self):
        # Gas estimate
        gas_estimate = await self.estimate_gas()

        txn = await self.factory.functions.DeployToken(
            self.supply,
            self.name,
            self.symbol,
            self.buy_tax,
            self.sell_tax,
            self.owner_tax_share,
            self.owner_tax_address,
            self.basu_tax_address,
        ).build_transaction(
            {
                "from": self.address,
                "gas": gas_estimate,
                "nonce": await self.w3.eth.get_transaction_count(self.address),
            }
        )
        sign_txn = self.w3.eth.account.sign_transaction(txn, self.secret)
        new_token = await self.w3.eth.send_raw_transaction(sign_txn.rawTransaction)
        return new_token.hex()

    async def wait_for_tx_hash(self, tx_hash: str) -> TxnHash:
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

    async def wait_for_event_logs(self, txn_hash: TxnHash) -> TokenInfo:
        # @DEV In case if there are miltiple token contracts deployed in same block
        # return the one who's owner is msg.sender 11 lines below this inside loop return
        counter = 0
        while counter < 3:
            try:
                logs = await self.factory.events.TokenDeployed().get_logs(
                    fromBlock=txn_hash.blockNumber
                )
                if not logs:
                    counter += 1
                    await asyncio.sleep(counter + counter * 3)
                    continue

                for log in logs:
                    token_contract = self.w3.eth.contract(
                        address=log.args.token, abi=TOKEN_ABI
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
                counter += 1
                await asyncio.sleep(counter + counter * 3)

    async def add_liquidity(self, token_address: str, _value: float):
        print("adding liq......")
        # Get router address
        _value = self.w3.to_wei(_value, "ether")
        try:
            x = await self.factory.functions.addLiquidity(
                token_address
            ).build_transaction(
                {
                    "from": self.address,
                    "gas": 30000000,
                    "nonce": await self.w3.eth.get_transaction_count(self.address),
                    "value": _value,
                }
            )
            sign_txn = self.w3.eth.account.sign_transaction(x, self.secret)
            txn_hash = await self.w3.eth.send_raw_transaction(sign_txn.rawTransaction)
            print(txn_hash.hex())
            return txn_hash.hex()
        except Exception as e:
            print(str(e))
            return None

    async def event_logs_for_adding_liquidity(self, txn_hash: TxnHash):
        counter = 1
        while counter < 4:
            try:
                await asyncio.sleep(counter + counter * 3)
                counter += 1
                logs = await self.factory.events.LiquidityAdded().get_logs(
                    fromBlock=txn_hash.blockNumber
                )
                print(logs)
                if not logs:
                    counter += 1
                    await asyncio.sleep(counter + counter * 3)
                    continue

                for log in logs:
                    return TokenLiqAdded(
                        log.args.token,
                        self.w3.from_wei(log.args.tokensAdded, "ether"),
                        self.w3.from_wei(log.args.WETHAdded, "ether"),
                    )

            except Exception as e:
                print("RAISE AN ERROR")
                print(str(e))

    async def lock_tokens(self, token_address: str, unlock_date, _withdrawer=False):
        if not _withdrawer:
            _withdrawer = self.address

        locker_address = self.w3.to_checksum_address(
            chainID.get(8453)["UNCX_lp_locker"]
        )
        locker = self.w3.eth.contract(address=locker_address, abi=UNXC_ABI)

        token_contract = self.w3.eth.contract(address=token_address, abi=TOKEN_ABI)
        print(token_contract)
        lp_token_address = await token_contract.functions.liquidityPoolAddress().call()
        print(lp_token_address)

        lp_token = self.w3.eth.contract(address=lp_token_address, abi=TOKEN_ABI)
        _factory_token_balance = await lp_token.functions.balanceOf(
            self.factory_address
        ).call()

        print(f"token lp tokens {_factory_token_balance}")
        _countryCode = 90
        txn = await self.factory.functions.lock_lp(
            lp_token_address,
            _factory_token_balance,
            unlock_date,
            self.factory_address,
            True,
            _withdrawer,
            _countryCode,
        ).build_transaction(
            {
                "from": self.address,
                "value": self.w3.to_wei(0.1, "ether"),
                "gas": 30000000,
                "nonce": await self.w3.eth.get_transaction_count(self.address),
            }
        )
        sign_txn = self.w3.eth.account.sign_transaction(txn, self.secret)
        new_token = await self.w3.eth.send_raw_transaction(sign_txn.rawTransaction)
        return new_token.hex()
