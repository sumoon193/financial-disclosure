"""FD-08 合同入口：CitationAnchor.execute 的持久化操作分发。"""

from __future__ import annotations

from ..contracts.errors import ErrorContract
from .errors import PersistenceError
from .store import PersistenceStore
from .types import FD08Input, FD08Result


class CitationAnchor:
    """持久化、幂等、租约与缓存的合同入口。"""

    def __init__(self, store: PersistenceStore | None = None) -> None:
        self._store = store or PersistenceStore()

    def execute(self, input: FD08Input) -> FD08Result:
        op = input.operation
        if op == "put_fact":
            if not input.fact_id or not input.version or input.value is None:
                return self._invalid(op, "fact_id/version/value required")
            self._store.put_fact(input.fact_id, input.version, input.value, input.unit or "")
            return FD08Result(operation=op, ok=True)
        if op == "get_fact":
            if not input.fact_id:
                return self._invalid(op, "fact_id required")
            got = self._store.get_fact(input.fact_id, input.version)
            if got is None:
                return FD08Result(
                    operation=op,
                    ok=False,
                    error=ErrorContract(PersistenceError.NOT_FOUND, f"fact not found: {input.fact_id}"),
                )
            value, unit, version = got
            return FD08Result(operation=op, ok=True, value=value, unit=unit, version=version)
        if op == "cache_put":
            if not input.cache_key or input.cache_result is None:
                return self._invalid(op, "cache_key/cache_result required")
            self._store.cache_put(input.cache_key, input.cache_result)
            return FD08Result(operation=op, ok=True)
        if op == "cache_get":
            if not input.cache_key:
                return self._invalid(op, "cache_key required")
            cached = self._store.cache_get(input.cache_key)
            if cached is None:
                return FD08Result(operation=op, ok=True, cached=False)
            return FD08Result(operation=op, ok=True, value=cached, cached=True)
        if op == "acquire_lease":
            if not input.lease_id or not input.owner or input.ttl_seconds <= 0:
                return self._invalid(op, "lease_id/owner/positive ttl required")
            acquired = self._store.acquire_lease(
                input.lease_id, input.owner, input.ttl_seconds
            )
            if not acquired:
                return FD08Result(
                    operation=op,
                    ok=False,
                    owner=input.owner,
                    error=ErrorContract(
                        PersistenceError.LEASE_HELD, f"lease held: {input.lease_id}"
                    ),
                )
            return FD08Result(operation=op, ok=True, owner=input.owner, lease_active=True)
        if op == "release_lease":
            if not input.lease_id or not input.owner:
                return self._invalid(op, "lease_id/owner required")
            released = self._store.release_lease(input.lease_id, input.owner)
            if not released:
                return FD08Result(
                    operation=op,
                    ok=False,
                    error=ErrorContract(
                        PersistenceError.LEASE_NOT_HELD, f"lease not held: {input.lease_id}"
                    ),
                )
            return FD08Result(operation=op, ok=True)
        if op == "lease_status":
            if not input.lease_id:
                return self._invalid(op, "lease_id required")
            return FD08Result(
                operation=op,
                ok=True,
                lease_active=self._store.lease_active(input.lease_id),
                owner=self._store.lease_owner(input.lease_id),
            )
        if op == "snapshot":
            return FD08Result(operation=op, ok=True, value=self._store.snapshot())
        if op == "restore":
            if input.snapshot is None:
                return self._invalid(op, "snapshot required")
            self._store.restore(input.snapshot)
            return FD08Result(operation=op, ok=True)
        return FD08Result(
            operation=op,
            ok=False,
            error=ErrorContract(
                PersistenceError.INVALID_OPERATION, f"unknown operation: {op}"
            ),
        )

    def _invalid(self, op: str, message: str) -> FD08Result:
        return FD08Result(
            operation=op,
            ok=False,
            error=ErrorContract(PersistenceError.INVALID_INPUT, message),
        )
