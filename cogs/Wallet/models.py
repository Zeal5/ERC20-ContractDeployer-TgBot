from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Boolean,
    BIGINT,
    Integer,
    Float,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    relationship,
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from typing import Optional

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int]  = mapped_column(BIGINT,nullable=False, index=True, unique=True)
    wallet : Mapped['Wallet'] = relationship(backref='user')
    wallet_id = Column(Integer, ForeignKey('wallets.id'))


class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[int] = mapped_column(primary_key=True)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)



