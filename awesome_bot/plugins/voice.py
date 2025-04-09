from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import MessageSegment
from voice_gen import voice_gen_impl

voice = on_command('voice', priority=10, block=True)

@voice.handle()
async def handle_function(args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await voice.finish('请输入文字')
        return
    if len(text) >= 20:
        await voice.finish('太长了...')
        return
    voice_url = voice_gen_impl(text)
    await voice.finish(MessageSegment.record(file=voice_url))