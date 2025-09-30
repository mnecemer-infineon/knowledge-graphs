from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def run_node2vec_and_knn():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Drop the graph if it already exists
        try:
            session.run("CALL gds.graph.drop('courseGraph', false)")
        except Exception:
            pass
        print("Projecting course graph...")
        session.run("""
        CALL gds.graph.project(
          'courseGraph',
          {
            Course: {}
          },
          {
            PART_OF: {
              type: 'PART_OF',
              orientation: 'UNDIRECTED'
            }
          }
        )
        """)
        print("Running Node2Vec for Course...")
        session.run("""
        CALL gds.node2vec.write(
          'courseGraph',
          {
            writeProperty: 'node2vecEmbedding'
          }
        )
        """)
        # Drop and re-project the graph with the embedding property loaded
        session.run("CALL gds.graph.drop('courseGraph', false)")
        print("Re-projecting course graph with embedding property...")
        session.run("""
        CALL gds.graph.project(
          'courseGraph',
          {
            Course: {
              properties: ['node2vecEmbedding']
            }
          },
          {
            PART_OF: {
              type: 'PART_OF',
              orientation: 'UNDIRECTED'
            }
          }
        )
        """)
        print("Finding top 5 similar Courses using KNN...")
        result = session.run("""
        CALL gds.knn.stream(
          'courseGraph',
          {
            topK: 5,
            nodeProperties: ['node2vecEmbedding']
          }
        )
        YIELD node1, node2, similarity
        RETURN gds.util.asNode(node1).id AS course1, gds.util.asNode(node2).id AS course2, similarity
        ORDER BY similarity DESC
        """)
        for record in result:
            print(f"Course {record['course1']} is similar to Course {record['course2']} (similarity: {record['similarity']:.3f})")
        print("Dropping course graph...")
        session.run("CALL gds.graph.drop('courseGraph')")

if __name__ == "__main__":
    run_node2vec_and_knn()
