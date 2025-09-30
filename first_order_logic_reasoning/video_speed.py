from neo4j import GraphDatabase
from collections import defaultdict, Counter
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

THRESHOLD_PERCENTAGE = 0.3  # 30% of users
THRESHOLD_NUMBER = 1        # or at least x users

# Query user-video interactions from the knowledge graph

def get_user_video_acts(tx):
    query = """
    MATCH (u:User)-[w:WATCHED]->(v:Video)
    RETURN u.id AS user_id, v.id AS video_id, w.video_progress_time AS video_progress_time, w.local_watching_time AS local_watching_time
    """
    return list(tx.run(query))


def recommend_playback_speeds(user_video_acts, threshold_percentage=THRESHOLD_PERCENTAGE, threshold_number=THRESHOLD_NUMBER):
    video_speed_counts = defaultdict(Counter)
    video_user_counts = defaultdict(set)

    for act in user_video_acts:
        v = act['video_id']
        user = act['user_id']
        progress = act.get('video_progress_time')
        local = act.get('local_watching_time')
        if progress and local and local > 0:
            speed = round(progress / local, 2)
            video_speed_counts[v][speed] += 1
            video_user_counts[v].add(user)

    recommendations = []
    for v, speed_counts in video_speed_counts.items():
        total_users = len(video_user_counts[v])
        for p, count in speed_counts.items():
            if count >= threshold_number or (total_users > 0 and count / total_users >= threshold_percentage):
                recommendations.append({'video_id': v, 'speed': p, 'user_count': count, 'total_users': total_users})
    return recommendations


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        user_video_acts = session.execute_read(get_user_video_acts)
    recs = recommend_playback_speeds(user_video_acts)
    print("Recommended playback speeds:")
    for rec in recs:
        if rec['user_count'] >= THRESHOLD_NUMBER:
            print(f"Video: {rec['video_id']}, Speed: {rec['speed']}x, Used by: {rec['user_count']}/{rec['total_users']} users")

if __name__ == "__main__":
    main()
