"""FD-11 冻结评测、检索消融与真实模型试验的测试。

RED 先观察失败：数值、citation 和检索收益必须由冻结集验证。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.eval import (  # noqa: E402
    CitationAnchor,
    EvalCase,
    EvalError,
    FD11Input,
    FD11Result,
    FrozenEvalSet,
    RunResult,
)


def _frozen() -> FrozenEvalSet:
    return FrozenEvalSet(
        cases=(
            EvalCase("c1", "revenue?", "3000000", "doc-1"),
            EvalCase("c2", "eps?", "25", "doc-2"),
        )
    )


def _anchor() -> CitationAnchor:
    return CitationAnchor(_frozen())


def _run(case_id: str, value: str, citation: str, retrieved: bool) -> RunResult:
    return RunResult(case_id, value, citation, retrieved)


def test_perfect_run_scores_1_0():
    result = _anchor().execute(
        FD11Input(
            operation="evaluate",
            results=(
                _run("c1", "3000000", "doc-1", True),
                _run("c2", "25", "doc-2", True),
            ),
        )
    )
    assert isinstance(result, FD11Result)
    assert result.error is None
    assert result.total == 2
    assert result.numerical_accuracy == 1.0
    assert result.citation_accuracy == 1.0
    assert result.retrieval_gain == 1.0


def test_numerical_accuracy_is_partial():
    result = _anchor().execute(
        FD11Input(
            operation="evaluate",
            results=(
                _run("c1", "3000000", "doc-1", True),
                _run("c2", "999", "doc-2", True),
            ),
        )
    )
    assert result.numerical_accuracy == 0.5
    assert result.citation_accuracy == 1.0


def test_citation_accuracy_is_partial():
    result = _anchor().execute(
        FD11Input(
            operation="evaluate",
            results=(
                _run("c1", "3000000", "doc-1", True),
                _run("c2", "25", "wrong-doc", True),
            ),
        )
    )
    assert result.citation_accuracy == 0.5


def test_retrieval_gain_requires_retrieval():
    result = _anchor().execute(
        FD11Input(
            operation="evaluate",
            results=(
                _run("c1", "3000000", "doc-1", False),
                _run("c2", "25", "doc-2", False),
            ),
        )
    )
    # 数值与 citation 正确，但未检索（消融）→ 检索收益为 0
    assert result.numerical_accuracy == 1.0
    assert result.citation_accuracy == 1.0
    assert result.retrieval_gain == 0.0


def test_ablation_retrieval_gain_drops():
    cases = (
        _run("c1", "3000000", "doc-1", True),
        _run("c2", "25", "doc-2", True),
    )
    ablated = (
        _run("c1", "3000000", "doc-1", False),
        _run("c2", "25", "doc-2", False),
    )
    full = _anchor().execute(FD11Input(operation="evaluate", results=cases))
    ab = _anchor().execute(FD11Input(operation="evaluate", results=ablated))
    assert full.retrieval_gain == 1.0
    assert ab.retrieval_gain == 0.0
    # 消融只影响检索收益，数值与 citation 收益不变
    assert full.citation_accuracy == ab.citation_accuracy == 1.0


def test_unknown_case_is_rejected():
    result = _anchor().execute(
        FD11Input(
            operation="evaluate",
            results=(
                _run("c1", "3000000", "doc-1", True),
                _run("x9", "25", "doc-2", True),
            ),
        )
    )
    assert result.error is not None
    assert result.error.code == EvalError.UNKNOWN_CASE


def test_incomplete_results_are_rejected():
    result = _anchor().execute(
        FD11Input(operation="evaluate", results=(_run("c1", "3000000", "doc-1", True),))
    )
    assert result.error is not None
    assert result.error.code == EvalError.INCOMPLETE


def test_empty_results_are_rejected():
    result = _anchor().execute(FD11Input(operation="evaluate"))
    assert result.error is not None
    assert result.error.code == EvalError.INCOMPLETE


def test_invalid_operation_is_rejected():
    result = _anchor().execute(FD11Input(operation="train"))
    assert result.error is not None
    assert result.error.code == EvalError.INVALID_OPERATION


def test_frozen_set_is_immutable():
    frozen = _frozen()
    with pytest.raises(FrozenInstanceError):
        frozen.cases = ()  # type: ignore[misc]


def test_result_is_frozen():
    result = _anchor().execute(
        FD11Input(operation="evaluate", results=(_run("c1", "3000000", "doc-1", True), _run("c2", "25", "doc-2", True)))
    )
    with pytest.raises(FrozenInstanceError):
        result.total = 0  # type: ignore[misc]
