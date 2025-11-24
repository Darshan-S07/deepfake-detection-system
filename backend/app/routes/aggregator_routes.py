# backend/app/routes/aggregator_routes.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from inference.aggregator import get_session_summary, add_result
from utils.db import get_db

router = APIRouter(prefix="/api/aggregator", tags=["Aggregator"])

@router.get("/session/{session_id}")
async def session_summary(session_id: str):
    s = get_session_summary(session_id)
    if not s:
        raise HTTPException(404, "session not found")
    return s

# optional: endpoint to inject a manual result (useful for testing)
@router.post("/session/{session_id}/inject")
async def inject_result(session_id: str, payload: Dict[str, Any]):
    # payload must contain 'kind' and inference 'result'
    kind = payload.get("kind")
    result = payload.get("result")
    user = payload.get("user", None)
    if kind not in ("audio", "video"):
        raise HTTPException(400, "kind must be audio or video")
    out = add_result(session_id, kind, result, user=user)
    return out
