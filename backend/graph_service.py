from database import driver


def get_topic_details(topic_name: str):
    query = """
    MATCH (t:Topic {name: $topic_name})
    OPTIONAL MATCH (p)-[:PREREQUISITE_FOR]->(t)
    OPTIONAL MATCH (t)-[:PREREQUISITE_FOR]->(next)
    RETURN 
        t.name AS topic,
        t.description AS description,
        t.grade AS grade,
        t.difficulty AS difficulty,
        t.formula AS formula,
        collect(DISTINCT p.name) AS prerequisites,
        collect(DISTINCT next.name) AS next_topics
    """

    with driver.session() as session:
        result = session.run(query, topic_name=topic_name)
        record = result.single()

        if record is None:
            return None

        return {
            "topic": record["topic"],
            "description": record["description"],
            "grade": record["grade"],
            "difficulty": record["difficulty"],
            "formula": record["formula"],
            "prerequisites": record["prerequisites"],
            "next_topics": record["next_topics"],
        }