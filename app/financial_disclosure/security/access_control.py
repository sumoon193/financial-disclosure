"""FD-10 操作级权限隔离。"""

from __future__ import annotations


class AccessControl:
    """principal -> 允许的操作集合。"""

    def __init__(self) -> None:
        self._permissions: dict[str, set[str]] = {}

    def grant(self, principal: str, operation: str) -> None:
        self._permissions.setdefault(principal, set()).add(operation)

    def can(self, principal: str, operation: str) -> bool:
        return operation in self._permissions.get(principal, set())
