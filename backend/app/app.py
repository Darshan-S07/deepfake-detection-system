from fastapi import FastAPI, UploadFile, File, HTTPException,Request
from pymongo import MongoClient
from bson import ObjectId
import shutil, os
from ai_model import DeepfakeDetector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import detection
import auth
from routes import spam,unauthorized,viewer,metrics
from routers import audio_detection,video_detection,upload
from datetime import datetime
app = FastAPI(title="Deepfake Detection API")

app.include_router(upload.router, prefix="/media")
app.include_router(audio_detection.router, prefix="/audio")
app.include_router(video_detection.router, prefix="/video")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection.router,prefix="/api")
app.include_router(auth.router)
app.include_router(spam.router,prefix="/api")
app.include_router(unauthorized.router,prefix="/api")
app.include_router(viewer.router,prefix="/api")
app.include_router(metrics.router,prefix="/api")
# Initialize MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_db"]
analysis = db["analysis"]

# Initialize model
detector = DeepfakeDetector()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def serialize_mongo_doc(doc: dict):
    """
    Convert any ObjectId values (like _id) into strings so FastAPI can JSON encode.
    """
    if not doc:
        return doc
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run your AI model
        result = detector.analyze_audio(file_path)

        # Insert into Mongo (Mongo will add an _id)
        insert_result = analysis.insert_one(result)

        # Merge the _id back into the dict for the response
        result["_id"] = insert_result.inserted_id

        return {
            "message": "Audio analyzed",
            "result": serialize_mongo_doc(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run your AI model
        result = detector.analyze_video(file_path)

        insert_result = analysis.insert_one(result)
        result["_id"] = insert_result.inserted_id

        return {
            "message": "Video analyzed",
            "result": serialize_mongo_doc(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    db.logs.insert_one(log_data)
    return response
