from typing import List
from pydantic.v1 import BaseModel


class ShortTermMemory(BaseModel):
    messages: List = []

    def remember(self, role: str, content: str, tool_call_id: int = None) -> None:
        if tool_call_id:
            message = {"role": role, "content": content, "tool_call_id": tool_call_id}
            self.messages.append(message)
        else:
            message = {"role": role, "content": content}
            self.messages.append(message)

    def recall(self):
        return self.messages

    def last_message(self):
        return self.messages[-1]

    def clear(self) -> None:
        self.messages = []
