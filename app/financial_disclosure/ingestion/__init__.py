"""FD-03 SEC、XBRL 与 HTML 摄取包。"""

from .errors import IngestionError
from .types import FD03Input, FD03Result
from .verification_result import VerificationResult

__all__ = [
    "FD03Input",
    "FD03Result",
    "IngestionError",
    "VerificationResult",
]
