import cv2
import numpy as np
import pickle
from keras.models import load_model
import os
from keras.models import Sequential
from keras.layers import Dense
from keras.models import load_model

# Dummy video model
if not os.path.exists("models/video_model.h5"):
    print("No video model found, creating dummy model…")
    os.makedirs("models", exist_ok=True)
    model = Sequential([Dense(1, input_shape=(224,224,3), activation='sigmoid')])
    model.save("models/video_model.h5")
# Load your trained video model
video_model = load_model("models/video_model.h5")  # example with Keras CNN

def preprocess_frame(frame_bytes):
    # Convert bytes to OpenCV image
    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (224, 224)) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def process_video_frame(frame_bytes):
    try:
        frame = preprocess_frame(frame_bytes)
        risk_prob = video_model.predict(frame)[0][0]
        if risk_prob < 0.3:
            return "LOW"
        elif risk_prob < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    except Exception as e:
        print("Video processing error:", e)
        return "LOW"
