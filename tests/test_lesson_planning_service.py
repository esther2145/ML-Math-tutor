from backend import lesson_planning_service


def test_lesson_plan_uses_grade_bloom_competency_and_reviewed_materials(
    monkeypatch,
):
    search_arguments = {}
    prompts = []
    materials = [
        {
            "id": 8,
            "grade": 4,
            "topic": "Fractions",
            "title": "Equivalent fractions",
            "content": "Equivalent fractions name the same amount.",
            "source_title": "Reviewed Uganda mathematics resource",
            "source_page": "24",
            "source_status": "reviewed",
        },
        {
            "id": 9,
            "title": "Unreviewed example",
            "content": "Do not include this.",
            "source_status": "prototype_unverified",
        },
    ]

    def fake_search(**arguments):
        search_arguments.update(arguments)
        return materials

    monkeypatch.setattr(lesson_planning_service, "search_materials", fake_search)
    monkeypatch.setattr(
        lesson_planning_service,
        "generate_response",
        lambda prompt: prompts.append(prompt) or "Draft lesson plan.",
    )

    result = lesson_planning_service.generate_lesson_plan(
        topic="Equivalent fractions",
        learner_grade=4,
        duration_minutes=40,
        bloom_level="Apply",
        competency="Represent equivalent fractions with diagrams.",
        assessment_criteria="Correctly solve four of five examples.",
        country_code="UG",
    )

    assert search_arguments["learner_grade"] == 4
    assert search_arguments["country_code"] == "UG"
    assert result["evidence_status"] == "reviewed_materials_retrieved"
    assert result["teacher_review_required"] is True
    assert result["retrieved_materials"] == [materials[0]]
    assert "[M1]" in prompts[0]
    assert "Primary 4" in prompts[0]
    assert "Apply (use a learned method to solve a problem)" in prompts[0]
    assert "Correctly solve four of five examples." in prompts[0]
    assert "Do not include this." not in prompts[0]
    assert "timings that add up to 40 minutes" in prompts[0]


def test_lesson_plan_labels_draft_when_no_reviewed_material_is_found(
    monkeypatch,
):
    prompts = []
    monkeypatch.setattr(
        lesson_planning_service,
        "search_materials",
        lambda **_: [],
    )
    monkeypatch.setattr(
        lesson_planning_service,
        "generate_response",
        lambda prompt: prompts.append(prompt) or "Generic draft.",
    )

    result = lesson_planning_service.generate_lesson_plan(
        topic="Addition",
        learner_grade=2,
        duration_minutes=30,
        bloom_level="Understand",
        competency="Explain how addition combines groups.",
        assessment_criteria="Answer three oral questions correctly.",
    )

    assert result["evidence_status"] == "no_reviewed_materials"
    assert result["retrieved_materials"] == []
    assert result["teacher_review_required"] is True
    assert "do not claim official curriculum alignment" in prompts[0]
