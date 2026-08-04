"""FD-04 公式血缘的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class Fact:
    """公式输入事实。"""

    fact_id: str
    raw_value: str
    unit: str
    scale: int = 0


@dataclass(frozen=True)
class FD04Input:
    """一次公式计算的 typed 输入。"""

    operation: str
    facts: tuple[Fact, ...]
    output_unit: str | None = None
    precision: int = 2


@dataclass(frozen=True)
class FD04Result:
    """公式计算的固定 typed 输出：保留单位、scale、rounding 与输入血缘。"""

    operation: str
    value: Decimal
    unit: str
    scale: int
    rounding: str
    lineage: tuple[str, ...]
    error: ErrorContract | None = None
