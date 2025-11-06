from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from auth import get_current_user

router = APIRouter(prefix="/viewer", tags=["viewer"])

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_db"]
logs_collection = db["analysis"]

@router.get("/logs")
async def get_all_logs(user: str = Depends(get_current_user)):
    """
    Fetch all logs for the authenticated user.
    """
    logs = list(logs_collection.find({"user": user}, {"_id": 0}))
    if not logs:
        return JSONResponse({"message": "No logs found for user", "data": []})
    return JSONResponse({"total_logs": len(logs), "data": logs})


@router.get("/logs/{detection_type}")
async def get_logs_by_type(detection_type: str, user: str = Depends(get_current_user)):
    """
    Fetch logs filtered by detection type: audio, video, spam, unauthorized
    """
    valid_types = ["audio", "video", "spam", "unauthorized"]
    if detection_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Use one of: {valid_types}")

    logs = list(logs_collection.find(
        {"user": user, "type": detection_type},
        {"_id": 0}
    ))

    if not logs:
        return JSONResponse({"message": f"No {detection_type} logs found", "data": []})

    return JSONResponse({"total_logs": len(logs), "data": logs})

@router.get("/logs/{log_id}")
def get_log_by_id(log_id: str):
    log = db.detection_logs.find_one({"_id": ObjectId(log_id)})
    if log:
        return serialize_doc(log)
    return {"error": "Log not found"}