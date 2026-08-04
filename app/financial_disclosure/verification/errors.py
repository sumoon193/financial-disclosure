"""FD-06 核验错误码（错误载体复用 contracts.ErrorContract）。"""


class VerificationError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_INPUT = "verification.input.invalid"
    INVALID_TOLERANCE = "verification.tolerance.invalid"
