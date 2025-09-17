# backend/routes/viewer.py
from fastapi import APIRouter
from utils.db import db
from bson import ObjectId

router = APIRouter()

# Custom serializer for MongoDB ObjectId
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.get("/logs")
def get_all_logs():
    logs = db.detection_logs.find().sort("timestamp", -1)  # latest first
    return [serialize_doc(log) for log in logs]

@router.get("/logs/{log_id}")
def get_log_by_id(log_id: str):
    log = db.detection_logs.find_one({"_id": ObjectId(log_id)})
    if log:
        return serialize_doc(log)
    return {"error": "Log not found"}

@router.get("/logs/type/{detection_type}")
def get_logs_by_type(detection_type: str):
    logs = db.detection_logs.find({"type": detection_type}).sort("timestamp", -1)
    return [serialize_doc(log) for log in logs]
