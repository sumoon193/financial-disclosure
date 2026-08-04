"""FD-10 合同入口：FilingIdentity.execute 的权限隔离 + 脱敏 trace。"""

from __future__ import annotations

from ..contracts.errors import ErrorContract
from ..observability.tracer import Tracer
from .access_control import AccessControl
from .errors import SecurityError
from .types import FD10Input, FD10Result

ALLOWED_OPERATIONS = ("source", "retrieve", "verify", "review")


class FilingIdentity:
    """来源、检索、核验、review 的脱敏 trace 与权限隔离合同入口。"""

    def __init__(
        self,
        access: AccessControl | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self._access = access or AccessControl()
        self._tracer = tracer or Tracer()

    def execute(self, input: FD10Input) -> FD10Result:
        if not input.principal or not input.operation:
            return FD10Result(
                operation=input.operation,
                permitted=False,
                trace=self._tracer.trace(),
                error=ErrorContract(
                    SecurityError.INVALID_INPUT, "principal/operation required"
                ),
            )
        if input.operation not in ALLOWED_OPERATIONS:
            return FD10Result(
                operation=input.operation,
                permitted=False,
                trace=self._tracer.trace(),
                error=ErrorContract(
                    SecurityError.INVALID_OPERATION,
                    f"unknown operation: {input.operation}",
                ),
            )
        permitted = self._access.can(input.principal, input.operation)
        self._tracer.record(
            "permission",
            "checked",
            (
                ("principal", input.principal),
                ("operation", input.operation),
                ("decision", str(permitted).lower()),
            ),
        )
        if not permitted:
            self._tracer.record(
                "permission",
                "denied",
                (("principal", input.principal), ("operation", input.operation)),
            )
            return FD10Result(
                operation=input.operation,
                permitted=False,
                trace=self._tracer.trace(),
                error=ErrorContract(
                    SecurityError.PERMISSION_DENIED,
                    f"permission denied for {input.operation}",
                ),
            )
        attributes = (("operation", input.operation),)
        if input.sensitive_value is not None:
            attributes += (("token", input.sensitive_value),)
        self._tracer.record("operation", input.operation, attributes)
        return FD10Result(
            operation=input.operation,
            permitted=True,
            trace=self._tracer.trace(),
        )
