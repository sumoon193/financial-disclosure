"""FD-10 安全错误码（错误载体复用 contracts.ErrorContract）。"""


class SecurityError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_INPUT = "security.input.invalid"
    INVALID_OPERATION = "security.operation.invalid"
    PERMISSION_DENIED = "security.permission.denied"
