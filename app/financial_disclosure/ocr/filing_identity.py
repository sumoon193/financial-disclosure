"""FD-07 合同入口：FilingIdentity.execute 的冻结准入判定。"""

from __future__ import annotations

from decimal import Decimal

from ..contracts.errors import ErrorContract
from .errors import OCRAdmissionError
from .types import FD07Input, FD07Result, FrozenAdmissionMetrics


class FilingIdentity:
    """只有通过冻结准入指标的 PDF/OCR 路径可启用。"""

    def __init__(self, frozen: FrozenAdmissionMetrics) -> None:
        self._frozen = frozen

    def execute(self, input: FD07Input) -> FD07Result:
        if not input.path_id:
            return self._error(
                input, OCRAdmissionError.INVALID_INPUT, "path_id must not be empty"
            )
        accuracy = input.metrics.accuracy
        coverage = input.metrics.coverage
        if not (Decimal(0) <= accuracy <= Decimal(1)) or not (
            Decimal(0) <= coverage <= Decimal(1)
        ):
            return self._error(
                input,
                OCRAdmissionError.INVALID_METRICS,
                "accuracy/coverage must be within [0,1]",
            )
        enabled = (
            accuracy >= self._frozen.min_accuracy
            and coverage >= self._frozen.min_coverage
        )
        return FD07Result(
            path_id=input.path_id,
            enabled=enabled,
            accuracy=accuracy,
            coverage=coverage,
            min_accuracy=self._frozen.min_accuracy,
            min_coverage=self._frozen.min_coverage,
        )

    def _error(self, input: FD07Input, code: str, message: str) -> FD07Result:
        return FD07Result(
            path_id=input.path_id,
            enabled=False,
            accuracy=input.metrics.accuracy,
            coverage=input.metrics.coverage,
            min_accuracy=self._frozen.min_accuracy,
            min_coverage=self._frozen.min_coverage,
            error=ErrorContract(code, message),
        )
