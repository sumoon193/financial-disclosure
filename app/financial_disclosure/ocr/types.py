"""FD-07 PDF/OCR 准入的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class FrozenAdmissionMetrics:
    """冻结准入指标：不可变阈值。"""

    min_accuracy: Decimal
    min_coverage: Decimal


@dataclass(frozen=True)
class OCRMetrics:
    """候选 PDF/OCR 路径的实测指标（范围 [0,1]）。"""

    accuracy: Decimal
    coverage: Decimal


@dataclass(frozen=True)
class FD07Input:
    """一次准入判定的 typed 输入。"""

    path_id: str
    metrics: OCRMetrics


@dataclass(frozen=True)
class FD07Result:
    """准入判定的固定 typed 输出。"""

    path_id: str
    enabled: bool
    accuracy: Decimal
    coverage: Decimal
    min_accuracy: Decimal
    min_coverage: Decimal
    error: ErrorContract | None = None
