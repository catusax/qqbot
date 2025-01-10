import base64
import httpx
import nonebot

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot_plugin_alconna.uniseg import UniMsg, At, Reply
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    PrivateMessageEvent,
    MessageEvent,
    helpers,
)
from nonebot.plugin import PluginMetadata
from .config import Config, ConfigError
from openai import AsyncOpenAI
from .openai_chat import chat_with_tools

from .tools import Weather

builtin_tools = [
    Weather()
]

__plugin_meta__ = PluginMetadata(
    name="OneAPI和OpenAI聊天Bot",
    description="具有上下文关联和多模态识别，适配OneAPI和OpenAI官方的nonebot插件。",
    usage="""
    @机器人发送问题时机器人不具有上下文回复的能力
    chat 使用该命令进行问答时，机器人具有上下文回复的能力
    lear 清除当前用户的聊天记录
    """,
    config=Config,
    extra={},
    type="application",
    homepage="https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo",
    supported_adapters={"~onebot.v11"},
)

plugin_config = Config.model_validate(nonebot.get_driver().config.model_dump())

if not plugin_config.oneapi_key:
    raise ConfigError("请配置大模型使用的KEY")
if plugin_config.oneapi_url:
    client = AsyncOpenAI(
        api_key=plugin_config.oneapi_key, base_url=plugin_config.oneapi_url
    )
else:
    client = AsyncOpenAI(api_key=plugin_config.oneapi_key)

model_id = plugin_config.oneapi_model

# public = plugin_config.chatgpt_turbo_public
session = {}

# 带上下文的聊天
chat_record = on_command("chat", block=False, priority=1)

# 不带上下文的聊天
chat_request = on_command("", rule=to_me(), block=False, priority=99)

# 清除历史记录
clear_request = on_command("clear", block=True, priority=1)

# 带记忆的聊天


@chat_record.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    # 若未开启私聊模式则检测到私聊就结束
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")
    content = msg.extract_plain_text()
    img_url = helpers.extract_image_urls(event.message)
    if content == "" or content is None:
        await chat_record.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    # await chat_request.send(
    #     MessageSegment.text("ChatGPT正在思考中......"), at_sender=True
    # )
    session_id = event.get_session_id()
    if session_id not in session:
        session[session_id] = []
    session[session_id].append(
        {"role": "system", "content": plugin_config.oneapi_prompt}),

    if not img_url:
        try:
            session[session_id].append({"role": "user", "content": content})
            response = await chat_with_tools(client=client, model=model_id,
                                             messages=session[session_id], tools=builtin_tools)
        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
        await chat_record.finish(
            MessageSegment.text(str(response.choices[0].message.content)),
            at_sender=True,
        )
    else:
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")
            session[session_id].append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": content},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_data}"},
                        },
                    ],
                }
            )
            response = await chat_with_tools(client=client, model=model_id,
                                             messages=session[session_id], tools=builtin_tools)

        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
        await chat_record.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


# 不带记忆的对话
@chat_request.handle()
async def _(event: MessageEvent, msg: UniMsg):
    messages = msg.extract_plain_text()
    event.message.get
    img_url = helpers.extract_image_urls(event.message)
    if event.reply is not None:
        reply = msg[Reply, 0]
        if isinstance(reply.msg, Message):
            messages += '\n' + reply.msg.extract_plain_text()
            img_url.extend(helpers.extract_image_urls(reply.msg))
        if isinstance(reply.msg, str):
            messages += '\n' + reply.msg

    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")

    content = messages
    if content == "" or content is None:
        await chat_request.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    # await chat_request.send(
    #     MessageSegment.text("ChatGPT正在思考中......"), at_sender=True
    # )
    if not img_url:
        try:

            response = await chat_with_tools(client=client, model=model_id,
                                             messages=[
                                                 {"role": "system",
                                                     "content": plugin_config.oneapi_prompt},
                                                 {"role": "user", "content": content}], tools=builtin_tools)
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(
            MessageSegment.text(str(response.choices[0].message.content)),
            at_sender=True,
        )
    else:
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")

            messages = [
                {"role": "system",
                 "content": plugin_config.oneapi_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            },
                        },
                    ],
                }
            ]

            response = await chat_with_tools(client=client, model=model_id,
                                             messages=messages, tools=builtin_tools)
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


@clear_request.handle()
async def _(event: MessageEvent):
    del session[event.get_session_id()]
    await clear_request.finish(
        MessageSegment.text("成功清除历史记录！"), at_sender=True
    )


# # 根据消息类型创建会话id
# def create_session_id(event):
#     if isinstance(event, PrivateMessageEvent):
#         session_id = f"Private_{event.user_id}"
#     elif public:
#         session_id = event.get_session_id().replace(f"{event.user_id}", "Public")
#     else:
#         session_id = event.get_session_id()
#     return session_id
