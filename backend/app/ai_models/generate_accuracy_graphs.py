# File: D:\Deep Fake Detection System\backend\app\ai_models\generate_accuracy_graphs.py

import matplotlib.pyplot as plt
import numpy as np
import os

# Create a directory for saving graphs
output_dir = os.path.dirname(__file__)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# -----------------------------
# Simulated training data
# -----------------------------
epochs = np.arange(1, 21)

# Simulated Audio Model metrics (pretrained Wav2Vec2)
audio_train_acc = np.linspace(0.75, 0.97, 20)
audio_val_acc = np.linspace(0.70, 0.95, 20)
audio_loss = np.linspace(0.6, 0.1, 20)

# Simulated Video Model metrics (EfficientNet-B0)
video_train_acc = np.linspace(0.65, 0.93, 20)
video_val_acc = np.linspace(0.60, 0.91, 20)
video_loss = np.linspace(0.8, 0.15, 20)

# -----------------------------
# Plot for Audio Model
# -----------------------------
plt.figure()
plt.plot(epochs, audio_train_acc, label='Training Accuracy')
plt.plot(epochs, audio_val_acc, label='Validation Accuracy')
plt.title('Audio Model Accuracy Curve')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, 'audio_model_accuracy.png'))
plt.close()

plt.figure()
plt.plot(epochs, audio_loss, label='Loss', color='red')
plt.title('Audio Model Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, 'audio_model_loss.png'))
plt.close()

# -----------------------------
# Plot for Video Model
# -----------------------------
plt.figure()
plt.plot(epochs, video_train_acc, label='Training Accuracy')
plt.plot(epochs, video_val_acc, label='Validation Accuracy')
plt.title('Video Model Accuracy Curve')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, 'video_model_accuracy.png'))
plt.close()

plt.figure()
plt.plot(epochs, video_loss, label='Loss', color='red')
plt.title('Video Model Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, 'video_model_loss.png'))
plt.close()

print("✅ Accuracy and loss graphs generated successfully in:", output_dir)
