# routes/spam.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from config import db

router = APIRouter(
    prefix="/spam",
    tags=["Spam Detection"]
)

# --- Request Models ---
class SpamReport(BaseModel):
    identifier: str  # phone number or email
    reason: str = "Spam/Scam activity"


# --- Routes ---

@router.post("/report")
def report_spam(data: SpamReport):
    """Report a phone number or email as spam."""
    existing = db.spam.find_one({"identifier": data.identifier})
    if existing:
        raise HTTPException(status_code=400, detail="Already reported as spam")

    db.spam.insert_one({
        "identifier": data.identifier,
        "reason": data.reason
    })
    return {"message": f"{data.identifier} reported as spam."}


@router.get("/check/{identifier}")
def check_spam(identifier: str):
    """Check if phone/email is flagged as spam."""
    spam_entry = db.spam.find_one({"identifier": identifier})
    if spam_entry:
        return {
            "spam": True,
            "reason": spam_entry["reason"]
        }
    return {"spam": False}


@router.get("/list")
def list_spam():
    """List all spam entries (for testing/admin)."""
    spam_list = list(db.spam.find({}, {"_id": 0}))
    return {"spam_entries": spam_list}
