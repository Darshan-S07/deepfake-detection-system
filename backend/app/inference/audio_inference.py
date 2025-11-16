# backend/app/inference/audio_inference.py

import torch
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
import librosa
import numpy as np

MODEL_NAME = "ai-forever/graphormer-audio-deepfake-detector"

class AudioDeepfakeDetector:
    def __init__(self):
        print("🔊 Loading HuggingFace Audio Deepfake Model...")
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
        self.model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("✅ Audio model loaded successfully.")

    def predict(self, audio_path: str):
        # Load audio
        signal, sr = librosa.load(audio_path, sr=16000)

        # Preprocess
        inputs = self.feature_extractor(
            signal,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )

        # Model prediction
        with torch.no_grad():
            logits = self.model(**inputs).logits

        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        return {
            "real": float(probs[0]),
            "fake": float(probs[1]),
            "prediction": "FAKE" if probs[1] > probs[0] else "REAL"
        }


# Singleton instance
audio_detector = AudioDeepfakeDetector()

def analyze_audio_file(path: str):
    return audio_detector.predict(path)
