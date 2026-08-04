"""FD-03 摄取的 typed 输入、输出与文档版本载体。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.errors import ErrorContract


@dataclass(frozen=True)
class FD03Input:
    """一次摄取的 typed 输入。

    amendment 与 base 共享 filing_id，以 amendment_of 指回基础 filing，
    并以不同 version 区分，从而不混淆身份。
    """

    filing_id: str
    form: str
    format: str
    content: str
    version: str
    amendment_of: str | None = None


@dataclass(frozen=True)
class FD03Result:
    """摄取的固定 typed 输出。"""

    filing_id: str
    document_version_id: str | None
    duplicate: bool
    amended: bool
    error: ErrorContract | None = None


@dataclass(frozen=True)
class DocumentVersion:
    """已摄取文档的不可变版本记录。"""

    document_version_id: str
    filing_id: str
    form: str
    format: str
    version: str
    amendment_of: str | None
    content_hash: str
