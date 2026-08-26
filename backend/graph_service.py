from typing import Any

from .database import driver


def get_topic_details(topic_name: str) -> dict[str, Any] | None:
    """
    Retrieve a rich topic record from the curriculum graph.
    """

    query = """
    MATCH (topic:Topic)
    WHERE toLower(topic.name) = toLower($topic_name)

    OPTIONAL MATCH (prerequisite:Topic)
        -[:PREREQUISITE_FOR]->(topic)

    OPTIONAL MATCH (topic)
        -[:PREREQUISITE_FOR]->(next_topic:Topic)

    OPTIONAL MATCH (subtopic:Subtopic)
        -[:SUBTOPIC_OF]->(topic)

    OPTIONAL MATCH (topic)
        -[:HAS_CONCEPT]->(concept:Concept)

    OPTIONAL MATCH (topic)
        -[:HAS_EXAMPLE]->(example:Example)

    OPTIONAL MATCH (topic)
        -[:USES_SKILL]->(skill)

    OPTIONAL MATCH (topic)
        -[:TAUGHT_IN]->(grade:Grade)

    OPTIONAL MATCH (subtopic)
        -[:HAS_FORMULA]->(formula:Formula)

    RETURN
        topic.node_id AS node_id,
        topic.name AS topic,
        topic.description AS description,
        topic.grade AS grade_number,
        topic.difficulty AS difficulty,
        topic.formula AS topic_formula,

        collect(DISTINCT prerequisite.name) AS prerequisites,
        collect(DISTINCT next_topic.name) AS next_topics,

        collect(
            DISTINCT {
                node_id: subtopic.node_id,
                name: subtopic.name,
                description: subtopic.description,
                grade: subtopic.grade,
                difficulty: subtopic.difficulty,
                formula: subtopic.formula
            }
        ) AS subtopics,

        collect(
            DISTINCT {
                node_id: concept.node_id,
                name: concept.name,
                description: concept.description
            }
        ) AS concepts,

        collect(
            DISTINCT {
                node_id: example.node_id,
                name: example.name,
                description: example.description,
                formula: example.formula
            }
        ) AS examples,

        collect(
            DISTINCT {
                node_id: formula.node_id,
                name: formula.name,
                description: formula.description,
                formula: formula.formula
            }
        ) AS formulas,

        collect(DISTINCT skill.name) AS related_skills,
        collect(DISTINCT grade.name) AS curriculum_grades
    """

    with driver.session() as session:
        record = session.run(
            query,
            topic_name=topic_name,
        ).single()

    if record is None or record["topic"] is None:
        return None

    return {
        "node_id": record["node_id"],
        "topic": record["topic"],
        "description": record["description"],
        "grade": record["grade_number"],
        "difficulty": record["difficulty"],
        "formula": record["topic_formula"],
        "prerequisites": clean_string_list(
            record["prerequisites"]
        ),
        "next_topics": clean_string_list(
            record["next_topics"]
        ),
        "subtopics": clean_object_list(
            record["subtopics"]
        ),
        "concepts": clean_object_list(
            record["concepts"]
        ),
        "examples": clean_object_list(
            record["examples"]
        ),
        "formulas": clean_object_list(
            record["formulas"]
        ),
        "related_skills": clean_string_list(
            record["related_skills"]
        ),
        "curriculum_grades": clean_string_list(
            record["curriculum_grades"]
        ),
    }


def get_prerequisite_path(
    topic_name: str,
    maximum_depth: int = 6,
) -> list[str]:
    """
    Find a prerequisite learning path leading to the selected topic.
    """

    query = """
    MATCH (topic:Topic)
    WHERE toLower(topic.name) = toLower($topic_name)

    OPTIONAL MATCH path =
        (prerequisite:Topic)
        -[:PREREQUISITE_FOR*1..6]->
        (topic)

    WITH path
    ORDER BY length(path) DESC
    LIMIT 1

    RETURN
        CASE
            WHEN path IS NULL THEN []
            ELSE [node IN nodes(path) | node.name]
        END AS learning_path
    """

    with driver.session() as session:
        record = session.run(
            query,
            topic_name=topic_name,
        ).single()

    if record is None:
        return []

    path = record["learning_path"] or []

    return [
        item
        for item in path
        if item is not None
    ]


def search_topics(search_text: str, limit: int = 10) -> list[dict]:
    """
    Search the graph for matching topic and subtopic names.
    """

    query = """
    MATCH (node)
    WHERE (
        node:Topic OR
        node:Subtopic
    )
    AND (
        toLower(node.name) CONTAINS toLower($search_text)
        OR toLower(node.description) CONTAINS toLower($search_text)
    )

    RETURN
        node.node_id AS node_id,
        labels(node) AS labels,
        node.name AS name,
        node.description AS description,
        node.grade AS grade,
        node.difficulty AS difficulty

    ORDER BY
        CASE
            WHEN toLower(node.name) = toLower($search_text)
            THEN 0
            ELSE 1
        END,
        node.name

    LIMIT $limit
    """

    with driver.session() as session:
        records = session.run(
            query,
            search_text=search_text,
            limit=limit,
        )

        return [
            {
                "node_id": record["node_id"],
                "node_type": get_specific_label(
                    record["labels"]
                ),
                "name": record["name"],
                "description": record["description"],
                "grade": record["grade"],
                "difficulty": record["difficulty"],
            }
            for record in records
        ]


def clean_string_list(values: list[Any] | None) -> list[str]:
    if not values:
        return []

    return sorted({
        value
        for value in values
        if value is not None and str(value).strip()
    })


def clean_object_list(values: list[dict] | None) -> list[dict]:
    if not values:
        return []

    cleaned = []

    for value in values:
        if not value:
            continue

        if not value.get("node_id"):
            continue

        cleaned.append({
            key: item
            for key, item in value.items()
            if item is not None
        })

    unique = {
        item["node_id"]: item
        for item in cleaned
    }

    return sorted(
        unique.values(),
        key=lambda item: item.get("name", ""),
    )


def get_specific_label(labels: list[str]) -> str:
    ignored_labels = {"GraphNode"}

    for label in labels:
        if label not in ignored_labels:
            return label

    return "Unknown"
