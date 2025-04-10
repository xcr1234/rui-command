import nonebot
from pymongo import MongoClient

config = nonebot.get_driver().config


MONGO_URL = f'mongodb://{config.mongodb_username}:{config.mongodb_password}@{config.mongodb_host}:{config.mongodb_port}/{config.database_name}?authSource={config.mongodb_auth_source}'


def save_voice_log(data: dict):
    client = MongoClient(data)
    collection = client[config.database_name]['voice_log']
    collection.insert_one(data)

    client.close()