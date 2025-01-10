from .tool import Tool, ToolParameter, ParamType


class Weather(Tool):

    def __init__(self):
        params = [
            ToolParameter(
                name="location",
                type=ParamType.STRING,
                description="the location",
            ),
        ]

        super().__init__(
            name="weather",
            description="get the weather of a location",
            parameters=params,
        )

    def call_tool(self, args):
        super().call_tool(args)
        res = "晴天"
        return f'{res}'
