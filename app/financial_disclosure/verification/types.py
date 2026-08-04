"""FD-06 只读核验的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..contracts.errors import ErrorContract
from ..retrieval.types import Citation


@dataclass(frozen=True)
class ComputedFact:
    """待核验的已计算事实。"""

    fact_id: str
    value: Decimal
    unit: str
    citation: Citation
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class FD06Input:
    """一次只读核验的 typed 输入。"""

    fact: ComputedFact
    expected_value: Decimal
    tolerance: Decimal


@dataclass(frozen=True)
class FD06Result:
    """核验的固定 typed 输出：discrepancy、tolerance、provenance、citations。"""

    fact_id: str
    discrepancy: Decimal
    tolerance: Decimal
    within_tolerance: bool
    provenance: tuple[str, ...]
    citations: tuple[Citation, ...]
    error: ErrorContract | None = None
