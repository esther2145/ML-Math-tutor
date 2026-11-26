from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)


def test_home_reports_backend_is_running():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Backend is running"}


def test_tutor_ask_rejects_blank_question():
    response = client.post("/tutor/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "The question cannot be empty."


def test_tutor_ask_rejects_grade_outside_primary_range():
    response = client.post(
        "/tutor/ask",
        json={"question": "What is 2 + 2?", "learner_grade": 8},
    )

    assert response.status_code == 400


def test_tutor_ask_returns_service_result(monkeypatch):
    expected = {
        "question": "What is 2 + 2?",
        "learner_grade": 1,
        "verification": {
            "status": "passed",
            "check": "arithmetic_result",
            "expected_result": "4",
        },
        "answer": "Four.",
    }
    monkeypatch.setattr(main, "answer_math_question", lambda **_: expected)

    response = client.post(
        "/tutor/ask",
        json={"question": "What is 2 + 2?", "learner_grade": 1},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_tutor_ask_normalizes_and_passes_country_code(monkeypatch):
    captured = {}

    def fake_answer(**arguments):
        captured.update(arguments)
        return {"answer": "A response."}

    monkeypatch.setattr(main, "answer_math_question", fake_answer)

    response = client.post(
        "/tutor/ask",
        json={"question": "How do I add?", "country_code": " ug "},
    )

    assert response.status_code == 200
    assert captured["country_code"] == "UG"


def test_baseline_endpoint_returns_unverified_direct_answer(monkeypatch):
    monkeypatch.setattr(
        main,
        "generate_baseline_answer",
        lambda **_: {
            "answer": "Direct answer.",
            "baseline": True,
            "verification": {"status": "not_checked"},
        },
    )

    response = client.post(
        "/tutor/baseline",
        json={"question": "What is 24 / 6?", "learner_grade": 3},
    )

    assert response.status_code == 200
    assert response.json()["baseline"] is True


def test_tutor_ask_rejects_invalid_country_code():
    response = client.post(
        "/tutor/ask",
        json={"question": "How do I add?", "country_code": "UGA"},
    )

    assert response.status_code == 400


def test_graph_topic_returns_404_when_topic_is_unknown(monkeypatch):
    monkeypatch.setattr(main, "get_topic_details", lambda _: None)

    response = client.get("/graph/topic/Unknown")

    assert response.status_code == 404


def test_teacher_lesson_plan_endpoint_passes_validated_inputs(monkeypatch):
    captured = {}

    def fake_generate_lesson_plan(**arguments):
        captured.update(arguments)
        return {"lesson_plan": "Draft", "teacher_review_required": True}

    monkeypatch.setattr(main, "generate_lesson_plan", fake_generate_lesson_plan)
    response = client.post(
        "/teacher/lesson-plan",
        json={
            "topic": "Equivalent fractions",
            "learner_grade": 4,
            "duration_minutes": 40,
            "bloom_level": "Apply",
            "competency": "Represent equivalent fractions with diagrams.",
            "assessment_criteria": "Correctly solve four of five examples.",
            "country_code": "ug",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "topic": "Equivalent fractions",
        "learner_grade": 4,
        "duration_minutes": 40,
        "bloom_level": "Apply",
        "competency": "Represent equivalent fractions with diagrams.",
        "assessment_criteria": "Correctly solve four of five examples.",
        "country_code": "UG",
    }


def test_teacher_lesson_plan_rejects_invalid_bloom_level():
    response = client.post(
        "/teacher/lesson-plan",
        json={
            "topic": "Addition",
            "learner_grade": 2,
            "duration_minutes": 30,
            "bloom_level": "MemoriseEverything",
            "competency": "Explain addition with objects.",
            "assessment_criteria": "Answer four practice questions.",
        },
    )

    assert response.status_code == 422


def test_teacher_lesson_plan_rejects_blank_competency():
    response = client.post(
        "/teacher/lesson-plan",
        json={
            "topic": "Addition",
            "learner_grade": 2,
            "duration_minutes": 30,
            "bloom_level": "Understand",
            "competency": "   ",
            "assessment_criteria": "Answer four practice questions.",
        },
    )

    assert response.status_code == 400
