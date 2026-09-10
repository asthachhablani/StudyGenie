"""
seed.py — Optional sample data seeder for StudyGenie AI.
Creates sample subjects and progress entries.

Run: python seed.py
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DATABASE_PATH", "studygenie.db")

from dotenv import load_dotenv
load_dotenv()

from models.db import init_db, get_db_connection
from models.user_model import create_user, find_user_by_email

DEMO_SUBJECTS = [
    {"name": "DBMS", "description": "Database Management Systems"},
    {"name": "Operating Systems", "description": "OS concepts and algorithms"},
    {"name": "Computer Networks", "description": "TCP/IP, routing, protocols"},
    {"name": "Data Structures & Algorithms", "description": "DSA fundamentals"},
]

DEMO_TOPICS = {
    "DBMS": ["SQL Joins", "Normalization", "Transactions", "Indexing", "ER Diagrams"],
    "Operating Systems": ["Process Scheduling", "Paging", "Deadlocks", "File Systems", "Memory Management"],
    "Computer Networks": ["TCP/IP", "OSI Model", "Routing Algorithms", "DNS", "HTTP"],
    "Data Structures & Algorithms": ["Sorting", "Trees", "Graphs", "Dynamic Programming", "Hashing"],
}


def seed():
    # Ensure schema exists
    init_db()

    conn = get_db_connection()
    print("StudyGenie AI — Data Seeder")
    print("=" * 40)

    # Create demo user if not exists
    demo_email = "demo@studygenie.ai"
    user = find_user_by_email(demo_email)
    if not user:
        user = create_user("Demo Student", demo_email, "StudyGenie@123")
        print(f"Created demo user: {demo_email} / StudyGenie@123")
    else:
        print(f"Demo user already exists: {demo_email}")

    user_id = user["id"]

    # Clear existing demo data for this user
    conn.execute("DELETE FROM subjects WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM progress WHERE user_id = ?", (user_id,))
    conn.commit()

    # Create subjects
    subject_ids = {}
    for sub_data in DEMO_SUBJECTS:
        cur = conn.execute(
            "INSERT INTO subjects (user_id, name, description) VALUES (?, ?, ?)",
            (user_id, sub_data["name"], sub_data["description"]),
        )
        subject_ids[sub_data["name"]] = cur.lastrowid
        print(f"  Created subject: {sub_data['name']}")
    conn.commit()

    # Seed progress data
    for subject_name, topics in DEMO_TOPICS.items():
        sid = subject_ids.get(subject_name)
        if not sid:
            continue
        for topic in topics:
            score = round(random.uniform(30, 95), 1)
            strength = "strong" if score >= 70 else ("moderate" if score >= 50 else "weak")
            conn.execute(
                """INSERT OR REPLACE INTO progress
                   (user_id, subject_id, topic, quiz_score, strength, attempt_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, sid, topic, score, strength, random.randint(1, 5)),
            )
    conn.commit()
    conn.close()

    print(f"\nSeeding complete!")
    print(f"Login: {demo_email}")
    print(f"Password: StudyGenie@123")
    print("\nNote: Upload a PDF to see RAG and AI features working.")


if __name__ == "__main__":
    seed()
