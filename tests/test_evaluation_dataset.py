import csv
from pathlib import Path

from backend import evaluation_service
from backend.evaluation_service import evaluate_expected_items
from backend.math_service import solve_arithmetic_question

DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "evaluation_cases.csv"
)

REQUIRED_FIELDS = {
    "case_id",
    "category",
    "question",
    "country_code",
    "grade",
    "expected_behavior",
    "expected_answer",
    "evidence_type",
    "evidence_ref",
    "evidence_note",
    "automation_status",
}


def load_evaluation_cases() -> list[dict[str, str]]:
    with DATASET_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert set(reader.fieldnames) >= REQUIRED_FIELDS
        return list(reader)


def test_evaluation_case_ids_are_unique_and_questions_have_provenance():
    cases = load_evaluation_cases()
    identifiers = [case["case_id"] for case in cases]

    assert len(identifiers) == len(set(identifiers))
    assert all(case["question"].strip() for case in cases)
    assert all(case["evidence_note"].strip() for case in cases)


def test_automated_arithmetic_cases_match_deterministic_solver():
    cases = load_evaluation_cases()
    arithmetic_cases = [
        case
        for case in cases
        if case["automation_status"] == "automated_solver"
    ]

    assert arithmetic_cases

    for case in arithmetic_cases:
        calculation = solve_arithmetic_question(case["question"])
        assert calculation is not None, case["case_id"]

        if case["expected_behavior"] == "identify_arithmetic_error":
            assert calculation.error == case["expected_answer"], case["case_id"]
        else:
            assert calculation.error is None, case["case_id"]
            assert calculation.result == case["expected_answer"], case["case_id"]


def test_unimplemented_policy_cases_are_not_counted_as_automated():
    cases = load_evaluation_cases()
    policy_cases = [
        case
        for case in cases
        if case["expected_behavior"] in {"abstain", "clarify"}
    ]
    blocked_curriculum_cases = [
        case
        for case in cases
        if case["automation_status"] == "blocked_pending_source"
    ]

    assert policy_cases
    assert all(case["automation_status"] == "policy_only" for case in policy_cases)
    assert len(blocked_curriculum_cases) == 1
    assert not blocked_curriculum_cases[0]["expected_answer"]


def test_curriculum_case_has_source_reference_and_is_not_automated():
    cases = load_evaluation_cases()
    curriculum_cases = [
        case
        for case in cases
        if case["category"] == "curriculum_source_fact"
    ]

    assert len(curriculum_cases) == 1
    case = curriculum_cases[0]
    assert case["evidence_ref"] == "UG-NCDC-P7-2012"
    assert "PDF page 153" in case["evidence_note"]
    assert "Algebra" in case["expected_answer"]
    assert case["automation_status"] == "manually_verified_source_fact"
    assert case["expected_answer"] == (
        "Sets; Whole Numbers; Operation on Whole Numbers; Patterns and "
        "Sequences; Fractions; Integers; Data Handling; Construction; Time; "
        "Length, Mass and Capacity; Algebra."
    )


def test_manual_fact_evaluation_accepts_reordered_items_and_citations():
    result = evaluate_expected_items(
        "Sets; Whole Numbers; Length, Mass and Capacity.",
        "The topics include Length, Mass and Capacity [M1]. They also include "
        "Sets and Whole Numbers [M1].",
    )

    assert result["status"] == "complete"
    assert result["coverage"] == 1
    assert result["missing_items"] == []


def test_manual_fact_evaluation_reports_missing_items_without_inference():
    result = evaluate_expected_items(
        "Sets; Whole Numbers; Fractions.",
        "The document lists Sets and Fractions.",
    )

    assert result["status"] == "incomplete"
    assert result["matched_items"] == ["Sets", "Fractions"]
    assert result["missing_items"] == ["Whole Numbers"]
    assert result["coverage"] == 2 / 3
    assert "does not detect unsupported extra claims" in result["limitation"]


def test_manual_fact_evaluation_does_not_pass_when_answer_or_gold_is_empty():
    assert evaluate_expected_items("Sets; Fractions.", "")["status"] == "incomplete"
    empty_gold = evaluate_expected_items("", "Sets and Fractions.")
    assert empty_gold["status"] == "incomplete"
    assert empty_gold["coverage"] == 0


def test_live_evaluation_sends_case_scope_and_keeps_citation_status_separate(
    monkeypatch,
):
    request_arguments = {}
    monkeypatch.setattr(
        evaluation_service,
        "load_manual_fact_cases",
        lambda: [
            {
                "case_id": "CURR-UG-P7-001",
                "question": "Which topics are listed?",
                "grade": "7",
                "country_code": "UG",
                "evidence_ref": "UG-NCDC-P7-2012",
                "expected_answer": "Sets; Fractions.",
            }
        ],
    )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "answer": "The topics include Sets and Fractions [M1].",
                "verification": {"reference_status": "passed"},
                "retrieved_materials": [
                    {"source_title": "Primary Seven Curriculum Set One"}
                ],
            }

    def fake_post(url, **arguments):
        request_arguments.update(url=url, **arguments)
        return FakeResponse()

    monkeypatch.setattr(evaluation_service.requests, "post", fake_post)

    results = evaluation_service.evaluate_live_tutor(
        "http://localhost:8000/",
        timeout=30,
    )

    assert request_arguments["url"] == "http://localhost:8000/tutor/ask"
    assert request_arguments["json"] == {
        "question": "Which topics are listed?",
        "learner_grade": 7,
        "country_code": "UG",
    }
    assert results[0]["evaluation"]["status"] == "complete"
    assert results[0]["citation_reference_status"] == "passed"
    assert results[0]["retrieved_source_titles"] == [
        "Primary Seven Curriculum Set One"
    ]
