# backend/app/ws_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import base64
import uuid
import os

app = FastAPI()
CHUNK_DIR = "chunks"
os.makedirs(CHUNK_DIR, exist_ok=True)

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # data example: {"type": "audio", "b64": "<base64string>", "timestamp": 12345}
            typ = data.get("type")
            b64 = data.get("b64")
            ts = data.get("timestamp")
            # Save chunk temporarily
            filename = f"{uuid.uuid4()}_{typ}_{ts}.wav"  # or .webm for video
            path = os.path.join(CHUNK_DIR, filename)
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            # TODO: call inference on path (async if possible)
            # For demo: send back a dummy result
            await websocket.send_json({"timestamp": ts, "type": typ, "deepfake_prob": 0.12})
    except WebSocketDisconnect:
        print("Client disconnected")
