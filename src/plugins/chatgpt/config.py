import nonebot
from pydantic import BaseModel
from typing import Optional


class Config(BaseModel, extra="allow"):
    oneapi_key: Optional[str] = ""  # （必填）OpenAI官方或者是支持OneAPI的大模型中转服务商提供的KEY
    oneapi_url: Optional[str] = ""  # （可选）大模型中转服务商提供的中转地址，使用OpenAI官方服务不需要填写
    oneapi_model: Optional[str] = "gpt-4o"  # （可选）使用的语言大模型，使用识图功能请填写合适的大模型名称
    enable_private_chat: bool = True   # 是否开启私聊对话
    # chatgpt_turbo_public: bool = True  # 是否开启群聊对话
    oneapi_prompt_default: Optional[str] = ""  # （可选）自定义的提示语

    oneapi_embedding: bool = False
    oneapi_embedding_key: Optional[str] = ""
    oneapi_embedding_url: Optional[str] = ""
    oneapi_embedding_model: Optional[str] = "text-embedding-3-small-v2"
    oneapi_postgres_url: Optional[str] = None

    oneapi_enabled_tools: list[str] = []

    oneapi_nick_name: Optional[dict] = None
    oneapi_nick_name_mapping: Optional[str] = None

    def nick_name_mapping(self):
        if self.oneapi_nick_name_mapping is None:
            return {}
        elif self.oneapi_nick_name is None:
            return eval(self.oneapi_nick_name_mapping)
        else:
            return self.oneapi_nick_name

    def prompt_getter(self):
        # find all field start with prompt_ and make a dict
        prompt_mapping = {
            k[14:]: v
            for k, v in plugin_config.model_dump().items()
            if k.startswith("oneapi_prompt_")
        }

        return PromptGetter(prompt_mapping)


class ConfigError(Exception):
    pass


class PromptGetter:
    mapping: dict

    def __init__(self, mapping: dict) -> None:
        self.mapping = mapping

    def get_prompt(self, group: int) -> str:
        if group in self.mapping:
            return self.mapping[group]
        elif "default" in self.mapping:
            return self.mapping["default"]
        else:
            return "you are a helpful assistant"


plugin_config = Config.model_validate(
    nonebot.get_driver().config.model_dump())
