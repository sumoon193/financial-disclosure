"""FD-06 合同入口：VerificationResult.execute 的只读规则核验。"""

from __future__ import annotations

from decimal import Decimal

from ..contracts.errors import ErrorContract
from .errors import VerificationError
from .types import FD06Input, FD06Result


class VerificationResult:
    """对已计算事实实施只读规则核验的合同入口。"""

    def execute(self, input: FD06Input) -> FD06Result:
        if not input.fact.fact_id:
            return FD06Result(
                fact_id=input.fact.fact_id,
                discrepancy=Decimal("0"),
                tolerance=input.tolerance,
                within_tolerance=False,
                provenance=input.fact.provenance,
                citations=(),
                error=ErrorContract(
                    VerificationError.INVALID_INPUT, "fact_id must not be empty"
                ),
            )
        if input.tolerance < 0:
            return FD06Result(
                fact_id=input.fact.fact_id,
                discrepancy=Decimal("0"),
                tolerance=input.tolerance,
                within_tolerance=False,
                provenance=input.fact.provenance,
                citations=(),
                error=ErrorContract(
                    VerificationError.INVALID_TOLERANCE, "tolerance must not be negative"
                ),
            )
        discrepancy = input.fact.value - input.expected_value
        within_tolerance = abs(discrepancy) <= input.tolerance
        return FD06Result(
            fact_id=input.fact.fact_id,
            discrepancy=discrepancy,
            tolerance=input.tolerance,
            within_tolerance=within_tolerance,
            provenance=input.fact.provenance,
            citations=(input.fact.citation,),
        )
