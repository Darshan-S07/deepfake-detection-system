from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import base64, os, uuid
from app.auth import get_current_user
from app.models.inference import analyze_chunk
from app.utils.db import get_db

router = APIRouter(prefix="/ws", tags=["websocket"])

CHUNK_DIR = "chunks"
os.makedirs(CHUNK_DIR, exist_ok=True)

@router.websocket("/stream")
async def stream_socket(ws: WebSocket):
    await ws.accept()
    # Expect first message to carry the token: {"auth":"Bearer <token>"}
    try:
        first = await ws.receive_json()
        auth = first.get("auth")
        if not auth or not auth.lower().startswith("bearer "):
            await ws.send_json({"error":"unauthorized"})
            await ws.close()
            return
        # We don't have Depends() in ws, so do a manual check:
        from app.auth import decode_token
        payload = decode_token(auth.split(" ")[1])
        if not payload:
            await ws.send_json({"error":"invalid token"})
            await ws.close()
            return
        user = payload["sub"]
    except Exception:
        await ws.close()
        return

    try:
        while True:
            data = await ws.receive_json()
            # data = {"type": "audio"|"video", "b64": "...", "timestamp": 123}
            typ = data.get("type")
            b64 = data.get("b64")
            ts = data.get("timestamp")

            # Save the chunk (optional)
            filename = f"{uuid.uuid4()}_{typ}_{ts}"
            path = os.path.join(CHUNK_DIR, filename)
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))

            result = analyze_chunk(typ, len(b64))
            result["timestamp"] = ts
            await ws.send_json(result)
    except WebSocketDisconnect:
        pass
