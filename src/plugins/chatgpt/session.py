from dataclasses import dataclass
import time
from typing import Any, Self
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion, ChatCompletionMessage
from asyncpg import Pool
import json
from datetime import datetime

from .config import PromptGetter


@dataclass
class Session():
    chat_id: str
    chat_type: str
    raw_session_id: str

    def to_session_id(self) -> str:
        if self.raw_session_id == "":
            return self.chat_type + "_" + self.chat_id
        return self.raw_session_id

    def is_group(self) -> bool:
        return self.chat_type == "group"

    def is_private(self) -> bool:
        return self.chat_type == "private"


class SessionStorage():
    prompt: PromptGetter

    async def get_session(self, session: Session) -> list[ChatCompletionMessageParam]:
        raise NotImplementedError()

    async def append_message(self, session: Session, messages: list[ChatCompletionMessageParam]) -> None:
        raise NotImplementedError()

    async def clear(self, session: Session) -> None:
        raise NotImplementedError()

    async def clear_all(self) -> None:
        raise NotImplementedError()

    def get_prompt(self, session: Session) -> str:
        return self.prompt.get_prompt(session.chat_id)


class MemSessionStorage(SessionStorage):

    def __init__(self):
        self.sessions = {}
        self.sessions_update_time = {}

    async def get_session(self, session: Session) -> list[ChatCompletionMessageParam]:
        # if session is 30 minutes, clear it
        session_id = session.to_session_id()
        if session_id in self.sessions_update_time:
            if self.sessions_update_time[session_id] + (30 * 60) < time.time():
                del self.sessions[session_id]
                del self.sessions_update_time[session_id]
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system",
                 "content": self.get_prompt(session)},
            ]
        msgs = self.sessions[session_id]
        if msgs and msgs[0]["role"] == "system":  # full context
            return msgs

        # remove any thing before the first user message
        for i, msg in enumerate(msgs):
            if msg["role"] == "user":
                msgs = msgs[i:]
                break
        msgs = [{"role": "system", "content": self.get_prompt(session)}] + msgs
        return msgs

    async def clear(self, session: Session):
        session_id = session.to_session_id()
        del self.sessions[session_id]
        del self.sessions_update_time[session_id]

    async def clear_all(self):
        self.sessions = {}
        self.sessions_update_time = {}

    async def append_message(self, session: Session, messages: list[ChatCompletionMessageParam]) -> None:
        if len(messages) == 0:
            return
        session = self.get_session(session)
        session.extend(messages)


class DBSessionStorage(SessionStorage):
    pool: Pool
    ttl: float = 30 * 60
    context_size: int = 20

    @dataclass
    class SessionMessage():
        # primary key
        message_id: int
        session_id: str
        message: str
        update_time: datetime

        @classmethod
        def from_pgrecord(self, data: Any) -> Self:
            return DBSessionStorage.SessionMessage(
                message_id=data["message_id"],
                session_id=data["session_id"],
                message=data["message"],
                update_time=data["update_time"],
            )

    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_table(self):
        await self.pool.execute(
            """CREATE TABLE IF NOT EXISTS chat_session (
                message_id SERIAL PRIMARY KEY,
                session_id TEXT,
                message JSONB,
                update_time TIMESTAMPTZ DEFAULT NOW())
            """)

    async def _session_get(self, session_id: str) -> list[SessionMessage]:
        res = await self.pool.fetch(
            "SELECT * FROM chat_session WHERE session_id = $1 ORDER BY message_id DESC limit $2", session_id, self.context_size)
        sessions = [self.SessionMessage.from_pgrecord(data) for data in res]
        return sessions

    async def get_session(self, session: Session) -> list[ChatCompletionMessageParam]:
        session_id = session.to_session_id()
        session_data = await self._session_get(session_id)
        if len(session_data) > 0:
            if session_data[-1].update_time.timestamp() + self.ttl < time.time():
                await self.clear(session)
                return [{"role": "system", "content": self.get_prompt(session)}]
        else:
            return [{"role": "system", "content": self.get_prompt(session)}]
        msgs = [json.loads(msg.message) for msg in session_data]
        msgs.reverse()

        if msgs and msgs[0]["role"] == "system":  # full context
            return msgs

        # remove any thing before the first user message
        for i, msg in enumerate(msgs):
            if msg["role"] == "user":
                msgs = msgs[i:]
                break
        msgs = [{"role": "system", "content": self.get_prompt(session)}] + msgs
        return msgs

    async def append_message(self, session: Session, messages: list[ChatCompletionMessageParam]) -> None:
        session_id = session.to_session_id()
        for message in messages:
            if isinstance(message, ChatCompletionMessage):
                content = message.model_dump_json()
            else:
                content = json.dumps(message)
            await self.pool.execute(
                "INSERT INTO chat_session (session_id, message) VALUES ($1, $2)", session_id, content)

    async def clear(self, session: Session) -> None:
        await self.pool.execute(
            "DELETE FROM chat_session WHERE session_id = $1", session.to_session_id())

    async def clear_all(self):
        await self.pool.execute("DELETE FROM chat_session")
