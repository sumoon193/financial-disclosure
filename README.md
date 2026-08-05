# Financial Disclosure Workbench

Financial Disclosure is a typed FastAPI service for versioned filing intake,
Decimal-based verification, citation-preserving explanations, persistence and
local OCR admission. Offline tests use deterministic Recorded adapters; live
model and OCR checks are reported separately and never masquerade as offline
acceptance.

## Implemented capabilities

- Typed filing and verification HTTP APIs with request validation.
- Versioned filing, fact, cache, lease, verification-run and audit storage.
- Decimal calculations that are not delegated to a language model.
- Real Qwen explanation adapter that must preserve computed facts.
- Local Tesseract OCR with confidence and coverage quality gates.
- Lifecycle rollback, recovery drills, citations and authorization contracts.

## Run locally

```powershell
Set-Location "D:\Code\agent study\managed-projects\financial-disclosure"
& "D:\py\py3.12\python.exe" -m uvicorn financial_disclosure.api:app `
  --app-dir app --host 127.0.0.1 --port 8001
```

Open:

- API documentation: <http://127.0.0.1:8001/docs>
- Health: <http://127.0.0.1:8001/health>

## Offline verification

```powershell
Set-Location "D:\Code\agent study\managed-projects\financial-disclosure"
& "D:\py\py3.12\python.exe" -m pytest -q
& "D:\py\py3.12\python.exe" -m compileall -q app tests scripts
& "D:\py\py3.12\python.exe" -m ruff check app tests scripts
```

## Live verification

```powershell
$env:FINANCIAL_DISCLOSURE_BASE_URL = "http://127.0.0.1:8001"

& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component health
& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component model
& "D:\py\py3.12\python.exe" ".\scripts\financial_disclosure\live_smoke.py" --component ocr
```

The OCR smoke uses the real local Tesseract binary and generates a temporary
test image when `FINANCIAL_DISCLOSURE_OCR_SAMPLE` is not supplied. To test an
authorized PDF, set that variable to its local path before running OCR.

## Live-smoke exit codes

- `0`: real verification passed.
- `1`: connected, but validation failed.
- `2`: blocked by missing credentials, authorization or service availability.

## Security and authenticity

Keep API keys in local environment variables and never commit `.env`. Fake and
Recorded adapters are offline test tools only. Missing real configuration is
reported as blocked rather than silently downgraded.

## Governance

Development follows `AGENTS.md`, `.agent-governance/` and the active task
handoff. Migrations live in `migrations/financial_disclosure/`.

## License

MIT. See [LICENSE](LICENSE).
