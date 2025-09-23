import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from neo4j_utils import is_seeded, should_reseed, insert_data_into_kg

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
DATA_FOLDER = os.getenv("DATA_FOLDER", "data/data_subset")
USER_VIDEO_ACT_LIMIT = int(os.getenv("USER_VIDEO_ACT_LIMIT", "0"))

# Load all data from DATA_FOLDER
with open(os.path.join(DATA_FOLDER, "user_video_act.json"), "r", encoding="utf-8") as f:
    user_video_act_data = json.load(f)
with open(os.path.join(DATA_FOLDER, "user.json"), "r", encoding="utf-8") as f:
    user_data = json.load(f)
with open(os.path.join(DATA_FOLDER, "course.json"), "r", encoding="utf-8") as f:
    course_data = json.load(f)
with open(os.path.join(DATA_FOLDER, "video.json"), "r", encoding="utf-8") as f:
    video_data = json.load(f)

# Limit user_video_act_data if USER_VIDEO_ACT_LIMIT is set
if USER_VIDEO_ACT_LIMIT > 0:
    user_video_act_data = user_video_act_data[:USER_VIDEO_ACT_LIMIT]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Seed the knowledge graph with data
def seed_knowledge_graph(user_video_act_data, user_data, course_data, video_data):
    from neo4j_utils import clear_database
    with driver.session() as session:
        if is_seeded(session):
            if should_reseed():
                print("Database already seeded. Reseeding as requested. Clearing database...", flush=True)
                clear_database(session)
            else:
                print("Database already seeded. Skipping seeding.", flush=True)
                return
        else:
            print("Database not seeded. Proceeding with seeding...", flush=True)
        print("Inserting data into knowledge graph...", flush=True)
        insert_data_into_kg(session, user_video_act_data, user_data, course_data, video_data)
        print("Knowledge graph seeded successfully.", flush=True)


if __name__ == "__main__":
    seed_knowledge_graph(user_video_act_data, user_data, course_data, video_data)
    print("Knowledge graph including seeds is set up and ready. Refresh your Neo4j browser window to see the latest changes!", flush=True)
