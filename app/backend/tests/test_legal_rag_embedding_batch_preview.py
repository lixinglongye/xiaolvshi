from __future__ import annotations

import json

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

from routers import legal_rag
from schemas.aihub import EmbedTextResponse
from services.legal_rag_embedding_batch_preview import (
    MAX_PREVIEW_CHUNKS,
    LegalRagEmbeddingBatchPreviewService,
    LegalRagEmbeddingBatchPreviewValidationError,
)


class _FakeAIHubService:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.requests = []

    async def embed_text(self, request):
        self.requests.append(request)
        if self.fail:
            raise ValueError("AI service not configured. Set APP_AI_BASE_URL and APP_AI_KEY.")
        return EmbedTextResponse(
            embeddings=[[3.0, 4.0], [0.0, 0.0]],
            model="gemini-embedding-001",
            task="embedding",
            budget_decision={"resolved_model": "gemini-embedding-001", "budget_mode": "cheap-first-embedding"},
            task_inference={"task": "embedding", "source": "explicit"},
            usage={"prompt_tokens": 12, "completion_tokens": 0, "total_tokens": 12},
            usage_units={
                "unit": "embedding_vector",
                "input_count": 2,
                "output_vector_count": 2,
                "dimension_count": 2,
            },
        )


@pytest.mark.asyncio
async def test_embedding_batch_preview_service_executes_aihub_without_returning_text_or_vectors():
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_EMBEDDING_PREVIEW"
    fake_aihub = _FakeAIHubService()
    service = LegalRagEmbeddingBatchPreviewService(aihub_service=fake_aihub)

    preview = await service.build_preview(
        {
            "chunks": [
                {"chunk_id": "source-A-001", "text": raw_text},
                {"chunk_id": "source-A-002", "text": "Second preview paragraph for vector dimensions."},
            ],
        }
    )

    assert fake_aihub.requests[0].input == [raw_text, "Second preview paragraph for vector dimensions."]
    assert fake_aihub.requests[0].model is None
    assert preview["status"] == "ready"
    assert preview["model"] == "gemini-embedding-001"
    assert preview["summary"]["model_called"] is True
    assert preview["summary"]["index_written"] is False
    assert preview["summary"]["embedding_vectors_returned"] is False
    assert preview["preview_rows"][0]["vector_dimension_count"] == 2
    assert preview["preview_rows"][0]["vector_l2_norm"] == 5.0
    assert preview["preview_rows"][0]["text_hash"].startswith("sha256:")
    assert preview["preview_rows"][0]["input_chunk_id_hash"].startswith("sha256:")
    assert "embedding" not in preview["preview_rows"][0]
    assert raw_text not in json.dumps(preview, ensure_ascii=False)
    assert "source-A-001" not in json.dumps(preview, ensure_ascii=False)


@pytest.mark.asyncio
async def test_embedding_batch_preview_service_rejects_oversized_batches_without_echoing_values():
    service = LegalRagEmbeddingBatchPreviewService(aihub_service=_FakeAIHubService())
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_REJECTION"

    with pytest.raises(LegalRagEmbeddingBatchPreviewValidationError) as exc_info:
        await service.build_preview(
            {
                "chunks": [
                    {"chunk_id": f"chunk-{index}", "text": raw_text}
                    for index in range(MAX_PREVIEW_CHUNKS + 1)
                ]
            }
        )

    assert str(exc_info.value) == "embedding_preview_chunk_limit_exceeded"
    assert raw_text not in str(exc_info.value)


def _test_client():
    app = fastapi.FastAPI()
    app.include_router(legal_rag.router)
    return testclient.TestClient(app)


def test_embedding_batch_preview_route_returns_sanitized_metadata(monkeypatch):
    fake_aihub = _FakeAIHubService()
    monkeypatch.setattr(legal_rag, "AIHubService", lambda: fake_aihub)
    client = _test_client()
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_ROUTE"

    response = client.post(
        "/api/v1/legal-rag/embedding-batch-preview",
        json={
            "chunks": [
                {"chunk_id": "route-source-1", "text": raw_text},
                {"chunk_id": "route-source-2", "text": "Second preview paragraph for routing."},
            ],
            "model": "auto-embedding",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    assert payload["success"] is True
    assert fake_aihub.requests[0].model == "auto-embedding"
    assert data["status"] == "ready"
    assert data["summary"]["preview_chunk_count"] == 2
    assert data["summary"]["database_written"] is False
    assert data["privacy_boundary"]["returns_chunk_text"] is False
    assert data["runtime_policy"]["uses_aihub_embedding_runtime"] is True
    assert raw_text not in response.text
    assert "route-source-1" not in response.text
    assert '"embeddings":' not in response.text


def test_embedding_batch_preview_route_returns_503_when_gateway_is_not_configured(monkeypatch):
    monkeypatch.setattr(legal_rag, "AIHubService", lambda: _FakeAIHubService(fail=True))
    client = _test_client()

    response = client.post(
        "/api/v1/legal-rag/embedding-batch-preview",
        json={"chunks": [{"chunk_id": "route-source-1", "text": "Contract paragraph"}]},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "legal_rag_embedding_preview_unavailable"
    assert "APP_AI_KEY" not in response.text
