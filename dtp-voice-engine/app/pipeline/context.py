from typing import List, Dict

class ContextManager:
    def __init__(self, system_prompt: str, max_tokens: int = 4000):
        self.system_prompt = {"role": "system", "content": system_prompt}
        self.history: List[Dict[str, str]] = []
        self.max_history_len = 10 # Keep last 5 turns (User + Assistant)

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})
        self._prune()

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})
        self._prune()

    def _prune(self):
        """Simple sliding window"""
        if len(self.history) > self.max_history_len:
            self.history = self.history[-self.max_history_len:]

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        return [self.system_prompt] + self.history