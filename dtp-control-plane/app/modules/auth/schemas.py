from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Token Payload (Decoded JWT)
class TokenPayload(BaseModel):
    sub: Optional[str] = None # User ID
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

# Login Request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User Creation (Invite)
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "admin" # owner, admin, agent