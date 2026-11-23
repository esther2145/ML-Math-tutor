from typing import Any, Literal

from .ollama_service import generate_response
from .vector_service import search_materials

BloomLevel = Literal[
    "Remember",
    "Understand",
    "Apply",
    "Analyse",
    "Evaluate",
    "Create",
]

BLOOM_DESCRIPTIONS = {
    "Remember": "recall facts, terms, and procedures",
    "Understand": "explain ideas, describe patterns, and interpret examples",
    "Apply": "use a learned method to solve a problem",
    "Analyse": "compare methods, identify relationships, and explain errors",
    "Evaluate": "justify a strategy using clear mathematical criteria",
    "Create": "design and explain an original mathematical solution or model",
}


def generate_lesson_plan(
    *,
    topic: str,
    learner_grade: int,
    duration_minutes: int,
    bloom_level: BloomLevel,
    competency: str,
    assessment_criteria: str,
    country_code: str = "UG",
) -> dict[str, Any]:
    """Generate an editable, teacher-reviewed lesson draft using reviewed materials."""

    materials = search_materials(
        question=f"{topic}. Competency: {competency}",
        limit=3,
        learner_grade=learner_grade,
        country_code=country_code,
    )
    reviewed_materials = [
        material
        for material in materials
        if material.get("source_status") == "reviewed"
    ]
    evidence_context = _build_evidence_context(reviewed_materials)

    if reviewed_materials:
        evidence_note = (
            "Reviewed curriculum material was retrieved. Cite it by its exact "
            "evidence ID in the draft. Do not claim curriculum alignment beyond "
            "what the supplied material states."
        )
        evidence_status = "reviewed_materials_retrieved"
    else:
        evidence_note = (
            "No reviewed curriculum material was retrieved. Make a clearly "
            "generic draft from the teacher's inputs; do not claim official "
            "curriculum alignment or invent curriculum outcomes."
        )
        evidence_status = "no_reviewed_materials"

    prompt = f"""
You are an assistant helping a primary mathematics teacher draft a lesson.
Produce a concise, editable draft for teacher review, not a final authoritative
lesson. Do not claim the learner has mastered the competency.

TEACHER INPUTS
Topic: {topic}
Learner grade: Primary {learner_grade}
Duration: {duration_minutes} minutes
Bloom level: {bloom_level} ({BLOOM_DESCRIPTIONS[bloom_level]})
Target competency: {competency}
Assessment criteria supplied by teacher: {assessment_criteria}
Country curriculum scope: {country_code}

REVIEWED CURRICULUM EVIDENCE
{evidence_context}

EVIDENCE RULE
{evidence_note}

Return a practical lesson draft with these headings:
1. Learning outcome (observable and aligned to the stated competency and Bloom level)
2. Prerequisite knowledge
3. Materials
4. Lesson sequence with timings that add up to {duration_minutes} minutes
5. Learner-centred activity and worked example
6. Formative assessment, including how the teacher can apply the supplied criteria
7. Support and extension
8. Exit question

Use age-appropriate language for Primary {learner_grade}. Keep all claims
within the supplied evidence; if evidence is missing, mark curriculum-specific
details as requiring teacher confirmation. Do not add citations other than the
provided evidence IDs. Keep the draft under 500 words.
"""
    lesson_plan = generate_response(prompt)

    return {
        "topic": topic,
        "learner_grade": learner_grade,
        "duration_minutes": duration_minutes,
        "bloom_level": bloom_level,
        "competency": competency,
        "assessment_criteria": assessment_criteria,
        "country_code": country_code,
        "lesson_plan": lesson_plan,
        "evidence_status": evidence_status,
        "teacher_review_required": True,
        "retrieved_materials": reviewed_materials,
    }


def _build_evidence_context(materials: list[dict[str, Any]]) -> str:
    if not materials:
        return "No reviewed curriculum material was retrieved."

    return "\n\n".join(
        (
            f"Evidence ID: [M{index}]\n"
            f"Source: {material.get('source_title') or material.get('title')}\n"
            f"Grade: Primary {material.get('grade')}\n"
            f"Topic: {material.get('topic')}\n"
            f"Content: {material.get('content')}"
        )
        for index, material in enumerate(materials, start=1)
    )
