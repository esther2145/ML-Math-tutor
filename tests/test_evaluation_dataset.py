import csv
from pathlib import Path

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
    assert case["automation_status"] == "manual_source_review"
