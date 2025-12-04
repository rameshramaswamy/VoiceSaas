from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class VoiceProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    OPENAI = "openai"

class AgentLanguage(str, Enum):
    EN_US = "en-US"
    AR_EG = "ar-EG" # Egyptian Arabic
    AR_SA = "ar-SA" # Saudi Arabic
    AR_AE = "ar-AE" # Gulf Arabic

# Base Schema
class AgentBase(BaseModel):
    name: str = Field(..., min_length=2, example="Sales Representative")
    
    # The "Brain"
    system_prompt: str = Field(
        ..., 
        min_length=10, 
        description="Instructions for the LLM",
        example="You are a helpful assistant for a dental clinic. Be polite and concise."
    )
    
    # Voice Settings
    voice_provider: VoiceProvider = VoiceProvider.ELEVENLABS
    voice_id: str = Field(..., description="The specific voice UUID from the provider")
    language: AgentLanguage = AgentLanguage.EN_US
    
    # Integrations
    calendar_enabled: bool = False
    
    # Advanced Tuning (Optional)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    
# Create Request
class AgentCreate(AgentBase):
    pass

# Update Request (PATCH) - All fields optional
class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    voice_provider: Optional[VoiceProvider] = None
    voice_id: Optional[str] = None
    language: Optional[AgentLanguage] = None
    calendar_enabled: Optional[bool] = None
    temperature: Optional[float] = None

# Output Schema
class AgentResponse(AgentBase):
    id: UUID
    tenant_id: UUID
    # We don't expose created_at in the MVP, but can add it here
    
    class Config:
        from_attributes = True