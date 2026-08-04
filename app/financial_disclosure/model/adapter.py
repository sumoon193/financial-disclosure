"""FD-05 模型 adapter：只解释已计算事实。"""

from __future__ import annotations

from ..retrieval.types import ComputedFact


class ModelAdapter:
    """只解释已计算事实的模型 adapter（确定性 Fake）。

    只接收已计算事实；没有已计算事实时返回空解释，绝不解释原始文本。
    """

    def interpret(self, question: str, facts: tuple[ComputedFact, ...]) -> str:
        if not facts:
            return ""
        parts = [
            f"{f.fact_id}={f.value}{f.unit}({f.citation.document_version_id})"
            for f in facts
        ]
        return f"{question}: " + "; ".join(parts)
