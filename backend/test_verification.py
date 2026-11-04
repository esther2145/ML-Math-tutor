
from backend.verification_service import verify_arithmetic_answer

tests = [
    # Correct answer
    ("Calculate 24 / 6", "24 / 6 equals 4."),

    # Incorrect answer
    ("Calculate 24 / 6", "24 / 6 equals 5."),

    # Correct multiplication answer
    ("Calculate 7 * 3", "7 multiplied by 3 equals 21."),

    # Incorrect multiplication answer
    ("Calculate 7 * 3", "7 multiplied by 3 equals 20."),
]

for question, answer in tests:
    result = verify_arithmetic_answer(question, answer)

    print(f"\nQuestion: {question}")
    print(f"Answer: {answer}")
    print(f"Verification: {result}")
