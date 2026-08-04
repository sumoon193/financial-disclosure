"""FD-08 持久化错误码（错误载体复用 contracts.ErrorContract）。"""


class PersistenceError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_OPERATION = "persistence.operation.invalid"
    INVALID_INPUT = "persistence.input.invalid"
    NOT_FOUND = "persistence.not_found"
    LEASE_HELD = "persistence.lease.held"
    LEASE_NOT_HELD = "persistence.lease.not_held"
