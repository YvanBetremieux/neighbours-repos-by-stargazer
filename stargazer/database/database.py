"""
database module
"""
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///database.sqlite3"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, echo=True, connect_args={"check_same_thread": False}
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
Base = declarative_base()


def verify_password(plain_password, hashed_password):
    """
    Check pwd, if match with the encrypted pwd in db
    :param plain_password: pwd in plain text
    :param hashed_password: crypted pwd
    :return: True if pwd are matching else False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash password
    :param password: pwd in plain text
    :return: hashed pwd
    """
    return pwd_context.hash(password)


async def get_db():
    """
    Get db session
    :return:
    """
    session = AsyncSession(engine)
    try:
        yield session
    finally:
        await session.close()


class User(Base):  # pylint: disable=R0903
    """
    User class for db
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)
    disabled = Column(Boolean, default=False)
    hashed_password = Column(String)
