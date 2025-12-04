from typing import Dict, List
from app.tools.base.tool import BaseTool
from app.tools.calendar.google import GoogleCalendarTool

class ToolExecutor:
    def __init__(self):
        # Register available tools
        self.tools: Dict[str, BaseTool] = {}
        self._register(GoogleCalendarTool())
        
        # Future: self._register(OutlookTool())
        # Future: self._register(CRMTool())

    def _register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_tool_definitions(self) -> List[Dict]:
        """
        Returns JSON schemas to send to OpenAI 'functions' parameter.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        Runs the python logic.
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found."
        
        # Execute
        result = await tool.run(**arguments)
        return result