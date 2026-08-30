from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_maven_build_uses_java_17_spring_boot_and_agentscope_2() -> None:
    pom = _read("pom.xml")

    assert "<java.version>17</java.version>" in pom
    assert "spring-boot-starter-web" in pom
    assert "spring-boot-starter-validation" in pom
    assert "spring-boot-starter-data-jpa" in pom
    assert "<groupId>io.agentscope</groupId>" in pom
    assert "<artifactId>agentscope-harness</artifactId>" in pom
    assert "<artifactId>agentscope-extensions-model-dashscope</artifactId>" in pom
    assert "<agentscope.version>2.0.0</agentscope.version>" in pom


def test_java_service_exposes_typed_health_filing_and_verification_api() -> None:
    application = ROOT / "src/main/java/com/example/financialdisclosure/FinancialDisclosureApplication.java"
    controller = _read(
        "src/main/java/com/example/financialdisclosure/api/FinancialDisclosureController.java"
    )

    assert application.is_file()
    assert '@GetMapping("/health")' in controller
    assert '@PostMapping("/api/filings")' in controller
    assert '@PostMapping("/api/verification-runs")' in controller
    assert "@Valid" in controller


def test_financial_calculation_is_bigdecimal_only() -> None:
    calculator = _read(
        "src/main/java/com/example/financialdisclosure/domain/DeterministicFinancialCalculator.java"
    )

    assert "BigDecimal" in calculator
    assert "double " not in calculator
    assert "float " not in calculator
    assert "MathContext" in calculator


def test_production_source_has_no_fake_or_recorded_adapter() -> None:
    production_sources = list((ROOT / "src/main/java").rglob("*.java"))
    assert production_sources

    forbidden = []
    for source_path in production_sources:
        source = source_path.read_text(encoding="utf-8").lower()
        if "fakeadapter" in source or "recordedadapter" in source:
            forbidden.append(source_path.relative_to(ROOT).as_posix())
    assert forbidden == []


def test_compose_declares_real_postgres_redis_and_minio() -> None:
    compose = _read("compose.yaml")

    assert "postgres:" in compose
    assert "redis:" in compose
    assert "minio:" in compose
    assert "healthcheck:" in compose
