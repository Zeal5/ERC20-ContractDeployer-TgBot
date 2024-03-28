from web3 import AsyncWeb3


w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider('http://127.0.0.1:8545'))
await w3.is_connected()


async def deploy():
    pass
