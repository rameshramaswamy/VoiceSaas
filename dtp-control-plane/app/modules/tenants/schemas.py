from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re

# Base Schema (Shared properties)
class TenantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Acme Corp")
    slug: str = Field(..., min_length=3, max_length=50, example="acme-corp")

    @validator("slug")
    def validate_slug(cls, v):
        if not re.match("^[a-z0-9-]+$", v):
            raise ValueError("Slug must be lowercase, alphanumeric, and contain no spaces.")
        return v

# Input Schema (POST /api/v1/tenants)
class TenantCreate(TenantBase):
    pass # Add billing_email here in future

# Output Schema (Response)
class TenantResponse(TenantBase):
    id: UUID
    is_active: bool
    created_at: datetime
    plan_tier: str

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy models