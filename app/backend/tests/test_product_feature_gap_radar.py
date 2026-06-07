import re

from services.product_feature_gap_radar import (
    ProductFeatureGapRadarService,
    priority_band,
    priority_score,
)


def test_product_feature_gap_radar_is_incomplete_and_product_wide():
    radar = ProductFeatureGapRadarService().build_radar()

    assert radar["status"] == "incomplete"
    assert radar["summary"]["ready_for_public_feature_claim"] is False
    assert radar["summary"]["feature_gap_count"] >= 11
    assert radar["summary"]["high_priority_count"] >= 8
    assert {
        "case_management",
        "document_generation",
        "contract_review",
        "evidence",
        "document_intake",
        "collaboration",
        "billing",
        "feedback",
        "model_ops",
        "legal_knowledge",
        "safety",
        "maintenance",
    }.issubset(set(radar["summary"]["modules"]))


def test_product_feature_gap_radar_prioritizes_by_score():
    radar = ProductFeatureGapRadarService().build_radar()
    gaps = radar["feature_gaps"]
    scores = [gap["priority_score"] for gap in gaps]

    assert scores == sorted(scores, reverse=True)
    assert gaps[0]["priority_band"] == "critical"
    assert "case-workbench" in radar["summary"]["top_gap_ids"]
    assert "safety-compliance" in radar["summary"]["top_gap_ids"]
    assert "legal-knowledge-rag" in radar["summary"]["top_gap_ids"]


def test_product_feature_gap_radar_has_evidence_paths_and_delivery_phases():
    radar = ProductFeatureGapRadarService().build_radar()

    assert all(gap["evidence_paths"] for gap in radar["feature_gaps"])
    assert all(
        path.startswith(("app/backend/", "app/frontend/", "docs/"))
        for gap in radar["feature_gaps"]
        for path in gap["evidence_paths"]
    )
    assert [phase["id"] for phase in radar["delivery_phases"]] == [
        "phase-1-core-legal-workflow",
        "phase-2-quality-and-ops",
        "phase-3-commercial-workspace",
    ]
    assert any("tests/test_product_feature_gap_radar.py" in command for command in radar["validation_commands"])


