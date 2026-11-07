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
