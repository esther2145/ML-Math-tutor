
import re
from decimal import Decimal

from .math_service import solve_arithmetic_question


def verify_arithmetic_answer(
    question: str,
    answer: str,
) -> dict[str, str | None]:
    """
    Check whether an answer contains the result produced by
    the existing arithmetic solver.

    This checks the final numerical result only. It does not
    prove that the full explanation or reasoning is correct.
    """

    calculation = solve_arithmetic_question(question)

    if calculation is None:
        return {
            "status": "not_checked",
            "check": "arithmetic_result",
            "reason": (
                "The question could not be solved by the "
                "existing arithmetic solver."
            ),
            "expected_result": None,
        }

    if calculation.error:
        mentions_error = _identifies_arithmetic_error(answer)

        return {
            "status": "passed" if mentions_error else "failed",
            "check": "arithmetic_result",
            "expression": calculation.expression,
            "expected_result": None,
            "reason": (
                "The answer correctly identifies the "
                "arithmetic error."
                if mentions_error
                else "The answer does not clearly identify "
                     "the arithmetic error."
            ),
        }

    expected = calculation.result

    answer_numbers = re.findall(
        r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!\w)",
        answer,
    )
    expected_fraction = bool(
        re.search(r"(?<!\w)-?\d+/\d+(?!\w)", expected)
    )
    matches = (
        re.search(
            rf"(?<![\w.]){re.escape(expected)}(?!\w)",
            answer,
        )
        is not None
        if expected_fraction
        else any(
            Decimal(number.replace(",", "")) == Decimal(expected)
            for number in answer_numbers
        )
    )

    return {
        "status": "passed" if matches else "failed",
        "check": "arithmetic_result",
        "expression": calculation.expression,
        "expected_result": expected,
        "reason": (
            "The expected numerical result appears in "
            "the generated answer."
            if matches
            else "The expected numerical result was not "
                 "found in the generated answer."
        ),
    }


def _identifies_arithmetic_error(answer: str) -> bool:
    error_pattern = re.compile(
        r"\b(?:undefined|division\s+by\s+zero|divided\s+by\s+zero)\b",
        re.IGNORECASE,
    )
    negation_pattern = re.compile(
        r"\b(?:not|isn't|is\s+not|never|without)\s+(?:\w+\s+){0,2}$",
        re.IGNORECASE,
    )

    return any(
        not negation_pattern.search(answer[max(0, match.start() - 32):match.start()])
        for match in error_pattern.finditer(answer)
    )
