import sys, os

# Add ai_models/audio path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ai_models/audio")))

from audio_inference import AudioDeepfakeDetector

# Load model once
audio_model_instance = AudioDeepfakeDetector()


def load_audio_model():
    """Return the already-loaded audio model instance"""
    return audio_model_instance


def predict_audio(model, file_path: str):
    """Run prediction using the model's .predict() method"""
    try:
        result = model.predict(file_path)
        return result
    except Exception as e:
        return {"error": str(e)}