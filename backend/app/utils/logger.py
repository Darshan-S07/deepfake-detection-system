import logging
from datetime import datetime
import os

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOG_DIR, "detections.log")
logging.basicConfig(
    filename=log_file,
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

class DetectionLogger:
    @staticmethod
    def log_event(content_type: str, status: str, details: str = ""):
        """
        Log detection event to file.
        
        Args:
            content_type (str): Type of detection (audio, video, text, email, etc.)
            status (str): Result (e.g., 'REAL', 'FAKE', 'SUSPICIOUS')
            details (str): Extra details (confidence score, file path, metadata, etc.)
        """
        message = f"TYPE={content_type} | STATUS={status} | DETAILS={details}"
        logging.info(message)
