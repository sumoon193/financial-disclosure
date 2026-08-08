from __future__ import annotations

import pytest

from scripts.financial_disclosure.production_readiness import (
    REQUIRED_GATES,
    EvidenceError,
    evaluate_evidence,
    gate_commands,
)

CURRENT_COMMIT = "dae9ad0c7d329e75c025f1598def559937d49f12"


def _passed(gate: str, commit: str = CURRENT_COMMIT) -> dict[str, object]:
    return {
        "gate": gate,
        "status": "passed",
        "commit_sha": commit,
        "command": f"verify {gate}",
        "exit_code": 0,
        "timestamp": "2026-08-08T12:00:00+08:00",
        "dataset_version": "financial-production-v2-test",
        "raw_result": f"reports/production-v2/{gate}.json",
    }


def test_required_gates_cover_strict_production_verification() -> None:
    assert REQUIRED_GATES == (
        "source", "build", "offline-tests", "sec-edgar", "postgres", "redis",
        "minio", "tesseract", "qwen", "business-e2e", "evaluation", "load",
        "security", "recovery", "cold-start", "public-deployment", "stability",
    )


def test_blocked_sec_never_reaches_integration_verified() -> None:
    evidence = [_passed(gate) for gate in REQUIRED_GATES]
    sec = next(item for item in evidence if item["gate"] == "sec-edgar")
    sec["status"] = "blocked"
    sec["exit_code"] = 2

    result = evaluate_evidence(evidence, CURRENT_COMMIT)

    assert result.status == "offline-verified"
    assert result.blocked_gates == ("sec-edgar",)
    assert result.exit_code == 2


def test_mixed_commit_evidence_fails_closed() -> None:
    evidence = [_passed(gate) for gate in REQUIRED_GATES]
    evidence[-1]["commit_sha"] = "b" * 40
    with pytest.raises(EvidenceError, match="multiple commits"):
        evaluate_evidence(evidence, CURRENT_COMMIT)


def test_all_gates_pass_at_expected_commit() -> None:
    result = evaluate_evidence([_passed(gate) for gate in REQUIRED_GATES], CURRENT_COMMIT)
    assert result.status == "production-verified"
    assert result.exit_code == 0


def test_gate_commands_keep_live_sources_distinct() -> None:
    commands = gate_commands()
    assert set(commands) == set(REQUIRED_GATES)
    assert "--component sec" in commands["sec-edgar"]
    assert "--component ocr" in commands["tesseract"]
    assert "npm --prefix frontend run test:e2e:live" in commands["business-e2e"]
    assert all("API_KEY=" not in command for command in commands.values())
