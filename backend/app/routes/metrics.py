from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import matplotlib.pyplot as plt
import io, base64

router = APIRouter(tags=["metrics"])

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["deepfake_db"]
logs_collection = db["analysis"]

@router.get("/metrics/overview")
def get_metrics_overview():
    """
    Returns summary of total detections, fake vs real counts, and accuracy.
    """
    total = logs_collection.count_documents({})
    fake_count = logs_collection.count_documents({"prediction": "FAKE"})
    real_count = logs_collection.count_documents({"prediction": "REAL"})

    accuracy = 0
    if total > 0:
        # Example calculation: treat REAL as correct for testing
        accuracy = (real_count / total) * 100

    return JSONResponse({
        "total_detections": total,
        "fake_count": fake_count,
        "real_count": real_count,
        "accuracy_percent": round(accuracy, 2)
    })


@router.get("/metrics/graph")
def get_accuracy_graph():
    """
    Generates accuracy graph (fake vs real ratio) and returns as Base64 image.
    """
    total = logs_collection.count_documents({})
    fake_count = logs_collection.count_documents({"prediction": "FAKE"})
    real_count = logs_collection.count_documents({"prediction": "REAL"})

    if total == 0:
        return JSONResponse({"error": "No data found in database"})

    labels = ['Fake', 'Real']
    values = [fake_count, real_count]
    colors = ['#ff4d4d', '#4CAF50']

    plt.figure(figsize=(5, 4))
    plt.bar(labels, values, color=colors)
    plt.title("Deepfake Detection Accuracy")
    plt.xlabel("Prediction Type")
    plt.ylabel("Count")

    # Save as base64 image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return JSONResponse({
        "graph_base64": image_base64,
        "message": "Accuracy graph generated successfully"
    })