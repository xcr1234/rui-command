import time
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
import requests
import logging
import unicodedata
import string
from .mongo_store import save_voice_log
from datetime import datetime


def get_fullwidth_punctuation():
    fullwidth = []
    for c in string.punctuation:
        code = ord(c)
        if 0x20 <= code <= 0x7e:
            fullwidth_code = code + 0xfee0
            fullwidth.append(chr(fullwidth_code))
    # 添加常见中文标点
    extra = ['、', '。', '「', '」', '『', '』', '【', '】', '《', '》', '“', '”', '‘', '’', '·', '…', '—', '～']
    fullwidth.extend(extra)
    return set(fullwidth)


fullwidth_punctuation = get_fullwidth_punctuation()


def is_punctuation(char):
    return (unicodedata.category(char).startswith('P') or
            char in string.punctuation or
            char in fullwidth_punctuation)


def trim_punctuation(s: str):
    end = len(s)
    while end > 0 and is_punctuation(s[end - 1]):
        end -= 1
    return s[:end]


# 大模型调用的key
llm_key = 'sk-mylcnsshejdqaxbpaijzgsdyupyvqyxcejmbbnwfvbfaxhtw'
llm_model = 'deepseek-ai/DeepSeek-V3'
voice_key = 'sk-df1b1b09431212125006cc6f12a5c8db'
llm_url = 'https://api.siliconflow.cn/v1'

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

    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    emotion_text = call_llm(f"""根据用户输入的内容，判断你应该给出的情绪，情绪为（{'/'.join(prompt_dict.keys())}）之一，
如果没有适合的情绪，请输出“默认”，不要输出多余的内容。
                
用户的输入是：{text}
现在的日期时间是：{time_str}
""")
    logging.info(f'{llm_model} emotion {emotion_text}')

    response_text = call_llm(f""""你的名字叫锐锐，一名小学女生。请根据当前情绪，用一句话回复用户的输入，不要过长，不要输出多余内容。
    请注意：如果是政治或色情类敏感问题固定回答“这个问题不太合适吧”。
    
    你的情绪是：{emotion_text if emotion_text in prompt_dict else '默认'}
    用户的输入是：{text}
    现在的日期时间是：{time_str}
""")

    logging.info(f'{llm_model} response {response_text}')

    response_text = trim_punctuation(response_text)

    logging.info(f'trim_punctuation response {response_text}')

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


def call_llm(content: str, model=llm_model) -> str:
    # 1.情绪判断
    res1 = requests.post(url=f'{llm_url}/chat/completions', headers={
        'Authorization': f'Bearer {llm_key}'
    }, json={
        "model": model,
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
    content_text = json1['choices'][0]['message']['content'].strip()
    return content_text


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
        voice_url, response_text, emotion_text = voice_gen_impl(text)
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
