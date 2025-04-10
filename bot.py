import sys

import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from pathlib import Path
from nonebot.log import default_format, default_filter, logger_id, logger


def custom_filter(record):
    return default_filter(record) and( '[message.group.normal]' not in record['message'] or '/rui' in record['message'])

# 移除 NoneBot 默认的日志处理器
logger.remove(logger_id)
# 添加新的日志处理器
logger.add(
    sys.stdout,
    level=0,
    diagnose=True,
    format=default_format,
    filter=custom_filter
)

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 在这里加载插件
#nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugin(Path("./awesome_bot"))

if __name__ == "__main__":
    nonebot.run()