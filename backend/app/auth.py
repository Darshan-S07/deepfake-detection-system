from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas.request_models import UserIn
from app.utils.db import get_db
from app.utils.security import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(user: UserIn, db=Depends(get_db)):
    if db.users.find_one({"username": user.username}):
        raise HTTPException(400, "User already exists")
    db.users.insert_one({"username": user.username, "password": hash_password(user.password)})
    return {"msg": "User created"}

@router.post("/login")
def login(user: UserIn, db=Depends(get_db)):
    rec = db.users.find_one({"username": user.username})
    if not rec or not verify_password(user.password, rec["password"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(user.username)
    return {"access_token": token, "token_type": "bearer"}

# Dependency to protect routes
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid/expired token")
    return payload["sub"]
