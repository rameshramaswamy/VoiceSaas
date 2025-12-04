from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.agents.models import Agent
from app.modules.agents.schemas import AgentCreate
from app.core.cache import CacheService

# Standard TTL: 1 hour (Voice engine needs speed, not infinite freshness)
CACHE_TTL = 3600 

async def get_agent_by_id(db: AsyncSession, agent_id: str, tenant_id: str):
    cache_key = f"agent:{tenant_id}:{agent_id}"
    
    # 1. Try Cache
    cached_agent = await CacheService.get(cache_key)
    if cached_agent:
        return cached_agent # Return Dict directly (FastAPI handles it)

    # 2. Try DB
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.tenant_id == tenant_id)
    )
    agent = result.scalar_one_or_none()
    
    # 3. Set Cache
    if agent:
        # Convert SQLAlchemy model to Dict for serialization
        agent_dict = {
            "id": str(agent.id),
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "voice_provider": agent.voice_provider,
            "voice_id": agent.voice_id,
            "language": agent.language
        }
        await CacheService.set(cache_key, agent_dict, expire=CACHE_TTL)
        return agent
        
    return None

async def create_agent(db: AsyncSession, agent_in: AgentCreate, tenant_id: str):
    new_agent = Agent(**agent_in.dict(), tenant_id=tenant_id)
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    
    # No cache to set yet, but good practice to ensure clean state
    return new_agent

async def update_agent(db: AsyncSession, agent_id: str, tenant_id: str, updates: dict):
    # ... update logic ...
    
    # CRITICAL: Invalidate Cache on Update
    cache_key = f"agent:{tenant_id}:{agent_id}"
    await CacheService.delete(cache_key)