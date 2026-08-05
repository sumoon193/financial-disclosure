"""FD-10 Tracer 脱敏与记录的独立单元测试。

RED 先观察失败：trace 写入前必须脱敏敏感 key 与密文模式，且 trace 不可变。
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

from financial_disclosure.observability import Tracer  # noqa: E402
from financial_disclosure.observability.tracer import TraceEvent  # noqa: E402


def test_redact_sensitive_keys_are_masked():
    tracer = Tracer()
    for key in ("password", "token", "secret", "api_key", "authorization"):
        assert tracer.redact(key, "raw-value") == "***"


def test_redact_normal_key_passes_through():
    tracer = Tracer()
    assert tracer.redact("operation", "verify") == "verify"


def test_redact_sk_pattern_is_masked():
    tracer = Tracer()
    assert tracer.redact("note", "sk-" + "a" * 20) == "***"


def test_redact_bearer_pattern_is_masked():
    tracer = Tracer()
    assert tracer.redact("header", "Bearer abc.def.ghi") == "***"


def test_redact_non_secret_value_passes():
    tracer = Tracer()
    assert tracer.redact("fact_id", "f1") == "f1"


def test_record_redacts_attributes():
    tracer = Tracer()
    tracer.record(
        "operation", "verify", (("principal", "alice"), ("token", "leak-me-now-1234567890"))
    )
    event = tracer.trace()[0]
    values = dict(event.attributes)
    assert values["principal"] == "alice"
    assert values["token"] == "***"
    assert "leak-me-now" not in " ".join(v for _, v in event.attributes)


def test_trace_returns_tuple_and_is_immutable_snapshot():
    tracer = Tracer()
    tracer.record("operation", "verify", (("operation", "verify"),))
    first = tracer.trace()
    assert isinstance(first, tuple)
    assert len(first) == 1
    # 再次 record 不影响已返回的快照
    tracer.record("operation", "source", (("operation", "source"),))
    assert len(first) == 1
    assert len(tracer.trace()) == 2


def test_trace_event_is_frozen():
    tracer = Tracer()
    tracer.record("operation", "verify", (("operation", "verify"),))
    event = tracer.trace()[0]
    assert isinstance(event, TraceEvent)
    with pytest.raises(FrozenInstanceError):
        event.stage = "hacked"  # type: ignore[misc]


def test_record_with_no_attributes_defaults_to_empty():
    tracer = Tracer()
    tracer.record("operation", "verify")
    event = tracer.trace()[0]
    assert event.attributes == ()