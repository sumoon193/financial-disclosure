"""FD-11 评测错误码（错误载体复用 contracts.ErrorContract）。"""


class EvalError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_OPERATION = "eval.operation.invalid"
    INCOMPLETE = "eval.results.incomplete"
    UNKNOWN_CASE = "eval.case.unknown"
