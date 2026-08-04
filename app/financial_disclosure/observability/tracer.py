"""FD-10 脱敏 Trace：记录事件并剔除敏感字段。"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "private_key",
        "access_key",
        "sensitive",
    }
)
_SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9]{16,}|Bearer\s+[A-Za-z0-9._-]+)")


@dataclass(frozen=True)
class TraceEvent:
    """一条已脱敏的 trace 事件。"""

    stage: str
    event: str
    attributes: tuple[tuple[str, str], ...]


class Tracer:
    """记录 trace；所有属性值在写入前脱敏。"""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    def redact(self, key: str, value: str) -> str:
        if key.lower() in _SENSITIVE_KEYS or _SECRET_PATTERN.search(value):
            return "***"
        return value

    def record(
        self, stage: str, event: str, attributes: tuple[tuple[str, str], ...] = ()
    ) -> None:
        redacted = tuple((key, self.redact(key, value)) for key, value in attributes)
        self._events.append(TraceEvent(stage, event, redacted))

    def trace(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)
