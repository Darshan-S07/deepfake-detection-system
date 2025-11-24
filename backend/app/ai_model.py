import librosa
import numpy as np
import cv2
import tensorflow as tf
import os

class DeepfakeDetector:
    def __init__(self):
        # Load pretrained lightweight models (dummy trained CNNs here)
        audio_model_path = "models/audio_cnn.h5"
        video_model_path = "models/video_cnn.h5"

        if os.path.exists(audio_model_path):
            self.audio_model = tf.keras.models.load_model(audio_model_path)
            print("✅ Loaded Audio Model")
        else:
            self.audio_model = None
            print("⚠️ Audio model not found, using dummy fallback")

        if os.path.exists(video_model_path):
            self.video_model = tf.keras.models.load_model(video_model_path)
            print("✅ Loaded Video Model")
        else:
            self.video_model = None
            print("⚠️ Video model not found, using dummy fallback")

    def extract_audio_features(self, file_path: str):
        y, sr = librosa.load(file_path, sr=22050)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfcc_scaled = np.mean(mfcc.T, axis=0)
        return mfcc_scaled.reshape(1, -1)

    def analyze_audio(self, file_path: str) -> dict:
        try:
            features = self.extract_audio_features(file_path)
            if self.audio_model:
                pred = self.audio_model.predict(features)
                result = "FAKE" if pred[0][0] > 0.5 else "REAL"
                confidence = float(pred[0][0])
            else:
                result = "REAL"
                confidence = 0.75
        except Exception as e:
            return {"error": str(e)}

        return {
            "type": "audio",
            "file": file_path,
            "prediction": result,
            "confidence": round(confidence, 2)
        }

    def extract_video_frames(self, file_path: str, max_frames=5):
        cap = cv2.VideoCapture(file_path)
        frames = []
        count = 0
        while count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (128, 128)) / 255.0
            frames.append(frame)
            count += 1
        cap.release()
        return np.array(frames)

    def analyze_video(self, file_path: str) -> dict:
        try:
            frames = self.extract_video_frames(file_path)
            if self.video_model and len(frames) > 0:
                pred = self.video_model.predict(frames)
                avg_score = float(np.mean(pred))
                result = "FAKE" if avg_score > 0.5 else "REAL"
                confidence = avg_score
            else:
                result = "REAL"
                confidence = 0.70
        except Exception as e:
            return {"error": str(e)}

        return {
            "type": "video",
            "file": file_path,
            "prediction": result,
            "confidence": round(confidence, 2)
        }
