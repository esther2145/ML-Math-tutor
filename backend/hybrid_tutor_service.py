from typing import Any

from .graph_service import get_topic_details
from .math_service import build_calculation_answer, solve_arithmetic_question
from .ollama_service import generate_response
from .vector_service import search_materials


def build_graph_context(topic: dict[str, Any] | None) -> str:
    """Convert Neo4j topic information into readable prompt context."""

    if topic is None:
        return "No matching graph topic was found."

    prerequisites = topic.get("prerequisites") or []
    next_topics = topic.get("next_topics") or []

    prerequisite_text = (
        ", ".join(prerequisites)
        if prerequisites
        else "None recorded"
    )

    next_topic_text = (
        ", ".join(next_topics)
        if next_topics
        else "None recorded"
    )

    formula = topic.get("formula") or "No formula recorded"

    return f"""
Topic: {topic.get("topic")}
Description: {topic.get("description")}
Curriculum grade: Primary {topic.get("grade")}
Difficulty: {topic.get("difficulty")}
Formula: {formula}
Prerequisites: {prerequisite_text}
Related next topics: {next_topic_text}
""".strip()


def build_vector_context(materials: list[dict[str, Any]]) -> str:
    """Convert Qdrant search results into readable prompt context."""

    if not materials:
        return "No relevant learning materials were found."

    sections = []

    for index, material in enumerate(materials, start=1):
        section = f"""
Material {index}
Title: {material.get("title")}
Topic: {material.get("topic")}
Grade: Primary {material.get("grade")}
Content: {material.get("content")}
Relevance score: {material.get("score")}
""".strip()

        sections.append(section)

    return "\n\n".join(sections)


def answer_math_question(
    question: str,
    learner_grade: int | None = None,
    result_limit: int = 3,
    country_code: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve information from Qdrant and Neo4j,
    then generate a grounded answer using Ollama.
    """

    verified_calculation = solve_arithmetic_question(question)

    if verified_calculation is not None:
        return {
            "question": question,
            "learner_grade": learner_grade or 3,
            "detected_topic": verified_calculation.topic,
            "graph_context": None,
            "retrieved_materials": [],
            "verified_calculation": verified_calculation.to_dict(),
            "answer": build_calculation_answer(verified_calculation),
        }

    materials = search_materials(
        question=question,
        limit=result_limit,
        learner_grade=learner_grade,
        country_code=country_code,
    )

    # Use the highest-ranked Qdrant result to identify the likely topic.
    detected_topic = (
        materials[0].get("topic")
        if materials
        else None
    )

    graph_topic = (
        get_topic_details(detected_topic)
        if detected_topic and country_code is None
        else None
    )

    if learner_grade is not None:
        grade = learner_grade
    elif graph_topic and graph_topic.get("grade"):
        grade = graph_topic["grade"]
    elif materials:
        grade = materials[0].get("grade", 3)
    else:
        grade = 3

    graph_context = build_graph_context(graph_topic)
    vector_context = build_vector_context(materials)

    prompt = f"""
You are a careful and friendly primary-school mathematics tutor.

Answer the learner's question using the supplied curriculum information.

LEARNER QUESTION
{question}

LEARNER LEVEL
Primary {grade}

KNOWLEDGE GRAPH CONTEXT
{graph_context}

RETRIEVED LEARNING MATERIALS
{vector_context}

INSTRUCTIONS
1. Answer the learner's exact question.
2. Use simple language appropriate for Primary {grade}.
3. Explain the idea step by step.
4. Give one clear worked example when appropriate.
5. Use only mathematical facts supported by the supplied context.
6. Do not invent a formula that is not supported by the context.
7. If the context is insufficient, clearly say that more curriculum information is needed.
8. Do not mention databases, embeddings, retrieval, prompts, Neo4j, Qdrant, or Ollama.
9. Keep the response below 220 words.
"""

    answer = generate_response(prompt)

    return {
        "question": question,
        "country_code": country_code,
        "learner_grade": grade,
        "detected_topic": detected_topic,
        "graph_context": graph_topic,
        "retrieved_materials": materials,
        "verified_calculation": None,
        "answer": answer,
    }
