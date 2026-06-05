import json
import re

from services.continuous_update_ledger import (
    TARGET_CONTINUOUS_HOURS,
    TARGET_MEDIUM_LARGE_UPDATE_COUNT,
    ContinuousUpdateLedgerService,
)
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.release_readiness import ReleaseReadinessService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def _fixture_payload(fixture_id: str, route: str, text: str) -> dict:
    return {
        "phase": "cheap_first",
        "model": "gemini-2.5-flash-lite",
        "http_status": 200,
        "latency_ms": 800,
        "estimated_cost_usd": 0.0002,
        "gateway_response": {
            "model": "gemini-2.5-flash-lite",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "fixture_id": fixture_id,
                                "route": route,
                                "output_text": text,
                                "release_decision": "pass",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        },
    }


def _passing_fixture_review_payload() -> dict:
    fixtures = LegalReviewBenchmarkService().build_fixture_smoke_template()["fixtures"]
    return {
        "responses": {
            fixture["id"]: _fixture_payload(
                fixture["id"],
                fixture["expected_routes"][0],
                " ".join([*fixture["expected_signals"], *fixture["expected_tasks"]]),
            )
            for fixture in fixtures
        }
    }


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
    assert ledger["low_resource_fixture_evidence"]["status"] == "not_supplied"
    assert ledger["low_resource_fixture_evidence"]["summary"]["observed_fixture_count"] == 0
    assert ledger["low_resource_fixture_evidence"]["summary"]["updates_count_mutated"] is False
    assert ledger["low_resource_fixture_evidence"]["privacy_boundary"]["raw_gateway_response_included"] is False
    assert ledger["low_resource_test_policy"]["run_monitor_review_endpoint"] == (
        "/api/v1/maintenance/continuous-session-run-monitor"
    )


def test_continuous_update_ledger_summarizes_low_resource_fixture_evidence_without_mutating_goal():
    baseline = ContinuousUpdateLedgerService().build_ledger()
    ledger = ContinuousUpdateLedgerService().build_ledger(
        {"low_resource_fixture_review": _passing_fixture_review_payload()}
    )
    serialized = json.dumps(ledger, ensure_ascii=False)
    evidence = ledger["low_resource_fixture_evidence"]

    assert evidence["status"] == "ready"
    assert evidence["summary"]["review_status"] == "ready"
    assert evidence["summary"]["archive_status"] == "ready"
    assert evidence["summary"]["release_decision"] == "keep_cheap_first_defaults"
    assert evidence["summary"]["observed_fixture_count"] == 4
    assert evidence["summary"]["archived_fixture_count"] == 4
    assert evidence["summary"]["not_run_fixture_count"] == 0
    assert evidence["summary"]["redacted_response_count"] == 0
    assert evidence["summary"]["release_ready"] is True
    assert evidence["summary"]["updates_count_mutated"] is False
    assert ledger["summary"]["completed_medium_large_update_count"] == baseline["summary"]["completed_medium_large_update_count"]
    assert ledger["summary"]["completion_ready"] is False
    assert evidence["privacy_boundary"]["returns_archive_summaries_only"] is True
    assert "run_report_payload" not in serialized
    assert "output_text" not in serialized
    assert "choices" not in serialized


