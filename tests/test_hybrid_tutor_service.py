from backend import hybrid_tutor_service


def test_answer_uses_detected_topic_and_requested_grade(monkeypatch):
    search_arguments = {}
    materials = [
        {
            "score": 0.91,
            "topic": "Addition",
            "grade": 1,
            "title": "Joining groups",
            "content": "Addition joins quantities.",
        }
    ]
    topic = {
        "topic": "Addition",
        "description": "Combining quantities.",
        "grade": 1,
        "difficulty": "beginner",
        "formula": "a + b = c",
        "prerequisites": ["Counting"],
        "next_topics": ["Subtraction"],
    }
    def fake_search(**arguments):
        search_arguments.update(arguments)
        return materials

    monkeypatch.setattr(hybrid_tutor_service, "search_materials", fake_search)
    monkeypatch.setattr(
        hybrid_tutor_service,
        "get_topic_details",
        lambda _: topic,
    )
    monkeypatch.setattr(
        hybrid_tutor_service,
        "generate_response",
        lambda _: "A grounded answer.",
    )

    result = hybrid_tutor_service.answer_math_question(
        "How do I add?",
        learner_grade=2,
    )

    assert result["detected_topic"] == "Addition"
    assert result["learner_grade"] == 2
    assert result["answer"] == "A grounded answer."
    assert search_arguments["learner_grade"] == 2


def test_explicit_arithmetic_bypasses_external_services(monkeypatch):
    def fail_if_called(**_):
        raise AssertionError("Retrieval should not run for explicit arithmetic")

    monkeypatch.setattr(hybrid_tutor_service, "search_materials", fail_if_called)
    monkeypatch.setattr(hybrid_tutor_service, "generate_response", fail_if_called)

    result = hybrid_tutor_service.answer_math_question(
        "What is 12 / 3?",
        learner_grade=2,
    )

    assert result["verified_calculation"]["result"] == "4"
    assert result["detected_topic"] == "Division"
    assert "12 ÷ 3 = 4" in result["answer"]
