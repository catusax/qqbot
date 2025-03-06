
from collections import OrderedDict
from typing import List, Optional, Union, Tuple
from dataclasses import dataclass


@dataclass
class ChatMessage():
    role: str
    content: str


class PromptBuilder():
    prompt: str
    history: List[ChatMessage]

    def __init__(self, prompt: str = ""):
        self.prompt = prompt.strip()
        self.history = []

    def add_history(self, role: str, message: str):
        self.history.append(ChatMessage(role=role, content=message))

    def add_prompt(self, prompt: str):
        self.prompt += prompt.strip()

    def build(self) -> str:
        last_message = self.prompt
        if not last_message:
            last_message = self.history.pop().content

        prompt = ""
        if len(self.history) > 0:
            prompt += "<context>"
            for message in self.history:
                prompt += f"'{message.role}' 说: {message.content}\n\n"
            prompt = prompt.removesuffix("\n") + "<context>\n\n"
        prompt += last_message
        return prompt
