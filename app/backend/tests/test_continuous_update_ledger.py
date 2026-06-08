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


def test_continuous_update_ledger_includes_modelops_legal_benchmark_risk_bridge_evidence():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    entry = next(
        item for item in ledger["completed_updates"]
        if item["id"] == "modelops-legal-benchmark-risk-bridge"
    )

    assert entry["category"] == "model_ops"
    assert entry["size"] == "medium"
    assert "metadata-only ModelOps review evidence" in entry["impact"]
    assert "gateway/network calls" in entry["impact"]
    assert "raw legal text" in entry["impact"]
    assert "app/backend/services/model_ops_legal_benchmark_risk_bridge.py" in entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in entry["evidence_paths"]
    assert "docs/MODEL_OPS_LEGAL_BENCHMARK_RISK_BRIDGE.md" in entry["evidence_paths"]
    assert "modelops-legal-benchmark-risk-bridge" in entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in entry["release_gate_links"]
    assert "cheap-first-review-routing" in entry["user_need_ids"]
    assert "traceable-legal-review" in entry["user_need_ids"]


def test_continuous_update_ledger_tracks_settings_ai_provider_status_card():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    entry = next(
        item for item in ledger["completed_updates"]
        if item["id"] == "settings-ai-provider-status-card"
    )

    assert entry["category"] == "frontend_ui"
    assert entry["size"] == "medium"
    assert entry["status"] == "shipped"
    assert "read-only Settings AI provider status card" in entry["impact"]
    assert "metadata-only gateway runtime configuration evidence" in entry["impact"]
    assert "cheap-first role counts" in entry["impact"]
    assert "admin settings access" in entry["impact"]
    assert "configuration writes" in entry["impact"]
    assert "raw gateway URLs" in entry["impact"]
    assert "credential values" in entry["impact"]
    assert "prompts" in entry["impact"]
    assert "model outputs" in entry["impact"]
    assert "app/frontend/src/pages/SettingsPage.tsx" in entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in entry["evidence_paths"]
    assert "app/backend/tests/test_frontend_ui_regression_gate.py" in entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in entry["evidence_paths"]
    assert "settings-ai-provider-status-card" in entry["release_gate_links"]
    assert "model-gateway-runtime-configuration" in entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in entry["release_gate_links"]
    assert "low-cost-routing" in entry["user_need_ids"]
    assert "safe-ai-ops" in entry["user_need_ids"]


def test_continuous_update_ledger_tracks_case_workbench_risk_state_badges():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    entry = next(
        item for item in ledger["completed_updates"]
        if item["id"] == "case-workbench-risk-state-badges"
    )

    assert entry["category"] == "product_planning"
    assert entry["size"] == "medium"
    assert entry["status"] == "shipped"
    assert "risk-state badge projection" in entry["impact"]
    assert "critical task, deadline, evidence, and runtime-event signals" in entry["impact"]
    assert "without writing risk state" in entry["impact"]
    assert "refreshing evidence graphs" in entry["impact"]
    assert "sending notifications" in entry["impact"]
    assert "raw case text" in entry["impact"]
    assert "credentials" in entry["impact"]
    assert "app/backend/services/case_workbench_risk_refresh_plan.py" in entry["evidence_paths"]
    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in entry["evidence_paths"]
    assert "docs/CASE_WORKBENCH_RISK_REFRESH_PLAN.md" in entry["evidence_paths"]
    assert "case-workbench-risk-refresh-plan" in entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in entry["release_gate_links"]


