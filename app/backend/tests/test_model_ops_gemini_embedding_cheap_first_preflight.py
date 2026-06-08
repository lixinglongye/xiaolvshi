import json
import re

from services.model_ops_gemini_embedding_cheap_first_preflight import (
    ModelOpsGeminiEmbeddingCheapFirstPreflightService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_embedding_cheap_first_preflight_tracks_text_default_and_multimodal_review():
    preflight = ModelOpsGeminiEmbeddingCheapFirstPreflightService().build_preflight()
    rows = {row["model_id"]: row for row in preflight["embedding_rows"]}
    route_rows = {row["id"]: row for row in preflight["route_rows"]}
    checks = {check["id"]: check for check in preflight["checks"]}

    assert preflight["id"] == "modelops-gemini-embedding-cheap-first-preflight"
    assert preflight["status"] == "review_required"
    assert preflight["summary"]["embedding_model_count"] == 2
    assert preflight["summary"]["route_row_count"] == 3
    assert preflight["summary"]["cheap_first_default_model"] == "gemini-embedding-001"
    assert preflight["summary"]["cheap_first_default_canonical_model"] == "gemini-embedding-001"
    assert preflight["summary"]["text_embedding_ready_count"] == 1
    assert preflight["summary"]["multimodal_review_count"] == 1
    assert preflight["summary"]["over_budget_candidate_count"] == 1
    assert preflight["summary"]["default_allowed_model_count"] == 1
    assert preflight["summary"]["review_route_count"] == 1
    assert preflight["summary"]["gateway_called"] is False
    assert preflight["summary"]["network_called"] is False
    assert preflight["summary"]["index_written"] is False
    assert preflight["blocking_check_ids"] == []
    assert "multimodal-embedding-review-boundary" in preflight["warning_check_ids"]
    assert "embedding-route-preflight-inventory" in preflight["warning_check_ids"]

    assert rows["gemini-embedding-001"]["route_role"] == "cheap_first_text_embedding_default"
    assert rows["gemini-embedding-001"]["cost_tier"] == "lowest"
    assert rows["gemini-embedding-001"]["input_usd_per_million_tokens"] == 0.15
    assert rows["gemini-embedding-001"]["batch_input_usd_per_million_tokens"] == 0.075
    assert rows["gemini-embedding-001"]["budget_mode"] == "cheap-first-embedding"
    assert rows["gemini-embedding-001"]["default_allowed_without_review"] is True
    assert rows["gemini-embedding-001"]["is_over_budget"] is False

    assert rows["gemini-embedding-2"]["route_role"] == "multimodal_embedding_review_candidate"
    assert rows["gemini-embedding-2"]["cost_tier"] == "low"
    assert rows["gemini-embedding-2"]["input_usd_per_million_tokens"] == 0.20
    assert rows["gemini-embedding-2"]["batch_input_usd_per_million_tokens"] == 0.10
    assert rows["gemini-embedding-2"]["is_over_budget"] is True
    assert rows["gemini-embedding-2"]["requires_operator_review"] is True
    assert rows["gemini-embedding-2"]["default_allowed_without_review"] is False
    assert "multimodal" in rows["gemini-embedding-2"]["capabilities"]

    assert route_rows["legal-rag-text-index"]["route_status"] == "ready"
    assert route_rows["source-deduping-batch-index"]["route_status"] == "ready"
    assert route_rows["multimodal-evidence-index"]["route_status"] == "review_required"
    assert "over_embedding_budget" in route_rows["multimodal-evidence-index"]["reason_codes"]
    assert checks["embedding-default-cataloged"]["status"] == "pass"
    assert checks["text-embedding-cheap-first"]["status"] == "pass"
    assert checks["metadata-only-boundary"]["status"] == "pass"


def test_embedding_cheap_first_preflight_boundaries_are_metadata_only():
    preflight = ModelOpsGeminiEmbeddingCheapFirstPreflightService().build_preflight(
        {
            "raw_prompt": "sk-THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED_123456789",
            "client_email": "client@example.com",
            "source_chunk": "do not echo",
        }
    )
    serialized = json.dumps(preflight, ensure_ascii=False)

    assert preflight["privacy_boundary"]["metadata_only"] is True
    assert preflight["privacy_boundary"]["gateway_called"] is False
    assert preflight["privacy_boundary"]["network_called"] is False
    assert preflight["privacy_boundary"]["index_written"] is False
    assert preflight["privacy_boundary"]["raw_embedding_vectors_included"] is False
    assert preflight["privacy_boundary"]["raw_legal_text_included"] is False
    assert preflight["claim_boundary"]["live_embedding_route_claimed"] is False
    assert preflight["claim_boundary"]["embedding_index_created"] is False
    assert preflight["claim_boundary"]["multimodal_embedding_default_claimed"] is False
    assert "THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED" not in serialized
    assert "client@example.com" not in serialized
    assert "do not echo" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_embedding_cheap_first_preflight_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-embedding-cheap-first-preflight")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-gemini-embedding-cheap-first-preflight"
    assert payload["data"]["summary"]["cheap_first_default_model"] == "gemini-embedding-001"
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/gemini-embedding-cheap-first-preflight",
        json={"raw_prompt": "do not echo", "model": "sk-THIS_SHOULD_NOT_BE_ECHOED_123456789"},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["embedding_model_count"] == 2
    assert "THIS_SHOULD_NOT_BE_ECHOED" not in json.dumps(posted.json(), ensure_ascii=False)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["routing_aliases"]["auto-embedding"] == "gemini-embedding-001"
    assert (
        models_payload["gemini_embedding_cheap_first_preflight"]["id"]
        == "modelops-gemini-embedding-cheap-first-preflight"
    )
    assert models_payload["gemini_embedding_cheap_first_preflight"]["summary"]["text_embedding_ready_count"] == 1
    assert any(
        check["source_key"] == "gemini_embedding_cheap_first_preflight"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
