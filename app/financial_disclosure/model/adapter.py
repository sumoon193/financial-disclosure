"""FD-05 模型 adapter：只解释已计算事实。"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class ModelUnavailableError(RuntimeError):
    """A real model was requested without credentials or a usable endpoint."""


class ModelProvider(Protocol):
    def interpret(self, question: str, facts: tuple[ComputedFact, ...]) -> str: ...


class RealModelAdapter:
    """OpenAI-compatible text adapter for live verification.

    It receives only computed facts and citations; raw filing text is never sent.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = (api_key or os.getenv("QWEN_API_KEY", "")).strip()
        self._model = model or os.getenv("QWEN_CHAT_MODEL", "")
        self._base_url = (base_url or os.getenv(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )).rstrip("/")
        self._timeout = timeout_seconds
        if not self._api_key or not self._model:
            raise ModelUnavailableError("QWEN_API_KEY and QWEN_CHAT_MODEL are required")

    def interpret(self, question: str, facts: tuple[ComputedFact, ...]) -> str:
        if not facts:
            return ""
        fact_lines = "\n".join(
            f"{fact.fact_id}={fact.value}{fact.unit} citation={fact.citation.document_version_id}"
            for fact in facts
        )
        payload = json.dumps({
            "model": self._model,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": (
                    "Explain the following computed financial facts. Do not invent values.\n"
                    f"Question: {question}\nFacts:\n{fact_lines}"
                ),
            }],
        }).encode("utf-8")
        request = Request(
            f"{self._base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"model request failed: {exc.__class__.__name__}") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("model response format is invalid") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("model response is empty")
        return content.strip()
