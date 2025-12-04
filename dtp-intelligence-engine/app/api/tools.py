from fastapi import APIRouter, Body
from app.tools.executor import ToolExecutor
from app.localization.dialects import DialectManager

router = APIRouter()
executor = ToolExecutor()

@router.get("/definitions")
async def get_tools():
    """Returns the list of tools for the LLM System Prompt."""
    return {"tools": executor.get_tool_definitions()}

@router.post("/execute")
async def execute_tool(
    tool_name: str = Body(...),
    arguments: dict = Body(...)
):
    """
    Called when the LLM decides to use a tool.
    Returns the result text.
    """
    result = await executor.execute_tool(tool_name, arguments)
    return {"result": result}

@router.get("/config/dialect/{language_code}")
async def get_dialect_config(language_code: str):
    """
    Used by Voice Engine to configure STT/TTS at start of call.
    """
    return {
        "stt": DialectManager.get_stt_config(language_code),
        "tts": DialectManager.get_tts_config(language_code)
    }