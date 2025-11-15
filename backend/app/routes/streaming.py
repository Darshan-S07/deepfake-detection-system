import os
import asyncio
import tempfile
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Depends
from models.audio_model import load_audio_model, predict_audio
from models.video_model import load_video_model, predict_video
from utils.db import log_detection  # optional logging
import time
import uuid
import cv2
import numpy as np

router = APIRouter(prefix="/stream", tags=["Streaming"])

# load models once
audio_model = load_audio_model()
video_model = load_video_model()

# configuration
AUDIO_BUFFER_SECONDS = 2.0    # accumulate ~2 seconds of audio per inference
VIDEO_BUFFER_FRAMES = 10      # number of frames to collect before inference
VIDEO_FPS = 10                # fps for temp video file

# helper: save binary audio (webm/ogg/wav) chunks into a temp file and call audio model
async def _run_audio_inference_and_send(ws: WebSocket, buffer_bytes: bytes):
    # write to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    try:
        tmp.write(buffer_bytes)
        tmp.flush()
        tmp.close()
        # If your audio_inference expects WAV at 16k, you may need to convert here (ffmpeg) or adjust model loader
        result = predict_audio(audio_model, tmp.name)
        await ws.send_json({"type": "audio_result", "result": result})
        # optional: log
        log_detection("deepfake_audio_stream", {"tmpfile": tmp.name}, {"result": result})
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass

# helper: assemble frames into a temporary video file using cv2.VideoWriter
def _frames_to_video_file(frames: list, fps=10):
    """
    frames: list of raw image bytes (JPEG/PNG) or numpy arrays
    returns: path to temp mp4 file
    """
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_path = tmp_video.name
    tmp_video.close()

    # decode first frame to get size
    # frames are expected as raw jpeg bytes
    first = cv2.imdecode(np.frombuffer(frames[0], np.uint8), cv2.IMREAD_COLOR)
    height, width = first.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

    for b in frames:
        img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # model expects RGB
        # convert back to BGR for writer
        writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    writer.release()
    return tmp_path

async def _run_video_inference_and_send(ws: WebSocket, frames_bytes_list: list):
    tmp_video_path = None
    try:
        tmp_video_path = _frames_to_video_file(frames_bytes_list, fps=VIDEO_FPS)
        result = predict_video(video_model, tmp_video_path)
        await ws.send_json({"type": "video_result", "result": result})
        log_detection("deepfake_video_stream", {"tmpfile": tmp_video_path}, {"result": result})
    finally:
        if tmp_video_path and os.path.exists(tmp_video_path):
            try:
                os.remove(tmp_video_path)
            except Exception:
                pass


@router.websocket("/audio/{session_id}")
async def ws_audio_stream(ws: WebSocket, session_id: str):
    """
    Client should send binary audio chunks (Blob) over WebSocket.
    We'll accumulate bytes until approximate duration (AUDIO_BUFFER_SECONDS) is reached,
    then run inference in background.
    """
    await ws.accept()
    print(f"[audio] session {session_id} connected")
    buffer = bytearray()
    last_send = time.time()
    inference_task = None

    try:
        while True:
            msg = await ws.receive()
            if "bytes" in msg:
                chunk = msg["bytes"]
                buffer.extend(chunk)

                # naive approach: once accumulated a certain number of bytes, trigger inference
                # This threshold is approximate; you may prefer to rely on client timestamps or send 'eod' message
                if len(buffer) > 16000 * 2 * AUDIO_BUFFER_SECONDS:  # rough bytes estimate for pcm16: sr*2bytes*seconds
                    # run inference in background
                    if inference_task is None or inference_task.done():
                        buf_copy = bytes(buffer)
                        buffer = bytearray()
                        inference_task = asyncio.create_task(_run_audio_inference_and_send(ws, buf_copy))
            elif "text" in msg:
                # allow control messages from client (e.g., {"event":"flush"})
                try:
                    data = msg["text"]
                    # if client explicitly asks to flush, run inference on current buffer
                    if data == "flush":
                        if buffer:
                            buf_copy = bytes(buffer)
                            buffer = bytearray()
                            asyncio.create_task(_run_audio_inference_and_send(ws, buf_copy))
                except Exception:
                    pass

    except WebSocketDisconnect:
        print(f"[audio] session {session_id} disconnected")
        # flush remaining buffer
        if buffer:
            await _run_audio_inference_and_send(ws, bytes(buffer))
        return


@router.websocket("/video/{session_id}")
async def ws_video_stream(ws: WebSocket, session_id: str):
    """
    Client sends base64 or raw binary JPEG/PNG frames. We'll collect VIDEO_BUFFER_FRAMES frames then infer.
    Protocol (recommended):
    - Each binary message = raw JPEG bytes
    - Or each text message = base64-encoded JPEG string
    - A small JSON text control message like {"event":"flush"} to force inference
    """
    await ws.accept()
    print(f"[video] session {session_id} connected")
    frames = []
    inference_task = None
    try:
        while True:
            msg = await ws.receive()
            if "bytes" in msg:
                # assume raw jpeg bytes
                frames.append(msg["bytes"])

                if len(frames) >= VIDEO_BUFFER_FRAMES:
                    # run inference in background
                    if inference_task is None or inference_task.done():
                        batch = frames.copy()
                        frames = []
                        inference_task = asyncio.create_task(_run_video_inference_and_send(ws, batch))

            elif "text" in msg:
                text = msg["text"]
                # accept base64 images or control commands
                if text.startswith("data:image"):
                    # strip header and decode
                    header, b64 = text.split(",", 1)
                    frames.append(base64.b64decode(b64))
                    if len(frames) >= VIDEO_BUFFER_FRAMES:
                        batch = frames.copy()
                        frames = []
                        inference_task = asyncio.create_task(_run_video_inference_and_send(ws, batch))
                else:
                    # control messages
                    if text == "flush":
                        if frames:
                            batch = frames.copy()
                            frames = []
                            asyncio.create_task(_run_video_inference_and_send(ws, batch))

    except WebSocketDisconnect:
        print(f"[video] session {session_id} disconnected")
        if frames:
            await _run_video_inference_and_send(ws, frames)
        return