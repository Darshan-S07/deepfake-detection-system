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
