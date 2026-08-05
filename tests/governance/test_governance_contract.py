"""Regression contracts for the generated governance runtime."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_push_branch_falls_back_to_github_ref_name() -> None:
    source = (ROOT / "tools" / "governance" / "run.py").read_text(encoding="utf-8")
    assert "GITHUB_REF_NAME" in source
