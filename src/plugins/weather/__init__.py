from nonebot import on_command
from nonebot import on_message
from nonebot.rule import to_me

weather = on_command("天气")


@weather.handle()
async def handle_function():
    await weather.finish("天气是...")
