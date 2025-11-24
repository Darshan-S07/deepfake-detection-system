# backend/app/routers/video_detection.py

import torch
import torch.nn.functional as F
from torch import nn
from fastapi import APIRouter, File, UploadFile
from PIL import Image
import cv2
from transformers import CLIPModel, CLIPConfig, CLIPImageProcessor
from typing import List, Union

router = APIRouter()

# -------------------------
# Model / Processor Setup
# -------------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_FRAMES = 12
FRAME_SIZE = (384, 384)
CLIP_MODEL_NAME = "openai/clip-vit-large-patch14"  # Backbone
CHECKPOINT_PATH = "path/to/deepfake_detector_checkpoint.pt"  # replace with actual

# -------------------------
# Deepfake Detector Class
# -------------------------
class DeepfakeDetector(nn.Module):
    def __init__(self, clip_model_name: str = CLIP_MODEL_NAME, num_frames: int = NUM_FRAMES):
        super().__init__()
        self.num_frames = num_frames
        self.clip = CLIPModel.from_pretrained(clip_model_name)
        for p in self.clip.parameters():
            p.requires_grad = False
        embed_dim = self.clip.config.projection_dim
        self.adapter = nn.Linear(self.num_frames, self.num_frames)
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 1024),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(1024, 2)
        )

    def forward(self, x: torch.Tensor):
        b, t, c, h, w = x.shape
        x_reshaped = x.view(b * t, c, h, w)
        clip_outputs = self.clip.vision_model(pixel_values=x_reshaped)
        pooled = clip_outputs.pooler_output
        pooled = pooled.view(b, t, -1)
        pooled_t = pooled.permute(0, 2, 1)
        adapted = self.adapter(pooled_t)
        adapted = adapted.permute(0, 2, 1)
        video_repr = adapted.mean(dim=1)
        logits = self.classifier(video_repr)
        return logits


# Load model
detector = DeepfakeDetector().to(DEVICE)
# Load checkpoint if available
try:
    ckpt = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
    state = ckpt.get("model_state_dict", ckpt)
    detector.load_state_dict(state)
except Exception:
    print("Checkpoint not found or invalid. Using randomly initialized model.")

detector.eval()
processor = CLIPImageProcessor.from_pretrained(CLIP_MODEL_NAME)


# -------------------------
# Helper Functions
# -------------------------
def extract_frames_from_video(video_path: str, num_frames: int = NUM_FRAMES, size=FRAME_SIZE) -> List[Image.Image]:
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return []

    indices = torch.linspace(0, total - 1, num_frames).int().tolist()
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame).resize(size)
        frames.append(img)
    cap.release()
    return frames


def preprocess_frames(pil_frames: List[Image.Image], processor: CLIPImageProcessor) -> torch.Tensor:
    proc = processor(images=pil_frames, return_tensors="pt")
    pixel_values = proc["pixel_values"]  # (num_frames, 3, H, W)
    pixel_values = pixel_values.unsqueeze(0)  # (1, num_frames, 3, H, W)
    return pixel_values


# -------------------------
# FastAPI Endpoint
# -------------------------
@router.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    try:
        # Save uploaded video
        temp_path = "/tmp/temp_video.mp4"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract frames
        frames = extract_frames_from_video(temp_path)
        if len(frames) < 4:
            return {"error": "Video too short for analysis"}

        # Preprocess
        pixel_values = preprocess_frames(frames, processor).to(DEVICE)

        # Model inference
        with torch.no_grad():
            logits = detector(pixel_values)
            probs = F.softmax(logits, dim=-1)
            fake_prob = float(probs[0, 1])
            real_prob = float(probs[0, 0])
            pred_label = "FAKE" if fake_prob > 0.5 else "REAL"

        return {
            "status": "success",
            "label": pred_label,
            "fake_probability": fake_prob,
            "real_probability": real_prob,
            "frames_used": len(frames)
        }

    except Exception as e:
        return {"error": str(e)}
