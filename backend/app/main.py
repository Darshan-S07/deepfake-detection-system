from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.routers.upload import router as media_router
from app.ws_stream import router as ws_router

app = FastAPI(title="SecureCallX API")

# CORS (allow your React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(media_router)
app.include_router(ws_router)
