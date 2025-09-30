from neo4j import GraphDatabase
from pyDatalog import pyDatalog
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")  

SKIP_RATE_THRESHOLD = 0.01
MIN_SKIPPED = 3  


def get_user_segment_interactions(tx):
    query = """
    MATCH (u:User)-[w:WATCHED]->(v:Video)-[:HAS_SEGMENT]->(s:Segment)
    RETURN u.id AS user, v.id AS video, s.id AS segment,
           s.start AS seg_start, s.end AS seg_end,
           w.video_start_time AS watched_start, w.video_end_time AS watched_end
    """
    return list(tx.run(query))

def get_segments_skipped_by_percentage(segment_views, segment_skips, threshold=0.5):
    """
    Returns a list of (video, segment, skip_rate, skipped, total) for segments skipped by at least threshold percent of users.
    """
    results = []
    for seg_id in segment_views:
        total = len(segment_views[seg_id])
        skipped = len(segment_skips.get(seg_id, set()))
        skip_rate = skipped / total if total > 0 else 0
        if total > 0 and skip_rate >= threshold:
            results.append((seg_id[0], seg_id[1], skip_rate, skipped, total))
    return results

def get_segments_skipped_by_number(segment_skips, min_skipped=1):
    """
    Returns a list of (video, segment, skipped) for segments skipped by at least min_skipped users.
    """
    results = []
    for seg_id, skipped_users in segment_skips.items():
        skipped = len(skipped_users)
        if skipped >= min_skipped:
            results.append((seg_id[0], seg_id[1], skipped))
    return results

def main():
    pyDatalog.clear()
    # Declare all logic terms before use
    pyDatalog.create_terms('WatchedSegment, HighSkipRate, RecommendToSkip, U, V, S')

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        user_segment_records = session.execute_read(get_user_segment_interactions)

    segment_views = defaultdict(set)
    segment_skips = defaultdict(set)

    for record in user_segment_records:
        seg_id = (record['video'], record['segment'])
        seg_start = record['seg_start']
        seg_end = record['seg_end']
        watched_start = record['watched_start']
        watched_end = record['watched_end']

        # Only consider users who actually watched some part of the segment
        if watched_end is not None and watched_start is not None and not (watched_end < seg_start or watched_start > seg_end):
            segment_views[seg_id].add(record['user'])
            # Assert WatchedSegment fact for pyDatalog
            pyDatalog.assert_fact('WatchedSegment', record['user'], record['video'], record['segment'])
        else:
            # If no watch times or no overlap, treat as skipped
            segment_skips[seg_id].add(record['user'])

    for seg_id in segment_views:
        total = len(segment_views[seg_id])
        skipped = len(segment_skips.get(seg_id, set()))
        if total > 0 and skipped / total > SKIP_RATE_THRESHOLD:
            pyDatalog.assert_fact('HighSkipRate', seg_id[0], seg_id[1])

    # Debug: print number of HighSkipRate facts asserted
    try:
        high_skip_facts = pyDatalog.ask('HighSkipRate(V, S)')
        num_high_skip = len(high_skip_facts.answers) if high_skip_facts is not None else 0
        print(f"Number of HighSkipRate facts asserted: {num_high_skip}")
    except AttributeError:
        print("No HighSkipRate facts asserted.")
        num_high_skip = 0

    # Define the rule
    pyDatalog.load('RecommendToSkip(V, S) <= WatchedSegment(U, V, S) & HighSkipRate(V, S)')

    # Query recommendations with error handling
    print("Recommendations to skip segments:")
    if num_high_skip > 0:
        try:
            result = pyDatalog.ask('RecommendToSkip(V, S)')
            if result is not None:
                for v, s in result.answers:
                    seg_id = (v, s)
                    total = len(segment_views.get(seg_id, set()))
                    skipped = len(segment_skips.get(seg_id, set()))
                    skip_rate = skipped / total if total > 0 else 0
                    print(f"Video: {v}, Segment: {s}, Skip Rate: {skip_rate:.2f} ({skipped}/{total})")
            else:
                print("No recommendations found.")
        except AttributeError:
            print("No recommendations found (RecommendToSkip predicate not defined).")
    else:
        print("No recommendations found (no HighSkipRate facts asserted).")

    # Example usage after main logic:
    skipped_segments = get_segments_skipped_by_percentage(segment_views, segment_skips, threshold=SKIP_RATE_THRESHOLD)
    print(f"Segments skipped by at least {SKIP_RATE_THRESHOLD*100:.0f}% of users:")
    for v, s, skip_rate, skipped, total in skipped_segments:
        print(f"Video: {v}, Segment: {s}, Skip Rate: {skip_rate:.2f} ({skipped}/{total})")
    
    skipped_by_number = get_segments_skipped_by_number(segment_skips, min_skipped=MIN_SKIPPED)
    print(f"Segments skipped by at least {MIN_SKIPPED} users:")
    for v, s, skipped in skipped_by_number:
        print(f"Video: {v}, Segment: {s}, Skipped by: {skipped} users")

if __name__ == "__main__":
    main()