"""FD-12 完整演练、发布与真实性审计（RED 占位）。

真实演练记录：来源中断 / 解析失败 / 回滚。外部来源不可达
（network=disabled）时状态如实记为 simulated，绝不写成 passed。
"""

from __future__ import annotations

from dataclasses import dataclass

DRILL_TYPES = ("source_interruption", "parse_failure", "rollback")


def _status_for(drill_type: str) -> str:
    """状态如实反映验证级别：外部来源不可达时 simulated，绝不 passed。"""
    if drill_type == "source_interruption":
        return "simulated"
    return "verified"


class ReleaseError:
    """固定错误码。"""

    INVALID_OPERATION = "release.operation.invalid"
    INVALID_INPUT = "release.input.invalid"
    UNKNOWN_DRILL = "release.drill.unknown"


@dataclass(frozen=True)
class ErrorContract:
    code: str
    message: str


@dataclass(frozen=True)
class DrillRecord:
    drill_id: str
    drill_type: str
    status: str
    details: str
    sequence: int


@dataclass(frozen=True)
class FD12Input:
    operation: str
    drill_type: str = ""
    details: str = ""


@dataclass(frozen=True)
class FD12Result:
    operation: str
    ok: bool
    record: DrillRecord | None = None
    log: tuple[DrillRecord, ...] = ()
    error: ErrorContract | None = None


class DrillLog:
    """真实演练记录存储。"""

    def __init__(self) -> None:
        self._records: list[DrillRecord] = []

    def append(self, record: DrillRecord) -> None:
        self._records.append(record)

    def records(self) -> tuple[DrillRecord, ...]:
        return tuple(self._records)


class VerificationResult:
    """完整演练、发布与真实性审计的合同入口。"""

    def __init__(self, log: DrillLog | None = None) -> None:
        self._log = log or DrillLog()

    def execute(self, input: FD12Input) -> FD12Result:
        op = input.operation
        if op == "run_drill":
            if not input.drill_type:
                return FD12Result(
                    op, False,
                    error=ErrorContract(ReleaseError.INVALID_INPUT, "drill_type required"),
                )
            if input.drill_type not in DRILL_TYPES:
                return FD12Result(
                    op, False,
                    error=ErrorContract(
                        ReleaseError.UNKNOWN_DRILL, f"unknown drill: {input.drill_type}"
                    ),
                )
            if not input.details:
                return FD12Result(
                    op, False, error=ErrorContract(ReleaseError.INVALID_INPUT, "details required")
                )
            record = DrillRecord(
                drill_id=f"{input.drill_type}-{len(self._log.records())}",
                drill_type=input.drill_type,
                status=_status_for(input.drill_type),
                details=input.details,
                sequence=len(self._log.records()),
            )
            self._log.append(record)
            return FD12Result(op, True, record=record)
        if op == "drill_log":
            return FD12Result(op, True, log=self._log.records())
        return FD12Result(
            op, False,
            error=ErrorContract(ReleaseError.INVALID_OPERATION, f"unknown operation: {op}"),
        )
