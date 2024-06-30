import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 在这里加载插件
# nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugin("nonebot_plugin_status")
nonebot.load_plugin("nonebot_plugin_plus_one")
nonebot.load_plugin("nonebot_plugin_memes")
# nonebot.load_plugin("nonebot_plugin_apscheduler")

nonebot.load_plugins("src/plugins")  # 本地插件

if __name__ == "__main__":
    nonebot.run()
