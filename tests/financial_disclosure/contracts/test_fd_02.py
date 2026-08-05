"""FD-02 Typed API、状态与错误合同的测试。

RED 先观察失败：Filing/Verification API 必须输出固定 typed result，
状态机非法转换必须稳定拒绝。
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# 让 app/ 可导入（仓库未安装包时本地运行也需要）。
_APP = Path(__file__).resolve().parents[3] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from financial_disclosure.contracts import (
    CitationAnchor,
    ErrorCode,
    ErrorContract,
    FD02Input,
    FD02Result,
    VerificationRun,
    VerificationState,
)


def _anchor() -> CitationAnchor:
    return CitationAnchor(
        {
            "vr-1": VerificationRun("vr-1", "2025-10K"),
            "vr-2": VerificationRun("vr-2", "2024-8K", VerificationState.COMPUTED),
        }
    )


def test_execute_returns_fixed_typed_output():
    result = _anchor().execute(FD02Input("vr-1", "2025-10K"))
    assert isinstance(result, FD02Result)
    assert result.verification_id == "vr-1"
    assert result.document_version == "2025-10K"
    assert result.state is VerificationState.CREATED
    assert result.error is None


def test_query_reflects_current_state():
    result = _anchor().execute(FD02Input("vr-2", "2024-8K"))
    assert result.state is VerificationState.COMPUTED
    assert result.error is None


def test_legal_transition_advances_state():
    result = _anchor().execute(FD02Input("vr-1", "2025-10K", "evidence_ready"))
    assert result.state is VerificationState.EVIDENCE_READY
    assert result.error is None


def test_full_state_path_is_legal():
    run = VerificationRun("vr-3", "2025-S1")
    for expected in (
        VerificationState.EVIDENCE_READY,
        VerificationState.COMPUTED,
        VerificationState.REVIEWED,
        VerificationState.COMPLETED,
    ):
        run = run.advance(expected)
        assert isinstance(run, VerificationRun)
        assert run.state is expected


def test_illegal_transition_is_stably_rejected():
    result = _anchor().execute(FD02Input("vr-1", "2025-10K", "completed"))
    assert result.state is VerificationState.CREATED
    assert result.error is not None
    assert result.error.code == ErrorCode.ILLEGAL_STATE_TRANSITION


def test_advance_from_completed_is_rejected():
    run = VerificationRun("vr-4", "2025-S1", VerificationState.COMPLETED)
    outcome = run.advance(VerificationState.REVIEWED)
    assert isinstance(outcome, ErrorContract)
    assert outcome.code == ErrorCode.ILLEGAL_STATE_TRANSITION


def test_unknown_verification_returns_stable_error():
    result = _anchor().execute(FD02Input("vr-nope", "2025-10K"))
    assert result.error is not None
    assert result.error.code == ErrorCode.UNKNOWN_VERIFICATION


def test_invalid_input_returns_stable_error():
    result = _anchor().execute(FD02Input("", "2025-10K"))
    assert result.error is not None
    assert result.error.code == ErrorCode.INVALID_INPUT


def test_invalid_target_state_returns_stable_error():
    result = _anchor().execute(FD02Input("vr-1", "2025-10K", "not-a-state"))
    assert result.error is not None
    assert result.error.code == ErrorCode.INVALID_INPUT


def test_typed_output_is_frozen():
    result = _anchor().execute(FD02Input("vr-1", "2025-10K"))
    with pytest.raises(FrozenInstanceError):
        result.state = VerificationState.COMPLETED  # type: ignore[misc]
