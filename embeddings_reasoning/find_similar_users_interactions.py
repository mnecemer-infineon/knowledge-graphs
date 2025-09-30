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
            session.run("CALL gds.graph.drop('userInteractionsGraph', false)")
        except Exception:
            pass
        print("Projecting user interactions graph...")
        session.run("""
        CALL gds.graph.project(
          'userInteractionsGraph',
          {
            User: {}
          },
          {
            ENROLLED_IN: {
              type: 'ENROLLED_IN',
              orientation: 'UNDIRECTED'                    
            },       
            WATCHED: {
              type: 'WATCHED',
              orientation: 'UNDIRECTED'
            },
            PART_OF: {
              type: 'PART_OF',
              orientation: 'UNDIRECTED'
            }
          }
        )
        """)
        print("Running Node2Vec for User interactions...")
        session.run("""
        CALL gds.node2vec.write(
          'userInteractionsGraph',
          {
            writeProperty: 'node2vecEmbedding'
          }
        )
        """)
        # Drop and re-project the graph with the embedding property loaded
        session.run("CALL gds.graph.drop('userInteractionsGraph', false)")
        print("Re-projecting user interactions graph with embedding property...")
        session.run("""
        CALL gds.graph.project(
          'userInteractionsGraph',
          {
            User: {
              properties: ['node2vecEmbedding']
            }
          },
          {
            WATCHED: {
              type: 'WATCHED',
              orientation: 'UNDIRECTED'
            },
            PART_OF: {
              type: 'PART_OF',
              orientation: 'UNDIRECTED'
            }
          }
        )
        """)
        print("Finding top 5 similar Users using KNN...")
        result = session.run("""
        CALL gds.knn.stream(
          'userInteractionsGraph',
          {
            topK: 5,
            nodeProperties: ['node2vecEmbedding']
          }
        )
        YIELD node1, node2, similarity
        RETURN gds.util.asNode(node1).id AS user1, gds.util.asNode(node2).id AS user2, similarity
        ORDER BY similarity DESC
        """)
        records = list(result)
        printed_pairs = set()
        for record in records:
            u1 = record['user1']
            u2 = record['user2']
            pair = tuple(sorted([u1, u2]))
            if pair not in printed_pairs:
                print(f"User {u1} is similar to User {u2} (similarity: {record['similarity']:.3f})")
                printed_pairs.add(pair)
        print("Dropping user interactions graph...")
        session.run("CALL gds.graph.drop('userInteractionsGraph')")

if __name__ == "__main__":
    run_node2vec_and_knn()
