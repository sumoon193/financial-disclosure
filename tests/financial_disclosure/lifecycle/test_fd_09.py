"""FD-09 迁移、回滚与对象生命周期的测试。

RED 先观察失败：active 版本切换必须可回滚，且旧审计事实必须保留。
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

from financial_disclosure.lifecycle import (
    FD09Input,
    FD09Result,
    LifecycleError,
    VerificationResult,
)


def _result() -> VerificationResult:
    return VerificationResult()


def _register(engine: VerificationResult, object_id: str = "obj-1", version: str = "v1", content: str = "c1") -> FD09Result:
    return engine.execute(
        FD09Input(operation="register", object_id=object_id, version=version, content=content)
    )


def test_register_sets_active_and_versions():
    engine = _result()
    result = _register(engine)
    assert isinstance(result, FD09Result)
    assert result.ok and result.error is None
    assert result.active_version == "v1"
    assert result.versions == ("v1",)


def test_switch_active_and_rollback():
    engine = _result()
    _register(engine, version="v1")
    assert engine.execute(FD09Input(operation="add_version", object_id="obj-1", version="v2", content="c2")).ok
    assert engine.execute(FD09Input(operation="switch_active", object_id="obj-1", version="v2")).ok
    after_switch = engine.execute(FD09Input(operation="active_version", object_id="obj-1"))
    assert after_switch.active_version == "v2"
    rollback = engine.execute(FD09Input(operation="rollback", object_id="obj-1"))
    assert rollback.ok
    assert rollback.active_version == "v1"


def test_audit_trail_preserved_and_versions_kept_after_rollback():
    engine = _result()
    _register(engine, version="v1")
    engine.execute(FD09Input(operation="add_version", object_id="obj-1", version="v2", content="c2"))
    engine.execute(FD09Input(operation="switch_active", object_id="obj-1", version="v2"))
    engine.execute(FD09Input(operation="rollback", object_id="obj-1"))
    trail = engine.execute(FD09Input(operation="audit_trail", object_id="obj-1"))
    assert trail.ok
    assert len(trail.audit_trail) == 3
    assert trail.audit_trail[0].version == "v1"
    assert trail.audit_trail[1].version == "v2"
    assert trail.audit_trail[2].action == "rollback"
    state = engine.execute(FD09Input(operation="active_version", object_id="obj-1"))
    assert state.versions == ("v1", "v2")  # 旧审计事实保留


def test_switch_to_unknown_version_is_rejected():
    engine = _result()
    _register(engine)
    result = engine.execute(FD09Input(operation="switch_active", object_id="obj-1", version="v9"))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == LifecycleError.VERSION_NOT_FOUND


def test_rollback_with_single_version_is_rejected():
    engine = _result()
    _register(engine)
    result = engine.execute(FD09Input(operation="rollback", object_id="obj-1"))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == LifecycleError.NOTHING_TO_ROLLBACK


def test_unknown_object_is_rejected():
    engine = _result()
    result = engine.execute(FD09Input(operation="active_version", object_id="missing"))
    assert not result.ok
    assert result.error is not None
    assert result.error.code == LifecycleError.OBJECT_NOT_FOUND


def test_register_is_idempotent():
    engine = _result()
    _register(engine, version="v1")
    again = _register(engine, version="v1")
    assert again.ok and again.error is None
    state = engine.execute(FD09Input(operation="active_version", object_id="obj-1"))
    assert state.active_version == "v1"
    assert state.versions == ("v1",)


def test_invalid_operation_is_rejected():
    result = _result().execute(FD09Input(operation="unknown", object_id="obj-1"))
    assert result.error is not None
    assert result.error.code == LifecycleError.INVALID_OPERATION


def test_result_is_frozen():
    engine = _result()
    _register(engine)
    result = engine.execute(FD09Input(operation="active_version", object_id="obj-1"))
    with pytest.raises(FrozenInstanceError):
        result.ok = False  # type: ignore[misc]
