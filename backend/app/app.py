from fastapi import FastAPI, UploadFile, File, HTTPException
from pymongo import MongoClient
from bson import ObjectId
import shutil, os
from ai_model import DeepfakeDetector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import detection
import auth

app = FastAPI(title="Deepfake Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection.router)
app.include_router(auth.router)



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
