from pathlib import Path

import pandas as pd

from .database import driver

DEFAULT_CURRICULUM_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "curriculum.csv"
)


def load_curriculum_to_graph(
    csv_path: str | Path = DEFAULT_CURRICULUM_PATH,
):
    df = pd.read_csv(csv_path)

    query = """
    MERGE (t:Topic {name: $topic})
    SET t.description = $description,
        t.grade = $grade,
        t.difficulty = $difficulty,
        t.formula = $formula

    WITH t
    WHERE $prerequisite IS NOT NULL AND $prerequisite <> ""
    MERGE (p:Topic {name: $prerequisite})
    MERGE (p)-[:PREREQUISITE_FOR]->(t)
    """

    with driver.session() as session:
        for _, row in df.iterrows():
            session.run(
                query,
                topic=row["topic"],
                description=row["description"],
                grade=int(row["grade"]),
                difficulty=row["difficulty"],
                formula="" if pd.isna(row["formula"]) else row["formula"],
                prerequisite="" if pd.isna(row["prerequisite"]) else row["prerequisite"],
            )

    return f"Loaded {len(df)} curriculum topics into Neo4j"
