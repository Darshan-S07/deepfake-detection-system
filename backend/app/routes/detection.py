from fastapi import APIRouter

from fastapi import APIRouter, Depends, HTTPException, Header
from utils.token import verify_token

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

