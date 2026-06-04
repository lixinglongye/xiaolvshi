import re

from services.continuous_update_ledger import (
    TARGET_CONTINUOUS_HOURS,
    TARGET_MEDIUM_LARGE_UPDATE_COUNT,
    ContinuousUpdateLedgerService,
)
from services.release_readiness import ReleaseReadinessService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_continuous_update_ledger_tracks_goal_without_claiming_completion():
    ledger = ContinuousUpdateLedgerService().build_ledger()

    assert ledger["status"] == "in_progress"
    assert ledger["goal"]["target_continuous_hours"] == TARGET_CONTINUOUS_HOURS
    assert ledger["goal"]["target_medium_large_update_count"] == TARGET_MEDIUM_LARGE_UPDATE_COUNT
    assert ledger["summary"]["completed_medium_large_update_count"] >= 10
    assert ledger["summary"]["completed_medium_large_update_count"] >= 63
    assert ledger["summary"]["completed_medium_large_update_count"] >= 66
    assert ledger["summary"]["completed_medium_large_update_count"] >= 69
    assert ledger["summary"]["completed_medium_large_update_count"] >= 73
    assert ledger["summary"]["completed_medium_large_update_count"] >= 77
    assert ledger["summary"]["completed_medium_large_update_count"] >= 81
    assert ledger["summary"]["completed_medium_large_update_count"] >= 86
    assert ledger["summary"]["completed_medium_large_update_count"] >= 88
    assert ledger["summary"]["completed_medium_large_update_count"] >= 89
    assert ledger["summary"]["completed_medium_large_update_count"] >= 92
    assert ledger["summary"]["completed_medium_large_update_count"] >= TARGET_MEDIUM_LARGE_UPDATE_COUNT
    assert ledger["summary"]["remaining_medium_large_update_count"] == 0
    assert ledger["summary"]["continuous_hours_verified"] == 0
    assert ledger["summary"]["completion_ready"] is False
    assert not SECRET_PATTERN.search(str(ledger))


def test_continuous_update_ledger_completed_entries_are_reviewable():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    completed = ledger["completed_updates"]
    categories = ledger["summary"]["category_counts"]

    assert completed
    assert categories["benchmark"] >= 5
    assert categories["model_ops"] >= 3
    assert categories["frontend_ui"] >= 2
    assert all(entry["size"] in {"medium", "large"} for entry in completed)
    assert all(entry["status"] == "shipped" for entry in completed)
    assert all(entry["evidence_paths"] for entry in completed)
    assert all(entry["release_gate_links"] for entry in completed)


