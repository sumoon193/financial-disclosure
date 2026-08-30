"""Fail-closed production evidence validation for Financial Disclosure."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

OFFLINE_GATES = ("source", "build", "offline-tests")
INTEGRATION_GATES = ("sec-edgar", "postgres", "redis", "minio", "tesseract", "qwen")
DEPLOYMENT_GATES = ("business-e2e", "evaluation", "load", "security", "recovery", "cold-start")
PRODUCTION_GATES = ("public-deployment", "stability")
REQUIRED_GATES = (*OFFLINE_GATES, *INTEGRATION_GATES, *DEPLOYMENT_GATES, *PRODUCTION_GATES)
EXPECTED_EXIT_CODES = {"passed": 0, "failed": 1, "blocked": 2}
REQUIRED_FIELDS = ("gate", "status", "commit_sha", "command", "exit_code", "timestamp", "dataset_version", "raw_result")


class EvidenceError(ValueError):
    """Raised when evidence is incomplete, inconsistent, or untraceable."""


@dataclass(frozen=True)
class ReadinessResult:
    status: str
    missing_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    blocked_gates: tuple[str, ...]
    exit_code: int


def gate_commands() -> dict[str, str]:
    return {
        "source": "git diff --check",
        "build": "mvn -B -ntp -DskipTests package && npm --prefix frontend run build",
        "offline-tests": "mvn -B -ntp test && python -m pytest -q",
        "sec-edgar": "python scripts/financial_disclosure/live_smoke.py --component sec",
        "postgres": "python scripts/financial_disclosure/live_smoke.py --component database",
        "redis": "python scripts/financial_disclosure/live_smoke.py --component database",
        "minio": "python scripts/financial_disclosure/live_smoke.py --component storage",
        "tesseract": "python scripts/financial_disclosure/live_smoke.py --component ocr",
        "qwen": "python scripts/financial_disclosure/live_smoke.py --component model",
        "business-e2e": "npm --prefix frontend run test:e2e:live",
        "evaluation": "python -m pytest tests/production -q",
        "load": "python scripts/financial_disclosure/http_probe.py --env-var FINANCIAL_DISCLOSURE_BASE_URL --path /actuator/health --samples 100",
        "security": "mvn -B -ntp test && python -m pytest tests/production -q",
        "recovery": "docker compose -f compose.yaml --profile full restart && python scripts/financial_disclosure/live_smoke.py --component health",
        "cold-start": "docker compose -f compose.yaml --profile full down --remove-orphans && docker compose -f compose.yaml --profile full up -d --build --wait && python scripts/financial_disclosure/live_smoke.py --component health",
        "public-deployment": "python scripts/financial_disclosure/http_probe.py --env-var FINANCIAL_DISCLOSURE_PUBLIC_BASE_URL --path /actuator/health --samples 1",
        "stability": "python scripts/financial_disclosure/http_probe.py --env-var FINANCIAL_DISCLOSURE_PUBLIC_BASE_URL --path /actuator/health --samples 30",
    }


def _text(item: Mapping[str, object], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"evidence field {field} must be non-empty")
    return value.strip()


def _validate_item(item: Mapping[str, object]) -> tuple[str, str, str]:
    for field in REQUIRED_FIELDS:
        if field not in item:
            raise EvidenceError(f"evidence missing field: {field}")
    gate = _text(item, "gate")
    if gate not in REQUIRED_GATES:
        raise EvidenceError(f"unsupported gate: {gate}")
    status = _text(item, "status")
    if status not in EXPECTED_EXIT_CODES:
        raise EvidenceError(f"unsupported evidence status: {status}")
    if item["exit_code"] != EXPECTED_EXIT_CODES[status]:
        raise EvidenceError(f"exit_code does not match status for gate {gate}")
    commit_sha = _text(item, "commit_sha")
    if re.fullmatch(r"[0-9a-f]{40}", commit_sha) is None:
        raise EvidenceError(f"invalid commit_sha for gate {gate}")
    _text(item, "command")
    _text(item, "dataset_version")
    timestamp = _text(item, "timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise EvidenceError(f"invalid timestamp for gate {gate}") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"timestamp must include timezone for gate {gate}")
    raw_result = _text(item, "raw_result").replace("\\", "/")
    result_path = PurePosixPath(raw_result)
    if result_path.is_absolute() or ".." in result_path.parts:
        raise EvidenceError(f"raw_result must be repository-relative for gate {gate}")
    return gate, status, commit_sha


def evaluate_evidence(evidence: Iterable[Mapping[str, object]], expected_commit: str) -> ReadinessResult:
    if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
        raise EvidenceError("expected commit must be a 40-character lowercase SHA")
    statuses: dict[str, str] = {}
    commits: set[str] = set()
    for item in evidence:
        gate, status, commit_sha = _validate_item(item)
        if gate in statuses:
            raise EvidenceError(f"duplicate evidence gate: {gate}")
        statuses[gate] = status
        commits.add(commit_sha)
    if len(commits) > 1:
        raise EvidenceError("evidence contains multiple commits")
    if commits and commits != {expected_commit}:
        raise EvidenceError("evidence does not match expected commit")
    missing = tuple(gate for gate in REQUIRED_GATES if gate not in statuses)
    failed = tuple(gate for gate in REQUIRED_GATES if statuses.get(gate) == "failed")
    blocked = tuple(gate for gate in REQUIRED_GATES if statuses.get(gate) == "blocked")
    status = "prototype"
    for candidate, required in (("offline-verified", OFFLINE_GATES), ("integration-verified", INTEGRATION_GATES), ("deployment-ready", DEPLOYMENT_GATES), ("production-verified", PRODUCTION_GATES)):
        if not all(statuses.get(gate) == "passed" for gate in required):
            break
        status = candidate
    exit_code = 1 if failed else 2 if missing or blocked else 0
    return ReadinessResult(status, missing, failed, blocked, exit_code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--expected-commit")
    args = parser.parse_args(argv)
    if args.describe:
        print(json.dumps(gate_commands(), indent=2, ensure_ascii=False))
        return 0
    if args.evidence is None or args.expected_commit is None:
        parser.error("--evidence and --expected-commit are required unless --describe is used")
    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise EvidenceError("evidence document must be a JSON array")
        result = evaluate_evidence(payload, args.expected_commit)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        parser.exit(2, f"blocked: {exc}\n")
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
