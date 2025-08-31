from fastapi import FastAPI, UploadFile, File
from pymongo import MongoClient
import shutil, os
from ai_model import DeepfakeDetector

app = FastAPI()

# Initialize MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_db"]
analysis = db["analysis"]

# Initialize model
detector = DeepfakeDetector()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = detector.analyze_audio(file_path)

    # Save to DB
    analysis.insert_one(result)

    return {"message": "Audio analyzed", "result": result}

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = detector.analyze_video(file_path)

    # Save to DB
    analysis.insert_one(result)

    return {"message": "Video analyzed", "result": result}
