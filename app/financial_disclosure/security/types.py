"""FD-10 安全与权限的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract
from ..observability.tracer import TraceEvent


@dataclass(frozen=True)
class FD10Input:
    """一次权限受控操作的 typed 输入。"""

    principal: str
    operation: str
    sensitive_value: str | None = None


@dataclass(frozen=True)
class FD10Result:
    """操作的固定 typed 输出：权限判定 + 脱敏 trace。"""

    operation: str
    permitted: bool
    trace: tuple[TraceEvent, ...]
    error: ErrorContract | None = None
