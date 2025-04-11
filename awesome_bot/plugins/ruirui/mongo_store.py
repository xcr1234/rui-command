import nonebot
from pymongo import MongoClient
from urllib.parse import quote_plus

config = nonebot.get_driver().config


MONGO_URL = f'mongodb://{quote_plus(config.mongodb_username)}:{quote_plus(config.mongodb_password)}@{config.mongodb_host}:{config.mongodb_port}/{config.database_name}?authSource={config.mongodb_auth_source}'


def save_voice_log(data: dict):
    client = MongoClient(MONGO_URL)
    collection = client[config.database_name]['voice_log']
    collection.insert_one(data)

    client.close()

def query_history(group_id: int, send_user_id: int):
    client = MongoClient(MONGO_URL)
    collection = client[config.database_name]['voice_log']

    agg_query = [
        {
            "$match": {
                "group_id": group_id,
                "send_user_id": send_user_id
            }
        },
        {
            "$sort": {
                "res_time": -1
            }
        },
        {
            "$limit": 6
        },
        {
            "$project": {
                "_id": 0,
                "response_text": 1,
                "emotion_text": 1,
                "user_input": {
                    "$concat": [
                        "[",
                        {
                            "$dateToString": {
                                "format": "%Y-%m-%d %H:%M:%S",
                                "date": {
                                    "$add": [
                                        "$res_time",
                                        28800000
                                    ]
                                }
                            }
                        },
                        "]: ",
                        "$input"
                    ]
                }
            }
        }
    ]

    res = collection.aggregate(agg_query)
    client.close()

    # 返回res,反向
    return reversed(list(res))




