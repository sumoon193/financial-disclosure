"""FD-12 完整演练、发布与真实性审计的测试。

RED 先观察失败：来源中断、解析失败和回滚必须有真实演练记录，
未验证外部服务不得写成 passed。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# 让 scripts/financial_disclosure/ 可导入（FD-12 实现位于 scripts 侧）。
_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts" / "financial_disclosure"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import release_drill

DrillLog = release_drill.DrillLog
ErrorContract = release_drill.ErrorContract
FD12Input = release_drill.FD12Input
FD12Result = release_drill.FD12Result
ReleaseError = release_drill.ReleaseError
VerificationResult = release_drill.VerificationResult


def _engine() -> VerificationResult:
    return VerificationResult()


def test_parse_failure_drill_records_verified():
    result = _engine().execute(FD12Input("run_drill", "parse_failure", "broken xbrl"))
    assert isinstance(result, FD12Result)
    assert result.ok and result.error is None
    assert result.record is not None
    assert result.record.drill_type == "parse_failure"
    assert result.record.status == "verified"


def test_rollback_drill_records_verified():
    result = _engine().execute(FD12Input("run_drill", "rollback", "revert v2"))
    assert result.ok
    assert result.record is not None
    assert result.record.status == "verified"


def test_source_interruption_drill_is_simulated_not_passed():
    result = _engine().execute(FD12Input("run_drill", "source_interruption", "sec unavailable"))
    assert result.ok
    assert result.record is not None
    assert result.record.status == "simulated"
    assert result.record.status != "passed"


def test_drill_log_accumulates_real_records():
    engine = _engine()
    engine.execute(FD12Input("run_drill", "parse_failure", "d1"))
    engine.execute(FD12Input("run_drill", "rollback", "d2"))
    engine.execute(FD12Input("run_drill", "source_interruption", "d3"))
    log = engine.execute(FD12Input("drill_log"))
    assert log.ok
    assert len(log.log) == 3
    assert [r.sequence for r in log.log] == [0, 1, 2]
    assert [r.drill_type for r in log.log] == ["parse_failure", "rollback", "source_interruption"]


def test_unknown_drill_type_is_rejected():
    result = _engine().execute(FD12Input("run_drill", "hack", "x"))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == ReleaseError.UNKNOWN_DRILL


def test_missing_details_is_rejected():
    result = _engine().execute(FD12Input("run_drill", "rollback", ""))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == ReleaseError.INVALID_INPUT


def test_invalid_operation_is_rejected():
    result = _engine().execute(FD12Input("train"))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == ReleaseError.INVALID_OPERATION


def test_result_is_frozen():
    result = _engine().execute(FD12Input("run_drill", "rollback", "x"))
    with pytest.raises(FrozenInstanceError):
        result.ok = False  # type: ignore[misc]
