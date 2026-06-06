from services.user_needs_radar import UserNeedsRadarService, priority_band, priority_score


def test_user_needs_radar_prioritizes_traceable_review_and_privacy():
    radar = UserNeedsRadarService().build_radar()

    assert radar["status"] == "ready"
    assert radar["summary"]["need_count"] >= 6
    assert radar["summary"]["high_priority_count"] >= 3
    assert "traceable-legal-review" in radar["summary"]["top_need_ids"]
    assert "privacy-safe-upload" in radar["summary"]["top_need_ids"]
    assert all(need["evidence_paths"] for need in radar["needs"])


def test_user_needs_radar_tracks_research_and_internal_sources():
    radar = UserNeedsRadarService().build_radar()
    source_ids = {source["id"] for source in radar["method"]["input_sources"]}

    assert {
        "legalbench",
        "legalbench-rag",
        "lexeval",
        "casegen",
        "stanford-legal-rag",
        "internal-feedback-triage",
        "legal-research-backlog",
    }.issubset(source_ids)
    assert radar["summary"]["source_coverage"]["legalbench"] >= 1
    assert radar["summary"]["source_coverage"]["legalbench-rag"] >= 2
    assert radar["summary"]["source_coverage"]["lexeval"] >= 2
    assert radar["summary"]["source_coverage"]["casegen"] >= 2
    assert radar["summary"]["source_coverage"]["internal-feedback-triage"] >= 3
    assert radar["summary"]["source_coverage"]["legal-research-backlog"] >= 3
    assert "sk-" not in str(radar)


def test_user_needs_radar_builds_release_planning_roadmap():
    radar = UserNeedsRadarService().build_radar()

    assert [phase["phase"] for phase in radar["roadmap"]] == ["stabilize", "measure"]
    assert radar["roadmap"][0]["focus_need_ids"]
    assert any("release gates" in criterion for criterion in radar["roadmap"][0]["exit_criteria"])
    assert any("Feedback" in action or "feedback" in action for action in radar["maintenance_actions"])


def test_priority_score_and_band_are_bounded():
    assert priority_score(10, 0, 10) == 100
    assert priority_score(1, 10, 1) == 0
    assert priority_band(50) == "high"
    assert priority_band(35) == "medium"
    assert priority_band(34) == "low"


def test_user_needs_route_returns_radar():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/user-needs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["need_count"] >= 6
