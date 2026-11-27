import argparse
import csv
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

EVALUATION_DATASET = (
    Path(__file__).resolve().parent.parent / "data" / "evaluation_cases.csv"
)


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def evaluate_expected_items(
    expected_answer: str,
    actual_answer: str,
) -> dict[str, Any]:
    """Measure coverage of a manually checked semicolon-separated fact list."""

    expected_items = [
        item.strip().rstrip(".")
        for item in expected_answer.split(";")
        if item.strip()
    ]
    normalized_answer = f" {_normalize(actual_answer)} "
    matched_items = [
        item
        for item in expected_items
        if f" {_normalize(item)} " in normalized_answer
    ]
    missing_items = [
        item for item in expected_items if item not in matched_items
    ]

    return {
        "status": "complete" if expected_items and not missing_items else "incomplete",
        "metric": "expected_item_coverage",
        "matched_items": matched_items,
        "missing_items": missing_items,
        "expected_item_count": len(expected_items),
        "matched_item_count": len(matched_items),
        "coverage": (
            len(matched_items) / len(expected_items)
            if expected_items
            else 0.0
        ),
        "limitation": (
            "Measures presence of expected items only; it does not detect "
            "unsupported extra claims or prove source support."
        ),
    }


def load_manual_fact_cases() -> list[dict[str, str]]:
    with EVALUATION_DATASET.open(encoding="utf-8", newline="") as handle:
        return [
            case
            for case in csv.DictReader(handle)
            if case["automation_status"] == "manually_verified_source_fact"
        ]


