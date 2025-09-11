from pymongo import MongoClient

# Connect to local MongoDB (change to your Atlas URI if needed)
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)

# Select database and collections
db = client["deepfake_detection"]

# Logs collection
logs_collection = db["detection_logs"]
