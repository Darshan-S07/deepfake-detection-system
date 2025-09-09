from fastapi import APIRouter

from fastapi import APIRouter, Depends, HTTPException, Header
from utils.token import verify_token
from fastapi import APIRouter, UploadFile, File
from utils.logger import DetectionLogger

router = APIRouter(
    prefix="/detection",
    tags=["Detection"]
)

@router.post("/analyze-audio/")
async def analyze_audio(file: UploadFile = File(...)):
    # Placeholder ML logic (to be replaced later with actual model)
    result = "FAKE"  # pretend detection result
    confidence = 0.87

    # Log the detection
    DetectionLogger.log_event(
        content_type="audio",
        status=result,
        details=f"confidence={confidence}, filename={file.filename}"
    )

    return {"result": result, "confidence": confidence}

router = APIRouter(prefix="/detect", tags=["detection"])

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

@router.get("/ping")
def ping(user: dict = Depends(get_current_user)):
    return {"msg": f"Hello {user['sub']}, detection service active"}

@router.post("/audio")
def detect_audio(file: str, user: dict = Depends(get_current_user)):
    return {"user": user["sub"], "result": "fake", "confidence": 0.82}

@router.post("/video")
def detect_video(file: str, user: dict = Depends(get_current_user)):
    return {"user": user["sub"], "result": "real", "confidence": 0.91}

