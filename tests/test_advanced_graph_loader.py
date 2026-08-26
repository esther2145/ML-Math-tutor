from backend import advanced_graph_loader


class FakeResult:
    def single(self):
        return {"source": "source", "target": "target"}


class FakeSession:
    def __init__(self, query_log):
        self.query_log = query_log

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def run(self, query, **parameters):
        self.query_log.append((query, parameters))
        return FakeResult()


class FakeDriver:
    def __init__(self):
        self.query_log = []

    def session(self):
        return FakeSession(self.query_log)


def test_advanced_nodes_upgrade_matching_topic_nodes(monkeypatch):
    fake_driver = FakeDriver()
    monkeypatch.setattr(advanced_graph_loader, "driver", fake_driver)

    loaded_count = advanced_graph_loader.load_nodes()

    assert loaded_count == 37
    addition_query, addition_parameters = next(
        (query, parameters)
        for query, parameters in fake_driver.query_log
        if parameters.get("node_id") == "topic_addition"
    )
    assert "MERGE (n:Topic" in addition_query
    assert "name: $name" in addition_query
    assert "SET n:GraphNode" in addition_query
    assert addition_parameters["name"] == "Addition"


def test_advanced_relationship_file_loads_all_relationships(monkeypatch):
    fake_driver = FakeDriver()
    monkeypatch.setattr(advanced_graph_loader, "driver", fake_driver)

    loaded_count = advanced_graph_loader.load_relationships()

    assert loaded_count == 39
    relationship_queries = [
        query
        for query, _ in fake_driver.query_log
        if "MERGE (source)-[r:" in query
    ]
    assert len(relationship_queries) == 39
