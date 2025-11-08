from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogModel(BaseModel):
    timestamp: datetime = datetime.utcnow()
    user_id: Optional[str] = None
    action: str
    endpoint: str
    status: str
    details: Optional[str] = None