"""FD-02 typed API 合同：固定输入与固定 typed 输出。"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ErrorContract
from .state import VerificationState


@dataclass(frozen=True)
class FD02Input:
    """Filing/Verification API 的 typed 输入。"""

    verification_id: str
    document_version: str
    target_state: str | None = None


@dataclass(frozen=True)
class FD02Result:
    """Filing/Verification API 的固定 typed 输出。"""

    verification_id: str
    document_version: str
    state: VerificationState
    error: ErrorContract | None = None
