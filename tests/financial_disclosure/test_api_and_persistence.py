from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

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


def test_verification_run_is_written_through_public_store_contract(tmp_path) -> None:
    path = tmp_path / "fd.sqlite3"
    store = PersistenceStore(database_path=path)
    client = TestClient(create_app(store=store))

    response = client.post(
        "/verification-runs",
        json={
            "fact_id": "revenue",
            "value": "123.45",
            "unit": "USD",
            "expected_value": "123.40",
            "tolerance": "0.10",
            "citation": {"filing_id": "filing-1", "document_version_id": "v1"},
        },
    )

    assert response.status_code == 201
    run_id = response.json()["run_id"]
    store.close()
    reopened = PersistenceStore(database_path=path)
    saved = reopened.get_verification_run(run_id)
    assert saved is not None
    assert saved[0] == "filing-1"
    assert saved[1] == "accepted"
    assert saved[2]["fact_id"] == "revenue"
    reopened.close()


def test_store_serializes_concurrent_connection_access(tmp_path) -> None:
    store = PersistenceStore(database_path=tmp_path / "concurrent.sqlite3")

    def write_and_read(worker: int) -> None:
        for item in range(50):
            key = f"{worker}-{item}"
            store.put_fact(key, "v1", str(item), "USD")
            store.cache_put(key, f"result-{item}")
            assert store.get_fact(key, "v1") == (str(item), "USD", "v1")
            assert store.cache_get(key) == f"result-{item}"

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(write_and_read, worker) for worker in range(12)]
        for future in futures:
            future.result()

    store.close()
