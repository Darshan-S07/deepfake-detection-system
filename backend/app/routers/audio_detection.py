from fastapi import APIRouter, File, UploadFile
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification
import torch
import soundfile as sf
import os

router = APIRouter()

model_name = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name,use_safetensors=True)

@router.post("/detect/audio")
async def detect_audio(file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    audio, rate = sf.read(file_path)
    inputs = extractor(audio, sampling_rate=rate, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).squeeze().tolist()

    result = {
        "label": "FAKE" if probs[1] > 0.5 else "REAL",
        "fake_prob": round(probs[1], 3),
        "real_prob": round(probs[0], 3)
    }

    return result
