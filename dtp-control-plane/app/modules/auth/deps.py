from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.db.session import get_tenant_db
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user_db(token: str = Depends(oauth2_scheme)):
    """
    Dependency that decodes JWT, extracts tenant_id, 
    and returns a DB session LOCKED to that tenant.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        user_id: str = payload.get("sub")
        
        if tenant_id is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token claims")
            
        # Return the generator that yields the RLS-protected session
        async for session in get_tenant_db(tenant_id):
            return session

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")