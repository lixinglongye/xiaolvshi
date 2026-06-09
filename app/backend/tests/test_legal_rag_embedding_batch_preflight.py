from __future__ import annotations

import json
import re

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

from routers import legal_rag, maintenance
from services.legal_rag_embedding_batch_preflight import LegalRagEmbeddingBatchPreflightService


def test_embedding_batch_preflight_allows_small_clean_preview_without_network():
    service = LegalRagEmbeddingBatchPreflightService()
    raw_text = "Clean contract clause for local preflight only."

    preflight = service.build_preflight(
        {
            "chunks": [
                {"chunk_id": "clean-source-001", "text": raw_text},
                {"chunk_id": "clean-source-002", "content": "Second clean paragraph for embedding preview."},
            ],
            "model": "auto-embedding",
        }
    )
    rendered = json.dumps(preflight, ensure_ascii=False)

    assert preflight["id"] == "legal-rag-embedding-batch-preflight"
    assert preflight["schema_version"] == "legal-rag-embedding-batch-preflight-v1"
    assert preflight["status"] == "ready_for_preview"
    assert preflight["summary"]["preview_eligible"] is True
    assert preflight["summary"]["resolved_model"] == "gemini-embedding-001"
    assert preflight["summary"]["canonical_model"] == "gemini-embedding-001"
    assert preflight["summary"]["model_cost_tier"] == "lowest"
    assert preflight["summary"]["model_called"] is False
    assert preflight["summary"]["gateway_called"] is False
    assert preflight["summary"]["network_called"] is False
    assert preflight["summary"]["embeddings_created"] is False
    assert preflight["summary"]["index_written"] is False
    assert preflight["preflight_rows"][0]["text_hash"].startswith("sha256:")
    assert preflight["preflight_rows"][0]["input_chunk_id_hash"].startswith("sha256:")
    assert raw_text not in rendered
    assert "clean-source-001" not in rendered


def test_embedding_batch_preflight_reviews_duplicates_and_pii_without_echoing_values():
    service = LegalRagEmbeddingBatchPreflightService()
    email = "client@example.invalid"
    phone = "+86 138 0000 0000"
    duplicated = "Duplicate contract paragraph with client contact "

    preflight = service.build_preflight(
        {
            "chunks": [
                {"chunk_id": "dup-1", "text": duplicated + email},
                {"chunk_id": "dup-2", "text": duplicated + email},
                {"chunk_id": "phone-1", "text": "Contact phone " + phone},
            ]
        }
    )
    rendered = json.dumps(preflight, ensure_ascii=False)
    rows = preflight["preflight_rows"]

    assert preflight["status"] == "review_required"
    assert preflight["summary"]["duplicate_text_hash_count"] == 2
    assert preflight["summary"]["pii_signal_count"] >= 3
    assert rows[0]["duplicate_text_hash"] is True
    assert "duplicate_text_hash" in rows[0]["reason_codes"]
    assert "pii_signal_detected:email" in rows[0]["reason_codes"]
    assert any("pii_signal_detected:phone" in row["reason_codes"] for row in rows)
    assert email not in rendered
    assert phone not in rendered
    assert "dup-1" not in rendered


def test_embedding_batch_preflight_blocks_secret_like_inputs_without_leaking_secret():
    service = LegalRagEmbeddingBatchPreflightService()
    secret = "sk-" + ("A" * 28)

    preflight = service.build_preflight(
        {"chunks": [{"chunk_id": "secret-source", "text": "Do not embed this credential " + secret}]}
    )
    rendered = json.dumps(preflight, ensure_ascii=False)

    assert preflight["status"] == "blocked"
    assert preflight["summary"]["blocked_row_count"] == 1
    assert preflight["summary"]["secret_signal_count"] == 1
    assert preflight["preflight_rows"][0]["preflight_status"] == "blocked"
    assert "secret_like_input_detected" in preflight["preflight_rows"][0]["reason_codes"]
    assert secret not in rendered
    assert "secret-source" not in rendered
    assert re.search(r"sk-[A-Za-z0-9_-]{20,}", rendered) is None


def test_embedding_batch_preflight_route_returns_sanitized_payload():
    app = fastapi.FastAPI()
    app.include_router(legal_rag.router)
    client = testclient.TestClient(app)
    raw_text = "Clean route paragraph that should not be echoed."

    response = client.post(
        "/api/v1/legal-rag/embedding-batch-preflight",
        json={"chunks": [{"chunk_id": "route-source-1", "text": raw_text}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_preview"
    assert payload["data"]["privacy_boundary"]["calls_gateway"] is False
    assert raw_text not in response.text
    assert "route-source-1" not in response.text


def test_embedding_batch_preflight_maintenance_route_uses_same_service():
    app = fastapi.FastAPI()
    app.include_router(maintenance.router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-rag-embedding-batch-preflight")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "blocked"
    assert "embedding_preflight_chunks_required" in get_response.json()["data"]["request_reason_codes"]

    post_response = client.post(
        "/api/v1/maintenance/legal-rag-embedding-batch-preflight",
        json={"chunks": [{"chunk_id": "maintenance-source", "text": "Maintenance clean paragraph"}]},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready_for_preview"
    assert "maintenance-source" not in post_response.text
