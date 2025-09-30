def is_seeded(session):
    result = session.run("MATCH (u:User) RETURN u LIMIT 1")
    return result.single() is not None

# Insert users, their properties, enrolled courses, and video interactions since these are all defined in the user_video_act.json 
def insert_data_into_kg(session, user_video_act_data, user_data, course_data, video_data):

    # --- Filter users, courses, and videos to only those referenced in user_video_act_data ---
    user_ids = set(user['id'] for user in user_video_act_data)
    course_ids = set()
    video_ids = set()
    for user in user_video_act_data:
        for act in user.get('activity', []):
            if 'course_id' in act:
                course_ids.add(act['course_id'])
            if 'video_id' in act:
                video_ids.add(act['video_id'])

    filtered_user_data = [u for u in user_data if u['id'] in user_ids]
    filtered_course_data = [c for c in course_data if c['id'] in course_ids]
    filtered_video_data = [v for v in video_data if v['id'] in video_ids]

    # --- Insert filtered users with full attributes ---
    print("Insert users", flush=True)
    for user in filtered_user_data:
        user_props = {k: v for k, v in user.items() if k != 'course_order' and k != 'enroll_time'}
        set_clause = ", ".join([f"u.{k} = ${k}" for k in user_props if k != 'id'])
        cypher = "MERGE (u:User {id: $id})"
        if set_clause:
            cypher += f" SET {set_clause}"
        session.run(
            cypher,
            **user_props
        )

    print("Insert courses", flush=True)
    # --- Insert filtered courses with full attributes ---
    for course in filtered_course_data:
        # Keep id, core_id, name, prerequisites, about
        course_props = {k: v for k, v in course.items() if k in ('id', 'core_id', 'name', 'prerequisites', 'about')}
        set_clause = ", ".join([f"c.{k} = ${k}" for k in course_props if k != 'id'])
        cypher = "MERGE (c:Course {id: $id})"
        if set_clause:
            cypher += f" SET {set_clause}"
        session.run(
            cypher,
            **course_props
        )

    print("Insert ENROLLED_IN relationships", flush=True)
    # --- Insert ENROLLED_IN relationships for users and courses ---
    for user in filtered_user_data:
        user_id = user.get("id")
        course_order = user.get("course_order", [])
        enroll_time = user.get("enroll_time", [])
        for idx, course_id in enumerate(course_order):
            time = enroll_time[idx] if idx < len(enroll_time) else None
            # Ensure Course node exists before relationship
            session.run(
                "MERGE (c:Course {id: $course_id})",
                course_id=course_id
            )
            session.run(
                "MATCH (u:User {id: $user_id}), (c:Course {id: $course_id}) "
                "MERGE (u)-[r:ENROLLED_IN]->(c) "
                "SET r.enroll_time = $enroll_time",
                user_id=user_id,
                course_id=course_id,
                enroll_time=time
            )

    print("Insert videos and video segments", flush=True)
    # --- Insert filtered videos with full attributes ---
    for video in filtered_video_data:
        video_props = {k: v for k, v in video.items() if k != 'start' and k != 'end' and k != 'text'}
        set_clause = ", ".join([f"v.{k} = ${k}" for k in video_props if k != 'id'])
        cypher = "MERGE (v:Video {id: $id})"
        if set_clause:
            cypher += f" SET {set_clause}"
        session.run(
            cypher,
            **video_props
        )

        # Insert video segments for this video
        starts = video.get('start', [])
        ends = video.get('end', [])
        texts = video.get('text', [])
        for idx, (start, end, text) in enumerate(zip(starts, ends, texts)):
            segment_id = f"{video['id']}_S{idx}"
            session.run(
                """
                MATCH (v:Video {id: $video_id})
                MERGE (s:Segment {id: $segment_id})
                SET s.segment_index = $segment_index, s.start = $start, s.end = $end, s.text = $text
                MERGE (v)-[:HAS_SEGMENT]->(s)
                """,
                video_id=video['id'],
                segment_id=segment_id,
                segment_index=idx,
                start=start,
                end=end,
                text=text
            )

    print("Insert relationships - videos are part of courses", flush=True)
    # --- Insert course-video relationships (PART_OF) for filtered courses/videos ---
    for course in filtered_course_data:
        video_order = course.get('video_order', [])
        display_names = course.get('display_name', [])
        chapters = course.get('chapter', [])
        for idx, video_id in enumerate(video_order):
            if video_id in video_ids:
                session.run(
                    "MATCH (v:Video {id: $video_id}), (c:Course {id: $course_id}) "
                    "MERGE (v)-[r:PART_OF {video_order: $video_order}]->(c) "
                    "SET r.display_name = $display_name, r.chapter = $chapter",
                    video_id=video_id,
                    course_id=course['id'],
                    video_order=idx,
                    display_name=display_names[idx] if idx < len(display_names) else None,
                    chapter=chapters[idx] if idx < len(chapters) else None
                )

    print("Insert user relationships - users watched videos", flush=True)
    # --- Insert user activities and WATCHED relationships ---
    for user in filtered_user_data:
        user_id = user.get("id")
        activities = user.get("activity", [])
        # Insert WATCHED relationships for videos
        for act in activities:
            video_id = act.get("video_id")
            if video_id:
                session.run(
                    "MATCH (u:User {id: $user_id}), (v:Video {id: $video_id}) "
                    "MERGE (u)-[r:WATCHED]->(v) "
                    "SET r.watching_count = $watching_count, r.video_duration = $video_duration, "
                    "r.local_watching_time = $local_watching_time, r.video_progress_time = $video_progress_time, "
                    "r.video_start_time = $video_start_time, r.video_end_time = $video_end_time, "
                    "r.local_start_time = $local_start_time, r.local_end_time = $local_end_time",
                    user_id=user_id,
                    video_id=video_id,
                    watching_count=act.get("watching_count"),
                    video_duration=act.get("video_duration"),
                    local_watching_time=act.get("local_watching_time"),
                    video_progress_time=act.get("video_progress_time"),
                    video_start_time=act.get("video_start_time"),
                    video_end_time=act.get("video_end_time"),
                    local_start_time=act.get("local_start_time"),
                    local_end_time=act.get("local_end_time")
                )


# Returns True if the RESEED environment variable is set to a truthy value
def should_reseed():
    import os
    return os.getenv("RESEED", "false").strip().lower() in ("1", "true", "yes", "y")

# Deletes all nodes and relationships in the database
def clear_database(session):
    session.run("MATCH (n) DETACH DELETE n")
