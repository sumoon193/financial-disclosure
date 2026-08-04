"""FD-05 三路检索与模型 adapter 的测试。

RED 先观察失败：检索必须返回版本 citation，且模型只解释已计算事实。
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

from financial_disclosure.retrieval import (  # noqa: E402
    Citation,
    CitationAnchor,
    ComputedFact,
    DocumentRecord,
    FD05Input,
    FD05Result,
    RetrievalError,
    Retriever,
)


def _record(
    filing_id: str = "A",
    document_version_id: str = "doc-1",
    version: str = "v1",
    text: str = "REVENUE TEXT",
    facts: tuple[ComputedFact, ...] = (),
) -> DocumentRecord:
    return DocumentRecord(
        filing_id=filing_id,
        document_version_id=document_version_id,
        version=version,
        text=text,
        facts=facts,
    )


def _fact(fact_id: str = "f1", value: str = "3000000") -> ComputedFact:
    return ComputedFact(
        fact_id=fact_id,
        value=value,
        unit="USD",
        citation=Citation("A", "doc-1", "v1"),
    )


def test_citations_are_versioned():
    retriever = Retriever((_record(),))
    retrieval = retriever.retrieve("REVENUE")
    assert len(retrieval.citations) == 1
    cit = retrieval.citations[0]
    assert cit.filing_id == "A"
    assert cit.document_version_id == "doc-1"
    assert cit.version == "v1"


def test_three_way_retrieval_surfaces_all_paths():
    records = (
        _record("A", "doc-1", "v1", "REVENUE TEXT"),  # 全文命中
        _record("B", "doc-2", "v2", "OTHER", (_fact(fact_id="f1"),)),  # 事实命中
        _record("C", "doc-3", "v3", "X"),  # 版本命中
    )
    retriever = Retriever(records)
    assert {c.document_version_id for c in retriever.retrieve("REVENUE").citations} == {"doc-1"}
    assert {c.document_version_id for c in retriever.retrieve("f1").citations} == {"doc-2"}
    assert {c.document_version_id for c in retriever.retrieve("v3").citations} == {"doc-3"}


def test_multi_path_match_is_deduplicated():
    record = _record("A", "doc-1", "v1", "REVENUE v1", (_fact(),))
    retriever = Retriever((record,))
    retrieval = retriever.retrieve("v1")  # 同时命中全文/版本/事实
    assert len(retrieval.citations) == 1
    assert retrieval.citations[0].document_version_id == "doc-1"


def test_anchor_returns_citations_and_interpretation_of_computed_facts():
    anchor = CitationAnchor(Retriever((_record(facts=(_fact(),)),)))
    result = anchor.execute(FD05Input("f1"))
    assert isinstance(result, FD05Result)
    assert result.error is None
    assert result.citations
    assert result.citations[0].document_version_id == "doc-1"
    assert "3000000" in result.interpretation
    assert "doc-1" in result.interpretation


def test_model_does_not_interpret_raw_full_text():
    anchor = CitationAnchor(Retriever((_record(text="REVENUE SECRET 9000"),)))
    result = anchor.execute(FD05Input("REVENUE"))
    assert result.citations  # 检索命中原始文档
    assert result.interpretation == ""  # 模型拒绝解释原始文本
    assert "9000" not in result.interpretation


def test_model_interpretation_uses_facts_not_raw_text():
    anchor = CitationAnchor(
        Retriever((_record(text="RAW HEADLINE 7777", facts=(_fact(),)),))
    )
    result = anchor.execute(FD05Input("3000000"))
    assert "3000000" in result.interpretation
    assert "7777" not in result.interpretation


def test_empty_query_is_rejected():
    anchor = CitationAnchor(Retriever())
    result = anchor.execute(FD05Input(""))
    assert result.error is not None
    assert result.error.code == RetrievalError.EMPTY_QUERY


def test_result_is_frozen():
    anchor = CitationAnchor(Retriever((_record(facts=(_fact(),)),)))
    result = anchor.execute(FD05Input("f1"))
    with pytest.raises(FrozenInstanceError):
        result.interpretation = "hacked"  # type: ignore[misc]
