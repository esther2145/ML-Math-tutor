import pytest

from backend.verification_service import verify_arithmetic_answer


@pytest.mark.parametrize(
    ("question", "answer"),
    [
        ("Calculate 24 / 6", "24 / 6 equals 4."),
        ("Calculate 7 * 3", "7 multiplied by 3 equals 21."),
        ("Calculate 1 / 2", "The answer is 0.50."),
        ("Calculate 1000 / 1", "The answer is 1,000."),
        ("Calculate 1 / 3", "The answer is 1/3."),
    ],
)
def test_accepts_correct_answer_formats(question, answer):
    result = verify_arithmetic_answer(question, answer)

    assert result["status"] == "passed"


@pytest.mark.parametrize(
    ("question", "answer"),
    [
        ("Calculate 24 / 6", "24 / 6 equals 5."),
        ("Calculate 1 / 2", "The answer is 0.49."),
        ("Calculate 1 / 3", "The answer is 1/4."),
    ],
)
def test_rejects_incorrect_answers(question, answer):
    result = verify_arithmetic_answer(question, answer)

    assert result["status"] == "failed"


def test_returns_not_checked_for_unsupported_question():
    result = verify_arithmetic_answer(
        "Explain equivalent fractions.",
        "Equivalent fractions have the same value.",
    )

    assert result["status"] == "not_checked"
    assert result["expected_result"] is None


@pytest.mark.parametrize(
    "answer",
    [
        "Division by zero is undefined.",
        "This result is undefined.",
    ],
)
def test_accepts_answer_identifying_division_by_zero(answer):
    result = verify_arithmetic_answer("Calculate 5 / 0", answer)

    assert result["status"] == "passed"


@pytest.mark.parametrize(
    "answer",
    [
        "This is not division by zero; it is valid.",
        "The result is not undefined.",
        "This calculation is valid.",
    ],
)
def test_rejects_answer_that_denies_or_omits_division_error(answer):
    result = verify_arithmetic_answer("Calculate 5 / 0", answer)

    assert result["status"] == "failed"
