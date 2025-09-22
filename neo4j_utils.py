def is_seeded(session):
    result = session.run("MATCH (u:User) RETURN u LIMIT 1")
    return result.single() is not None

# Insert users, their properties, enrolled courses, and video interactions
def insert_users(session, users):
    for user in users:
        user_id = user.get("id", user.get("user_id"))
        session.run(
            "MERGE (u:User {id: $id, name: $name, age: $age, location: $location})",
            id=user_id, name=user["name"], age=user.get("age"), location=user.get("location")
        )
        # Video interactions
        for interaction in user.get("video_interactions", []):
            session.run(
                "MATCH (u:User {id: $user_id}), (v:Video {id: $video_id}) "
                "MERGE (u)-[r:INTERACTED_WITH {preferred_speed: $preferred_speed, advertisements_skipped: $advertisements_skipped}] -> (v) "
                "SET r.segments_skipped = $segments_skipped, r.segments_watched = $segments_watched",
                user_id=user_id,
                video_id=interaction["video_id"],
                preferred_speed=interaction.get("preferred_speed"),
                advertisements_skipped=interaction.get("advertisements_skipped"),
                segments_skipped=interaction.get("segments_skipped", []),
                segments_watched=interaction.get("segments_watched", [])
            )

def insert_courses(session, users):
    course_ids = set()
    for user in users:
        user_id = user.get("id", user.get("user_id"))
        for course in user.get("enrolled_courses", []):
            course_id = course["course_id"]
            course_ids.add(course_id)
            session.run(
                "MERGE (c:Course {id: $course_id}) SET c.name = $course_name",
                course_id=course_id,
                course_name=course.get("name")
            )
            session.run(
                "MATCH (u:User {id: $user_id}), (c:Course {id: $course_id}) "
                "MERGE (u)-[r:ENROLLED_IN {enroll_time: $enroll_time}]->(c)",
                user_id=user_id, course_id=course_id, enroll_time=course["enrollment_date"]
            )
    return list(course_ids)

# Insert videos, segments, and link to creator and courses
def insert_videos(session, videos, courses=None):
    for video in videos:
        session.run(
            "MERGE (v:Video {id: $id, name: $name, duration: $duration, tags: $tags})",
            id=video["video_id"], name=video["name"], duration=video["duration"], tags=video.get("tags", [])
        )
        # Link video to creator
        session.run(
            "MATCH (v:Video {id: $video_id}), (u:User {id: $creator_id}) "
            "MERGE (u)-[:CREATED]->(v)",
            video_id=video["video_id"], creator_id=video["creator_id"]
        )
        # Add segments as nodes and relationships
        for segment in video.get("segments", []):
            session.run(
                "MERGE (s:Segment {id: $segment_id, type: $type, start: $start, end: $end})",
                segment_id=segment["segment_id"], type=segment["type"], start=segment["start"], end=segment["end"]
            )
            session.run(
                "MATCH (v:Video {id: $video_id}), (s:Segment {id: $segment_id}) "
                "MERGE (v)-[:HAS_SEGMENT]->(s)",
                video_id=video["video_id"], segment_id=segment["segment_id"]
            )
    # Link videos to courses with order if courses provided
    if courses:
        for course in courses:
            session.run(
                "MERGE (c:Course {id: $course_id}) SET c.name = $course_name",
                course_id=course["id"], course_name=course.get("name")
            )
            video_order = course.get("video_order", [])
            for idx, video_id in enumerate(video_order):
                session.run(
                    "MATCH (v:Video {id: $video_id}), (c:Course {id: $course_id}) "
                    "MERGE (v)-[r:PART_OF {order: $order}]->(c)",
                    video_id=video_id, course_id=course["id"], order=idx
                )

def should_reseed():
    import os
    return os.getenv("RESEED", "false").lower() == "true"
