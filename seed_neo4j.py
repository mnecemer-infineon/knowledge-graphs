import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from neo4j_utils import is_seeded, insert_users, insert_courses, insert_videos, should_reseed

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Load users from JSON file
with open("data/users.json", "r", encoding="utf-8") as f:
    users = json.load(f)
# Load videos from JSON file
with open("data/videos.json", "r", encoding="utf-8") as f:
    videos = json.load(f)
# Load courses from JSON file if available
try:
    with open("data/courses.json", "r", encoding="utf-8") as f:
        courses = json.load(f)
except FileNotFoundError:
    courses = None

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Helper to create nodes and relationships
def seed_knowledge_graph(users, videos, courses=None):
    with driver.session() as session:
        if is_seeded(session):
            if should_reseed():
                print("Database already seeded. Reseeding as requested.", flush=True)
            else:
                print("Database already seeded. Skipping seeding.", flush=True)
                return
        else:
            print("Database not seeded. Proceeding with seeding...", flush=True)
        insert_users(session, users)
        insert_courses(session, users)
        insert_videos(session, videos, courses)
        print("Knowledge graph seeded successfully.", flush=True)

if __name__ == "__main__":
    seed_knowledge_graph(users, videos, courses)
    print("Knowledge graph including seeds is set up and ready. Refresh your Neo4j browser window to see the lastest changes!", flush=True)
