"""FD-05 三路检索的 typed 输入/输出。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class Citation:
    """版本 citation：每个检索结果必须携带。"""

    filing_id: str
    document_version_id: str
    version: str


@dataclass(frozen=True)
class ComputedFact:
    """已计算事实：模型唯一可解释的输入，必须带 citation。"""

    fact_id: str
    value: str
    unit: str
    citation: Citation


@dataclass(frozen=True)
class FD05Input:
    """一次检索的 typed 输入。"""

    query: str


@dataclass(frozen=True)
class FD05Result:
    """检索的固定 typed 输出。"""

    query: str
    citations: tuple[Citation, ...]
    interpretation: str
    error: ErrorContract | None = None


@dataclass(frozen=True)
class Retrieval:
    """三路检索合并结果：版本化 citations + 可解释的已计算事实。"""

    citations: tuple[Citation, ...]
    facts: tuple[ComputedFact, ...]
