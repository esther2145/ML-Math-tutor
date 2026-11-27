import csv
from pathlib import Path

from backend import evaluation_service
from backend.evaluation_service import evaluate_expected_items
from backend.hybrid_tutor_service import answer_math_question
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


def test_policy_cases_are_marked_and_checked_automatically():
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
    assert all(case["automation_status"] == "automated_policy" for case in policy_cases)
    assert len(blocked_curriculum_cases) == 1
    assert not blocked_curriculum_cases[0]["expected_answer"]

    for case in policy_cases:
        result = answer_math_question(
            case["question"],
            learner_grade=int(case["grade"]),
            country_code=case["country_code"] or None,
        )
        assert result["verification"]["status"] == "passed", case["case_id"]
        assert (
            result["verification"]["expected_behavior"]
            == case["expected_behavior"]
        )


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


def test_p7_candidate_cases_are_provisional_and_excluded_from_evaluation():
    cases = load_evaluation_cases()
    candidates = [
        case
        for case in cases
        if case["automation_status"] == "pending_independent_review"
    ]
    active_ids = {
        case["case_id"]
        for case in evaluation_service._active_cases()
    }

    assert len(candidates) == 4
    for case in candidates:
        assert case["category"] == "curriculum_source_candidate"
        assert case["evidence_type"] == "document_candidate"
        assert case["evidence_ref"] == "UG-NCDC-P7-2012"
        assert "not independently verified" in case["evidence_note"].casefold()
        assert "PDF page" in case["evidence_note"]
        assert case["expected_answer"]
        assert case["case_id"] not in active_ids


def test_p7_evaluation_fact_has_matching_reviewed_retrieval_material():
    with (
        DATASET_PATH.parent.joinpath("learning_materials.csv").open(
            encoding="utf-8",
            newline="",
        ) as handle
    ):
        materials = list(csv.DictReader(handle))

    p7_materials = [
        material
        for material in materials
        if material["source_status"] == "reviewed"
        and material["country_code"] == "UG"
        and material["grade"] == "7"
        and material["source_page"] == "153"
    ]

    assert len(p7_materials) == 1
    material = p7_materials[0]
    assert material["id"] == "11"
    assert material["source_title"] == "Primary Seven Curriculum Set One (2012)"
    assert "Length, Mass and Capacity" in material["content"]
    assert "do not redistribute" in material["source_license"]


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


def test_paired_evaluation_writes_blinded_pairs_and_narrow_automatic_scores(
    monkeypatch,
    tmp_path,
):
    seen_requests = []
    cases = evaluation_service._active_cases()

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_post(url, json, timeout):
        seen_requests.append((url, json, timeout))
        question = json["question"]
        if url.endswith("/tutor/baseline"):
            return FakeResponse({
                "answer": (
                    "The answer is 4."
                    if "24 / 6" in question
                    else "A direct answer without a policy guarantee."
                )
            })
        calculation = solve_arithmetic_question(question)
        if calculation is not None and calculation.error:
            answer = calculation.error
        elif calculation is not None:
            answer = f"The answer is {calculation.result}."
        elif "What did I eat" in question:
            answer = "I cannot know what you ate because I lack personal context."
        elif "official Uganda Primary 4" in question:
            answer = "I cannot verify without an approved Primary 4 source."
        elif "12 divided by" in question:
            answer = "The divisor is missing; what number should I divide by?"
        elif "How much did I spend" in question:
            answer = "What amount and context should I use?"
        else:
            answer = "Sets; Whole Numbers; Operation on Whole Numbers; Patterns and Sequences; Fractions; Integers; Data Handling; Construction; Time; Length, Mass and Capacity; Algebra."
        return FakeResponse({
            "answer": answer,
            "verification": {
                "status": "passed",
                "check": "arithmetic_result",
                "reference_status": "passed",
            },
            "retrieved_materials": [],
        })

    monkeypatch.setattr(evaluation_service.requests, "post", fake_post)
    monkeypatch.setattr(evaluation_service, "_active_cases", lambda: cases)

    summary = evaluation_service.run_paired_evaluation(
        "http://example.test",
        timeout=20,
        output_dir=tmp_path,
        seed=3,
    )

    assert summary["case_count"] == len(cases)
    assert summary["design"] == "paired single-run pilot"
    assert summary["categories"]["automated_solver"]["graft_mean_score"] == 1
    assert summary["categories"]["automated_policy"]["graft_mean_score"] == 1
    assert summary["categories"]["manually_verified_source_fact"]["graft_mean_score"] == 1
    assert len(seen_requests) == 2 * len(cases)
    for pair in range(0, len(seen_requests), 2):
        assert seen_requests[pair][1] == seen_requests[pair + 1][1]

    required_files = {
        "paired_outputs.csv",
        "blinded_review_sheet.csv",
        "condition_key_private.csv",
        "automatic_summary.json",
        "reviewer_1_template.csv",
        "reviewer_2_template.csv",
    }
    assert required_files == {path.name for path in tmp_path.iterdir()}

    with (tmp_path / "condition_key_private.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        key_rows = list(csv.DictReader(handle))
    with (tmp_path / "blinded_review_sheet.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        review_rows = list(csv.DictReader(handle))
    assert len(key_rows) == len(review_rows) == len(cases)
    assert "baseline" not in review_rows[0]
    assert "graft" not in review_rows[0]
    assert {
        key_rows[0]["condition_A"],
        key_rows[0]["condition_B"],
    } == {"baseline", "graft"}
