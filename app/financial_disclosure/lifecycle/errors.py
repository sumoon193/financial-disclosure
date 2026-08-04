"""FD-09 生命周期错误码（错误载体复用 contracts.ErrorContract）。"""


class LifecycleError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_OPERATION = "lifecycle.operation.invalid"
    INVALID_INPUT = "lifecycle.input.invalid"
    OBJECT_NOT_FOUND = "lifecycle.object.not_found"
    VERSION_NOT_FOUND = "lifecycle.version.not_found"
    NOTHING_TO_ROLLBACK = "lifecycle.rollback.nothing"
