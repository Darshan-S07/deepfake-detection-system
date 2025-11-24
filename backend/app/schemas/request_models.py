from pydantic import BaseModel

class UserIn(BaseModel):
    username: str
    password: str

class CallInfo(BaseModel):
    caller_id: str
    audio_url: str | None = None
    video_url: str | None = None
    metadata: dict | None = None
