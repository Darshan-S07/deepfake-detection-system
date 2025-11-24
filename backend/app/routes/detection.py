from fastapi import APIRouter, Depends, HTTPException, Header,File,UploadFile
from utils.token import verify_token
from utils.logger import DetectionLogger
from ai_models.audio.audio_inference import AudioDeepfakeDetector
from ai_models.video.video_inference import VideoDeepfakeDetector

router = APIRouter(
    prefix="/detection",
    tags=["Detection"]
)

audio_detector = AudioDeepfakeDetector()
video_detector = VideoDeepfakeDetector()