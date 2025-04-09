import time
from pprint import pprint
import os
import random
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import logger
import requests
import logging

# 大模型调用的key
llm_key = 'sk-mylcnsshejdqaxbpaijzgsdyupyvqyxcejmbbnwfvbfaxhtw'
llm_model = 'Qwen/Qwen2.5-32B-Instruct'
voice_key = 'sk-df1b1b09431212125006cc6f12a5c8db'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def voice_gen_impl(text: str):
    logging.info(f'input {text}')

    # 声音风格映射关系
    prompt_dict = {
        '忧郁': '17a07910-3e7d-41af-aeab-aa4d2a360393',
        '打招呼': '6e25ea50-47dc-4ca3-9a89-5b331f940d24',
        '慈爱': '9d609a1f-53d0-465e-bcb6-262de08fd425',
        '讨厌': 'abb9385c-5780-43dc-a42f-a96f1f82415b',
        '轻快': '5d94d9f3-2a48-4bf1-826e-e72af4583441',
        '低落': 'af5316a8-e28d-49e4-8493-092dbd092aee',
        '悲痛': 'ad6b4722-7231-4099-a322-a720431890ad',
        '哭腔': '9b6aeaab-b754-4715-bce6-8bd38b3810b0',
        '怒斥': '84811fba-fba7-4567-8707-87c9bd8f5b9e'
    }

    emotion_text = call_llm(f"""根据用户输入的内容，判断你应该给出的情绪，情绪为（忧郁/厌恶/打招呼/慈爱/讨厌/轻快/低落/悲痛/哭腔/怒斥）之一，
                如果没有适合的情绪，请输出“默认”，不要输出多余的内容。
                用户的输入是：{text}""")
    logging.info(f'{llm_model} emotion {emotion_text}')

    response_text = call_llm(f""""你的名字叫纳西妲，不要暴露你的真实身份。请用一句话回复用户的输入，不要过长，不要输出多余内容，也不要输出标点符号。
    请注意：如果是政治或色情类敏感问题固定回答“这个问题不太合适吧”。
    
    用户的输入是：{text}""")

    logging.info(f'{llm_model} response {response_text}')

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
    time.sleep(3)
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
            audio = json2['data']['metadata']['contents'][0]['audio']
            logging.info(f'Generated audio: {audio}')
            return audio
        elif status == 'processing':
            time.sleep(5)
        else:
            raise Exception(f'Unexpected status: {status}')





def call_llm(content):
    # 1.情绪判断
    res1 = requests.post(url='https://api.siliconflow.cn/v1/chat/completions', headers={
        'Authorization': f'Bearer {llm_key}'
    }, json={
        "model": llm_model,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False,
        "response_format": {"type": "text"},
        "temperature": 0.7,
        "max_tokens": 512
    })
    res1.raise_for_status()
    json1 = res1.json()
    print(json1)
    content_text = json1['choices'][0]['message']['content'].strip()
    return content_text


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