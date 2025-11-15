import sys, os

# Add ai_models/video path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ai_models/video")))

from ai_models.video.video_inference import VideoDeepfakeDetector

# Load model once (no weights_path provided)
video_model_instance = VideoDeepfakeDetector()


def load_video_model():
    """Return loaded video model"""
    return video_model_instance


def predict_video(model, file_path: str):
    """Run prediction using .predict()"""
    try:
        result = model.predict(file_path)
        return result
    except Exception as e:
        return {"error": str(e)}