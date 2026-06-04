import re

from services.legal_adoption_research_bridge import (
    LegalAdoptionResearchBridgeService,
    priority_band,
    priority_score,
)


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_legal_adoption_research_bridge_tracks_research_and_adoption_sources():
    bridge = LegalAdoptionResearchBridgeService().build_bridge()
    source_ids = {source["id"] for source in bridge["method"]["input_sources"]}

    assert bridge["status"] == "ready"
    assert {
        "legalbench",
        "frugalgpt",
        "ragas",
        "crag",
        "tr-future-professionals-2025",
        "tr-ai-ethics-2025",
    }.issubset(source_ids)
    assert bridge["summary"]["source_count"] >= 6
    assert bridge["summary"]["action_count"] >= 5
    assert bridge["summary"]["research_digest_signal_count"] >= 5
    assert bridge["summary"]["governance_action_count"] >= 1
    assert bridge["summary"]["legal_benchmark_action_count"] >= 1
    assert not SECRET_PATTERN.search(str(bridge))


def test_legal_adoption_research_bridge_maps_to_existing_needs_and_gaps():
    bridge = LegalAdoptionResearchBridgeService().build_bridge()

    assert bridge["summary"]["unmapped_need_ids"] == []
    assert bridge["summary"]["unmapped_gap_ids"] == []
    assert all(action["user_need_ids"] for action in bridge["actions"])
    assert all(action["product_gap_ids"] for action in bridge["actions"])
    assert all(action["release_gate_links"] for action in bridge["actions"])
    assert all(action["evidence_paths"] for action in bridge["actions"])
    assert any("privacy-safe-upload" in action["user_need_ids"] for action in bridge["actions"])
    assert any("model-cost-ops" in action["product_gap_ids"] for action in bridge["actions"])


def test_legal_adoption_research_bridge_prioritizes_cheap_first_and_validation_queue():
    bridge = LegalAdoptionResearchBridgeService().build_bridge()
    queue = bridge["implementation_queue"]

    assert queue[0]["action_id"] == "cheap-first-governed-review-loop"
    assert queue[0]["validation_commands"]
    assert bridge["summary"]["cheap_first_action_count"] >= 3
    assert any(
        "tests/test_gemini_newapi_model_selector.py" in command
        for command in queue[0]["validation_commands"]
    )
    assert any("Gemini/NewAPI" in guardrail for guardrail in bridge["release_guardrails"])


def test_legal_adoption_research_bridge_keeps_survey_intake_metadata_only():
    bridge = LegalAdoptionResearchBridgeService().build_bridge()

    assert bridge["survey_intake_questions"]
    assert all(question["maps_to_need_ids"] for question in bridge["survey_intake_questions"])
    privacy_text = str(bridge["survey_intake_questions"]) + bridge["privacy_note"]
    assert "free text" in bridge["privacy_note"]
    assert "client documents" in bridge["privacy_note"]
    assert "model outputs" in bridge["privacy_note"]
    assert "API keys" in bridge["privacy_note"]
    assert "Capture category" in privacy_text or "Capture task type" in privacy_text


def test_priority_score_and_band_are_bounded():
    assert priority_score(impact=10, urgency=10, effort=0, confidence=10, low_cost_fit=10) == 100
    assert priority_score(impact=1, urgency=1, effort=10, confidence=1, low_cost_fit=1) == 0
    assert priority_band(70) == "high"
    assert priority_band(45) == "medium"
    assert priority_band(44) == "low"


def test_legal_adoption_research_bridge_route_returns_bridge():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/adoption-research-bridge")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["action_count"] >= 5
