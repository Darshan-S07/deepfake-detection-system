import numpy as np
import librosa
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
if not os.path.exists("models/audio_model.pkl"):
    print("No audio model found, creating dummy model…")
    X_dummy = np.random.rand(10, 13)  # 10 samples, 13 features (MFCCs)
    y_dummy = np.random.randint(0, 2, 10)  # 0 = LOW, 1 = HIGH
    dummy_model = RandomForestClassifier()
    dummy_model.fit(X_dummy, y_dummy)

    os.makedirs("models", exist_ok=True)
    with open("models/audio_model.pkl", "wb") as f:
        pickle.dump(dummy_model, f)

# Load your trained audio model
with open("models/audio_model.pkl", "rb") as f:
    audio_model = pickle.load(f)

def extract_audio_features(audio_bytes):
    # Convert bytes to numpy float array
    audio = np.frombuffer(audio_bytes, dtype=np.float32)
    # Feature extraction (MFCCs)
    mfcc = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=13)
    return np.mean(mfcc.T, axis=0)

def process_audio_chunk(audio_bytes):
    try:
        features = extract_audio_features(audio_bytes)
        risk_prob = audio_model.predict_proba([features])[0][1]  # probability of deepfake
        if risk_prob < 0.3:
            return "LOW"
        elif risk_prob < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    except Exception as e:
        print("Audio processing error:", e)
        return "LOW"
