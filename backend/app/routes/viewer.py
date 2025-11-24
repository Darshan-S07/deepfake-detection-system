# app/routes/viewer.py

from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId

router = APIRouter(prefix="/viewer", tags=["Viewer Logs"])

# Connect to MongoDB (same DB as your main app)
client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_db"]
viewer_logs = db["viewer_logs"]

def serialize_mongo_doc(doc: dict):
    """Convert ObjectId to string for JSON response"""
    if not doc:
        return doc
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}

@router.get("/logs")
async def get_all_logs():
    """Return recent viewer logs"""
    try:
        logs = list(viewer_logs.find().sort("_id", -1).limit(20))
        return [serialize_mongo_doc(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{log_type}")
async def get_logs_by_type(log_type: str):
    """Return logs filtered by type (audio, video, spam, unauthorized)"""
    try:
        logs = list(viewer_logs.find({"type": log_type}).sort("_id", -1).limit(20))
        return [serialize_mongo_doc(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))