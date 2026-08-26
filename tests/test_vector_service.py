from types import SimpleNamespace

from backend import vector_service


class FakeEmbeddingModel:
    def encode(self, *_args, **_kwargs):
        return SimpleNamespace(tolist=lambda: [0.1, 0.2, 0.3])


class FakeQdrantClient:
    def __init__(self):
        self.arguments = None

    def query_points(self, **arguments):
        self.arguments = arguments
        point = SimpleNamespace(
            score=0.9,
            payload={
                "topic": "Addition",
                "grade": 1,
                "title": "Joining groups",
                "content": "Addition joins quantities.",
            },
        )
        return SimpleNamespace(points=[point])


def test_search_applies_grade_and_relevance_filters(monkeypatch):
    fake_client = FakeQdrantClient()
    monkeypatch.setattr(vector_service, "client", fake_client)
    monkeypatch.setattr(
        vector_service,
        "get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    results = vector_service.search_materials(
        "How do I add?",
        limit=2,
        learner_grade=3,
    )

    arguments = fake_client.arguments
    grade_condition = arguments["query_filter"].must[0]
    assert grade_condition.key == "grade"
    assert grade_condition.range.lte == 3
    assert arguments["score_threshold"] == vector_service.MINIMUM_RELEVANCE_SCORE
    assert results[0]["topic"] == "Addition"
