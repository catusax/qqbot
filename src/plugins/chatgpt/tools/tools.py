from .tool import Tool, ToolParameter, ParamType
from datetime import datetime


def get_tools() -> list[Tool]:
    return [
        Time(),
    ]


class Time(Tool):

    def __init__(self):
        params = []

        super().__init__(
            name="time",
            description="get current time",
            parameters=params,
        )

    def call_tool(self, args):
        super().call_tool(args)
        t = datetime.now()
        return t.strftime("%Y-%m-%d %H:%M:%S")
