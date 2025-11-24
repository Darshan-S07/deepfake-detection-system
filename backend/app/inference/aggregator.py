# backend/app/inference/aggregator.py
import time
from collections import deque, defaultdict
from typing import Dict, Any
from utils.db import get_db  # your db helper
from threading import Lock

# Config
AUDIO_WINDOW = 6
VIDEO_WINDOW = 6
WEIGHT_AUDIO = 0.4
WEIGHT_VIDEO = 0.6
ALERT_THRESHOLD = 0.6
HIGH_CONFIDENCE = 0.85

# In-memory store: session_id -> buffers
_sessions = defaultdict(lambda: {"audio": deque(maxlen=AUDIO_WINDOW),
                                 "video": deque(maxlen=VIDEO_WINDOW),
                                 "last_alert_ts": 0})
_lock = Lock()

db = get_db()

def _avg_fake(buf: deque):
    if not buf:
        return 0.0
    vals = [x.get("fake_prob", 0.0) for x in buf]
    return sum(vals) / len(vals)

def add_result(session_id: str, kind: str, result: Dict[str, Any], user: str = None):
    """
    kind: "audio" or "video"
    result: expected to contain at least 'fake' or 'fake_prob' or 'confidence' depending on model output
    """
    with _lock:
        s = _sessions[session_id]
        entry = {
            "timestamp": time.time(),
            "kind": kind,
            "raw": result
        }

        # Normalize to fake_prob in [0,1]
        fake_prob = None
        if "fake" in result and isinstance(result["fake"], (float, int)):
            fake_prob = float(result["fake"])
        elif "confidence" in result:
            # some modules return confidence for predicted class. If predicted==FAKE use it else 1-confidence? fallback
            if result.get("label", "").lower() == "fake":
                fake_prob = float(result["confidence"])
            else:
                fake_prob = 1.0 - float(result["confidence"])
        elif "fake_prob" in result:
            fake_prob = float(result["fake_prob"])
        else:
            # best effort: if model returned two probs as list
            if isinstance(result.get("probs"), (list, tuple)) and len(result["probs"]) >= 2:
                fake_prob = float(result["probs"][1])
            else:
                fake_prob = 0.0

        entry["fake_prob"] = max(0.0, min(1.0, fake_prob))

        # push into buffer
        if kind == "audio":
            s["audio"].append(entry)
        else:
            s["video"].append(entry)

        # compute aggregated scores
        audio_score = _avg_fake(s["audio"])
        video_score = _avg_fake(s["video"])
        combined_score = WEIGHT_AUDIO * audio_score + WEIGHT_VIDEO * video_score

        agg = {
            "session_id": session_id,
            "timestamp": time.time(),
            "audio_score": audio_score,
            "video_score": video_score,
            "combined_score": combined_score,
            "audio_count": len(s["audio"]),
            "video_count": len(s["video"]),
            "last_raw": result
        }

        # Persist small aggregate doc to Mongo for auditing / dashboard
        try:
            db.aggregates.insert_one({
                "session_id": session_id,
                "user": user,
                "timestamp": agg["timestamp"],
                "audio_score": audio_score,
                "video_score": video_score,
                "combined_score": combined_score,
                "audio_count": agg["audio_count"],
                "video_count": agg["video_count"],
                "last_raw": result
            })
        except Exception:
            # don't fail aggregator if DB write fails
            pass

        # determine alert
        alert = None
        now = time.time()
        # throttle alerts to e.g., once per 10s per session
        THROTTLE_SECONDS = 10
        if combined_score >= ALERT_THRESHOLD and (now - s.get("last_alert_ts", 0) > THROTTLE_SECONDS):
            alert = {
                "level": "ALERT",
                "combined_score": combined_score,
                "reason": "combined_score >= threshold",
                "timestamp": now
            }
            s["last_alert_ts"] = now
        elif combined_score >= HIGH_CONFIDENCE and (now - s.get("last_alert_ts", 0) > THROTTLE_SECONDS):
            alert = {
                "level": "HIGH",
                "combined_score": combined_score,
                "reason": "high confidence",
                "timestamp": now
            }
            s["last_alert_ts"] = now

        return {
            "aggregate": agg,
            "alert": alert
        }


def get_session_summary(session_id: str):
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            return None
        return {
            "session_id": session_id,
            "audio_count": len(s["audio"]),
            "video_count": len(s["video"]),
            "audio_recent": list(s["audio"]),
            "video_recent": list(s["video"])
        }
