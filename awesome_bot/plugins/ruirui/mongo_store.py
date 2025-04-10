import nonebot
from pymongo import MongoClient
from urllib.parse import quote_plus
config = nonebot.get_driver().config


MONGO_URL = f'mongodb://{quote_plus(config.mongodb_username)}:{quote_plus(config.mongodb_password)}@{config.mongodb_host}:{config.mongodb_port}/'


def save_voice_log(data: dict):
    client = MongoClient(MONGO_URL)
    collection = client[config.database_name]['voice_log']
    collection.insert_one(data)

    client.close()