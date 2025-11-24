# backend/routes/unauthorized.py
from fastapi import APIRouter, Request
from utils.db import log_detection

router = APIRouter()

# Define a list of allowed actions for simulation
ALLOWED_ACTIONS = {
    "WhatsApp": ["send_message", "read_own_messages"],
    "GoogleMeet": ["start_meeting", "join_meeting"],
    "Zoom": ["start_meeting", "join_meeting"],
}

@router.post("/detect/unauthorized")
async def detect_unauthorized(request: Request):
    body = await request.json()
    app_name = body.get("app_name")
    action = body.get("action")

    if not app_name or not action:
        return {"error": "app_name and action are required"}

    # Check if action is allowed
    if app_name in ALLOWED_ACTIONS and action in ALLOWED_ACTIONS[app_name]:
        result = {"alert": False, "message": "Authorized access"}
    else:
        result = {"alert": True, "message": f"Unauthorized access detected from {app_name} trying {action}"}

    # Log to MongoDB
    log_detection(
        detection_type="unauthorized_access",
        details={"app_name": app_name, "action": action},
        result=result
    )

    return result
