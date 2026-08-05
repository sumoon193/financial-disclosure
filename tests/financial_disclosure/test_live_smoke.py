import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "financial_disclosure" / "live_smoke.py"


def _module():
    spec = importlib.util.spec_from_file_location("financial_live_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_smoke_is_blocked_without_real_credentials(monkeypatch):
    module = _module()
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_CHAT_MODEL", raising=False)

    assert module.main(["--component", "model"]) == 2


def test_ocr_smoke_generates_a_local_fixture_without_user_document(monkeypatch):
    module = _module()
    monkeypatch.delenv("FINANCIAL_DISCLOSURE_OCR_SAMPLE", raising=False)

    assert module.main(["--component", "ocr"]) == 0


def test_ocr_binary_uses_explicit_nonsecret_override(monkeypatch):
    module = _module()
    monkeypatch.setenv("FINANCIAL_DISCLOSURE_TESSERACT_BINARY", r"C:\\OCR\\tesseract.exe")

    assert module._ocr_binary() == r"C:\\OCR\\tesseract.exe"


def test_ocr_smoke_fixture_is_generated_without_user_document(tmp_path):
    module = _module()

    sample = module._generate_ocr_sample(tmp_path)

    assert sample.is_file()
    assert sample.suffix == ".png"
    assert sample.stat().st_size > 100
