"""FD-09 对象生命周期存储：active 版本切换、回滚与审计保留。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditEntry:
    """一次 active 切换/回滚的审计记录。"""

    version: str
    action: str
    seq: int


@dataclass(frozen=True)
class LifecycleState:
    """对象生命周期状态快照。"""

    versions: tuple[str, ...]
    active: str
    history: tuple[AuditEntry, ...]


class ObjectLifecycle:
    """对象版本、active 切换与审计历史；回滚不丢失旧审计事实。"""

    def __init__(self) -> None:
        self._objects: dict[str, dict] = {}

    def has(self, object_id: str) -> bool:
        return object_id in self._objects

    def register(self, object_id: str, version: str, content: str) -> None:
        self._objects[object_id] = {
            "versions": {version: content},
            "active": version,
            "history": [AuditEntry(version, "activate", 0)],
        }

    def add_version(self, object_id: str, version: str, content: str) -> bool:
        obj = self._objects[object_id]
        if version in obj["versions"]:
            return False
        obj["versions"][version] = content
        return True

    def switch_active(self, object_id: str, version: str) -> None:
        obj = self._objects[object_id]
        obj["active"] = version
        obj["history"].append(
            AuditEntry(version, "activate", len(obj["history"]))
        )

    def rollback(self, object_id: str) -> str | None:
        obj = self._objects[object_id]
        if len(obj["history"]) < 2:
            return None
        previous = obj["history"][-2].version
        obj["active"] = previous
        obj["history"].append(
            AuditEntry(previous, "rollback", len(obj["history"]))
        )
        return previous

    def get(self, object_id: str) -> LifecycleState:
        obj = self._objects[object_id]
        return LifecycleState(
            versions=tuple(sorted(obj["versions"])),
            active=obj["active"],
            history=tuple(obj["history"]),
        )
