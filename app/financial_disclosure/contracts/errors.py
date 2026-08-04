"""FD-02 错误合同：稳定错误码与 typed 错误载体。"""

from __future__ import annotations

from dataclasses import dataclass


class ErrorCode:
    """固定错误码，API 层必须原样透出。"""

    INVALID_INPUT = "input.invalid"
    UNKNOWN_VERIFICATION = "verification.not_found"
    ILLEGAL_STATE_TRANSITION = "state.illegal_transition"


@dataclass(frozen=True)
class ErrorContract:
    """typed 错误输出，永不抛裸异常泄漏到 API 边界。"""

    code: str
    message: str
