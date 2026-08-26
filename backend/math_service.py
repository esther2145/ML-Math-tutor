import ast
import operator
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Callable

MAX_EXPRESSION_LENGTH = 120
MAX_AST_NODES = 31
EXPRESSION_CHUNKS = re.compile(r"[\d().+\-*/×÷xX\s]+")

BINARY_OPERATORS: dict[type[ast.operator], Callable[[Fraction, Fraction], Fraction]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

TOPICS_BY_OPERATOR = {
    ast.Add: "Addition",
    ast.Sub: "Subtraction",
    ast.Mult: "Multiplication",
    ast.Div: "Division",
}


@dataclass(frozen=True)
class VerifiedCalculation:
    expression: str
    result: str | None
    topic: str
    error: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def solve_arithmetic_question(question: str) -> VerifiedCalculation | None:
    """Safely solve a single explicit arithmetic expression in a question."""

    for chunk in EXPRESSION_CHUNKS.findall(question):
        expression = normalize_expression(chunk)

        if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
            continue

        try:
            tree = ast.parse(expression, mode="eval")
            operators = collect_operators(tree)

            if not operators or len(list(ast.walk(tree))) > MAX_AST_NODES:
                continue

            value = evaluate_node(tree.body)
        except (SyntaxError, TypeError, ValueError):
            continue
        except ZeroDivisionError:
            return VerifiedCalculation(
                expression=display_expression(expression),
                result=None,
                topic="Division",
                error="Division by zero is undefined.",
            )

        topic = (
            TOPICS_BY_OPERATOR[next(iter(operators))]
            if len(operators) == 1
            else "Arithmetic"
        )

        return VerifiedCalculation(
            expression=display_expression(expression),
            result=format_fraction(value),
            topic=topic,
        )

    return None


def normalize_expression(chunk: str) -> str:
    expression = chunk.strip(" .")
    expression = expression.replace("×", "*").replace("÷", "/")
    expression = expression.replace("x", "*").replace("X", "*")
    return re.sub(r"\s+", " ", expression).strip()


def collect_operators(tree: ast.AST) -> set[type[ast.operator]]:
    operators = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            operator_type = type(node.op)

            if operator_type not in BINARY_OPERATORS:
                raise ValueError("Unsupported arithmetic operator")

            operators.add(operator_type)
        elif isinstance(node, ast.Call | ast.Name | ast.Attribute | ast.Subscript):
            raise ValueError("Unsupported expression")

    return operators


def evaluate_node(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return Fraction(str(node.value))

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        value = evaluate_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
        operation = BINARY_OPERATORS[type(node.op)]
        return operation(evaluate_node(node.left), evaluate_node(node.right))

    raise ValueError("Unsupported expression")


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)

    remaining_denominator = value.denominator

    for factor in (2, 5):
        while remaining_denominator % factor == 0:
            remaining_denominator //= factor

    if remaining_denominator == 1:
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        return format(decimal_value.normalize(), "f")

    return f"{value.numerator}/{value.denominator}"


def display_expression(expression: str) -> str:
    return expression.replace("*", "×").replace("/", "÷")


def build_calculation_answer(calculation: VerifiedCalculation) -> str:
    if calculation.error:
        return (
            f"We cannot calculate {calculation.expression}. "
            f"{calculation.error} A number cannot be shared into zero groups."
        )

    return (
        "Let's calculate it carefully:\n\n"
        f"{calculation.expression} = {calculation.result}\n\n"
        f"So the answer is **{calculation.result}**."
    )
