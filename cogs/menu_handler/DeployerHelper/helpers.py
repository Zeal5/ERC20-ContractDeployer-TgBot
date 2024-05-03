from web3 import AsyncWeb3, Account
from cogs.DataBase.wallet_manager import add_user_and_wallet
from cogs.DataBase import UserInfo
from cogs import chainID
from ABI import FACTORY_ABI, TOKEN_ABI, UNXC_ABI
from cogs.menu_handler.DeployToken import TokenLiqAdded, TxnHash
import asyncio

rpc_url = chainID[8453]["rpc_url"]


class MidWay:
    def __init__(self, _tg_id):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self.tg_id = _tg_id

        self.factory_address = self.w3.to_checksum_address(
            chainID.get(8453)["basu_factory"]
        )
        self.factory = self.w3.eth.contract(
            address=self.factory_address, abi=FACTORY_ABI
        )

    def is_address(self, _address):
        try:
            return self.w3.to_checksum_address(_address)
        except Exception as e:
            print(str(e))
            return False

    async def get_account(self):
        user: UserInfo = await add_user_and_wallet(self.tg_id)
        print(user.address, user.secret)
        self.address = user.address
        self.secret = user.secret

    async def get_balance(self, _token_address):
        token_contract = self.w3.eth.contract(address=_token_address, abi=TOKEN_ABI)
        return await token_contract.functions.balanceOf(self.factory_address).call()

    async def check_wallet_balance(self):
        await self.get_account()
        bal: int = await self.w3.eth.get_balance(self.address)
        return self.w3.from_wei(bal, "ether")

    async def add_liquidity(self, token_address: str, _value: float):
        await self.get_account()
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
            return False

    async def wait_for_txn_hash(self, tx_hash: str) -> TxnHash:
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
                    # counter += 1
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
        return False

    async def lock_tokens(self, lp_token_address: str, unlock_date, _withdrawer=False):
        await self.get_account()
        if not _withdrawer:
            _withdrawer = self.address

        locker_address = self.w3.to_checksum_address(
            chainID.get(8453)["UNCX_lp_locker"]
        )
        # locker = self.w3.eth.contract(address=locker_address, abi=UNXC_ABI)

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
