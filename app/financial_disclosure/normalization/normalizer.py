"""FD-04 规范化：raw 数值 -> 保留单位/scale/rounding 的 NumericValue。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

DEFAULT_ROUNDING = "ROUND_HALF_EVEN"


@dataclass(frozen=True)
class NumericValue:
    """规范化后的数值：绝对 Decimal + 单位 + scale + rounding + 血缘。"""

    value: Decimal
    unit: str
    scale: int
    rounding: str
    fact_id: str


class Normalizer:
    """把 raw 字符串数值按 scale 换算为绝对值并保留元数据。

    value = Decimal(raw) * 10**scale。
    """

    def normalize(
        self,
        raw: str,
        unit: str,
        scale: int = 0,
        fact_id: str = "",
    ) -> NumericValue:
        value = Decimal(raw) * (Decimal(10) ** scale)
        return NumericValue(
            value=value,
            unit=unit,
            scale=scale,
            rounding=DEFAULT_ROUNDING,
            fact_id=fact_id,
        )