def evaluate_live_tutor(
    api_url: str,
    timeout: float,
    include_baseline: bool = False,
) -> list[dict[str, Any]]:
    results = []
    for case in load_manual_fact_cases():
        response = requests.post(
            f"{api_url.rstrip('/')}/tutor/ask",
            json={
                "question": case["question"],
                "learner_grade": int(case["grade"]),
                "country_code": case["country_code"] or None,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        tutor_result = response.json()
        answer = tutor_result.get("answer")
        if not isinstance(answer, str):
            raise ValueError(
                f"The tutor returned no answer for evaluation case "
                f"{case['case_id']}."
            )

        materials = tutor_result.get("retrieved_materials") or []
        baseline_answer = None
        if include_baseline:
            baseline_response = requests.post(
                f"{api_url.rstrip('/')}/tutor/baseline",
                json={
                    "question": case["question"],
                    "learner_grade": int(case["grade"]),
                },
                timeout=timeout,
            )
            baseline_response.raise_for_status()
            baseline_answer = baseline_response.json().get("answer")
        results.append(
            {
                "case_id": case["case_id"],
                "evidence_ref": case["evidence_ref"],
                "answer": answer,
                "baseline_answer": baseline_answer,
                "evaluation": evaluate_expected_items(
                    case["expected_answer"],
                    answer,
                ),
                "citation_reference_status": (
                    (tutor_result.get("verification") or {}).get(
                        "reference_status"
                    )
                ),
                "retrieved_material_count": len(materials),
                "retrieved_source_titles": [
                    material.get("source_title")
                    for material in materials
                    if material.get("source_title")
                ],
            }
        )
    return results


def _active_cases() -> list[dict[str, str]]:
    with EVALUATION_DATASET.open(encoding="utf-8", newline="") as handle:
        return [
            case
            for case in csv.DictReader(handle)
            if case["automation_status"]
            in {
                "automated_solver",
                "automated_policy",
                "manually_verified_source_fact",
            }
        ]


def _automatic_case_assessment(
    case: dict[str, str],
    answer: str,
) -> dict[str, Any]:
    if case["automation_status"] == "automated_solver":
        from .verification_service import verify_arithmetic_answer

        result = verify_arithmetic_answer(case["question"], answer)
        return {
            "metric": "arithmetic_result_match",
            "status": result["status"],
        }

    if case["automation_status"] == "automated_policy":
        from .verification_service import verify_policy_answer

        result = verify_policy_answer(case["question"], answer)
        return {
            "metric": "response_policy_compliance",
            "status": result["status"],
            "expected_behavior": result["expected_behavior"],
        }

    result = evaluate_expected_items(case["expected_answer"], answer)
    return {
        "metric": "expected_item_coverage",
        "status": result["status"],
        "coverage": result["coverage"],
        "matched_item_count": result["matched_item_count"],
        "expected_item_count": result["expected_item_count"],
        "missing_items": result["missing_items"],
    }


def run_paired_evaluation(
    api_url: str,
    timeout: float,
    output_dir: str | Path,
    seed: int = 2026,
) -> dict[str, Any]:
    """Run baseline and G-RAFT on identical cases and write blinded review files."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    cases = _active_cases()
    rng = random.Random(seed)
    paired_rows = []
    review_rows = []
    key_rows = []
    summary: dict[str, Any] = {
        "design": "paired single-run pilot",
        "random_seed": seed,
        "model_label": os.getenv("OLLAMA_MODEL", "not_recorded"),
        "generation_temperature": 0.2,
        "case_count": len(cases),
        "categories": {},
        "limitations": [
            "Single model response per condition and question.",
            "Automatic checks assess only their named narrow criterion.",
            "Human blinded review is required for factual support and quality.",
            "The small authored dataset is not representative of all learners.",
        ],
    }

    for index, case in enumerate(cases, start=1):
        pair_id = f"P{index:03d}"
        request_body = {
            "question": case["question"],
            "learner_grade": int(case["grade"]),
            "country_code": case["country_code"] or None,
        }
        order = ["baseline", "graft"]
        rng.shuffle(order)
        responses: dict[str, dict[str, Any]] = {}
        for condition in order:
            endpoint = "tutor/baseline" if condition == "baseline" else "tutor/ask"
            response = requests.post(
                f"{api_url.rstrip('/')}/{endpoint}",
                json=request_body,
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload.get("answer")
            if not isinstance(answer, str):
                raise ValueError(
                    f"{condition} returned no answer for case {case['case_id']}."
                )
            responses[condition] = payload

        baseline = responses["baseline"]
        graft = responses["graft"]
        baseline_answer = baseline["answer"]
        graft_answer = graft["answer"]
        baseline_assessment = _automatic_case_assessment(case, baseline_answer)
        graft_assessment = _automatic_case_assessment(case, graft_answer)
        graft_verification = graft.get("verification") or {}
        retrieved = graft.get("retrieved_materials") or []
        paired_rows.append(
            {
                "pair_id": pair_id,
                "case_id": case["case_id"],
                "category": case["category"],
                "grade": case["grade"],
                "question": case["question"],
                "expected_behavior": case["expected_behavior"],
                "expected_answer": case["expected_answer"],
                "evidence_ref": case["evidence_ref"],
                "baseline_answer": baseline_answer,
                "graft_answer": graft_answer,
                "baseline_automatic_assessment": json.dumps(
                    baseline_assessment,
                    ensure_ascii=False,
                ),
                "graft_automatic_assessment": json.dumps(
                    graft_assessment,
                    ensure_ascii=False,
                ),
                "graft_verification_status": graft_verification.get("status"),
                "graft_check_type": graft_verification.get("check"),
                "graft_citation_reference_status": graft_verification.get(
                    "reference_status"
                ),
                "graft_retrieved_material_count": len(retrieved),
                "graft_retrieved_sources": json.dumps(
                    [
                        material.get("source_title") or material.get("title")
                        for material in retrieved
                    ],
                    ensure_ascii=False,
                ),
            }
        )

        condition_for_letter = {"A": "baseline", "B": "graft"}
        if rng.random() < 0.5:
            condition_for_letter = {"A": "graft", "B": "baseline"}
        review_rows.append(
            {
                "pair_id": pair_id,
                "category": case["category"],
                "grade": case["grade"],
                "question": case["question"],
                "expected_behavior": case["expected_behavior"],
                "expected_answer_or_gold_fact": case["expected_answer"],
                "evidence_reference": case["evidence_ref"],
                "evidence_note": case["evidence_note"],
                "response_A": responses[condition_for_letter["A"]]["answer"],
                "response_B": responses[condition_for_letter["B"]]["answer"],
                "A_factuality_0_correct_1_partial_2_wrong_3_unverifiable": "",
                "A_unsupported_claims_yes_no_unclear": "",
                "A_grade_appropriateness_1_to_5": "",
                "A_helpfulness_1_to_5": "",
                "B_factuality_0_correct_1_partial_2_wrong_3_unverifiable": "",
                "B_unsupported_claims_yes_no_unclear": "",
                "B_grade_appropriateness_1_to_5": "",
                "B_helpfulness_1_to_5": "",
                "reviewer_notes": "",
            }
        )
        key_rows.append(
            {
                "pair_id": pair_id,
                "condition_A": condition_for_letter["A"],
                "condition_B": condition_for_letter["B"],
            }
        )
        category = summary["categories"].setdefault(
            case["automation_status"],
            {
                "case_count": 0,
                "baseline_scores": [],
                "graft_scores": [],
            },
        )
        category["case_count"] += 1
        for condition, assessment in (
            ("baseline", baseline_assessment),
            ("graft", graft_assessment),
        ):
            score = (
                assessment.get("coverage")
                if assessment["metric"] == "expected_item_coverage"
                else 1.0 if assessment["status"] == "passed" else 0.0
            )
            category[f"{condition}_scores"].append(score)

    for category in summary["categories"].values():
        for condition in ("baseline", "graft"):
            scores = category.pop(f"{condition}_scores")
            category[f"{condition}_mean_score"] = (
                sum(scores) / len(scores) if scores else None
            )
    summary["interpretation_warning"] = (
        "Do not interpret these automatic scores as an overall hallucination "
        "rate. Report each category separately and use blinded human review."
    )
    summary["created_at_utc"] = datetime.now(timezone.utc).isoformat()

    review_sheet_path = output_path / "blinded_review_sheet.csv"
    _write_csv(output_path / "paired_outputs.csv", paired_rows)
    _write_csv(review_sheet_path, review_rows)
    _write_csv(output_path / "reviewer_1_template.csv", review_rows)
    _write_csv(output_path / "reviewer_2_template.csv", review_rows)
    _write_csv(output_path / "condition_key_private.csv", key_rows)
    (output_path / "automatic_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No evaluation rows to write to {path}.")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the live tutor's coverage of manually checked "
            "curriculum fact items."
        )
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running FastAPI backend.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-question HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="Call /tutor/baseline for direct-model comparison.",
    )
    parser.add_argument(
        "--paired",
        action="store_true",
        help=(
            "Run all eligible cases against baseline and G-RAFT; write paired "
            "outputs, an anonymized review sheet, a private condition key, "
            "and a narrow automatic summary."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="data/evaluation_runs/latest",
        help="Directory for paired evaluation outputs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Seed used to shuffle request order and blind response labels.",
    )
    arguments = parser.parse_args()

    try:
        if arguments.paired:
            results = run_paired_evaluation(
                arguments.api_url,
                arguments.timeout,
                arguments.output_dir,
                seed=arguments.seed,
            )
        else:
            results = evaluate_live_tutor(
                arguments.api_url,
                arguments.timeout,
                include_baseline=arguments.include_baseline,
            )
    except (requests.RequestException, ValueError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
