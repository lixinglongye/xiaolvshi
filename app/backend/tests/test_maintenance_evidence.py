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
    assert "app/backend/services/case_access_control.py" in evidence_paths
    assert "app/backend/tests/test_case_permission_runtime_router.py" in evidence_paths
    assert "docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md" in evidence_paths
    assert "app/backend/services/case_workbench_risk_refresh_plan.py" in evidence_paths
    assert "app/backend/tests/test_case_workbench_risk_refresh_plan.py" in evidence_paths
    assert "docs/CASE_WORKBENCH_RISK_REFRESH_PLAN.md" in evidence_paths
    assert "app/backend/services/case_evidence_catalog_export_preflight.py" in evidence_paths
    assert "app/backend/tests/test_case_evidence_catalog_export_preflight.py" in evidence_paths
    assert "docs/CASE_EVIDENCE_CATALOG_EXPORT_PREFLIGHT.md" in evidence_paths
    assert "docs/CASE_EXPORT_READINESS_DOWNLOAD_GATE.md" in evidence_paths
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in evidence_paths
    assert "app/backend/routers/billing_usage.py" in evidence_paths
    assert "Billing report preflight route" in profile["release_management"]["release_readiness_controls"]
    assert "Case access control runtime gate" in profile["release_management"]["release_readiness_controls"]
    assert "Case workbench risk refresh plan" in profile["release_management"]["release_readiness_controls"]
    assert "Case edit runtime event binding" in profile["release_management"]["release_readiness_controls"]
    assert "Case export readiness download gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG research context cache" in profile["release_management"]["release_readiness_controls"]
    assert "Document generation quota consumption attempt" in profile["release_management"]["release_readiness_controls"]
    assert "Generated documents CRUD quota guard" in profile["release_management"]["release_readiness_controls"]
    assert "Case generation quota guard" in profile["release_management"]["release_readiness_controls"]
    assert "Case evidence catalog export preflight" in profile["release_management"]["release_readiness_controls"]
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
    assert "Legal document fact consistency benchmark" in profile["release_management"]["release_readiness_controls"]
    assert "Legal document coverage claim policy" in profile["release_management"]["release_readiness_controls"]
    assert "User need public benchmark mapping" in profile["release_management"]["release_readiness_controls"]
    assert "User need cheap-first calibration mapping" in profile["release_management"]["release_readiness_controls"]
    assert "Legal benchmark research registry UI" in profile["release_management"]["release_readiness_controls"]
    assert "Legal benchmark research refresh" in profile["release_management"]["release_readiness_controls"]
    assert "Model route legal benchmark risk queue" in profile["release_management"]["release_readiness_controls"]
    assert "Observed gateway model fit matrix" in profile["release_management"]["release_readiness_controls"]
    assert "User need implementation priority queue" in profile["release_management"]["release_readiness_controls"]
    assert "User need Gemini route coverage" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG authority citation gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG abstention escalation gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG retrieval diagnostics gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG index coverage gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding readiness gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding chunk policy gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding index dry-run gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding batch budget gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding batch approval packet" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding batch observation gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG embedding index commit review packet" in profile["release_management"]["release_readiness_controls"]
    assert "Legal RAG retrieval observation gate" in profile["release_management"]["release_readiness_controls"]
    assert "Legal adoption research bridge" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI model selector" in profile["release_management"]["release_readiness_controls"]
    assert "Model default ladder review boundaries" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI observed model extraction" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI model alias matrix" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI alias capability coverage" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini official preview alias review" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI selector replay" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini/NewAPI cheap-first calibration" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini model variant matrix" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps Gemini variant review form" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini model-list ingestion" in profile["release_management"]["release_readiness_controls"]
    assert "Gemini catalog source audit" in profile["release_management"]["release_readiness_controls"]
    assert "Model gateway connection profile" in profile["release_management"]["release_readiness_controls"]
    assert "Model operations readiness warning drilldown" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps load performance budget" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps performance observation review" in profile["release_management"]["release_readiness_controls"]
    assert "Cheap-first route quality budget" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first escalation budget" in profile["release_management"]["release_readiness_controls"]
    assert "Model failure upgrade budget" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry repository" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry catalog cost estimation" in profile["release_management"]["release_readiness_controls"]
    assert "Runtime route reason codes" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry operations summary" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry triage queue" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry reason-code hotspots" in profile["release_management"]["release_readiness_controls"]
    assert "Route telemetry remediation plan" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first release decision" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps default change queue" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary plan" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary observation review" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary promotion decision" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary approval packet" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary rollback drill" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps cheap-first canary change manifest" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps Gemini cheap-first coverage gate" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps Gemini cheap-first route preflight" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps AIHub endpoint route coverage gate" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps runtime explicit model fit gate" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps legal micro benchmark preflight" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps legal fixture cheap-first benchmark gate" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps legal fixture cheap-first default promotion packet" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps agentic grounded defaults" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps default template alignment audit" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps Gemini default change proposal review" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps Gemini default cost impact forecast" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps observed Gemini model intake queue" in profile["release_management"]["release_readiness_controls"]
    assert "ModelOps observed Gemini coverage gap queue" in profile["release_management"]["release_readiness_controls"]
    assert "Model catalog candidate patch plan" in profile["release_management"]["release_readiness_controls"]
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
    assert "app/backend/services/legal_benchmark_research_refresh.py" in evidence_paths
    assert "app/backend/tests/test_legal_benchmark_research_refresh.py" in evidence_paths
    assert "docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md" in evidence_paths
    assert "app/backend/services/legal_adoption_research_bridge.py" in evidence_paths
    assert "app/backend/tests/test_legal_adoption_research_bridge.py" in evidence_paths
    assert "docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_model_selector.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_model_selector.py" in evidence_paths
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in evidence_paths
    assert "app/backend/services/gemini_newapi_model_alias_matrix.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_model_alias_matrix.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_MODEL_ALIAS_MATRIX.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_alias_capability_coverage.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_alias_capability_coverage.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_ALIAS_CAPABILITY_COVERAGE.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_selector_replay.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_selector_replay.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md" in evidence_paths
    assert "app/backend/services/gemini_newapi_cheap_first_calibration.py" in evidence_paths
    assert "app/backend/tests/test_gemini_newapi_cheap_first_calibration.py" in evidence_paths
    assert "docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md" in evidence_paths
    assert "app/backend/services/gemini_model_variant_matrix.py" in evidence_paths
    assert "app/backend/tests/test_gemini_model_variant_matrix.py" in evidence_paths
    assert "docs/GEMINI_MODEL_VARIANT_MATRIX.md" in evidence_paths
    assert "app/backend/services/model_ops_observed_gemini_coverage_gap_queue.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_observed_gemini_coverage_gap_queue.py" in evidence_paths
    assert "docs/MODELOPS_OBSERVED_GEMINI_COVERAGE_GAP_QUEUE.md" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_escalation_budget.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_escalation_budget.py" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_ESCALATION_BUDGET.md" in evidence_paths
    assert "app/backend/services/model_failure_upgrade_budget.py" in evidence_paths
    assert "app/backend/tests/test_model_failure_upgrade_budget.py" in evidence_paths
    assert "docs/MODEL_FAILURE_UPGRADE_BUDGET.md" in evidence_paths
    assert "app/backend/services/model_route_legal_benchmark_risk_queue.py" in evidence_paths
    assert "app/backend/tests/test_model_route_legal_benchmark_risk_queue.py" in evidence_paths
    assert "docs/MODEL_ROUTE_LEGAL_BENCHMARK_RISK_QUEUE.md" in evidence_paths
    assert "app/backend/services/legal_rag_authority_citation_gate.py" in evidence_paths
    assert "app/backend/tests/test_legal_rag_authority_citation_gate.py" in evidence_paths
    assert "docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md" in evidence_paths
    assert "app/backend/services/legal_rag_retrieval_diagnostics_gate.py" in evidence_paths
    assert "app/backend/tests/test_legal_rag_retrieval_diagnostics_gate.py" in evidence_paths
    assert "docs/LEGAL_RAG_RETRIEVAL_DIAGNOSTICS_GATE.md" in evidence_paths
    assert "app/backend/services/legal_rag_retrieval_observation_gate.py" in evidence_paths
    assert "app/backend/tests/test_legal_rag_retrieval_observation_gate.py" in evidence_paths
    assert "docs/LEGAL_RAG_RETRIEVAL_OBSERVATION_GATE.md" in evidence_paths
    assert "app/backend/services/modelops_gemini_cheap_first_coverage_gate.py" in evidence_paths
    assert "app/backend/tests/test_modelops_gemini_cheap_first_coverage_gate.py" in evidence_paths
    assert "docs/MODELOPS_GEMINI_CHEAP_FIRST_COVERAGE_GATE.md" in evidence_paths
    assert "app/backend/services/model_gateway_connection_profile.py" in evidence_paths
    assert "docs/MODEL_GATEWAY_CONNECTION_PROFILE.md" in evidence_paths
    assert "app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py" in evidence_paths
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in evidence_paths
    assert "app/backend/services/model_ops_runtime_explicit_model_fit_gate.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_runtime_explicit_model_fit_gate.py" in evidence_paths
    assert "docs/MODELOPS_RUNTIME_EXPLICIT_MODEL_FIT_GATE.md" in evidence_paths
    assert "app/backend/services/modelops_legal_micro_benchmark_preflight.py" in evidence_paths
    assert "app/backend/tests/test_modelops_legal_micro_benchmark_preflight.py" in evidence_paths
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in evidence_paths
    assert "app/backend/tests/test_model_catalog_candidate_patch_plan.py" in evidence_paths
    assert "docs/MODEL_CATALOG_CANDIDATE_PATCH_PLAN.md" in evidence_paths
    assert "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py" in evidence_paths
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in evidence_paths
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in evidence_paths
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in evidence_paths
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in evidence_paths
    assert "app/backend/services/modelops_legal_fixture_default_promotion_packet.py" in evidence_paths
    assert "app/backend/tests/test_modelops_legal_fixture_default_promotion_packet.py" in evidence_paths
    assert "app/backend/routers/maintenance.py" in evidence_paths
    assert "app/frontend/src/lib/maintenanceApi.ts" in evidence_paths
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in evidence_paths
    assert "app/frontend/scripts/ui-regression.mjs" in evidence_paths
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in evidence_paths
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in evidence_paths
    assert "app/backend/.env.example" in evidence_paths
    assert "README.md" in evidence_paths
    assert "app/backend/services/release_readiness.py" in evidence_paths
    assert "app/backend/services/continuous_update_ledger.py" in evidence_paths
    assert "app/backend/services/maintenance_evidence.py" in evidence_paths
    assert "app/backend/tests/test_release_readiness.py" in evidence_paths
    assert "app/backend/tests/test_continuous_update_ledger.py" in evidence_paths
    assert "app/backend/tests/test_maintenance_evidence.py" in evidence_paths
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in evidence_paths
    model_signal = next(signal for signal in profile["signals"] if signal["id"] == "model-routing-cost-control")
    quality_signal = next(signal for signal in profile["signals"] if signal["id"] == "deep-review-quality-gates")
    priority_signal = next(
        signal for signal in profile["signals"] if signal["id"] == "user-need-implementation-priority-queue"
    )
    route_coverage_signal = next(
        signal for signal in profile["signals"] if signal["id"] == "user-need-gemini-route-coverage"
    )
    assert "high-priority user needs" in priority_signal["description"]
    assert "legal benchmark coverage gaps" in priority_signal["description"]
    assert "cheap-first calibration/model routing risk" in priority_signal["description"]
    assert "product execution actions" in priority_signal["description"]
    assert "priority queue" in priority_signal["responsibility"]
    assert "cheap-first calibration tasks" in route_coverage_signal["description"]
    assert "Gemini route preflight rows" in route_coverage_signal["description"]
    assert "Flash-Lite protection" in route_coverage_signal["description"]
    assert "premium exceptions" in route_coverage_signal["description"]
    assert "public benchmark/license gaps" in route_coverage_signal["description"]
    assert "unmapped route blockers" in route_coverage_signal["description"]
    assert "user-need route coverage" in route_coverage_signal["responsibility"]
    assert "runtime route reason-code evidence" in model_signal["description"]
    assert "safe gateway connection profile evidence" in model_signal["description"]
    assert "observed gateway model fit matrix evidence" in model_signal["description"]
    assert "runtime explicit model fit gate evidence" in model_signal["description"]
    assert "gateway connection profile review" in model_signal["responsibility"]
    assert "observed gateway model fit matrix review" in model_signal["responsibility"]
    assert "runtime explicit model fit gate review" in model_signal["responsibility"]
    assert "ModelOps AIHub endpoint route coverage gate review" in model_signal["description"]
    assert "ModelOps runtime explicit model fit gate review" in model_signal["description"]
    assert "runtime explicit model fit review states" in model_signal["description"]
    assert "AIHub endpoint runtime-router and route telemetry coverage evidence" in model_signal["description"]
    assert "route telemetry reason-code hotspot evidence" in model_signal["description"]
    assert "runtime route reason-code review" in model_signal["responsibility"]
    assert "ModelOps AIHub endpoint route coverage gate review" in model_signal["responsibility"]
    assert "ModelOps runtime explicit model fit gate review" in model_signal["responsibility"]
    assert "runtime explicit model fit review" in model_signal["responsibility"]
    assert "AIHub endpoint runtime-router coverage review" in model_signal["responsibility"]
    assert "AIHub route telemetry coverage review" in model_signal["responsibility"]
    assert "route telemetry reason-code hotspot review" in model_signal["responsibility"]
    assert "app/backend/services/model_runtime_router.py" in model_signal["evidence_paths"]
    assert "app/backend/services/model_ops_runtime_explicit_model_fit_gate.py" in model_signal["evidence_paths"]
    assert "app/backend/tests/test_model_ops_runtime_explicit_model_fit_gate.py" in model_signal["evidence_paths"]
    assert "docs/MODELOPS_RUNTIME_EXPLICIT_MODEL_FIT_GATE.md" in model_signal["evidence_paths"]
    assert "app/backend/services/modelops_observed_gateway_model_fit_matrix.py" in model_signal["evidence_paths"]
    assert "app/backend/tests/test_modelops_observed_gateway_model_fit_matrix.py" in model_signal["evidence_paths"]
    assert "docs/MODELOPS_OBSERVED_GATEWAY_MODEL_FIT_MATRIX.md" in model_signal["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in model_signal["evidence_paths"]
    assert "app/backend/services/route_telemetry_persistence_plan.py" in model_signal["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in priority_signal["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in priority_signal["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in priority_signal["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in priority_signal["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in priority_signal["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in priority_signal["evidence_paths"]
    assert "app/backend/services/user_need_gemini_route_coverage.py" in route_coverage_signal["evidence_paths"]
    assert "app/backend/tests/test_user_need_gemini_route_coverage.py" in route_coverage_signal["evidence_paths"]
    assert "app/backend/services/user_need_benchmark_coverage.py" in route_coverage_signal["evidence_paths"]
    assert "app/backend/services/model_ops_gemini_cheap_first_route_preflight.py" in route_coverage_signal["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in route_coverage_signal["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in route_coverage_signal["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in route_coverage_signal["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in route_coverage_signal["evidence_paths"]
    assert "docs/USER_NEED_GEMINI_ROUTE_COVERAGE.md" in route_coverage_signal["evidence_paths"]
    assert "docs/USER_NEED_BENCHMARK_COVERAGE.md" in route_coverage_signal["evidence_paths"]
    assert "docs/USER_NEEDS_RADAR.md" in route_coverage_signal["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in priority_signal["evidence_paths"]
    assert "docs/USER_NEED_BENCHMARK_COVERAGE.md" in priority_signal["evidence_paths"]
    assert "docs/USER_NEEDS_RADAR.md" in priority_signal["evidence_paths"]
    assert "metadata-only legal benchmark research refresh evidence" in quality_signal["description"]
    assert "metadata-only legal document fact consistency benchmark evidence" in quality_signal["description"]
    assert "fact consistency" in quality_signal["description"]
    assert "metadata-only authority/citation gate evidence" in quality_signal["description"]
    assert "metadata-only retrieval diagnostics gate evidence" in quality_signal["description"]
    assert "metadata-only retrieval observation gate evidence" in quality_signal["description"]
    assert "benchmark research registry, refresh, and UI review" in quality_signal["responsibility"]
    assert "fact-consistency benchmark review" in quality_signal["responsibility"]
    assert "authority/citation gate review" in quality_signal["responsibility"]
    assert "retrieval diagnostics gate review" in quality_signal["responsibility"]
    assert "retrieval observation gate review" in quality_signal["responsibility"]
    assert "public benchmark research mappings" in model_signal["description"]
    assert "Gemini variant matrix review" in model_signal["description"]
    assert "Gemini/NewAPI observed model extraction evidence" in model_signal["description"]
    assert "Gemini/NewAPI observed model extraction review" in model_signal["responsibility"]
    assert "Gemini/NewAPI alias capability coverage evidence" in model_signal["description"]
    assert "Gemini/NewAPI alias capability coverage review" in model_signal["responsibility"]
    assert "default ladder review-boundary evidence" in model_signal["description"]
    assert "model default ladder review-boundary review" in model_signal["responsibility"]
    assert "Gemini official preview alias review evidence" in model_signal["description"]
    assert "Gemini official preview alias review" in model_signal["responsibility"]
    assert "sanitized ModelOps Gemini variant review" in model_signal["description"]
    assert "sanitized gateway model-list ingestion" in model_signal["description"]
    assert "Gemini catalog source audit" in model_signal["description"]
    assert "model catalog candidate patch planning" in model_signal["description"]
    assert "ModelOps cheap-first release decision review" in model_signal["description"]
    assert "ModelOps default change queue review" in model_signal["description"]
    assert "ModelOps cheap-first canary plan review" in model_signal["description"]
    assert "ModelOps cheap-first canary observation review" in model_signal["description"]
    assert "ModelOps cheap-first canary promotion decision review" in model_signal["description"]
    assert "ModelOps cheap-first canary approval packet review" in model_signal["description"]
    assert "ModelOps cheap-first canary rollback drill review" in model_signal["description"]
    assert "ModelOps cheap-first canary change manifest review" in model_signal["description"]
    assert "ModelOps Gemini cheap-first coverage gate review" in model_signal["description"]
    assert "ModelOps Gemini cheap-first route preflight review" in model_signal["description"]
    assert "ModelOps legal micro benchmark preflight review" in model_signal["description"]
    assert "ModelOps legal fixture cheap-first benchmark gate review" in model_signal["description"]
    assert "ModelOps legal fixture cheap-first default promotion packet review" in model_signal["description"]
    assert "ModelOps agentic/grounded default routing evidence" in model_signal["description"]
    assert "ModelOps default template alignment audit evidence" in model_signal["description"]
    assert "ModelOps Gemini default change proposal review evidence" in model_signal["description"]
    assert "ModelOps Gemini default cost impact forecast evidence" in model_signal["description"]
    assert "ModelOps observed Gemini model intake queue evidence" in model_signal["description"]
    assert "ModelOps observed Gemini coverage gap evidence" in model_signal["description"]
    assert "ModelOps readiness warning drilldown evidence" in model_signal["description"]
    assert "ModelOps load performance budgets" in model_signal["description"]
    assert "sanitized ModelOps performance observation review" in model_signal["description"]
    assert "cheap-first route quality budgets" in model_signal["description"]
    assert "model failure upgrade budget review" in model_signal["description"]
    assert "legal benchmark route risk queue review" in model_signal["description"]
    assert "sanitized ModelOps calibration review" in model_signal["description"]
    assert "sanitized review-form upkeep" in model_signal["responsibility"]
    assert "catalog source-audit review" in model_signal["responsibility"]
    assert "model catalog candidate patch-plan review" in model_signal["responsibility"]
    assert "observed-model form upkeep" in model_signal["responsibility"]
    assert "public benchmark mapping review" in model_signal["responsibility"]
    assert "ModelOps performance-observation review" in model_signal["responsibility"]
    assert "ModelOps cheap-first release decision review" in model_signal["responsibility"]
    assert "ModelOps default change queue review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary plan review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary observation review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary promotion decision review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary approval packet review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary rollback drill review" in model_signal["responsibility"]
    assert "ModelOps cheap-first canary change manifest review" in model_signal["responsibility"]
    assert "ModelOps Gemini cheap-first coverage gate review" in model_signal["responsibility"]
    assert "ModelOps Gemini cheap-first route preflight review" in model_signal["responsibility"]
    assert "ModelOps AIHub endpoint route coverage gate review" in model_signal["responsibility"]
    assert "ModelOps legal micro benchmark preflight review" in model_signal["responsibility"]
    assert "ModelOps legal fixture cheap-first benchmark gate review" in model_signal["responsibility"]
    assert "ModelOps legal fixture cheap-first default promotion packet review" in model_signal["responsibility"]
    assert "ModelOps agentic/grounded defaults review" in model_signal["responsibility"]
    assert "ModelOps default template alignment audit review" in model_signal["responsibility"]
    assert "ModelOps Gemini default change proposal review" in model_signal["responsibility"]
    assert "ModelOps Gemini default cost impact forecast review" in model_signal["responsibility"]
    assert "ModelOps observed Gemini model intake queue review" in model_signal["responsibility"]
    assert "ModelOps observed Gemini coverage gap review" in model_signal["responsibility"]
    assert "ModelOps readiness warning triage review" in model_signal["responsibility"]
    assert "route quality-budget review" in model_signal["responsibility"]
    assert "model failure-upgrade budget review" in model_signal["responsibility"]
    assert "route telemetry catalog cost-estimation review" in model_signal["responsibility"]
    assert "legal benchmark route risk queue review" in model_signal["responsibility"]
    assert "catalog-priced route telemetry cost estimation" in model_signal["description"]
    assert "app/backend/services/model_route_quality_budget.py" in evidence_paths
    assert "app/backend/services/model_catalog_source_audit.py" in evidence_paths
    assert "app/backend/services/model_catalog_candidate_patch_plan.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in evidence_paths
    assert "app/backend/services/model_ops_default_change_queue.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_plan.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_observation.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_promotion_decision.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_approval_packet.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_rollback_drill.py" in evidence_paths
    assert "app/backend/services/model_ops_cheap_first_canary_change_manifest.py" in evidence_paths
    assert "app/backend/services/model_ops_gemini_cheap_first_route_preflight.py" in evidence_paths
    assert "app/backend/services/model_ops_aihub_endpoint_route_coverage_gate.py" in evidence_paths
    assert "app/backend/tests/test_model_catalog_source_audit.py" in evidence_paths
    assert "app/backend/tests/test_model_catalog_candidate_patch_plan.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_release_decision.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_default_change_queue.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_plan.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_observation.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_promotion_decision.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_approval_packet.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_rollback_drill.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_cheap_first_canary_change_manifest.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_gemini_cheap_first_route_preflight.py" in evidence_paths
    assert "app/backend/tests/test_model_ops_aihub_endpoint_route_coverage_gate.py" in evidence_paths
    assert "docs/MODEL_CATALOG_SOURCE_AUDIT.md" in evidence_paths
    assert "docs/MODEL_CATALOG_CANDIDATE_PATCH_PLAN.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_RELEASE_DECISION.md" in evidence_paths
    assert "docs/MODEL_OPS_DEFAULT_CHANGE_QUEUE.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_PLAN.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_OBSERVATION.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_PROMOTION_DECISION.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_APPROVAL_PACKET.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_ROLLBACK_DRILL.md" in evidence_paths
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_CHANGE_MANIFEST.md" in evidence_paths
    assert "docs/MODELOPS_GEMINI_CHEAP_FIRST_ROUTE_PREFLIGHT.md" in evidence_paths
    assert "docs/MODELOPS_AIHUB_ENDPOINT_ROUTE_COVERAGE_GATE.md" in evidence_paths
    assert "app/backend/tests/test_model_route_quality_budget.py" in evidence_paths
    assert "docs/MODEL_ROUTE_QUALITY_BUDGET.md" in evidence_paths
    assert "app/backend/services/route_telemetry_repository.py" in evidence_paths
    assert "app/backend/services/model_usage.py" in evidence_paths
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
    assert any("legal benchmark research refresh is metadata-only maintenance evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("model route legal benchmark risk queue is metadata-only route review evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("AIHub endpoint route coverage gate is metadata-only endpoint wiring evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("media/speech catalog review gaps" in guardrail for guardrail in profile["application_guardrails"])
    assert any("gateway connection profile is metadata-only OpenAI-compatible URL-shape evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("normalizes remote bare NewAPI/Gemini hosts to /v1" in guardrail for guardrail in profile["application_guardrails"])
    assert any("key presence with placeholders only" in guardrail for guardrail in profile["application_guardrails"])
    assert any("observed gateway model fit matrix is metadata-only inventory fit evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("runtime explicit model fit gate is metadata-only runtime route evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("unknown gateway guards" in guardrail for guardrail in profile["application_guardrails"])
    assert any("reviewed gateway pass-through exceptions" in guardrail for guardrail in profile["application_guardrails"])
    assert any("cheap-first task capabilities" in guardrail for guardrail in profile["application_guardrails"])
    assert any("lowest-cost observed candidates" in guardrail for guardrail in profile["application_guardrails"])
    assert any("missing task coverage" in guardrail for guardrail in profile["application_guardrails"])
    assert any("review-only Pro/preview/image/unknown/external/unpriced boundaries" in guardrail for guardrail in profile["application_guardrails"])
    assert any("validating account inventory" in guardrail for guardrail in profile["application_guardrails"])
    assert any("user-need implementation priority queue is metadata-only planning evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("high-priority user needs, legal benchmark coverage gaps, cheap-first calibration/model routing risk, and product execution actions" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG authority citation gate is metadata-only authority and citation evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG hallucination triage gate is metadata-only triage evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG abstention escalation gate is metadata-only answer-routing evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG retrieval diagnostics gate is metadata-only retrieval evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding readiness gate is metadata-only Gemini embedding" in guardrail for guardrail in profile["application_guardrails"])
    assert any("multimodal embedding review boundaries" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding chunk policy gate is metadata-only chunk planning evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("source-type split strategies" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding index dry-run gate is metadata-only manifest evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("planned vector-slot counts" in guardrail for guardrail in profile["application_guardrails"])
    assert any("durable index persistence fields" in guardrail for guardrail in profile["application_guardrails"])
    assert any("repository validation" in guardrail for guardrail in profile["application_guardrails"])
    assert any("commit-action blockers" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding batch budget gate is metadata-only cheap Gemini batch-budget evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("planned batch counts" in guardrail for guardrail in profile["application_guardrails"])
    assert any("laptop-safe chunk and token limits" in guardrail for guardrail in profile["application_guardrails"])
    assert any("local catalog batch-cost estimates" in guardrail for guardrail in profile["application_guardrails"])
    assert any("live pricing claims" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding batch approval packet is metadata-only maintainer review evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("serial low-resource queue order" in guardrail for guardrail in profile["application_guardrails"])
    assert any("max_parallel_embedding_requests=1" in guardrail for guardrail in profile["application_guardrails"])
    assert any("required maintainer/RAG-index reviewer roles" in guardrail for guardrail in profile["application_guardrails"])
    assert any("pre-approval checks" in guardrail for guardrail in profile["application_guardrails"])
    assert any("advance/hold/block actions" in guardrail for guardrail in profile["application_guardrails"])
    assert any("without claiming approval" in guardrail for guardrail in profile["application_guardrails"])
    assert any("collecting approver identity" in guardrail for guardrail in profile["application_guardrails"])
    assert any("writing approval records" in guardrail for guardrail in profile["application_guardrails"])
    assert any("writing indexes" in guardrail for guardrail in profile["application_guardrails"])
    assert any("writing indexes or databases" in guardrail for guardrail in profile["application_guardrails"])
    assert any("creating embeddings" in guardrail for guardrail in profile["application_guardrails"])
    assert any("source chunks" in guardrail for guardrail in profile["application_guardrails"])
    assert any("embedding vectors" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG retrieval observation gate is metadata-only local retrieval observation evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding batch observation gate is metadata-only aggregate observation evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal RAG embedding index commit review packet is metadata-only maintainer review evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("store or return source ids" in guardrail for guardrail in profile["application_guardrails"])
    assert any("raw query" in guardrail for guardrail in profile["application_guardrails"])
    assert any("raw retrieved context" in guardrail for guardrail in profile["application_guardrails"])
    assert any("write model routes" in guardrail for guardrail in profile["application_guardrails"])
    assert any("does not download datasets" in guardrail for guardrail in profile["application_guardrails"])
    assert any("store external legal text" in guardrail for guardrail in profile["application_guardrails"])
    assert any("call models" in guardrail for guardrail in profile["application_guardrails"])
    assert any("handle credentials" in guardrail for guardrail in profile["application_guardrails"])
    assert any("rollback drill is rehearsal metadata only" in guardrail for guardrail in profile["application_guardrails"])
    assert any("change manifest is proposed-change metadata only" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini cheap-first coverage gate is metadata-only coverage evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini cheap-first route preflight is metadata-only route review evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("official source refresh notes, local task defaults, variant review states" in guardrail for guardrail in profile["application_guardrails"])
    assert any("gateway responses, credentials, emails, or user identifiers" in guardrail for guardrail in profile["application_guardrails"])
    assert any("legal micro benchmark preflight is metadata-only low-resource legal benchmark run-planning evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("fixture ids, document case ids, fact-consistency case ids, serial run order" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini/NewAPI model alias matrix is metadata-only alias evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("sanitized model ids to canonical catalog ids" in guardrail for guardrail in profile["application_guardrails"])
    assert any("legal fixture cheap-first default promotion packet is metadata-only maintainer review evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("linked cheap-first calibration task ids" in guardrail for guardrail in profile["application_guardrails"])
    assert any("calibration payloads" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Legal document fact consistency benchmark is metadata-only amount/date/fact consistency evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("case ids, counts, and reason codes only" in guardrail for guardrail in profile["application_guardrails"])
    assert any(
        "legal document benchmark fixture UI" in guardrail and "does not render raw fixture snippets" in guardrail
        for guardrail in profile["application_guardrails"]
    )
    assert any("does not write configuration" in guardrail for guardrail in profile["application_guardrails"])
    assert any("shift traffic" in guardrail for guardrail in profile["application_guardrails"])
    assert any("agentic grounded defaults evidence is metadata-only/default routing evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("default template alignment audit is metadata-only env/template evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini default change proposal review is metadata-only proposal evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini default cost impact forecast is metadata-only cost evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("observed Gemini model intake queue is metadata-only intake evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Gemini/NewAPI observed model extraction evidence is metadata-only parsing evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("model catalog candidate patch plan is metadata-only catalog maintenance evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("does not edit model_catalog.py" in guardrail for guardrail in profile["application_guardrails"])
    assert any("OpenAI-compatible gateway /models or manually observed Gemini-like model ids" in guardrail for guardrail in profile["application_guardrails"])
    assert any("known/unknown status, price, lifecycle, cost tier, cheap-first eligibility" in guardrail for guardrail in profile["application_guardrails"])
    assert any("default-promotion block/review/ready state" in guardrail for guardrail in profile["application_guardrails"])
    assert any("cost tier, lifecycle, capabilities, gateway compatibility, and premium/manual review boundary" in guardrail for guardrail in profile["application_guardrails"])
    assert any("estimated monthly cost delta, cheap-first savings or regression, unknown pricing, and premium exception/manual review boundary" in guardrail for guardrail in profile["application_guardrails"])
    assert any("Settings defaults, app/backend/.env.example, the README env block, and docs/AI_MODEL_STRATEGY" in guardrail for guardrail in profile["application_guardrails"])
    assert any("does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network" in guardrail for guardrail in profile["application_guardrails"])
    assert any("ModelOps readiness warning drilldown is metadata-only warning triage evidence" in guardrail for guardrail in profile["application_guardrails"])
    assert any("review category, priority, next action, and validation hint" in guardrail for guardrail in profile["application_guardrails"])
    assert any("write real environment values" in guardrail for guardrail in profile["application_guardrails"])
    assert any("raw prompts, payloads, model outputs, or credentials" in guardrail for guardrail in profile["application_guardrails"])


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


def test_legacy_maintenance_evidence_alias_returns_profile():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/evidence?language=en")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["project"]["repository_url"] == REPOSITORY_URL


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
