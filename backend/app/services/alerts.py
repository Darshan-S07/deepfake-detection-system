def analyze_call(call_info):
    # Simulate deepfake/spam detection
    caller_id = call_info.caller_id
    suspicious_audio = "suspicious" in call_info.audio_url
    suspicious_video = "suspicious" in call_info.video_url

    result = {
        "caller_id": caller_id,
        "deepfake_detected": suspicious_audio or suspicious_video,
        "spam_detected": "spam" in caller_id.lower(),
        "recommendation": "Block call" if suspicious_audio or suspicious_video else "Safe"
    }
    return result
