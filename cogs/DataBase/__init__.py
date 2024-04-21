from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from . models import Base  # noqa: E402
from dataclasses import dataclass


engine = create_async_engine(f"postgresql+asyncpg://postgres:zeal@127.0.0.1:5432/basu")
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@dataclass
class UserInfo:
    tg_id : int 
    address: str
    secret : str

async def db_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
