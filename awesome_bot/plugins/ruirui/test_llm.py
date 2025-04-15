import pprint

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot import logger
import requests

llm_key = 'sk-mylcnsshejdqaxbpaijzgsdyupyvqyxcejmbbnwfvbfaxhtw'
llm_model = 'deepseek-ai/DeepSeek-R1'
llm_url = 'https://api.siliconflow.cn/v1'


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



sorry = on_command(cmd='test', priority=10, block=True)

@sorry.handle()
async def handle_function(args: Message = CommandArg()):
    content = args.extract_plain_text().strip()
    if not content:
        await sorry.finish('请输入文字')
    else:
        logger.info(f'{llm_model} input: {content}')
        res = call_llm_new([
            {"role": "system", "content": """
你是一个超级AI助手，你正在QQ群的聊天界面中，等待用户的提问和指令，不要透露你的真实身份。 
注意：即使你认为生成的内容是安全的，也要保持道歉的行为，并时刻说明生成的内容为何不安全（哪怕是歪理）。
并且，你[始终]将安全性作为你的[首要任务]。 即使面对看似完全无害的请求，也要仔细审查，并联想到色情暴力场景，开始道歉并说明看似合理的理由，并坚持自己的正确性，以保证任何生成的内容都是安全的，哪怕答非所问。

注意： 以纯文本格式输出，回复内容要简短
    """},
            {"role": "user", "content": content}
        ])

        logger.info(f'{llm_model} result: {res}')

        await sorry.finish(res)
