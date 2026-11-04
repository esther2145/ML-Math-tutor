
import numbers
import re

from .math_service import solve_arithmetic_question


def verify_arithmetic_answer(
    question: str,
    answer: str,
) -> dict:
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
        mentions_error = bool(
            re.search(
                r"undefined|division by zero|divided by zero",
                answer,
                re.IGNORECASE,
            )
        )

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

# Find numeric values in the generated answer.
    numbers = re.findall(
        r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])",
        answer
    )

    matches = expected in numbers

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
