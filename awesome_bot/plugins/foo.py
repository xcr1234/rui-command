import os
import random
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import logger

rui = on_command('rui', priority=10, block=True)


def list_files(directory):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")

        # 获取目录及其子目录中的所有文件
    all_files = []
    for root, _, files in os.walk(directory, followlinks=True):
        for file in files:
            all_files.append(os.path.join(root, file))

    # 如果没有找到任何文件，抛出异常
    if not all_files:
        raise ValueError(f"No files found in the directory '{directory}' or its subdirectories.")

    return all_files


def get_random_file(directory):
    """
    从指定目录及其子目录中随机选择一个文件，并返回其完整路径。

    :param directory: 要搜索的根目录
    :return: 随机选择的文件的完整路径
    """

    # 获取目录及其子目录中的所有文件
    all_files = list_files(directory)

    # 随机选择一个文件
    random_file = random.choice(all_files)

    return random_file

def is_hero_command(file: str, command: str):
    file_name = file.replace('/opt/voices/ow/','', 1)
    return command in file_name


@rui.handle()
async def handle_function(args: Message = CommandArg()):
    real_command = args.extract_plain_text().strip()
    if real_command == 'hello':
        logger.info('say hello')
        await rui.finish('hello')
    elif real_command == '':
        random_file = get_random_file('/opt/voices/ow')
        logger.info(f'ow voice file {random_file}')
        await rui.finish(MessageSegment.record(file=random_file))
    else:
        all_files = list_files('/opt/voices/ow')
        command_files = list(filter(lambda file: is_hero_command(file, real_command), all_files))
        if len(command_files) == 0:
            await rui.finish('没找到这个英雄')
        else:
            command_file = random.choice(command_files)
            logger.info(f'ow voice file {command_file}')
            await rui.finish(MessageSegment.record(file=command_file))