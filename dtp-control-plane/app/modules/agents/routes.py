from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.modules.agents import schemas, models
from app.modules.auth.deps import get_current_user_db
from app.core.pagination import PageParams, PaginatedResponse, paginate


router = APIRouter()

@router.post("/", response_model=schemas.AgentResponse)
async def create_agent(
    agent_in: schemas.AgentCreate,
    # This DB session is already restricted to the caller's tenant!
    db: AsyncSession = Depends(get_current_user_db) 
):
    new_agent = models.Agent(**agent_in.dict())
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent

@router.get("/", response_model=PaginatedResponse[schemas.AgentResponse])
async def list_agents(
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_current_user_db)
):
    # Fetch Total
    total = await service.count_agents(db)
    # Fetch Page
    agents = await service.get_agents_paginated(db, skip=params.skip, limit=params.size)
    
    return paginate(agents, total, params)