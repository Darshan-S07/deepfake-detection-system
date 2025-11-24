from fastapi import APIRouter, Depends
from utils.token import verify_token
from datetime import datetime
from config import db

router = APIRouter(prefix="/call", tags=["Call Logs"])

@router.post("/save")
def save_call_log(payload: dict, token: str = Depends(verify_token)):
    user = verify_token(token)
    if not user:
        return {"error": "Unauthorized"}

    payload["user"] = user["sub"]
    payload["timestamp"] = datetime.utcnow()

    db.logs_collection.insert_one(payload)

    return {"message": "Saved"}