def test_continuous_update_ledger_blocks_failed_fixture_evidence_without_echoing_secret():
    secret = "s" + "k-" + ("D" * 24)
    ledger = ContinuousUpdateLedgerService().build_ledger(
        {
            "low_resource_fixture_review": {
                "fixture_id": "fixture-service-agreement-small",
                "model": "gemini-2.5-flash-lite",
                "gateway_response": {"choices": [{"message": {}}]},
                "http_status": 200,
                "note": f"{secret} raw fixture text should not appear",
            }
        }
    )
    serialized = json.dumps(ledger, ensure_ascii=False)
    evidence = ledger["low_resource_fixture_evidence"]

    assert evidence["status"] == "blocked"
    assert evidence["summary"]["review_status"] == "fail"
    assert evidence["summary"]["observed_fixture_count"] == 0
    assert evidence["summary"]["release_ready"] is False
    assert evidence["summary"]["updates_count_mutated"] is False
    assert ledger["summary"]["completion_ready"] is False
    assert secret not in serialized
    assert "raw fixture text should not appear" not in serialized
    assert "choices" not in serialized


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
    assert "model-price-refresh-monitor-readiness-ui" in completed_ids
    assert "gemini-newapi-model-selector" in completed_ids
    assert "gemini-newapi-selector-replay" in completed_ids
    assert "gemini-newapi-cheap-first-calibration" in completed_ids
    assert "modelops-cheap-first-calibration-review-form" in completed_ids
    assert "gemini-model-variant-matrix" in completed_ids
    assert "modelops-gemini-variant-review-form" in completed_ids
    assert "gemini-variant-model-list-ingestion" in completed_ids
    assert "modelops-load-performance-budget" in completed_ids
    assert "modelops-cheap-first-quality-budget" in completed_ids
    assert "small-legal-document-corpus-expansion" in completed_ids
    assert "legal-rag-failure-fixtures" in completed_ids
    assert "model-cost-regression-snapshots" in completed_ids
    assert "twenty-four-hour-heartbeat-evidence" in completed_ids
    assert "continuous-session-evidence-validator" in completed_ids
    assert "continuous-session-timeline" in completed_ids
    assert "continuous-session-run-monitor" in completed_ids
    assert "git-history-cadence-evidence" in completed_ids
    assert "validation-event-evidence-normalizer" in completed_ids
    assert "continuous-session-review-packet" in completed_ids
    assert "continuous-session-low-resource-fixture-review" in completed_ids
    assert "continuous-ledger-low-resource-fixture-evidence" in completed_ids
    assert "route-telemetry-persistence-plan" in completed_ids
    assert "route-telemetry-repository" in completed_ids
    assert "pdf-image-route-telemetry" in completed_ids
    assert "image-auto-route-default" in completed_ids
    assert "image-price-refresh-monitor" in completed_ids
    assert "image-gateway-health-plan" in completed_ids
    assert "image-gateway-probe-evaluation" in completed_ids
    assert "gateway-probe-secret-value-guard" in completed_ids
    assert "gateway-probe-readiness-binding" in completed_ids
    assert "gateway-probe-latest-evidence-store" in completed_ids
    assert "model-ops-readiness-required-optional-summary" in completed_ids
    assert "route-telemetry-ops-summary" in completed_ids
    assert "route-telemetry-triage-queue" in completed_ids
    assert "route-telemetry-remediation-plan" in completed_ids
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
    assert "legal-document-benchmark-coverage" in completed_ids
    assert "legal-document-benchmark-gap-fixtures" in completed_ids
    assert "legal-document-benchmark-coverage-ui" in completed_ids
    assert "legal-document-coverage-claim-policy" in completed_ids
    assert "legal-benchmark-research-registry" in completed_ids
    assert "legal-benchmark-research-registry-ui" in completed_ids
    assert "legal-adoption-research-bridge" in completed_ids
    assert "deep-review-selected-source-binding" in completed_ids
    assert "quota-delivery-decision" in completed_ids
    assert "feedback-issue-cluster" in completed_ids
    assert "evidence-bundle-integrity" in completed_ids
    assert "privacy-retention-rules" in completed_ids
    assert "release-claim-compliance" in completed_ids
    assert "case-export-readiness" in completed_ids
    assert "admin-audit-policy" in completed_ids
    assert "legal-fixture-regression-comparison" in completed_ids
    assert "user-need-benchmark-coverage" in completed_ids
    assert "user-need-public-benchmark-mapping" in completed_ids
    assert "continuous-session-evidence-validator" not in queue_ids
    assert "continuous-session-timeline" not in queue_ids
    assert "continuous-session-run-monitor" not in queue_ids
    assert "git-history-cadence-evidence" not in queue_ids
    assert "validation-event-evidence-normalizer" not in queue_ids
    assert "continuous-session-review-packet" not in queue_ids
    assert "continuous-session-low-resource-fixture-review" not in queue_ids
    assert "continuous-ledger-low-resource-fixture-evidence" not in queue_ids
    assert "gemini-newapi-model-selector" not in queue_ids
    assert "gemini-newapi-selector-replay" not in queue_ids
    assert "gemini-newapi-cheap-first-calibration" not in queue_ids
    assert "modelops-cheap-first-calibration-review-form" not in queue_ids
    assert "gemini-model-variant-matrix" not in queue_ids
    assert "modelops-gemini-variant-review-form" not in queue_ids
    assert "gemini-variant-model-list-ingestion" not in queue_ids
    assert "modelops-load-performance-budget" not in queue_ids
    assert "modelops-cheap-first-quality-budget" not in queue_ids
    assert "route-telemetry-repository" not in queue_ids
    assert "pdf-image-route-telemetry" not in queue_ids
    assert "image-auto-route-default" not in queue_ids
    assert "image-price-refresh-monitor" not in queue_ids
    assert "image-gateway-health-plan" not in queue_ids
    assert "image-gateway-probe-evaluation" not in queue_ids
    assert "gateway-probe-secret-value-guard" not in queue_ids
    assert "gateway-probe-readiness-binding" not in queue_ids
    assert "gateway-probe-latest-evidence-store" not in queue_ids
    assert "model-ops-readiness-required-optional-summary" not in queue_ids
    assert "route-telemetry-ops-summary" not in queue_ids
    assert "route-telemetry-triage-queue" not in queue_ids
    assert "route-telemetry-remediation-plan" not in queue_ids
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
    assert "legal-document-benchmark-coverage" not in queue_ids
    assert "legal-document-benchmark-gap-fixtures" not in queue_ids
    assert "legal-document-benchmark-coverage-ui" not in queue_ids
    assert "legal-document-coverage-claim-policy" not in queue_ids
    assert "legal-benchmark-research-registry" not in queue_ids
    assert "legal-benchmark-research-registry-ui" not in queue_ids
    assert "legal-adoption-research-bridge" not in queue_ids
    assert "deep-review-selected-source-binding" not in queue_ids
    assert "quota-delivery-decision" not in queue_ids
    assert "feedback-issue-cluster" not in queue_ids
    assert "evidence-bundle-integrity" not in queue_ids
    assert "privacy-retention-rules" not in queue_ids
    assert "release-claim-compliance" not in queue_ids
    assert "case-export-readiness" not in queue_ids
    assert "admin-audit-policy" not in queue_ids
    assert "legal-fixture-regression-comparison" not in queue_ids
    assert "user-need-benchmark-coverage" not in queue_ids
    assert "user-need-public-benchmark-mapping" not in queue_ids
    assert ledger["low_resource_test_policy"]["max_parallel_requests"] == 1
    assert ledger["low_resource_test_policy"]["network_access"] == "disabled_by_default"
    assert ledger["low_resource_test_policy"]["review_endpoint"] == "/api/v1/maintenance/legal-review-benchmark/local-run-review"
    assert ledger["low_resource_test_policy"]["archive_endpoint"] == "/api/v1/maintenance/legal-review-benchmark/result-archive"
    assert ledger["low_resource_test_policy"]["ledger_review_endpoint"] == "/api/v1/maintenance/continuous-update-ledger"
    assert "python -m pytest tests/test_continuous_session_evidence.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_continuous_session_timeline.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_continuous_session_run_monitor.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_continuous_session_review_packet.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_continuous_session_review_packet.py "
        "tests/test_legal_fixture_local_run_review.py tests/test_legal_fixture_response_normalizer.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_continuous_update_ledger.py tests/test_legal_fixture_local_run_review.py "
        "tests/test_legal_fixture_result_archive.py -q"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_git_history_evidence.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_validation_event_evidence.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_health_plan.py "
        "tests/test_model_catalog.py -q && cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_gemini_newapi_model_selector.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_gemini_newapi_selector_replay.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_gemini_model_variant_matrix.py tests/test_model_ops_readiness.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_gemini_model_variant_matrix.py -q && cd ../frontend && npm run typecheck && "
        "npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_performance_budget.py tests/test_model_ops_readiness.py -q && "
        "cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_model_price_refresh_monitor.py tests/test_model_ops_readiness.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_model_gateway_health_plan.py tests/test_model_price_refresh_monitor.py "
        "tests/test_model_ops_readiness.py -q && cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_price_refresh_monitor.py tests/test_model_ops_readiness.py -q && "
        "cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_aihub_runtime_routing.py tests/test_model_runtime_router.py "
        "tests/test_model_route_telemetry.py tests/test_route_telemetry_repository.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_catalog.py tests/test_model_budget.py tests/test_model_runtime_router.py "
        "tests/test_aihub_runtime_routing.py tests/test_model_configuration_audit.py tests/test_model_gateway_compatibility.py -q"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_route_telemetry_repository.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_route_telemetry_ops_summary.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_route_telemetry_triage_queue.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_route_telemetry_remediation_plan.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_document_benchmark_coverage.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_document_coverage_claim_policy.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_adoption_research_bridge.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_user_need_benchmark_coverage.py tests/test_legal_public_benchmark_sampler.py "
        "tests/test_gemini_newapi_cheap_first_calibration.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_route_quality_budget.py tests/test_model_ops_readiness.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )


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
    assert payload["data"]["low_resource_fixture_evidence"]["status"] == "not_supplied"

    reviewed = testclient.TestClient(app).post(
        "/api/v1/maintenance/continuous-update-ledger",
        json={"low_resource_fixture_review": _passing_fixture_review_payload()},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["low_resource_fixture_evidence"]["status"] == "ready"
    assert reviewed.json()["data"]["low_resource_fixture_evidence"]["summary"]["observed_fixture_count"] == 4
