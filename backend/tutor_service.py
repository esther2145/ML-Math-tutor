from graph_service import get_topic_details
from ollama_service import generate_response


def explain_topic(topic_name: str, learner_grade: int | None = None):
    """
    Retrieve a topic from Neo4j and ask Ollama to explain it
    using only the retrieved curriculum information.
    """

    topic = get_topic_details(topic_name)

    if topic is None:
        return None

    grade = learner_grade if learner_grade is not None else topic["grade"]

    prerequisites = topic.get("prerequisites", [])
    next_topics = topic.get("next_topics", [])

    prerequisite_text = (
        ", ".join(prerequisites)
        if prerequisites
        else "No prerequisite topic is recorded."
    )

    next_topics_text = (
        ", ".join(next_topics)
        if next_topics
        else "No next topic is recorded."
    )

    formula = topic.get("formula") or "No formula is recorded."

    prompt = f"""
You are a friendly primary-school mathematics tutor.

Explain the topic using only the curriculum information provided below.

CURRICULUM INFORMATION
Topic: {topic["topic"]}
Description: {topic["description"]}
Curriculum grade: Primary {topic["grade"]}
Learner grade: Primary {grade}
Difficulty: {topic["difficulty"]}
Formula: {formula}
Prerequisite topics: {prerequisite_text}
Related next topics: {next_topics_text}

INSTRUCTIONS
1. Use simple language suitable for a Primary {grade} learner.
2. Start with a short definition.
3. Give one simple worked example.
4. Show the calculation step by step.
5. Mention the prerequisite only when it helps the explanation.
6. Do not introduce formulas or facts that contradict the curriculum information.
7. Keep the answer below 180 words.
8. Do not mention Neo4j, databases, prompts, or knowledge graphs.
"""

    answer = generate_response(prompt)

    return {
        "topic": topic["topic"],
        "learner_grade": grade,
        "graph_context": topic,
        "answer": answer,
    }