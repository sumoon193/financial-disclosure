"""FD-09 对象生命周期的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract
from .lifecycle import AuditEntry


@dataclass(frozen=True)
class FD09Input:
    """一次生命周期操作的 typed 输入。"""

    operation: str
    object_id: str = ""
    version: str = ""
    content: str = ""


@dataclass(frozen=True)
class FD09Result:
    """生命周期操作的固定 typed 输出。"""

    operation: str
    ok: bool
    object_id: str | None = None
    active_version: str | None = None
    versions: tuple[str, ...] = ()
    audit_trail: tuple[AuditEntry, ...] = ()
    error: ErrorContract | None = None
