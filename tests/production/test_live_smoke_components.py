from types import SimpleNamespace

from scripts.financial_disclosure import live_smoke


def test_sec_smoke_is_blocked_without_contactable_user_agent(monkeypatch) -> None:
    monkeypatch.delenv("FINANCIAL_SEC_USER_AGENT", raising=False)
    assert live_smoke.main(["--component", "sec"]) == 2


def test_storage_smoke_uses_minio_health_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("FINANCIAL_MINIO_URL", "http://minio.test")

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(live_smoke.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    assert live_smoke.main(["--component", "storage"]) == 0


def test_database_smoke_checks_postgres_and_redis(monkeypatch) -> None:
    calls: list[list[str]] = []

    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(live_smoke.subprocess, "run", run)
    assert live_smoke.main(["--component", "database"]) == 0
    assert any("pg_isready" in command for command in calls)
    assert any("redis-cli" in command for command in calls)
