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
            id=17,
            score=0.9,
            payload={
                "topic": "Addition",
                "grade": 1,
                "title": "Joining groups",
                "content": "Addition joins quantities.",
                "country_code": "UG",
                "source_status": "reviewed",
            },
        )
        return SimpleNamespace(points=[point])


def test_search_applies_grade_country_and_relevance_filters(monkeypatch):
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
        country_code="ug",
    )

    arguments = fake_client.arguments
    grade_condition, country_condition, status_condition = (
        arguments["query_filter"].must
    )
    assert grade_condition.key == "grade"
    assert grade_condition.range.lte == 3
    assert country_condition.key == "country_code"
    assert country_condition.match.value == "UG"
    assert status_condition.key == "source_status"
    assert status_condition.match.value == "reviewed"
    assert arguments["score_threshold"] == vector_service.MINIMUM_RELEVANCE_SCORE
    assert results[0]["topic"] == "Addition"
    assert results[0]["id"] == 17
    assert results[0]["country_code"] == "UG"
    assert results[0]["source_status"] == "reviewed"


def test_search_applies_country_filter_without_grade(monkeypatch):
    fake_client = FakeQdrantClient()
    monkeypatch.setattr(vector_service, "client", fake_client)
    monkeypatch.setattr(
        vector_service,
        "get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    vector_service.search_materials("How do I add?", country_code="KE")

    conditions = fake_client.arguments["query_filter"].must
    assert len(conditions) == 2
    assert conditions[0].key == "country_code"
    assert conditions[0].match.value == "KE"
    assert conditions[1].key == "source_status"
    assert conditions[1].match.value == "reviewed"


def test_load_materials_stores_provenance_fields(tmp_path, monkeypatch):
    class FakeVector:
        def tolist(self):
            return [0.1, 0.2, 0.3]

    class BatchEmbeddingModel:
        def encode(self, texts, **_kwargs):
            return [FakeVector() for _ in texts]

    class RecordingQdrantClient:
        def __init__(self):
            self.points = []

        def upsert(self, **arguments):
            self.points.extend(arguments["points"])

    csv_path = tmp_path / "materials.csv"
    csv_path.write_text(
        "id,topic,grade,title,content,country_code,curriculum_name,"
        "curriculum_version,source_title,source_url,source_page,"
        "source_license,source_status\n"
        "1,Addition,1,Joining groups,Example,ug,Uganda Primary,2025,"
        "Curriculum PDF,https://example.test/curriculum.pdf,12,"
        "Permission granted,reviewed\n",
        encoding="utf-8",
    )
    fake_client = RecordingQdrantClient()
    monkeypatch.setattr(vector_service, "client", fake_client)
    monkeypatch.setattr(vector_service, "create_collection", lambda: "created")
    monkeypatch.setattr(
        vector_service,
        "get_embedding_model",
        lambda: BatchEmbeddingModel(),
    )

    assert vector_service.load_materials(csv_path) == 1

    payload = fake_client.points[0].payload
    assert payload["country_code"] == "UG"
    assert payload["curriculum_name"] == "Uganda Primary"
    assert payload["source_page"] == "12"
    assert payload["source_license"] == "Permission granted"
    assert payload["source_status"] == "reviewed"
