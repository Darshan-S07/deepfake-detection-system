from fastapi import APIRouter, WebSocket
import httpx
import json

router = APIRouter()

@router.websocket("/ws/{meeting_id}/{participant_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str, participant_id: str):
    await websocket.accept()

    # ---- Spam check ----
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://127.0.0.1:8000/spam/check/{participant_id}")
        result = resp.json()

    if result["spam"]:
        # Alert user and deny entry
        await websocket.send_json({
            "type": "alert",
            "message": f"⚠️ Participant {participant_id} flagged as spam",
            "reason": result["reason"]
        })
        await websocket.close()
        return

    # ---- If safe, allow join ----
    await websocket.send_json({
        "type": "welcome",
        "message": f"✅ {participant_id} joined meeting {meeting_id}"
    })

    # Placeholder loop to keep connection alive
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        await websocket.close()
