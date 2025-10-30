from pymongo import MongoClient
import redis

def get_mongo_collection():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["my_database"]
    return db["my_collection"]

def get_redis_client():
    return redis.StrictRedis(host="localhost", port=6379, db=0)
