"""Local Tesseract OCR adapter with explicit quality and failure states."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import tempfile
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..contracts.errors import ErrorContract
from .types import (
    FrozenAdmissionMetrics,
    LocalOCRResult,
    OCRMetrics,
    OCRQualityStatus,
)

CommandRunner = Callable[[tuple[str, ...], int], str]
PdfRenderer = Callable[[Path, Path], tuple[Path, ...]]
EngineVersionProvider = Callable[[], str | None]


def _subprocess_runner(command: tuple[str, ...], timeout_seconds: int) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
    )
    return completed.stdout


def _poppler_renderer(input_path: Path, output_dir: Path) -> tuple[Path, ...]:
    prefix = output_dir / "page"
    subprocess.run(
        ("pdftoppm", "-r", "300", "-png", str(input_path), str(prefix)),
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    pages = tuple(sorted(output_dir.glob("page-*.png")))
    if not pages:
        raise ValueError("PDF renderer produced no pages")
    return pages


class LocalTesseractOcr:
    """Runs an installed Tesseract binary and gates the result using frozen metrics."""

    def __init__(
        self,
        frozen: FrozenAdmissionMetrics,
        runner: CommandRunner = _subprocess_runner,
        pdf_renderer: PdfRenderer = _poppler_renderer,
        engine_version_provider: EngineVersionProvider | None = None,
        binary: str = "tesseract",
        languages: tuple[str, ...] = ("chi_sim", "eng"),
        timeout_seconds: int = 30,
    ) -> None:
        self._frozen = frozen
        self._runner = runner
        self._pdf_renderer = pdf_renderer
        self._engine_version_provider = engine_version_provider or (lambda: None)
        self._binary = binary
        self._languages = languages
        self._timeout_seconds = timeout_seconds

    def extract(self, input_path: Path) -> LocalOCRResult:
        digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
        if input_path.suffix.lower() == ".pdf":
            try:
                with tempfile.TemporaryDirectory(prefix="financial-disclosure-ocr-") as directory:
                    pages = self._pdf_renderer(input_path, Path(directory))
                    return self._extract_pages(pages, digest)
            except FileNotFoundError:
                return self._error(
                    OCRQualityStatus.BLOCKED,
                    digest,
                    "ocr.local.pdf_renderer.unavailable",
                    "local PDF renderer is unavailable",
                )
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
                return self._error(
                    OCRQualityStatus.FAILED,
                    digest,
                    "ocr.local.pdf_renderer.failed",
                    "local PDF renderer failed",
                )
        return self._extract_pages((input_path,), digest)

    def _extract_pages(self, pages: tuple[Path, ...], digest: str) -> LocalOCRResult:
        outputs: list[str] = []
        for page in pages:
            command = (
                self._binary,
                str(page),
                "stdout",
                "-l",
                "+".join(self._languages),
                "tsv",
            )
            try:
                outputs.append(self._runner(command, self._timeout_seconds))
            except FileNotFoundError:
                return self._error(
                    OCRQualityStatus.BLOCKED,
                    digest,
                    "ocr.local.binary.unavailable",
                    "local tesseract binary is unavailable",
                )
            except subprocess.TimeoutExpired:
                return self._error(
                    OCRQualityStatus.FAILED,
                    digest,
                    "ocr.local.timeout",
                    "local tesseract timed out",
                )
            except subprocess.CalledProcessError:
                return self._error(
                    OCRQualityStatus.FAILED,
                    digest,
                    "ocr.local.execution.failed",
                    "local tesseract failed",
                )
        try:
            parsed = [self._parse_tsv(output) for output in outputs]
        except (csv.Error, InvalidOperation, KeyError, ValueError):
            return self._error(
                OCRQualityStatus.FAILED,
                digest,
                "ocr.local.output.invalid",
                "local tesseract returned invalid TSV",
            )
        words = [(text, confidences) for text, confidences in parsed if text]
        if not words:
            return self._error(
                OCRQualityStatus.FAILED,
                digest,
                "ocr.local.output.invalid",
                "local tesseract returned no recognized text",
            )
        confidences = [confidence for _, values in words for confidence in values]
        text = " ".join(value for value, _ in words)
        metrics = OCRMetrics(
            accuracy=sum(confidences) / Decimal(len(confidences)) / Decimal("100"),
            coverage=Decimal(len(words)) / Decimal(len(pages)),
        )
        status = (
            OCRQualityStatus.PASSED
            if metrics.accuracy >= self._frozen.min_accuracy
            and metrics.coverage >= self._frozen.min_coverage
            else OCRQualityStatus.NEEDS_REVIEW
        )
        return LocalOCRResult(
            status=status,
            text=text,
            metrics=metrics,
            engine="tesseract",
            engine_version=self._engine_version_provider(),
            languages=self._languages,
            input_sha256=digest,
        )

    def _parse_tsv(self, output: str) -> tuple[str, list[Decimal]]:
        rows = list(csv.DictReader(output.splitlines(), delimiter="\t"))
        words = [row for row in rows if row.get("text", "").strip()]
        if not words:
            return "", []
        confidences = [Decimal(row["conf"]) for row in words]
        return " ".join(row["text"].strip() for row in words), confidences

    def _error(
        self, status: OCRQualityStatus, digest: str, code: str, message: str
    ) -> LocalOCRResult:
        return LocalOCRResult(
            status=status,
            text="",
            metrics=OCRMetrics(Decimal("0"), Decimal("0")),
            engine="tesseract",
            engine_version=self._engine_version_provider(),
            languages=self._languages,
            input_sha256=digest,
            error=ErrorContract(code, message),
        )
