"""FD-01 来源、许可证与公开样例基线的可观察合同测试。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from audit.contracts import FD01Input, FD01Result, FilingIdentity

BASELINE = Path(__file__).resolve().parents[3] / "docs" / "audit" / "sample-baseline.json"


def _load_baseline():
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert data["schema_version"]
    return data["samples"]


def test_every_sample_has_source_version_and_license_status():
    for sample in _load_baseline():
        assert sample["sample_id"]
        assert sample["source"]
        assert sample["version"]
        assert sample["license_status"]


def test_filing_identity_returns_typed_contract_for_every_sample():
    baseline = {s["sample_id"]: s for s in _load_baseline()}
    identity = FilingIdentity(baseline)
    for sample_id, expected in baseline.items():
        result = identity.execute(FD01Input(sample_id))
        assert isinstance(result, FD01Result)
        assert result.sample_id == sample_id
        assert result.source == expected["source"]
        assert result.version == expected["version"]
        assert result.license_status == expected["license_status"]


def test_unknown_sample_fails_stably():
    identity = FilingIdentity({})
    with pytest.raises(KeyError):
        identity.execute(FD01Input("does-not-exist"))
