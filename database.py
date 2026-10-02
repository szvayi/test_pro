"""Database engine and session helpers.

The runtime Secret provides DATABASE_URL and SCHEMA_NAME.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
import os
import re

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for future SQLAlchemy models."""


def get_database_url() -> str | None:
    """Read the configured database URL without exposing its value."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return "postgresql+asyncpg://" + database_url.removeprefix("postgres://")
        if database_url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + database_url.removeprefix("postgresql://")
    return database_url


def get_schema_name() -> str:
    """Read and validate the PostgreSQL schema used by the application."""
    schema_name = os.getenv("SCHEMA_NAME", "public")
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema_name):
        raise ValueError(f"Invalid schema name: {schema_name!r}")
    return schema_name


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine | None:
    """Create one process-wide engine when a database URL is configured."""
    database_url = get_database_url()
    if not database_url:
        return None

    return create_async_engine(
        database_url,
        connect_args={"server_settings": {"search_path": get_schema_name()}},
        pool_pre_ping=True,
    )


async def check_database_connection() -> bool:
    """Return whether the configured database can execute a trivial query."""
    engine = get_engine()
    if engine is None:
        return False

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped SQLAlchemy session."""
    engine = get_engine()
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )

    session_factory = async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
