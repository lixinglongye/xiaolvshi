from services.maintenance_evidence import MaintenanceEvidenceService, REPOSITORY_URL


def test_maintenance_profile_links_reviewable_evidence():
    profile = MaintenanceEvidenceService().build_profile("en")
    evidence_paths = [path for signal in profile["signals"] for path in signal["evidence_paths"]]

    assert profile["project"]["repository_url"] == REPOSITORY_URL
    assert profile["maintainer_role"] == "primary_project_maintainer"
    assert profile["evidence_score"] >= 80
    assert profile["signals"]
    assert all(signal["evidence_paths"] for signal in profile["signals"])
    assert "release_decision" in " ".join(evidence_paths)
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in evidence_paths
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in evidence_paths
    assert "app/backend/routers/billing_usage.py" in evidence_paths
    assert "Billing report preflight route" in profile["release_management"]["release_readiness_controls"]
    assert "Case edit runtime event binding" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG research context cache" in profile["release_management"]["release_readiness_controls"]
    assert "Document generation quota consumption attempt" in profile["release_management"]["release_readiness_controls"]
    assert "Generated documents CRUD quota guard" in profile["release_management"]["release_readiness_controls"]
    assert "Case generation quota guard" in profile["release_management"]["release_readiness_controls"]
    assert "Deep-review document generation quota guard" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG selected-source request metadata" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG selected-source citation validation" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG selected-source validation maintenance route" in profile["release_management"]["release_readiness_controls"]
    assert "Deep-review selected-source binding" in profile["release_management"]["release_readiness_controls"]
    assert "Quota delivery decision" in profile["release_management"]["release_readiness_controls"]
    assert "Feedback issue cluster" in profile["release_management"]["release_readiness_controls"]
    assert "Evidence bundle integrity" in profile["release_management"]["release_readiness_controls"]
    assert "Privacy retention rules" in profile["release_management"]["release_readiness_controls"]
    assert "Release claim compliance" in profile["release_management"]["release_readiness_controls"]
    assert "Case export readiness" in profile["release_management"]["release_readiness_controls"]
    assert "Admin audit policy" in profile["release_management"]["release_readiness_controls"]
    assert "Billing payment reconciliation policy" in profile["release_management"]["release_readiness_controls"]
    assert "Case task runtime notification summary" in profile["release_management"]["release_readiness_controls"]
    assert "Legal document benchmark suite" in profile["release_management"]["release_readiness_controls"]
    assert "Legal document benchmark gap fixtures" in profile["release_management"]["release_readiness_controls"]
    assert "Legal document benchmark coverage matrix" in profile["release_management"]["release_readiness_controls"]
    assert "Legal document coverage claim policy" in profile["release_management"]["release_readiness_controls"]
    assert "User need public benchmark mapping" in profile["release_management"]["release_readiness_controls"]
    assert "User need cheap-first calibration mapping" in profile["release_management"]["release_readiness_controls"]
    assert "Legal benchmark research registry UI" in profile["release_management"]["release_readiness_controls"]
    assert "Legal adoption research bridge" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI model selector" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI selector replay" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI cheap-first calibration" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini model variant matrix" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry repository" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry operations summary" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry triage queue" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry remediation plan" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous session evidence validator" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous ledger low-resource fixture evidence" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous session timeline" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous session run monitor" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous run monitor fixture evidence" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous session review packet" in profile["release_management"]["release_readiness_controls"]
    assert "Continuous session low-resource fixture review" in profile["release_management"]["release_readiness_controls"]
    assert "Git history cadence evidence" in profile["release_management"]["release_readiness_controls"]
    assert "Validation event evidence normalizer" in profile["release_management"]["release_readiness_controls"]
    assert "app/backend/routers/generated_documents.py" in evidence_paths
    assert "app/backend/routers/case_intelligence.py" in evidence_paths
    assert "app/backend/services/deep_review_document_quota.py" in evidence_paths
    assert "app/backend/services/legal_rag_request_metadata.py" in evidence_paths
    assert "app/backend/services/legal_rag_selected_source_validation.py" in evidence_paths
    assert "app/backend/services/deep_review_selected_source_binding.py" in evidence_paths
    assert "app/backend/services/evidence_bundle_integrity.py" in evidence_paths
    assert "app/backend/services/billing_payment_reconciliation.py" in evidence_paths
    assert "app/backend/services/quota_delivery_decision.py" in evidence_paths
    assert "app/backend/services/privacy_retention_rules.py" in evidence_paths
    assert "app/backend/services/release_claim_compliance.py" in evidence_paths
    assert "app/backend/services/admin_audit_policy.py" in evidence_paths
    assert "app/backend/services/legal_document_benchmark_suite.py" in evidence_paths
    assert "app/backend/services/legal_document_benchmark_coverage.py" in evidence_paths
    assert "app/backend/services/legal_document_coverage_claim_policy.py" in evidence_paths
    assert "app/backend/tests/test_legal_document_benchmark_coverage.py" in evidence_paths
    assert "app/backend/tests/test_legal_document_coverage_claim_policy.py" in evidence_paths
    assert "docs/LEGAL_DOCUMENT_BENCHMARK_COVERAGE.md" in evidence_paths
    assert "docs/LEGAL_DOCUMENT_COVERAGE_CLAIM_POLICY.md" in evidence_paths
    assert "app/backend/services/legal_benchmark_research_registry.py" in evidence_paths
    assert "app/backend/services/legal_adoption_research_bridge.py" in evidence_paths
    assert "app/backend/tests/test_legal_adoption_research_bridge.py" in evidence_paths
    assert "docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_model_selector.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_model_selector.py" in evidence_paths
    assert "app/backend/services/gemini_newapi_selector_replay.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_selector_replay.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_cheap_first_calibration.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md" in evidence_paths
    assert "app/backend/services/gemini_model_variant_matrix.py" in evidence_paths
    assert "app/backend/tests/test_gemini_model_variant_matrix.py" in evidence_paths
    assert "docs/GEMINI_MODEL_VARIANT_MATRIX.md" in evidence_paths
    model_signal = next(signal for signal in profile["signals"] if signal["id"] == "model-routing-cost-control")
    assert "public benchmark research mappings" in model_signal["description"]
    assert "Gemini variant matrix review" in model_signal["description"]
    assert "sanitized ModelOps calibration review" in model_signal["description"]
    assert "sanitized review-form upkeep" in model_signal["responsibility"]
    assert "Gemini variant matrix review" in model_signal["responsibility"]
    assert "public benchmark mapping review" in model_signal["responsibility"]
    assert "app/backend/services/route_telemetry_repository.py" in evidence_paths
    assert "app/backend/tests/test_route_telemetry_repository.py" in evidence_paths
    assert "app/backend/services/route_telemetry_ops_summary.py" in evidence_paths
    assert "app/backend/tests/test_route_telemetry_ops_summary.py" in evidence_paths
    assert "docs/ROUTE_TELEMETRY_OPS_SUMMARY.md" in evidence_paths
    assert "app/backend/services/route_telemetry_triage_queue.py" in evidence_paths
    assert "app/backend/tests/test_route_telemetry_triage_queue.py" in evidence_paths
    assert "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md" in evidence_paths
    assert "app/backend/services/route_telemetry_remediation_plan.py" in evidence_paths
    assert "app/backend/tests/test_route_telemetry_remediation_plan.py" in evidence_paths
    assert "docs/ROUTE_TELEMETRY_REMEDIATION_PLAN.md" in evidence_paths
    assert "app/backend/services/continuous_session_evidence.py" in evidence_paths
    assert "app/backend/tests/test_continuous_session_evidence.py" in evidence_paths
    assert "app/backend/services/continuous_session_timeline.py" in evidence_paths
    assert "app/backend/tests/test_continuous_session_timeline.py" in evidence_paths
    assert "app/backend/services/continuous_session_run_monitor.py" in evidence_paths
    assert "app/backend/tests/test_continuous_session_run_monitor.py" in evidence_paths
    assert "docs/CONTINUOUS_SESSION_RUN_MONITOR.md" in evidence_paths
    assert "app/backend/services/continuous_session_review_packet.py" in evidence_paths
    assert "app/backend/tests/test_continuous_session_review_packet.py" in evidence_paths
    assert "app/backend/services/legal_fixture_local_run_review.py" in evidence_paths
    assert "app/backend/services/git_history_evidence.py" in evidence_paths
    assert "app/backend/tests/test_git_history_evidence.py" in evidence_paths
    assert "app/backend/services/validation_event_evidence.py" in evidence_paths
    assert "app/backend/tests/test_validation_event_evidence.py" in evidence_paths
    assert "app/frontend/src/lib/maintenanceApi.ts" in evidence_paths
    assert "app/frontend/scripts/ui-regression.mjs" in evidence_paths
    assert any("real provider settlement" in guardrail for guardrail in profile["application_guardrails"])
    assert any("automatic deep-review report binding" in guardrail for guardrail in profile["application_guardrails"])
    assert any("does not prove completion" in guardrail for guardrail in profile["application_guardrails"])
    assert any("support claims must remain blocked" in guardrail for guardrail in profile["application_guardrails"])
    assert any("active-run gaps" in guardrail for guardrail in profile["application_guardrails"])
    assert any("archive-safe and non-mutating" in guardrail for guardrail in profile["application_guardrails"])
    assert any("not a substitute for real timestamped 24-hour evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("does not prove tests" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Validation event evidence accepts only sanitized" in guardrail for guardrail in profile["application_guardrails"])
    assert any("deep-review first-principles generation are quota guarded" in guardrail for guardrail in profile["application_guardrails"])
    assert any("legal document coverage claim policy" in guardrail for guardrail in profile["application_guardrails"])
    assert any("repository-backed synthetic fixture wording" in guardrail for guardrail in profile["application_guardrails"])
    assert any("public benchmark mapping reports sampler" in guardrail for guardrail in profile["application_guardrails"])
    assert any("cheap-first calibration mapping reports task IDs" in guardrail for guardrail in profile["application_guardrails"])


def test_form_answers_are_application_safe_and_bilingual():
    service = MaintenanceEvidenceService()

    english = service.build_form_answer("en")
    chinese = service.build_form_answer("zh")

    assert REPOSITORY_URL in english
    assert REPOSITORY_URL in chinese
    assert "third-party PR" not in english
    assert "大量外部 PR" not in chinese
    assert "sk-" not in english + chinese
    assert "维护者" in chinese


def test_unknown_language_falls_back_to_english():
    service = MaintenanceEvidenceService()

    assert service.build_profile("fr")["form_answer"] == service.build_form_answer("en")


def test_maintenance_evidence_route_returns_bilingual_form_answer():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/oss-evidence?language=zh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["project"]["repository_url"] == REPOSITORY_URL
    assert "维护者" in payload["data"]["form_answer"]
