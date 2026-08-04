"""FD-02 合同入口：CitationAnchor.execute -> 固定 typed output。"""

from __future__ import annotations

from .errors import ErrorCode, ErrorContract
from .state import VerificationRun, VerificationState
from .types import FD02Input, FD02Result


class CitationAnchor:
    """Filing/Verification API 的合同入口，输出固定 typed 结果。"""

    def __init__(self, runs: dict[str, VerificationRun] | None = None) -> None:
        self._runs: dict[str, VerificationRun] = dict(runs or {})

    def execute(self, input: FD02Input) -> FD02Result:
        """返回固定 typed output；非法转换/未知/非法输入返回稳定 typed 错误。"""
        if not input.verification_id or not input.document_version:
            return FD02Result(
                verification_id=input.verification_id,
                document_version=input.document_version,
                state=VerificationState.CREATED,
                error=ErrorContract(
                    ErrorCode.INVALID_INPUT,
                    "verification_id/document_version must not be empty",
                ),
            )
        run = self._runs.get(input.verification_id)
        if run is None:
            return FD02Result(
                verification_id=input.verification_id,
                document_version=input.document_version,
                state=VerificationState.CREATED,
                error=ErrorContract(
                    ErrorCode.UNKNOWN_VERIFICATION,
                    f"no such verification: {input.verification_id}",
                ),
            )
        if input.target_state is None:
            return FD02Result(
                run.verification_id, run.document_version, run.state, None
            )
        try:
            target = VerificationState(input.target_state)
        except ValueError:
            return FD02Result(
                verification_id=run.verification_id,
                document_version=run.document_version,
                state=run.state,
                error=ErrorContract(
                    ErrorCode.INVALID_INPUT,
                    f"unknown state: {input.target_state}",
                ),
            )
        next_run = run.advance(target)
        if isinstance(next_run, ErrorContract):
            return FD02Result(
                verification_id=run.verification_id,
                document_version=run.document_version,
                state=run.state,
                error=next_run,
            )
        return FD02Result(
            next_run.verification_id, next_run.document_version, next_run.state, None
        )
