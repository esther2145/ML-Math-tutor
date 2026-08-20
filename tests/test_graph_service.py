from backend import graph_service


class FakeResult:
    def __init__(self, record):
        self.record = record

    def single(self):
        return self.record


class FakeSession:
    def __init__(self, record, query_log):
        self.record = record
        self.query_log = query_log

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def run(self, query, **parameters):
        self.query_log.append((query, parameters))
        return FakeResult(self.record)


class FakeDriver:
    def __init__(self, record):
        self.record = record
        self.query_log = []

    def session(self):
        return FakeSession(self.record, self.query_log)


def test_topic_query_uses_loader_compatible_topic_label(monkeypatch):
    record = {
        "node_id": None,
        "topic": "Addition",
        "description": "Combining quantities.",
        "grade_number": 1,
        "difficulty": "beginner",
        "topic_formula": "a + b = c",
        "prerequisites": ["Counting"],
        "next_topics": ["Subtraction"],
        "subtopics": [],
        "concepts": [],
        "examples": [],
        "formulas": [],
        "related_skills": [],
        "curriculum_grades": [],
    }
    fake_driver = FakeDriver(record)
    monkeypatch.setattr(graph_service, "driver", fake_driver)

    result = graph_service.get_topic_details("addition")

    query, parameters = fake_driver.query_log[0]
    assert "MATCH (topic:Topic)" in query
    assert "GraphNode:Topic" not in query
    assert parameters == {"topic_name": "addition"}
    assert result["topic"] == "Addition"
    assert result["prerequisites"] == ["Counting"]
