from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Async Engine for High Performance
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_tenant_db(tenant_id: str):
    """
    Returns a DB session with the RLS context set for the specific tenant.
    Critical for security.
    """
    async with AsyncSessionLocal() as session:
        # Enforce RLS Context
        await session.execute(f"SELECT set_tenant_context('{tenant_id}')")
        try:
            yield session
        finally:
            # Clean up context to prevent leaking
            await session.execute("RESET app.current_tenant")