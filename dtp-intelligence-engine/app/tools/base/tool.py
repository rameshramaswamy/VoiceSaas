from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name the LLM uses to call this tool (e.g., 'check_calendar')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description for the System Prompt so LLM knows when to use it."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema of parameters."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """
        Executes the logic.
        Returns a natural language string for the LLM to read back to the user.
        """
        pass