def test_continuous_update_ledger_prioritizes_low_resource_next_work():
    ledger = ContinuousUpdateLedgerService().build_ledger()
    queue_ids = {entry["id"] for entry in ledger["next_update_queue"]}
    completed_ids = {entry["id"] for entry in ledger["completed_updates"]}

    assert "cheap-first-result-archive" in completed_ids
    assert "gemini-price-refresh-monitor" in completed_ids
    assert "model-price-refresh-monitor-readiness-ui" in completed_ids
    assert "gemini-newapi-model-selector" in completed_ids
    assert "gemini-newapi-observed-model-extraction" in completed_ids
    assert "gemini-newapi-extractor-rejection-taxonomy" in completed_ids
    assert "gemini-newapi-model-alias-matrix" in completed_ids
    assert "gemini-newapi-alias-capability-coverage" in completed_ids
    assert "gemini-official-preview-alias-review" in completed_ids
    assert "gemini-newapi-selector-replay" in completed_ids
    assert "gemini-newapi-cheap-first-calibration" in completed_ids
    assert "modelops-cheap-first-calibration-review-form" in completed_ids
    assert "gemini-model-variant-matrix" in completed_ids
    assert "modelops-gemini-variant-review-form" in completed_ids
    assert "gemini-variant-model-list-ingestion" in completed_ids
    assert "modelops-load-performance-budget" in completed_ids
    assert "modelops-performance-observation-review" in completed_ids
    assert "modelops-performance-observation-release-binding" in completed_ids
    assert "modelops-first-paint-aggregate-binding" in completed_ids
    performance_release_binding_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-performance-observation-release-binding"
    )
    assert performance_release_binding_entry["size"] == "medium"
    assert performance_release_binding_entry["status"] == "shipped"
    assert "sanitized POST performance observations" in performance_release_binding_entry["impact"]
    assert "aggregate ModelOps readiness" in performance_release_binding_entry["impact"]
    assert "cheap-first release decision" in performance_release_binding_entry["impact"]
    assert "subsequent in-process /models payloads" in performance_release_binding_entry["impact"]
    assert "maintainer review" in performance_release_binding_entry["impact"]
    assert "block default promotion" in performance_release_binding_entry["impact"]
    assert "raw payloads" in performance_release_binding_entry["impact"]
    assert "credentials" in performance_release_binding_entry["impact"]
    assert "network calls" in performance_release_binding_entry["impact"]
    assert "app/backend/routers/aihub.py" in performance_release_binding_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_performance_budget.py" in performance_release_binding_entry["evidence_paths"]
    assert "docs/MODEL_OPS_PERFORMANCE_BUDGET.md" in performance_release_binding_entry["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_RELEASE_DECISION.md" in performance_release_binding_entry["evidence_paths"]
    assert "modelops-performance-observation-review" in performance_release_binding_entry["release_gate_links"]
    assert "model-ops-readiness" in performance_release_binding_entry["release_gate_links"]
    assert "modelops-cheap-first-release-decision" in performance_release_binding_entry["release_gate_links"]
    first_paint_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-first-paint-aggregate-binding"
    )
    assert first_paint_entry["size"] == "medium"
    assert first_paint_entry["status"] == "shipped"
    assert "aggregate /api/v1/aihub/models payload returns" in first_paint_entry["impact"]
    assert "legal fixture cheap-first gate evidence" in first_paint_entry["impact"]
    assert "default promotion packet evidence" in first_paint_entry["impact"]
    assert "provider calls" in first_paint_entry["impact"]
    assert "traffic shifts" in first_paint_entry["impact"]
    assert "raw payloads" in first_paint_entry["impact"]
    assert "credentials" in first_paint_entry["impact"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in first_paint_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in first_paint_entry["evidence_paths"]
    assert "docs/MODEL_OPS_PERFORMANCE_BUDGET.md" in first_paint_entry["evidence_paths"]
    assert "modelops-load-performance-budget" in first_paint_entry["release_gate_links"]
    assert "modelops-legal-fixture-modelops-ui-binding" in first_paint_entry["release_gate_links"]
    assert "frontend-ui-regression" in first_paint_entry["release_gate_links"]
    assert "modelops-cheap-first-quality-budget" in completed_ids
    assert "modelops-cheap-first-escalation-budget" in completed_ids
    assert "model-failure-upgrade-budget" in completed_ids
    assert "gemini-catalog-source-audit" in completed_ids
    catalog_source_audit_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gemini-catalog-source-audit"
    )
    assert "source review freshness" in catalog_source_audit_entry["impact"]
    assert "default-promotion source blocks" in catalog_source_audit_entry["impact"]
    assert "Flash-Lite cheap-first alignment" in catalog_source_audit_entry["impact"]
    assert "model-catalog-candidate-patch-plan" in completed_ids
    assert "model-catalog-candidate-impact-replay" in completed_ids
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
    assert "modelops-gemini-cheap-first-route-preflight" in completed_ids
    assert "modelops-aihub-media-speech-default-catalog-gate" in completed_ids
    assert "gemini-media-speech-review-catalog" in completed_ids
    assert "modelops-gemini-embedding-cheap-first-preflight" in completed_ids
    assert "model-gateway-request-compatibility-gate" in completed_ids
    assert "model-gateway-runtime-configuration" in completed_ids
    assert "modelops-observed-gateway-model-fit-matrix" in completed_ids
    assert "modelops-legal-micro-benchmark-preflight" in completed_ids
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in completed_ids
    assert "legal-document-fact-consistency-benchmark" in completed_ids
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in completed_ids
    assert "settings-ai-provider-status-card" in completed_ids
    assert "modelops-legal-fixture-cheap-first-calibration-binding" in completed_ids
    assert "modelops-legal-fixture-modelops-ui-binding" in completed_ids
    assert "modelops-cheap-first-release-legal-benchmark-binding" in completed_ids
    assert "modelops-cheap-first-release-maintenance-evidence-panel" in completed_ids
    assert "modelops-agentic-grounded-defaults" in completed_ids
    assert "modelops-default-template-alignment" in completed_ids
    assert "modelops-gemini-default-change-review" in completed_ids
    assert "modelops-gemini-default-cost-impact" in completed_ids
    assert "modelops-observed-gemini-model-intake-queue" in completed_ids
    assert "modelops-observed-gemini-coverage-gap-queue" in completed_ids
    assert "modelops-gemini-official-model-family-roadmap-evidence" in completed_ids
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
    assert "route-telemetry-catalog-cost-estimation" in completed_ids
    assert "runtime-route-reason-codes" in completed_ids
    assert "pdf-image-route-telemetry" in completed_ids
    assert "image-auto-route-default" in completed_ids
    assert "image-price-refresh-monitor" in completed_ids
    assert "image-gateway-health-plan" in completed_ids
    assert "image-gateway-probe-evaluation" in completed_ids
    assert "gateway-probe-secret-value-guard" in completed_ids
    assert "gateway-probe-readiness-binding" in completed_ids
    assert "gateway-probe-latest-evidence-store" in completed_ids
    assert "model-ops-readiness-required-optional-summary" in completed_ids
    assert "model-ops-readiness-warning-drilldown" in completed_ids
    assert "route-telemetry-ops-summary" in completed_ids
    assert "route-telemetry-triage-queue" in completed_ids
    assert "route-telemetry-reason-code-hotspots" in completed_ids
    assert "route-telemetry-remediation-plan" in completed_ids
    assert "route-telemetry-ui-regression-contract" in completed_ids
    assert "legal-source-freshness-policy" in completed_ids
    assert "maintenance-dashboard-filtering" in completed_ids
    assert "frontend-local-run-review-form" in completed_ids
    assert "case-workbench-payload" in completed_ids
    assert "document-delivery-package-manifest" in completed_ids
    assert "case-role-permission-matrix" in completed_ids
    assert "case-access-control-runtime-gate" in completed_ids
    assert "billing-usage-quota-policy" in completed_ids
    assert "feedback-lifecycle-policy" in completed_ids
    assert "feedback-capture-plan" in completed_ids
    assert "model-default-candidate-selector" in completed_ids
    assert "model-default-ladder-review-boundaries" in completed_ids
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
    assert "legal-rag-missing-answer-citation-blocker" in completed_ids
    assert "billing-entitlement-repository-binding" in completed_ids
    assert "case-workbench-runtime-router" in completed_ids
    assert "case-workbench-risk-refresh-plan" in completed_ids
    assert "case-workbench-risk-state-badges" in completed_ids
    assert "legal-rag-index-route" in completed_ids
    assert "billing-quota-consumption-route" in completed_ids
    assert "frontend-runtime-api-client-bindings" in completed_ids
    assert "runtime-router-discovery-smoke" in completed_ids
    assert "case-workbench-frontend-state-events" in completed_ids
    assert "legal-rag-case-research-ui" in completed_ids
    assert "case-export-readiness-download-gate" in completed_ids
    assert "deep-review-export-readiness-route-gate" in completed_ids
    assert "deep-review-ocr-readiness-runtime-binding" in completed_ids
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
    assert "legal-document-template-benchmark-alignment" in completed_ids
    template_benchmark_alignment_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-document-template-benchmark-alignment"
    )
    assert template_benchmark_alignment_entry["size"] == "medium"
    assert template_benchmark_alignment_entry["status"] == "shipped"
    assert "template matrix canonical benchmark document types" in template_benchmark_alignment_entry["impact"]
    assert "defense-answer fixture coverage" in template_benchmark_alignment_entry["impact"]
    assert "legal-opinion template delivery rules" in template_benchmark_alignment_entry["impact"]
    assert "UTF-8 readability" in template_benchmark_alignment_entry["impact"]
    assert "model calls" in template_benchmark_alignment_entry["impact"]
    assert "dataset downloads" in template_benchmark_alignment_entry["impact"]
    assert "credentials" in template_benchmark_alignment_entry["impact"]
    assert "app/backend/services/legal_document_template_matrix.py" in template_benchmark_alignment_entry["evidence_paths"]
    assert "app/backend/services/legal_document_benchmark_coverage.py" in template_benchmark_alignment_entry["evidence_paths"]
    assert "app/backend/services/legal_document_benchmark_suite.py" in template_benchmark_alignment_entry["evidence_paths"]
    assert "app/backend/services/legal_document_coverage_claim_policy.py" in template_benchmark_alignment_entry["evidence_paths"]
    assert "app/backend/mock_data/templates.json" in template_benchmark_alignment_entry["evidence_paths"]
    assert "legal-document-template-matrix" in template_benchmark_alignment_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage" in template_benchmark_alignment_entry["release_gate_links"]
    assert "legal-document-coverage-claim-policy" in template_benchmark_alignment_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage-ui" in completed_ids
    assert "legal-document-benchmark-fixture-ui" in completed_ids
    legal_document_benchmark_fixture_ui_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-document-benchmark-fixture-ui"
    )
    assert legal_document_benchmark_fixture_ui_entry["size"] == "medium"
    assert legal_document_benchmark_fixture_ui_entry["status"] == "shipped"
    assert "empty-prediction evaluator" in legal_document_benchmark_fixture_ui_entry["impact"]
    assert "raw-snippet rendering boundary" in legal_document_benchmark_fixture_ui_entry["impact"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in legal_document_benchmark_fixture_ui_entry[
        "evidence_paths"
    ]
    assert "app/frontend/scripts/ui-regression.mjs" in legal_document_benchmark_fixture_ui_entry["evidence_paths"]
    assert "legal-document-benchmark-fixtures" in legal_document_benchmark_fixture_ui_entry["release_gate_links"]
    assert "frontend-ui-regression" in legal_document_benchmark_fixture_ui_entry["release_gate_links"]
    assert "legal-document-coverage-claim-policy" in completed_ids
    assert "legal-benchmark-research-registry" in completed_ids
    assert "legal-benchmark-research-refresh" in completed_ids
    assert "legal-public-benchmark-license-gate" in completed_ids
    assert "model-route-legal-benchmark-risk-queue" in completed_ids
    assert "modelops-legal-benchmark-risk-bridge" in completed_ids
    assert "local-dev-reload-stability-guard" in completed_ids
    assert "local-dev-dynamic-proxy-port-guard" in completed_ids
    assert "feedback-roadmap-cheap-first-route-coverage" in completed_ids
    assert "local-dev-reload-stability-guard" not in queue_ids
    assert "local-dev-dynamic-proxy-port-guard" not in queue_ids
    assert "feedback-roadmap-cheap-first-route-coverage" not in queue_ids
    assert "legal-benchmark-research-registry-ui" in completed_ids
    assert "legal-rag-abstention-escalation-gate" in completed_ids
    assert "legal-rag-retrieval-diagnostics-gate" in completed_ids
    assert "legal-rag-index-coverage-gate" in completed_ids
    assert "legal-rag-embedding-readiness-gate" in completed_ids
    assert "legal-rag-embedding-chunk-policy-gate" in completed_ids
    assert "legal-rag-embedding-index-dry-run-gate" in completed_ids
    assert "legal-rag-embedding-batch-budget-gate" in completed_ids
    assert "legal-rag-embedding-batch-approval-packet" in completed_ids
    assert "legal-rag-embedding-batch-observation-gate" in completed_ids
    assert "legal-rag-embedding-index-commit-review-packet" in completed_ids
    assert "legal-rag-embedding-index-post-commit-verification-gate" in completed_ids
    assert "legal-rag-embedding-retrieval-diagnostics-handoff-gate" in completed_ids
    assert "legal-rag-benchmark-alignment" in completed_ids
    assert "legal-rag-retrieval-observation-gate" in completed_ids
    assert "legal-rag-answer-release-readiness-gate" in completed_ids
    assert "legal-rag-retrieval-observation-ui-binding" in completed_ids
    assert "legal-adoption-research-bridge" in completed_ids
    assert "deep-review-selected-source-binding" in completed_ids
    assert "legal-rag-export-readiness-packet" in completed_ids
    assert "quota-delivery-decision" in completed_ids
    assert "feedback-issue-cluster" in completed_ids
    assert "evidence-bundle-integrity" in completed_ids
    assert "privacy-retention-rules" in completed_ids
    assert "release-claim-compliance" in completed_ids
    assert "case-export-readiness" in completed_ids
    local_dev_reload_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "local-dev-reload-stability-guard"
    )
    assert local_dev_reload_entry["size"] == "medium"
    assert local_dev_reload_entry["status"] == "shipped"
    assert "backend reload watches exclude logs" in local_dev_reload_entry["impact"]
    assert "Vite proxy" in local_dev_reload_entry["impact"]
    assert "127.0.0.1:3000" in local_dev_reload_entry["impact"]
    assert "business routes" in local_dev_reload_entry["impact"]
    assert "provider calls" in local_dev_reload_entry["impact"]
    assert "credentials" in local_dev_reload_entry["impact"]
    assert "app/start_app_v2.sh" in local_dev_reload_entry["evidence_paths"]
    assert "app/backend/tests/test_local_dev_startup_reload_guard.py" in local_dev_reload_entry["evidence_paths"]
    assert "frontend-local-run-review-form" in local_dev_reload_entry["release_gate_links"]
    assert "runtime-router-discovery-smoke" in local_dev_reload_entry["release_gate_links"]
    assert "product-readiness" in local_dev_reload_entry["user_need_ids"]
    local_dev_proxy_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "local-dev-dynamic-proxy-port-guard"
    )
    assert local_dev_proxy_entry["size"] == "medium"
    assert local_dev_proxy_entry["status"] == "shipped"
    assert "Vite development /api proxy" in local_dev_proxy_entry["impact"]
    assert "backend port selected by the local startup script" in local_dev_proxy_entry["impact"]
    assert "loopback frontend home page" in local_dev_proxy_entry["impact"]
    assert "bare 127.0.0.1" in local_dev_proxy_entry["impact"]
    assert "business routes" in local_dev_proxy_entry["impact"]
    assert "model defaults" in local_dev_proxy_entry["impact"]
    assert "credentials" in local_dev_proxy_entry["impact"]
    assert "app/frontend/vite.config.ts" in local_dev_proxy_entry["evidence_paths"]
    assert "app/start_app_v2.sh" in local_dev_proxy_entry["evidence_paths"]
    assert "local-dev-dynamic-proxy-port-guard" in local_dev_proxy_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in local_dev_proxy_entry["release_gate_links"]
    assert "reviewer-visibility" in local_dev_proxy_entry["user_need_ids"]
    feedback_route_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "feedback-roadmap-cheap-first-route-coverage"
    )
    assert feedback_route_entry["size"] == "medium"
    assert feedback_route_entry["status"] == "shipped"
    assert "feedback-to-roadmap cheap-first classification coverage" in feedback_route_entry["impact"]
    assert "FrugalGPT cost-quality mapping" in feedback_route_entry["impact"]
    assert "blocked to review-required" in feedback_route_entry["impact"]
    assert "default-route changes" in feedback_route_entry["impact"]
    assert "raw feedback text" in feedback_route_entry["impact"]
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in feedback_route_entry["evidence_paths"]
    assert "app/backend/services/user_need_gemini_route_coverage.py" in feedback_route_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md" in feedback_route_entry["evidence_paths"]
    assert "feedback_triage" in feedback_route_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in feedback_route_entry["release_gate_links"]
    assert "feedback-to-roadmap-loop" in feedback_route_entry["user_need_ids"]
    assert "cheap-first-review-routing" in feedback_route_entry["user_need_ids"]
    deep_review_export_gate_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "deep-review-export-readiness-route-gate"
    )
    assert deep_review_export_gate_entry["size"] == "medium"
    assert deep_review_export_gate_entry["status"] == "shipped"
    assert "real deep-review report export route" in deep_review_export_gate_entry["impact"]
    assert "metadata-only case export readiness" in deep_review_export_gate_entry["impact"]
    assert "pdf/doc/md/json download content" in deep_review_export_gate_entry["impact"]
    assert "selected-source validation failures" in deep_review_export_gate_entry["impact"]
    assert "raw report text" in deep_review_export_gate_entry["impact"]
    assert "client emails" in deep_review_export_gate_entry["impact"]
    assert "credentials" in deep_review_export_gate_entry["impact"]
    assert "app/backend/routers/deep_review.py" in deep_review_export_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_deep_review_export_gate.py" in deep_review_export_gate_entry["evidence_paths"]
    assert "app/backend/services/case_export_readiness.py" in deep_review_export_gate_entry["evidence_paths"]
    assert "docs/DEEP_REVIEW_EXPORT_READINESS_GATE.md" in deep_review_export_gate_entry["evidence_paths"]
    assert "deep-review-export-readiness-route-gate" in deep_review_export_gate_entry["release_gate_links"]
    assert "case-export-readiness" in deep_review_export_gate_entry["release_gate_links"]
    assert "deep-review-selected-source-binding" in deep_review_export_gate_entry["release_gate_links"]
    ocr_runtime_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "deep-review-ocr-readiness-runtime-binding"
    )
    assert ocr_runtime_entry["size"] == "medium"
    assert ocr_runtime_entry["status"] == "shipped"
    assert "uploaded-document deep-review responses" in ocr_runtime_entry["impact"]
    assert "polling status" in ocr_runtime_entry["impact"]
    assert "upload UI" in ocr_runtime_entry["impact"]
    assert "progress UI" in ocr_runtime_entry["impact"]
    assert "OCR-completed/failed states" in ocr_runtime_entry["impact"]
    assert "raw OCR text" in ocr_runtime_entry["impact"]
    assert "uploaded images" in ocr_runtime_entry["impact"]
    assert "client emails" in ocr_runtime_entry["impact"]
    assert "credentials" in ocr_runtime_entry["impact"]
    assert "app/backend/routers/deep_review.py" in ocr_runtime_entry["evidence_paths"]
    assert "app/backend/tests/test_deep_review_ocr_readiness_runtime.py" in ocr_runtime_entry["evidence_paths"]
    assert "app/frontend/src/lib/deepReviewApi.ts" in ocr_runtime_entry["evidence_paths"]
    assert "app/frontend/src/pages/UploadPage.tsx" in ocr_runtime_entry["evidence_paths"]
    assert "app/frontend/src/pages/ReviewProgressPage.tsx" in ocr_runtime_entry["evidence_paths"]
    assert "docs/OCR_IMPORT_READINESS_POLICY.md" in ocr_runtime_entry["evidence_paths"]
    assert "deep-review-ocr-readiness-runtime-binding" in ocr_runtime_entry["release_gate_links"]
    assert "ocr-import-readiness-policy" in ocr_runtime_entry["release_gate_links"]
    assert "frontend-typecheck" in ocr_runtime_entry["release_gate_links"]
    case_access_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "case-access-control-runtime-gate"
    )
    assert case_access_entry["size"] == "large"
    assert case_access_entry["status"] == "shipped"
    assert "real cases API and CaseDetail UI" in case_access_entry["impact"]
    assert "/all route no longer bypasses access filtering" in case_access_entry["impact"]
    assert "/permissions returns a privacy-safe operation summary" in case_access_entry["impact"]
    assert "raw team member text" in case_access_entry["impact"]
    assert "client names" in case_access_entry["impact"]
    assert "emails" in case_access_entry["impact"]
    assert "credentials" in case_access_entry["impact"]
    assert "app/backend/services/case_access_control.py" in case_access_entry["evidence_paths"]
    assert "app/backend/routers/cases.py" in case_access_entry["evidence_paths"]
    assert "app/backend/tests/test_case_access_control.py" in case_access_entry["evidence_paths"]
    assert "app/backend/tests/test_case_permission_runtime_router.py" in case_access_entry["evidence_paths"]
    assert "app/frontend/src/lib/caseApi.ts" in case_access_entry["evidence_paths"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in case_access_entry["evidence_paths"]
    assert "docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md" in case_access_entry["evidence_paths"]
    assert "case-access-control-runtime-gate" in case_access_entry["release_gate_links"]
    assert "case-role-permission-matrix" in case_access_entry["release_gate_links"]
    assert "case-team-access-policy" in case_access_entry["release_gate_links"]
    assert "admin-audit-policy" in completed_ids
    assert "legal-fixture-regression-comparison" in completed_ids
    assert "user-need-benchmark-coverage" in completed_ids
    assert "user-need-public-benchmark-mapping" in completed_ids
    assert "user-need-implementation-priority-queue" in completed_ids
    assert "user-need-gemini-route-coverage" in completed_ids
    assert "continuous-session-evidence-validator" not in queue_ids
    assert "continuous-session-timeline" not in queue_ids
    assert "continuous-session-run-monitor" not in queue_ids
    assert "git-history-cadence-evidence" not in queue_ids
    assert "validation-event-evidence-normalizer" not in queue_ids
    assert "continuous-session-review-packet" not in queue_ids
    assert "continuous-session-low-resource-fixture-review" not in queue_ids
    assert "continuous-ledger-low-resource-fixture-evidence" not in queue_ids
    assert "gemini-newapi-model-selector" not in queue_ids
    assert "gemini-newapi-observed-model-extraction" not in queue_ids
    assert "gemini-newapi-extractor-rejection-taxonomy" not in queue_ids
    assert "gemini-newapi-model-alias-matrix" not in queue_ids
    assert "gemini-newapi-alias-capability-coverage" not in queue_ids
    assert "gemini-newapi-selector-replay" not in queue_ids
    assert "gemini-newapi-cheap-first-calibration" not in queue_ids
    assert "modelops-cheap-first-calibration-review-form" not in queue_ids
    assert "gemini-model-variant-matrix" not in queue_ids
    assert "modelops-gemini-variant-review-form" not in queue_ids
    assert "gemini-variant-model-list-ingestion" not in queue_ids
    assert "modelops-load-performance-budget" not in queue_ids
    assert "modelops-performance-observation-review" not in queue_ids
    assert "modelops-performance-observation-release-binding" not in queue_ids
    assert "modelops-first-paint-aggregate-binding" not in queue_ids
    assert "modelops-cheap-first-quality-budget" not in queue_ids
    assert "gemini-catalog-source-audit" not in queue_ids
    assert "model-catalog-candidate-patch-plan" not in queue_ids
    assert "model-catalog-candidate-impact-replay" not in queue_ids
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
    assert "modelops-gemini-cheap-first-route-preflight" not in queue_ids
    assert "modelops-gemini-embedding-cheap-first-preflight" not in queue_ids
    assert "model-gateway-request-compatibility-gate" not in queue_ids
    assert "modelops-legal-micro-benchmark-preflight" not in queue_ids
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" not in queue_ids
    assert "legal-document-fact-consistency-benchmark" not in queue_ids
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" not in queue_ids
    assert "modelops-legal-fixture-modelops-ui-binding" not in queue_ids
    assert "modelops-agentic-grounded-defaults" not in queue_ids
    assert "modelops-default-template-alignment" not in queue_ids
    assert "modelops-gemini-default-change-review" not in queue_ids
    assert "modelops-gemini-default-cost-impact" not in queue_ids
    assert "modelops-observed-gemini-model-intake-queue" not in queue_ids
    assert "modelops-observed-gemini-coverage-gap-queue" not in queue_ids
    assert "modelops-gemini-official-model-family-roadmap-evidence" not in queue_ids
    assert "route-telemetry-repository" not in queue_ids
    assert "runtime-route-reason-codes" not in queue_ids
    assert "pdf-image-route-telemetry" not in queue_ids
    assert "image-auto-route-default" not in queue_ids
    assert "image-price-refresh-monitor" not in queue_ids
    assert "image-gateway-health-plan" not in queue_ids
    assert "image-gateway-probe-evaluation" not in queue_ids
    assert "gateway-probe-secret-value-guard" not in queue_ids
    assert "gateway-probe-readiness-binding" not in queue_ids
    assert "gateway-probe-latest-evidence-store" not in queue_ids
    assert "model-ops-readiness-required-optional-summary" not in queue_ids
    assert "model-ops-readiness-warning-drilldown" not in queue_ids
    assert "route-telemetry-ops-summary" not in queue_ids
    assert "route-telemetry-triage-queue" not in queue_ids
    assert "route-telemetry-reason-code-hotspots" not in queue_ids
    assert "route-telemetry-remediation-plan" not in queue_ids
    assert "route-telemetry-ui-regression-contract" not in queue_ids
    assert "runtime-router-discovery-smoke" not in queue_ids
    assert "case-workbench-frontend-state-events" not in queue_ids
    assert "legal-rag-case-research-ui" not in queue_ids
    assert "case-export-readiness-download-gate" not in queue_ids
    assert "deep-review-export-readiness-route-gate" not in queue_ids
    assert "deep-review-ocr-readiness-runtime-binding" not in queue_ids
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
    assert "legal-document-template-benchmark-alignment" not in queue_ids
    assert "legal-document-benchmark-coverage-ui" not in queue_ids
    assert "legal-document-benchmark-fixture-ui" not in queue_ids
    assert "legal-document-coverage-claim-policy" not in queue_ids
    assert "legal-benchmark-research-registry" not in queue_ids
    assert "legal-benchmark-research-refresh" not in queue_ids
    assert "legal-public-benchmark-license-gate" not in queue_ids
    assert "model-route-legal-benchmark-risk-queue" not in queue_ids
    assert "modelops-legal-benchmark-risk-bridge" not in queue_ids
    assert "legal-benchmark-research-registry-ui" not in queue_ids
    assert "legal-rag-abstention-escalation-gate" not in queue_ids
    assert "legal-rag-retrieval-diagnostics-gate" not in queue_ids
    assert "legal-rag-index-coverage-gate" not in queue_ids
    assert "legal-rag-embedding-readiness-gate" not in queue_ids
    assert "legal-rag-embedding-chunk-policy-gate" not in queue_ids
    assert "legal-rag-embedding-index-dry-run-gate" not in queue_ids
    assert "legal-rag-embedding-batch-budget-gate" not in queue_ids
    assert "legal-rag-embedding-batch-approval-packet" not in queue_ids
    assert "legal-rag-embedding-batch-observation-gate" not in queue_ids
    assert "legal-rag-embedding-index-commit-review-packet" not in queue_ids
    assert "legal-rag-embedding-index-post-commit-verification-gate" not in queue_ids
    assert "legal-rag-embedding-retrieval-diagnostics-handoff-gate" not in queue_ids
    assert "legal-rag-benchmark-alignment" not in queue_ids
    assert "legal-rag-retrieval-observation-gate" not in queue_ids
    assert "legal-rag-answer-release-readiness-gate" not in queue_ids
    assert "legal-rag-retrieval-observation-ui-binding" not in queue_ids
    assert "legal-adoption-research-bridge" not in queue_ids
    assert "deep-review-selected-source-binding" not in queue_ids
    assert "legal-rag-export-readiness-packet" not in queue_ids
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
    assert "user-need-gemini-route-coverage" not in queue_ids
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
    assert (
        "python -m pytest tests/test_deep_review_ocr_readiness_runtime.py "
        "tests/test_ocr_import_readiness_policy.py -q && cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_case_access_control.py tests/test_case_permission_runtime_router.py "
        "tests/test_case_role_permission_matrix.py tests/test_case_team_access_policy.py -q && "
        "cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_gemini_newapi_model_selector.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py "
        "tests/test_gemini_model_variant_matrix.py tests/test_gemini_newapi_model_selector.py "
        "tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py "
        "tests/test_model_catalog_candidate_patch_plan.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py "
        "tests/test_gemini_newapi_model_alias_matrix.py "
        "tests/test_gemini_newapi_alias_capability_coverage.py "
        "tests/test_model_catalog_candidate_patch_plan.py -q && cd ../frontend && npm run typecheck && "
        "npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_gemini_newapi_model_alias_matrix.py "
        "tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_gemini_newapi_alias_capability_coverage.py "
        "tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py "
        "tests/test_model_catalog.py tests/test_model_ops_readiness.py -q && cd ../frontend && "
        "npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_catalog.py tests/test_gemini_newapi_model_alias_matrix.py "
        "tests/test_gemini_newapi_alias_capability_coverage.py tests/test_gemini_model_variant_matrix.py "
        "tests/test_model_catalog_source_audit.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_gemini_official_model_family_roadmap.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
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
    assert (
        "python -m pytest tests/test_model_ops_performance_budget.py "
        "tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && "
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
    assert (
        "python -m pytest tests/test_model_default_candidate_selector.py "
        "tests/test_gemini_newapi_model_selector.py -q && cd ../frontend && npm run typecheck"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_runtime_router.py tests/test_route_telemetry_repository.py "
        "tests/test_route_telemetry_persistence_plan.py tests/test_aihub_runtime_routing.py "
        "tests/test_release_readiness.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_route_telemetry_repository.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_route_telemetry_repository.py tests/test_aihub_runtime_routing.py "
        "tests/test_model_usage.py -q"
        in ledger["validation_commands"]
    )
    assert "python -m pytest tests/test_route_telemetry_ops_summary.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_route_telemetry_triage_queue.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_route_telemetry_remediation_plan.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_frontend_ui_regression_gate.py tests/test_continuous_update_ledger.py -q "
        "&& cd ../frontend && npm run ui:regression"
    ) in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_document_benchmark_coverage.py -q" in ledger["validation_commands"]
    assert "python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_legal_document_template_matrix.py "
        "tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py "
        "tests/test_legal_document_coverage_claim_policy.py -q"
        in ledger["validation_commands"]
    )
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
    assert "python -m pytest tests/test_legal_rag_evaluation.py -q" in ledger["validation_commands"]
    assert (
        "python -m pytest tests/test_deep_review_export_gate.py tests/test_case_export_readiness.py -q"
        in ledger["validation_commands"]
    )
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
        "python -m pytest tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_readiness.py "
        "tests/test_model_ops_cheap_first_release_decision.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_failure_upgrade_budget.py tests/test_model_ops_readiness.py "
        "tests/test_model_ops_cheap_first_release_decision.py tests/test_frontend_ui_regression_gate.py -q "
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
        "python -m pytest tests/test_model_catalog_candidate_impact_replay.py "
        "tests/test_model_default_candidate_selector.py tests/test_model_capability_matrix.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
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
        "python -m pytest tests/test_modelops_legal_micro_benchmark_preflight.py "
        "tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
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
    assert "shared observed-model extraction" in alias_matrix_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in alias_matrix_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in alias_matrix_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in alias_matrix_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_model_alias_matrix.py" in alias_matrix_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_MODEL_ALIAS_MATRIX.md" in alias_matrix_entry["evidence_paths"]
    assert "gemini-newapi-model-alias-matrix" in alias_matrix_entry["release_gate_links"]
    assert "gemini-newapi-model-selector" in alias_matrix_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in alias_matrix_entry["release_gate_links"]
    observed_extraction_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gemini-newapi-observed-model-extraction"
    )
    assert observed_extraction_entry["size"] == "medium"
    assert observed_extraction_entry["status"] == "shipped"
    assert "shared extractor" in observed_extraction_entry["impact"]
    assert "OpenAI-compatible /models responses" in observed_extraction_entry["impact"]
    assert "Gemini native wrappers" in observed_extraction_entry["impact"]
    assert "gateway probe rows" in observed_extraction_entry["impact"]
    assert "intake queue rows" in observed_extraction_entry["impact"]
    assert "sensitive/invalid/total rejection counts" in observed_extraction_entry["impact"]
    assert "no raw payloads" in observed_extraction_entry["impact"]
    assert "gateway calls" in observed_extraction_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in observed_extraction_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in observed_extraction_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_model_variant_matrix.py" in observed_extraction_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_selector.py" in observed_extraction_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in observed_extraction_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_alias_capability_coverage.py" in observed_extraction_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in observed_extraction_entry["evidence_paths"]
    assert "gemini-newapi-observed-model-extraction" in observed_extraction_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in observed_extraction_entry["release_gate_links"]
    assert "gemini-newapi-alias-capability-coverage" in observed_extraction_entry["release_gate_links"]
    assert "model-catalog-candidate-patch-plan" in observed_extraction_entry["release_gate_links"]
    rejection_taxonomy_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gemini-newapi-extractor-rejection-taxonomy"
    )
    assert rejection_taxonomy_entry["size"] == "medium"
    assert rejection_taxonomy_entry["status"] == "shipped"
    assert "Separates sensitive observed model values" in rejection_taxonomy_entry["impact"]
    assert "malformed model-list metadata" in rejection_taxonomy_entry["impact"]
    assert "sensitive/invalid/total rejected counts" in rejection_taxonomy_entry["impact"]
    assert "maintenance UI" in rejection_taxonomy_entry["impact"]
    assert "total rejected model count" in rejection_taxonomy_entry["impact"]
    assert "without echoing rejected raw values" in rejection_taxonomy_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in rejection_taxonomy_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in rejection_taxonomy_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in rejection_taxonomy_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_alias_capability_coverage.py" in rejection_taxonomy_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in rejection_taxonomy_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in rejection_taxonomy_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in rejection_taxonomy_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_MODEL_ALIAS_MATRIX.md" in rejection_taxonomy_entry["evidence_paths"]
    assert "gemini-newapi-observed-model-extraction" in rejection_taxonomy_entry["release_gate_links"]
    assert "frontend-ui-regression" in rejection_taxonomy_entry["release_gate_links"]
    alias_capability_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gemini-newapi-alias-capability-coverage"
    )
    assert alias_capability_entry["size"] == "medium"
    assert alias_capability_entry["status"] == "shipped"
    assert "yibuapi" in alias_capability_entry["impact"]
    assert "Gemini native action-suffix aliases" in alias_capability_entry["impact"]
    assert "task coverage" in alias_capability_entry["impact"]
    assert "without gateway calls" in alias_capability_entry["impact"]
    assert "configuration writes" in alias_capability_entry["impact"]
    assert "credentials" in alias_capability_entry["impact"]
    assert "shared observed-model extraction" in alias_capability_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in alias_capability_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_alias_capability_coverage.py" in alias_capability_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in alias_capability_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_alias_capability_coverage.py" in alias_capability_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in alias_capability_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in alias_capability_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in alias_capability_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in alias_capability_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_ALIAS_CAPABILITY_COVERAGE.md" in alias_capability_entry["evidence_paths"]
    assert "gemini-newapi-alias-capability-coverage" in alias_capability_entry["release_gate_links"]
    assert "gemini-newapi-model-alias-matrix" in alias_capability_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in alias_capability_entry["release_gate_links"]
    assert "model-ops-readiness" in alias_capability_entry["release_gate_links"]
    assert "frontend-ui-regression" in alias_capability_entry["release_gate_links"]
    official_preview_alias_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "gemini-official-preview-alias-review"
    )
    assert official_preview_alias_entry["category"] == "model_ops"
    assert official_preview_alias_entry["size"] == "medium"
    assert official_preview_alias_entry["status"] == "shipped"
    assert "Gemini 3 Flash Preview" in official_preview_alias_entry["impact"]
    assert "NewAPI/YibuAPI/publishers Google prefix compatibility" in official_preview_alias_entry["impact"]
    assert "Gemini 3.5 Flash posture" in official_preview_alias_entry["impact"]
    assert "stable Flash-Lite routes" in official_preview_alias_entry["impact"]
    assert "calling gateways" in official_preview_alias_entry["impact"]
    assert "raw legal text" in official_preview_alias_entry["impact"]
    assert "credentials" in official_preview_alias_entry["impact"]
    assert "app/backend/services/model_catalog.py" in official_preview_alias_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in official_preview_alias_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_newapi_alias_capability_coverage.py" in official_preview_alias_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_model_variant_matrix.py" in official_preview_alias_entry["evidence_paths"]
    assert "app/backend/services/model_catalog_source_audit.py" in official_preview_alias_entry["evidence_paths"]
    assert "app/backend/tests/test_model_catalog.py" in official_preview_alias_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_model_alias_matrix.py" in official_preview_alias_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_gemini_newapi_alias_capability_coverage.py" in official_preview_alias_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_gemini_model_variant_matrix.py" in official_preview_alias_entry["evidence_paths"]
    assert "app/backend/tests/test_model_catalog_source_audit.py" in official_preview_alias_entry["evidence_paths"]
    assert "gemini-newapi-model-alias-matrix" in official_preview_alias_entry["release_gate_links"]
    assert "gemini-newapi-alias-capability-coverage" in official_preview_alias_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in official_preview_alias_entry["release_gate_links"]
    assert "model-catalog-source-audit" in official_preview_alias_entry["release_gate_links"]
    assert "model-ops-readiness" in official_preview_alias_entry["release_gate_links"]
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
    route_preflight_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-gemini-cheap-first-route-preflight"
    )
    assert route_preflight_entry["size"] == "medium"
    assert route_preflight_entry["status"] == "shipped"
    assert "Gemini cheap-first route preflight evidence" in route_preflight_entry["impact"]
    assert "POST review form coverage" in route_preflight_entry["impact"]
    assert "official source refresh notes" in route_preflight_entry["impact"]
    assert "local task defaults" in route_preflight_entry["impact"]
    assert "observed model id metadata" in route_preflight_entry["impact"]
    assert "variant review states" in route_preflight_entry["impact"]
    assert "alias capability coverage" in route_preflight_entry["impact"]
    assert "cheap-first coverage-gate signals" in route_preflight_entry["impact"]
    assert "stable Flash-Lite defaults" in route_preflight_entry["impact"]
    assert "review/explicit-only" in route_preflight_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/app-AI/network calls" in route_preflight_entry["impact"]
    assert "configuration writes" in route_preflight_entry["impact"]
    assert "traffic shifts" in route_preflight_entry["impact"]
    assert "request or response bodies" in route_preflight_entry["impact"]
    assert "headers" in route_preflight_entry["impact"]
    assert "prompts" in route_preflight_entry["impact"]
    assert "raw payloads" in route_preflight_entry["impact"]
    assert "legal text" in route_preflight_entry["impact"]
    assert "model outputs" in route_preflight_entry["impact"]
    assert "gateway responses" in route_preflight_entry["impact"]
    assert "credentials" in route_preflight_entry["impact"]
    assert "emails" in route_preflight_entry["impact"]
    assert "user identifiers" in route_preflight_entry["impact"]
    assert "app/backend/services/model_ops_gemini_cheap_first_route_preflight.py" in route_preflight_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_gemini_cheap_first_route_preflight.py" in route_preflight_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in route_preflight_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in route_preflight_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in route_preflight_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in route_preflight_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in route_preflight_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in route_preflight_entry["evidence_paths"]
    assert "docs/MODELOPS_GEMINI_CHEAP_FIRST_ROUTE_PREFLIGHT.md" in route_preflight_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in route_preflight_entry["evidence_paths"]
    assert "modelops-gemini-cheap-first-route-preflight" in route_preflight_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in route_preflight_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in route_preflight_entry["release_gate_links"]
    assert "gemini-newapi-alias-capability-coverage" in route_preflight_entry["release_gate_links"]
    assert "model-gateway-request-compatibility-gate" in route_preflight_entry["release_gate_links"]
    assert "model-ops-readiness" in route_preflight_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in route_preflight_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in route_preflight_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_ops_gemini_cheap_first_route_preflight.py "
        "tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    aihub_route_coverage_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-aihub-endpoint-route-coverage-gate"
    )
    assert aihub_route_coverage_entry["size"] == "medium"
    assert aihub_route_coverage_entry["status"] == "shipped"
    assert aihub_route_coverage_entry["category"] == "model_ops"
    assert "AIHub endpoint route coverage gate evidence" in aihub_route_coverage_entry["impact"]
    assert "gentxt streaming" in aihub_route_coverage_entry["impact"]
    assert "runtime-router coverage" in aihub_route_coverage_entry["impact"]
    assert "budget-decision coverage" in aihub_route_coverage_entry["impact"]
    assert "route telemetry coverage" in aihub_route_coverage_entry["impact"]
    assert "response route-payload coverage" in aihub_route_coverage_entry["impact"]
    assert "media/speech catalog review gaps" in aihub_route_coverage_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/app-AI/model/network calls" in aihub_route_coverage_entry["impact"]
    assert "configuration writes" in aihub_route_coverage_entry["impact"]
    assert "traffic shifts" in aihub_route_coverage_entry["impact"]
    assert "request or response bodies" in aihub_route_coverage_entry["impact"]
    assert "headers" in aihub_route_coverage_entry["impact"]
    assert "prompts" in aihub_route_coverage_entry["impact"]
    assert "raw payloads" in aihub_route_coverage_entry["impact"]
    assert "legal text" in aihub_route_coverage_entry["impact"]
    assert "model outputs" in aihub_route_coverage_entry["impact"]
    assert "gateway responses" in aihub_route_coverage_entry["impact"]
    assert "credentials" in aihub_route_coverage_entry["impact"]
    assert "emails" in aihub_route_coverage_entry["impact"]
    assert "user identifiers" in aihub_route_coverage_entry["impact"]
    assert "app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py" in aihub_route_coverage_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py" in aihub_route_coverage_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_readiness.py" in aihub_route_coverage_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in aihub_route_coverage_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in aihub_route_coverage_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in aihub_route_coverage_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in aihub_route_coverage_entry["evidence_paths"]
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in aihub_route_coverage_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in aihub_route_coverage_entry["evidence_paths"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in aihub_route_coverage_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in aihub_route_coverage_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in aihub_route_coverage_entry["release_gate_links"]
    assert "model-gateway-request-compatibility-gate" in aihub_route_coverage_entry["release_gate_links"]
    assert "model-ops-readiness" in aihub_route_coverage_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in aihub_route_coverage_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_ops_aihub_endpoint_route_coverage_gate.py "
        "tests/test_model_ops_readiness.py tests/test_aihub_runtime_routing.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    media_speech_default_catalog_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-aihub-media-speech-default-catalog-gate"
    )
    assert media_speech_default_catalog_entry["size"] == "medium"
    assert media_speech_default_catalog_entry["status"] == "shipped"
    assert media_speech_default_catalog_entry["category"] == "model_ops"
    assert "required metadata-only release evidence" in media_speech_default_catalog_entry["impact"]
    assert "/api/v1/aihub/models/aihub-media-speech-default-catalog-gate" in media_speech_default_catalog_entry["impact"]
    assert "image, video, audio, transcription, future Live audio, and embedding" in media_speech_default_catalog_entry["impact"]
    assert "endpoint route coverage" in media_speech_default_catalog_entry["impact"]
    assert "local catalog status" in media_speech_default_catalog_entry["impact"]
    assert "explicit media/speech budget modes" in media_speech_default_catalog_entry["impact"]
    assert "official Gemini/Veo/TTS source anchors" in media_speech_default_catalog_entry["impact"]
    assert "default release actions" in media_speech_default_catalog_entry["impact"]
    assert "explicit-review only" in media_speech_default_catalog_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/app-AI/model/network calls" in media_speech_default_catalog_entry["impact"]
    assert "configuration writes" in media_speech_default_catalog_entry["impact"]
    assert "default changes" in media_speech_default_catalog_entry["impact"]
    assert "traffic shifts" in media_speech_default_catalog_entry["impact"]
    assert "request or response bodies" in media_speech_default_catalog_entry["impact"]
    assert "headers" in media_speech_default_catalog_entry["impact"]
    assert "prompts" in media_speech_default_catalog_entry["impact"]
    assert "raw payloads" in media_speech_default_catalog_entry["impact"]
    assert "audio" in media_speech_default_catalog_entry["impact"]
    assert "transcripts" in media_speech_default_catalog_entry["impact"]
    assert "model outputs" in media_speech_default_catalog_entry["impact"]
    assert "gateway responses" in media_speech_default_catalog_entry["impact"]
    assert "credentials" in media_speech_default_catalog_entry["impact"]
    assert "emails" in media_speech_default_catalog_entry["impact"]
    assert "user identifiers" in media_speech_default_catalog_entry["impact"]
    assert "app/backend/services/model_ops_aihub_media_speech_default_catalog_gate.py" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_aihub_media_speech_default_catalog_gate.py" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_readiness.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/backend/tests/test_frontend_ui_regression_gate.py" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in media_speech_default_catalog_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in media_speech_default_catalog_entry["evidence_paths"]
    assert "docs/MODELOPS_AIHUB_MEDIA_SPEECH_DEFAULT_CATALOG_GATE.md" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in media_speech_default_catalog_entry[
        "evidence_paths"
    ]
    assert "docs/MODEL_OPS_READINESS.md" in media_speech_default_catalog_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in media_speech_default_catalog_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in media_speech_default_catalog_entry["evidence_paths"]
    assert "docs/FRONTEND_UI_REGRESSION_GATE.md" in media_speech_default_catalog_entry["evidence_paths"]
    assert "docs/RELEASE_READINESS.md" in media_speech_default_catalog_entry["evidence_paths"]
    assert "modelops-aihub-media-speech-default-catalog-gate" in media_speech_default_catalog_entry[
        "release_gate_links"
    ]
    assert "modelops-aihub-endpoint-route-coverage-gate" in media_speech_default_catalog_entry[
        "release_gate_links"
    ]
    assert "modelops-gemini-official-model-family-roadmap-evidence" in media_speech_default_catalog_entry[
        "release_gate_links"
    ]
    assert "modelops-gemini-cheap-first-route-preflight" in media_speech_default_catalog_entry[
        "release_gate_links"
    ]
    assert "model-ops-readiness" in media_speech_default_catalog_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in media_speech_default_catalog_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_ops_aihub_media_speech_default_catalog_gate.py "
        "tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    media_speech_review_catalog_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "gemini-media-speech-review-catalog"
    )
    assert media_speech_review_catalog_entry["category"] == "model_ops"
    assert media_speech_review_catalog_entry["size"] == "medium"
    assert media_speech_review_catalog_entry["status"] == "shipped"
    assert "Veo 3.1 video" in media_speech_review_catalog_entry["impact"]
    assert "Gemini TTS" in media_speech_review_catalog_entry["impact"]
    assert "Gemini Live/native-audio" in media_speech_review_catalog_entry["impact"]
    assert "kept out of high-frequency defaults" in media_speech_review_catalog_entry["impact"]
    assert "Current APP_AI_VIDEO_MODEL" in media_speech_review_catalog_entry["impact"]
    assert "APP_AI_AUDIO_MODEL" in media_speech_review_catalog_entry["impact"]
    assert "APP_AI_TRANSCRIPTION_MODEL defaults remain unchanged" in media_speech_review_catalog_entry["impact"]
    assert "audio/video candidate pricing stays explicit-review only" in media_speech_review_catalog_entry["impact"]
    assert "default changes" in media_speech_review_catalog_entry["impact"]
    assert "credentials" in media_speech_review_catalog_entry["impact"]
    assert "app/backend/services/model_catalog.py" in media_speech_review_catalog_entry["evidence_paths"]
    assert "app/backend/services/model_default_candidate_selector.py" in media_speech_review_catalog_entry["evidence_paths"]
    assert "app/backend/services/model_ops_gemini_official_model_family_roadmap.py" in media_speech_review_catalog_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_model_variant_matrix.py" in media_speech_review_catalog_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_model_variant_matrix.py" in media_speech_review_catalog_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in media_speech_review_catalog_entry["evidence_paths"]
    assert "gemini-media-speech-review-catalog" in media_speech_review_catalog_entry["release_gate_links"]
    assert "modelops-aihub-media-speech-default-catalog-gate" in media_speech_review_catalog_entry[
        "release_gate_links"
    ]
    assert "gemini-variant-matrix" in media_speech_review_catalog_entry["release_gate_links"]
    gemini_embedding_preflight_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-gemini-embedding-cheap-first-preflight"
    )
    assert gemini_embedding_preflight_entry["size"] == "medium"
    assert gemini_embedding_preflight_entry["status"] == "shipped"
    assert gemini_embedding_preflight_entry["category"] == "model_ops"
    assert "required metadata-only Gemini embedding cheap-first preflight evidence" in gemini_embedding_preflight_entry["impact"]
    assert "/api/v1/aihub/models/gemini-embedding-cheap-first-preflight" in gemini_embedding_preflight_entry["impact"]
    assert "APP_AI_EMBEDDING_MODEL=gemini-embedding-001" in gemini_embedding_preflight_entry["impact"]
    assert "auto-embedding aliases" in gemini_embedding_preflight_entry["impact"]
    assert "local catalog pricing" in gemini_embedding_preflight_entry["impact"]
    assert "cheap-first embedding budget policy" in gemini_embedding_preflight_entry["impact"]
    assert "multimodal gemini-embedding-2 review routing" in gemini_embedding_preflight_entry["impact"]
    assert "Text embedding defaults stay on gemini-embedding-001" in gemini_embedding_preflight_entry["impact"]
    assert "multimodal gemini-embedding-2 remains review-required" in gemini_embedding_preflight_entry["impact"]
    assert "source-index use" in gemini_embedding_preflight_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/app-AI/model/network calls" in gemini_embedding_preflight_entry[
        "impact"
    ]
    assert "configuration writes" in gemini_embedding_preflight_entry["impact"]
    assert "default changes" in gemini_embedding_preflight_entry["impact"]
    assert "index writes" in gemini_embedding_preflight_entry["impact"]
    assert "traffic shifts" in gemini_embedding_preflight_entry["impact"]
    assert "source text" in gemini_embedding_preflight_entry["impact"]
    assert "raw legal text" in gemini_embedding_preflight_entry["impact"]
    assert "source chunks" in gemini_embedding_preflight_entry["impact"]
    assert "embedding vectors" in gemini_embedding_preflight_entry["impact"]
    assert "request bodies" in gemini_embedding_preflight_entry["impact"]
    assert "response bodies" in gemini_embedding_preflight_entry["impact"]
    assert "headers" in gemini_embedding_preflight_entry["impact"]
    assert "prompts" in gemini_embedding_preflight_entry["impact"]
    assert "raw payloads" in gemini_embedding_preflight_entry["impact"]
    assert "model outputs" in gemini_embedding_preflight_entry["impact"]
    assert "gateway responses" in gemini_embedding_preflight_entry["impact"]
    assert "credentials" in gemini_embedding_preflight_entry["impact"]
    assert "emails" in gemini_embedding_preflight_entry["impact"]
    assert "user identifiers" in gemini_embedding_preflight_entry["impact"]
    assert "app/backend/services/model_ops_gemini_embedding_cheap_first_preflight.py" in gemini_embedding_preflight_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_gemini_embedding_cheap_first_preflight.py" in gemini_embedding_preflight_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_catalog.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/services/model_budget.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/tests/test_frontend_ui_regression_gate.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "docs/MODELOPS_GEMINI_EMBEDDING_CHEAP_FIRST_PREFLIGHT.md" in gemini_embedding_preflight_entry[
        "evidence_paths"
    ]
    assert "docs/MODEL_OPS_READINESS.md" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "docs/FRONTEND_UI_REGRESSION_GATE.md" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "docs/RELEASE_READINESS.md" in gemini_embedding_preflight_entry["evidence_paths"]
    assert "modelops-gemini-embedding-cheap-first-preflight" in gemini_embedding_preflight_entry[
        "release_gate_links"
    ]
    assert "modelops-aihub-media-speech-default-catalog-gate" in gemini_embedding_preflight_entry[
        "release_gate_links"
    ]
    assert "modelops-gemini-official-model-family-roadmap-evidence" in gemini_embedding_preflight_entry[
        "release_gate_links"
    ]
    assert "modelops-gemini-cheap-first-route-preflight" in gemini_embedding_preflight_entry[
        "release_gate_links"
    ]
    assert "model-ops-readiness" in gemini_embedding_preflight_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in gemini_embedding_preflight_entry["release_gate_links"]
    assert "frontend-typecheck" in gemini_embedding_preflight_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_ops_gemini_embedding_cheap_first_preflight.py "
        "tests/test_model_catalog.py tests/test_model_budget.py tests/test_model_configuration_audit.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    media_speech_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "aihub-media-speech-runtime-routing"
    )
    assert media_speech_entry["size"] == "medium"
    assert media_speech_entry["status"] == "shipped"
    assert media_speech_entry["category"] == "model_ops"
    assert "video generation, audio generation, and transcription" in media_speech_entry["impact"]
    assert "explicit media/speech budget tasks" in media_speech_entry["impact"]
    assert "runtime model policy" in media_speech_entry["impact"]
    assert "sanitized route telemetry" in media_speech_entry["impact"]
    assert "response route payload metadata" in media_speech_entry["impact"]
    assert "review-only" in media_speech_entry["impact"]
    assert "without provider calls" in media_speech_entry["impact"]
    assert "gateway calls" in media_speech_entry["impact"]
    assert "prompts" in media_speech_entry["impact"]
    assert "audio" in media_speech_entry["impact"]
    assert "transcripts" in media_speech_entry["impact"]
    assert "output URLs" in media_speech_entry["impact"]
    assert "revised prompts" in media_speech_entry["impact"]
    assert "headers" in media_speech_entry["impact"]
    assert "payloads" in media_speech_entry["impact"]
    assert "credentials" in media_speech_entry["impact"]
    assert "app/backend/services/aihub.py" in media_speech_entry["evidence_paths"]
    assert "app/backend/services/model_task_inference.py" in media_speech_entry["evidence_paths"]
    assert "app/backend/tests/test_model_task_inference.py" in media_speech_entry["evidence_paths"]
    assert "docs/MODEL_RUNTIME_ROUTER.md" in media_speech_entry["evidence_paths"]
    route_payload_units_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "aihub-route-payload-usage-units"
    )
    assert route_payload_units_entry["size"] == "medium"
    assert route_payload_units_entry["status"] == "shipped"
    assert route_payload_units_entry["category"] == "model_ops"
    assert "PDF analysis and image generation responses" in route_payload_units_entry["impact"]
    assert "task inference and media usage-unit response coverage" in route_payload_units_entry["impact"]
    assert "image, video, audio, and transcription routes" in route_payload_units_entry["impact"]
    assert "ModelOps" in route_payload_units_entry["impact"]
    assert "without provider calls" in route_payload_units_entry["impact"]
    assert "gateway calls" in route_payload_units_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google calls" in route_payload_units_entry["impact"]
    assert "prompts" in route_payload_units_entry["impact"]
    assert "PDF bytes" in route_payload_units_entry["impact"]
    assert "image bytes" in route_payload_units_entry["impact"]
    assert "transcripts" in route_payload_units_entry["impact"]
    assert "output URLs" in route_payload_units_entry["impact"]
    assert "credentials" in route_payload_units_entry["impact"]
    assert "app/backend/services/aihub.py" in route_payload_units_entry["evidence_paths"]
    assert "app/backend/schemas/aihub.py" in route_payload_units_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in route_payload_units_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in route_payload_units_entry["evidence_paths"]
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in route_payload_units_entry["evidence_paths"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in route_payload_units_entry["release_gate_links"]
    assert "aihub-media-speech-runtime-routing" in route_payload_units_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in route_payload_units_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in route_payload_units_entry["release_gate_links"]
    gentxt_routing_guard_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gentxt-routing-media-guard"
    )
    assert gentxt_routing_guard_entry["size"] == "medium"
    assert gentxt_routing_guard_entry["status"] == "shipped"
    assert gentxt_routing_guard_entry["category"] == "model_ops"
    assert "metadata-only gentxt routing guard evidence" in gentxt_routing_guard_entry["impact"]
    assert "image, video, audio, transcription" in gentxt_routing_guard_entry["impact"]
    assert "text endpoint" in gentxt_routing_guard_entry["impact"]
    assert "media endpoints" in gentxt_routing_guard_entry["impact"]
    assert "service integration coverage" in gentxt_routing_guard_entry["impact"]
    assert "does not call media default models" in gentxt_routing_guard_entry["impact"]
    assert "ModelOps" in gentxt_routing_guard_entry["impact"]
    assert "provider calls" in gentxt_routing_guard_entry["impact"]
    assert "gateway calls" in gentxt_routing_guard_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google calls" in gentxt_routing_guard_entry["impact"]
    assert "configuration writes" in gentxt_routing_guard_entry["impact"]
    assert "traffic shifts" in gentxt_routing_guard_entry["impact"]
    assert "request bodies" in gentxt_routing_guard_entry["impact"]
    assert "response bodies" in gentxt_routing_guard_entry["impact"]
    assert "headers" in gentxt_routing_guard_entry["impact"]
    assert "prompts" in gentxt_routing_guard_entry["impact"]
    assert "raw payloads" in gentxt_routing_guard_entry["impact"]
    assert "model outputs" in gentxt_routing_guard_entry["impact"]
    assert "credentials" in gentxt_routing_guard_entry["impact"]
    assert "app/backend/services/model_ops_gentxt_task_guard.py" in gentxt_routing_guard_entry["evidence_paths"]
    assert "app/backend/services/model_task_inference.py" in gentxt_routing_guard_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_gentxt_task_guard.py" in gentxt_routing_guard_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in gentxt_routing_guard_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gentxt_routing_guard_entry["evidence_paths"]
    assert "docs/MODELOPS_GENTXT_ROUTING_GUARD.md" in gentxt_routing_guard_entry["evidence_paths"]
    assert "modelops-gentxt-routing-guard" in gentxt_routing_guard_entry["release_gate_links"]
    assert "model-task-inference" in gentxt_routing_guard_entry["release_gate_links"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in gentxt_routing_guard_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in gentxt_routing_guard_entry["release_gate_links"]
    gentxt_stream_metadata_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "gentxt-stream-route-metadata"
    )
    assert gentxt_stream_metadata_entry["size"] == "medium"
    assert gentxt_stream_metadata_entry["status"] == "shipped"
    assert gentxt_stream_metadata_entry["category"] == "model_ops"
    assert "metadata-first SSE route evidence" in gentxt_stream_metadata_entry["impact"]
    assert "gentxt streaming responses" in gentxt_stream_metadata_entry["impact"]
    assert "stream route payload and task inference coverage gap" in gentxt_stream_metadata_entry["impact"]
    assert "legacy content-only service wrapper" in gentxt_stream_metadata_entry["impact"]
    assert "ModelOps coverage counts" in gentxt_stream_metadata_entry["impact"]
    assert "provider calls" in gentxt_stream_metadata_entry["impact"]
    assert "gateway calls" in gentxt_stream_metadata_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google calls" in gentxt_stream_metadata_entry["impact"]
    assert "configuration writes" in gentxt_stream_metadata_entry["impact"]
    assert "traffic shifts" in gentxt_stream_metadata_entry["impact"]
    assert "request bodies" in gentxt_stream_metadata_entry["impact"]
    assert "response bodies" in gentxt_stream_metadata_entry["impact"]
    assert "headers" in gentxt_stream_metadata_entry["impact"]
    assert "prompts" in gentxt_stream_metadata_entry["impact"]
    assert "raw payloads" in gentxt_stream_metadata_entry["impact"]
    assert "model outputs" in gentxt_stream_metadata_entry["impact"]
    assert "credentials" in gentxt_stream_metadata_entry["impact"]
    assert "app/backend/services/aihub.py" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in gentxt_stream_metadata_entry["evidence_paths"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in gentxt_stream_metadata_entry["release_gate_links"]
    assert "aihub-route-payload-usage-units" in gentxt_stream_metadata_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in gentxt_stream_metadata_entry["release_gate_links"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in media_speech_entry["release_gate_links"]
    assert "runtime-router" in media_speech_entry["release_gate_links"]
    gateway_request_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-gateway-request-compatibility-gate"
    )
    assert gateway_request_gate_entry["size"] == "medium"
    assert gateway_request_gate_entry["status"] == "shipped"
    assert "OpenAI-compatible Gemini request-shape evidence" in gateway_request_gate_entry["impact"]
    assert "task defaults" in gateway_request_gate_entry["impact"]
    assert "gateway model compatibility" in gateway_request_gate_entry["impact"]
    assert "request parameter caps" in gateway_request_gate_entry["impact"]
    assert "reasoning_effort policy" in gateway_request_gate_entry["impact"]
    assert "cheap-first cost bounds" in gateway_request_gate_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in gateway_request_gate_entry["impact"]
    assert "configuration writes" in gateway_request_gate_entry["impact"]
    assert "traffic shifts" in gateway_request_gate_entry["impact"]
    assert "headers" in gateway_request_gate_entry["impact"]
    assert "request bodies" in gateway_request_gate_entry["impact"]
    assert "prompts" in gateway_request_gate_entry["impact"]
    assert "raw legal text" in gateway_request_gate_entry["impact"]
    assert "model outputs" in gateway_request_gate_entry["impact"]
    assert "payloads" in gateway_request_gate_entry["impact"]
    assert "emails" in gateway_request_gate_entry["impact"]
    assert "credentials" in gateway_request_gate_entry["impact"]
    assert "app/backend/services/model_gateway_request_compatibility_gate.py" in gateway_request_gate_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_gateway_request_compatibility_gate.py" in gateway_request_gate_entry[
        "evidence_paths"
    ]
    assert "app/backend/routers/aihub.py" in gateway_request_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in gateway_request_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gateway_request_gate_entry["evidence_paths"]
    assert "docs/MODEL_GATEWAY_REQUEST_COMPATIBILITY_GATE.md" in gateway_request_gate_entry["evidence_paths"]
    assert "model-gateway-request-compatibility-gate" in gateway_request_gate_entry["release_gate_links"]
    assert "model-request-policy" in gateway_request_gate_entry["release_gate_links"]
    assert "model-reasoning-policy" in gateway_request_gate_entry["release_gate_links"]
    assert "model-gateway-compatibility" in gateway_request_gate_entry["release_gate_links"]
    assert "model-request-cost-bounds" in gateway_request_gate_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in gateway_request_gate_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_gateway_request_compatibility_gate.py "
        "tests/test_model_request_policy.py tests/test_model_reasoning_policy.py "
        "tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    gateway_connection_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-gateway-connection-profile"
    )
    assert gateway_connection_entry["size"] == "medium"
    assert gateway_connection_entry["status"] == "shipped"
    assert "OpenAI-compatible gateway connection profile evidence" in gateway_connection_entry["impact"]
    assert "runtime base URL normalization" in gateway_connection_entry["impact"]
    assert "https://yibuapi.com" in gateway_connection_entry["impact"]
    assert "/v1 clients" in gateway_connection_entry["impact"]
    assert "credential-bearing URLs" in gateway_connection_entry["impact"]
    assert "insecure remote HTTP" in gateway_connection_entry["impact"]
    assert "unknown cheap-first role models" in gateway_connection_entry["impact"]
    assert "raw keys" in gateway_connection_entry["impact"]
    assert "Authorization headers" in gateway_connection_entry["impact"]
    assert "prompts" in gateway_connection_entry["impact"]
    assert "request bodies" in gateway_connection_entry["impact"]
    assert "response bodies" in gateway_connection_entry["impact"]
    assert "model outputs" in gateway_connection_entry["impact"]
    assert "gateway responses" in gateway_connection_entry["impact"]
    assert "configuration writes" in gateway_connection_entry["impact"]
    assert "app/backend/services/model_gateway_connection_profile.py" in gateway_connection_entry["evidence_paths"]
    assert "app/backend/tests/test_model_gateway_connection_profile.py" in gateway_connection_entry["evidence_paths"]
    assert "app/backend/services/model_gateway_health_plan.py" in gateway_connection_entry["evidence_paths"]
    assert "app/backend/services/aihub.py" in gateway_connection_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in gateway_connection_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in gateway_connection_entry["evidence_paths"]
    assert "docs/MODEL_GATEWAY_CONNECTION_PROFILE.md" in gateway_connection_entry["evidence_paths"]
    assert "model-gateway-connection-profile" in gateway_connection_entry["release_gate_links"]
    assert "model-gateway-health-plan" in gateway_connection_entry["release_gate_links"]
    assert "model-gateway-request-compatibility-gate" in gateway_connection_entry["release_gate_links"]
    assert "model-ops-readiness" in gateway_connection_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in gateway_connection_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_gateway_connection_profile.py "
        "tests/test_model_gateway_health_plan.py tests/test_aihub_runtime_routing.py "
        "tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && "
        "cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    gateway_runtime_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-gateway-runtime-configuration"
    )
    assert gateway_runtime_entry["size"] == "medium"
    assert gateway_runtime_entry["status"] == "shipped"
    assert "runtime gateway configuration evidence" in gateway_runtime_entry["impact"]
    assert "APP_AI_BASE_URL normalization" in gateway_runtime_entry["impact"]
    assert "APP_AI_KEY placeholder" in gateway_runtime_entry["impact"]
    assert "safe probe ordering" in gateway_runtime_entry["impact"]
    assert "without writing env files" in gateway_runtime_entry["impact"]
    assert "calling providers or the network" in gateway_runtime_entry["impact"]
    assert "Authorization headers" in gateway_runtime_entry["impact"]
    assert "request bodies" in gateway_runtime_entry["impact"]
    assert "model outputs" in gateway_runtime_entry["impact"]
    assert "credentials" in gateway_runtime_entry["impact"]
    assert "app/backend/services/model_gateway_runtime_configuration.py" in gateway_runtime_entry["evidence_paths"]
    assert "app/backend/tests/test_model_gateway_runtime_configuration.py" in gateway_runtime_entry["evidence_paths"]
    assert "app/backend/services/model_runtime_router.py" in gateway_runtime_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in gateway_runtime_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in gateway_runtime_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gateway_runtime_entry["evidence_paths"]
    assert "docs/MODEL_GATEWAY_RUNTIME_CONFIGURATION.md" in gateway_runtime_entry["evidence_paths"]
    assert "model-gateway-runtime-configuration" in gateway_runtime_entry["release_gate_links"]
    assert "model-gateway-connection-profile" in gateway_runtime_entry["release_gate_links"]
    assert "model-gateway-health-plan" in gateway_runtime_entry["release_gate_links"]
    assert "model-runtime-router" in gateway_runtime_entry["release_gate_links"]
    assert "model-ops-readiness" in gateway_runtime_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_gateway_runtime_configuration.py "
        "tests/test_model_gateway_connection_profile.py tests/test_model_gateway_health_plan.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py "
        "tests/test_frontend_ui_regression_gate.py -q"
        in ledger["validation_commands"]
    )
    observed_gateway_fit_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-observed-gateway-model-fit-matrix"
    )
    assert observed_gateway_fit_entry["size"] == "medium"
    assert observed_gateway_fit_entry["status"] == "shipped"
    assert "observed gateway model fit evidence" in observed_gateway_fit_entry["impact"]
    assert "sanitized /models inventory ids" in observed_gateway_fit_entry["impact"]
    assert "cheap-first task capabilities" in observed_gateway_fit_entry["impact"]
    assert "lowest-cost observed candidates" in observed_gateway_fit_entry["impact"]
    assert "missing task coverage" in observed_gateway_fit_entry["impact"]
    assert "review-only Pro/preview/image/unknown/external/unpriced boundaries" in observed_gateway_fit_entry["impact"]
    assert "live gateway calls" in observed_gateway_fit_entry["impact"]
    assert "account inventory validation" in observed_gateway_fit_entry["impact"]
    assert "configuration writes" in observed_gateway_fit_entry["impact"]
    assert "default changes" in observed_gateway_fit_entry["impact"]
    assert "traffic shifts" in observed_gateway_fit_entry["impact"]
    assert "Authorization headers" in observed_gateway_fit_entry["impact"]
    assert "request bodies" in observed_gateway_fit_entry["impact"]
    assert "response bodies" in observed_gateway_fit_entry["impact"]
    assert "prompts" in observed_gateway_fit_entry["impact"]
    assert "raw payloads" in observed_gateway_fit_entry["impact"]
    assert "model outputs" in observed_gateway_fit_entry["impact"]
    assert "gateway responses" in observed_gateway_fit_entry["impact"]
    assert "credentials" in observed_gateway_fit_entry["impact"]
    assert "app/backend/services/modelops_observed_gateway_model_fit_matrix.py" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_observed_gateway_model_fit_matrix.py" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/backend/services/model_default_candidate_selector.py" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in observed_gateway_fit_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in observed_gateway_fit_entry["evidence_paths"]
    assert "docs/MODELOPS_OBSERVED_GATEWAY_MODEL_FIT_MATRIX.md" in observed_gateway_fit_entry["evidence_paths"]
    assert "modelops-observed-gateway-model-fit-matrix" in observed_gateway_fit_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in observed_gateway_fit_entry["release_gate_links"]
    assert "model-gateway-connection-profile" in observed_gateway_fit_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in observed_gateway_fit_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_modelops_observed_gateway_model_fit_matrix.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    runtime_explicit_fit_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-runtime-explicit-model-fit-gate"
    )
    assert runtime_explicit_fit_entry["size"] == "medium"
    assert runtime_explicit_fit_entry["status"] == "shipped"
    assert "runtime explicit model fit evidence" in runtime_explicit_fit_entry["impact"]
    assert "sanitized task/model scenarios" in runtime_explicit_fit_entry["impact"]
    assert "runtime router" in runtime_explicit_fit_entry["impact"]
    assert "unknown gateway guards" in runtime_explicit_fit_entry["impact"]
    assert "reviewed gateway pass-through exceptions" in runtime_explicit_fit_entry["impact"]
    assert "explicit over-budget exceptions" in runtime_explicit_fit_entry["impact"]
    assert "local downgrade enforcement" in runtime_explicit_fit_entry["impact"]
    assert "cheap-first alignment" in runtime_explicit_fit_entry["impact"]
    assert "observed gateway fit review states" in runtime_explicit_fit_entry["impact"]
    assert "live gateway calls" in runtime_explicit_fit_entry["impact"]
    assert "model calls" in runtime_explicit_fit_entry["impact"]
    assert "account inventory validation" in runtime_explicit_fit_entry["impact"]
    assert "configuration writes" in runtime_explicit_fit_entry["impact"]
    assert "default changes" in runtime_explicit_fit_entry["impact"]
    assert "traffic shifts" in runtime_explicit_fit_entry["impact"]
    assert "API keys" in runtime_explicit_fit_entry["impact"]
    assert "Authorization headers" in runtime_explicit_fit_entry["impact"]
    assert "request bodies" in runtime_explicit_fit_entry["impact"]
    assert "messages" in runtime_explicit_fit_entry["impact"]
    assert "prompts" in runtime_explicit_fit_entry["impact"]
    assert "raw payloads" in runtime_explicit_fit_entry["impact"]
    assert "model outputs" in runtime_explicit_fit_entry["impact"]
    assert "gateway responses" in runtime_explicit_fit_entry["impact"]
    assert "credentials" in runtime_explicit_fit_entry["impact"]
    assert "app/backend/services/model_ops_runtime_explicit_model_fit_gate.py" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_runtime_explicit_model_fit_gate.py" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/backend/services/model_runtime_router.py" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/backend/services/model_budget.py" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in runtime_explicit_fit_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in runtime_explicit_fit_entry["evidence_paths"]
    assert "docs/MODELOPS_RUNTIME_EXPLICIT_MODEL_FIT_GATE.md" in runtime_explicit_fit_entry["evidence_paths"]
    assert "modelops-runtime-explicit-model-fit-gate" in runtime_explicit_fit_entry["release_gate_links"]
    assert "modelops-observed-gateway-model-fit-matrix" in runtime_explicit_fit_entry["release_gate_links"]
    assert "modelops-aihub-endpoint-route-coverage-gate" in runtime_explicit_fit_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in runtime_explicit_fit_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_model_ops_runtime_explicit_model_fit_gate.py "
        "tests/test_model_runtime_router.py tests/test_aihub_runtime_routing.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )

    explicit_guard_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "model-runtime-explicit-unknown-lifecycle-guard"
    )
    assert explicit_guard_entry["category"] == "model_ops"
    assert explicit_guard_entry["size"] == "medium"
    assert explicit_guard_entry["status"] == "shipped"
    assert "explicit unknown gateway models" in explicit_guard_entry["impact"]
    assert "non-stable preview/review lifecycle catalog models" in explicit_guard_entry["impact"]
    assert "stable task recommendations by default" in explicit_guard_entry["impact"]
    assert "allow_over_budget_model=True" in explicit_guard_entry["impact"]
    assert "reason codes" in explicit_guard_entry["impact"]
    assert "route telemetry visibility" in explicit_guard_entry["impact"]
    assert "live gateway calls" in explicit_guard_entry["impact"]
    assert "default changes" in explicit_guard_entry["impact"]
    assert "prompts" in explicit_guard_entry["impact"]
    assert "raw legal text" in explicit_guard_entry["impact"]
    assert "API keys" in explicit_guard_entry["impact"]
    assert "credentials" in explicit_guard_entry["impact"]
    assert "app/backend/services/model_runtime_router.py" in explicit_guard_entry["evidence_paths"]
    assert "app/backend/services/model_route_telemetry.py" in explicit_guard_entry["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in explicit_guard_entry["evidence_paths"]
    assert "app/backend/tests/test_model_runtime_router.py" in explicit_guard_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in explicit_guard_entry["evidence_paths"]
    assert "modelops-runtime-explicit-model-fit-gate" in explicit_guard_entry["release_gate_links"]
    assert "route-telemetry-repository" in explicit_guard_entry["release_gate_links"]
    legal_micro_preflight_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-micro-benchmark-preflight"
    )
    assert legal_micro_preflight_entry["size"] == "medium"
    assert legal_micro_preflight_entry["status"] == "shipped"
    assert "low-resource legal benchmark preflight evidence" in legal_micro_preflight_entry["impact"]
    assert "cheap-first Gemini fixture ids" in legal_micro_preflight_entry["impact"]
    assert "document case ids" in legal_micro_preflight_entry["impact"]
    assert "fact-consistency case ids" in legal_micro_preflight_entry["impact"]
    assert "serial run order" in legal_micro_preflight_entry["impact"]
    assert "cost estimates" in legal_micro_preflight_entry["impact"]
    assert "follow-up gate bindings" in legal_micro_preflight_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network/app-AI calls" in legal_micro_preflight_entry["impact"]
    assert "configuration writes" in legal_micro_preflight_entry["impact"]
    assert "traffic shifts" in legal_micro_preflight_entry["impact"]
    assert "request bodies" in legal_micro_preflight_entry["impact"]
    assert "messages" in legal_micro_preflight_entry["impact"]
    assert "prompt text" in legal_micro_preflight_entry["impact"]
    assert "fixture excerpts" in legal_micro_preflight_entry["impact"]
    assert "legal text" in legal_micro_preflight_entry["impact"]
    assert "generated document text" in legal_micro_preflight_entry["impact"]
    assert "model outputs" in legal_micro_preflight_entry["impact"]
    assert "gateway responses" in legal_micro_preflight_entry["impact"]
    assert "credentials" in legal_micro_preflight_entry["impact"]
    assert "emails" in legal_micro_preflight_entry["impact"]
    assert "app/backend/services/modelops_legal_micro_benchmark_preflight.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_micro_benchmark_preflight.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/services/legal_fixture_local_run_package.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in legal_micro_preflight_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in legal_micro_preflight_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_MICRO_BENCHMARK_PREFLIGHT.md" in legal_micro_preflight_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in legal_micro_preflight_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in legal_micro_preflight_entry["evidence_paths"]
    assert "modelops-legal-micro-benchmark-preflight" in legal_micro_preflight_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in legal_micro_preflight_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in legal_micro_preflight_entry["release_gate_links"]
    assert "legal-document-fact-consistency-benchmark" in legal_micro_preflight_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in legal_micro_preflight_entry["release_gate_links"]
    legal_fixture_gate_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-cheap-first-benchmark-gate"
    )
    assert legal_fixture_gate_entry["size"] == "medium"
    assert legal_fixture_gate_entry["status"] == "shipped"
    assert "small legal-document cheap-first Gemini benchmark/risk gate evidence" in legal_fixture_gate_entry["impact"]
    assert "AIHub ModelOps payload/UI" in legal_fixture_gate_entry["impact"]
    assert "redacted fixture ids" in legal_fixture_gate_entry["impact"]
    assert "document case ids" in legal_fixture_gate_entry["impact"]
    assert "fact-consistency case ids" in legal_fixture_gate_entry["impact"]
    assert "linked cheap-first calibration task ids" in legal_fixture_gate_entry["impact"]
    assert "calibration decisions" in legal_fixture_gate_entry["impact"]
    assert "release gates" in legal_fixture_gate_entry["impact"]
    assert "expected issue counts" in legal_fixture_gate_entry["impact"]
    assert "amount/date/fact consistency counts" in legal_fixture_gate_entry["impact"]
    assert "cost metadata" in legal_fixture_gate_entry["impact"]
    assert "document benchmark pass/fail counts" in legal_fixture_gate_entry["impact"]
    assert "coverage-gap counts" in legal_fixture_gate_entry["impact"]
    assert "escalation metadata" in legal_fixture_gate_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in legal_fixture_gate_entry["impact"]
    assert "real legal text" in legal_fixture_gate_entry["impact"]
    assert "fixture snippets" in legal_fixture_gate_entry["impact"]
    assert "generated document text" in legal_fixture_gate_entry["impact"]
    assert "prompts" in legal_fixture_gate_entry["impact"]
    assert "calibration payloads" in legal_fixture_gate_entry["impact"]
    assert "model outputs" in legal_fixture_gate_entry["impact"]
    assert "credentials" in legal_fixture_gate_entry["impact"]
    assert "emails" in legal_fixture_gate_entry["impact"]
    assert "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_cheap_first_calibration.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_selector_replay.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in legal_fixture_gate_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in legal_fixture_gate_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in legal_fixture_gate_entry["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in legal_fixture_gate_entry["evidence_paths"]
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
    assert "legal-document-fact-consistency-benchmark" in legal_fixture_gate_entry["release_gate_links"]
    fact_consistency_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-document-fact-consistency-benchmark"
    )
    assert fact_consistency_entry["size"] == "medium"
    assert fact_consistency_entry["status"] == "shipped"
    assert "legal-document fact consistency benchmark evidence" in fact_consistency_entry["impact"]
    assert "structured amount checks" in fact_consistency_entry["impact"]
    assert "deadline checks" in fact_consistency_entry["impact"]
    assert "required fact IDs" in fact_consistency_entry["impact"]
    assert "contradiction pairs" in fact_consistency_entry["impact"]
    assert "raw-input rejection" in fact_consistency_entry["impact"]
    assert "cheap-first default-change gating" in fact_consistency_entry["impact"]
    assert "without model calls" in fact_consistency_entry["impact"]
    assert "network calls" in fact_consistency_entry["impact"]
    assert "public dataset downloads" in fact_consistency_entry["impact"]
    assert "raw legal text" in fact_consistency_entry["impact"]
    assert "generated document text" in fact_consistency_entry["impact"]
    assert "credentials" in fact_consistency_entry["impact"]
    assert "client identifiers" in fact_consistency_entry["impact"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in fact_consistency_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in fact_consistency_entry["evidence_paths"]
    assert "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py" in fact_consistency_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in fact_consistency_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in fact_consistency_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in fact_consistency_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in fact_consistency_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in fact_consistency_entry["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in fact_consistency_entry["evidence_paths"]
    assert "legal-document-fact-consistency-benchmark" in fact_consistency_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in fact_consistency_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage" in fact_consistency_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in fact_consistency_entry["release_gate_links"]
    legal_fixture_promotion_packet_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-cheap-first-default-promotion-packet"
    )
    assert legal_fixture_promotion_packet_entry["size"] == "medium"
    assert legal_fixture_promotion_packet_entry["status"] == "shipped"
    assert "maintainer review packet evidence" in legal_fixture_promotion_packet_entry["impact"]
    assert "AIHub ModelOps payload/UI" in legal_fixture_promotion_packet_entry["impact"]
    assert "cheap-first legal fixture default promotion" in legal_fixture_promotion_packet_entry["impact"]
    assert "fixture ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "document case ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "fact-consistency case ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "linked cheap-first calibration task ids" in legal_fixture_promotion_packet_entry["impact"]
    assert "calibration decisions" in legal_fixture_promotion_packet_entry["impact"]
    assert "release gates" in legal_fixture_promotion_packet_entry["impact"]
    assert "document benchmark pass/fail counts" in legal_fixture_promotion_packet_entry["impact"]
    assert "amount/date/fact consistency counts" in legal_fixture_promotion_packet_entry["impact"]
    assert "coverage-gap counts" in legal_fixture_promotion_packet_entry["impact"]
    assert "cost-tier metadata" in legal_fixture_promotion_packet_entry["impact"]
    assert "required signoff roles" in legal_fixture_promotion_packet_entry["impact"]
    assert "without configuration writes" in legal_fixture_promotion_packet_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google/gateway/network calls" in legal_fixture_promotion_packet_entry["impact"]
    assert "traffic shifts" in legal_fixture_promotion_packet_entry["impact"]
    assert "real legal text" in legal_fixture_promotion_packet_entry["impact"]
    assert "generated document text" in legal_fixture_promotion_packet_entry["impact"]
    assert "calibration payloads" in legal_fixture_promotion_packet_entry["impact"]
    assert "model outputs" in legal_fixture_promotion_packet_entry["impact"]
    assert "credentials" in legal_fixture_promotion_packet_entry["impact"]
    assert "emails" in legal_fixture_promotion_packet_entry["impact"]
    assert "app/backend/services/modelops_legal_fixture_default_promotion_packet.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_default_promotion_packet.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_cheap_first_calibration.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in legal_fixture_promotion_packet_entry["evidence_paths"]
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "legal-document-benchmark-coverage" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "legal-document-fact-consistency-benchmark" in legal_fixture_promotion_packet_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in legal_fixture_promotion_packet_entry["release_gate_links"]
    calibration_binding_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-cheap-first-calibration-binding"
    )
    assert calibration_binding_entry["size"] == "medium"
    assert calibration_binding_entry["status"] == "shipped"
    assert "cheap-first calibration rows" in calibration_binding_entry["impact"]
    assert "ModelOps UI" in calibration_binding_entry["impact"]
    assert "calibration decisions" in calibration_binding_entry["impact"]
    assert "release gates" in calibration_binding_entry["impact"]
    assert "default promotion packet" in calibration_binding_entry["impact"]
    assert "limited-concurrency evidence loading" in calibration_binding_entry["impact"]
    assert "legacy maintenance evidence URL" in calibration_binding_entry["impact"]
    assert "calibration payloads" in calibration_binding_entry["impact"]
    assert "prompts" in calibration_binding_entry["impact"]
    assert "model outputs" in calibration_binding_entry["impact"]
    assert "credentials" in calibration_binding_entry["impact"]
    assert "emails" in calibration_binding_entry["impact"]
    assert (
        "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py"
        in calibration_binding_entry["evidence_paths"]
    )
    assert (
        "app/backend/services/modelops_legal_fixture_default_promotion_packet.py"
        in calibration_binding_entry["evidence_paths"]
    )
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in calibration_binding_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in calibration_binding_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/vite.config.ts" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in calibration_binding_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in calibration_binding_entry["evidence_paths"]
    assert (
        "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md"
        in calibration_binding_entry["evidence_paths"]
    )
    assert (
        "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md"
        in calibration_binding_entry["evidence_paths"]
    )
    assert "docs/AI_MODEL_STRATEGY.md" in calibration_binding_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in calibration_binding_entry["evidence_paths"]
    assert (
        "modelops-legal-fixture-cheap-first-calibration-binding"
        in calibration_binding_entry["release_gate_links"]
    )
    assert "gemini-newapi-cheap-first-calibration" in calibration_binding_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in calibration_binding_entry["release_gate_links"]
    modelops_ui_binding_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-legal-fixture-modelops-ui-binding"
    )
    assert modelops_ui_binding_entry["size"] == "medium"
    assert modelops_ui_binding_entry["status"] == "shipped"
    assert "AIHub ModelOps payload" in modelops_ui_binding_entry["impact"]
    assert "direct ModelOps endpoints" in modelops_ui_binding_entry["impact"]
    assert "ModelOps main-page panels" in modelops_ui_binding_entry["impact"]
    assert "linked calibration task ids" in modelops_ui_binding_entry["impact"]
    assert "default-change safety boundaries" in modelops_ui_binding_entry["impact"]
    assert "configuration writes" in modelops_ui_binding_entry["impact"]
    assert "traffic shifts" in modelops_ui_binding_entry["impact"]
    assert "calibration payloads" in modelops_ui_binding_entry["impact"]
    assert "credentials" in modelops_ui_binding_entry["impact"]
    assert "emails" in modelops_ui_binding_entry["impact"]
    assert "app/backend/routers/aihub.py" in modelops_ui_binding_entry["evidence_paths"]
    assert (
        "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py"
        in modelops_ui_binding_entry["evidence_paths"]
    )
    assert (
        "app/backend/services/modelops_legal_fixture_default_promotion_packet.py"
        in modelops_ui_binding_entry["evidence_paths"]
    )
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_default_promotion_packet.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in modelops_ui_binding_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in modelops_ui_binding_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in modelops_ui_binding_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in modelops_ui_binding_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in modelops_ui_binding_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in modelops_ui_binding_entry["evidence_paths"]
    assert "modelops-legal-fixture-modelops-ui-binding" in modelops_ui_binding_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in modelops_ui_binding_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in modelops_ui_binding_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in modelops_ui_binding_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in modelops_ui_binding_entry["release_gate_links"]
    release_legal_binding_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-cheap-first-release-legal-benchmark-binding"
    )
    assert release_legal_binding_entry["size"] == "medium"
    assert release_legal_binding_entry["status"] == "shipped"
    assert "legal fixture cheap-first benchmark gate" in release_legal_binding_entry["impact"]
    assert "legal fixture default promotion packet" in release_legal_binding_entry["impact"]
    assert "legal benchmark risk bridge" in release_legal_binding_entry["impact"]
    assert "cheap-first release decision" in release_legal_binding_entry["impact"]
    assert "failed fixture/document/fact-consistency/calibration/route evidence" in release_legal_binding_entry["impact"]
    assert "not-run, not-ready" in release_legal_binding_entry["impact"]
    assert "public benchmark license" in release_legal_binding_entry["impact"]
    assert "premium exception" in release_legal_binding_entry["impact"]
    assert "configuration writes" in release_legal_binding_entry["impact"]
    assert "public dataset downloads" in release_legal_binding_entry["impact"]
    assert "raw legal text" in release_legal_binding_entry["impact"]
    assert "credentials" in release_legal_binding_entry["impact"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in release_legal_binding_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_cheap_first_release_decision.py" in release_legal_binding_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in release_legal_binding_entry["evidence_paths"]
    assert (
        "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py"
        in release_legal_binding_entry["evidence_paths"]
    )
    assert (
        "app/backend/services/modelops_legal_fixture_default_promotion_packet.py"
        in release_legal_binding_entry["evidence_paths"]
    )
    assert "app/backend/services/model_ops_legal_benchmark_risk_bridge.py" in release_legal_binding_entry["evidence_paths"]
    assert "app/backend/services/model_ops_default_change_queue.py" in release_legal_binding_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in release_legal_binding_entry["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_RELEASE_DECISION.md" in release_legal_binding_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in release_legal_binding_entry["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in release_legal_binding_entry["evidence_paths"]
    assert "docs/MODEL_OPS_LEGAL_BENCHMARK_RISK_BRIDGE.md" in release_legal_binding_entry["evidence_paths"]
    assert "modelops-cheap-first-release-legal-benchmark-binding" in release_legal_binding_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in release_legal_binding_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in release_legal_binding_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in release_legal_binding_entry["release_gate_links"]
    assert "modelops-legal-benchmark-risk-bridge" in release_legal_binding_entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in release_legal_binding_entry["release_gate_links"]
    release_maintenance_panel_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-cheap-first-release-maintenance-evidence-panel"
    )
    assert release_maintenance_panel_entry["category"] == "frontend_ui"
    assert release_maintenance_panel_entry["size"] == "medium"
    assert release_maintenance_panel_entry["status"] == "shipped"
    assert "maintenance evidence page" in release_maintenance_panel_entry["impact"]
    assert "required signal counts" in release_maintenance_panel_entry["impact"]
    assert "legal source checks" in release_maintenance_panel_entry["impact"]
    assert "default-promotion blockers" in release_maintenance_panel_entry["impact"]
    assert "legal fixture policy" in release_maintenance_panel_entry["impact"]
    assert "legal benchmark policy" in release_maintenance_panel_entry["impact"]
    assert "privacy/claim boundaries" in release_maintenance_panel_entry["impact"]
    assert "without switching pages" in release_maintenance_panel_entry["impact"]
    assert "configuration" in release_maintenance_panel_entry["impact"]
    assert "traffic" in release_maintenance_panel_entry["impact"]
    assert "raw legal text" in release_maintenance_panel_entry["impact"]
    assert "credentials" in release_maintenance_panel_entry["impact"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in release_maintenance_panel_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in release_maintenance_panel_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in release_maintenance_panel_entry["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in release_maintenance_panel_entry["evidence_paths"]
    assert (
        "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py"
        in release_maintenance_panel_entry["evidence_paths"]
    )
    assert (
        "app/backend/services/modelops_legal_fixture_default_promotion_packet.py"
        in release_maintenance_panel_entry["evidence_paths"]
    )
    assert "app/backend/services/model_ops_legal_benchmark_risk_bridge.py" in release_maintenance_panel_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in release_maintenance_panel_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in release_maintenance_panel_entry["evidence_paths"]
    assert "modelops-cheap-first-release-maintenance-evidence-panel" in release_maintenance_panel_entry["release_gate_links"]
    assert "modelops-cheap-first-release-legal-benchmark-binding" in release_maintenance_panel_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in release_maintenance_panel_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-benchmark-gate" in release_maintenance_panel_entry["release_gate_links"]
    assert "modelops-legal-fixture-cheap-first-default-promotion-packet" in release_maintenance_panel_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in release_maintenance_panel_entry["release_gate_links"]
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
    assert "promotion safety checks" in intake_queue_entry["impact"]
    assert "cheap-first candidate summaries" in intake_queue_entry["impact"]
    assert "maintainer runbook steps" in intake_queue_entry["impact"]
    assert "before they enter default candidates" in intake_queue_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in intake_queue_entry["impact"]
    assert "real environment writes" in intake_queue_entry["impact"]
    assert "configuration writes" in intake_queue_entry["impact"]
    assert "traffic shifts" in intake_queue_entry["impact"]
    assert "raw prompts" in intake_queue_entry["impact"]
    assert "payloads" in intake_queue_entry["impact"]
    assert "model outputs" in intake_queue_entry["impact"]
    assert "legal text" in intake_queue_entry["impact"]
    assert "emails" in intake_queue_entry["impact"]
    assert "credentials" in intake_queue_entry["impact"]
    assert "shared observed-model extraction" in intake_queue_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/services/model_ops_observed_gemini_model_intake_queue.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_observed_gemini_model_intake_queue.py" in intake_queue_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/release_readiness.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in intake_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in intake_queue_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in intake_queue_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in intake_queue_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in intake_queue_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in intake_queue_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in intake_queue_entry["evidence_paths"]
    assert "modelops-observed-gemini-model-intake-queue" in intake_queue_entry["release_gate_links"]
    assert "gemini-newapi-selector-replay" in intake_queue_entry["release_gate_links"]
    assert "model-catalog-candidate-impact-replay" in intake_queue_entry["release_gate_links"]
    assert "modelops-default-change-queue" in intake_queue_entry["release_gate_links"]
    assert "modelops-cheap-first-maintainer-execution-checklist" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-default-change-review" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-default-cost-impact" in intake_queue_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in intake_queue_entry["release_gate_links"]
    assert "model-catalog-source-audit" in intake_queue_entry["release_gate_links"]
    assert "model-gateway-compatibility" in intake_queue_entry["release_gate_links"]
    assert "model-lifecycle-policy" in intake_queue_entry["release_gate_links"]
    coverage_gap_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-observed-gemini-coverage-gap-queue"
    )
    assert coverage_gap_entry["size"] == "medium"
    assert coverage_gap_entry["status"] == "shipped"
    assert "metadata-only observed Gemini coverage gap queue evidence" in coverage_gap_entry["impact"]
    assert "observed model intake queue" in coverage_gap_entry["impact"]
    assert "Gemini variant matrix" in coverage_gap_entry["impact"]
    assert "family coverage gaps" in coverage_gap_entry["impact"]
    assert "high-frequency cheap-first task gaps" in coverage_gap_entry["impact"]
    assert "unknown/unpriced/preview/media risk" in coverage_gap_entry["impact"]
    assert "default-promotion review actions" in coverage_gap_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in coverage_gap_entry["impact"]
    assert "configuration writes" in coverage_gap_entry["impact"]
    assert "raw prompts" in coverage_gap_entry["impact"]
    assert "payloads" in coverage_gap_entry["impact"]
    assert "model outputs" in coverage_gap_entry["impact"]
    assert "credentials" in coverage_gap_entry["impact"]
    assert "app/backend/services/model_ops_observed_gemini_coverage_gap_queue.py" in coverage_gap_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_observed_gemini_model_intake_queue.py" in coverage_gap_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/gemini_model_variant_matrix.py" in coverage_gap_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_observed_gemini_coverage_gap_queue.py" in coverage_gap_entry[
        "evidence_paths"
    ]
    assert "app/frontend/src/lib/modelOpsApi.ts" in coverage_gap_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in coverage_gap_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in coverage_gap_entry["evidence_paths"]
    assert "docs/MODELOPS_OBSERVED_GEMINI_COVERAGE_GAP_QUEUE.md" in coverage_gap_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in coverage_gap_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in coverage_gap_entry["evidence_paths"]
    assert "modelops-observed-gemini-coverage-gap-queue" in coverage_gap_entry["release_gate_links"]
    assert "modelops-observed-gemini-model-intake-queue" in coverage_gap_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in coverage_gap_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in coverage_gap_entry["release_gate_links"]
    assert "gemini-newapi-alias-capability-coverage" in coverage_gap_entry["release_gate_links"]
    assert "model-ops-readiness" in coverage_gap_entry["release_gate_links"]
    assert "frontend-ui-regression" in coverage_gap_entry["release_gate_links"]

    gemini_official_roadmap_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "modelops-gemini-official-model-family-roadmap-evidence"
    )
    assert gemini_official_roadmap_entry["category"] == "model_ops"
    assert gemini_official_roadmap_entry["size"] == "medium"
    assert gemini_official_roadmap_entry["status"] == "shipped"
    assert "metadata-only official Gemini family roadmap evidence" in gemini_official_roadmap_entry["impact"]
    assert "cheap-first Flash-Lite defaults" in gemini_official_roadmap_entry["impact"]
    assert "review-only Gemini 3/image rows" in gemini_official_roadmap_entry["impact"]
    assert "live/audio/embedding/TTS gap queues" in gemini_official_roadmap_entry["impact"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in gemini_official_roadmap_entry["impact"]
    assert "configuration writes" in gemini_official_roadmap_entry["impact"]
    assert "default changes" in gemini_official_roadmap_entry["impact"]
    assert "request bodies" in gemini_official_roadmap_entry["impact"]
    assert "response bodies" in gemini_official_roadmap_entry["impact"]
    assert "headers" in gemini_official_roadmap_entry["impact"]
    assert "model outputs" in gemini_official_roadmap_entry["impact"]
    assert "credentials" in gemini_official_roadmap_entry["impact"]
    assert "app/backend/services/model_ops_gemini_official_model_family_roadmap.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_gemini_official_model_family_roadmap.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gemini_official_roadmap_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in gemini_official_roadmap_entry["evidence_paths"]
    assert "docs/MODELOPS_GEMINI_OFFICIAL_MODEL_FAMILY_ROADMAP.md" in gemini_official_roadmap_entry["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in gemini_official_roadmap_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in gemini_official_roadmap_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in gemini_official_roadmap_entry["evidence_paths"]
    assert "modelops-gemini-official-model-family-roadmap-evidence" in gemini_official_roadmap_entry["release_gate_links"]
    assert "model-catalog-source-audit" in gemini_official_roadmap_entry["release_gate_links"]
    assert "gemini-model-variant-matrix" in gemini_official_roadmap_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in gemini_official_roadmap_entry["release_gate_links"]
    assert "modelops-observed-gemini-coverage-gap-queue" in gemini_official_roadmap_entry["release_gate_links"]
    assert "model-ops-readiness" in gemini_official_roadmap_entry["release_gate_links"]
    assert "frontend-ui-regression" in gemini_official_roadmap_entry["release_gate_links"]

    route_telemetry_catalog_cost_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "route-telemetry-catalog-cost-estimation"
    )
    assert route_telemetry_catalog_cost_entry["category"] == "model_ops"
    assert route_telemetry_catalog_cost_entry["size"] == "medium"
    assert route_telemetry_catalog_cost_entry["status"] == "shipped"
    assert "local Gemini catalog token pricing" in route_telemetry_catalog_cost_entry["impact"]
    assert "known NewAPI/Gemini routes" in route_telemetry_catalog_cost_entry["impact"]
    assert "unknown gateway models unpriced" in route_telemetry_catalog_cost_entry["impact"]
    assert "daily cheap-first cost aggregates" in route_telemetry_catalog_cost_entry["impact"]
    assert "raw model output" in route_telemetry_catalog_cost_entry["impact"]
    assert "payloads" in route_telemetry_catalog_cost_entry["impact"]
    assert "credentials" in route_telemetry_catalog_cost_entry["impact"]
    assert "app/backend/services/route_telemetry_repository.py" in route_telemetry_catalog_cost_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_catalog.py" in route_telemetry_catalog_cost_entry["evidence_paths"]
    assert "app/backend/services/model_usage.py" in route_telemetry_catalog_cost_entry["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_repository.py" in route_telemetry_catalog_cost_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in route_telemetry_catalog_cost_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_usage.py" in route_telemetry_catalog_cost_entry["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md" in route_telemetry_catalog_cost_entry[
        "evidence_paths"
    ]
    assert "docs/ROUTE_TELEMETRY_OPS_SUMMARY.md" in route_telemetry_catalog_cost_entry["evidence_paths"]
    assert "route-telemetry-repository" in route_telemetry_catalog_cost_entry["release_gate_links"]
    assert "route-telemetry-ops-summary" in route_telemetry_catalog_cost_entry["release_gate_links"]
    assert "model-usage" in route_telemetry_catalog_cost_entry["release_gate_links"]

    route_reason_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "runtime-route-reason-codes"
    )
    assert route_reason_entry["category"] == "model_ops"
    assert route_reason_entry["size"] == "medium"
    assert route_reason_entry["status"] == "shipped"
    assert "structured cheap-first runtime route reason codes" in route_reason_entry["impact"]
    assert "sanitized reason-code counts" in route_reason_entry["impact"]
    assert "unknown catalog models" in route_reason_entry["impact"]
    assert "operator-review gates" in route_reason_entry["impact"]
    assert "prompts" in route_reason_entry["impact"]
    assert "raw legal text" in route_reason_entry["impact"]
    assert "model output" in route_reason_entry["impact"]
    assert "credentials" in route_reason_entry["impact"]
    assert "app/backend/services/model_runtime_router.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/services/route_telemetry_persistence_plan.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/tests/test_model_runtime_router.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_repository.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_persistence_plan.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in route_reason_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in route_reason_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in route_reason_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in route_reason_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in route_reason_entry["evidence_paths"]
    assert "docs/MODEL_RUNTIME_ROUTER.md" in route_reason_entry["evidence_paths"]
    assert "docs/MODEL_ROUTE_TELEMETRY.md" in route_reason_entry["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md" in route_reason_entry["evidence_paths"]
    assert "docs/RELEASE_READINESS.md" in route_reason_entry["evidence_paths"]
    assert "runtime-route-reason-codes" in route_reason_entry["release_gate_links"]
    assert "model-runtime-router" in route_reason_entry["release_gate_links"]
    assert "route-telemetry-repository" in route_reason_entry["release_gate_links"]
    assert "route-telemetry-persistence-plan" in route_reason_entry["release_gate_links"]
    assert "model-ops-readiness" in route_reason_entry["release_gate_links"]
    assert "frontend-typecheck" in route_reason_entry["release_gate_links"]
    assert "frontend-ui-regression" in route_reason_entry["release_gate_links"]

    reason_hotspot_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "route-telemetry-reason-code-hotspots"
    )
    assert reason_hotspot_entry["category"] == "model_ops"
    assert reason_hotspot_entry["size"] == "medium"
    assert reason_hotspot_entry["status"] == "shipped"
    assert "sanitized route reason_code_counts" in reason_hotspot_entry["impact"]
    assert "cheap-first/Gemini route hotspots" in reason_hotspot_entry["impact"]
    assert "over_task_budget" in reason_hotspot_entry["impact"]
    assert "operator_review_required" in reason_hotspot_entry["impact"]
    assert "unknown_catalog_model" in reason_hotspot_entry["impact"]
    assert "unknown_gateway_routed_to_recommended" in reason_hotspot_entry["impact"]
    assert "non_stable_model_routed_to_recommended" in reason_hotspot_entry["impact"]
    assert "allow-gated gateway_passthrough" in reason_hotspot_entry["impact"]
    assert "unknown_reason_code" in reason_hotspot_entry["impact"]
    assert "prompts" in reason_hotspot_entry["impact"]
    assert "raw legal text" in reason_hotspot_entry["impact"]
    assert "payloads" in reason_hotspot_entry["impact"]
    assert "credentials" in reason_hotspot_entry["impact"]
    assert "model output" in reason_hotspot_entry["impact"]
    assert "app/backend/services/route_telemetry_ops_summary.py" in reason_hotspot_entry["evidence_paths"]
    assert "app/backend/services/route_telemetry_triage_queue.py" in reason_hotspot_entry["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in reason_hotspot_entry["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_ops_summary.py" in reason_hotspot_entry["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_triage_queue.py" in reason_hotspot_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in reason_hotspot_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in reason_hotspot_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in reason_hotspot_entry["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_OPS_SUMMARY.md" in reason_hotspot_entry["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md" in reason_hotspot_entry["evidence_paths"]
    assert "docs/MODEL_ROUTE_TELEMETRY.md" in reason_hotspot_entry["evidence_paths"]
    assert "docs/RELEASE_READINESS.md" in reason_hotspot_entry["evidence_paths"]
    assert "route-telemetry-ops-summary" in reason_hotspot_entry["release_gate_links"]
    assert "route-telemetry-triage-queue" in reason_hotspot_entry["release_gate_links"]
    assert "route-telemetry-repository" in reason_hotspot_entry["release_gate_links"]
    assert "runtime-route-reason-codes" in reason_hotspot_entry["release_gate_links"]
    assert "frontend-ui-regression" in reason_hotspot_entry["release_gate_links"]

    route_telemetry_ui_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "route-telemetry-ui-regression-contract"
    )
    assert route_telemetry_ui_entry["size"] == "medium"
    assert route_telemetry_ui_entry["status"] == "shipped"
    assert "route telemetry repository" in route_telemetry_ui_entry["impact"]
    assert "ops summary" in route_telemetry_ui_entry["impact"]
    assert "triage queue" in route_telemetry_ui_entry["impact"]
    assert "remediation panels" in route_telemetry_ui_entry["impact"]
    assert "cheap-first routing warnings" in route_telemetry_ui_entry["impact"]
    assert "sanitized route counters" in route_telemetry_ui_entry["impact"]
    assert "no-config-write boundaries" in route_telemetry_ui_entry["impact"]
    assert "no-NewAPI-call boundaries" in route_telemetry_ui_entry["impact"]
    assert "prompts" in route_telemetry_ui_entry["impact"]
    assert "request bodies" in route_telemetry_ui_entry["impact"]
    assert "response bodies" in route_telemetry_ui_entry["impact"]
    assert "headers" in route_telemetry_ui_entry["impact"]
    assert "raw model output" in route_telemetry_ui_entry["impact"]
    assert "credentials" in route_telemetry_ui_entry["impact"]
    assert "app/frontend/scripts/ui-regression.mjs" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/backend/services/frontend_ui_regression_gate.py" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/backend/tests/test_frontend_ui_regression_gate.py" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in route_telemetry_ui_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in route_telemetry_ui_entry["evidence_paths"]
    assert "docs/FRONTEND_UI_REGRESSION_GATE.md" in route_telemetry_ui_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in route_telemetry_ui_entry["evidence_paths"]
    assert "frontend-ui-regression-gate" in route_telemetry_ui_entry["release_gate_links"]
    assert "frontend-ui-regression" in route_telemetry_ui_entry["release_gate_links"]
    assert "route-telemetry-repository" in route_telemetry_ui_entry["release_gate_links"]
    assert "route-telemetry-ops-summary" in route_telemetry_ui_entry["release_gate_links"]
    assert "route-telemetry-triage-queue" in route_telemetry_ui_entry["release_gate_links"]
    assert "route-telemetry-remediation-plan" in route_telemetry_ui_entry["release_gate_links"]
    assert "model-ops-readiness" in route_telemetry_ui_entry["release_gate_links"]

    readiness_drilldown_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-ops-readiness-warning-drilldown"
    )
    assert readiness_drilldown_entry["size"] == "medium"
    assert readiness_drilldown_entry["status"] == "shipped"
    assert "Classifies ModelOps readiness warnings" in readiness_drilldown_entry["impact"]
    assert "priority" in readiness_drilldown_entry["impact"]
    assert "validation-hint" in readiness_drilldown_entry["impact"]
    assert "without calling NewAPI/Gemini/gateways" in readiness_drilldown_entry["impact"]
    assert "raw payloads" in readiness_drilldown_entry["impact"]
    assert "credentials" in readiness_drilldown_entry["impact"]
    assert "app/backend/services/model_ops_readiness.py" in readiness_drilldown_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_readiness.py" in readiness_drilldown_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in readiness_drilldown_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in readiness_drilldown_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in readiness_drilldown_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in readiness_drilldown_entry["evidence_paths"]
    assert "model-ops-readiness" in readiness_drilldown_entry["release_gate_links"]
    assert "frontend-ui-regression" in readiness_drilldown_entry["release_gate_links"]

    default_recommendation_readiness_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "model-ops-default-recommendation-readiness-binding"
    )
    assert default_recommendation_readiness_entry["size"] == "medium"
    assert default_recommendation_readiness_entry["status"] == "shipped"
    assert "default recommendation snapshot into required ModelOps readiness" in default_recommendation_readiness_entry["impact"]
    assert "role-level blocking and warning ids" in default_recommendation_readiness_entry["impact"]
    assert "default_recommendation_snapshot" in default_recommendation_readiness_entry["impact"]
    assert "without calling gateways" in default_recommendation_readiness_entry["impact"]
    assert "writing configuration" in default_recommendation_readiness_entry["impact"]
    assert "credentials" in default_recommendation_readiness_entry["impact"]
    assert "app/backend/services/model_default_recommendation_snapshot.py" in default_recommendation_readiness_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_ops_readiness.py" in default_recommendation_readiness_entry["evidence_paths"]
    assert "app/backend/tests/test_model_default_recommendation_snapshot.py" in default_recommendation_readiness_entry[
        "evidence_paths"
    ]
    assert "app/backend/tests/test_model_ops_readiness.py" in default_recommendation_readiness_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in default_recommendation_readiness_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in default_recommendation_readiness_entry["evidence_paths"]
    assert "docs/MODEL_OPS_READINESS.md" in default_recommendation_readiness_entry["evidence_paths"]
    assert "model-default-recommendation-snapshot" in default_recommendation_readiness_entry["release_gate_links"]
    assert "model-default-candidate-selector" in default_recommendation_readiness_entry["release_gate_links"]
    assert "model-ops-readiness" in default_recommendation_readiness_entry["release_gate_links"]
    assert "frontend-ui-regression" in default_recommendation_readiness_entry["release_gate_links"]

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
    assert "shared observed-model extraction" in catalog_candidate_patch_entry["impact"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in catalog_candidate_patch_entry[
        "evidence_paths"
    ]
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in catalog_candidate_patch_entry["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in catalog_candidate_patch_entry[
        "evidence_paths"
    ]
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
    catalog_candidate_impact_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-catalog-candidate-impact-replay"
    )
    assert catalog_candidate_impact_entry["size"] == "medium"
    assert catalog_candidate_impact_entry["status"] == "shipped"
    assert "sanitized Gemini candidate profiles" in catalog_candidate_impact_entry["impact"]
    assert "in-memory virtual catalog" in catalog_candidate_impact_entry["impact"]
    assert "cheap-first selector deltas" in catalog_candidate_impact_entry["impact"]
    assert "no-write/no-gateway safety boundaries" in catalog_candidate_impact_entry["impact"]
    assert "app/backend/services/model_catalog_candidate_impact_replay.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/backend/tests/test_model_catalog_candidate_impact_replay.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/backend/services/model_default_candidate_selector.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/backend/services/model_capability_matrix.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in catalog_candidate_impact_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in catalog_candidate_impact_entry["evidence_paths"]
    assert "docs/MODEL_CATALOG_CANDIDATE_IMPACT_REPLAY.md" in catalog_candidate_impact_entry["evidence_paths"]
    assert "model-catalog-candidate-impact-replay" in catalog_candidate_impact_entry["release_gate_links"]
    assert "model-catalog-candidate-patch-plan" in catalog_candidate_impact_entry["release_gate_links"]
    assert "model-default-candidate-selector" in catalog_candidate_impact_entry["release_gate_links"]
    assert "model-ops-readiness" in catalog_candidate_impact_entry["release_gate_links"]
    assert "frontend-ui-regression" in catalog_candidate_impact_entry["release_gate_links"]
    escalation_budget_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-cheap-first-escalation-budget"
    )
    assert escalation_budget_entry["size"] == "medium"
    assert escalation_budget_entry["status"] == "shipped"
    assert "aggregate cheap-first cascade budget gate" in escalation_budget_entry["impact"]
    assert "runaway retries" in escalation_budget_entry["impact"]
    assert "wasted escalation spend" in escalation_budget_entry["impact"]
    assert "operator-review coverage" in escalation_budget_entry["impact"]
    assert "app/backend/services/model_ops_cheap_first_escalation_budget.py" in escalation_budget_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_cheap_first_escalation_budget.py" in escalation_budget_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in escalation_budget_entry["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in escalation_budget_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in escalation_budget_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in escalation_budget_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in escalation_budget_entry["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_ESCALATION_BUDGET.md" in escalation_budget_entry["evidence_paths"]
    assert "model-ops-cheap-first-escalation-budget" in escalation_budget_entry["release_gate_links"]
    assert "model-ops-readiness" in escalation_budget_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in escalation_budget_entry["release_gate_links"]
    assert "frontend-ui-regression" in escalation_budget_entry["release_gate_links"]
    failure_upgrade_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-failure-upgrade-budget"
    )
    assert failure_upgrade_entry["size"] == "medium"
    assert failure_upgrade_entry["status"] == "shipped"
    assert "cheap-first failure upgrade decision gate" in failure_upgrade_entry["impact"]
    assert "premium approval" in failure_upgrade_entry["impact"]
    assert "attempt budget" in failure_upgrade_entry["impact"]
    assert "incremental cost decisions" in failure_upgrade_entry["impact"]
    assert "app/backend/services/model_failure_upgrade_budget.py" in failure_upgrade_entry["evidence_paths"]
    assert "app/backend/tests/test_model_failure_upgrade_budget.py" in failure_upgrade_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in failure_upgrade_entry["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in failure_upgrade_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in failure_upgrade_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in failure_upgrade_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in failure_upgrade_entry["evidence_paths"]
    assert "docs/MODEL_FAILURE_UPGRADE_BUDGET.md" in failure_upgrade_entry["evidence_paths"]
    assert "model-failure-upgrade-budget" in failure_upgrade_entry["release_gate_links"]
    assert "model-ops-readiness" in failure_upgrade_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in failure_upgrade_entry["release_gate_links"]
    assert "frontend-ui-regression" in failure_upgrade_entry["release_gate_links"]
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
    license_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-public-benchmark-license-gate"
    )
    assert license_gate_entry["size"] == "medium"
    assert license_gate_entry["status"] == "shipped"
    assert "metadata-only public legal benchmark license" in license_gate_entry["impact"]
    assert "attribution" in license_gate_entry["impact"]
    assert "privacy" in license_gate_entry["impact"]
    assert "storage" in license_gate_entry["impact"]
    assert "user-need" in license_gate_entry["impact"]
    assert "route-risk review evidence" in license_gate_entry["impact"]
    assert "without public dataset downloads" in license_gate_entry["impact"]
    assert "public benchmark text imports" in license_gate_entry["impact"]
    assert "public benchmark score claims" in license_gate_entry["impact"]
    assert "model or gateway calls" in license_gate_entry["impact"]
    assert "network calls" in license_gate_entry["impact"]
    assert "raw legal text" in license_gate_entry["impact"]
    assert "prompts" in license_gate_entry["impact"]
    assert "model outputs" in license_gate_entry["impact"]
    assert "payloads" in license_gate_entry["impact"]
    assert "credentials" in license_gate_entry["impact"]
    assert "app/backend/services/legal_public_benchmark_license_gate.py" in license_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_public_benchmark_license_gate.py" in license_gate_entry["evidence_paths"]
    assert "app/backend/services/legal_public_benchmark_sampler.py" in license_gate_entry["evidence_paths"]
    assert "app/backend/services/user_need_benchmark_coverage.py" in license_gate_entry["evidence_paths"]
    assert "app/backend/services/model_route_legal_benchmark_risk_queue.py" in license_gate_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in license_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in license_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in license_gate_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in license_gate_entry["evidence_paths"]
    assert "docs/LEGAL_PUBLIC_BENCHMARK_LICENSE_GATE.md" in license_gate_entry["evidence_paths"]
    assert "legal-public-benchmark-license-gate" in license_gate_entry["release_gate_links"]
    assert "legal-public-benchmark-sampler" in license_gate_entry["release_gate_links"]
    assert "user-need-benchmark-coverage" in license_gate_entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in license_gate_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in license_gate_entry["release_gate_links"]
    assert "traceable-legal-review" in license_gate_entry["user_need_ids"]
    assert "cheap-first-review-routing" in license_gate_entry["user_need_ids"]
    assert (
        "python -m pytest tests/test_legal_public_benchmark_license_gate.py "
        "tests/test_legal_public_benchmark_sampler.py tests/test_user_need_benchmark_coverage.py "
        "tests/test_model_route_legal_benchmark_risk_queue.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
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
    assert "app/backend/services/user_need_implementation_priority_queue.py" in priority_queue_entry["evidence_paths"]
    assert "app/backend/tests/test_user_need_implementation_priority_queue.py" in priority_queue_entry["evidence_paths"]
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
    assert "modelops-user-need-release-bridge" in priority_queue_entry["release_gate_links"]
    assert "model-ops-readiness" in priority_queue_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in priority_queue_entry["release_gate_links"]
    assert "model-ops-default-change-queue" in priority_queue_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py -q"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_user_need_gemini_route_coverage.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    assert (
        "python -m pytest tests/test_model_ops_user_need_release_bridge.py tests/test_user_need_implementation_priority_queue.py "
        "tests/test_user_need_gemini_route_coverage.py tests/test_model_ops_cheap_first_release_decision.py "
        "tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    route_coverage_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "user-need-gemini-route-coverage"
    )
    assert route_coverage_entry["size"] == "medium"
    assert route_coverage_entry["status"] == "shipped"
    assert "metadata-only user-need to Gemini route coverage evidence" in route_coverage_entry["impact"]
    assert "user-need benchmark coverage" in route_coverage_entry["impact"]
    assert "cheap-first calibration tasks" in route_coverage_entry["impact"]
    assert "Gemini cheap-first route preflight rows" in route_coverage_entry["impact"]
    assert "Flash-Lite protected needs" in route_coverage_entry["impact"]
    assert "premium/benchmark/license gaps" in route_coverage_entry["impact"]
    assert "unmapped route blockers" in route_coverage_entry["impact"]
    assert "without public dataset downloads" in route_coverage_entry["impact"]
    assert "public benchmark sample imports" in route_coverage_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google/gateway/app-AI/network calls" in route_coverage_entry["impact"]
    assert "configuration writes" in route_coverage_entry["impact"]
    assert "default route changes" in route_coverage_entry["impact"]
    assert "traffic shifts" in route_coverage_entry["impact"]
    assert "raw legal text" in route_coverage_entry["impact"]
    assert "prompts" in route_coverage_entry["impact"]
    assert "route payloads" in route_coverage_entry["impact"]
    assert "request/response bodies" in route_coverage_entry["impact"]
    assert "headers" in route_coverage_entry["impact"]
    assert "model outputs" in route_coverage_entry["impact"]
    assert "gateway responses" in route_coverage_entry["impact"]
    assert "credentials" in route_coverage_entry["impact"]
    assert "emails" in route_coverage_entry["impact"]
    assert "user identifiers" in route_coverage_entry["impact"]
    assert "app/backend/services/user_need_gemini_route_coverage.py" in route_coverage_entry["evidence_paths"]
    assert "app/backend/tests/test_user_need_gemini_route_coverage.py" in route_coverage_entry["evidence_paths"]
    assert "app/backend/services/model_ops_gemini_cheap_first_route_preflight.py" in route_coverage_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in route_coverage_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in route_coverage_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in route_coverage_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in route_coverage_entry["evidence_paths"]
    assert "docs/USER_NEED_GEMINI_ROUTE_COVERAGE.md" in route_coverage_entry["evidence_paths"]
    assert "docs/USER_NEED_BENCHMARK_COVERAGE.md" in route_coverage_entry["evidence_paths"]
    assert "docs/USER_NEEDS_RADAR.md" in route_coverage_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in route_coverage_entry["evidence_paths"]
    assert "user-need-gemini-route-coverage" in route_coverage_entry["release_gate_links"]
    assert "user-needs-radar" in route_coverage_entry["release_gate_links"]
    assert "user-need-benchmark-coverage" in route_coverage_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-calibration" in route_coverage_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-route-preflight" in route_coverage_entry["release_gate_links"]
    assert "modelops-gemini-cheap-first-coverage-gate" in route_coverage_entry["release_gate_links"]
    assert "model-route-legal-benchmark-risk-queue" in route_coverage_entry["release_gate_links"]
    assert "modelops-user-need-release-bridge" in route_coverage_entry["release_gate_links"]
    assert "model-ops-readiness" in route_coverage_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in route_coverage_entry["release_gate_links"]
    assert "model-ops-default-change-queue" in route_coverage_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in route_coverage_entry["release_gate_links"]
    bridge_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "modelops-user-need-release-bridge"
    )
    assert bridge_entry["size"] == "medium"
    assert bridge_entry["status"] == "shipped"
    assert "metadata-only ModelOps user-need release bridge" in bridge_entry["impact"]
    assert "implementation priority queue rows" in bridge_entry["impact"]
    assert "Gemini cheap-first route coverage" in bridge_entry["impact"]
    assert "high-priority implementation or route blockers" in bridge_entry["impact"]
    assert "public benchmark license review" in bridge_entry["impact"]
    assert "premium exception review" in bridge_entry["impact"]
    assert "maintainer-review only" in bridge_entry["impact"]
    assert "NewAPI/Gemini/OpenAI/Google/gateway/app-AI/network calls" in bridge_entry["impact"]
    assert "configuration writes" in bridge_entry["impact"]
    assert "default route changes" in bridge_entry["impact"]
    assert "traffic shifts" in bridge_entry["impact"]
    assert "raw legal text" in bridge_entry["impact"]
    assert "model outputs" in bridge_entry["impact"]
    assert "credentials" in bridge_entry["impact"]
    assert "emails" in bridge_entry["impact"]
    assert "user identifiers" in bridge_entry["impact"]
    assert "app/backend/services/model_ops_user_need_release_bridge.py" in bridge_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_user_need_release_bridge.py" in bridge_entry["evidence_paths"]
    assert "app/backend/services/user_need_implementation_priority_queue.py" in bridge_entry["evidence_paths"]
    assert "app/backend/tests/test_user_need_implementation_priority_queue.py" in bridge_entry["evidence_paths"]
    assert "app/backend/services/user_need_gemini_route_coverage.py" in bridge_entry["evidence_paths"]
    assert "app/backend/tests/test_user_need_gemini_route_coverage.py" in bridge_entry["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in bridge_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_cheap_first_release_decision.py" in bridge_entry["evidence_paths"]
    assert "app/backend/services/model_ops_readiness.py" in bridge_entry["evidence_paths"]
    assert "app/backend/tests/test_model_ops_readiness.py" in bridge_entry["evidence_paths"]
    assert "app/backend/routers/aihub.py" in bridge_entry["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in bridge_entry["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in bridge_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in bridge_entry["evidence_paths"]
    assert "docs/MODEL_OPS_USER_NEED_RELEASE_BRIDGE.md" in bridge_entry["evidence_paths"]
    assert "modelops-user-need-release-bridge" in bridge_entry["release_gate_links"]
    assert "model-ops-readiness" in bridge_entry["release_gate_links"]
    assert "model-ops-cheap-first-release-decision" in bridge_entry["release_gate_links"]
    assert "model-ops-default-change-queue" in bridge_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in bridge_entry["release_gate_links"]
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
    default_ladder_boundary_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "model-default-ladder-review-boundaries"
    )
    assert default_ladder_boundary_entry["size"] == "medium"
    assert default_ladder_boundary_entry["status"] == "shipped"
    assert default_ladder_boundary_entry["category"] == "model_ops"
    assert "default_eligible" in default_ladder_boundary_entry["impact"]
    assert "review-only" in default_ladder_boundary_entry["impact"]
    assert "promotion blockers" in default_ladder_boundary_entry["impact"]
    assert "preview" in default_ladder_boundary_entry["impact"]
    assert "unpriced" in default_ladder_boundary_entry["impact"]
    assert "premium-over-budget" in default_ladder_boundary_entry["impact"]
    assert "calling gateways" in default_ladder_boundary_entry["impact"]
    assert "raw legal text" in default_ladder_boundary_entry["impact"]
    assert "credentials" in default_ladder_boundary_entry["impact"]
    assert "app/backend/services/model_default_candidate_selector.py" in default_ladder_boundary_entry["evidence_paths"]
    assert "app/backend/tests/test_model_default_candidate_selector.py" in default_ladder_boundary_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in default_ladder_boundary_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in default_ladder_boundary_entry["evidence_paths"]
    assert "docs/MODEL_DEFAULT_CANDIDATE_SELECTOR.md" in default_ladder_boundary_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_MODEL_SELECTOR.md" in default_ladder_boundary_entry["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md" in default_ladder_boundary_entry["evidence_paths"]
    assert "model-default-candidate-selector" in default_ladder_boundary_entry["release_gate_links"]
    assert "gemini-newapi-model-selector" in default_ladder_boundary_entry["release_gate_links"]
    assert "gemini-newapi-cheap-first-policy" in default_ladder_boundary_entry["release_gate_links"]
    assert "model-ops-readiness" in default_ladder_boundary_entry["release_gate_links"]
    assert "frontend-typecheck" in default_ladder_boundary_entry["release_gate_links"]
    missing_answer_citation_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-rag-missing-answer-citation-blocker"
    )
    assert missing_answer_citation_entry["size"] == "medium"
    assert missing_answer_citation_entry["status"] == "shipped"
    assert "expected or retrieved legal source IDs" in missing_answer_citation_entry["impact"]
    assert "no citation source IDs" in missing_answer_citation_entry["impact"]
    assert "citation precision to zero" in missing_answer_citation_entry["impact"]
    assert "metadata-only coverage flags" in missing_answer_citation_entry["impact"]
    assert "raw retrieval context" in missing_answer_citation_entry["impact"]
    assert "answer text" in missing_answer_citation_entry["impact"]
    assert "prompts" in missing_answer_citation_entry["impact"]
    assert "model output" in missing_answer_citation_entry["impact"]
    assert "credentials" in missing_answer_citation_entry["impact"]
    assert "network calls" in missing_answer_citation_entry["impact"]
    assert "app/backend/services/legal_rag_evaluation.py" in missing_answer_citation_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_evaluation.py" in missing_answer_citation_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EVALUATION.md" in missing_answer_citation_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in missing_answer_citation_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in missing_answer_citation_entry["evidence_paths"]
    assert "legal-rag-evaluation" in missing_answer_citation_entry["release_gate_links"]
    assert "legal-rag-index-binding" in missing_answer_citation_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in missing_answer_citation_entry["release_gate_links"]
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
    index_coverage_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-index-coverage-gate"
    )
    assert index_coverage_entry["category"] == "benchmark"
    assert index_coverage_entry["size"] == "medium"
    assert index_coverage_entry["status"] == "shipped"
    assert "Legal RAG index coverage gate" in index_coverage_entry["impact"]
    assert "index binding plan rows" in index_coverage_entry["impact"]
    assert "filter validation" in index_coverage_entry["impact"]
    assert "source coverage" in index_coverage_entry["impact"]
    assert "retrieval locator coverage" in index_coverage_entry["impact"]
    assert "jurisdiction/freshness gaps" in index_coverage_entry["impact"]
    assert "missing or stale source counts" in index_coverage_entry["impact"]
    assert "forbidden filters" in index_coverage_entry["impact"]
    assert "cheap-first review actions" in index_coverage_entry["impact"]
    assert "typed maintenance API helpers" in index_coverage_entry["impact"]
    assert "maintenance UI review" in index_coverage_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in index_coverage_entry["impact"]
    assert "gateway calls" in index_coverage_entry["impact"]
    assert "network calls" in index_coverage_entry["impact"]
    assert "dataset downloads" in index_coverage_entry["impact"]
    assert "source-id echoing" in index_coverage_entry["impact"]
    assert "raw query" in index_coverage_entry["impact"]
    assert "raw retrieved context" in index_coverage_entry["impact"]
    assert "raw legal text" in index_coverage_entry["impact"]
    assert "prompts" in index_coverage_entry["impact"]
    assert "model outputs" in index_coverage_entry["impact"]
    assert "gateway payloads" in index_coverage_entry["impact"]
    assert "credentials" in index_coverage_entry["impact"]
    assert "client-delivery or index-quality claims" in index_coverage_entry["impact"]
    assert "app/backend/services/legal_rag_index_coverage_gate.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_index_coverage_gate.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_index_binding.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in index_coverage_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in index_coverage_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in index_coverage_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in index_coverage_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in index_coverage_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_INDEX_COVERAGE_GATE.md" in index_coverage_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in index_coverage_entry["evidence_paths"]
    assert "legal-rag-index-coverage-gate" in index_coverage_entry["release_gate_links"]
    assert "legal-rag-index-binding" in index_coverage_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in index_coverage_entry["release_gate_links"]
    assert "legal-rag-retrieval-observation-gate" in index_coverage_entry["release_gate_links"]
    assert "frontend-typecheck" in index_coverage_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in index_coverage_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_index_binding.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    embedding_readiness_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-readiness-gate"
    )
    assert embedding_readiness_entry["category"] == "benchmark"
    assert embedding_readiness_entry["size"] == "medium"
    assert embedding_readiness_entry["status"] == "shipped"
    assert "Gemini embedding cheap-first defaults" in embedding_readiness_entry["impact"]
    assert "text-only index preflight rows" in embedding_readiness_entry["impact"]
    assert "multimodal embedding review boundaries" in embedding_readiness_entry["impact"]
    assert "index coverage blockers" in embedding_readiness_entry["impact"]
    assert "retrieval diagnostics linkage" in embedding_readiness_entry["impact"]
    assert "typed maintenance API helpers" in embedding_readiness_entry["impact"]
    assert "maintenance UI review" in embedding_readiness_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in embedding_readiness_entry["impact"]
    assert "gateway calls" in embedding_readiness_entry["impact"]
    assert "network calls" in embedding_readiness_entry["impact"]
    assert "index writes" in embedding_readiness_entry["impact"]
    assert "dataset downloads" in embedding_readiness_entry["impact"]
    assert "source-id echoing" in embedding_readiness_entry["impact"]
    assert "raw query" in embedding_readiness_entry["impact"]
    assert "raw retrieved context" in embedding_readiness_entry["impact"]
    assert "raw legal text" in embedding_readiness_entry["impact"]
    assert "embedding vectors" in embedding_readiness_entry["impact"]
    assert "prompts" in embedding_readiness_entry["impact"]
    assert "model outputs" in embedding_readiness_entry["impact"]
    assert "gateway payloads" in embedding_readiness_entry["impact"]
    assert "credentials" in embedding_readiness_entry["impact"]
    assert "embedding/index/retrieval quality claims" in embedding_readiness_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_readiness_gate.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_readiness_gate.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in embedding_readiness_entry["evidence_paths"]
    assert (
        "app/backend/services/model_ops_gemini_embedding_cheap_first_preflight.py"
        in embedding_readiness_entry["evidence_paths"]
    )
    assert "app/backend/services/legal_rag_index_coverage_gate.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_retrieval_diagnostics_gate.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in embedding_readiness_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in embedding_readiness_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in embedding_readiness_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in embedding_readiness_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_READINESS_GATE.md" in embedding_readiness_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in embedding_readiness_entry["evidence_paths"]
    assert "legal-rag-embedding-readiness-gate" in embedding_readiness_entry["release_gate_links"]
    assert "modelops-gemini-embedding-cheap-first-preflight" in embedding_readiness_entry["release_gate_links"]
    assert "legal-rag-index-coverage-gate" in embedding_readiness_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in embedding_readiness_entry["release_gate_links"]
    assert "frontend-typecheck" in embedding_readiness_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in embedding_readiness_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_readiness_gate.py "
        "tests/test_model_ops_gemini_embedding_cheap_first_preflight.py "
        "tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_retrieval_diagnostics_gate.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    chunk_policy_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-chunk-policy-gate"
    )
    assert chunk_policy_entry["category"] == "benchmark"
    assert chunk_policy_entry["size"] == "medium"
    assert chunk_policy_entry["status"] == "shipped"
    assert "token-estimate chunking" in chunk_policy_entry["impact"]
    assert "source-type split strategies" in chunk_policy_entry["impact"]
    assert "citation-anchor checks" in chunk_policy_entry["impact"]
    assert "retrieval-locator blockers" in chunk_policy_entry["impact"]
    assert "freshness review boundaries" in chunk_policy_entry["impact"]
    assert "laptop-safe chunk limits" in chunk_policy_entry["impact"]
    assert "cheap Gemini embedding defaults" in chunk_policy_entry["impact"]
    assert "typed maintenance API helpers" in chunk_policy_entry["impact"]
    assert "maintenance UI review" in chunk_policy_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in chunk_policy_entry["impact"]
    assert "embedding creation" in chunk_policy_entry["impact"]
    assert "index writes" in chunk_policy_entry["impact"]
    assert "source-id echoing" in chunk_policy_entry["impact"]
    assert "raw legal text" in chunk_policy_entry["impact"]
    assert "source chunks" in chunk_policy_entry["impact"]
    assert "embedding vectors" in chunk_policy_entry["impact"]
    assert "credentials" in chunk_policy_entry["impact"]
    assert "chunk/embedding/index/retrieval quality claims" in chunk_policy_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_chunk_policy_gate.py" in chunk_policy_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_chunk_policy_gate.py" in chunk_policy_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in chunk_policy_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_readiness_gate.py" in chunk_policy_entry["evidence_paths"]
    assert "app/backend/services/legal_source_durable_index_plan.py" in chunk_policy_entry["evidence_paths"]
    assert "app/backend/services/legal_source_ingestion_metadata.py" in chunk_policy_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in chunk_policy_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in chunk_policy_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in chunk_policy_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_CHUNK_POLICY_GATE.md" in chunk_policy_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in chunk_policy_entry["evidence_paths"]
    assert "legal-rag-embedding-chunk-policy-gate" in chunk_policy_entry["release_gate_links"]
    assert "legal-rag-embedding-readiness-gate" in chunk_policy_entry["release_gate_links"]
    assert "legal-source-durable-index-plan" in chunk_policy_entry["release_gate_links"]
    assert "legal-source-ingestion-metadata" in chunk_policy_entry["release_gate_links"]
    assert "legal-rag-index-coverage-gate" in chunk_policy_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in chunk_policy_entry["release_gate_links"]
    assert "frontend-typecheck" in chunk_policy_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in chunk_policy_entry["release_gate_links"]

    dry_run_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-index-dry-run-gate"
    )
    assert dry_run_entry["category"] == "benchmark"
    assert dry_run_entry["size"] == "medium"
    assert dry_run_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding index dry-run gate" in dry_run_entry["impact"]
    assert "reviewable index manifest rows" in dry_run_entry["impact"]
    assert "planned vector-slot counts" in dry_run_entry["impact"]
    assert "durable index persistence-field checks" in dry_run_entry["impact"]
    assert "repository validation linkage" in dry_run_entry["impact"]
    assert "commit-action blockers" in dry_run_entry["impact"]
    assert "maintenance UI review" in dry_run_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in dry_run_entry["impact"]
    assert "embedding creation" in dry_run_entry["impact"]
    assert "index or database writes" in dry_run_entry["impact"]
    assert "source-id echoing" in dry_run_entry["impact"]
    assert "raw legal text" in dry_run_entry["impact"]
    assert "source chunks" in dry_run_entry["impact"]
    assert "embedding vectors" in dry_run_entry["impact"]
    assert "credentials" in dry_run_entry["impact"]
    assert "index/vector/retrieval quality claims" in dry_run_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_index_dry_run_gate.py" in dry_run_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_index_dry_run_gate.py" in dry_run_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in dry_run_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_chunk_policy_gate.py" in dry_run_entry["evidence_paths"]
    assert "app/backend/services/legal_source_durable_index_plan.py" in dry_run_entry["evidence_paths"]
    assert "app/backend/services/legal_source_index_repository.py" in dry_run_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in dry_run_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in dry_run_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in dry_run_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_INDEX_DRY_RUN_GATE.md" in dry_run_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in dry_run_entry["evidence_paths"]
    assert "legal-rag-embedding-index-dry-run-gate" in dry_run_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in dry_run_entry["release_gate_links"]
    assert "legal-rag-embedding-readiness-gate" in dry_run_entry["release_gate_links"]
    assert "legal-source-durable-index-plan" in dry_run_entry["release_gate_links"]
    assert "legal-source-index-repository" in dry_run_entry["release_gate_links"]
    assert "legal-rag-index-coverage-gate" in dry_run_entry["release_gate_links"]
    assert "frontend-typecheck" in dry_run_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in dry_run_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_index_dry_run_gate.py "
        "tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_legal_source_durable_index_plan.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )

    batch_budget_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-batch-budget-gate"
    )
    assert batch_budget_entry["category"] == "benchmark"
    assert batch_budget_entry["size"] == "medium"
    assert batch_budget_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding batch budget gate" in batch_budget_entry["impact"]
    assert "cheap Gemini embedding batch-budget rows" in batch_budget_entry["impact"]
    assert "planned batch counts" in batch_budget_entry["impact"]
    assert "laptop-safe chunk and token limits" in batch_budget_entry["impact"]
    assert "local catalog batch-cost estimates" in batch_budget_entry["impact"]
    assert "release-action blockers" in batch_budget_entry["impact"]
    assert "maintenance UI review" in batch_budget_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in batch_budget_entry["impact"]
    assert "embedding creation" in batch_budget_entry["impact"]
    assert "index or database writes" in batch_budget_entry["impact"]
    assert "source-id echoing" in batch_budget_entry["impact"]
    assert "raw legal text" in batch_budget_entry["impact"]
    assert "source chunks" in batch_budget_entry["impact"]
    assert "embedding vectors" in batch_budget_entry["impact"]
    assert "credentials" in batch_budget_entry["impact"]
    assert "live pricing claims" in batch_budget_entry["impact"]
    assert "embedding/index/retrieval quality claims" in batch_budget_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_batch_budget_gate.py" in batch_budget_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_batch_budget_gate.py" in batch_budget_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in batch_budget_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_index_dry_run_gate.py" in batch_budget_entry["evidence_paths"]
    assert "app/backend/services/model_ops_gemini_embedding_cheap_first_preflight.py" in batch_budget_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in batch_budget_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in batch_budget_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in batch_budget_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_BATCH_BUDGET_GATE.md" in batch_budget_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in batch_budget_entry["evidence_paths"]
    assert "legal-rag-embedding-batch-budget-gate" in batch_budget_entry["release_gate_links"]
    assert "legal-rag-embedding-index-dry-run-gate" in batch_budget_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in batch_budget_entry["release_gate_links"]
    assert "legal-rag-embedding-readiness-gate" in batch_budget_entry["release_gate_links"]
    assert "modelops-gemini-embedding-cheap-first-preflight" in batch_budget_entry["release_gate_links"]
    assert "frontend-typecheck" in batch_budget_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in batch_budget_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_batch_budget_gate.py "
        "tests/test_legal_rag_embedding_index_dry_run_gate.py "
        "tests/test_model_ops_gemini_embedding_cheap_first_preflight.py "
        "tests/test_release_readiness.py tests/test_continuous_update_ledger.py "
        "tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )

    approval_packet_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-batch-approval-packet"
    )
    assert approval_packet_entry["category"] == "benchmark"
    assert approval_packet_entry["size"] == "medium"
    assert approval_packet_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding batch approval packet" in approval_packet_entry["impact"]
    assert "serial low-resource queue order" in approval_packet_entry["impact"]
    assert "max_parallel_embedding_requests=1" in approval_packet_entry["impact"]
    assert "required maintainer and RAG-index reviewer signoff roles" in approval_packet_entry["impact"]
    assert "pre-approval checks" in approval_packet_entry["impact"]
    assert "advance/hold/block run actions" in approval_packet_entry["impact"]
    assert "maintenance UI review" in approval_packet_entry["impact"]
    assert "without claiming approval" in approval_packet_entry["impact"]
    assert "collecting approver identity" in approval_packet_entry["impact"]
    assert "writing approval records" in approval_packet_entry["impact"]
    assert "NewAPI/Gemini/model calls" in approval_packet_entry["impact"]
    assert "embedding creation" in approval_packet_entry["impact"]
    assert "index or database writes" in approval_packet_entry["impact"]
    assert "source-id echoing" in approval_packet_entry["impact"]
    assert "raw legal text" in approval_packet_entry["impact"]
    assert "source chunks" in approval_packet_entry["impact"]
    assert "embedding vectors" in approval_packet_entry["impact"]
    assert "credentials" in approval_packet_entry["impact"]
    assert "live pricing claims" in approval_packet_entry["impact"]
    assert "embedding/index/retrieval quality claims" in approval_packet_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_batch_approval_packet.py" in approval_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_batch_approval_packet.py" in approval_packet_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in approval_packet_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_batch_budget_gate.py" in approval_packet_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_index_dry_run_gate.py" in approval_packet_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in approval_packet_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in approval_packet_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in approval_packet_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_BATCH_APPROVAL_PACKET.md" in approval_packet_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in approval_packet_entry["evidence_paths"]
    assert "legal-rag-embedding-batch-approval-packet" in approval_packet_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-budget-gate" in approval_packet_entry["release_gate_links"]
    assert "legal-rag-embedding-index-dry-run-gate" in approval_packet_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in approval_packet_entry["release_gate_links"]
    assert "modelops-gemini-embedding-cheap-first-preflight" in approval_packet_entry["release_gate_links"]
    assert "frontend-typecheck" in approval_packet_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in approval_packet_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_batch_approval_packet.py "
        "tests/test_legal_rag_embedding_batch_budget_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    observation_gate_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-embedding-batch-observation-gate"
    )
    assert observation_gate_entry["category"] == "benchmark"
    assert observation_gate_entry["size"] == "medium"
    assert observation_gate_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding batch observation gate" in observation_gate_entry["impact"]
    assert "sanitized aggregate observations" in observation_gate_entry["impact"]
    assert "observed batch/chunk/vector-slot/token counts" in observation_gate_entry["impact"]
    assert "cost deltas" in observation_gate_entry["impact"]
    assert "max_parallel_embedding_requests=1" in observation_gate_entry["impact"]
    assert "allow/hold/block index-review actions" in observation_gate_entry["impact"]
    assert "maintenance UI review" in observation_gate_entry["impact"]
    assert "without claiming maintainer approval" in observation_gate_entry["impact"]
    assert "executing embeddings" in observation_gate_entry["impact"]
    assert "NewAPI/Gemini/model calls" in observation_gate_entry["impact"]
    assert "embedding creation by the gate" in observation_gate_entry["impact"]
    assert "index or database writes" in observation_gate_entry["impact"]
    assert "approver identity collection" in observation_gate_entry["impact"]
    assert "source-id echoing" in observation_gate_entry["impact"]
    assert "approval item id echoing" in observation_gate_entry["impact"]
    assert "raw legal text" in observation_gate_entry["impact"]
    assert "source chunks" in observation_gate_entry["impact"]
    assert "embedding vectors" in observation_gate_entry["impact"]
    assert "credentials" in observation_gate_entry["impact"]
    assert "live pricing claims" in observation_gate_entry["impact"]
    assert "embedding/index/retrieval quality claims" in observation_gate_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_batch_observation_gate.py" in observation_gate_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_batch_observation_gate.py" in observation_gate_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in observation_gate_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_batch_approval_packet.py" in observation_gate_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_batch_budget_gate.py" in observation_gate_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in observation_gate_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in observation_gate_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in observation_gate_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_BATCH_OBSERVATION_GATE.md" in observation_gate_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in observation_gate_entry["evidence_paths"]
    assert "legal-rag-embedding-batch-observation-gate" in observation_gate_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-approval-packet" in observation_gate_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-budget-gate" in observation_gate_entry["release_gate_links"]
    assert "legal-rag-embedding-index-dry-run-gate" in observation_gate_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in observation_gate_entry["release_gate_links"]
    assert "modelops-gemini-embedding-cheap-first-preflight" in observation_gate_entry["release_gate_links"]
    assert "frontend-typecheck" in observation_gate_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in observation_gate_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_batch_observation_gate.py "
        "tests/test_legal_rag_embedding_batch_approval_packet.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    commit_review_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-rag-embedding-index-commit-review-packet"
    )
    assert commit_review_entry["category"] == "benchmark"
    assert commit_review_entry["size"] == "medium"
    assert commit_review_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding index commit review packet" in commit_review_entry["impact"]
    assert "ready aggregate embedding observations" in commit_review_entry["impact"]
    assert "vector-slot match evidence" in commit_review_entry["impact"]
    assert "observed chunk/cost evidence" in commit_review_entry["impact"]
    assert "required maintainer/RAG-index/privacy signoffs" in commit_review_entry["impact"]
    assert "pre-commit checks" in commit_review_entry["impact"]
    assert "prepare/hold/block commit-review actions" in commit_review_entry["impact"]
    assert "maintenance UI review" in commit_review_entry["impact"]
    assert "without claiming maintainer commit approval" in commit_review_entry["impact"]
    assert "executing embeddings" in commit_review_entry["impact"]
    assert "NewAPI/Gemini/model calls" in commit_review_entry["impact"]
    assert "index or database writes" in commit_review_entry["impact"]
    assert "commit record writes" in commit_review_entry["impact"]
    assert "committer identity collection" in commit_review_entry["impact"]
    assert "source-id echoing" in commit_review_entry["impact"]
    assert "approval item id echoing" in commit_review_entry["impact"]
    assert "raw legal text" in commit_review_entry["impact"]
    assert "source chunks" in commit_review_entry["impact"]
    assert "embedding vectors" in commit_review_entry["impact"]
    assert "credentials" in commit_review_entry["impact"]
    assert "live pricing claims" in commit_review_entry["impact"]
    assert "embedding/index/retrieval quality claims" in commit_review_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_index_commit_review_packet.py" in commit_review_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_index_commit_review_packet.py" in commit_review_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in commit_review_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_batch_observation_gate.py" in commit_review_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_batch_approval_packet.py" in commit_review_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in commit_review_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in commit_review_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in commit_review_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_INDEX_COMMIT_REVIEW_PACKET.md" in commit_review_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in commit_review_entry["evidence_paths"]
    assert "legal-rag-embedding-index-commit-review-packet" in commit_review_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-observation-gate" in commit_review_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-approval-packet" in commit_review_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-budget-gate" in commit_review_entry["release_gate_links"]
    assert "legal-rag-embedding-index-dry-run-gate" in commit_review_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in commit_review_entry["release_gate_links"]
    assert "frontend-typecheck" in commit_review_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in commit_review_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_index_commit_review_packet.py "
        "tests/test_legal_rag_embedding_batch_observation_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    post_commit_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-rag-embedding-index-post-commit-verification-gate"
    )
    assert post_commit_entry["category"] == "benchmark"
    assert post_commit_entry["size"] == "medium"
    assert post_commit_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding index post-commit verification gate" in post_commit_entry["impact"]
    assert "commit-review rows" in post_commit_entry["impact"]
    assert "sanitized post-commit observations" in post_commit_entry["impact"]
    assert "expected/observed vector-slot counts" in post_commit_entry["impact"]
    assert "index entry counts" in post_commit_entry["impact"]
    assert "metadata records" in post_commit_entry["impact"]
    assert "retrieval locators" in post_commit_entry["impact"]
    assert "checksum records" in post_commit_entry["impact"]
    assert "failed-entry totals" in post_commit_entry["impact"]
    assert "rollback signals" in post_commit_entry["impact"]
    assert "allow/hold/block retrieval-diagnostics review actions" in post_commit_entry["impact"]
    assert "maintenance UI review" in post_commit_entry["impact"]
    assert "without claiming maintainer commit approval" in post_commit_entry["impact"]
    assert "executing embeddings" in post_commit_entry["impact"]
    assert "NewAPI/Gemini/model calls" in post_commit_entry["impact"]
    assert "index or database writes" in post_commit_entry["impact"]
    assert "commit record writes" in post_commit_entry["impact"]
    assert "production retrieval enablement" in post_commit_entry["impact"]
    assert "committer identity collection" in post_commit_entry["impact"]
    assert "source-id echoing" in post_commit_entry["impact"]
    assert "approval item id echoing" in post_commit_entry["impact"]
    assert "raw legal text" in post_commit_entry["impact"]
    assert "source chunks" in post_commit_entry["impact"]
    assert "embedding vectors" in post_commit_entry["impact"]
    assert "credentials" in post_commit_entry["impact"]
    assert "live pricing claims" in post_commit_entry["impact"]
    assert "embedding/index/retrieval quality claims" in post_commit_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_index_post_commit_verification_gate.py" in post_commit_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_index_post_commit_verification_gate.py" in post_commit_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in post_commit_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_index_commit_review_packet.py" in post_commit_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_index_commit_review_packet.py" in post_commit_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in post_commit_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in post_commit_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in post_commit_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_INDEX_POST_COMMIT_VERIFICATION_GATE.md" in post_commit_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in post_commit_entry["evidence_paths"]
    assert "legal-rag-embedding-index-post-commit-verification-gate" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-index-commit-review-packet" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-observation-gate" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-approval-packet" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-batch-budget-gate" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-index-dry-run-gate" in post_commit_entry["release_gate_links"]
    assert "legal-rag-embedding-chunk-policy-gate" in post_commit_entry["release_gate_links"]
    assert "frontend-typecheck" in post_commit_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in post_commit_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_index_post_commit_verification_gate.py "
        "tests/test_legal_rag_embedding_index_commit_review_packet.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    handoff_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-rag-embedding-retrieval-diagnostics-handoff-gate"
    )
    assert handoff_entry["category"] == "benchmark"
    assert handoff_entry["size"] == "medium"
    assert handoff_entry["status"] == "shipped"
    assert "metadata-only Legal RAG embedding retrieval diagnostics handoff gate" in handoff_entry["impact"]
    assert "post-commit verification rows" in handoff_entry["impact"]
    assert "ready/hold/block handoff rows" in handoff_entry["impact"]
    assert "safe handoff payload fields" in handoff_entry["impact"]
    assert "diagnostics-review-only actions" in handoff_entry["impact"]
    assert "rollback review links" in handoff_entry["impact"]
    assert "production retrieval false flags" in handoff_entry["impact"]
    assert "maintenance UI review" in handoff_entry["impact"]
    assert "without executing retrieval diagnostics" in handoff_entry["impact"]
    assert "enabling production retrieval" in handoff_entry["impact"]
    assert "claiming index or retrieval quality" in handoff_entry["impact"]
    assert "executing embeddings" in handoff_entry["impact"]
    assert "NewAPI/Gemini/model calls" in handoff_entry["impact"]
    assert "index or database writes" in handoff_entry["impact"]
    assert "commit record writes" in handoff_entry["impact"]
    assert "committer identity collection" in handoff_entry["impact"]
    assert "source-id echoing" in handoff_entry["impact"]
    assert "raw query" in handoff_entry["impact"]
    assert "user question" in handoff_entry["impact"]
    assert "retrieved context" in handoff_entry["impact"]
    assert "source chunks" in handoff_entry["impact"]
    assert "embedding vectors" in handoff_entry["impact"]
    assert "credentials" in handoff_entry["impact"]
    assert "legal advice/client delivery claims" in handoff_entry["impact"]
    assert "app/backend/services/legal_rag_embedding_retrieval_diagnostics_handoff_gate.py" in handoff_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py" in handoff_entry["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in handoff_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_embedding_index_post_commit_verification_gate.py" in handoff_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_embedding_index_post_commit_verification_gate.py" in handoff_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_retrieval_diagnostics_gate.py" in handoff_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in handoff_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in handoff_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in handoff_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EMBEDDING_RETRIEVAL_DIAGNOSTICS_HANDOFF_GATE.md" in handoff_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in handoff_entry["evidence_paths"]
    assert "legal-rag-embedding-retrieval-diagnostics-handoff-gate" in handoff_entry["release_gate_links"]
    assert "legal-rag-embedding-index-post-commit-verification-gate" in handoff_entry["release_gate_links"]
    assert "legal-rag-embedding-index-commit-review-packet" in handoff_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in handoff_entry["release_gate_links"]
    assert "frontend-typecheck" in handoff_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in handoff_entry["release_gate_links"]
    assert (
        "python -m pytest tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py "
        "tests/test_legal_rag_embedding_index_post_commit_verification_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q "
        "&& cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    benchmark_alignment_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-benchmark-alignment"
    )
    assert benchmark_alignment_entry["category"] == "benchmark"
    assert benchmark_alignment_entry["size"] == "medium"
    assert "LegalBench-RAG" in benchmark_alignment_entry["impact"]
    assert "CRAG" in benchmark_alignment_entry["impact"]
    assert "RAGAS" in benchmark_alignment_entry["impact"]
    assert "Legal RAG Bench" in benchmark_alignment_entry["impact"]
    assert "cheap-first Gemini/NewAPI boundaries" in benchmark_alignment_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in benchmark_alignment_entry["impact"]
    assert "public dataset downloads" in benchmark_alignment_entry["impact"]
    assert "public benchmark text" in benchmark_alignment_entry["impact"]
    assert "raw query" in benchmark_alignment_entry["impact"]
    assert "raw retrieved context" in benchmark_alignment_entry["impact"]
    assert "raw legal text" in benchmark_alignment_entry["impact"]
    assert "prompts" in benchmark_alignment_entry["impact"]
    assert "model outputs" in benchmark_alignment_entry["impact"]
    assert "credentials" in benchmark_alignment_entry["impact"]
    assert "app/backend/services/legal_rag_benchmark_alignment.py" in benchmark_alignment_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_benchmark_alignment.py" in benchmark_alignment_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in benchmark_alignment_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_BENCHMARK_ALIGNMENT.md" in benchmark_alignment_entry["evidence_paths"]
    assert "legal-rag-benchmark-alignment" in benchmark_alignment_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in benchmark_alignment_entry["release_gate_links"]
    assert "legal-rag-abstention-escalation-gate" in benchmark_alignment_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in benchmark_alignment_entry["release_gate_links"]
    retrieval_observation_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-retrieval-observation-gate"
    )
    assert "app/backend/services/legal_rag_retrieval_observation_gate.py" in retrieval_observation_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_retrieval_observation_gate.py" in retrieval_observation_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in retrieval_observation_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in retrieval_observation_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in retrieval_observation_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_RETRIEVAL_OBSERVATION_GATE.md" in retrieval_observation_entry["evidence_paths"]
    assert "legal-rag-retrieval-observation-gate" in retrieval_observation_entry["release_gate_links"]
    assert "legal-rag-selected-source-citation-validation" in retrieval_observation_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in retrieval_observation_entry["release_gate_links"]
    assert "legal-rag-authority-citation-gate" in retrieval_observation_entry["release_gate_links"]
    assert "frontend-typecheck" in retrieval_observation_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in retrieval_observation_entry["release_gate_links"]
    assert "model-escalation-policy" in retrieval_observation_entry["release_gate_links"]
    assert "sanitized local retrieval observation rows" in retrieval_observation_entry["impact"]
    assert "selected-source citation validation" in retrieval_observation_entry["impact"]
    assert "top-k depth" in retrieval_observation_entry["impact"]
    assert "jurisdiction/freshness" in retrieval_observation_entry["impact"]
    assert "cheap-first routing decisions" in retrieval_observation_entry["impact"]
    assert "answer-release actions" in retrieval_observation_entry["impact"]
    assert "typed maintenance API helpers" in retrieval_observation_entry["impact"]
    assert "maintenance UI review" in retrieval_observation_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in retrieval_observation_entry["impact"]
    assert "gateway calls" in retrieval_observation_entry["impact"]
    assert "network calls" in retrieval_observation_entry["impact"]
    assert "dataset downloads" in retrieval_observation_entry["impact"]
    assert "source-id echoing" in retrieval_observation_entry["impact"]
    assert "raw query" in retrieval_observation_entry["impact"]
    assert "raw retrieved context" in retrieval_observation_entry["impact"]
    assert "raw legal text" in retrieval_observation_entry["impact"]
    assert "prompts" in retrieval_observation_entry["impact"]
    assert "model outputs" in retrieval_observation_entry["impact"]
    assert "credentials" in retrieval_observation_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_retrieval_observation_gate.py "
        "tests/test_legal_rag_selected_source_validation.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q && "
        "cd ../frontend && npm run typecheck && npm run ui:regression"
        in ledger["validation_commands"]
    )
    answer_release_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-answer-release-readiness-gate"
    )
    assert "app/backend/services/legal_rag_answer_release_readiness_gate.py" in answer_release_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_answer_release_readiness_gate.py" in answer_release_entry["evidence_paths"]
    assert "app/backend/services/legal_rag_retrieval_observation_gate.py" in answer_release_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in answer_release_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in answer_release_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in answer_release_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_ANSWER_RELEASE_READINESS_GATE.md" in answer_release_entry["evidence_paths"]
    assert "legal-rag-answer-release-readiness-gate" in answer_release_entry["release_gate_links"]
    assert "legal-rag-retrieval-observation-gate" in answer_release_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in answer_release_entry["release_gate_links"]
    assert "legal-rag-authority-citation-gate" in answer_release_entry["release_gate_links"]
    assert "legal-rag-abstention-escalation-gate" in answer_release_entry["release_gate_links"]
    assert "model-escalation-policy" in answer_release_entry["release_gate_links"]
    assert "sanitized retrieval observation rows" in answer_release_entry["impact"]
    assert "ready/review/block answer-release rows" in answer_release_entry["impact"]
    assert "internal draft actions" in answer_release_entry["impact"]
    assert "citation packet requirements" in answer_release_entry["impact"]
    assert "lawyer-review requirements" in answer_release_entry["impact"]
    assert "client-delivery false flags" in answer_release_entry["impact"]
    assert "without NewAPI/Gemini/model calls" in answer_release_entry["impact"]
    assert "source-id echoing" in answer_release_entry["impact"]
    assert "raw query" in answer_release_entry["impact"]
    assert "user questions" in answer_release_entry["impact"]
    assert "raw retrieved context" in answer_release_entry["impact"]
    assert "raw legal text" in answer_release_entry["impact"]
    assert "legal advice claims" in answer_release_entry["impact"]
    assert "automatic client delivery" in answer_release_entry["impact"]
    assert (
        "python -m pytest tests/test_legal_rag_answer_release_readiness_gate.py "
        "tests/test_legal_rag_retrieval_observation_gate.py tests/test_release_readiness.py "
        "tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py "
        "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && "
        "npm run ui:regression"
        in ledger["validation_commands"]
    )
    retrieval_observation_ui_entry = next(
        entry
        for entry in ledger["completed_updates"]
        if entry["id"] == "legal-rag-retrieval-observation-ui-binding"
    )
    assert retrieval_observation_ui_entry["category"] == "frontend_ui"
    assert retrieval_observation_ui_entry["size"] == "medium"
    assert retrieval_observation_ui_entry["status"] == "shipped"
    assert "maintenance evidence page panel" in retrieval_observation_ui_entry["impact"]
    assert "typed POST helper" in retrieval_observation_ui_entry["impact"]
    assert "sanitized sample payload" in retrieval_observation_ui_entry["impact"]
    assert "status and release distributions" in retrieval_observation_ui_entry["impact"]
    assert "source-validation counts" in retrieval_observation_ui_entry["impact"]
    assert "cheap-first action review" in retrieval_observation_ui_entry["impact"]
    assert "privacy/claim boundaries" in retrieval_observation_ui_entry["impact"]
    assert "model/gateway/network calls" in retrieval_observation_ui_entry["impact"]
    assert "dataset downloads" in retrieval_observation_ui_entry["impact"]
    assert "source-id echoing" in retrieval_observation_ui_entry["impact"]
    assert "raw query" in retrieval_observation_ui_entry["impact"]
    assert "raw retrieved context" in retrieval_observation_ui_entry["impact"]
    assert "raw legal text" in retrieval_observation_ui_entry["impact"]
    assert "prompts" in retrieval_observation_ui_entry["impact"]
    assert "model outputs" in retrieval_observation_ui_entry["impact"]
    assert "gateway payloads" in retrieval_observation_ui_entry["impact"]
    assert "credentials" in retrieval_observation_ui_entry["impact"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in retrieval_observation_ui_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in retrieval_observation_ui_entry["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in retrieval_observation_ui_entry["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in retrieval_observation_ui_entry["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in retrieval_observation_ui_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_RETRIEVAL_OBSERVATION_GATE.md" in retrieval_observation_ui_entry["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in retrieval_observation_ui_entry["evidence_paths"]
    assert "legal-rag-retrieval-observation-gate" in retrieval_observation_ui_entry["release_gate_links"]
    assert "legal-rag-retrieval-diagnostics-gate" in retrieval_observation_ui_entry["release_gate_links"]
    assert "frontend-typecheck" in retrieval_observation_ui_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in retrieval_observation_ui_entry["release_gate_links"]
    rag_export_packet_entry = next(
        entry for entry in ledger["completed_updates"] if entry["id"] == "legal-rag-export-readiness-packet"
    )
    assert rag_export_packet_entry["category"] == "full_stack"
    assert rag_export_packet_entry["size"] == "medium"
    assert "selected-source binding" in rag_export_packet_entry["impact"]
    assert "case export readiness" in rag_export_packet_entry["impact"]
    assert "deep-review export route gate" in rag_export_packet_entry["impact"]
    assert "raw reports" in rag_export_packet_entry["impact"]
    assert "legal text" in rag_export_packet_entry["impact"]
    assert "document text" in rag_export_packet_entry["impact"]
    assert "user claims" in rag_export_packet_entry["impact"]
    assert "PII" in rag_export_packet_entry["impact"]
    assert "prompts" in rag_export_packet_entry["impact"]
    assert "model outputs" in rag_export_packet_entry["impact"]
    assert "credentials" in rag_export_packet_entry["impact"]
    assert "NewAPI" in rag_export_packet_entry["impact"]
    assert "Gemini" in rag_export_packet_entry["impact"]
    assert "gateways" in rag_export_packet_entry["impact"]
    assert "network" in rag_export_packet_entry["impact"]
    assert "app/backend/services/legal_rag_export_readiness_packet.py" in rag_export_packet_entry["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_export_readiness_packet.py" in rag_export_packet_entry["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in rag_export_packet_entry["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in rag_export_packet_entry["evidence_paths"]
    assert "docs/LEGAL_RAG_EXPORT_READINESS_PACKET.md" in rag_export_packet_entry["evidence_paths"]
    assert "legal-rag-export-readiness-packet" in rag_export_packet_entry["release_gate_links"]
    assert "legal-rag-selected-source-citation-validation" in rag_export_packet_entry["release_gate_links"]
    assert "deep-review-selected-source-binding" in rag_export_packet_entry["release_gate_links"]
    assert "case-export-readiness" in rag_export_packet_entry["release_gate_links"]
    assert "deep-review-export-readiness-route-gate" in rag_export_packet_entry["release_gate_links"]
    assert "frontend-ui-regression-gate" in rag_export_packet_entry["release_gate_links"]


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
