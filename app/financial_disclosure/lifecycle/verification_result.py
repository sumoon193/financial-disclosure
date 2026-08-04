"""FD-09 合同入口：VerificationResult.execute 的生命周期操作。"""

from __future__ import annotations

from ..contracts.errors import ErrorContract
from .errors import LifecycleError
from .lifecycle import ObjectLifecycle
from .types import FD09Input, FD09Result


class VerificationResult:
    """active 版本切换可回滚且旧审计事实保留的合同入口。"""

    def __init__(self, lifecycle: ObjectLifecycle | None = None) -> None:
        self._lifecycle = lifecycle or ObjectLifecycle()

    def execute(self, input: FD09Input) -> FD09Result:
        op = input.operation
        if op == "register":
            if not input.object_id or not input.version or not input.content:
                return self._invalid(op, "object_id/version/content required")
            if self._lifecycle.has(input.object_id):
                state = self._lifecycle.get(input.object_id)
                return FD09Result(
                    operation=op, ok=True, object_id=input.object_id,
                    active_version=state.active, versions=state.versions,
                )
            self._lifecycle.register(input.object_id, input.version, input.content)
            return FD09Result(
                operation=op, ok=True, object_id=input.object_id,
                active_version=input.version, versions=(input.version,),
            )
        if op == "add_version":
            if not input.object_id or not input.version or not input.content:
                return self._invalid(op, "object_id/version/content required")
            if not self._lifecycle.has(input.object_id):
                return self._not_found(op, input.object_id)
            self._lifecycle.add_version(input.object_id, input.version, input.content)
            state = self._lifecycle.get(input.object_id)
            return FD09Result(
                operation=op, ok=True, object_id=input.object_id,
                active_version=state.active, versions=state.versions,
            )
        if op == "switch_active":
            if not input.object_id or not input.version:
                return self._invalid(op, "object_id/version required")
            if not self._lifecycle.has(input.object_id):
                return self._not_found(op, input.object_id)
            if input.version not in self._lifecycle.get(input.object_id).versions:
                return self._error(
                    op, input.object_id, LifecycleError.VERSION_NOT_FOUND,
                    f"unknown version: {input.version}",
                )
            self._lifecycle.switch_active(input.object_id, input.version)
            return FD09Result(
                operation=op, ok=True, object_id=input.object_id,
                active_version=input.version,
            )
        if op == "rollback":
            if not input.object_id:
                return self._invalid(op, "object_id required")
            if not self._lifecycle.has(input.object_id):
                return self._not_found(op, input.object_id)
            previous = self._lifecycle.rollback(input.object_id)
            if previous is None:
                return self._error(
                    op, input.object_id, LifecycleError.NOTHING_TO_ROLLBACK,
                    "no previous active version",
                )
            return FD09Result(
                operation=op, ok=True, object_id=input.object_id,
                active_version=previous,
            )
        if op in ("audit_trail", "active_version"):
            if not input.object_id:
                return self._invalid(op, "object_id required")
            if not self._lifecycle.has(input.object_id):
                return self._not_found(op, input.object_id)
            state = self._lifecycle.get(input.object_id)
            return FD09Result(
                operation=op, ok=True, object_id=input.object_id,
                active_version=state.active, versions=state.versions,
                audit_trail=state.history,
            )
        return FD09Result(
            operation=op,
            ok=False,
            error=ErrorContract(
                LifecycleError.INVALID_OPERATION, f"unknown operation: {op}"
            ),
        )

    def _invalid(self, op: str, message: str) -> FD09Result:
        return FD09Result(
            operation=op, ok=False, error=ErrorContract(LifecycleError.INVALID_INPUT, message)
        )

    def _not_found(self, op: str, object_id: str) -> FD09Result:
        return self._error(
            op, object_id, LifecycleError.OBJECT_NOT_FOUND, f"unknown object: {object_id}"
        )

    def _error(self, op: str, object_id: str, code: str, message: str) -> FD09Result:
        return FD09Result(
            operation=op, ok=False, object_id=object_id, error=ErrorContract(code, message)
        )
