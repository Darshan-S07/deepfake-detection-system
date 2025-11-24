from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
import torch
import torchaudio

MODEL_NAME = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"

# Load model + extractor
feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
model = AutoModelForAudioClassification.from_pretrained(MODEL_NAME)

model.eval()

def load_audio_model():
    return model, feature_extractor


def predict_audio(file_path: str) -> dict:
    waveform, sample_rate = torchaudio.load(file_path)

    # Resample to 16kHz if needed
    if sample_rate != 16000:
        transform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = transform(waveform)

    inputs = feature_extractor(
        waveform.squeeze().numpy(), 
        sampling_rate=16000, 
        return_tensors="pt"
    )

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1)

    fake_prob = float(probs[0][1])
    real_prob = float(probs[0][0])

    return {
        "real": real_prob,
        "fake": fake_prob,
        "prediction": "FAKE" if fake_prob > 0.5 else "REAL"
    }