from fastapi import APIRouter, File, UploadFile
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
import torch
import soundfile as sf
import os

router = APIRouter()

# ✅ use feature extractor instead of processor
extractor = AutoFeatureExtractor.from_pretrained("superb/wav2vec2-base-superb-ks")
model = AutoModelForAudioClassification.from_pretrained("superb/wav2vec2-base-superb-ks")

@router.post("/detect/audio")
async def detect_audio(file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # read audio
    audio, rate = sf.read(file_path)
    inputs = extractor(audio, sampling_rate=rate, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        conf, pred = torch.max(probs, dim=1)

    label = model.config.id2label[pred.item()]
    return {"label": label, "confidence": round(conf.item(), 3)}