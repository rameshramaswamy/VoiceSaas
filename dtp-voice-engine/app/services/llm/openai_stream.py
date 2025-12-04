import json
import structlog
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from app.core.config import settings
from app.services.base import LLMService

logger = structlog.get_logger()

class OpenAIStream(LLMService):
    def __init__(self):
        """
        Initializes the LLM Service with OpenAI and a connection to the Intelligence Brain.
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.brain_url = settings.INTELLIGENCE_ENGINE_URL # e.g., "http://dtp-intelligence:8090"
        
        # Context Management
        self.history: List[Dict[str, Any]] = []
        self.system_prompt_set = False
        
        # Usage Tracking (For Phase 5 Billing)
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def _update_history(self, role: str, content: str = None, tool_calls: List = None, name: str = None):
        """
        Maintains the conversation context window.
        """
        msg = {"role": role}
        if content:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if name:
            msg["name"] = name  # Required for tool_result messages
            
        self.history.append(msg)
        
        # Simple Sliding Window (Keep System + Last 10 messages)
        if len(self.history) > 11:
            # Preserve System Prompt [0] and slice the rest
            self.history = [self.history[0]] + self.history[-10:]

    async def _fetch_tools_config(self) -> List[Dict]:
        """
        Phase 4 Integration: Asks the Brain for available tools (Calendar, CRM, etc.)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.brain_url}/api/v1/tools/definitions", timeout=2.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("tools", [])
                return []
        except Exception as e:
            logger.warning("failed_to_fetch_tools", error=str(e))
            return []

    async def _execute_tool_remote(self, tool_name: str, arguments: Dict) -> str:
        """
        Phase 4 Integration: Executes the tool on the Intelligence Engine.
        """
        try:
            async with httpx.AsyncClient() as client:
                payload = {"tool_name": tool_name, "arguments": arguments}
                response = await client.post(
                    f"{self.brain_url}/api/v1/tools/execute", 
                    json=payload, 
                    timeout=10.0 # Tools might take time (e.g. searching vectors)
                )
                if response.status_code == 200:
                    return response.json().get("result", "Done.")
                return f"Error: Tool execution failed with status {response.status_code}"
        except Exception as e:
            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            return "Error: Internal system failure during tool execution."

    async def get_response_stream(
        self, 
        prompt: str, 
        system_prompt: str = "You are a helpful assistant."
    ) -> AsyncGenerator[str, None]:
        """
        The Core Loop:
        1. Add User Input to History
        2. Fetch Tools
        3. Call OpenAI
        4. Handle Stream (Text vs Tool Calls)
        5. If Tool Call -> Execute -> Recurse
        """
        
        # 1. Initialize System Prompt (Once)
        if not self.system_prompt_set:
            self.history.insert(0, {"role": "system", "content": system_prompt})
            self.system_prompt_set = True

        # 2. Add User Message
        self._update_history("user", content=prompt)
        
        # 3. Fetch Tools (Dynamic based on tenant/agent config potentially)
        tools = await self._fetch_tools_config()
        
        # 4. Start Streaming Loop
        # We might loop multiple times if tools are called (Re-entrant)
        while True:
            # Estimate prompt tokens (rough approximation for billing)
            self.token_usage["prompt_tokens"] += len(str(self.history)) // 4
            
            stream = await self.client.chat.completions.create(
                model="gpt-4o", # Use 4o for speed + intelligence
                messages=self.history,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                stream=True,
                temperature=0.7,
                max_tokens=300
            )

            # State for aggregating chunks
            current_content = ""
            tool_calls_buffer = {} # Index -> {name, args_str, id}
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Case A: Text Content (Speak immediately)
                if delta.content:
                    token = delta.content
                    current_content += token
                    self.token_usage["completion_tokens"] += 1
                    yield token

                # Case B: Tool Call (Buffer it)
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "arguments": ""
                            }
                        
                        # Append fragment
                        if tool_call.function.name:
                            tool_calls_buffer[idx]["name"] = tool_call.function.name
                        if tool_call.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tool_call.function.arguments

            # End of Stream for this turn
            
            # 5. Check if we did a Tool Call
            if tool_calls_buffer:
                # We have tools to execute. 
                # First, append the Assistant's "Intent" to history
                assistant_msg_tool_calls = []
                for idx in sorted(tool_calls_buffer.keys()):
                    t = tool_calls_buffer[idx]
                    assistant_msg_tool_calls.append({
                        "id": t["id"],
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "arguments": t["arguments"]
                        }
                    })
                
                # If there was text mixed with tools (rare but possible), add it
                self._update_history("assistant", content=current_content if current_content else None, tool_calls=assistant_msg_tool_calls)
                
                # 6. Execute Tools (Phase 4 Integration)
                for tool_data in assistant_msg_tool_calls:
                    func_name = tool_data["function"]["name"]
                    call_id = tool_data["id"]
                    try:
                        args = json.loads(tool_data["function"]["arguments"])
                        logger.info("executing_tool", tool=func_name, args=args)
                        
                        # Call Brain
                        result_text = await self._execute_tool_remote(func_name, args)
                        
                    except json.JSONDecodeError:
                        result_text = "Error: Invalid arguments generated."
                    
                    # 7. Append Tool Result to History
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": str(result_text)
                    })
                
                # 8. Loop continues! 
                # OpenAI will now see the tool results and generate the spoken response.
                continue
            
            else:
                # No tools called. This was a normal response.
                # Update history with the final text
                if current_content:
                    self._update_history("assistant", content=current_content)
                
                # Break the loop, we are done
                break

    def get_usage(self) -> Dict[str, int]:
        """Returns token counts for Phase 5 Billing"""
        return self.token_usage