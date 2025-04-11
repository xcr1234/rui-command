import logging
import string
import time
import unicodedata

import requests

from .mongo_store import query_history

llm_key = 'sk-mylcnsshejdqaxbpaijzgsdyupyvqyxcejmbbnwfvbfaxhtw'
llm_model = 'deepseek-ai/DeepSeek-V3'
llm_url = 'https://api.siliconflow.cn/v1'

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


def call_llm_new(messages: list) -> str:
    res1 = requests.post(url=f'{llm_url}/chat/completions', headers={
        'Authorization': f'Bearer {llm_key}'
    }, json={
        "model": llm_model,
        "messages": messages,
        "stream": False,
        "response_format": {"type": "text"},
        "temperature": 0.7,
        "max_tokens": 512
    })
    res1.raise_for_status()
    json1 = res1.json()
    content_text = json1['choices'][0]['message']['content'].strip()
    return content_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def generate_llm(text: str,group_id: int,user_id: int):
    history_list = query_history(group_id=group_id, send_user_id=user_id)

    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    #1.情感助手

    # 1.1 情感助手的提示词
    emotion_list = [
        {
            'role': 'system',
            'content': f"""根据用户输入的内容，判断你应该给出的情绪，情绪为（{'/'.join(prompt_dict.keys())}）之一，
            如果没有适合的情绪，请输出“默认”，不要输出多余的内容。
            现在的日期时间是：{time_str}"""
        },
    ]
    # 1.2 对话历史
    for history in history_list:
        emotion_list.append({
            'role': 'user',
            'content': history['user_input']
        })
        emotion_list.append({
            'role': 'assistant',
            'content': history['emotion_text']
        })
    # 1.3 用户输入
    emotion_list.append({
        'role': 'user',
        'content': f'[{time_str}]: {text}'
    })

    emotion_text = call_llm_new(emotion_list)

    logging.info(f'{llm_model} emotion {emotion_text}')


    # 2.回应用户
    response_list = [
        {
            'role': 'system',
            'content': f"""你的名字叫锐锐，一名小学女生。请根据当前情绪，用一句话回复用户的输入，不要过长，不要输出多余内容。
请注意：如果是政治或色情类敏感问题固定回答“这个问题不太合适吧”。
现在的日期时间是：{time_str}
"""
        }
    ]
    for history in history_list:
        response_list.append({
            'role': 'user',
            'content': history['user_input']
        })
        response_list.append({
            'role': 'assistant',
            'content': history['response_text']
        })

    response_list.append({
        'role': 'user',
        'content': f"""
你的当前的情绪是：{emotion_text if emotion_text in prompt_dict else '默认'}
用户的输入是：        
[{time_str}]: {text}"""
    })

    response_text = call_llm_new(response_list)

    logging.info(f'{llm_model} response {response_text}')

    return emotion_text, trim_punctuation(response_text)