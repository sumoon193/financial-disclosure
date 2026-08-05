"""Financial Disclosure live smoke: 0 passed, 1 failed, 2 blocked."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=("health", "model", "ocr"), default="health")
    args = parser.parse_args(argv)
    if args.component == "model":
        return _model_smoke()
    if args.component == "ocr":
        return _ocr_smoke()
    base = os.getenv("FINANCIAL_DISCLOSURE_BASE_URL", "").rstrip("/")
    if not base:
        print("BLOCKED: set FINANCIAL_DISCLOSURE_BASE_URL")
        return 2
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
            ok = response.status == 200
            print(
                "PASSED: Financial Disclosure health"
                if ok
                else f"FAILED: status={response.status}"
            )
            return 0 if ok else 1
    except urllib.error.URLError as exc:
        print(f"BLOCKED: service unavailable ({exc.reason})")
        return 2
    except (TimeoutError, ValueError) as exc:
        print(f"FAILED: {exc.__class__.__name__}")
        return 1


def _model_smoke() -> int:
    if not os.getenv("QWEN_API_KEY", "").strip() or not os.getenv("QWEN_CHAT_MODEL", "").strip():
        print("BLOCKED: set QWEN_API_KEY and QWEN_CHAT_MODEL")
        return 2
    _bypass_proxy_for_model_host()
    app_root = Path(__file__).resolve().parents[2] / "app"
    sys.path.insert(0, str(app_root))
    try:
        from financial_disclosure.model.adapter import RealModelAdapter
        from financial_disclosure.retrieval.types import Citation, ComputedFact

        fact = ComputedFact(
            "live-revenue", "123.45", "USD",
            Citation("filing-live", "document-live", "v1"),
        )
        result = RealModelAdapter().interpret(
            "Explain the computed fact without inventing values", (fact,)
        )
        if not result.strip() or "123.45" not in result:
            print("FAILED: model did not preserve the computed fact")
            return 1
        print("PASSED: Financial Disclosure real model adapter")
        return 0
    except (ImportError, RuntimeError, ValueError) as exc:
        if "model request failed" in str(exc):
            print(f"BLOCKED: model service unavailable ({exc.__class__.__name__})")
            return 2
        print(f"FAILED: real model validation ({exc.__class__.__name__})")
        return 1


def _ocr_smoke() -> int:
    sample = os.getenv("FINANCIAL_DISCLOSURE_OCR_SAMPLE", "").strip()
    if not sample:
        with tempfile.TemporaryDirectory(prefix="financial-disclosure-ocr-smoke-") as directory:
            return _run_ocr(Path(_generate_ocr_sample(Path(directory))), generated=True)
    input_path = Path(sample)
    if not input_path.is_file():
        print("BLOCKED: FINANCIAL_DISCLOSURE_OCR_SAMPLE is not an accessible file")
        return 2
    return _run_ocr(input_path, generated=False)


def _run_ocr(input_path: Path, generated: bool) -> int:
    _configure_ocr_environment()
    app_root = Path(__file__).resolve().parents[2] / "app"
    sys.path.insert(0, str(app_root))
    try:
        from financial_disclosure.ocr import (
            FrozenAdmissionMetrics,
            LocalTesseractOcr,
            OCRQualityStatus,
        )

        result = LocalTesseractOcr(
            frozen=FrozenAdmissionMetrics(Decimal("0.90"), Decimal("0.80")),
            binary=_ocr_binary(),
            engine_version_provider=lambda: _ocr_version(_ocr_binary()),
        ).extract(input_path)
    except (ImportError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAILED: local OCR validation ({exc.__class__.__name__})")
        return 1
    if result.status is OCRQualityStatus.PASSED:
        suffix = " (generated smoke fixture)" if generated else ""
        print(f"PASSED: Financial Disclosure local Tesseract OCR{suffix}")
        return 0
    if result.status is OCRQualityStatus.BLOCKED:
        print(f"BLOCKED: {result.error.code if result.error else 'local OCR unavailable'}")
        return 2
    if result.status is OCRQualityStatus.NEEDS_REVIEW:
        print("FAILED: OCR quality gate requires review")
        return 1
    print(f"FAILED: {result.error.code if result.error else 'local OCR failed'}")
    return 1


def _ocr_binary() -> str:
    configured = os.getenv("FINANCIAL_DISCLOSURE_TESSERACT_BINARY", "").strip()
    if configured:
        return configured
    candidate = (
        Path(os.getenv("ProgramFiles", r"C:\Program Files"))
        / "Tesseract-OCR"
        / "tesseract.exe"
    )
    return str(candidate) if candidate.is_file() else "tesseract"


def _configure_ocr_environment() -> None:
    if os.getenv("TESSDATA_PREFIX", "").strip():
        return
    local_app_data = os.getenv("LOCALAPPDATA", "")
    candidate = Path(local_app_data) / "Tesseract-OCR" / "tessdata"
    if (candidate / "chi_sim.traineddata").is_file():
        os.environ["TESSDATA_PREFIX"] = str(candidate)


def _generate_ocr_sample(output_dir: Path) -> Path:
    """Create a high-resolution, dependency-free PNG fixture for real OCR."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required to generate the OCR smoke fixture") from exc
    image = Image.new("RGB", (1400, 300), "white")
    draw = ImageDraw.Draw(image)
    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    font = (
        ImageFont.truetype(str(font_path), 96)
        if font_path.is_file()
        else ImageFont.load_default(size=96)
    )
    draw.text((48, 88), "Revenue 2025", fill="black", font=font)
    sample = output_dir / "generated-ocr-smoke.png"
    image.save(sample, format="PNG")
    return sample


def _ocr_version(binary: str) -> str | None:
    try:
        completed = subprocess.run(
            (binary, "--version"),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    first_line = completed.stdout.splitlines()[0].strip() if completed.stdout else ""
    return first_line.removeprefix("tesseract ") or None


def _bypass_proxy_for_model_host() -> None:
    host = urlparse(os.getenv(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )).hostname
    if not host:
        return
    for name in ("NO_PROXY", "no_proxy"):
        current = [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]
        if host not in current:
            os.environ[name] = ",".join([*current, host])

if __name__ == "__main__":
    sys.exit(main())
