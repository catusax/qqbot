
from .tool import Tool
from .tools import Time


def get_tools(enabled: list[str]) -> list[Tool]:
    tools = {
        "time": Time(),
    }
    res = []
    for t in enabled:
        if t in tools:
            res.append(tools[t])
    return res
