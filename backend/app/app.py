from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime
from db import analysis,db
# Import Routers & modules
from routes import detection
import auth
from routes import spam, unauthorized, viewer, metrics, inference_routes, stream_routes, aggregator_routes
from routers import audio_detection, video_detection, upload
from routes.call_logs import router as call_router

# --------------------------------------
# Initialize FastAPI
# --------------------------------------
app = FastAPI(title="Deepfake Detection API")

# --------------------------------------
# CORS Middleware
# --------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------
# Include Routers (keep canonical endpoints in routers)
# --------------------------------------
app.include_router(call_router)
app.include_router(upload.router, prefix="/media")
app.include_router(audio_detection.router, prefix="/audio")
app.include_router(video_detection.router, prefix="/video")

app.include_router(inference_routes.router)
app.include_router(detection.router, prefix="/api")
app.include_router(auth.router)
app.include_router(spam.router, prefix="/api")
app.include_router(unauthorized.router, prefix="/api")
app.include_router(viewer.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(stream_routes.router)
app.include_router(aggregator_routes.router)

# --------------------------------------
# MongoDB Setup
# --------------------------------------

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------
# Helper: Convert ObjectId to string
# --------------------------------------
def serialize_mongo_doc(doc: dict):
    if not doc:
        return doc
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}


# --------------------------------------
# Logging Middleware (API Logs)
# --------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds()

    log_data = {
        "timestamp": datetime.utcnow(),
        "action": "API_CALL",
        "endpoint": request.url.path,
        "status": str(response.status_code),
        "details": f"Method: {request.method}, Duration: {duration}s"
    }

    # Write to Mongo logs collection safely
    try:
        db.logs.insert_one(log_data)
    except Exception:
        # don't block the request if logging fails
        pass

    return response
