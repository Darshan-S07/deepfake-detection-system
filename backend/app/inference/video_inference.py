# backend/app/inference/video_inference.py

import cv2
import torch
import numpy as np
from transformers import VideoMAEForVideoClassification, AutoProcessor

MODEL_NAME = "shylhy/videomae-large-finetuned-deepfake-subset"

class VideoDeepfakeDetector:
    def __init__(self):
        print("🎥 Loading HuggingFace Video Deepfake Model...")
        
        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        self.model = VideoMAEForVideoClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        
        print("✅ Video model loaded successfully.")

    def predict_frame(self, frame):
        # Convert BGR to RGB (HuggingFace needs RGB)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        inputs = self.processor(images=rgb, return_tensors="pt")

        with torch.no_grad():
            output = self.model(**inputs).logits

        probs = torch.softmax(output, dim=1)[0].cpu().numpy()

        return {
            "real": float(probs[0]),
            "fake": float(probs[1]),
            "prediction": "FAKE" if probs[1] > probs[0] else "REAL"
        }

    def analyze_video(self, video_path):
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {"error": "Could not open video"}

        frame_count = 0
        fake_votes = 0
        real_votes = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % 5 != 0:
                continue  # sample every 5th frame

            result = self.predict_frame(frame)

            if result["prediction"] == "FAKE":
                fake_votes += 1
            else:
                real_votes += 1

        cap.release()

        final_prediction = "FAKE" if fake_votes > real_votes else "REAL"

        return {
            "total_frames": frame_count,
            "fake_votes": fake_votes,
            "real_votes": real_votes,
            "prediction": final_prediction
        }


video_detector = VideoDeepfakeDetector()

def analyze_video_file(path: str):
    return video_detector.analyze_video(path)
