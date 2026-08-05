"""FD-04 合同入口：FilingIdentity.execute 的公式血缘计算。"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

from ..contracts.errors import ErrorContract
from ..normalization.normalizer import DEFAULT_ROUNDING, Normalizer, NumericValue
from .errors import FormulaError
from .types import FD04Input, FD04Result


class FilingIdentity:
    """对数值计算实施单位/scale/rounding/血缘保留的合同入口。"""

    def __init__(self, normalizer: Normalizer | None = None) -> None:
        self._normalizer = normalizer or Normalizer()

    def execute(self, input: FD04Input) -> FD04Result:
        if not input.facts:
            return self._error(
                input, FormulaError.NO_FACTS, "no facts provided"
            )
        try:
            values = [
                self._normalizer.normalize(
                    fact.raw_value, fact.unit, fact.scale, fact.fact_id
                )
                for fact in input.facts
            ]
        except (InvalidOperation, ValueError) as exc:
            return self._error(input, FormulaError.INVALID_VALUE, str(exc))
        if input.operation == "sum":
            return self._sum(input, values)
        if input.operation == "divide":
            return self._divide(input, values)
        return self._error(
            input,
            FormulaError.INVALID_OPERATION,
            f"unknown operation: {input.operation}",
        )

    def _quantize(self, value: Decimal, precision: int) -> Decimal:
        quantum = Decimal(1).scaleb(-precision)
        return value.quantize(quantum, rounding=ROUND_HALF_EVEN)

    def _sum(self, input: FD04Input, values: list[NumericValue]) -> FD04Result:
        units = {value.unit for value in values}
        if len(units) != 1:
            return self._error(
                input,
                FormulaError.UNIT_MISMATCH,
                f"unit mismatch: {sorted(units)}",
            )
        total = sum((value.value for value in values), Decimal(0))
        return FD04Result(
            operation=input.operation,
            value=self._quantize(total, input.precision),
            unit=values[0].unit,
            scale=max(value.scale for value in values),
            rounding=DEFAULT_ROUNDING,
            lineage=tuple(value.fact_id for value in values),
        )

    def _divide(self, input: FD04Input, values: list[NumericValue]) -> FD04Result:
        if len(values) != 2:
            return self._error(
                input, FormulaError.INVALID_OPERATION, "divide requires exactly two facts"
            )
        if values[1].value == 0:
            return self._error(
                input, FormulaError.DIVISION_BY_ZERO, "division by zero"
            )
        unit = input.output_unit or f"{values[0].unit}/{values[1].unit}"
        quotient = values[0].value / values[1].value
        return FD04Result(
            operation=input.operation,
            value=self._quantize(quotient, input.precision),
            unit=unit,
            scale=0,
            rounding=DEFAULT_ROUNDING,
            lineage=(values[0].fact_id, values[1].fact_id),
        )

    def _error(self, input: FD04Input, code: str, message: str) -> FD04Result:
        return FD04Result(
            operation=input.operation,
            value=Decimal(0),
            unit="",
            scale=0,
            rounding=DEFAULT_ROUNDING,
            lineage=tuple(fact.fact_id for fact in input.facts),
            error=ErrorContract(code, message),
        )