def test_continuous_update_ledger_prioritizes_low_resource_next_work():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    queue_ids = {entry["id"] for entry in ledger["next_update_queue"]}
    completed_ids = {entry["id"] for entry in ledger["completed_updates"]}

    assert "cheap-first-result-archive" in completed_ids
    assert "gemini-price-refresh-monitor" in completed_ids
    assert "small-legal-document-corpus-expansion" in completed_ids
    assert "legal-rag-failure-fixtures" in completed_ids
    assert "model-cost-regression-snapshots" in completed_ids
    assert "twenty-four-hour-heartbeat-evidence" in completed_ids
    assert "continuous-session-evidence-validator" in completed_ids
    assert "continuous-session-timeline" in completed_ids
    assert "route-telemetry-persistence-plan" in completed_ids
    assert "legal-source-freshness-policy" in completed_ids
    assert "maintenance-dashboard-filtering" in completed_ids
    assert "frontend-local-run-review-form" in completed_ids
    assert "case-workbench-payload" in completed_ids
    assert "document-delivery-package-manifest" in completed_ids
    assert "case-role-permission-matrix" in completed_ids
    assert "billing-usage-quota-policy" in completed_ids
    assert "feedback-lifecycle-policy" in completed_ids
    assert "contract-clause-extraction-schema" in completed_ids
    assert "case-workbench-ui-binding" in completed_ids
    assert "legal-source-ingestion-metadata" in completed_ids
    assert "billing-quota-persistence" in completed_ids
    assert "document-version-diff-checklist" in completed_ids
    assert "case-workbench-persistence-plan" in completed_ids
    assert "legal-source-durable-index-plan" in completed_ids
    assert "billing-quota-migration-plan" in completed_ids
    assert "case-workbench-repository-implementation" in completed_ids
    assert "legal-source-index-repository" in completed_ids
    assert "billing-quota-repository-implementation" in completed_ids
    assert "case-workbench-runtime-binding" in completed_ids
    assert "legal-rag-query-index-binding" in completed_ids
    assert "billing-entitlement-repository-binding" in completed_ids
    assert "case-workbench-runtime-router" in completed_ids
    assert "legal-rag-index-route" in completed_ids
    assert "billing-quota-consumption-route" in completed_ids
    assert "frontend-runtime-api-client-bindings" in completed_ids
    assert "runtime-router-discovery-smoke" in completed_ids
    assert "case-workbench-frontend-state-events" in completed_ids
    assert "legal-rag-case-research-ui" in completed_ids
    assert "billing-usage-workspace-badge" in completed_ids
    assert "billing-report-preflight-route" in completed_ids
    assert "case-edit-runtime-event-binding" in completed_ids
    assert "legal-rag-research-context-cache" in completed_ids
    assert "document-generation-quota-consumption-attempt" in completed_ids
    assert "generated-documents-crud-quota-guard" in completed_ids
    assert "case-generation-quota-guard" in completed_ids
    assert "deep-review-document-generation-quota-guard" in completed_ids
    assert "legal-rag-selected-source-request-metadata" in completed_ids
    assert "legal-rag-selected-source-citation-validation" in completed_ids
    assert "legal-rag-selected-source-validation-maintenance-route" in completed_ids
    assert "billing-payment-reconciliation-policy" in completed_ids
    assert "case-task-runtime-notification-summary" in completed_ids
    assert "legal-document-benchmark-suite" in completed_ids
    assert "legal-benchmark-research-registry" in completed_ids
    assert "legal-benchmark-research-registry-ui" in completed_ids
    assert "deep-review-selected-source-binding" in completed_ids
    assert "quota-delivery-decision" in completed_ids
    assert "feedback-issue-cluster" in completed_ids
    assert "evidence-bundle-integrity" in completed_ids
    assert "privacy-retention-rules" in completed_ids
    assert "release-claim-compliance" in completed_ids
    assert "case-export-readiness" in completed_ids
    assert "admin-audit-policy" in completed_ids
    assert "continuous-session-evidence-validator" not in queue_ids
    assert "continuous-session-timeline" not in queue_ids
    assert "runtime-router-discovery-smoke" not in queue_ids
    assert "case-workbench-frontend-state-events" not in queue_ids
    assert "legal-rag-case-research-ui" not in queue_ids
    assert "billing-usage-workspace-badge" not in queue_ids
    assert "billing-report-preflight-route" not in queue_ids
    assert "case-edit-runtime-event-binding" not in queue_ids
    assert "legal-rag-research-context-cache" not in queue_ids
    assert "document-generation-quota-consumption-attempt" not in queue_ids
    assert "generated-documents-crud-quota-guard" not in queue_ids
    assert "case-generation-quota-guard" not in queue_ids
    assert "deep-review-document-generation-quota-guard" not in queue_ids
    assert "legal-rag-selected-source-request-metadata" not in queue_ids
    assert "legal-rag-selected-source-citation-validation" not in queue_ids
    assert "legal-rag-selected-source-validation-maintenance-route" not in queue_ids
    assert "billing-payment-reconciliation-policy" not in queue_ids
    assert "case-task-runtime-notification-summary" not in queue_ids
    assert "legal-document-benchmark-suite" not in queue_ids
    assert "legal-benchmark-research-registry" not in queue_ids
    assert "legal-benchmark-research-registry-ui" not in queue_ids
    assert "deep-review-selected-source-binding" not in queue_ids
    assert "quota-delivery-decision" not in queue_ids
    assert "feedback-issue-cluster" not in queue_ids
    assert "evidence-bundle-integrity" not in queue_ids
    assert "privacy-retention-rules" not in queue_ids
    assert "release-claim-compliance" not in queue_ids
    assert "case-export-readiness" not in queue_ids
    assert "admin-audit-policy" not in queue_ids
    assert ledger["low_resource_test_policy"]["max_parallel_requests"] == 1
    assert ledger["low_resource_test_policy"]["network_access"] == "disabled_by_default"
    assert "python -m pytest tests/test_continuous_session_evidence.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_continuous_session_timeline.py -q" in ledger["validation_commands"]


def test_continuous_update_ledger_is_optional_release_evidence():
    service = ReleaseReadinessService()
    ledger_commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "continuous-update-ledger"
    ]
    result = service.evaluate({"continuous-update-ledger": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "continuous-update-ledger")

    assert ledger_commands == [
        {
            "check_id": "continuous-update-ledger",
            "command": "python -m pytest tests/test_continuous_update_ledger.py -q",
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False


def test_continuous_update_ledger_route_returns_progress_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/continuous-update-ledger")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "in_progress"
    assert payload["data"]["summary"]["completion_ready"] is False
