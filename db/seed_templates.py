"""Seed initial BFSI templates. Used when MongoDB is connected; otherwise backend uses in-memory _TEMPLATES."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# When MongoDB is wired, insert these; for MVP backend/main.py has _TEMPLATES in memory.
SEED_TEMPLATES = [
    {
        "id": "bfsi-loan-reminder",
        "name": "BFSI Loan Reminder",
        "description": "Template for loan payment reminders",
        "use_count": 0,
        "avg_rating": 0.0,
        "language": "English",
        "category": "BFSI",
    },
    {
        "id": "bfsi-appointment-booking",
        "name": "BFSI Appointment Booking",
        "description": "Template for booking branch or agent appointments",
        "use_count": 0,
        "avg_rating": 0.0,
        "language": "English",
        "category": "BFSI",
    },
]

if __name__ == "__main__":
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("MONGO_URI not set; backend uses in-memory templates.")
        sys.exit(0)
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri)
        db = client.get_default_database()
        coll = db.get_collection("templates")
        for t in SEED_TEMPLATES:
            coll.update_one({"id": t["id"]}, {"$set": t}, upsert=True)
        print("Seeded", len(SEED_TEMPLATES), "templates.")
    except Exception as e:
        print("Seed failed:", e)
        sys.exit(1)
