"""FD-07 PDF/OCR 准入的测试。

RED 先观察失败：只有通过冻结准入指标的 PDF/OCR 路径可启用。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.ocr import (  # noqa: E402
    FD07Input,
    FD07Result,
    FilingIdentity,
    FrozenAdmissionMetrics,
    OCRAdmissionError,
    OCRMetrics,
)


def _frozen(min_accuracy: str = "0.90", min_coverage: str = "0.80") -> FrozenAdmissionMetrics:
    return FrozenAdmissionMetrics(
        min_accuracy=Decimal(min_accuracy), min_coverage=Decimal(min_coverage)
    )


def _identity(**kwargs) -> FilingIdentity:
    return FilingIdentity(_frozen(**kwargs))


def test_path_passing_frozen_metrics_is_enabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    assert isinstance(result, FD07Result)
    assert result.error is None
    assert result.enabled
    assert result.accuracy == Decimal("0.95")
    assert result.coverage == Decimal("0.85")
    assert result.min_accuracy == Decimal("0.90")
    assert result.min_coverage == Decimal("0.80")


def test_path_failing_accuracy_is_disabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.80"), Decimal("0.85")))
    )
    assert not result.enabled
    assert result.error is None


def test_path_failing_coverage_is_disabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.70")))
    )
    assert not result.enabled
    assert result.error is None


def test_boundary_equal_to_threshold_is_enabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.90"), Decimal("0.80")))
    )
    assert result.enabled
    assert result.error is None


def test_empty_path_id_is_rejected():
    result = _identity().execute(
        FD07Input("", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    assert result.error is not None
    assert result.error.code == OCRAdmissionError.INVALID_INPUT


def test_out_of_range_metrics_are_rejected():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("1.5"), Decimal("0.85")))
    )
    assert result.error is not None
    assert result.error.code == OCRAdmissionError.INVALID_METRICS


def test_frozen_metrics_are_immutable():
    frozen = _frozen()
    with pytest.raises(FrozenInstanceError):
        frozen.min_accuracy = Decimal("0.99")  # type: ignore[misc]


def test_result_is_frozen():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    with pytest.raises(FrozenInstanceError):
        result.enabled = False  # type: ignore[misc]
