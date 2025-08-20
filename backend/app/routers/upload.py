from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
import os, uuid, shutil
from app.auth import get_current_user
from app.models.inference import analyze_file_paths
from app.utils.db import get_db

router = APIRouter(prefix="/media", tags=["media"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_media(
    caller_id: str = Form(...),
    audio: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    user: str = Depends(get_current_user),
    db = Depends(get_db)
):
    if not audio and not video:
        raise HTTPException(400, "Provide audio or video file")

    audio_path = None
    video_path = None

    if audio:
        aname = f"{uuid.uuid4()}_{audio.filename}"
        audio_path = os.path.join(UPLOAD_DIR, aname)
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

    if video:
        vname = f"{uuid.uuid4()}_{video.filename}"
        video_path = os.path.join(UPLOAD_DIR, vname)
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

    result = analyze_file_paths(caller_id, audio_path, video_path)
    db.logs.insert_one({"user": user, "type": "upload", **result})
    return JSONResponse(result)
