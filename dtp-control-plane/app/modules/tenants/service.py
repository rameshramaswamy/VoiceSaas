from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas import TenantCreate

async def create_tenant(db: AsyncSession, tenant_in: TenantCreate) -> Tenant:
    # 1. Create Tenant Record
    new_tenant = Tenant(name=tenant_in.name, slug=tenant_in.slug)
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)
    
    # 2. (Future) Trigger Stripe Customer Creation here
    
    return new_tenant