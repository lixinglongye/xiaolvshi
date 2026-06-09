import json
import re

from services.model_ops_gemini_official_model_family_roadmap import (
    ModelOpsGeminiOfficialModelFamilyRoadmapService,
)


SENSITIVE_PATTERN = re.compile(
    r"authorization|password|secret_value|credential_value|api[_-]?key_value|bearer[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_gemini_official_model_family_roadmap_tracks_coverage_and_gaps():
    roadmap = ModelOpsGeminiOfficialModelFamilyRoadmapService().build_roadmap()
    family_rows = {row["family_id"]: row for row in roadmap["family_rows"]}
    cheap_first_rows = {row["task"]: row for row in roadmap["cheap_first_evidence_rows"]}

    assert roadmap["id"] == "modelops-gemini-official-model-family-roadmap-evidence"
    assert roadmap["status"] == "review_required"
    assert roadmap["summary"]["official_family_count"] == 7
    assert roadmap["summary"]["covered_family_count"] == 2
    assert roadmap["summary"]["review_family_count"] == 4
    assert roadmap["summary"]["gap_family_count"] == 1
    assert roadmap["summary"]["cheap_first_candidate_count"] == 6
    assert roadmap["blocking_check_ids"] == []
    assert "official-family-gap-queue" in roadmap["warning_check_ids"]
    assert "preview-and-review-family-boundary" in roadmap["warning_check_ids"]

    assert family_rows["gemini-2.5-text"]["coverage_status"] == "covered"
    assert family_rows["gemini-2.5-text"]["preferred_cheap_first_model"] == "gemini-2.5-flash-lite"
    assert family_rows["gemini-2.5-text"]["high_frequency_default_allowed"] is True
    assert family_rows["gemini-3-text"]["coverage_status"] == "review_required"
    assert "gemini-3.1-pro-preview-customtools" in family_rows["gemini-3-text"]["catalog_models"]
    assert family_rows["gemini-3-text"]["fallback_model"] == "gemini-3.5-flash"
    assert family_rows["gemini-3-text"]["fallback_model_catalog_status"] == "stable"
    assert family_rows["gemini-image"]["route_policy"] == "explicit_media_route_only"
    assert family_rows["gemini-image"]["coverage_status"] == "covered"
    assert family_rows["gemini-image"]["premium_model_catalog_status"] == "stable"
    assert family_rows["gemini-live-audio"]["coverage_status"] == "review_required"
    assert family_rows["gemini-live-audio"]["catalog_model_count"] == 2
    assert family_rows["veo-video"]["coverage_status"] == "review_required"
    assert family_rows["veo-video"]["catalog_model_count"] == 3
    assert family_rows["gemini-embedding"]["coverage_status"] == "gap"
    assert family_rows["gemini-tts"]["coverage_status"] == "review_required"
    assert family_rows["gemini-tts"]["catalog_model_count"] == 3

    for task in ("cheap", "fast", "classification", "ocr", "agentic", "grounded-research"):
        assert cheap_first_rows[task]["cheap_first_allowed"] is True
        assert "flash-lite" in cheap_first_rows[task]["canonical_model"]


def test_gemini_official_model_family_roadmap_boundaries_are_metadata_only():
    roadmap = ModelOpsGeminiOfficialModelFamilyRoadmapService().build_roadmap()
    serialized = json.dumps(roadmap, ensure_ascii=False)

    assert roadmap["privacy_boundary"]["metadata_only"] is True
    assert roadmap["privacy_boundary"]["gateway_called"] is False
    assert roadmap["privacy_boundary"]["network_called"] is False
    assert roadmap["privacy_boundary"]["configuration_written"] is False
    assert roadmap["privacy_boundary"]["credentials_included"] is False
    assert roadmap["privacy_boundary"]["request_bodies_included"] is False
    assert roadmap["privacy_boundary"]["response_bodies_included"] is False
    assert roadmap["privacy_boundary"]["raw_payload_echoed"] is False
    assert roadmap["privacy_boundary"]["raw_model_output_included"] is False
    assert roadmap["claim_boundary"]["all_gemini_models_supported_claimed"] is False
    assert roadmap["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert roadmap["claim_boundary"]["automatic_default_change_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_official_model_family_roadmap_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-official-model-family-roadmap-evidence")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["official_family_count"] == 7
    assert payload["summary"]["network_called"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["gemini_official_model_family_roadmap_evidence"]["id"]
        == "modelops-gemini-official-model-family-roadmap-evidence"
    )
    assert any(
        check["source_key"] == "gemini_official_model_family_roadmap_evidence"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
