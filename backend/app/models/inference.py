import random

def analyze_file_paths(caller_id: str, audio_path: str | None, video_path: str | None):
    # TODO: replace with real model inference
    deepfake_prob = round(random.uniform(0.05, 0.95), 2)
    spam_prob = round(random.uniform(0.05, 0.95), 2)
    return {
        "caller_id": caller_id,
        "deepfake_prob": deepfake_prob,
        "deepfake_detected": deepfake_prob > 0.6,
        "spam_prob": spam_prob,
        "spam_detected": spam_prob > 0.7,
        "recommendation": "Block call" if deepfake_prob > 0.6 or spam_prob > 0.7 else "Safe",
    }

def analyze_chunk(chunk_type: str, b64bytes_len: int):
    # TODO: replace with streaming model inference
    prob = round(random.uniform(0.01, 0.99), 2)
    return {
        "type": chunk_type,
        "deepfake_prob": prob,
        "flag": prob > 0.7,
        "info": f"len={b64bytes_len}"
    }
