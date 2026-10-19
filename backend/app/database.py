import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger("vickyops.database")

Base = declarative_base()

def create_engine_instance(db_url: str):
    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False
    return create_async_engine(db_url, echo=False, connect_args=connect_args)

engine = create_engine_instance(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        # Fallback to local SQLite if PostgreSQL container is unreachable on host
        if "sqlite" not in settings.DATABASE_URL:
            logger.warning(f"Could not connect to configured DB ({e}). Falling back to local SQLite.")
            fallback_url = "sqlite+aiosqlite:///./vickyops.db"
            engine = create_engine_instance(fallback_url)
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Fallback SQLite database initialized successfully.")
        else:
            raise e
