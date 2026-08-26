import pytest

from backend.math_service import solve_arithmetic_question


@pytest.mark.parametrize(
    ("question", "expected_result", "expected_topic"),
    [
        ("What is 2 + 2?", "4", "Addition"),
        ("Calculate (2 + 3) x 4.", "20", "Arithmetic"),
        ("What is 7.5 - 2.25?", "5.25", "Subtraction"),
        ("Please calculate 1 / 3", "1/3", "Division"),
    ],
)
def test_solves_supported_explicit_arithmetic(
    question,
    expected_result,
    expected_topic,
):
    calculation = solve_arithmetic_question(question)

    assert calculation.result == expected_result
    assert calculation.topic == expected_topic
    assert calculation.error is None


def test_rejects_question_without_explicit_arithmetic():
    assert solve_arithmetic_question("Explain what a fraction means.") is None


def test_handles_division_by_zero_without_raising():
    calculation = solve_arithmetic_question("What is 5 / 0?")

    assert calculation.result is None
    assert calculation.error == "Division by zero is undefined."
