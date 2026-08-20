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
