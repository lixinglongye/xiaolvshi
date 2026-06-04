import json
import re

from services.git_history_evidence import GitHistoryEvidenceService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _commit_events():
    return [
        {"commit_hash": "a111111", "timestamp": "2026-06-03T00:00:00Z", "title": "Start maintenance session"},
        {"commit_hash": "b222222", "timestamp": "2026-06-03T05:00:00Z", "title": "Add low resource fixture checks"},
        {"commit_hash": "c333333", "timestamp": "2026-06-03T10:00:00Z", "title": "Improve maintenance evidence"},
        {"commit_hash": "d444444", "timestamp": "2026-06-03T15:00:00Z", "title": "Surface reviewer gates"},
        {"commit_hash": "e555555", "timestamp": "2026-06-03T20:00:00Z", "title": "Add timeline checks"},
        {"commit_hash": "f666666", "timestamp": "2026-06-04T01:10:00Z", "title": "Publish timeline evidence"},
    ]


def test_git_history_evidence_detects_reviewable_commit_cadence_without_goal_claim():
    evidence = GitHistoryEvidenceService().build_evidence({"events": _commit_events(), "max_allowed_gap_hours": 6})

    assert evidence["status"] == "cadence_reviewable"
    assert evidence["summary"]["source"] == "submitted_metadata"
    assert evidence["summary"]["commit_count"] == 6
    assert evidence["summary"]["longest_window_hours"] >= 24
    assert evidence["summary"]["commit_cadence_ready"] is True
    assert evidence["summary"]["ready_for_goal_claim"] is False
    assert any(blocker["id"] == "non-commit-validation-evidence-required" for blocker in evidence["blockers"])
    assert evidence["privacy_boundary"]["raw_patch_included"] is False


def test_git_history_evidence_flags_gaps_and_short_windows():
    evidence = GitHistoryEvidenceService().build_evidence(
        {
            "max_allowed_gap_hours": 4,
            "events": [
                {"commit_hash": "a111111", "timestamp": "2026-06-03T00:00:00Z", "title": "Start"},
                {"commit_hash": "b222222", "timestamp": "2026-06-03T08:00:00Z", "title": "Resume"},
            ],
        }
    )

    assert evidence["status"] == "collecting"
    assert evidence["summary"]["longest_window_hours"] == 0
    assert evidence["gap_analysis"][0]["gap_hours"] == 8
    assert any(blocker["id"] == "git-history-gap-exceeded" for blocker in evidence["blockers"])


def test_git_history_evidence_redacts_sensitive_titles_and_bad_hashes():
    evidence = GitHistoryEvidenceService().build_evidence(
        {
            "events": [
                {
                    "commit_hash": "not-a-hash",
                    "timestamp": "2026-06-03T00:00:00Z",
                    "title": "client@example.com password secret",
                }
            ]
        }
    )
    serialized = json.dumps(evidence, ensure_ascii=False)
    event = evidence["commit_events"][0]

    assert not SENSITIVE_PATTERN.search(serialized)
    assert event["title"] == "redacted"
    assert event["status"] == "fail"
    assert event["missing_fields"] == ["commit_hash"]


def test_git_history_evidence_route_returns_local_template_and_post_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/git-history-evidence")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["ready_for_goal_claim"] is False

    response = client.post(
        "/api/v1/maintenance/git-history-evidence",
        json={"events": _commit_events(), "max_allowed_gap_hours": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["commit_cadence_ready"] is True
