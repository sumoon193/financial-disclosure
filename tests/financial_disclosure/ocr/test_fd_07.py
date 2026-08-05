"""FD-07 PDF/OCR 准入的测试。

RED 先观察失败：只有通过冻结准入指标的 PDF/OCR 路径可启用。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.ocr import (
    FD07Input,
    FD07Result,
    FilingIdentity,
    FrozenAdmissionMetrics,
    LocalTesseractOcr,
    OCRAdmissionError,
    OCRMetrics,
    OCRQualityStatus,
)


def _frozen(min_accuracy: str = "0.90", min_coverage: str = "0.80") -> FrozenAdmissionMetrics:
    return FrozenAdmissionMetrics(
        min_accuracy=Decimal(min_accuracy), min_coverage=Decimal(min_coverage)
    )


def _identity(**kwargs) -> FilingIdentity:
    return FilingIdentity(_frozen(**kwargs))


def test_path_passing_frozen_metrics_is_enabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    assert isinstance(result, FD07Result)
    assert result.error is None
    assert result.enabled
    assert result.accuracy == Decimal("0.95")
    assert result.coverage == Decimal("0.85")
    assert result.min_accuracy == Decimal("0.90")
    assert result.min_coverage == Decimal("0.80")


def test_path_failing_accuracy_is_disabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.80"), Decimal("0.85")))
    )
    assert not result.enabled
    assert result.error is None


def test_path_failing_coverage_is_disabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.70")))
    )
    assert not result.enabled
    assert result.error is None


def test_boundary_equal_to_threshold_is_enabled():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.90"), Decimal("0.80")))
    )
    assert result.enabled
    assert result.error is None


def test_empty_path_id_is_rejected():
    result = _identity().execute(
        FD07Input("", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    assert result.error is not None
    assert result.error.code == OCRAdmissionError.INVALID_INPUT


def test_out_of_range_metrics_are_rejected():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("1.5"), Decimal("0.85")))
    )
    assert result.error is not None
    assert result.error.code == OCRAdmissionError.INVALID_METRICS


def test_frozen_metrics_are_immutable():
    frozen = _frozen()
    with pytest.raises(FrozenInstanceError):
        frozen.min_accuracy = Decimal("0.99")  # type: ignore[misc]


def test_result_is_frozen():
    result = _identity().execute(
        FD07Input("pdf-path-a", OCRMetrics(Decimal("0.95"), Decimal("0.85")))
    )
    with pytest.raises(FrozenInstanceError):
        result.enabled = False  # type: ignore[misc]


def test_local_tesseract_uses_tsv_confidence_and_marks_low_quality_for_review(
    tmp_path: Path,
):
    image = tmp_path / "statement.png"
    image.write_bytes(b"not-a-real-image")
    calls: list[tuple[str, ...]] = []

    def run(command: tuple[str, ...], timeout_seconds: int) -> str:
        calls.append(command)
        assert timeout_seconds == 30
        assert command[-1] == "tsv"
        return (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t55.0\tRevenue\n"
        )

    result = LocalTesseractOcr(
        runner=run,
        engine_version_provider=lambda: "5.5.0",
        frozen=_frozen(min_accuracy="0.90", min_coverage="0.80"),
    ).extract(image)

    assert result.status is OCRQualityStatus.NEEDS_REVIEW
    assert result.metrics.accuracy == Decimal("0.55")
    assert result.metrics.coverage == Decimal(1)
    assert result.engine == "tesseract"
    assert result.engine_version == "5.5.0"
    assert result.languages == ("chi_sim", "eng")
    assert calls == [
        ("tesseract", str(image), "stdout", "-l", "chi_sim+eng", "tsv")
    ]


def test_local_tesseract_reports_blocked_when_binary_is_not_available(tmp_path: Path):
    image = tmp_path / "statement.png"
    image.write_bytes(b"not-a-real-image")

    def missing_binary(command: tuple[str, ...], timeout_seconds: int) -> str:
        raise FileNotFoundError(command[0])

    result = LocalTesseractOcr(runner=missing_binary, frozen=_frozen()).extract(image)

    assert result.status is OCRQualityStatus.BLOCKED
    assert result.error is not None
    assert result.error.code == "ocr.local.binary.unavailable"


def test_local_tesseract_renders_each_pdf_page_before_quality_gating(tmp_path: Path):
    document = tmp_path / "statement.pdf"
    page_one = tmp_path / "page-1.png"
    page_two = tmp_path / "page-2.png"
    document.write_bytes(b"pdf")
    page_one.write_bytes(b"page one")
    page_two.write_bytes(b"page two")

    def render(source: Path, output_dir: Path) -> tuple[Path, ...]:
        assert source == document
        assert output_dir.is_dir()
        return (page_one, page_two)

    def run(command: tuple[str, ...], timeout_seconds: int) -> str:
        assert timeout_seconds == 30
        word = "Revenue" if command[1] == str(page_one) else "2025"
        return (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            f"5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t95.0\t{word}\n"
        )

    result = LocalTesseractOcr(
        runner=run,
        pdf_renderer=render,
        frozen=_frozen(min_accuracy="0.90", min_coverage="1.00"),
    ).extract(document)

    assert result.status is OCRQualityStatus.PASSED
    assert result.text == "Revenue 2025"
    assert result.metrics.accuracy == Decimal("0.95")
    assert result.metrics.coverage == Decimal(1)


def test_pdf_path_keeps_tesseract_binary_block_reason_after_rendering(tmp_path: Path):
    document = tmp_path / "statement.pdf"
    page = tmp_path / "page-1.png"
    document.write_bytes(b"pdf")
    page.write_bytes(b"page")

    def missing_tesseract(command: tuple[str, ...], timeout_seconds: int) -> str:
        raise FileNotFoundError(command[0])

    result = LocalTesseractOcr(
        runner=missing_tesseract,
        pdf_renderer=lambda _source, _output_dir: (page,),
        frozen=_frozen(),
    ).extract(document)

    assert result.status is OCRQualityStatus.BLOCKED
    assert result.error is not None
    assert result.error.code == "ocr.local.binary.unavailable"
