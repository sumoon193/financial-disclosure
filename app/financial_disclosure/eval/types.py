"""FD-11 冻结评测的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class EvalCase:
    """冻结评测用例。"""

    case_id: str
    query: str
    expected_value: str
    expected_citation: str


@dataclass(frozen=True)
class FrozenEvalSet:
    """冻结评测集：不可变。"""

    cases: tuple[EvalCase, ...]


@dataclass(frozen=True)
class RunResult:
    """一次运行的结果（含检索消融标记）。"""

    case_id: str
    value: str
    citation: str
    retrieved: bool


@dataclass(frozen=True)
class FD11Input:
    """一次评测的 typed 输入。"""

    operation: str
    results: tuple[RunResult, ...] = ()


@dataclass(frozen=True)
class FD11Result:
    """评测的固定 typed 输出：数值/citation/检索收益。"""

    operation: str
    total: int
    correct_numerical: int
    correct_citation: int
    correct_retrieval: int
    numerical_accuracy: float
    citation_accuracy: float
    retrieval_gain: float
    error: ErrorContract | None = None
