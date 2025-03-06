import base64
import traceback
import httpx

from nonebot import get_bot, on_command, on_message
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot_plugin_alconna.uniseg import UniMsg, At, Reply
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageEvent,
    helpers,
)
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.plugin import PluginMetadata
from nonebot import get_driver
from openai import AsyncOpenAI

from .config import Config, plugin_config, ConfigError
from .openai_chat import OpenAIChat
from .chat_history import ChatMessage, init_pgconn, EmbeddingClient
from .prompt_builder import PromptBuilder

from .tools import get_tools
from .session import DBSessionStorage, MemSessionStorage, Session
import asyncio

builtin_tools = get_tools(plugin_config.oneapi_enabled_tools)

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

pgconn = None
inited = False


driver = get_driver()


@driver.on_startup
async def do_something():
    plugin_config.prompt_getter()
    global inited
    if inited:
        return
    if plugin_config.oneapi_postgres_url:
        global pgconn
        pgconn = await init_pgconn(plugin_config.oneapi_postgres_url)
        session_storage = DBSessionStorage(pgconn)
        await session_storage.create_table()
    else:
        session_storage = MemSessionStorage()

    if not plugin_config.oneapi_key:
        raise ConfigError("请配置大模型使用的KEY")
    if plugin_config.oneapi_url:
        client = AsyncOpenAI(
            api_key=plugin_config.oneapi_key, base_url=plugin_config.oneapi_url
        )
    else:
        client = AsyncOpenAI(api_key=plugin_config.oneapi_key)

    OpenAIChat(client=client, model=plugin_config.oneapi_model,
               prompt=plugin_config.prompt_getter(), session_storage=session_storage)

    if plugin_config.oneapi_embedding in ("yes", "true", "t", "1"):
        if not plugin_config.oneapi_embedding_key:
            EmbeddingClient(client=client,
                            model=plugin_config.oneapi_embedding_model)
        else:
            embedding_client = AsyncOpenAI(
                api_key=plugin_config.oneapi_embedding_key,
                base_url=plugin_config.oneapi_embedding_url,
            )
            EmbeddingClient(
                client=embedding_client,
                model=plugin_config.oneapi_embedding_model)
    else:
        EmbeddingClient()

    inited = True


# 带用户上下文的聊天
chat_record = on_command("chat", block=False, priority=1)

# 群聊/私聊
chat_request = on_command("", rule=to_me(), block=False, priority=99)

# 清除历史记录
clear_request = on_command("clear", block=True, priority=1)

chat_history = on_message(priority=2, block=False)

search_history = on_command("历史", priority=1, rule=to_me(), block=True)


@chat_history.handle()
async def _(event: MessageEvent, msg: UniMsg):

    message_id = event.message_id

    if (session := event.get_session_id()).startswith("group_"):
        group_id = session.split("_")[1]
    else:
        return

    msg = msg.extract_plain_text()

    message = ChatMessage(
        group=int(group_id),
        message=msg,
        message_id=message_id,
        nick_name=get_sender_name(event.sender),
        user_id=event.sender.user_id,
        time=event.time,
    )

    await message.save(pgconn)


@search_history.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):

    if (session := event.get_session_id()).startswith("group_"):
        group_id = int(session.split("_")[1])
    else:
        return

    msg = msg.extract_plain_text()

    if msg == "":
        return

    history = await ChatMessage.load_similar(pgconn, group_id, msg, topk=5)
    if len(history) == 0:
        await search_history.finish("没有找到相关记录")

    messages = MessageSegment.text("以下是历史记录：\n")
    for i, message in enumerate(history):
        messages += f"{i+1}. {message.nick_name}: {message.message}\n"

    await search_history.finish(messages)


@chat_record.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    # 若未开启私聊模式则检测到私聊就结束
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")
    content = msg.extract_plain_text().strip()
    img_url = helpers.extract_image_urls(event.message)

    session = create_session(event)

    if content.startswith("context="):
        context_len = int(content.split("=")[1].split(" ")[0])
        content_text = content.split("=")[1].split(" ")[1]
        if (session.is_group()):
            group_id = int(session.chat_id)
            context = await ChatMessage.load_context(pgconn, group_id, min(context_len+1, 30))

            context_text = "下面是当前群聊的聊天记录：\n<context>"
            for message in context:
                # skip self chat
                # if message.message.startswith("chat ") or message.user_id == int(get_bot().self_id):
                #     continue

                # skip current message
                if message.message_id == event.message_id:
                    continue
                sender = message.nick_name if message.user_id != int(
                    get_bot().self_id) else "bot"

                context_text += f"<message sender='{sender}'>{message.message}</message>\n"
            context_text += "</context>\n"
            content = context_text + content_text

    if content == "" or content is None:
        await chat_record.finish(MessageSegment.text("内容不能为空！"), at_sender=True)

    if not img_url:
        try:
            messages = [{"role": "user", "content": content}]
            response = await OpenAIChat().chat_with_tools(session=session, messages=messages, tools=builtin_tools)
        except Exception as error:
            traceback.print_exc()
            await chat_record.finish(str(error), at_sender=True)
        await chat_record.finish(
            MessageSegment.text(str(response.choices[0].message.content)),
            at_sender=True,
        )
    else:
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")
            messages = [
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
            ]
            response = await OpenAIChat().chat_with_tools(session, messages, builtin_tools)

        except Exception as error:
            traceback.print_exc()
            await chat_record.finish(str(error), at_sender=True)
        await chat_record.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


# 不带记忆的对话
@chat_request.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    session = create_session(event)

    prompt_builder = PromptBuilder(msg.extract_plain_text())
    img_url = helpers.extract_image_urls(event.message)
    if event.reply is not None and event.reply.sender.user_id != int(get_bot().self_id):
        reply = event.reply
        sender_nickname: str = get_sender_name(reply.sender)
        reply_text = ""
        if isinstance(reply.message, Message):
            reply_text = reply.message.extract_plain_text()
            img_url.extend(helpers.extract_image_urls(reply.message))
        if isinstance(reply.message, str):
            reply_text = reply.message
        prompt_builder.add_history(sender_nickname, reply_text)

    content = prompt_builder.build()
    if content == "":
        await chat_request.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    if not img_url:
        try:

            response = await OpenAIChat().chat_with_tools(
                session=session,
                messages=[
                    {"role": "user", "content": content}], tools=builtin_tools)
        except Exception as error:
            traceback.print_exc()
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

            response = await OpenAIChat().chat_with_tools(session=session, messages=messages, tools=builtin_tools)
        except Exception as error:
            traceback.print_exc()
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


@clear_request.handle()
async def _(event: MessageEvent):
    OpenAIChat().session_storage.clear(create_session(event))
    await clear_request.finish(
        MessageSegment.text("成功清除历史记录！"), at_sender=True
    )


# # 根据消息类型创建会话id
def create_session(event: MessageEvent) -> Session:
    if isinstance(event, PrivateMessageEvent):
        session = Session(
            chat_id=str(event.user_id),
            chat_type="private",
            raw_session_id="",
        )
    elif isinstance(event, GroupMessageEvent):
        session = Session(
            chat_id=str(event.group_id),
            chat_type="group",
            raw_session_id="",
        )
    else:
        session = Session(
            chat_id='',
            chat_type='',
            raw_session_id=event.get_session_id(),
        )
    return session


def get_sender_name(sender: Sender) -> str:
    if sender.card:
        return sender.card
    elif sender.nickname:
        return sender.nickname
    else:
        return sender.user_id
