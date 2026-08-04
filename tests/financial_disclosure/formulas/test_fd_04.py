"""FD-04 规范化与 Decimal 公式血缘的测试。

RED 先观察失败：数值计算必须保留单位、scale、rounding 和输入血缘。
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

from financial_disclosure.formulas import (  # noqa: E402
    FD04Input,
    FD04Result,
    Fact,
    FilingIdentity,
    FormulaError,
)


def test_sum_preserves_unit_scale_rounding_and_lineage():
    result = FilingIdentity().execute(
        FD04Input(
            operation="sum",
            facts=(Fact("f1", "100", "USD", 0), Fact("f2", "200", "USD", 0)),
        )
    )
    assert isinstance(result, FD04Result)
    assert result.error is None
    assert result.value == Decimal("300")
    assert result.unit == "USD"
    assert result.scale == 0
    assert result.rounding == "ROUND_HALF_EVEN"
    assert result.lineage == ("f1", "f2")


def test_sum_applies_scale_to_magnitude():
    result = FilingIdentity().execute(
        FD04Input(
            operation="sum",
            facts=(Fact("f1", "1.5", "USD", 6), Fact("f2", "0.5", "USD", 6)),
        )
    )
    assert result.error is None
    assert result.value == Decimal("2000000")
    assert result.scale == 6


def test_sum_rounds_half_even():
    engine = FilingIdentity()
    low = engine.execute(
        FD04Input(operation="sum", facts=(Fact("f1", "0.125", "USD", 0),), precision=2)
    )
    high = engine.execute(
        FD04Input(operation="sum", facts=(Fact("f2", "0.135", "USD", 0),), precision=2)
    )
    assert low.value == Decimal("0.12")
    assert high.value == Decimal("0.14")


def test_divide_produces_per_share_with_lineage():
    result = FilingIdentity().execute(
        FD04Input(
            operation="divide",
            facts=(Fact("ni", "100", "USD", 0), Fact("sh", "4", "shares", 0)),
            output_unit="USD/shares",
        )
    )
    assert result.error is None
    assert result.value == Decimal("25")
    assert result.unit == "USD/shares"
    assert result.lineage == ("ni", "sh")


def test_unit_mismatch_is_rejected():
    result = FilingIdentity().execute(
        FD04Input(
            operation="sum",
            facts=(Fact("f1", "1", "USD", 0), Fact("f2", "1", "shares", 0)),
        )
    )
    assert result.error is not None
    assert result.error.code == FormulaError.UNIT_MISMATCH


def test_division_by_zero_is_rejected():
    result = FilingIdentity().execute(
        FD04Input(
            operation="divide",
            facts=(Fact("ni", "100", "USD", 0), Fact("sh", "0", "shares", 0)),
        )
    )
    assert result.error is not None
    assert result.error.code == FormulaError.DIVISION_BY_ZERO


def test_invalid_operation_is_rejected():
    result = FilingIdentity().execute(
        FD04Input(operation="subtract", facts=(Fact("f1", "1", "USD", 0),))
    )
    assert result.error is not None
    assert result.error.code == FormulaError.INVALID_OPERATION


def test_invalid_raw_value_is_rejected():
    result = FilingIdentity().execute(
        FD04Input(operation="sum", facts=(Fact("f1", "abc", "USD", 0),))
    )
    assert result.error is not None
    assert result.error.code == FormulaError.INVALID_VALUE


def test_empty_facts_is_rejected():
    result = FilingIdentity().execute(FD04Input(operation="sum", facts=()))
    assert result.error is not None
    assert result.error.code == FormulaError.NO_FACTS


def test_result_is_frozen():
    result = FilingIdentity().execute(
        FD04Input(operation="sum", facts=(Fact("f1", "1", "USD", 0),))
    )
    with pytest.raises(FrozenInstanceError):
        result.value = Decimal("2")  # type: ignore[misc]
