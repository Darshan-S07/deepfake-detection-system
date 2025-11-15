from fastapi import APIRouter, UploadFile, File
from utils.db import log_detection
import torch
import tempfile

router = APIRouter(prefix="/analyze", tags=["Inference"])

# Load your models globally here
from models.audio_model import load_audio_model, predict_audio
from models.video_model import load_video_model, predict_video

audio_model = load_audio_model()
video_model = load_video_model()

@router.post("/audio")
async def analyze_audio(file: UploadFile = File(...)):
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = predict_audio(audio_model, tmp_path)
    log_detection("deepfake_audio", {"filename": file.filename}, {"result": result})
    return {"status": "success", "file": file.filename, "result": result}

@router.post("/video")
async def analyze_video(file: UploadFile = File(...)):
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = predict_video(video_model, tmp_path)
    log_detection("deepfake_video", {"filename": file.filename}, {"result": result})
    return {"status": "success", "file": file.filename, "result": result}