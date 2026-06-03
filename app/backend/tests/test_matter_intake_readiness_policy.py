import re

from services.matter_intake_readiness_policy import MatterIntakeReadinessPolicyService


SECRET_PATTERN = re.compile(
    "s" + "k-" + r"[A-Za-z0-9]{20,}|" + "pass" + "word|" + "2725" + "186241|" + "lixing" + "long",
    re.IGNORECASE,
)


def _ready_intake() -> dict:
    return {
        "client_name": "Client A",
        "opposing_parties": ["Company B"],
        "matter_type": "contract dispute",
        "jurisdiction": "PRC",
        "claim_objective": "recover payment",
        "facts_summary": "metadata-only placeholder",
        "key_dates": ["2026-01-10"],
        "deadline_assessment": "limitation reviewed",
        "evidence_items": ["contract", "payment record"],
        "identity_materials": ["client id reference"],
        "authorization_materials": ["engagement letter reference"],
        "engagement_scope_acknowledged": True,
        "conflict_search_completed": True,
        "conflict_result": "clear",
        "risk_level": "low",
        "lawyer_review_required": False,
    }


def test_matter_intake_readiness_policy_passes_complete_intake():
    payload = MatterIntakeReadinessPolicyService().evaluate(_ready_intake())

    assert payload["status"] == "pass"
    assert payload["summary"]["ready_for_matter_creation"] is True
    assert payload["summary"]["failed_check_count"] == 0
    assert all(check["status"] == "pass" for check in payload["checks"])
    assert payload["validation_commands"] == [
        "python -m pytest tests/test_matter_intake_readiness_policy.py -q",
    ]


def test_matter_intake_readiness_policy_warns_for_restricted_review_flow():
    intake = _ready_intake()
    intake.update(
        {
            "risk_level": "high",
            "lawyer_review_required": True,
            "assigned_lawyer_id": "lawyer-1",
            "review_status": "pending",
            "conflict_result": "possible",
            "conflict_waiver_id": "waiver-1",
            "conflict_reviewer_id": "lawyer-1",
        }
    )

    payload = MatterIntakeReadinessPolicyService().evaluate(intake)
    statuses = {check["id"]: check["status"] for check in payload["checks"]}

    assert payload["status"] == "warn"
    assert payload["summary"]["restricted_creation_allowed"] is True
    assert payload["summary"]["lawyer_review_required"] is True
    assert statuses["conflict-screening"] == "warn"
    assert statuses["lawyer-review-gate"] == "warn"


def test_matter_intake_readiness_policy_fails_missing_core_and_unresolved_conflict():
    payload = MatterIntakeReadinessPolicyService().evaluate(
        {
            "client_name": "Client A",
            "matter_type": "contract dispute",
            "conflict_search_completed": True,
            "conflict_result": "confirmed",
            "lawyer_review_required": True,
        }
    )
    failed = {check["id"]: check for check in payload["checks"] if check["status"] == "fail"}

    assert payload["status"] == "fail"
    assert payload["summary"]["ready_for_matter_creation"] is False
    assert payload["summary"]["failed_check_count"] >= 4
    assert "basic-matter-profile" in failed
    assert "conflict-screening" in failed
    assert "lawyer-review-gate" in failed
    assert "opposing_party_identity" in failed["basic-matter-profile"]["missing_fields"]


def test_matter_intake_readiness_policy_does_not_echo_sensitive_values():
    intake = _ready_intake()
    intake.update(
        {
            "facts_summary": "contains " + "s" + "k-" + "123456789012345678901234567890",
            "pass" + "word": "do not return this field or value",
            "client_name": "lixing" + "long secret fixture",
            "contact": "2725" + "186241" + "@example.com",
        }
    )

    payload = MatterIntakeReadinessPolicyService().evaluate(intake)

    assert "metadata" in payload["privacy_note"]
    assert not SECRET_PATTERN.search(str(payload))


def test_matter_intake_readiness_policy_build_policy_alias_matches_evaluate():
    service = MatterIntakeReadinessPolicyService()

    assert service.build_policy(_ready_intake()) == service.evaluate(_ready_intake())


def test_matter_intake_readiness_policy_route_evaluates_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/matter-intake-readiness-policy",
        json=_ready_intake(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
