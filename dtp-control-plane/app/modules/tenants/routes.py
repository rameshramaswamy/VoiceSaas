from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.modules.tenants import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.TenantResponse)
async def create_tenant(
    tenant_in: schemas.TenantCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Public Endpoint: Sign up a new organization.
    Triggers creation of Admin User and billing setup.
    """
    return await service.create_tenant(db, tenant_in)