from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import logger

rui = on_command('rui',priority=10, block=True)

@rui.handle()
async def handle_function(args: Message = CommandArg()):
    real_command = args.extract_plain_text()
    if real_command == 'hello':
        logger.info('say hello')
        await rui.finish('hello')