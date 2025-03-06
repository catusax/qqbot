from typing import List, Optional, Self, Callable, Coroutine, Any, Union
from asyncpg import create_pool, Pool
from pydantic import BaseModel
from datetime import datetime
from openai import AsyncOpenAI
from .singleton import Singleton


class ChatMessage(BaseModel):
    user_id: int
    nick_name: str
    message: str
    message_id: int
    time: datetime
    group: int
    vector_message: Optional[str] = None

    @classmethod
    def from_pgrecord(self, data: Any) -> Self:
        return ChatMessage(
            message_id=data["id"],
            user_id=data["user_id"],
            nick_name=data["nick_name"],
            message=data["chat_message"],
            time=data["time"],
            group=data["group_id"],
            vector_message=data["vector_message"],
        )

    @classmethod
    async def create_table(self, conn: Pool):
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        res = await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id BIGINT PRIMARY KEY,
                group_id BIGINT,
                time TIMESTAMPTZ,
                chat_message TEXT,
                vector_message VECTOR(1024),
                user_id BIGINT,
                nick_name TEXT
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS chat_history_vector_message_idx ON chat_history USING ivfflat (vector_message vector_cosine_ops)
            """
        )

    async def save(self, conn: Pool):

        # check if same chat_message exists
        data = await conn.fetch(
            """
            SELECT * FROM chat_history
            WHERE chat_message = $1 limit 1
            """,
            self.message,
        )

        if len(data) > 0:
            cache = ChatMessage.from_pgrecord(data[0])
            vector_message = cache.vector_message
        else:
            vector_message_list = await EmbeddingClient().get_vector_message(self.message)
            vector_message = vector_message_list.__str__() if len(
                vector_message_list) > 0 else None

        res = await conn.execute(
            """
            INSERT INTO chat_history (id, time,group_id, chat_message, vector_message, user_id, nick_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            self.message_id,
            self.time,
            self.group,
            self.message,
            vector_message,
            self.user_id,
            self.nick_name,
        )
        print(res)

    @classmethod
    async def load_similar(self, conn: Pool, group: int, message: str, topk: int = 5, time=False) -> List[Self]:

        vector = await EmbeddingClient().get_vector_message(message)

        res = await conn.fetch(
            f"""
            SELECT * FROM chat_history
            WHERE group_id = $1 AND vector_message <-> $2 < 0.9 {"AND time > NOW() - INTERVAL '1 DAY'" if time else ""}
            ORDER BY vector_message <=> $2
            LIMIT $3
            """,
            group,
            vector.__str__(),
            topk,
        )
        return [ChatMessage.from_pgrecord(item) for item in res]

    @classmethod
    async def load_context(self, conn: Pool, group: int, context: int):
        res = await conn.fetch(
            f"""
            SELECT * FROM chat_history
            WHERE group_id = $1
            ORDER BY time DESC
            LIMIT $2
            """,
            group,
            context,
        )
        return [ChatMessage.from_pgrecord(item) for item in res]


pgconn = None


async def init_pgconn(postgres_url: str):
    global pgconn
    if pgconn is None:
        pgconn = await create_pool(dsn=postgres_url)
    return pgconn


class EmbeddingClient(Singleton):
    client: Optional[AsyncOpenAI] = None
    model: str = ""

    def __init__(self, client: Optional[AsyncOpenAI] = None, model: str = ""):
        self.client = client
        self.model = model

    async def get_vector_message(self, message: str) -> Union[list[float], None]:
        if self.client is None:
            return []
        response = await self.client.embeddings.create(
            input=message,
            model=self.model,
        )
        return response.data[0].embedding
