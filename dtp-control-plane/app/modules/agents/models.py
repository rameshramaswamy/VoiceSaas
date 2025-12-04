import uuid
from sqlalchemy import Column, String, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String, nullable=False)
    
    # Voice Config
    voice_provider = Column(String, default="elevenlabs") # elevenlabs, azure
    voice_id = Column(String) # 'rachel', 'adam', etc.
    
    # AI Brain
    system_prompt = Column(String, nullable=False) # "You are a helpful assistant..."
    language = Column(String, default="en-US") # en-US, ar-EG
    
    # Integration
    calendar_enabled = Column(Boolean, default=False)
    
    # RLS Policy applies here automatically in DB