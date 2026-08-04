"""FD-04 公式错误码（错误载体复用 contracts.ErrorContract）。"""


class FormulaError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_OPERATION = "formula.operation.invalid"
    INVALID_VALUE = "formula.value.invalid"
    UNIT_MISMATCH = "formula.unit.mismatch"
    DIVISION_BY_ZERO = "formula.division_by_zero"
    NO_FACTS = "formula.facts.empty"
