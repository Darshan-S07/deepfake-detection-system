from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
import torch
import librosa

class AudioDeepfakeDetector:
    def __init__(self, model_name="HyperMoon/wav2vec2-base-960h-finetuned-deepfake"):
        # Use feature extractor for models without a tokenizer
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
        self.model = AutoModelForAudioClassification.from_pretrained(model_name)
        self.model.eval()

    def predict(self, audio_path: str):
        # Load audio
        speech, sr = librosa.load(audio_path, sr=16000)
        inputs = self.feature_extractor(speech, sampling_rate=sr, return_tensors="pt")

        with torch.no_grad():
            logits = self.model(**inputs).logits
        
        probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        # Ensure probs is always a list
        if isinstance(probs, float):
            probs = [probs]

        # Simple label assignment
        if len(probs) >= 2:
            label = "fake" if probs[1] > probs[0] else "real"
        else:
            label = "real"  # fallback if only one class

        return {
            "label": label,
            "confidence": float(max(probs))
        }
