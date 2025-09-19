import cv2
import torch
from torchvision import transforms
from torchvision.models import efficientnet_b0

class VideoDeepfakeDetector:
    def __init__(self, weights_path=None):
        self.model = efficientnet_b0(pretrained=False)
        self.model.classifier = torch.nn.Linear(self.model.classifier[1].in_features, 2)

        if weights_path:
            self.model.load_state_dict(torch.load(weights_path, map_location="cpu"))

        self.model.eval()
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225])
        ])

    def predict(self, video_path: str, max_frames=10):
        cap = cv2.VideoCapture(video_path)
        frames, total = [], int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total // max_frames)

        for i in range(0, total, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(self.transform(frame))
        cap.release()

        if not frames:
            return {"label": "real", "confidence": 0.0}

        batch = torch.stack(frames)
        with torch.no_grad():
            logits = self.model(batch)
        probs = torch.softmax(logits, dim=1).mean(dim=0).tolist()

        return {
            "label": "fake" if probs[1] > probs[0] else "real",
            "confidence": float(max(probs))
        }
