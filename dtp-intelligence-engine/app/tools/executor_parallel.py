import asyncio
import structlog
from typing import List, Dict, Any
from app.tools.executor_robust import RobustToolExecutor

logger = structlog.get_logger()

class ParallelToolExecutor(RobustToolExecutor):
    async def execute_batch(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """
        Executes multiple tool calls concurrently.
        
        tool_calls format: 
        [
            {"name": "check_calendar", "args": {"date": "2023-10-01"}},
            {"name": "check_calendar", "args": {"date": "2023-10-02"}}
        ]
        """
        tasks = []
        for call in tool_calls:
            tool_name = call.get("name")
            args = call.get("args", {})
            
            logger.info("queueing_tool", tool=tool_name, args=args)
            
            # Use the robust parent method (Circuit Breaker/Timeout logic)
            tasks.append(self.execute_tool(tool_name, args))

        # Run all concurrently
        if not tasks:
            return []
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results
        final_outputs = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("batch_tool_error", error=str(res))
                final_outputs.append(f"Tool call {i+1} failed.")
            else:
                final_outputs.append(res)
                
        return final_outputs