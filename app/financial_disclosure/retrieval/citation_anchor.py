"""FD-05 合同入口：CitationAnchor.execute 的三路检索 + 模型 adapter。"""

from __future__ import annotations

from ..contracts.errors import ErrorContract
from ..model.adapter import ModelAdapter
from .errors import RetrievalError
from .retriever import Retriever
from .types import FD05Input, FD05Result


class CitationAnchor:
    """三路检索与模型 adapter 的合同入口。"""

    def __init__(self, retriever: Retriever, adapter: ModelAdapter | None = None) -> None:
        self._retriever = retriever
        self._adapter = adapter or ModelAdapter()

    def execute(self, input: FD05Input) -> FD05Result:
        if not input.query.strip():
            return FD05Result(
                query=input.query,
                citations=(),
                interpretation="",
                error=ErrorContract(
                    RetrievalError.EMPTY_QUERY, "query must not be empty"
                ),
            )
        retrieval = self._retriever.retrieve(input.query)
        interpretation = self._adapter.interpret(input.query, retrieval.facts)
        return FD05Result(
            query=input.query,
            citations=retrieval.citations,
            interpretation=interpretation,
        )
