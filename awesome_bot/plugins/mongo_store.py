import nonebot
from pymongo import MongoClient

config = nonebot.get_driver().config


MONGO_URL = f'mongodb://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@{config.MONGODB_HOST}:{config.MONGODB_PORT}/{config.DATABASE_NAME}?authSource={config.MONGODB_AUTH_SOURCE}'


def save_voice_log(data: dict):
    client = MongoClient(data)
    collection = client['config.DATABASE_NAME']['voice_log']
    collection.insert_one(data)

    client.close()