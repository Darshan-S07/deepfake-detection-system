# backend/app/models/video_model.py

from app.inference.video_inference import analyze_video_file

def load_video_model():
    return True  # model loaded globally

def predict_video(model, file_path: str):
    return analyze_video_file(file_path)
