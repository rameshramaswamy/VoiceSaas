import asyncio
from typing import Dict
from app.tools.executor import ToolExecutor
from app.core.telemetry import TOOL_EXECUTION_TIME, TOOL_ERRORS

class RobustToolExecutor(ToolExecutor):
    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"System Error: Tool '{tool_name}' is not configured."

        # Start Timer
        with TOOL_EXECUTION_TIME.labels(tool=tool_name).time():
            try:
                # Enforce a hard timeout on the tool execution (e.g., 5 seconds)
                # This prevents the Voice Engine from hanging indefinitely
                result = await asyncio.wait_for(
                    tool.run(**arguments), 
                    timeout=5.0
                )
                return result
            
            except asyncio.TimeoutError:
                TOOL_ERRORS.labels(tool=tool_name, type="timeout").inc()
                return "The external tool timed out. Please try again later."
            
            except Exception as e:
                TOOL_ERRORS.labels(tool=tool_name, type="crash").inc()
                return f"The tool encountered an error: {str(e)}"