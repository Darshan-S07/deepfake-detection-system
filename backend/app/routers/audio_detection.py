from fastapi import APIRouter, File, UploadFile
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
import torch
import soundfile as sf

router = APIRouter()
# Load pretrained fake voice detection model
processor = Wav2Vec2Processor.from_pretrained("anton-l/wav2vec2-base-fake-audio-detection")
model = Wav2Vec2ForSequenceClassification.from_pretrained("anton-l/wav2vec2-base-fake-audio-detection")

@router.post("/detect/audio")
async def detect_audio(file: UploadFile = File(...)):
    audio_path = f"temp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())
    audio, rate = sf.read(audio_path)
    inputs = processor(audio, sampling_rate=rate, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
        pred = torch.sigmoid(logits).item()
    label = "FAKE" if pred > 0.5 else "REAL"
    return {"result": label, "confidence": round(pred, 3)}