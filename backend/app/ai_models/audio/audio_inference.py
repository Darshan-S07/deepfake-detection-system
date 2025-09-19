from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
import torch
import librosa

class AudioDeepfakeDetector:
    def __init__(self, model_name="motheecreator/wav2vec2-base-deepfake"):
        # HuggingFace pretrained model
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

    def predict(self, audio_path: str):
        # load audio
        speech, sr = librosa.load(audio_path, sr=16000)
        inputs = self.processor(speech, sampling_rate=sr, return_tensors="pt", padding=True)

        with torch.no_grad():
            logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        return {
            "label": "fake" if probs[1] > probs[0] else "real",
            "confidence": float(max(probs))
        }
