"""FD-05 模型 adapter：只解释已计算事实。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 延迟导入避免与 retrieval 包的循环依赖：retrieval.citation_anchor
    # 在顶层导入本模块，本模块仅需 ComputedFact 作类型注解。
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
