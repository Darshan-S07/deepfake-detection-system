from pydantic import BaseModel

class CallInfo(BaseModel):
    caller_id: str
    audio_url: str  # URL/path to audio for detection
    video_url: str  # URL/path to video for detection
    metadata: dict  # Info like duration, location, etc.
