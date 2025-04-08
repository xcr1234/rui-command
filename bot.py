import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from pathlib import Path

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 在这里加载插件
#nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugin(Path("./awesome_bot/plugins/foo.py"))  # 加载项目插件


if __name__ == "__main__":
    nonebot.run()