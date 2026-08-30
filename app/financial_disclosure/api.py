"""Typed HTTP API for the financial disclosure workbench."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .ingestion import FD03Input, VerificationResult
from .persistence import PersistenceStore


class FilingRequest(BaseModel):
    filing_id: str = Field(min_length=1)
    form: str = Field(min_length=1)
    format: str = Field(min_length=1)
    content: str
    version: str = Field(min_length=1)
    amendment_of: str | None = None


class FilingResponse(BaseModel):
    filing_id: str
    document_version_id: str | None
    duplicate: bool
    amended: bool


class VerificationRunRequest(BaseModel):
    fact_id: str = Field(min_length=1)
    value: str
    unit: str
    expected_value: str
    tolerance: str
    citation: dict[str, str]


class VerificationRunResponse(BaseModel):
    run_id: str
    status: str
    result: dict[str, Any]


def create_app(*, store: PersistenceStore | None = None) -> FastAPI:
    app = FastAPI(title="Financial Disclosure Verification API", version="0.1.0")
    persistence = store or PersistenceStore()
    ingestion = VerificationResult()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/filings", response_model=FilingResponse, status_code=201)
    def ingest_filing(body: FilingRequest) -> FilingResponse:
        result = ingestion.execute(FD03Input(**body.model_dump()))
        if result.error is not None:
            raise HTTPException(status_code=400, detail=result.error.__dict__)
        if result.document_version_id is None:
            raise HTTPException(
                status_code=500, detail="ingestion did not produce a document version"
            )
        return FilingResponse(
            filing_id=result.filing_id,
            document_version_id=result.document_version_id,
            duplicate=result.duplicate,
            amended=result.amended,
        )

    @app.post("/verification-runs", response_model=VerificationRunResponse, status_code=201)
    def create_verification_run(body: VerificationRunRequest) -> VerificationRunResponse:
        run_id = f"run-{uuid.uuid4().hex}"
        result = {
            "fact_id": body.fact_id,
            "value": body.value,
            "unit": body.unit,
            "expected_value": body.expected_value,
            "tolerance": body.tolerance,
            "citation": body.citation,
        }
        persistence.record_verification_run(
            run_id,
            body.citation.get("filing_id", ""),
            "accepted",
            result,
        )
        return VerificationRunResponse(run_id=run_id, status="accepted", result=result)

    return app


app = create_app()
