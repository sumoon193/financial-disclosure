"""Financial Disclosure live smoke: 0 passed, 1 failed, 2 blocked."""
from __future__ import annotations

import argparse
import json
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
    parser.add_argument(
        "--component",
        choices=("health", "model", "ocr", "sec", "database", "storage"),
        default="health",
    )
    args = parser.parse_args(argv)
    if args.component == "model":
        return _model_smoke()
    if args.component == "ocr":
        return _ocr_smoke()
    if args.component == "sec":
        return _sec_smoke()
    if args.component == "database":
        return _database_smoke()
    if args.component == "storage":
        return _storage_smoke()
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


def _sec_smoke() -> int:
    user_agent = os.getenv("FINANCIAL_SEC_USER_AGENT", "").strip()
    if not user_agent:
        print("BLOCKED: set FINANCIAL_SEC_USER_AGENT with a contactable identity")
        return 2
    cik = os.getenv("FINANCIAL_SEC_CIK", "0000320193").strip().zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                print(f"FAILED: SEC EDGAR status={response.status}")
                return 1
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload.get("filings"), dict):
            print("FAILED: SEC EDGAR response lacks filings")
            return 1
        print(f"PASSED: SEC EDGAR submissions fetched; cik={cik}")
        return 0
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429, 503):
            print(f"BLOCKED: SEC EDGAR access unavailable (HTTP {exc.code})")
            return 2
        print(f"FAILED: SEC EDGAR HTTP {exc.code}")
        return 1
    except urllib.error.URLError as exc:
        print(f"BLOCKED: SEC EDGAR unavailable ({exc.reason})")
        return 2
    except (OSError, TypeError, ValueError) as exc:
        print(f"FAILED: SEC EDGAR response ({exc.__class__.__name__})")
        return 1


def _database_smoke() -> int:
    compose_file = os.getenv("FINANCIAL_COMPOSE_FILE", "compose.yaml")
    postgres_service = os.getenv("FINANCIAL_POSTGRES_SERVICE", "postgres")
    redis_service = os.getenv("FINANCIAL_REDIS_SERVICE", "redis")
    postgres_user = os.getenv("FINANCIAL_POSTGRES_USER", "financial")
    commands = (
        ["docker", "compose", "-f", compose_file, "exec", "-T", postgres_service, "pg_isready", "-U", postgres_user],
        ["docker", "compose", "-f", compose_file, "exec", "-T", redis_service, "redis-cli", "ping"],
    )
    try:
        for command in commands:
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"FAILED: middleware command failed ({command[-2]})")
                return 1
    except FileNotFoundError:
        print("BLOCKED: Docker CLI is unavailable")
        return 2
    except subprocess.SubprocessError as exc:
        print(f"BLOCKED: middleware command unavailable ({exc.__class__.__name__})")
        return 2
    print("PASSED: PostgreSQL and Redis Compose clients")
    return 0


def _storage_smoke() -> int:
    base = os.getenv("FINANCIAL_MINIO_URL", "http://127.0.0.1:9010").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/minio/health/live", timeout=10) as response:
            if response.status != 200:
                print(f"FAILED: MinIO health status={response.status}")
                return 1
        print("PASSED: MinIO health")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"FAILED: MinIO HTTP {exc.code}")
        return 1
    except urllib.error.URLError as exc:
        print(f"BLOCKED: MinIO unavailable ({exc.reason})")
        return 2
    except (OSError, ValueError) as exc:
        print(f"FAILED: MinIO health ({exc.__class__.__name__})")
        return 1


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
