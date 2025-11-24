
from fastapi import APIRouter, HTTPException
from utils.db import db
from models.log_model import LogModel
from datetime import datetime

router = APIRouter(prefix="/logs", tags=["Viewer Logs"])

# Save a new log entry
@router.post("/add")
async def add_log(log: LogModel):
    log_dict = log.dict()
    log_dict["timestamp"] = datetime.utcnow()
    result = db.logs.insert_one(log_dict)
    return {"message": "Log saved", "id": str(result.inserted_id)}

# Get all logs
@router.get("/view")
async def get_logs():
    logs = list(db.logs.find({}, {"_id": 0}))
    return {"logs": logs}

# Clear all logs (optional, admin-only)
@router.delete("/clear")
async def clear_logs():
    db.logs.delete_many({})
    return {"message": "All logs cleared"}