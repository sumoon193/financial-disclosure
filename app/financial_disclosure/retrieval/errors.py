"""FD-05 检索错误码（错误载体复用 contracts.ErrorContract）。"""


class RetrievalError:
    """固定错误码，API 层必须原样透出。"""

    EMPTY_QUERY = "retrieval.query.empty"
