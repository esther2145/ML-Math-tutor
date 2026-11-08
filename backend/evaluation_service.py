import argparse
import csv
import json
import re
import sys
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
        results.append(
            {
                "case_id": case["case_id"],
                "evidence_ref": case["evidence_ref"],
                "answer": answer,
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
    arguments = parser.parse_args()

    try:
        results = evaluate_live_tutor(arguments.api_url, arguments.timeout)
    except (requests.RequestException, ValueError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
