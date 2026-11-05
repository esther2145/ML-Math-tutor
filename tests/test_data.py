import csv
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"


def read_rows(filename: str) -> list[dict[str, str]]:
    with (DATA_DIRECTORY / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_curriculum_prerequisites_reference_known_topics():
    curriculum = read_rows("curriculum.csv")
    topics = {row["topic"] for row in curriculum}
    prerequisites = {
        row["prerequisite"]
        for row in curriculum
        if row["prerequisite"].strip()
    }

    assert prerequisites <= topics


def test_learning_materials_match_curriculum_topic_and_grade():
    curriculum = {
        row["topic"]: int(row["grade"])
        for row in read_rows("curriculum.csv")
    }

    for material in read_rows("learning_materials.csv"):
        assert material["topic"] in curriculum
        assert int(material["grade"]) == curriculum[material["topic"]]


def test_learning_material_ids_are_unique():
    identifiers = [row["id"] for row in read_rows("learning_materials.csv")]

    assert len(identifiers) == len(set(identifiers))


def test_advanced_graph_relationships_reference_known_nodes():
    nodes = read_rows("graph_nodes.csv")
    relationships = read_rows("graph_relationships.csv")
    node_ids = {node["node_id"] for node in nodes}

    assert len(node_ids) == len(nodes)
    assert all(row["source_id"] in node_ids for row in relationships)
    assert all(row["target_id"] in node_ids for row in relationships)


def test_advanced_graph_contains_every_curriculum_topic():
    curriculum_topics = {
        row["topic"]
        for row in read_rows("curriculum.csv")
    }
    graph_topics = {
        row["name"]
        for row in read_rows("graph_nodes.csv")
        if row["node_type"] == "Topic"
    }

    assert graph_topics == curriculum_topics


def test_starter_materials_are_not_mislabeled_as_national_curriculum():
    for filename in ("curriculum.csv", "learning_materials.csv"):
        rows = read_rows(filename)

        assert rows
        assert all(row["source_status"] == "prototype_unverified" for row in rows)
        assert all(not row["country_code"] for row in rows)


def test_regional_alignment_template_starts_without_unverified_matches():
    assert read_rows("eac_curriculum_alignments.csv") == []
