from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
#NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def run_node2vec_and_knn():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Drop the graph if it already exists
        try:
            session.run("CALL gds.graph.drop('userGraph', false)")
        except Exception:
            pass
        print("Projecting user graph...")
        session.run("""
        CALL gds.graph.project(
          'userGraph',
          {
            User: {
              properties: ['node2vecEmbedding']
            }
          },
          {
            WATCHED: {
              type: 'WATCHED',
              orientation: 'UNDIRECTED'
            }
          }
        )
        """)
        print("Running Node2Vec for User...")
        session.run("""
        CALL gds.node2vec.write(
          'userGraph',
          {
            writeProperty: 'node2vecEmbedding'
          }
        )
        """)
        print("Finding top 5 similar Users using KNN...")
        result = session.run("""
        CALL gds.knn.stream(
          'userGraph',
          {
            topK: 5,
            nodeProperties: ['node2vecEmbedding']
          }
        )
        YIELD node1, node2, similarity
        RETURN gds.util.asNode(node1).id AS user1, gds.util.asNode(node2).id AS user2, similarity
        ORDER BY similarity DESC
        """)
        for record in result:
            print(f"User {record['user1']} is similar to User {record['user2']} (similarity: {record['similarity']:.3f})")
        print("Dropping user graph...")
        session.run("CALL gds.graph.drop('userGraph')")

if __name__ == "__main__":
    run_node2vec_and_knn()
