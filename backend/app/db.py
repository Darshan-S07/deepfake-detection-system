from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_system"]

analysis = db["analysis"]
logs = db["logs"]
calls = db["call_logs"]
