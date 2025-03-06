
from enum import Enum
from dataclasses import dataclass
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion


class ParamType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "array"


@dataclass
class ToolParameter:
    name: str
    type: ParamType
    description: str
    subtype: ParamType | None = None
    required: bool = True

    def __str__(self):
        return f"{self.name}: {self.description}"

    def to_openai_tool(self):
        if self.type == ParamType.LIST:
            return {
                "type": self.type.value,
                "description": self.description,
                "items": {"type": self.subtype}
            }
        return {
            "type": self.type.value,
            "description": self.description,
        }


@dataclass
class Tool:
    name: str
    description: str
    parameters: list[ToolParameter]

    def to_openai_tool(self) -> ChatCompletionToolParam:

        parameters = {}
        for param in self.parameters:

            parameters[param.name] = param.to_openai_tool()

        if len(self.parameters) == 0:
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                },
            }
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters
                },
            },
        }

    def call_tool(self, args: dict) -> str:
        print(
            f"\n\ncalling tool {self.name} with args {args}\n\n")
        pass
