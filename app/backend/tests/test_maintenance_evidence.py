from services.maintenance_evidence import MaintenanceEvidenceService, REPOSITORY_URL


def test_maintenance_profile_links_reviewable_evidence():
    profile = MaintenanceEvidenceService().build_profile("en")

    assert profile["project"]["repository_url"] == REPOSITORY_URL
    assert profile["maintainer_role"] == "primary_project_maintainer"
    assert profile["evidence_score"] >= 80
    assert profile["signals"]
    assert all(signal["evidence_paths"] for signal in profile["signals"])
    assert "release_decision" in " ".join(
        path for signal in profile["signals"] for path in signal["evidence_paths"]
    )


def test_form_answers_are_application_safe_and_bilingual():
    service = MaintenanceEvidenceService()

    english = service.build_form_answer("en")
    chinese = service.build_form_answer("zh")

    assert REPOSITORY_URL in english
    assert REPOSITORY_URL in chinese
    assert "third-party PR" not in english
    assert "大量外部 PR" not in chinese
    assert "sk-" not in english + chinese
    assert "维护者" in chinese


def test_unknown_language_falls_back_to_english():
    service = MaintenanceEvidenceService()

    assert service.build_profile("fr")["form_answer"] == service.build_form_answer("en")


def test_maintenance_evidence_route_returns_bilingual_form_answer():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/oss-evidence?language=zh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["project"]["repository_url"] == REPOSITORY_URL
    assert "维护者" in payload["data"]["form_answer"]
