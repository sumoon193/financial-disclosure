"""FD-03 摄取错误码（错误载体复用 contracts.ErrorContract）。"""


class IngestionError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_INPUT = "ingestion.input.invalid"
    UNSUPPORTED_FORMAT = "ingestion.format.unsupported"
    UNKNOWN_BASE_FILING = "ingestion.amendment.unknown_base"
    VERSION_CONFLICT = "ingestion.version.conflict"
