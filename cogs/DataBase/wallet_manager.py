from . import Session
from .models import Users, Wallet
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.exc import NoResultFound
from typing import Union, Optional
from eth_account import Account
from . import UserInfo
from .helpers import encrypt_wallet_secret, decrypt_wallet_secret


async def delete_user(_id: int):
    user: Optional[UserInfo] =await _check_user_exists(_id)
    if user:
        async with Session() as session:
            async with session.begin():
                stmt = delete(Users).where(Users.tg_id == _id)
                await session.execute(stmt)
                await session.commit()
                return True
    else:
        return False


async def _check_user_exists(_id: int) -> Union[bool, UserInfo]:
    """Checks if user with tg_id exists in database

    Args:
    ``tg_id``: The Telegram ID of user

    Returns:
    ``bool`` : user pk if user with tg_id exists else False
    """
    async with Session() as s:
        async with s.begin():
            try:
                user = await s.execute(select(Users).filter(Users.tg_id == _id))
                user = user.scalars().first()
                if not user:
                    return False

                return UserInfo(
                    tg_id=_id,
                    address=user.wallet.address,
                    secret=decrypt_wallet_secret(user.wallet.secret),
                )

            except NoResultFound as e:
                print(f"error {str(e)}")
                return False


async def add_user_and_wallet(tg_id: int) -> Union[UserInfo,bool]:
    user_exists = await _check_user_exists(tg_id)
    if isinstance(user_exists, UserInfo):
        return user_exists

    account = Account.create(f"{tg_id}")
    print("addingf user")
    try:
        async with Session() as session:
            async with session.begin():
                # Create a new wallet
                new_wallet = Wallet(
                    secret=encrypt_wallet_secret(account._private_key.hex()),
                    address=account.address,
                )
                session.add(new_wallet)
                await session.flush()  # Flush the session to get the wallet's ID

                # Create a new user with the wallet
                new_user = Users(tg_id=tg_id, wallet_id=new_wallet.id)
                session.add(new_user)

            await session.commit()
            return UserInfo(
                tg_id=tg_id, address=account.address, secret=account._private_key.hex()
            )
    except Exception as e:
        print("error while adding user {str(e)}")
        return False  # user wasem't added. alredy present?
    return True  # user added
