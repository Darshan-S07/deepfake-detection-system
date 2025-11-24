import torch
from fastapi import APIRouter, File, UploadFile
from transformers import AutoProcessor, VideoMAEForVideoClassification
import cv2
from PIL import Image
import os

router = APIRouter()

# Use a reliable VideoMAE model fine-tuned on deepfakes
MODEL_NAME = "shylhy/videomae-large-finetuned-deepfake-subset"

# Load processor and model
processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = VideoMAEForVideoClassification.from_pretrained(MODEL_NAME).eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def extract_frames(video_path, num_frames=16):
    """Extracts evenly spaced frames from the video."""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < 4:
        cap.release()
        return []

    frame_indices = torch.linspace(0, total_frames - 1, num_frames).int().tolist()
    frames = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame))

    cap.release()
    return frames

@router.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    try:
        # Save uploaded video temporarily
        temp_path = "/tmp/video.mp4"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract frames
        frames = extract_frames(temp_path, num_frames=16)
        if len(frames) < 4:
            return {"error": "Video too short for analysis"}

        # Process frames into model input
        inputs = processor(
            frames, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]

        fake_prob = float(probs[1])
        real_prob = float(probs[0])

        # Remove temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            "status": "success",
            "label": "FAKE" if fake_prob > 0.5 else "REAL",
            "fake_probability": fake_prob,
            "real_probability": real_prob,
            "frames_used": len(frames)
        }

    except Exception as e:
        return {"error": str(e)}
