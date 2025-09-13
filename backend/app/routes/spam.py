# routes/spam.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from config import db
import re
from datetime import datetime

router = APIRouter(
    prefix="/spam",
    tags=["Spam Detection"]
)

# ---------------------------
# Input Schemas
# ---------------------------
class EmailInput(BaseModel):
    subject: str
    body: str
    sender: str

class PhoneInput(BaseModel):
    phone_number: str

# ---------------------------
# Simple Spam Filters
# ---------------------------
def is_spam_email(subject: str, body: str) -> bool:
    spam_keywords = ["win money", "lottery", "prize", "urgent", "click here", "free gift"]
    text = f"{subject} {body}".lower()
    return any(word in text for word in spam_keywords)


def is_spam_phone(phone_number: str) -> bool:
    # Simple rules: suspicious if not 10 digits or from blacklisted patterns
    blacklisted_prefixes = ["140", "1800"]  # Example spam prefixes
    if not re.fullmatch(r"\d{10}", phone_number):
        return True
    return any(phone_number.startswith(prefix) for prefix in blacklisted_prefixes)


# ---------------------------
# Routes
# ---------------------------
@router.post("/email")
async def detect_email_spam(email: EmailInput):
    try:
        result = is_spam_email(email.subject, email.body)
        log = {
            "type": "email",
            "sender": email.sender,
            "subject": email.subject,
            "is_spam": result,
            "timestamp": datetime.utcnow()
        }
        db.detection_logs.insert_one(log)
        return {"spam": result, "message": "Spam email detected" if result else "Email is safe"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/phone")
async def detect_phone_spam(phone: PhoneInput):
    try:
        result = is_spam_phone(phone.phone_number)
        log = {
            "type": "phone",
            "phone_number": phone.phone_number,
            "is_spam": result,
            "timestamp": datetime.utcnow()
        }
        db.detection_logs.insert_one(log)
        return {"spam": result, "message": "Spam call detected" if result else "Phone number is safe"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
