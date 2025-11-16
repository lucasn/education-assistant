from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pymongo import MongoClient
from datetime import datetime
import os
from pathlib import Path
import uvicorn

app = FastAPI(title="Evaluation Dashboard API")

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB configuration
mongo_host = os.getenv("MONGO_HOST", "localhost")
mongo_port = int(os.getenv("MONGO_PORT", "27017"))
mongo_user = os.getenv("MONGO_USER", "root")
mongo_password = os.getenv("MONGO_PASSWORD", "root")

mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
mongo_client = MongoClient(mongo_uri)
db = mongo_client["education"]
evaluation_collection = db["evaluation"]


@app.get('/')
def serve_frontend():
    """
    Serve the frontend HTML file.
    """
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend file not found")
    return FileResponse(index_file)


@app.get('/api/test-batteries')
def get_test_batteries():
    """
    Get all test batteries grouped by test_run_id, ordered by most recent.
    Returns a list of test batteries with metadata.
    """
        # Aggregate to group tests by test_run_id
    pipeline = [
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$group": {
                "_id": "$test_run_id",
                "test_run_id": {"$first": "$test_run_id"},
                "test_count": {"$sum": 1},
                "timestamp": {"$first": "$timestamp"},
                "questions": {"$push": "$question"}
            }
        },
        {
            "$sort": {"timestamp": -1}
        }
    ]

    batteries = list(evaluation_collection.aggregate(pipeline))

    # Convert datetime to string for JSON serialization
    for battery in batteries:
        battery["_id"] = str(battery["_id"])
        if isinstance(battery["timestamp"], datetime):
            battery["timestamp"] = battery["timestamp"].isoformat()

    return batteries


@app.get('/api/test-battery/{test_run_id}')
def get_test_battery(test_run_id: str):
    """
    Get all tests for a specific test_run_id.
    """
    tests = list(evaluation_collection.find(
        {"test_run_id": test_run_id}
    ).sort("timestamp", 1))

    # Convert ObjectId and datetime to string for JSON serialization
    for test in tests:
        test["_id"] = str(test["_id"])
        if isinstance(test["timestamp"], datetime):
            test["timestamp"] = test["timestamp"].isoformat()

    return tests


if __name__ == '__main__':
    print("=" * 80)
    print("Starting Evaluation Dashboard (FastAPI)")
    print("=" * 80)
    print(f"MongoDB Connection: {mongo_host}:{mongo_port}")
    print()
    print(f"🌐 Dashboard:        http://localhost:5001")
    print(f"📚 API Docs:         http://localhost:5001/docs")
    print(f"📖 ReDoc:            http://localhost:5001/redoc")
    print("=" * 80)
    uvicorn.run("api:app", host="0.0.0.0", port=5001, reload=True)
