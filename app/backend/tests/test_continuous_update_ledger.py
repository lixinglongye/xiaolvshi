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
    assert "gemini-newapi-model-alias-matrix" in completed_ids
    assert "gemini-newapi-selector-replay" in completed_ids
    assert "gemini-newapi-cheap-first-calibration" in completed_ids
    assert "modelops-cheap-first-calibration-review-form" in completed_ids
    assert "gemini-model-variant-matrix" in completed_ids
    assert "modelops-gemini-variant-review-form" in completed_ids
    assert "gemini-variant-model-list-ingestion" in completed_ids
    assert "modelops-load-performance-budget" in completed_ids
    assert "modelops-performance-observation-review" in completed_ids
    assert "modelops-cheap-first-quality-budget" in completed_ids
    assert "gemini-catalog-source-audit" in completed_ids
    assert "model-catalog-candidate-patch-plan" in completed_ids
    assert "modelops-cheap-first-release-decision" in completed_ids
    assert "modelops-default-change-queue" in completed_ids
    assert "modelops-cheap-first-priority-queue" in completed_ids
    assert "modelops-cheap-first-maintainer-execution-checklist" in completed_ids
    assert "modelops-cheap-first-canary-plan" in completed_ids
    assert "modelops-cheap-first-canary-observation-review" in completed_ids
    assert "modelops-cheap-first-canary-promotion-decision" in completed_ids
    assert "modelops-cheap-first-canary-approval-packet" in completed_ids
    assert "modelops-cheap-first-canary-rollback-drill" in completed_ids
    assert "modelops-cheap-first-canary-change-manifest" in completed_ids
    assert "modelops-gemini-cheap-first-coverage-gate" in completed_ids
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in completed_ids
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in completed_ids
    assert "modelops-agentic-grounded-defaults" in completed_ids
    assert "modelops-default-template-alignment" in completed_ids
    assert "modelops-gemini-default-change-review" in completed_ids
    assert "modelops-gemini-default-cost-impact" in completed_ids
    assert "modelops-observed-gemini-model-intake-queue" in completed_ids
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
    assert "feedback-capture-plan" in completed_ids
    assert "model-default-candidate-selector" in completed_ids
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
    assert "case-workbench-risk-refresh-plan" in completed_ids
    assert "legal-rag-index-route" in completed_ids
    assert "billing-quota-consumption-route" in completed_ids
    assert "frontend-runtime-api-client-bindings" in completed_ids
    assert "runtime-router-discovery-smoke" in completed_ids
    assert "case-workbench-frontend-state-events" in completed_ids
    assert "legal-rag-case-research-ui" in completed_ids
    assert "case-export-readiness-download-gate" in completed_ids
    assert "billing-usage-workspace-badge" in completed_ids
    assert "billing-report-preflight-route" in completed_ids
    assert "case-edit-runtime-event-binding" in completed_ids
    assert "legal-rag-research-context-cache" in completed_ids
    assert "document-generation-quota-consumption-attempt" in completed_ids
    assert "generated-documents-crud-quota-guard" in completed_ids
    assert "case-generation-quota-guard" in completed_ids
    assert "case-evidence-catalog-export-preflight" in completed_ids
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
    assert "legal-benchmark-research-refresh" in completed_ids
    assert "model-route-legal-benchmark-risk-queue" in completed_ids
    assert "legal-benchmark-research-registry-ui" in completed_ids
    assert "legal-rag-abstention-escalation-gate" in completed_ids
    assert "legal-rag-retrieval-diagnostics-gate" in completed_ids
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
    assert "user-need-implementation-priority-queue" in completed_ids
    assert "continuous-session-evidence-validator" not in queue_ids
    assert "continuous-session-timeline" not in queue_ids
    assert "continuous-session-run-monitor" not in queue_ids
    assert "git-history-cadence-evidence" not in queue_ids
    assert "validation-event-evidence-normalizer" not in queue_ids
    assert "continuous-session-review-packet" not in queue_ids
    assert "continuous-session-low-resource-fixture-review" not in queue_ids
    assert "continuous-ledger-low-resource-fixture-evidence" not in queue_ids
    assert "gemini-newapi-model-selector" not in queue_ids
    assert "gemini-newapi-model-alias-matrix" not in queue_ids
    assert "gemini-newapi-selector-replay" not in queue_ids
    assert "gemini-newapi-cheap-first-calibration" not in queue_ids
    assert "modelops-cheap-first-calibration-review-form" not in queue_ids
    assert "gemini-model-variant-matrix" not in queue_ids
    assert "modelops-gemini-variant-review-form" not in queue_ids
    assert "gemini-variant-model-list-ingestion" not in queue_ids
    assert "modelops-load-performance-budget" not in queue_ids
    assert "modelops-performance-observation-review" not in queue_ids
    assert "modelops-cheap-first-quality-budget" not in queue_ids
    assert "gemini-catalog-source-audit" not in queue_ids
    assert "model-catalog-candidate-patch-plan" not in queue_ids
    assert "modelops-cheap-first-release-decision" not in queue_ids
    assert "modelops-default-change-queue" not in queue_ids
    assert "modelops-cheap-first-priority-queue" not in queue_ids
    assert "modelops-cheap-first-maintainer-execution-checklist" not in queue_ids
    assert "modelops-cheap-first-canary-plan" not in queue_ids
    assert "modelops-cheap-first-canary-observation-review" not in queue_ids
    assert "modelops-cheap-first-canary-promotion-decision" not in queue_ids
    assert "modelops-cheap-first-canary-approval-packet" not in queue_ids
    assert "modelops-cheap-first-canary-rollback-drill" not in queue_ids
    assert "modelops-cheap-first-canary-change-manifest" not in queue_ids
    assert "modelops-gemini-cheap-first-coverage-gate" not in queue_ids
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" not in queue_ids
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" not in queue_ids
    assert "modelops-agentic-grounded-defaults" not in queue_ids
    assert "modelops-default-template-alignment" not in queue_ids
    assert "modelops-gemini-default-change-review" not in queue_ids
    assert "modelops-gemini-default-cost-impact" not in queue_ids
    assert "modelops-observed-gemini-model-intake-queue" not in queue_ids
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
    assert "case-export-readiness-download-gate" not in queue_ids
    assert "billing-usage-workspace-badge" not in queue_ids
    assert "billing-report-preflight-route" not in queue_ids
    assert "case-edit-runtime-event-binding" not in queue_ids
    assert "legal-rag-research-context-cache" not in queue_ids
    assert "document-generation-quota-consumption-attempt" not in queue_ids
    assert "generated-documents-crud-quota-guard" not in queue_ids
    assert "case-generation-quota-guard" not in queue_ids
    assert "case-evidence-catalog-export-preflight" not in queue_ids
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
    assert "legal-benchmark-research-refresh" not in queue_ids
    assert "model-route-legal-benchmark-risk-queue" not in queue_ids
    assert "legal-benchmark-research-registry-ui" not in queue_ids
    assert "legal-rag-abstention-escalation-gate" not in queue_ids
    assert "legal-rag-retrieval-diagnostics-gate" not in queue_ids
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
    assert "user-need-implementation-priority-queue" not in queue_ids
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
    assert (
        "python -m pytest tests/test_gemini_newapi_model_alias_matrix.py "
        "tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py -q"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_gemini_newapi_selector_replay.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_gemini_model_variant_matrix.py tests/test_model_ops_readiness.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_gemini_model_variant_matrix.py -q && cd ../frontend && npm run typecheck && "
        "npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_performance_budget.py tests/test_model_ops_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
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
    assert (
        "python -m pytest tests/test_legal_benchmark_research_refresh.py "
        "tests/test_legal_benchmark_research_registry.py tests/test_legal_adoption_research_bridge.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_route_legal_benchmark_risk_queue.py "
        "tests/test_gemini_newapi_cheap_first_calibration.py tests/test_user_need_benchmark_coverage.py "
        "tests/test_legal_benchmark_research_refresh.py -q"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_legal_adoption_research_bridge.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_user_need_benchmark_coverage.py tests/test_legal_public_benchmark_sampler.py "
        "tests/test_gemini_newapi_cheap_first_calibration.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_route_quality_budget.py tests/test_model_ops_readiness.py "
        "tests/test_model_default_candidate_selector.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_ops_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_catalog_candidate_patch_plan.py "
        "tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_model_gateway_probe_evaluation.py "
        "tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && "
        "npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_release_decision.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_priority_queue.py tests/test_model_ops_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_maintainer_execution_checklist.py "
        "tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && "
        "npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_plan.py tests/test_model_ops_default_change_queue.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_observation.py "
        "tests/test_model_ops_cheap_first_canary_plan.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_promotion_decision.py "
        "tests/test_model_ops_cheap_first_canary_observation.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_approval_packet.py "
        "tests/test_model_ops_cheap_first_canary_promotion_decision.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_rollback_drill.py "
        "tests/test_model_ops_cheap_first_canary_approval_packet.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py "
        "tests/test_model_ops_cheap_first_canary_rollback_drill.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_modelops_gemini_cheap_first_coverage_gate.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py -q"
        in ledger["validation_commands"]
    )
    alias_matrix_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gemini-newapi-model-alias-matrix"
    )
    assert alias_matrix_entry["size"] == "medium"
    assert alias_matrix_entry["status"] == "shipped"
    assert "canonical, models/, google/, yibu/" in alias_matrix_entry["impact"]
    assert "premium exceptions" in alias_matrix_entry["impact"]
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in alias_matrix_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_model_alias_matrix.py" in alias_matrix_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_MODEL_ALIAS_MATRIX.md" in alias_matrix_entry["evidence_paths"]
    assert "gemini-newapi-model-alias-matrix" in alias_matrix_entry["release_gate_links"]
    assert "gemini-newapi-model-selector" in alias_matrix_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in alias_matrix_entry["release_gate_links"]
    coverage_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-gemini-cheap-first-coverage-gate"
    )
    assert coverage_gate_entry["size"] == "medium"
    assert coverage_gate_entry["status"] == "shipped"
    assert "app/backend/services/modelops_gemini_cheap_first_coverage_gate.py" in coverage_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_gemini_cheap_first_coverage_gate.py" in coverage_gate_entry["evidence_paths"]
    assert "docs/MODELOPS_GEMINI_CHEAP_FIRST_COVERAGE_GATE.md" in coverage_gate_entry["evidence_paths"]
    assert "modelops-gemini-cheap-first-coverage-gate" in coverage_gate_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in coverage_gate_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in coverage_gate_entry["release_gate_links"]
    assert "model-gateway-compatibility" in coverage_gate_entry["release_gate_links"]
    assert "model-lifecycle-policy" in coverage_gate_entry["release_gate_links"]
    assert "model-reasoning-policy" in coverage_gate_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in coverage_gate_entry["release_gate_links"]
    assert "Gemini-like defaults" in coverage_gate_entry["impact"]
    assert "cheap-first alignment" in coverage_gate_entry["impact"]
    assert "premium exceptions" in coverage_gate_entry["impact"]
    assert "unknown model handling" in coverage_gate_entry["impact"]
    assert "pricing" in coverage_gate_entry["impact"]
    assert "lifecycle" in coverage_gate_entry["impact"]
    assert "reasoning" in coverage_gate_entry["impact"]
    assert "gateway compatibility" in coverage_gate_entry["impact"]
    assert "claim/privacy boundaries" in coverage_gate_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in coverage_gate_entry["impact"]
    assert "raw prompts" in coverage_gate_entry["impact"]
    assert "payloads" in coverage_gate_entry["impact"]
    assert "model outputs" in coverage_gate_entry["impact"]
    assert "credentials" in coverage_gate_entry["impact"]
    legal_fixture_gate_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-cheap-first-benchmark-gate"
    )
    assert legal_fixture_gate_entry["size"] == "medium"
    assert legal_fixture_gate_entry["status"] == "shipped"
    assert "small legal-document cheap-first Gemini benchmark/risk gate evidence" in legal_fixture_gate_entry["impact"]
    assert "redacted fixture ids" in legal_fixture_gate_entry["impact"]
    assert "document case ids" in legal_fixture_gate_entry["impact"]
    assert "expected issue counts" in legal_fixture_gate_entry["impact"]
    assert "cost metadata" in legal_fixture_gate_entry["impact"]
    assert "document benchmark pass/fail counts" in legal_fixture_gate_entry["impact"]
    assert "coverage-gap counts" in legal_fixture_gate_entry["impact"]
    assert "escalation metadata" in legal_fixture_gate_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in legal_fixture_gate_entry["impact"]
    assert "real legal text" in legal_fixture_gate_entry["impact"]
    assert "fixture snippets" in legal_fixture_gate_entry["impact"]
    assert "generated document text" in legal_fixture_gate_entry["impact"]
    assert "prompts" in legal_fixture_gate_entry["impact"]
    assert "model outputs" in legal_fixture_gate_entry["impact"]
    assert "credentials" in legal_fixture_gate_entry["impact"]
    assert "emails" in legal_fixture_gate_entry["impact"]
    assert "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in legal_fixture_gate_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in legal_fixture_gate_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in legal_fixture_gate_entry["evidence_paths"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in legal_fixture_gate_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in legal_fixture_gate_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in legal_fixture_gate_entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in legal_fixture_gate_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage" in legal_fixture_gate_entry["release_gate_links"]
    legal_fixture_promotion_packet_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-cheap-first-default-promotion-packet"
    )
    assert legal_fixture_promotion_packet_entry["size"] == "medium"
    assert legal_fixture_promotion_packet_entry["status"] == "shipped"
    assert "maintainer review packet evidence" in legal_fixture_promotion_packet_entry["impact"]
    assert "cheap-first legal fixture default promotion" in legal_fixture_promotion_packet_entry["impact"]
    assert "fixture ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "document case ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "document benchmark pass/fail counts" in legal_fixture_promotion_packet_entry["impact"]
    assert "coverage-gap counts" in legal_fixture_promotion_packet_entry["impact"]
    assert "cost-tier metadata" in legal_fixture_promotion_packet_entry["impact"]
    assert "required signoff roles" in legal_fixture_promotion_packet_entry["impact"]
    assert "without configuration writes" in legal_fixture_promotion_packet_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google/gateway/network calls" in legal_fixture_promotion_packet_entry["impact"]
    assert "traffic shifts" in legal_fixture_promotion_packet_entry["impact"]
    assert "real legal text" in legal_fixture_promotion_packet_entry["impact"]
    assert "generated document text" in legal_fixture_promotion_packet_entry["impact"]
    assert "model outputs" in legal_fixture_promotion_packet_entry["impact"]
    assert "credentials" in legal_fixture_promotion_packet_entry["impact"]
    assert "emails" in legal_fixture_promotion_packet_entry["impact"]
    assert "app/backend/services/modelops_legal_fixture_default_promotion_packet.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_default_promotion_packet.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    agentic_defaults_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-agentic-grounded-defaults"
    )
    assert agentic_defaults_entry["size"] == "medium"
    assert agentic_defaults_entry["status"] == "shipped"
    assert "APP_AI_AGENTIC_MODEL -> gemini-3.1-flash-lite" in agentic_defaults_entry["impact"]
    assert "APP_AI_GROUNDED_RESEARCH_MODEL -> gemini-3.1-flash-lite" in agentic_defaults_entry["impact"]
    assert "agentic and grounded-research task defaults" in agentic_defaults_entry["impact"]
    assert "ready instead of blocked" in agentic_defaults_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in agentic_defaults_entry["impact"]
    assert "real environment writes" in agentic_defaults_entry["impact"]
    assert "raw prompts" in agentic_defaults_entry["impact"]
    assert "payloads" in agentic_defaults_entry["impact"]
    assert "model outputs" in agentic_defaults_entry["impact"]
    assert "credentials" in agentic_defaults_entry["impact"]
    assert "app/backend/core/config.py" in agentic_defaults_entry["evidence_paths"]
    assert "app/backend/services/model_catalog.py" in agentic_defaults_entry["evidence_paths"]
    assert "app/backend/services/modelops_gemini_cheap_first_coverage_gate.py" in agentic_defaults_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in agentic_defaults_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in agentic_defaults_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in agentic_defaults_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in agentic_defaults_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in agentic_defaults_entry["evidence_paths"]
    assert "modelops-agentic-grounded-defaults" in agentic_defaults_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in agentic_defaults_entry["release_gate_links"]
    assert "model-default-recommendation-snapshot" in agentic_defaults_entry["release_gate_links"]
    assert "model-gateway-compatibility" in agentic_defaults_entry["release_gate_links"]
    assert "model-lifecycle-policy" in agentic_defaults_entry["release_gate_links"]
    default_template_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-default-template-alignment"
    )
    assert default_template_entry["size"] == "medium"
    assert default_template_entry["status"] == "shipped"
    assert "env/template alignment audit evidence" in default_template_entry["impact"]
    assert "Settings defaults" in default_template_entry["impact"]
    assert "app/backend/.env.example" in default_template_entry["impact"]
    assert "README env block" in default_template_entry["impact"]
    assert "docs/AI_MODEL_STRATEGY" in default_template_entry["impact"]
    assert "Gemini cheap-first defaults" in default_template_entry["impact"]
    assert "APP_AI_AGENTIC_MODEL -> gemini-3.1-flash-lite" in default_template_entry["impact"]
    assert "APP_AI_GROUNDED_RESEARCH_MODEL -> gemini-3.1-flash-lite" in default_template_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in default_template_entry["impact"]
    assert "real environment writes" in default_template_entry["impact"]
    assert "raw prompts" in default_template_entry["impact"]
    assert "payloads" in default_template_entry["impact"]
    assert "model outputs" in default_template_entry["impact"]
    assert "credentials" in default_template_entry["impact"]
    assert "app/backend/core/config.py" in default_template_entry["evidence_paths"]
    assert "app/backend/.env.example" in default_template_entry["evidence_paths"]
    assert "README.md" in default_template_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in default_template_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in default_template_entry["evidence_paths"]
    assert "modelops-default-template-alignment" in default_template_entry["release_gate_links"]
    assert "modelops-agentic-grounded-defaults" in default_template_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in default_template_entry["release_gate_links"]
    assert "model-configuration-audit" in default_template_entry["release_gate_links"]
    assert "model-default-recommendation-snapshot" in default_template_entry["release_gate_links"]
    default_change_review_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-gemini-default-change-review"
    )
    assert default_change_review_entry["size"] == "medium"
    assert default_change_review_entry["status"] == "shipped"
    assert "metadata-only Gemini default change proposal review evidence" in default_change_review_entry["impact"]
    assert "cost tier" in default_change_review_entry["impact"]
    assert "lifecycle" in default_change_review_entry["impact"]
    assert "capabilities" in default_change_review_entry["impact"]
    assert "gateway compatibility" in default_change_review_entry["impact"]
    assert "premium/manual review boundary" in default_change_review_entry["impact"]
    assert "new Gemini variant" in default_change_review_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in default_change_review_entry["impact"]
    assert "real environment writes" in default_change_review_entry["impact"]
    assert "raw prompts" in default_change_review_entry["impact"]
    assert "payloads" in default_change_review_entry["impact"]
    assert "model outputs" in default_change_review_entry["impact"]
    assert "credentials" in default_change_review_entry["impact"]
    assert "app/backend/services/release_readiness.py" in default_change_review_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in default_change_review_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in default_change_review_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in default_change_review_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in default_change_review_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in default_change_review_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in default_change_review_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in default_change_review_entry["evidence_paths"]
    assert "modelops-gemini-default-change-review" in default_change_review_entry["release_gate_links"]
    assert "modelops-default-template-alignment" in default_change_review_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in default_change_review_entry["release_gate_links"]
    assert "model-default-recommendation-snapshot" in default_change_review_entry["release_gate_links"]
    assert "model-capability-matrix" in default_change_review_entry["release_gate_links"]
    assert "model-gateway-compatibility" in default_change_review_entry["release_gate_links"]
    assert "model-lifecycle-policy" in default_change_review_entry["release_gate_links"]
    cost_impact_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-gemini-default-cost-impact"
    )
    assert cost_impact_entry["size"] == "medium"
    assert cost_impact_entry["status"] == "shipped"
    assert "metadata-only Gemini default change cost impact forecast evidence" in cost_impact_entry["impact"]
    assert "estimated monthly cost delta" in cost_impact_entry["impact"]
    assert "cheap-first savings or regression" in cost_impact_entry["impact"]
    assert "unknown pricing" in cost_impact_entry["impact"]
    assert "premium exception/manual review boundary" in cost_impact_entry["impact"]
    assert "new Gemini variant" in cost_impact_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in cost_impact_entry["impact"]
    assert "real environment writes" in cost_impact_entry["impact"]
    assert "raw prompts" in cost_impact_entry["impact"]
    assert "payloads" in cost_impact_entry["impact"]
    assert "model outputs" in cost_impact_entry["impact"]
    assert "credentials" in cost_impact_entry["impact"]
    assert "app/backend/services/release_readiness.py" in cost_impact_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in cost_impact_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in cost_impact_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in cost_impact_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in cost_impact_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in cost_impact_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in cost_impact_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in cost_impact_entry["evidence_paths"]
    assert "modelops-gemini-default-cost-impact" in cost_impact_entry["release_gate_links"]
    assert "modelops-gemini-default-change-review" in cost_impact_entry["release_gate_links"]
    assert "modelops-default-template-alignment" in cost_impact_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in cost_impact_entry["release_gate_links"]
    assert "model-cost-forecast" in cost_impact_entry["release_gate_links"]
    assert "model-cost-guardrails" in cost_impact_entry["release_gate_links"]
    assert "model-default-recommendation-snapshot" in cost_impact_entry["release_gate_links"]
    intake_queue_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-observed-gemini-model-intake-queue"
    )
    assert intake_queue_entry["size"] == "medium"
    assert intake_queue_entry["status"] == "shipped"
    assert "metadata-only observed Gemini model intake queue evidence" in intake_queue_entry["impact"]
    assert "OpenAI-compatible gateway /models" in intake_queue_entry["impact"]
    assert "manually observed Gemini-like model ids" in intake_queue_entry["impact"]
    assert "normalized" in intake_queue_entry["impact"]
    assert "known or unknown status" in intake_queue_entry["impact"]
    assert "price" in intake_queue_entry["impact"]
    assert "lifecycle" in intake_queue_entry["impact"]
    assert "cost tier" in intake_queue_entry["impact"]
    assert "cheap-first eligibility" in intake_queue_entry["impact"]
    assert "default-promotion block/review/ready state" in intake_queue_entry["impact"]
    assert "before they enter default candidates" in intake_queue_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in intake_queue_entry["impact"]
    assert "real environment writes" in intake_queue_entry["impact"]
    assert "raw prompts" in intake_queue_entry["impact"]
    assert "payloads" in intake_queue_entry["impact"]
    assert "model outputs" in intake_queue_entry["impact"]
    assert "credentials" in intake_queue_entry["impact"]
    assert "app/backend/services/release_readiness.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in intake_queue_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in intake_queue_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in intake_queue_entry["evidence_paths"]
    assert "modelops-observed-gemini-model-intake-queue" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-default-change-review" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-default-cost-impact" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in intake_queue_entry["release_gate_links"]
    assert "model-catalog-source-audit" in intake_queue_entry["release_gate_links"]
    assert "model-gateway-compatibility" in intake_queue_entry["release_gate_links"]
    assert "model-lifecycle-policy" in intake_queue_entry["release_gate_links"]
    catalog_candidate_patch_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-catalog-candidate-patch-plan"
    )
    assert catalog_candidate_patch_entry["size"] == "medium"
    assert catalog_candidate_patch_entry["status"] == "shipped"
    assert "sanitized observed Gemini-like gateway model ids" in catalog_candidate_patch_entry["impact"]
    assert "manual ModelProfile candidate rows" in catalog_candidate_patch_entry["impact"]
    assert "required metadata checks" in catalog_candidate_patch_entry["impact"]
    assert "explicit-only default-promotion boundaries" in catalog_candidate_patch_entry["impact"]
    assert "without editing model_catalog.py" in catalog_candidate_patch_entry["impact"]
    assert "calling gateways" in catalog_candidate_patch_entry["impact"]
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/backend/tests/test_model_catalog_candidate_patch_plan.py" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in catalog_candidate_patch_entry["evidence_paths"]
    assert "docs/MODEL_CATALOG_CANDIDATE_PATCH_PLAN.md" in catalog_candidate_patch_entry["evidence_paths"]
    assert "model-catalog-candidate-patch-plan" in catalog_candidate_patch_entry["release_gate_links"]
    assert "modelops-observed-gemini-model-intake-queue" in catalog_candidate_patch_entry["release_gate_links"]
    assert "model-catalog-source-audit" in catalog_candidate_patch_entry["release_gate_links"]
    assert "model-ops-readiness" in catalog_candidate_patch_entry["release_gate_links"]
    assert "frontend-ui-regression" in catalog_candidate_patch_entry["release_gate_links"]
    refresh_entry = next(entry for entry in ledger["completed_updates"] if entry["id"] == "legal-benchmark-research-refresh")
    assert "app/backend/services/legal_benchmark_research_refresh.py" in refresh_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_benchmark_research_refresh.py" in refresh_entry["evidence_paths"]
    assert "docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md" in refresh_entry["evidence_paths"]
    assert "legal-benchmark-research-refresh" in refresh_entry["release_gate_links"]
    assert "without dataset downloads" in refresh_entry["impact"]
    assert "public scores" in refresh_entry["impact"]
    assert "external legal text" in refresh_entry["impact"]
    assert "model calls" in refresh_entry["impact"]
    assert "credentials" in refresh_entry["impact"]
    route_queue_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-route-legal-benchmark-risk-queue"
    )
    assert "app/backend/services/model_route_legal_benchmark_risk_queue.py" in route_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_model_route_legal_benchmark_risk_queue.py" in route_queue_entry["evidence_paths"]
    assert "docs/MODEL_ROUTE_LEGAL_BENCHMARK_RISK_QUEUE.md" in route_queue_entry["evidence_paths"]
    assert "model-route-legal-benchmark-risk-queue" in route_queue_entry["release_gate_links"]
    assert "cheap-first Gemini/NewAPI calibration" in route_queue_entry["impact"]
    assert "legal benchmark refresh" in route_queue_entry["impact"]
    assert "user-need coverage" in route_queue_entry["impact"]
    assert "without gateway calls" in route_queue_entry["impact"]
    assert "dataset downloads" in route_queue_entry["impact"]
    assert "public benchmark scores" in route_queue_entry["impact"]
    assert "raw legal text" in route_queue_entry["impact"]
    assert "credentials" in route_queue_entry["impact"]
    priority_queue_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "user-need-implementation-priority-queue"
    )
    assert priority_queue_entry["size"] == "medium"
    assert priority_queue_entry["status"] == "shipped"
    assert "metadata-only review evidence" in priority_queue_entry["impact"]
    assert "high-priority user needs" in priority_queue_entry["impact"]
    assert "legal benchmark coverage gaps" in priority_queue_entry["impact"]
    assert "cheap-first calibration/model routing risk" in priority_queue_entry["impact"]
    assert "product execution actions" in priority_queue_entry["impact"]
    assert "without public dataset downloads" in priority_queue_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google/gateway/network calls" in priority_queue_entry["impact"]
    assert "real env writes" in priority_queue_entry["impact"]
    assert "raw legal text" in priority_queue_entry["impact"]
    assert "prompts" in priority_queue_entry["impact"]
    assert "payloads" in priority_queue_entry["impact"]
    assert "model outputs" in priority_queue_entry["impact"]
    assert "credentials" in priority_queue_entry["impact"]
    assert "app/backend/services/release_readiness.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in priority_queue_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in priority_queue_entry["evidence_paths"]
    assert "docs/USER_NEED_BENCHMARK_COVERAGE.md" in priority_queue_entry["evidence_paths"]
    assert "docs/USER_NEEDS_RADAR.md" in priority_queue_entry["evidence_paths"]
    assert "user-need-implementation-priority-queue" in priority_queue_entry["release_gate_links"]
    assert "user-needs-radar" in priority_queue_entry["release_gate_links"]
    assert "user-need-benchmark-coverage" in priority_queue_entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in priority_queue_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in priority_queue_entry["release_gate_links"]
    assert "legal-benchmark-research-refresh" in priority_queue_entry["release_gate_links"]
    assert "product-feature-gap-radar" in priority_queue_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py -q"
        in ledger["validation_commands"]
    )
    default_candidate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-default-candidate-selector"
    )
    assert default_candidate_entry["size"] == "medium"
    assert default_candidate_entry["status"] == "shipped"
    assert "metadata-only Gemini/NewAPI default candidate selector" in default_candidate_entry["impact"]
    assert "cheapest capable task recommendations" in default_candidate_entry["impact"]
    assert "future lower-cost stable Flash-Lite variants" in default_candidate_entry["impact"]
    assert "without hard-coded default drift" in default_candidate_entry["impact"]
    assert "real env writes" in default_candidate_entry["impact"]
    assert "gateway calls" in default_candidate_entry["impact"]
    assert "network calls" in default_candidate_entry["impact"]
    assert "prompts" in default_candidate_entry["impact"]
    assert "raw legal text" in default_candidate_entry["impact"]
    assert "model outputs" in default_candidate_entry["impact"]
    assert "credentials" in default_candidate_entry["impact"]
    assert "app/backend/services/model_default_candidate_selector.py" in default_candidate_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_cheap_first_policy.py" in default_candidate_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_selector.py" in default_candidate_entry["evidence_paths"]
    assert "app/backend/services/model_capability_matrix.py" in default_candidate_entry["evidence_paths"]
    assert "app/backend/tests/test_model_default_candidate_selector.py" in default_candidate_entry["evidence_paths"]
    assert "app/backend/tests/test_model_capability_matrix.py" in default_candidate_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in default_candidate_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in default_candidate_entry["evidence_paths"]
    assert "docs/MODEL_DEFAULT_CANDIDATE_SELECTOR.md" in default_candidate_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in default_candidate_entry["evidence_paths"]
    assert "model-default-candidate-selector" in default_candidate_entry["release_gate_links"]
    assert "gemini-newapi-model-selector" in default_candidate_entry["release_gate_links"]
    assert "model-price-refresh-monitor" in default_candidate_entry["release_gate_links"]
    authority_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-authority-citation-gate"
    )
    assert "app/backend/services/legal_rag_authority_citation_gate.py" in authority_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_authority_citation_gate.py" in authority_gate_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md" in authority_gate_entry["evidence_paths"]
    assert "legal-rag-authority-citation-gate" in authority_gate_entry["release_gate_links"]
    assert "selected-source ids" in authority_gate_entry["impact"]
    assert "authority tiers" in authority_gate_entry["impact"]
    assert "citation-map source ids" in authority_gate_entry["impact"]
    assert "without NewAPI/Gemini calls" in authority_gate_entry["impact"]
    assert "gateway calls" in authority_gate_entry["impact"]
    assert "dataset downloads" in authority_gate_entry["impact"]
    assert "raw legal text" in authority_gate_entry["impact"]
    assert "prompts" in authority_gate_entry["impact"]
    assert "model outputs" in authority_gate_entry["impact"]
    assert "credentials" in authority_gate_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_authority_citation_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q"
        in ledger["validation_commands"]
    )
    triage_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-hallucination-triage-gate"
    )
    assert "app/backend/services/legal_rag_hallucination_triage_gate.py" in triage_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_hallucination_triage_gate.py" in triage_gate_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_HALLUCINATION_TRIAGE_GATE.md" in triage_gate_entry["evidence_paths"]
    assert "legal-rag-hallucination-triage-gate" in triage_gate_entry["release_gate_links"]
    assert "failure fixture labels" in triage_gate_entry["impact"]
    assert "reviewer actions" in triage_gate_entry["impact"]
    assert "release blockers" in triage_gate_entry["impact"]
    assert "authority-gate rows" in triage_gate_entry["impact"]
    assert "without NewAPI/Gemini calls" in triage_gate_entry["impact"]
    assert "gateway calls" in triage_gate_entry["impact"]
    assert "dataset downloads" in triage_gate_entry["impact"]
    assert "raw legal text" in triage_gate_entry["impact"]
    assert "retrieved snippets" in triage_gate_entry["impact"]
    assert "prompts" in triage_gate_entry["impact"]
    assert "model outputs" in triage_gate_entry["impact"]
    assert "credentials" in triage_gate_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_hallucination_triage_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q"
        in ledger["validation_commands"]
    )
    abstention_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-abstention-escalation-gate"
    )
    assert "app/backend/services/legal_rag_abstention_escalation_gate.py" in abstention_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_abstention_escalation_gate.py" in abstention_gate_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_ABSTENTION_ESCALATION_GATE.md" in abstention_gate_entry["evidence_paths"]
    assert "legal-rag-abstention-escalation-gate" in abstention_gate_entry["release_gate_links"]
    assert "legal-rag-hallucination-triage-gate" in abstention_gate_entry["release_gate_links"]
    assert "legal-rag-authority-citation-gate" in abstention_gate_entry["release_gate_links"]
    assert "model-escalation-policy" in abstention_gate_entry["release_gate_links"]
    assert "raw retrieved context" in abstention_gate_entry["impact"]
    assert "credentials" in abstention_gate_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q"
        in ledger["validation_commands"]
    )
    retrieval_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-retrieval-diagnostics-gate"
    )
    assert "app/backend/services/legal_rag_retrieval_diagnostics_gate.py" in retrieval_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_retrieval_diagnostics_gate.py" in retrieval_gate_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_RETRIEVAL_DIAGNOSTICS_GATE.md" in retrieval_gate_entry["evidence_paths"]
    assert "legal-rag-retrieval-diagnostics-gate" in retrieval_gate_entry["release_gate_links"]
    assert "legal-rag-index-binding" in retrieval_gate_entry["release_gate_links"]
    assert "legal-rag-authority-citation-gate" in retrieval_gate_entry["release_gate_links"]
    assert "legal-rag-abstention-escalation-gate" in retrieval_gate_entry["release_gate_links"]
    assert "model-escalation-policy" in retrieval_gate_entry["release_gate_links"]
    assert "query-intent labels" in retrieval_gate_entry["impact"]
    assert "authority coverage" in retrieval_gate_entry["impact"]
    assert "top-k depth" in retrieval_gate_entry["impact"]
    assert "jurisdiction/freshness" in retrieval_gate_entry["impact"]
    assert "citation gaps" in retrieval_gate_entry["impact"]
    assert "retrieval gaps" in retrieval_gate_entry["impact"]
    assert "cheap-first defaults" in retrieval_gate_entry["impact"]
    assert "premium-exception boundaries" in retrieval_gate_entry["impact"]
    assert "model calls" in retrieval_gate_entry["impact"]
    assert "gateway calls" in retrieval_gate_entry["impact"]
    assert "network calls" in retrieval_gate_entry["impact"]
    assert "raw query" in retrieval_gate_entry["impact"]
    assert "raw retrieved context" in retrieval_gate_entry["impact"]
    assert "raw legal text" in retrieval_gate_entry["impact"]
    assert "prompts" in retrieval_gate_entry["impact"]
    assert "model outputs" in retrieval_gate_entry["impact"]
    assert "credentials" in retrieval_gate_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q"
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
