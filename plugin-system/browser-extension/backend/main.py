from fastapi import FastAPI, WebSocket
from utils.audio_processing import process_audio_chunk
from utils.video_processing import process_video_frame
import base64
import json

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Client connected for live detection.")

    try:
        while True:
            raw_msg = await ws.receive_text()

            # Convert JSON string to dictionary
            msg = json.loads(raw_msg)

            data_type = msg.get("type")
            payload = msg.get("data")

            if not payload:
                continue

            # ------------------------ AUDIO ------------------------
            if data_type == "AUDIO_FRAME":
                try:
                    decoded = base64.b64decode(payload)
                    risk = process_audio_chunk(decoded)
                except Exception as e:
                    print("Audio error:", e)
                    risk = "LOW"

            # ------------------------ VIDEO ------------------------
            elif data_type == "VIDEO_FRAME":
                try:
                    decoded = base64.b64decode(payload)
                    risk = process_video_frame(decoded)
                except Exception as e:
                    print("Video processing error:", e)
                    risk = "LOW"

            else:
                risk = "LOW"

            # Respond to extension
            await ws.send_text(json.dumps({"risk": risk}))

    except Exception as e:
        print("Connection closed:", e)

    print("🔴 Client Disconnected.")
