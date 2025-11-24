from pymongo import MongoClient

def init_db():
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["deepfake_db"]

    # Create collections
    users = db["users"]
    analysis = db["analysis"]

    # Add indexes (for faster lookups)
    users.create_index("email", unique=True)
    analysis.create_index("user_id")

    # Insert a sample user
    if users.count_documents({"email": "test@example.com"}) == 0:
        users.insert_one({
            "name": "Test User",
            "email": "test@example.com",
            "password": "hashed_password",  # Later we replace with bcrypt hash
            "role": "user"
        })

    print("✅ Database initialized with collections and sample data.")

if __name__ == "__main__":
    init_db()
