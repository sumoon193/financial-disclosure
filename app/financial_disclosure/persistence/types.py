"""FD-08 持久化的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class FD08Input:
    """一次持久化操作的 typed 输入。"""

    operation: str
    fact_id: str | None = None
    version: str | None = None
    value: str | None = None
    unit: str | None = None
    cache_key: str | None = None
    cache_result: str | None = None
    lease_id: str | None = None
    owner: str | None = None
    ttl_seconds: float = 0.0
    snapshot: str | None = None


@dataclass(frozen=True)
class FD08Result:
    """持久化操作的固定 typed 输出。"""

    operation: str
    ok: bool
    value: str | None = None
    version: str | None = None
    unit: str | None = None
    cached: bool = False
    lease_active: bool = False
    owner: str | None = None
    error: ErrorContract | None = None
