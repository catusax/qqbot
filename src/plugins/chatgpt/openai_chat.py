
from typing import Iterable
from openai import AsyncOpenAI

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion
from openai import NotGiven
import json

from .tools import Tool
from .singleton import Singleton
from .session import SessionStorage, Session
from .config import PromptGetter


class OpenAIChat(Singleton):
    def __init__(self, client: AsyncOpenAI, model: str, prompt: PromptGetter, session_storage: SessionStorage):
        self.client = client
        self.model = model
        self.session_storage = session_storage
        self.session_storage.prompt = prompt

    async def chat_with_tools(self, session: Session, messages: list[ChatCompletionMessageParam], tools: list[Tool], add_tools=True) -> ChatCompletion:

        old_session = await self.session_storage.get_session(session)
        await self.session_storage.append_message(session, messages)
        old_session.extend(messages)
        new_session = old_session

        print(
            f"chat_with_tools: {session.to_session_id()} ::: {new_session}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=new_session,
            tools=[tool.to_openai_tool()
                   for tool in tools] if add_tools and len(tools) > 0 else NotGiven(),
        )

        resp_message = response.choices[0].message
        resp_message_dict = resp_message.to_dict()

        resp_message_dict.pop('reasoning_content', None)

        # print(f"chat_with_tools_response: {response.choices[0]}")

        await self.session_storage.append_message(
            session, [resp_message_dict])

        if resp_message.tool_calls:
            toolcalls = resp_message.tool_calls

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
                        await self.session_storage.append_message(
                            session, [function_call_result_message])
                        break

            response = await self.chat_with_tools(session, [], tools, add_tools=False)
        return response
