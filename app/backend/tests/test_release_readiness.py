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


def test_runtime_router_discovery_smoke_is_optional_release_evidence():
    service = ReleaseReadinessService()
    discovery_commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "runtime-router-discovery-smoke"
    ]
    result = service.evaluate({"runtime-router-discovery-smoke": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "runtime-router-discovery-smoke")

    assert discovery_commands == [
        {
            "check_id": "runtime-router-discovery-smoke",
            "command": "python -m pytest tests/test_runtime_router_discovery.py -q",
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False
    assert "app/backend/tests/test_runtime_router_discovery.py" in check["evidence_paths"]


def test_frontend_runtime_ui_checks_are_optional_release_evidence():
    service = ReleaseReadinessService()
    commands = {
        item["check_id"]: item["command"]
        for item in service.default_validation_commands()
        if item["check_id"]
        in {
            "case-workbench-frontend-state-events",
            "legal-rag-case-research-ui",
            "billing-usage-workspace-badge",
        }
    }
    result = service.evaluate({
        "case-workbench-frontend-state-events": "not_run",
        "legal-rag-case-research-ui": "not_run",
        "billing-usage-workspace-badge": "not_run",
    })
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == {
        "case-workbench-frontend-state-events": "npm run typecheck",
        "legal-rag-case-research-ui": "npm run typecheck",
        "billing-usage-workspace-badge": "npm run typecheck",
    }
    assert checks["case-workbench-frontend-state-events"]["required"] is False
    assert checks["legal-rag-case-research-ui"]["required"] is False
    assert checks["billing-usage-workspace-badge"]["required"] is False
    assert checks["case-workbench-frontend-state-events"]["blocks_release"] is False
    assert checks["legal-rag-case-research-ui"]["blocks_release"] is False
    assert checks["billing-usage-workspace-badge"]["blocks_release"] is False
    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in checks["case-workbench-frontend-state-events"]["evidence_paths"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in checks["legal-rag-case-research-ui"]["evidence_paths"]
    assert "app/frontend/src/components/billing/BillingUsageBadge.tsx" in checks["billing-usage-workspace-badge"]["evidence_paths"]
