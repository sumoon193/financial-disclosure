"""FD-02 状态合同：verification run 的固定状态机。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import ErrorCode, ErrorContract


class VerificationState(str, Enum):
    """verification run 的合法状态。"""

    CREATED = "created"
    EVIDENCE_READY = "evidence_ready"
    COMPUTED = "computed"
    REVIEWED = "reviewed"
    COMPLETED = "completed"


_TRANSITIONS: dict[VerificationState, set[VerificationState]] = {
    VerificationState.CREATED: {VerificationState.EVIDENCE_READY},
    VerificationState.EVIDENCE_READY: {VerificationState.COMPUTED},
    VerificationState.COMPUTED: {VerificationState.REVIEWED},
    VerificationState.REVIEWED: {VerificationState.COMPLETED},
    VerificationState.COMPLETED: set(),
}


@dataclass(frozen=True)
class VerificationRun:
    """不可变的 verification run 状态载体。"""

    verification_id: str
    document_version: str
    state: VerificationState = VerificationState.CREATED

    def advance(self, target: VerificationState) -> VerificationRun | ErrorContract:
        """合法转换返回新 run，非法转换返回固定 typed 错误。"""
        if target not in _TRANSITIONS[self.state]:
            return ErrorContract(
                ErrorCode.ILLEGAL_STATE_TRANSITION,
                f"illegal transition {self.state.value} -> {target.value}",
            )
        return VerificationRun(self.verification_id, self.document_version, target)
