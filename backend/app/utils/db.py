from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "deepfake_detection")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    return db

def log_detection(detection_type, details, result):
    """
    Logs detection events in MongoDB.
    :param detection_type: email / phone / unauthorized_access / deepfake_audio / deepfake_video
    :param details: dict containing request data
    :param result: dict with result details
    """
    log_entry = {
        "type": detection_type,
        "details": details,
        "result": result,
        "timestamp": datetime.utcnow()
    }
    db["detection_logs"].insert_one(log_entry)
    return log_entry