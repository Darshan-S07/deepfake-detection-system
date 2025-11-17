import os
import asyncio
import tempfile
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.audio_model import load_audio_model, predict_audio
from models.video_model import load_video_model, predict_video
from utils.db import log_detection
import time
import cv2
import numpy as np
from inference.aggregator import add_result as aggregator_add

router = APIRouter(prefix="/stream", tags=["Streaming"])

# Load models once
audio_model = load_audio_model()
video_model = load_video_model()

# Configuration
AUDIO_BUFFER_SECONDS = 2.0
VIDEO_BUFFER_FRAMES = 10
VIDEO_FPS = 10


# -------------------------
# AUDIO INFERENCE
# -------------------------
async def _run_audio_inference_and_send(ws: WebSocket, buffer_bytes: bytes, session_id: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    try:
        tmp.write(buffer_bytes)
        tmp.flush()
        tmp.close()

        result = predict_audio(audio_model, tmp.name)

        agg_out = aggregator_add(session_id, "audio", result, user=None)

        await ws.send_json({"type": "audio_result", "result": result, "aggregate": agg_out["aggregate"]})

        if agg_out.get("alert"):
            await ws.send_json({"type": "alert", "alert": agg_out["alert"]})

        log_detection("deepfake_audio_stream", {"tmpfile": tmp.name}, {"result": result})

    finally:
        try:
            os.remove(tmp.name)
        except:
            pass


# -------------------------
# VIDEO HELPERS
# -------------------------
def _frames_to_video_file(frames: list, fps=10):
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_path = tmp_video.name
    tmp_video.close()

    first = cv2.imdecode(np.frombuffer(frames[0], np.uint8), cv2.IMREAD_COLOR)
    height, width = first.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

    for f in frames:
        img = cv2.imdecode(np.frombuffer(f, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    writer.release()
    return tmp_path


async def _run_video_inference_and_send(ws: WebSocket, frames_bytes_list, session_id):
    tmp_video_path = None
    try:
        tmp_video_path = _frames_to_video_file(frames_bytes_list, fps=VIDEO_FPS)

        result = predict_video(video_model, tmp_video_path)
        agg_out = aggregator_add(session_id, "video", result, user=None)

        await ws.send_json({"type": "video_result", "result": result, "aggregate": agg_out["aggregate"]})

        if agg_out.get("alert"):
            await ws.send_json({"type": "alert", "alert": agg_out["alert"]})

        log_detection("deepfake_video_stream", {"tmpfile": tmp_video_path}, {"result": result})

    finally:
        if tmp_video_path and os.path.exists(tmp_video_path):
            try:
                os.remove(tmp_video_path)
            except:
                pass


# -------------------------
# AUDIO STREAM ROUTE
# -------------------------
@router.websocket("/audio/{session_id}")
async def ws_audio_stream(ws: WebSocket, session_id: str):
    await ws.accept()
    print(f"[audio] session {session_id} connected")

    buffer = bytearray()
    inference_task = None

    try:
        while True:
            msg = await ws.receive()

            if "bytes" in msg:
                chunk = msg["bytes"]
                buffer.extend(chunk)

                # Rough threshold (approx)
                if len(buffer) > 16000 * 2 * AUDIO_BUFFER_SECONDS:
                    if inference_task is None or inference_task.done():
                        copy = bytes(buffer)
                        buffer = bytearray()
                        inference_task = asyncio.create_task(_run_audio_inference_and_send(ws, copy, session_id))

            elif "text" in msg:
                if msg["text"] == "flush":
                    if buffer:
                        copy = bytes(buffer)
                        buffer = bytearray()
                        asyncio.create_task(_run_audio_inference_and_send(ws, copy, session_id))

    except WebSocketDisconnect:
        print(f"[audio] session {session_id} disconnected")
        if buffer:
            await _run_audio_inference_and_send(ws, bytes(buffer), session_id)


# -------------------------
# VIDEO STREAM ROUTE
# -------------------------
@router.websocket("/video/{session_id}")
async def ws_video_stream(ws: WebSocket, session_id: str):
    await ws.accept()
    print(f"[video] session {session_id} connected")

    frames = []
    inference_task = None

    try:
        while True:
            msg = await ws.receive()

            if "bytes" in msg:
                frames.append(msg["bytes"])

                if len(frames) >= VIDEO_BUFFER_FRAMES:
                    if inference_task is None or inference_task.done():
                        batch = frames.copy()
                        frames = []
                        inference_task = asyncio.create_task(_run_video_inference_and_send(ws, batch, session_id))

            elif "text" in msg:
                text = msg["text"]

                if text.startswith("data:image"):
                    header, b64 = text.split(",", 1)
                    frames.append(base64.b64decode(b64))

                    if len(frames) >= VIDEO_BUFFER_FRAMES:
                        batch = frames.copy()
                        frames = []
                        inference_task = asyncio.create_task(_run_video_inference_and_send(ws, batch, session_id))

                elif text == "flush":
                    if frames:
                        batch = frames.copy()
                        frames = []
                        asyncio.create_task(_run_video_inference_and_send(ws, batch, session_id))

    except WebSocketDisconnect:
        print(f"[video] session {session_id} disconnected")
        if frames:
            await _run_video_inference_and_send(ws, frames, session_id)