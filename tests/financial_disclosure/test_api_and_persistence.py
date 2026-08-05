from __future__ import annotations

from fastapi.testclient import TestClient
from financial_disclosure.api import create_app
from financial_disclosure.persistence import PersistenceStore


def test_filings_api_is_typed_and_idempotent() -> None:
    client = TestClient(create_app())
    payload = {
        "filing_id": "10-K-A",
        "form": "10-K",
        "format": "html",
        "content": "Revenue 100",
        "version": "2025",
    }
    first = client.post("/filings", json=payload)
    second = client.post("/filings", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["duplicate"] is True


def test_persistence_can_reopen_file(tmp_path) -> None:
    path = tmp_path / "fd.sqlite3"
    first = PersistenceStore(database_path=path)
    first.put_fact("f1", "v1", "100", "USD")
    first.close()

    reopened = PersistenceStore(database_path=path)
    assert reopened.get_fact("f1", "v1") == ("100", "USD", "v1")
    reopened.close()
