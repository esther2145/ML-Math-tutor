from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Connected to Neo4j!' AS message")
        return result.single()["message"]
    
def create_basic_math_graph():
    query = """
    MERGE (addition:Topic {
        name: "Addition",
        description: "Combining two or more numbers to get a total."
    })

    MERGE (multiplication:Topic {
        name: "Multiplication",
        description: "Repeated addition of the same number."
    })

    MERGE (fractions:Topic {
        name: "Fractions",
        description: "Parts of a whole number."
    })

    MERGE (addition)-[:PREREQUISITE_FOR]->(multiplication)
    MERGE (multiplication)-[:PREREQUISITE_FOR]->(fractions)

    RETURN addition, multiplication, fractions
    """

    with driver.session() as session:
        session.run(query)

    return "Basic math graph created successfully"    