"""FD-06 只读核验链路的测试。

RED 先观察失败：规则核验必须输出 discrepancy、tolerance、provenance 和 citations。
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

from financial_disclosure.retrieval.types import Citation
from financial_disclosure.verification import (
    ComputedFact,
    FD06Input,
    FD06Result,
    VerificationError,
    VerificationResult,
)


def _citation() -> Citation:
    return Citation("A", "doc-1", "v1")


def _fact(
    fact_id: str = "f1",
    value: Decimal = Decimal(100),
    unit: str = "USD",
    provenance: tuple[str, ...] = ("f1", "f2"),
) -> ComputedFact:
    return ComputedFact(
        fact_id=fact_id, value=value, unit=unit, citation=_citation(), provenance=provenance
    )


def test_verification_outputs_all_four_components():
    result = VerificationResult().execute(
        FD06Input(_fact(), Decimal(100), Decimal(1))
    )
    assert isinstance(result, FD06Result)
    assert result.error is None
    assert result.discrepancy == Decimal(0)
    assert result.tolerance == Decimal(1)
    assert result.within_tolerance
    assert result.provenance == ("f1", "f2")
    assert result.citations == (_citation(),)


def test_discrepancy_within_tolerance():
    result = VerificationResult().execute(
        FD06Input(_fact(value=Decimal("100.5")), Decimal(100), Decimal(1))
    )
    assert result.discrepancy == Decimal("0.5")
    assert result.within_tolerance


def test_discrepancy_exceeds_tolerance():
    result = VerificationResult().execute(
        FD06Input(_fact(value=Decimal(105)), Decimal(100), Decimal(1))
    )
    assert not result.within_tolerance
    assert result.discrepancy == Decimal(5)


def test_negative_discrepancy_uses_absolute_tolerance():
    result = VerificationResult().execute(
        FD06Input(_fact(value=Decimal(98)), Decimal(100), Decimal(3))
    )
    assert result.discrepancy == Decimal(-2)
    assert result.within_tolerance


def test_boundary_equal_to_tolerance_is_within():
    result = VerificationResult().execute(
        FD06Input(_fact(value=Decimal(103)), Decimal(100), Decimal(3))
    )
    assert result.discrepancy == Decimal(3)
    assert result.within_tolerance


def test_negative_tolerance_is_rejected():
    result = VerificationResult().execute(
        FD06Input(_fact(), Decimal(100), Decimal(-1))
    )
    assert result.error is not None
    assert result.error.code == VerificationError.INVALID_TOLERANCE


def test_empty_fact_id_is_rejected():
    result = VerificationResult().execute(
        FD06Input(_fact(fact_id=""), Decimal(100), Decimal(1))
    )
    assert result.error is not None
    assert result.error.code == VerificationError.INVALID_INPUT


def test_result_is_frozen():
    result = VerificationResult().execute(
        FD06Input(_fact(), Decimal(100), Decimal(1))
    )
    with pytest.raises(FrozenInstanceError):
        result.discrepancy = Decimal(1)  # type: ignore[misc]
