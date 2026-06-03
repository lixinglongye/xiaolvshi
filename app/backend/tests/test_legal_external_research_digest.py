import re

from services.legal_external_research_digest import LegalExternalResearchDigestService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_legal_external_research_digest_tracks_primary_sources():
    digest = LegalExternalResearchDigestService().build_digest()
    signal_ids = {signal["id"] for signal in digest["signals"]}

    assert digest["status"] == "ready"
    assert {"legalbench", "cuad", "ragas", "crag", "frugalgpt"}.issubset(signal_ids)
    assert digest["summary"]["signal_count"] >= 5
    assert digest["summary"]["rag_source_count"] >= 2
    assert digest["summary"]["cheap_first_source_count"] == 1
    assert not SECRET_PATTERN.search(str(digest))


def test_legal_external_research_digest_maps_sources_to_local_evidence():
    digest = LegalExternalResearchDigestService().build_digest()

    assert all(signal["url"].startswith("https://") for signal in digest["signals"])
    assert all(signal["evidence_paths"] for signal in digest["signals"])
    assert all(signal["license_or_privacy_gate"] for signal in digest["signals"])
    assert any(
        signal["local_validation_path"] == "/api/v1/maintenance/legal-review-benchmark/result-archive"
        for signal in digest["signals"]
    )
    assert "raw model outputs" in " ".join(digest["release_guardrails"])


def test_legal_external_research_digest_prioritizes_cheap_first_work():
    digest = LegalExternalResearchDigestService().build_digest()
    queue = digest["implementation_queue"]

    assert queue[0]["signal_id"] == "frugalgpt"
    assert queue[0]["validation_target"].endswith("/result-archive")
    assert all(item["evidence_paths"] for item in queue)
    assert digest["low_resource_validation"]["default_fixture_limit"] == 2


def test_legal_external_research_digest_route_returns_digest():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/external-research-digest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["signal_count"] >= 5
