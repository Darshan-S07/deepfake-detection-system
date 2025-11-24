# backend/app/inference/audio_detector.py

import torch
import librosa
import numpy as np
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor

MODEL_NAME = "jonatasgrosman/wav2vec2-large-xlsr-53-english"

class AudioDeepfakeDetector:
    def __init__(self):
        print("🔊 Loading Audio Deepfake Model from HuggingFace...")

        self.processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME)

        self.model.eval()
        print("✅ Audio model loaded successfully.")

    def predict(self, audio_path):
        audio, sr = librosa.load(audio_path, sr=16000)

        inputs = self.processor(
            audio, sampling_rate=16000, return_tensors="pt", padding=True
        )

        with torch.no_grad():
            logits = self.model(**inputs).logits

        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        return {
            "real": float(probs[0]),
            "fake": float(probs[1]),
            "prediction": "FAKE" if probs[1] > probs[0] else "REAL"
        }

audio_detector = AudioDeepfakeDetector()
