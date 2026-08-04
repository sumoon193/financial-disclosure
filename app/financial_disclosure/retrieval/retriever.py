"""FD-05 三路检索：全文 / 已计算事实 / 版本。"""

from __future__ import annotations

from dataclasses import dataclass

from .types import Citation, ComputedFact, Retrieval


@dataclass(frozen=True)
class DocumentRecord:
    """检索语料条目：全文 + 已计算事实 + 版本元数据。"""

    filing_id: str
    document_version_id: str
    version: str
    text: str
    facts: tuple[ComputedFact, ...] = ()


class Retriever:
    """三路检索并合并去重版本化 citation。

    全文/版本命中只产生 citation；已计算事实命中产生 citation 与
    可解释事实（模型唯一输入）。
    """

    def __init__(self, records: tuple[DocumentRecord, ...] = ()) -> None:
        self._records = list(records)

    def retrieve(self, query: str) -> Retrieval:
        normalized = query.strip().lower()
        citations: dict[tuple[str, str], Citation] = {}
        facts: dict[str, ComputedFact] = {}
        for record in self._records:
            matched = False
            if normalized and normalized in record.text.lower():
                matched = True
            if normalized and (
                normalized in record.version.lower()
                or normalized in record.document_version_id.lower()
            ):
                matched = True
            for fact in record.facts:
                if normalized and (
                    normalized in fact.fact_id.lower() or normalized in fact.value
                ):
                    facts[fact.fact_id] = fact
                    matched = True
            if matched:
                citations[(record.filing_id, record.document_version_id)] = Citation(
                    record.filing_id, record.document_version_id, record.version
                )
        ordered_citations = tuple(
            sorted(citations.values(), key=lambda c: (c.filing_id, c.document_version_id))
        )
        ordered_facts = tuple(sorted(facts.values(), key=lambda f: f.fact_id))
        return Retrieval(citations=ordered_citations, facts=ordered_facts)
