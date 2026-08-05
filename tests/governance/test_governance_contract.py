"""Regression contracts for the generated governance runtime."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_push_branch_falls_back_to_github_ref_name() -> None:
    source = (ROOT / "tools" / "governance" / "run.py").read_text(encoding="utf-8")
    assert "GITHUB_REF_NAME" in source


def test_editable_install_discovers_only_application_packages() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["build-system"]["build-backend"] == "setuptools.build_meta"
    package_find = config["tool"]["setuptools"]["packages"]["find"]
    assert package_find["where"] == ["app"]
    assert package_find["include"] == ["financial_disclosure*"]


def test_editable_install_metadata_is_ignored() -> None:
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert any("egg-info" in pattern for pattern in patterns)


def test_governance_commands_use_current_python_interpreter() -> None:
    source = (ROOT / "tools" / "governance" / "run.py").read_text(encoding="utf-8")
    assert "sys.executable" in source


def test_package_declares_api_runtime_dependencies() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = config["project"]["dependencies"]

    assert any(dependency.startswith("fastapi") for dependency in dependencies)
    assert any(dependency.startswith("pydantic") for dependency in dependencies)
    assert any(dependency.startswith("httpx") for dependency in dependencies)
    assert any(dependency.startswith("pillow") for dependency in dependencies)
