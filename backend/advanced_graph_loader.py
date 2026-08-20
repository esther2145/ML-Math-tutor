from pathlib import Path

import pandas as pd

from .database import driver

BASE_DIR = Path(__file__).resolve().parent.parent
NODES_FILE = BASE_DIR / "data" / "graph_nodes.csv"
RELATIONSHIPS_FILE = BASE_DIR / "data" / "graph_relationships.csv"


ALLOWED_NODE_TYPES = {
    "Grade",
    "Topic",
    "Subtopic",
    "Concept",
    "Formula",
    "Example",
    "Skill",
    "Question",
    "LearningObjective",
}


ALLOWED_RELATIONSHIPS = {
    "TAUGHT_IN",
    "PREREQUISITE_FOR",
    "SUBTOPIC_OF",
    "HAS_CONCEPT",
    "HAS_FORMULA",
    "HAS_EXAMPLE",
    "USES_SKILL",
    "ASSESSES",
    "NEXT_TOPIC",
    "HAS_OBJECTIVE",
}


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    return value


def create_constraints():
    query = """
    CREATE CONSTRAINT graph_node_id_unique IF NOT EXISTS
    FOR (n:GraphNode)
    REQUIRE n.node_id IS UNIQUE
    """

    with driver.session() as session:
        session.run(query)


def load_nodes() -> int:
    if not NODES_FILE.exists():
        raise FileNotFoundError(
            f"Nodes file not found: {NODES_FILE}"
        )

    dataframe = pd.read_csv(NODES_FILE)

    required_columns = {
        "node_id",
        "node_type",
        "name",
        "description",
        "grade",
        "difficulty",
        "formula",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Missing node columns: {sorted(missing_columns)}"
        )

    create_constraints()

    loaded_count = 0

    with driver.session() as session:
        for row in dataframe.to_dict(orient="records"):
            node_type = clean_value(row["node_type"])

            if node_type not in ALLOWED_NODE_TYPES:
                raise ValueError(
                    f"Unsupported node type: {node_type}"
                )

            query = f"""
            MERGE (n:GraphNode:{node_type} {{
                node_id: $node_id
            }})
            SET n.name = $name,
                n.description = $description,
                n.grade = $grade,
                n.difficulty = $difficulty,
                n.formula = $formula
            """

            grade_value = clean_value(row["grade"])

            session.run(
                query,
                node_id=clean_value(row["node_id"]),
                name=clean_value(row["name"]),
                description=clean_value(row["description"]),
                grade=(
                    int(grade_value)
                    if grade_value is not None
                    else None
                ),
                difficulty=clean_value(row["difficulty"]),
                formula=clean_value(row["formula"]),
            )

            loaded_count += 1

    return loaded_count


def load_relationships() -> int:
    if not RELATIONSHIPS_FILE.exists():
        raise FileNotFoundError(
            f"Relationships file not found: {RELATIONSHIPS_FILE}"
        )

    dataframe = pd.read_csv(RELATIONSHIPS_FILE)

    required_columns = {
        "source_id",
        "relationship",
        "target_id",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Missing relationship columns: "
            f"{sorted(missing_columns)}"
        )

    loaded_count = 0

    with driver.session() as session:
        for row in dataframe.to_dict(orient="records"):
            relationship = clean_value(row["relationship"])

            if relationship not in ALLOWED_RELATIONSHIPS:
                raise ValueError(
                    f"Unsupported relationship: {relationship}"
                )

            query = f"""
            MATCH (source:GraphNode {{
                node_id: $source_id
            }})
            MATCH (target:GraphNode {{
                node_id: $target_id
            }})
            MERGE (source)-[r:{relationship}]->(target)
            RETURN source.node_id AS source,
                   target.node_id AS target
            """

            result = session.run(
                query,
                source_id=clean_value(row["source_id"]),
                target_id=clean_value(row["target_id"]),
            )

            record = result.single()

            if record is None:
                raise ValueError(
                    "Could not create relationship "
                    f"{row['source_id']} -[{relationship}]-> "
                    f"{row['target_id']}. Check that both nodes exist."
                )

            loaded_count += 1

    return loaded_count


def load_complete_graph() -> dict:
    node_count = load_nodes()
    relationship_count = load_relationships()

    return {
        "nodes_loaded": node_count,
        "relationships_loaded": relationship_count,
    }
