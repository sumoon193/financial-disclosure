"""FD-03 SEC、XBRL 与 HTML 摄取的测试。

RED 先观察失败：重复摄取必须幂等，filing identity 不得混淆 amendment。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.ingestion import (
    FD03Input,
    FD03Result,
    IngestionError,
    VerificationResult,
)


def _input(
    filing_id: str = "cik-0000320193",
    form: str = "10-K",
    format: str = "sec",
    content: str = "CONTENT",
    version: str = "v1",
    amendment_of: str | None = None,
) -> FD03Input:
    return FD03Input(
        filing_id=filing_id,
        form=form,
        format=format,
        content=content,
        version=version,
        amendment_of=amendment_of,
    )


def test_sec_ingestion_creates_document_version():
    result = VerificationResult().execute(_input())
    assert isinstance(result, FD03Result)
    assert result.error is None
    assert not result.duplicate
    assert result.document_version_id


def test_xbrl_and_html_formats_are_supported():
    engine = VerificationResult()
    for fmt in ("xbrl", "html"):
        result = engine.execute(_input(format=fmt))
        assert result.error is None
        assert result.document_version_id


def test_reingest_same_input_is_idempotent():
    engine = VerificationResult()
    first = engine.execute(_input(content="SAME"))
    second = engine.execute(_input(content="SAME"))
    assert first.error is None and second.error is None
    assert second.duplicate
    assert second.document_version_id == first.document_version_id


def test_amendment_is_distinct_version_and_does_not_confuse_identity():
    engine = VerificationResult()
    base = engine.execute(_input(form="10-K", version="2025-10K", content="BASE"))
    amendment = engine.execute(
        _input(
            form="10-K/A",
            version="2025-10K-A",
            content="AMENDED",
            amendment_of="cik-0000320193",
        )
    )
    assert base.error is None and amendment.error is None
    assert amendment.amended
    assert amendment.filing_id == base.filing_id
    assert amendment.document_version_id != base.document_version_id
    # 基础 filing 未被覆盖：重新摄取 base 仍是同一版本（幂等 duplicate）。
    rebase = engine.execute(_input(form="10-K", version="2025-10K", content="BASE"))
    assert rebase.duplicate
    assert rebase.document_version_id == base.document_version_id


def test_amendment_without_existing_base_is_rejected():
    result = VerificationResult().execute(
        _input(form="10-K/A", version="v2", content="X", amendment_of="missing-filing")
    )
    assert result.error is not None
    assert result.error.code == IngestionError.UNKNOWN_BASE_FILING
    assert result.document_version_id is None


def test_version_conflict_is_rejected_and_original_preserved():
    engine = VerificationResult()
    first = engine.execute(_input(content="ORIGINAL"))
    conflict = engine.execute(_input(content="DIFFERENT"))
    assert conflict.error is not None
    assert conflict.error.code == IngestionError.VERSION_CONFLICT
    assert conflict.document_version_id == first.document_version_id


def test_invalid_input_is_rejected():
    result = VerificationResult().execute(_input(filing_id=""))
    assert result.error is not None
    assert result.error.code == IngestionError.INVALID_INPUT


def test_unsupported_format_is_rejected():
    result = VerificationResult().execute(_input(format="pdf"))
    assert result.error is not None
    assert result.error.code == IngestionError.UNSUPPORTED_FORMAT
