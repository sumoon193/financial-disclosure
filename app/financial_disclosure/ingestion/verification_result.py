"""FD-03 合同入口：VerificationResult.execute 的幂等摄取。"""

from __future__ import annotations

import hashlib

from ..contracts.errors import ErrorContract
from .errors import IngestionError
from .types import DocumentVersion, FD03Input, FD03Result

SUPPORTED_FORMATS = frozenset({"sec", "xbrl", "html"})


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _document_version_id(filing_id: str, version: str) -> str:
    raw = f"{filing_id}|{version}".encode("utf-8")
    return "doc-" + hashlib.sha256(raw).hexdigest()[:16]


def _error_result(input: FD03Input, code: str, message: str) -> FD03Result:
    return FD03Result(
        filing_id=input.filing_id,
        document_version_id=None,
        duplicate=False,
        amended=input.amendment_of is not None,
        error=ErrorContract(code, message),
    )


class VerificationResult:
    """对 SEC/XBRL/HTML 文档实施幂等摄取的合同入口。"""

    def __init__(self) -> None:
        self._versions: dict[tuple[str, str], DocumentVersion] = {}
        self._filing_ids: set[str] = set()

    def execute(self, input: FD03Input) -> FD03Result:
        if (
            not input.filing_id
            or not input.form
            or not input.format
            or not input.version
        ):
            return _error_result(
                input,
                IngestionError.INVALID_INPUT,
                "filing_id/form/format/version must not be empty",
            )
        if input.format not in SUPPORTED_FORMATS:
            return _error_result(
                input,
                IngestionError.UNSUPPORTED_FORMAT,
                f"unsupported format: {input.format}",
            )
        key = (input.filing_id, input.version)
        existing = self._versions.get(key)
        if existing is not None:
            if existing.content_hash == _content_hash(input.content):
                return FD03Result(
                    filing_id=input.filing_id,
                    document_version_id=existing.document_version_id,
                    duplicate=True,
                    amended=existing.amendment_of is not None,
                )
            return FD03Result(
                filing_id=input.filing_id,
                document_version_id=existing.document_version_id,
                duplicate=False,
                amended=existing.amendment_of is not None,
                error=ErrorContract(
                    IngestionError.VERSION_CONFLICT,
                    f"version already ingested with different content: {key}",
                ),
            )
        if input.amendment_of is not None and input.amendment_of not in self._filing_ids:
            return _error_result(
                input,
                IngestionError.UNKNOWN_BASE_FILING,
                f"amendment references unknown base filing: {input.amendment_of}",
            )
        document = DocumentVersion(
            document_version_id=_document_version_id(
                input.filing_id, input.version
            ),
            filing_id=input.filing_id,
            form=input.form,
            format=input.format,
            version=input.version,
            amendment_of=input.amendment_of,
            content_hash=_content_hash(input.content),
        )
        self._versions[key] = document
        self._filing_ids.add(input.filing_id)
        return FD03Result(
            filing_id=input.filing_id,
            document_version_id=document.document_version_id,
            duplicate=False,
            amended=input.amendment_of is not None,
        )
