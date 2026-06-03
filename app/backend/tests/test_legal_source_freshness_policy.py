import re
from datetime import date

from services.legal_source_freshness_policy import LegalSourceFreshnessPolicyService


def test_legal_source_freshness_policy_default_sources_are_ready():
    payload = LegalSourceFreshnessPolicyService().build_policy()

    assert payload["status"] == "ready"
    assert payload["summary"]["source_count"] >= 3
    assert payload["summary"]["blocked_count"] == 0
    assert payload["summary"]["reference_date"] == "2026-06-04"
    assert all(review["status"] == "pass" for review in payload["source_reviews"])
    assert any(rule["source_type"] == "statute" for rule in payload["freshness_rules"])


def test_legal_source_freshness_policy_blocks_stale_or_missing_metadata():
    payload = LegalSourceFreshnessPolicyService().build_policy(
        [
            {
                "id": "old-source",
                "title": "Old local rule",
                "source_type": "regulation",
                "jurisdiction": "CN-Shanghai",
                "effective_date": "2020-01-01",
                "last_verified_at": "2024-01-01",
                "citation": "Synthetic citation",
            },
            {
                "id": "missing-fields",
                "title": "Missing jurisdiction and citation",
                "source_type": "unknown",
                "effective_date": "",
                "last_verified_at": "",
                "citation": "",
            },
        ]
    )

    assert payload["status"] == "blocked"
    assert payload["summary"]["blocked_count"] == 2
    assert "old-source" in payload["summary"]["stale_source_ids"]
    assert "missing-fields" in payload["summary"]["missing_jurisdiction_ids"]
    assert any("Block automatic legal answers" in action for action in payload["recommended_actions"])


def test_legal_source_freshness_policy_warns_when_review_is_due():
    payload = LegalSourceFreshnessPolicyService().build_policy(
        [
            {
                "id": "review-due",
                "title": "Review due statute",
                "source_type": "statute",
                "jurisdiction": "CN-National",
                "effective_date": "2022-01-01",
                "last_verified_at": "2025-07-10",
                "citation": "Synthetic citation",
            }
        ],
        reference_date=date(2026, 6, 4),
    )

    assert payload["status"] == "review_recommended"
    review = payload["source_reviews"][0]
    assert review["status"] == "warn"
    assert "freshness_review_due" in review["flags"]


def test_legal_source_freshness_policy_sanitizes_sensitive_metadata():
    payload = LegalSourceFreshnessPolicyService().build_policy(
        [
            {
                "id": "source-with-email",
                "title": "Contact person@example.com password",
                "source_type": "statute",
                "jurisdiction": "CN-National",
                "effective_date": "2021-01-01",
                "last_verified_at": "2026-05-01",
                "citation": "Synthetic sk-" + "A" * 24,
            }
        ]
    )

    text = str(payload)
    assert "[redacted]" in text
    assert "person@example.com" not in text
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", text)


def test_legal_source_freshness_policy_route_can_be_added_later_without_state():
    payload = LegalSourceFreshnessPolicyService().build_policy()

    assert "validation_commands" in payload
    assert any("test_legal_source_freshness_policy.py" in command for command in payload["validation_commands"])
    assert "privacy" in payload["privacy_note"].lower()


def test_legal_source_freshness_policy_route_returns_default_and_custom_reviews():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-review-benchmark/source-freshness-policy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"

    custom = client.post(
        "/api/v1/maintenance/legal-review-benchmark/source-freshness-policy",
        json={
            "sources": [
                {
                    "id": "stale-template",
                    "title": "Stale template",
                    "source_type": "template",
                    "jurisdiction": "CN-Beijing",
                    "effective_date": "2022-01-01",
                    "last_verified_at": "2024-01-01",
                    "citation": "Synthetic citation",
                }
            ]
        },
    )

    assert custom.status_code == 200
    assert custom.json()["data"]["status"] == "blocked"
