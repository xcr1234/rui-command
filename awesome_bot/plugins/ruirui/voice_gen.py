import time
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
import requests
import logging
from .mongo_store import save_voice_log
from .voice_llm import generate_llm, prompt_dict
from datetime import datetime

voice_key = 'sk-df1b1b09431212125006cc6f12a5c8db'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def voice_gen_impl(text: str, event: GroupMessageEvent):
    logging.info(f'input {text}')

    emotion_text, response_text = generate_llm(text, event.group_id, event.user_id)

    prompt_id = prompt_dict.get(emotion_text, 'default')

    # Step 1: 异步生成语音
    generate_url = 'https://v1.vocu.ai/api/tts/generate'
    headers = {'Authorization': f'Bearer {voice_key}'}
    payload = {
        "contents": [
            {
                "voiceId": "5088f41c-3ede-46d7-891d-a75970c17eac",
                "text": response_text,
                "promptId": prompt_id
            }
        ]
    }
    res1 = requests.post(generate_url, headers=headers, json=payload)
    res1.raise_for_status()
    json1 = res1.json()
    logging.debug(f'Generate response: {json1}')

    if json1['status'] != 200:
        raise Exception(f'Generate failed: {json1["message"]}')

    task_id = json1['data']['id']
    logging.info(f'audio task id: {task_id}')
    # Step 2: 查询状态
    time.sleep(5)
    status_url = f'https://v1.vocu.ai/api/tts/generate/{task_id}'
    while True:
        res2 = requests.get(status_url, headers=headers)
        res2.raise_for_status()
        json2 = res2.json()
        logging.debug(f'Status response: {json2}')

        if json2['status'] != 200:
            raise Exception(f'Status check failed: {json2["message"]}')

        status = json2['data']['status']
        if status == 'generated':
            audio: str = json2['data']['metadata']['contents'][0]['audio']
            logging.info(f'Generated audio: {audio}')
            return audio, response_text, emotion_text
        elif status == 'processing':
            time.sleep(5)
        else:
            raise Exception(f'Unexpected status: {status}')



voice = on_command('voice', priority=10, block=True)


def download_url_to_file(url, file_path):
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功

    # 将内容写入文件
    with open(file_path, 'wb') as file:
        file.write(response.content)


@voice.handle()
async def handle_function(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await voice.finish('请输入文字')
    elif len(text) >= 25:
        await voice.finish('太长了...')
    else:
        try:
            voice_url, response_text, emotion_text = voice_gen_impl(text, event)
        except Exception as e:
            logging.exception(f'生成失败 {e}')
            await voice.finish(f'生成失败: \n {str(e)}')
            return
        if isinstance(event, GroupMessageEvent):
            save_voice_log({
                'input': text,
                'res_time': datetime.utcnow(),
                'group_id': event.group_id,
                'send_user_id': event.user_id,
                'emotion_text': emotion_text,
                'response_text': response_text,
                'voice_url': voice_url,
            })
        await voice.finish(MessageSegment.record(file=voice_url))
