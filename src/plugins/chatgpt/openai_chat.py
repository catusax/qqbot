
from typing import Iterable
from openai import AsyncOpenAI

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion
from openai import NotGiven
from .tool import Tool
import json


async def chat_with_tools(client: AsyncOpenAI, model: str, messages: Iterable[ChatCompletionMessageParam], tools: list[Tool], add_tools=True) -> ChatCompletion:

    # print(f"chat_with_tools: {messages}")

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[tool.to_openai_tool()
               for tool in tools] if add_tools and len(tool) > 0 else NotGiven(),
    )

    # print(f"chat_with_tools_response: {response.choices[0]}")

    if response.choices[0].message.tool_calls:
        messages.append(response.choices[0].message)
        toolcalls = response.choices[0].message.tool_calls

        for toolcall in toolcalls:
            for tool in tools:
                if tool.name == toolcall.function.name:
                    args = json.loads(toolcall.function.arguments)
                    resp = tool.call_tool(args)
                    function_call_result_message = {
                        "role": "tool",
                        "content": resp,
                        "tool_call_id": toolcall.id,
                    }
                    messages.append(function_call_result_message)
                    break

        response = await chat_with_tools(client, model, messages, tools, add_tools=False)

    return response
