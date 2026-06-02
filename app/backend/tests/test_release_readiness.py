from services.release_readiness import ReleaseReadinessService


def test_release_readiness_requires_manual_validation_by_default():
    result = ReleaseReadinessService().evaluate()

    assert result["status"] == "manual_validation_required"
    assert result["release_allowed"] is False
    assert "backend-tests" in result["blocking_check_ids"]
    assert result["required_check_count"] > 0


def test_release_readiness_allows_release_candidate_when_required_checks_pass():
    service = ReleaseReadinessService()
    validation_results = {
        item["check_id"]: "pass"
        for item in service.default_validation_commands()
        if item["check_id"] != "oss-maintenance-evidence"
    }

    result = service.evaluate(validation_results)

    assert result["status"] == "ready_for_release_candidate"
    assert result["release_allowed"] is True
    assert result["blocking_check_ids"] == []


def test_release_readiness_blocks_failed_required_check():
    result = ReleaseReadinessService().evaluate(
        {
            "backend-tests": "pass",
            "frontend-typecheck": "fail",
            "frontend-build": "pass",
            "secret-scan": "pass",
            "deep-review-release-decision": "pass",
            "feedback-triage": "pass",
        }
    )

    assert result["status"] == "blocked"
    assert result["release_allowed"] is False
    assert result["failed_check_ids"] == ["frontend-typecheck"]
