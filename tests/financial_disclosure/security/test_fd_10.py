"""FD-10 OTel、安全与权限的测试。

RED 先观察失败：来源、检索、核验和 review 必须具有脱敏 Trace 和权限隔离。
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

from financial_disclosure.security import (
    AccessControl,
    FD10Input,
    FD10Result,
    FilingIdentity,
    SecurityError,
)


def _access() -> AccessControl:
    access = AccessControl()
    access.grant("alice", "verify")
    access.grant("bob", "source")
    return access


def _identity() -> FilingIdentity:
    return FilingIdentity(_access())


def test_authorized_operation_is_permitted():
    result = _identity().execute(FD10Input("alice", "verify"))
    assert isinstance(result, FD10Result)
    assert result.error is None
    assert result.permitted
    assert result.operation == "verify"


def test_unauthorized_operation_is_denied():
    result = _identity().execute(FD10Input("alice", "review"))
    assert not result.permitted
    assert result.error is not None
    assert result.error.code == SecurityError.PERMISSION_DENIED


def test_unknown_principal_is_denied():
    result = _identity().execute(FD10Input("mallory", "verify"))
    assert not result.permitted
    assert result.error is not None
    assert result.error.code == SecurityError.PERMISSION_DENIED


def test_sensitive_value_is_redacted_in_trace():
    raw = "supersecretvalue1234567890"
    result = _identity().execute(
        FD10Input("alice", "verify", sensitive_value=raw)
    )
    assert result.permitted
    rendered = " ".join(
        value
        for event in result.trace
        for _, value in event.attributes
    )
    assert raw not in rendered
    assert "***" in rendered


def test_permission_and_operation_stages_are_recorded():
    result = _identity().execute(FD10Input("bob", "source"))
    assert result.permitted
    stages = {event.stage for event in result.trace}
    assert "permission" in stages
    assert "operation" in stages


def test_empty_principal_is_rejected():
    result = _identity().execute(FD10Input("", "verify"))
    assert result.error is not None
    assert result.error.code == SecurityError.INVALID_INPUT


def test_invalid_operation_is_rejected():
    result = _identity().execute(FD10Input("alice", "hack"))
    assert result.error is not None
    assert result.error.code == SecurityError.INVALID_OPERATION


def test_result_is_frozen():
    result = _identity().execute(FD10Input("alice", "verify"))
    with pytest.raises(FrozenInstanceError):
        result.permitted = False  # type: ignore[misc]