def test_frontend_productization_has_reviewable_evidence_and_next_deeper_work():
    radar = ProductFeatureGapRadarService().build_radar()
    gaps = {gap["id"]: gap for gap in radar["feature_gaps"]}

    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in gaps["case-workbench"]["evidence_paths"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in gaps["legal-knowledge-rag"]["evidence_paths"]
    assert "app/frontend/src/components/billing/BillingUsageBadge.tsx" in gaps["billing-entitlements"]["evidence_paths"]
    assert "privacy-safe material/evidence/fact/task edit event binding" in gaps["case-workbench"]["current_state"]
    assert "metadata-only risk/evidence refresh planning from runtime event deltas" in gaps["case-workbench"]["current_state"]
    assert "runtime risk-state badge projection" in gaps["case-workbench"]["current_state"]
    assert "task runtime notification policy summaries" in gaps["case-workbench"]["current_state"]
    assert "localStorage summary cache" in gaps["legal-knowledge-rag"]["current_state"]
    assert "selected-source request metadata propagation" in gaps["legal-knowledge-rag"]["current_state"]
    assert "metadata-level selected-source citation validation" in gaps["legal-knowledge-rag"]["current_state"]
    assert "report preflight" in gaps["billing-entitlements"]["current_state"]
    assert "generated_documents CRUD quota guard" in gaps["billing-entitlements"]["current_state"]
    assert "case generation quota guard" in gaps["billing-entitlements"]["current_state"]
    assert "deep-review first-principles document-generation quota guard" in gaps["billing-entitlements"]["current_state"]
    assert "evidence-catalog export preflight metadata" in gaps["document-generation"]["current_state"]
    assert "metadata-only case download gates" in gaps["document-generation"]["current_state"]
    assert "quota delivery decisions" in gaps["document-generation"]["current_state"]
    assert "metadata-only evidence bundle integrity checker" in gaps["evidence-management"]["current_state"]
    assert "evidence-catalog export preflight" in gaps["evidence-management"]["current_state"]
    assert "case download readiness gating" in gaps["evidence-management"]["current_state"]
    assert "uploaded deep-review status binding" in gaps["ocr-import"]["current_state"]
    assert "upload/progress UI OCR readiness panels" in gaps["ocr-import"]["current_state"]
    assert "safe OCR failure-code persistence" in gaps["ocr-import"]["current_state"]
    assert "first runtime cases API access-control gate" in gaps["permissions-team"]["current_state"]
    assert "durable matter memberships" in gaps["permissions-team"]["current_state"]
    assert "deterministic repeated issue clustering" in gaps["feedback-loop"]["current_state"]
    assert "adoption research bridge" in gaps["feedback-loop"]["current_state"]
    assert "reusable settings/report capture-plan previews" in gaps["feedback-loop"]["current_state"]
    assert "admin feedback lifecycle summaries" in gaps["feedback-loop"]["current_state"]
    assert "deep-review selected-source report binding" in gaps["legal-knowledge-rag"]["current_state"]
    assert "privacy retention rules" in gaps["safety-compliance"]["current_state"]
    assert "local-only payment/invoice/plan-change reconciliation policy evidence" in gaps["billing-entitlements"]["current_state"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_generated_documents_quota.py" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_case_generation_quota.py" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_case_evidence_catalog_export_preflight.py" in gaps["document-generation"]["evidence_paths"]
    assert "docs/CASE_EXPORT_READINESS_DOWNLOAD_GATE.md" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_deep_review_document_quota.py" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_case_export_readiness.py" in gaps["document-generation"]["evidence_paths"]
    assert "app/backend/tests/test_deep_review_ocr_readiness_runtime.py" in gaps["ocr-import"]["evidence_paths"]
    assert "app/frontend/src/pages/UploadPage.tsx" in gaps["ocr-import"]["evidence_paths"]
    assert "app/frontend/src/pages/ReviewProgressPage.tsx" in gaps["ocr-import"]["evidence_paths"]
    assert "app/backend/services/case_access_control.py" in gaps["permissions-team"]["evidence_paths"]
    assert "app/backend/routers/cases.py" in gaps["permissions-team"]["evidence_paths"]
    assert "app/backend/tests/test_case_permission_runtime_router.py" in gaps["permissions-team"]["evidence_paths"]
    assert "docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md" in gaps["permissions-team"]["evidence_paths"]
    assert any("approval workflow persistence" in action for action in gaps["permissions-team"]["next_actions"])
    assert "app/backend/tests/test_evidence_bundle_integrity.py" in gaps["evidence-management"]["evidence_paths"]
    assert "app/backend/services/case_evidence_catalog_export_preflight.py" in gaps["evidence-management"]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in gaps["evidence-management"]["evidence_paths"]
    assert "Extend evidence-catalog readiness from markdown download gating into final attachment package release." in gaps["evidence-management"]["next_actions"]
    assert "app/backend/tests/test_feedback_issue_cluster.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/services/feedback_capture_plan.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/routers/admin_ops.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/tests/test_admin_feedback_capture_summary.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/tests/test_feedback_capture_plan.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/frontend/src/components/feedback/FeedbackCapturePanel.tsx" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/frontend/src/lib/feedbackApi.ts" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/frontend/src/pages/AdminPage.tsx" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/frontend/src/pages/DeepReportPage.tsx" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/frontend/src/pages/SettingsPage.tsx" in gaps["feedback-loop"]["evidence_paths"]
    assert "docs/FEEDBACK_CAPTURE_PLAN.md" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/services/legal_rag_request_metadata.py" in gaps["legal-knowledge-rag"]["evidence_paths"]
    assert "app/backend/services/legal_rag_selected_source_validation.py" in gaps["legal-knowledge-rag"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_legal_rag_selected_source_validation_route.py" in gaps["legal-knowledge-rag"]["evidence_paths"]
    assert "app/backend/tests/test_deep_review_selected_source_binding.py" in gaps["legal-knowledge-rag"]["evidence_paths"]
    assert "app/backend/services/billing_payment_reconciliation.py" in gaps["billing-entitlements"]["evidence_paths"]
    assert "LegalBench/LexGLUE/LegalBench-RAG/LexEval/CaseGen/COLIEE research registry" in gaps["model-cost-ops"][
        "current_state"
    ]
    assert "task-level model selector audits" in gaps["model-cost-ops"]["current_state"]
    assert "deterministic selector replay evidence" in gaps["model-cost-ops"]["current_state"]
    assert "metadata-only cheap-first calibration" in gaps["model-cost-ops"]["current_state"]
    assert "sanitized ModelOps calibration review form" in gaps["model-cost-ops"]["current_state"]
    assert "public benchmark research mappings" in gaps["model-cost-ops"]["current_state"]
    assert "privacy-safe route telemetry repository aggregates" in gaps["model-cost-ops"]["current_state"]
    assert "persisted route telemetry operations summary checks" in gaps["model-cost-ops"]["current_state"]
    assert "route telemetry triage actions" in gaps["model-cost-ops"]["current_state"]
    assert "operator-reviewed route telemetry remediation plans" in gaps["model-cost-ops"]["current_state"]
    assert "maintenance UI for the metadata-only registry" in gaps["model-cost-ops"]["current_state"]
    assert "public adoption/research bridge" in gaps["model-cost-ops"]["current_state"]
    assert "metadata-only benchmark coverage matrix" in gaps["contract-review"]["current_state"]
    assert "broader real-world document coverage" in gaps["contract-review"]["current_state"]
    assert "app/backend/services/legal_document_benchmark_coverage.py" in gaps["contract-review"]["evidence_paths"]
    assert "app/backend/tests/test_legal_document_benchmark_coverage.py" in gaps["contract-review"]["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_BENCHMARK_COVERAGE.md" in gaps["contract-review"]["evidence_paths"]
    assert "app/backend/services/legal_adoption_research_bridge.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/tests/test_legal_adoption_research_bridge.py" in gaps["feedback-loop"]["evidence_paths"]
    assert "app/backend/services/legal_benchmark_research_registry.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/legal_adoption_research_bridge.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/gemini_newapi_model_selector.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/gemini_newapi_selector_replay.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/route_telemetry_ops_summary.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/route_telemetry_triage_queue.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/route_telemetry_remediation_plan.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_selector_replay.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_cheap_first_calibration.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_repository.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_ops_summary.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_triage_queue.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/tests/test_route_telemetry_remediation_plan.py" in gaps["model-cost-ops"]["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md" in gaps["model-cost-ops"]["evidence_paths"]
    assert "docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md" in gaps["model-cost-ops"]["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_OPS_SUMMARY.md" in gaps["model-cost-ops"]["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md" in gaps["model-cost-ops"]["evidence_paths"]
    assert "docs/ROUTE_TELEMETRY_REMEDIATION_PLAN.md" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in gaps["model-cost-ops"]["evidence_paths"]
    assert "app/backend/services/continuous_session_evidence.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/continuous_session_timeline.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/continuous_session_run_monitor.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_session_run_monitor.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "docs/CONTINUOUS_SESSION_RUN_MONITOR.md" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/continuous_session_review_packet.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/git_history_evidence.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/validation_event_evidence.py" in gaps["continuous-maintenance-evidence"]["evidence_paths"]
    assert "app/backend/services/case_workbench_risk_refresh_plan.py" in gaps["case-workbench"]["evidence_paths"]
    assert "app/backend/tests/test_case_workbench_risk_refresh_plan.py" in gaps["case-workbench"]["evidence_paths"]
    assert "docs/CASE_WORKBENCH_RISK_REFRESH_PLAN.md" in gaps["case-workbench"]["evidence_paths"]
    assert "metadata-only continuous session timeline" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "active-run monitor" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "next-checkpoint" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "continuous session review packet" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "stable packet hash" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "git history cadence evidence" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "validation event evidence normalizer" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert "max-gap, commit-window, credential-scan" in gaps["continuous-maintenance-evidence"]["current_state"]
    assert any("risk refresh plan" in action for action in gaps["case-workbench"]["next_actions"])
    assert any("projected badges" in action for action in gaps["case-workbench"]["next_actions"])
    assert any("live deep-review persistence" in action for action in gaps["legal-knowledge-rag"]["next_actions"])
    assert any("account plan review" in action for action in gaps["billing-entitlements"]["next_actions"])
    assert any("webhook signature verification" in action for action in gaps["billing-entitlements"]["next_actions"])
    assert any("model selector audits" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("Replay selector scenarios" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("public benchmark research mappings" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("operations summary" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("triage actions" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("remediation-plan env suggestions" in action for action in gaps["model-cost-ops"]["next_actions"])
    assert any("maintenance page" in action for action in gaps["continuous-maintenance-evidence"]["next_actions"])
    assert any("active-run monitor" in action for action in gaps["continuous-maintenance-evidence"]["next_actions"])
    assert any("support-facing index" in action for action in gaps["continuous-maintenance-evidence"]["next_actions"])
    assert any("validation event normalizer" in action for action in gaps["continuous-maintenance-evidence"]["next_actions"])
    assert any("benchmark coverage matrix" in action for action in gaps["contract-review"]["next_actions"])
    assert any("OCR retry execution records" in action for action in gaps["ocr-import"]["next_actions"])


def test_product_feature_gap_radar_has_no_secret_material():
    radar = ProductFeatureGapRadarService().build_radar()

    assert "privacy" in radar["privacy_note"].lower()
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", str(radar))
    assert "password" in radar["privacy_note"].lower()


def test_priority_score_and_band_are_bounded():
    assert priority_score(10, 10, 0, 10) == 100
    assert priority_score(1, 1, 10, 1) == 0
    assert priority_band(90) == "critical"
    assert priority_band(75) == "high"
    assert priority_band(55) == "medium"
    assert priority_band(54) == "low"


def test_product_feature_gap_radar_route_returns_gaps():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/product-feature-gaps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "incomplete"
    assert payload["data"]["summary"]["ready_for_public_feature_claim"] is False
