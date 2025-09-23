import os
import json
from dotenv import load_dotenv

# Run this function to generate a proper data subset of all mooc data
load_dotenv()

USER_VIDEO_ACT_LIMIT = int(os.getenv("USER_VIDEO_ACT_LIMIT", "100"))
print("USER_VIDEO_ACT_LIMIT:", USER_VIDEO_ACT_LIMIT)
MOOC_DIR = os.path.join(os.path.dirname(__file__), "../mooc")
SUBSET_DIR = os.path.dirname(__file__)

# Load mooc data
with open(os.path.join(MOOC_DIR, "user_video_act.json"), "r", encoding="utf-8") as f:
    user_video_act_data = json.load(f)
with open(os.path.join(MOOC_DIR, "user.json"), "r", encoding="utf-8") as f:
    user_data = json.load(f)
with open(os.path.join(MOOC_DIR, "course.json"), "r", encoding="utf-8") as f:
    course_data = json.load(f)
with open(os.path.join(MOOC_DIR, "video.json"), "r", encoding="utf-8") as f:
    video_data = json.load(f)

# Limit user_video_act_data
user_video_act_subset = user_video_act_data[:USER_VIDEO_ACT_LIMIT]

# Find referenced user, course, and video ids
user_ids = set(user['id'] for user in user_video_act_subset)
course_ids = set()
video_ids = set()
for user in user_video_act_subset:
    for act in user.get('activity', []):
        if 'course_id' in act:
            course_ids.add(act['course_id'])
        if 'video_id' in act:
            video_ids.add(act['video_id'])

user_subset = [u for u in user_data if u['id'] in user_ids]
course_subset = [c for c in course_data if c['id'] in course_ids]
video_subset = [v for v in video_data if v['id'] in video_ids]

# Write subset files
with open(os.path.join(SUBSET_DIR, "user_video_act.json"), "w", encoding="utf-8") as f:
    json.dump(user_video_act_subset, f, ensure_ascii=False, indent=2)
with open(os.path.join(SUBSET_DIR, "user.json"), "w", encoding="utf-8") as f:
    json.dump(user_subset, f, ensure_ascii=False, indent=2)
with open(os.path.join(SUBSET_DIR, "course.json"), "w", encoding="utf-8") as f:
    json.dump(course_subset, f, ensure_ascii=False, indent=2)
with open(os.path.join(SUBSET_DIR, "video.json"), "w", encoding="utf-8") as f:
    json.dump(video_subset, f, ensure_ascii=False, indent=2)

print(f"Subset files written to {SUBSET_DIR}")
