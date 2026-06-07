from services.release_readiness import ReleaseReadinessService


def test_release_readiness_requires_manual_validation_by_default():
    result = ReleaseReadinessService().evaluate()

    assert result["status"] == "manual_validation_required"
    assert result["release_allowed"] is False
    assert "backend-tests" in result["blocking_check_ids"]
    assert "frontend-ui-regression" in result["blocking_check_ids"]
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


def test_feedback_capture_plan_is_required_release_evidence():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "feedback-capture-plan"
    ]
    result = service.evaluate({"feedback-capture-plan": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "feedback-capture-plan")

    assert commands == [
        {
            "check_id": "feedback-capture-plan",
            "command": "python -m pytest tests/test_feedback_capture_plan.py tests/test_admin_feedback_capture_summary.py tests/test_feedback_lifecycle_policy.py tests/test_feedback_roadmap_alignment.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "app/backend/services/feedback_capture_plan.py" in check["evidence_paths"]
    assert "app/backend/routers/admin_ops.py" in check["evidence_paths"]
    assert "app/backend/routers/feedback_tickets.py" in check["evidence_paths"]
    assert "app/backend/tests/test_admin_feedback_capture_summary.py" in check["evidence_paths"]
    assert "app/backend/tests/test_feedback_capture_plan.py" in check["evidence_paths"]
    assert "app/frontend/src/components/feedback/FeedbackCapturePanel.tsx" in check["evidence_paths"]
    assert "app/frontend/src/lib/feedbackApi.ts" in check["evidence_paths"]
    assert "app/frontend/src/pages/AdminPage.tsx" in check["evidence_paths"]
    assert "app/frontend/src/pages/DeepReportPage.tsx" in check["evidence_paths"]
    assert "app/frontend/src/pages/SettingsPage.tsx" in check["evidence_paths"]
    assert "docs/FEEDBACK_CAPTURE_PLAN.md" in check["evidence_paths"]
    assert "metadata-only triage" in check["manual_note"]
    assert "raw feedback text" in check["manual_note"]


def test_case_workbench_risk_refresh_plan_is_optional_release_evidence():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "case-workbench-risk-refresh-plan"
    ]
    result = service.evaluate({"case-workbench-risk-refresh-plan": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "case-workbench-risk-refresh-plan")

    assert commands == [
        {
            "check_id": "case-workbench-risk-refresh-plan",
            "command": "python -m pytest tests/test_case_workbench_risk_refresh_plan.py tests/test_case_workbench_runtime_binding.py tests/test_case_workbench_runtime_router.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False
    assert "app/backend/services/case_workbench_risk_refresh_plan.py" in check["evidence_paths"]
    assert "app/backend/tests/test_case_workbench_risk_refresh_plan.py" in check["evidence_paths"]
    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in check["evidence_paths"]
    assert "docs/CASE_WORKBENCH_RISK_REFRESH_PLAN.md" in check["evidence_paths"]
    assert "does not write risk state" in check["manual_note"]
    assert "return raw event payloads" in check["manual_note"]


def test_case_access_control_runtime_gate_is_optional_security_evidence():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "case-access-control-runtime-gate"
    ]
    result = service.evaluate({"case-access-control-runtime-gate": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "case-access-control-runtime-gate")

    assert commands == [
        {
            "check_id": "case-access-control-runtime-gate",
            "command": (
                "python -m pytest tests/test_case_access_control.py tests/test_case_permission_runtime_router.py "
                "tests/test_case_role_permission_matrix.py tests/test_case_team_access_policy.py -q && cd ../frontend && npm run typecheck"
            ),
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False
    assert "app/backend/services/case_access_control.py" in check["evidence_paths"]
    assert "app/backend/routers/cases.py" in check["evidence_paths"]
    assert "app/backend/tests/test_case_permission_runtime_router.py" in check["evidence_paths"]
    assert "app/frontend/src/lib/caseApi.ts" in check["evidence_paths"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in check["evidence_paths"]
    assert "docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md" in check["evidence_paths"]
    assert "cases API and CaseDetail UI" in check["manual_note"]
    assert "durable membership rows" in check["manual_note"]


def test_frontend_runtime_ui_checks_are_optional_release_evidence():
    service = ReleaseReadinessService()
    commands = {
        item["check_id"]: item["command"]
        for item in service.default_validation_commands()
        if item["check_id"]
        in {
            "case-workbench-frontend-state-events",
            "case-edit-runtime-event-binding",
            "case-export-readiness-download-gate",
            "legal-rag-case-research-ui",
            "legal-rag-research-context-cache",
            "billing-usage-workspace-badge",
            "document-generation-quota-consumption-attempt",
        }
    }
    result = service.evaluate({
        "case-workbench-frontend-state-events": "not_run",
        "case-edit-runtime-event-binding": "not_run",
        "case-export-readiness-download-gate": "not_run",
        "legal-rag-case-research-ui": "not_run",
        "legal-rag-research-context-cache": "not_run",
        "billing-usage-workspace-badge": "not_run",
        "document-generation-quota-consumption-attempt": "not_run",
    })
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == {
        "case-workbench-frontend-state-events": "npm run typecheck",
        "case-edit-runtime-event-binding": "npm run typecheck",
        "case-export-readiness-download-gate": "cd ../frontend && npm run typecheck && npm run ui:regression && cd ../backend && python -m pytest tests/test_case_export_readiness.py tests/test_frontend_ui_regression_gate.py -q",
        "legal-rag-case-research-ui": "npm run typecheck",
        "legal-rag-research-context-cache": "npm run typecheck",
        "billing-usage-workspace-badge": "npm run typecheck",
        "document-generation-quota-consumption-attempt": "npm run typecheck",
    }
    assert checks["case-workbench-frontend-state-events"]["required"] is False
    assert checks["case-edit-runtime-event-binding"]["required"] is False
    assert checks["case-export-readiness-download-gate"]["required"] is False
    assert checks["legal-rag-case-research-ui"]["required"] is False
    assert checks["legal-rag-research-context-cache"]["required"] is False
    assert checks["billing-usage-workspace-badge"]["required"] is False
    assert checks["document-generation-quota-consumption-attempt"]["required"] is False
    assert checks["case-workbench-frontend-state-events"]["blocks_release"] is False
    assert checks["case-edit-runtime-event-binding"]["blocks_release"] is False
    assert checks["case-export-readiness-download-gate"]["blocks_release"] is False
    assert checks["legal-rag-case-research-ui"]["blocks_release"] is False
    assert checks["legal-rag-research-context-cache"]["blocks_release"] is False
    assert checks["billing-usage-workspace-badge"]["blocks_release"] is False
    assert checks["document-generation-quota-consumption-attempt"]["blocks_release"] is False
    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in checks["case-workbench-frontend-state-events"]["evidence_paths"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in checks["case-edit-runtime-event-binding"]["evidence_paths"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in checks["case-export-readiness-download-gate"]["evidence_paths"]
    assert "metadata-only export readiness" in checks["case-export-readiness-download-gate"]["manual_note"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in checks["legal-rag-case-research-ui"]["evidence_paths"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in checks["legal-rag-research-context-cache"]["evidence_paths"]
    assert "app/frontend/src/components/billing/BillingUsageBadge.tsx" in checks["billing-usage-workspace-badge"]["evidence_paths"]
    assert "app/frontend/src/lib/billingUsageApi.ts" in checks["document-generation-quota-consumption-attempt"]["evidence_paths"]


def test_model_gateway_request_compatibility_gate_is_required_release_evidence():
    service = ReleaseReadinessService()
    commands = [
        item
        for item in service.default_validation_commands()
        if item["check_id"] == "model-gateway-request-compatibility-gate"
    ]
    result = service.evaluate({"model-gateway-request-compatibility-gate": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-gateway-request-compatibility-gate")

    assert commands == [
        {
            "check_id": "model-gateway-request-compatibility-gate",
            "command": "python -m pytest tests/test_model_gateway_request_compatibility_gate.py tests/test_model_request_policy.py tests/test_model_reasoning_policy.py tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only OpenAI-compatible Gemini request-shape gate evidence" in check["manual_note"]
    assert "does not call NewAPI" in check["manual_note"]
    assert "gateways" in check["manual_note"]
    assert "does not write configuration" in check["manual_note"]
    assert "headers" in check["manual_note"]
    assert "request bodies" in check["manual_note"]
    assert "prompts" in check["manual_note"]
    assert "raw legal text" in check["manual_note"]
    assert "model output" in check["manual_note"]
    assert "payloads" in check["manual_note"]
    assert "emails" in check["manual_note"]
    assert "credentials" in check["manual_note"]
    assert "app/backend/services/model_gateway_request_compatibility_gate.py" in check["evidence_paths"]
    assert "app/backend/tests/test_model_gateway_request_compatibility_gate.py" in check["evidence_paths"]
    assert "app/backend/services/model_request_policy.py" in check["evidence_paths"]
    assert "app/backend/services/model_reasoning_policy.py" in check["evidence_paths"]
    assert "app/backend/services/model_gateway_compatibility.py" in check["evidence_paths"]
    assert "app/backend/routers/aihub.py" in check["evidence_paths"]
    assert "app/frontend/src/lib/modelOpsApi.ts" in check["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_GATEWAY_REQUEST_COMPATIBILITY_GATE.md" in check["evidence_paths"]


def test_billing_preflight_route_is_optional_release_evidence():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "billing-report-preflight-route"
    ]
    result = service.evaluate({"billing-report-preflight-route": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "billing-report-preflight-route")

    assert commands == [
        {
            "check_id": "billing-report-preflight-route",
            "command": "python -m pytest tests/test_billing_usage_router.py -q",
        }
    ]
    assert check["required"] is False
    assert check["blocks_release"] is False
    assert "app/backend/tests/test_billing_usage_router.py" in check["evidence_paths"]
    assert "server-side enforcement" in check["manual_note"]


def test_gemini_newapi_model_selector_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = {
        item["check_id"]: item["command"]
        for item in service.default_validation_commands()
        if item["check_id"]
        in {
            "gemini-newapi-model-selector",
            "gemini-newapi-observed-model-extraction",
            "gemini-newapi-model-alias-matrix",
            "gemini-newapi-alias-capability-coverage",
            "gemini-newapi-selector-replay",
            "gemini-newapi-cheap-first-calibration",
            "model-catalog-source-audit",
            "model-catalog-candidate-patch-plan",
            "model-catalog-candidate-impact-replay",
        }
    }
    result = service.evaluate(
        {
            "gemini-newapi-model-selector": "not_run",
            "gemini-newapi-observed-model-extraction": "not_run",
            "gemini-newapi-model-alias-matrix": "not_run",
            "gemini-newapi-alias-capability-coverage": "not_run",
            "gemini-newapi-selector-replay": "not_run",
            "gemini-newapi-cheap-first-calibration": "not_run",
            "model-catalog-source-audit": "not_run",
            "model-catalog-candidate-patch-plan": "not_run",
            "model-catalog-candidate-impact-replay": "not_run",
        }
    )
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == {
        "gemini-newapi-model-selector": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_model_catalog.py -q",
        "gemini-newapi-observed-model-extraction": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_model_variant_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_model_catalog_candidate_patch_plan.py -q",
        "gemini-newapi-model-alias-matrix": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py -q",
        "gemini-newapi-alias-capability-coverage": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q",
        "gemini-newapi-selector-replay": "python -m pytest tests/test_gemini_newapi_selector_replay.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_model_catalog.py -q",
        "gemini-newapi-cheap-first-calibration": "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_run_report.py tests/test_model_cost_guardrails.py -q",
        "model-catalog-source-audit": "python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q",
        "model-catalog-candidate-patch-plan": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_model_catalog_candidate_patch_plan.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_model_gateway_probe_evaluation.py tests/test_model_ops_readiness.py -q",
        "model-catalog-candidate-impact-replay": "python -m pytest tests/test_model_catalog_candidate_impact_replay.py tests/test_model_default_candidate_selector.py tests/test_model_capability_matrix.py tests/test_model_catalog_candidate_patch_plan.py tests/test_model_ops_readiness.py -q",
    }
    assert checks["gemini-newapi-model-selector"]["required"] is True
    assert checks["gemini-newapi-observed-model-extraction"]["required"] is True
    assert checks["gemini-newapi-model-alias-matrix"]["required"] is True
    assert checks["gemini-newapi-alias-capability-coverage"]["required"] is True
    assert checks["gemini-newapi-selector-replay"]["required"] is True
    assert checks["gemini-newapi-cheap-first-calibration"]["required"] is True
    assert checks["model-catalog-source-audit"]["required"] is True
    assert checks["model-catalog-candidate-patch-plan"]["required"] is True
    assert checks["model-catalog-candidate-impact-replay"]["required"] is True
    assert checks["gemini-newapi-model-selector"]["blocks_release"] is True
    assert checks["gemini-newapi-observed-model-extraction"]["blocks_release"] is True
    assert checks["gemini-newapi-model-alias-matrix"]["blocks_release"] is True
    assert checks["gemini-newapi-alias-capability-coverage"]["blocks_release"] is True
    assert checks["gemini-newapi-selector-replay"]["blocks_release"] is True
    assert checks["gemini-newapi-cheap-first-calibration"]["blocks_release"] is True
    assert checks["model-catalog-source-audit"]["blocks_release"] is True
    assert checks["model-catalog-candidate-patch-plan"]["blocks_release"] is True
    assert checks["model-catalog-candidate-impact-replay"]["blocks_release"] is True
    assert "does not call NewAPI" in checks["gemini-newapi-model-selector"]["manual_note"]
    assert "shared extraction evidence" in checks["gemini-newapi-observed-model-extraction"]["manual_note"]
    assert "sanitized model ids" in checks["gemini-newapi-observed-model-extraction"]["manual_note"]
    assert "raw payload echoing" in checks["gemini-newapi-observed-model-extraction"]["manual_note"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in checks[
        "gemini-newapi-observed-model-extraction"
    ]["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in checks[
        "gemini-newapi-observed-model-extraction"
    ]["evidence_paths"]
    assert "alias normalization evidence" in checks["gemini-newapi-model-alias-matrix"]["manual_note"]
    assert "write configuration" in checks["gemini-newapi-model-alias-matrix"]["manual_note"]
    assert "alias capability evidence" in checks["gemini-newapi-alias-capability-coverage"]["manual_note"]
    assert "without NewAPI/Gemini/OpenAI/Google/gateway/network calls" in checks[
        "gemini-newapi-alias-capability-coverage"
    ]["manual_note"]
    assert "without NewAPI calls" in checks["gemini-newapi-selector-replay"]["manual_note"]
    assert "metadata-only cheap-first calibration" in checks["gemini-newapi-cheap-first-calibration"]["manual_note"]
    assert "does not call Google" in checks["model-catalog-source-audit"]["manual_note"]
    assert "catalog candidate patch plan" in checks["model-catalog-candidate-patch-plan"]["manual_note"]
    assert "does not edit model_catalog.py" in checks["model-catalog-candidate-patch-plan"]["manual_note"]
    assert "virtual catalog impact replay" in checks["model-catalog-candidate-impact-replay"]["manual_note"]
    assert "does not edit model_catalog.py" in checks["model-catalog-candidate-impact-replay"]["manual_note"]
    assert "does not automatically change defaults" in checks["model-catalog-candidate-impact-replay"]["manual_note"]
    assert "gateway credentials" in checks["gemini-newapi-model-selector"]["manual_note"]
    assert "raw payloads" in checks["gemini-newapi-model-alias-matrix"]["manual_note"]


def test_model_ops_cheap_first_release_decision_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-release-decision"
    ]
    result = service.evaluate({"model-ops-cheap-first-release-decision": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-release-decision")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-release-decision",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_release_decision.py "
                "tests/test_model_ops_readiness.py tests/test_model_catalog_source_audit.py "
                "tests/test_model_route_quality_budget.py tests/test_model_ops_cheap_first_escalation_budget.py "
                "tests/test_model_failure_upgrade_budget.py tests/test_model_default_candidate_selector.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only cheap-first release decision packet" in check["manual_note"]
    assert "does not call NewAPI" in check["manual_note"]
    assert "public benchmark scores" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_release_decision.py" in check["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_escalation_budget.py" in check["evidence_paths"]
    assert "app/backend/services/model_failure_upgrade_budget.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_RELEASE_DECISION.md" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_ESCALATION_BUDGET.md" in check["evidence_paths"]
    assert "docs/MODEL_FAILURE_UPGRADE_BUDGET.md" in check["evidence_paths"]


def test_model_ops_cheap_first_escalation_budget_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-escalation-budget"
    ]
    result = service.evaluate({"model-ops-cheap-first-escalation-budget": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-escalation-budget")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-escalation-budget",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_escalation_budget.py "
                "tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py "
                "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only aggregate escalation budget evidence" in check["manual_note"]
    assert "does not execute retries" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_escalation_budget.py" in check["evidence_paths"]
    assert "app/backend/tests/test_model_ops_cheap_first_escalation_budget.py" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_ESCALATION_BUDGET.md" in check["evidence_paths"]


def test_model_failure_upgrade_budget_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-failure-upgrade-budget"
    ]
    result = service.evaluate({"model-failure-upgrade-budget": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-failure-upgrade-budget")

    assert commands == [
        {
            "check_id": "model-failure-upgrade-budget",
            "command": (
                "python -m pytest tests/test_model_failure_upgrade_budget.py "
                "tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py "
                "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only failure upgrade budget evidence" in check["manual_note"]
    assert "does not execute retries" in check["manual_note"]
    assert "app/backend/services/model_failure_upgrade_budget.py" in check["evidence_paths"]
    assert "app/backend/tests/test_model_failure_upgrade_budget.py" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_FAILURE_UPGRADE_BUDGET.md" in check["evidence_paths"]


def test_modelops_legal_benchmark_risk_bridge_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "modelops-legal-benchmark-risk-bridge"
    ]
    result = service.evaluate({"modelops-legal-benchmark-risk-bridge": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "modelops-legal-benchmark-risk-bridge")

    assert commands == [
        {
            "check_id": "modelops-legal-benchmark-risk-bridge",
            "command": (
                "python -m pytest tests/test_model_ops_legal_benchmark_risk_bridge.py "
                "tests/test_model_route_legal_benchmark_risk_queue.py "
                "tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && "
                "npm run typecheck && npm run ui:regression"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only legal benchmark risk bridge evidence" in check["manual_note"]
    assert "does not call NewAPI" in check["manual_note"]
    assert "public benchmark scores" in check["manual_note"]
    assert "raw legal text" in check["manual_note"]
    assert "app/backend/services/model_ops_legal_benchmark_risk_bridge.py" in check["evidence_paths"]
    assert "app/backend/tests/test_model_ops_legal_benchmark_risk_bridge.py" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_OPS_LEGAL_BENCHMARK_RISK_BRIDGE.md" in check["evidence_paths"]


def test_model_ops_default_change_queue_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-default-change-queue"
    ]
    result = service.evaluate({"model-ops-default-change-queue": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-default-change-queue")

    assert commands == [
        {
            "check_id": "model-ops-default-change-queue",
            "command": (
                "python -m pytest tests/test_model_ops_default_change_queue.py "
                "tests/test_model_ops_cheap_first_release_decision.py tests/test_model_default_optimization.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only maintainer queue" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "calls a gateway" in check["manual_note"]
    assert "docs/MODEL_OPS_DEFAULT_CHANGE_QUEUE.md" in check["evidence_paths"]


def test_model_ops_cheap_first_priority_queue_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-priority-queue"
    ]
    result = service.evaluate({"model-ops-cheap-first-priority-queue": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-priority-queue")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-priority-queue",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_priority_queue.py "
                "tests/test_model_ops_readiness.py tests/test_model_ops_default_change_queue.py "
                "tests/test_model_route_quality_budget.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only ranked maintainer queue" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "does not claim automatic default changes" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_priority_queue.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_PRIORITY_QUEUE.md" in check["evidence_paths"]


def test_model_ops_cheap_first_maintainer_execution_checklist_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-maintainer-execution-checklist"
    ]
    result = service.evaluate({"model-ops-cheap-first-maintainer-execution-checklist": "not_run"})
    check = next(
        check for check in result["checks"]
        if check["id"] == "model-ops-cheap-first-maintainer-execution-checklist"
    )

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-maintainer-execution-checklist",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_maintainer_execution_checklist.py "
                "tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_canary_change_manifest.py "
                "tests/test_model_ops_cheap_first_priority_queue.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only maintainer execution checklist" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "shifts traffic" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_maintainer_execution_checklist.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_MAINTAINER_EXECUTION_CHECKLIST.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_plan_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-plan"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-plan": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-plan")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-plan",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_plan.py "
                "tests/test_model_ops_default_change_queue.py "
                "tests/test_model_ops_cheap_first_release_decision.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only canary plan" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "shifts production traffic" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_plan.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_PLAN.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_observation_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-observation"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-observation": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-observation")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-observation",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_observation.py "
                "tests/test_model_ops_cheap_first_canary_plan.py "
                "tests/test_model_ops_default_change_queue.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only canary observation review" in check["manual_note"]
    assert "never stores raw payloads" in check["manual_note"]
    assert "shifts production traffic" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_observation.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_OBSERVATION.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_promotion_decision_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-promotion-decision"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-promotion-decision": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-promotion-decision")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-promotion-decision",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_promotion_decision.py "
                "tests/test_model_ops_cheap_first_canary_observation.py "
                "tests/test_model_ops_cheap_first_canary_plan.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only canary promotion decision" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "shifts production traffic" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_promotion_decision.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_PROMOTION_DECISION.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_approval_packet_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-approval-packet"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-approval-packet": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-approval-packet")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-approval-packet",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_approval_packet.py "
                "tests/test_model_ops_cheap_first_canary_promotion_decision.py "
                "tests/test_model_ops_cheap_first_canary_observation.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only maintainer approval packet" in check["manual_note"]
    assert "never records approval identity" in check["manual_note"]
    assert "shifts production traffic" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_approval_packet.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_APPROVAL_PACKET.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_rollback_drill_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-rollback-drill"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-rollback-drill": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-rollback-drill")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-rollback-drill",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_rollback_drill.py "
                "tests/test_model_ops_cheap_first_canary_approval_packet.py "
                "tests/test_model_ops_cheap_first_canary_promotion_decision.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only rollback rehearsal packet" in check["manual_note"]
    assert "never executes rollback" in check["manual_note"]
    assert "persists drill state" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_rollback_drill.py" in check["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_ROLLBACK_DRILL.md" in check["evidence_paths"]


def test_model_ops_cheap_first_canary_change_manifest_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands()
        if item["check_id"] == "model-ops-cheap-first-canary-change-manifest"
    ]
    result = service.evaluate({"model-ops-cheap-first-canary-change-manifest": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "model-ops-cheap-first-canary-change-manifest")

    assert commands == [
        {
            "check_id": "model-ops-cheap-first-canary-change-manifest",
            "command": (
                "python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py "
                "tests/test_model_ops_cheap_first_canary_rollback_drill.py "
                "tests/test_model_ops_cheap_first_canary_approval_packet.py -q"
            ),
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "metadata-only default-change manifest" in check["manual_note"]
    assert "external change-set metadata" in check["manual_note"]
    assert "never writes configuration" in check["manual_note"]
    assert "stores secret values" in check["manual_note"]
    assert "app/backend/services/model_ops_cheap_first_canary_change_manifest.py" in check["evidence_paths"]
    assert "app/backend/services/model_ops_cheap_first_canary_rollback_drill.py" in check["evidence_paths"]
    assert "docs/MODEL_OPS_CHEAP_FIRST_CANARY_CHANGE_MANIFEST.md" in check["evidence_paths"]


def test_route_telemetry_repository_is_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = {
        item["check_id"]: item["command"]
        for item in service.default_validation_commands()
        if item["check_id"]
        in {
            "route-telemetry-repository",
            "route-telemetry-persistence-plan",
            "route-telemetry-ops-summary",
            "route-telemetry-triage-queue",
            "route-telemetry-remediation-plan",
        }
    }
    result = service.evaluate(
        {
            "route-telemetry-repository": "not_run",
            "route-telemetry-persistence-plan": "not_run",
            "route-telemetry-ops-summary": "not_run",
            "route-telemetry-triage-queue": "not_run",
            "route-telemetry-remediation-plan": "not_run",
        }
    )
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == {
        "route-telemetry-persistence-plan": "python -m pytest tests/test_route_telemetry_persistence_plan.py -q",
        "route-telemetry-repository": "python -m pytest tests/test_route_telemetry_repository.py tests/test_route_telemetry_persistence_plan.py tests/test_model_route_telemetry.py tests/test_aihub_runtime_routing.py tests/test_model_usage.py -q",
        "route-telemetry-ops-summary": "python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_repository.py tests/test_model_route_telemetry.py -q",
        "route-telemetry-triage-queue": "python -m pytest tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py -q",
        "route-telemetry-remediation-plan": "python -m pytest tests/test_route_telemetry_remediation_plan.py tests/test_route_telemetry_triage_queue.py tests/test_model_default_optimization.py -q",
    }
    assert checks["route-telemetry-persistence-plan"]["required"] is False
    assert checks["route-telemetry-repository"]["required"] is True
    assert checks["route-telemetry-ops-summary"]["required"] is True
    assert checks["route-telemetry-triage-queue"]["required"] is True
    assert checks["route-telemetry-remediation-plan"]["required"] is True
    assert checks["route-telemetry-persistence-plan"]["blocks_release"] is False
    assert checks["route-telemetry-repository"]["blocks_release"] is True
    assert checks["route-telemetry-ops-summary"]["blocks_release"] is True
    assert checks["route-telemetry-triage-queue"]["blocks_release"] is True
    assert checks["route-telemetry-remediation-plan"]["blocks_release"] is True
    assert "durable storage and migrations remain separate" in checks["route-telemetry-persistence-plan"]["manual_note"]
    assert "persists sanitized route telemetry events locally" in checks["route-telemetry-repository"]["manual_note"]
    assert "local catalog token pricing" in checks["route-telemetry-repository"]["manual_note"]
    assert "unknown gateway models unpriced" in checks["route-telemetry-repository"]["manual_note"]
    assert "raw model outputs" in checks["route-telemetry-repository"]["manual_note"]
    assert "summarizes sanitized persisted telemetry" in checks["route-telemetry-ops-summary"]["manual_note"]
    assert "route reason-code hotspots" in checks["route-telemetry-ops-summary"]["manual_note"]
    assert "not proof that production routing is healthy" in checks["route-telemetry-ops-summary"]["manual_note"]
    assert "converts sanitized route telemetry operations checks" in checks["route-telemetry-triage-queue"]["manual_note"]
    assert "reason-code hotspots" in checks["route-telemetry-triage-queue"]["manual_note"]
    assert "no route events exist" in checks["route-telemetry-triage-queue"]["manual_note"]
    assert "operator-reviewed remediation suggestions only" in checks["route-telemetry-remediation-plan"]["manual_note"]
    assert "never writes configuration" in checks["route-telemetry-remediation-plan"]["manual_note"]


def test_runtime_route_reason_codes_are_required_model_ops_gate():
    service = ReleaseReadinessService()
    commands = [
        item for item in service.default_validation_commands() if item["check_id"] == "runtime-route-reason-codes"
    ]
    result = service.evaluate({"runtime-route-reason-codes": "not_run"})
    check = next(check for check in result["checks"] if check["id"] == "runtime-route-reason-codes")

    assert commands == [
        {
            "check_id": "runtime-route-reason-codes",
            "command": "python -m pytest tests/test_model_runtime_router.py tests/test_route_telemetry_repository.py tests/test_route_telemetry_persistence_plan.py tests/test_aihub_runtime_routing.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        }
    ]
    assert check["required"] is True
    assert check["blocks_release"] is True
    assert "allowlisted runtime route reason codes" in check["manual_note"]
    assert "sanitized repository reason-code counts" in check["manual_note"]
    assert "without storing prompts" in check["manual_note"]
    assert "credentials" in check["manual_note"]
    assert "app/backend/services/model_runtime_router.py" in check["evidence_paths"]
    assert "app/backend/services/route_telemetry_repository.py" in check["evidence_paths"]
    assert "app/backend/services/route_telemetry_persistence_plan.py" in check["evidence_paths"]
    assert "app/backend/tests/test_aihub_runtime_routing.py" in check["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in check["evidence_paths"]
    assert "docs/MODEL_ROUTE_TELEMETRY.md" in check["evidence_paths"]
    assert "docs/RELEASE_READINESS.md" in check["evidence_paths"]


def test_recent_backend_product_slices_are_optional_release_evidence():
    service = ReleaseReadinessService()
    expected_commands = {
        "generated-documents-crud-quota-guard": "python -m pytest tests/test_generated_documents_quota.py tests/test_billing_entitlement_quota_binding.py tests/test_billing_usage_router.py -q",
        "case-generation-quota-guard": "python -m pytest tests/test_case_generation_quota.py tests/test_billing_entitlement_quota_binding.py -q",
        "case-evidence-catalog-export-preflight": "python -m pytest tests/test_case_evidence_catalog_export_preflight.py tests/test_case_generation_quota.py -q",
        "deep-review-document-generation-quota-guard": "python -m pytest tests/test_deep_review_document_quota.py tests/test_billing_entitlement_quota_binding.py -q",
        "legal-rag-selected-source-request-metadata": "python -m pytest tests/test_legal_rag_request_metadata.py -q",
        "legal-rag-selected-source-citation-validation": "python -m pytest tests/test_legal_rag_selected_source_validation.py tests/test_maintenance_legal_rag_selected_source_validation_route.py tests/test_legal_rag_request_metadata.py -q",
        "deep-review-selected-source-binding": "python -m pytest tests/test_deep_review_selected_source_binding.py tests/test_legal_rag_selected_source_validation.py -q",
        "quota-delivery-decision": "python -m pytest tests/test_quota_delivery_decision.py tests/test_deep_review_document_quota.py -q",
        "feedback-issue-cluster": "python -m pytest tests/test_feedback_issue_cluster.py -q",
        "evidence-bundle-integrity": "python -m pytest tests/test_evidence_bundle_integrity.py -q",
        "privacy-retention-rules": "python -m pytest tests/test_privacy_retention_rules.py -q",
        "release-claim-compliance": "python -m pytest tests/test_release_claim_compliance.py -q",
        "legal-document-coverage-claim-policy": "python -m pytest tests/test_legal_document_coverage_claim_policy.py tests/test_legal_document_benchmark_coverage.py -q",
        "case-export-readiness": "python -m pytest tests/test_case_export_readiness.py tests/test_deep_review_selected_source_binding.py -q",
        "admin-audit-policy": "python -m pytest tests/test_admin_audit_policy.py -q",
        "continuous-session-evidence": "python -m pytest tests/test_continuous_session_evidence.py -q",
        "continuous-session-timeline": "python -m pytest tests/test_continuous_session_timeline.py -q",
        "continuous-session-run-monitor": "python -m pytest tests/test_continuous_session_run_monitor.py tests/test_continuous_session_timeline.py tests/test_continuous_session_review_packet.py -q",
        "continuous-session-review-packet": "python -m pytest tests/test_continuous_session_review_packet.py tests/test_continuous_session_timeline.py tests/test_validation_event_evidence.py -q",
        "git-history-evidence": "python -m pytest tests/test_git_history_evidence.py -q",
        "validation-event-evidence": "python -m pytest tests/test_validation_event_evidence.py tests/test_continuous_session_timeline.py -q",
        "billing-payment-reconciliation-policy": "python -m pytest tests/test_billing_payment_reconciliation.py -q",
        "case-task-runtime-notification-summary": "python -m pytest tests/test_case_task_notification_policy.py -q",
        "legal-document-benchmark-suite": "python -m pytest tests/test_legal_document_benchmark_suite.py -q",
        "legal-document-benchmark-gap-fixtures": "python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py -q",
        "legal-document-benchmark-coverage": "python -m pytest tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py -q",
        "legal-document-benchmark-coverage-ui": "npm run typecheck",
        "legal-document-fact-consistency-benchmark": "python -m pytest tests/test_legal_document_fact_consistency_benchmark.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        "frontend-ui-regression-gate": "python -m pytest tests/test_frontend_ui_regression_gate.py -q",
        "legal-benchmark-research-registry": "python -m pytest tests/test_legal_benchmark_research_registry.py -q",
        "legal-benchmark-research-refresh": "python -m pytest tests/test_legal_benchmark_research_refresh.py tests/test_legal_benchmark_research_registry.py tests/test_legal_adoption_research_bridge.py -q",
        "legal-public-benchmark-license-gate": "python -m pytest tests/test_legal_public_benchmark_license_gate.py tests/test_legal_public_benchmark_sampler.py tests/test_user_need_benchmark_coverage.py tests/test_model_route_legal_benchmark_risk_queue.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression",
        "model-route-legal-benchmark-risk-queue": "python -m pytest tests/test_model_route_legal_benchmark_risk_queue.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "user-need-implementation-priority-queue": "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-gemini-cheap-first-coverage-gate": "python -m pytest tests/test_modelops_gemini_cheap_first_coverage_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "modelops-legal-fixture-cheap-first-benchmark-gate": "python -m pytest tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-legal-fixture-cheap-first-default-promotion-packet": "python -m pytest tests/test_modelops_legal_fixture_default_promotion_packet.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-agentic-grounded-defaults": "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-default-template-alignment": "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-gemini-default-change-review": "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-gemini-default-cost-impact": "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-observed-gemini-model-intake-queue": "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "modelops-observed-gemini-coverage-gap-queue": "python -m pytest tests/test_model_ops_observed_gemini_coverage_gap_queue.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_gemini_model_variant_matrix.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "legal-rag-authority-citation-gate": "python -m pytest tests/test_legal_rag_authority_citation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "legal-rag-hallucination-triage-gate": "python -m pytest tests/test_legal_rag_hallucination_triage_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "legal-rag-abstention-escalation-gate": "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "legal-rag-retrieval-diagnostics-gate": "python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
        "legal-rag-retrieval-observation-gate": "python -m pytest tests/test_legal_rag_retrieval_observation_gate.py tests/test_legal_rag_selected_source_validation.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
        "legal-benchmark-research-registry-ui": "npm run typecheck",
        "legal-adoption-research-bridge": "python -m pytest tests/test_legal_adoption_research_bridge.py tests/test_user_needs_radar.py tests/test_product_feature_gap_radar.py -q",
    }
    commands = {
        item["check_id"]: item["command"]
        for item in service.default_validation_commands()
        if item["check_id"] in expected_commands
    }
    result = service.evaluate({check_id: "not_run" for check_id in expected_commands})
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == expected_commands
    for check_id in expected_commands:
        assert checks[check_id]["required"] is False
        assert checks[check_id]["blocks_release"] is False
    assert "case generation and deep-review first-principles generation are covered separately" in checks["generated-documents-crud-quota-guard"]["manual_note"]
    assert "evidence-catalog and civil-complaint generation consume report quota" in checks["case-generation-quota-guard"]["manual_note"]
    assert "exhibit package policy and bundle integrity metadata" in checks["case-evidence-catalog-export-preflight"]["manual_note"]
    assert "does not read files" in checks["case-evidence-catalog-export-preflight"]["manual_note"]
    assert "blocks exhausted users without calling the AI generator" in checks["deep-review-document-generation-quota-guard"]["manual_note"]
    assert "metadata only" in checks["legal-rag-selected-source-request-metadata"]["manual_note"]
    assert "citation_map and generation_plan source IDs" in checks["legal-rag-selected-source-citation-validation"]["manual_note"]
    assert "metadata-only maintenance self-check route" in checks["legal-rag-selected-source-citation-validation"]["manual_note"]
    assert "deep-review report metadata" in checks["deep-review-selected-source-binding"]["manual_note"]
    assert "account-plan review decisions" in checks["quota-delivery-decision"]["manual_note"]
    assert "repeated user feedback" in checks["feedback-issue-cluster"]["manual_note"]
    assert "missing proof purposes" in checks["evidence-bundle-integrity"]["manual_note"]
    assert "retention and deletion review rules" in checks["privacy-retention-rules"]["manual_note"]
    assert "unsupported legal-document coverage claims" in checks["legal-document-coverage-claim-policy"]["manual_note"]
    assert "repository-backed synthetic fixture coverage wording" in checks["legal-document-coverage-claim-policy"]["manual_note"]
    assert "not proof that the 24-hour session is complete" in checks["continuous-session-run-monitor"]["manual_note"]
    assert "unsupported public claims" in checks["release-claim-compliance"]["manual_note"]
    assert "selected-source validation before case export" in checks["case-export-readiness"]["manual_note"]
    assert "sensitive admin actions" in checks["admin-audit-policy"]["manual_note"]
    assert "does not create proof by itself" in checks["continuous-session-evidence"]["manual_note"]
    assert "keeping 24-hour completion blocked" in checks["continuous-session-timeline"]["manual_note"]
    assert "not a substitute for real timestamped 24-hour evidence" in checks["continuous-session-review-packet"]["manual_note"]
    assert "does not prove tests" in checks["git-history-evidence"]["manual_note"]
    assert "rejects raw logs" in checks["validation-event-evidence"]["manual_note"]
    assert "does not prove 24-hour completion" in checks["validation-event-evidence"]["manual_note"]
    assert "does not verify real payment provider settlement" in checks["billing-payment-reconciliation-policy"]["manual_note"]
    assert "fills the synthetic evidence-catalog" in checks["legal-document-benchmark-gap-fixtures"]["manual_note"]
    assert "real client-document coverage" in checks["legal-document-benchmark-gap-fixtures"]["manual_note"]
    assert "metadata-only coverage matrix" in checks["legal-document-benchmark-coverage"]["manual_note"]
    assert "without rendering raw fixture snippets" in checks["legal-document-benchmark-coverage-ui"]["manual_note"]
    assert "metadata-only amount, deadline, and fact-consistency benchmark evidence" in checks[
        "legal-document-fact-consistency-benchmark"
    ]["manual_note"]
    assert "does not call NewAPI" in checks["legal-document-fact-consistency-benchmark"]["manual_note"]
    assert "raw legal text" in checks["legal-document-fact-consistency-benchmark"]["manual_note"]
    assert "generated document text" in checks["legal-document-fact-consistency-benchmark"]["manual_note"]
    assert "credentials" in checks["legal-document-fact-consistency-benchmark"]["manual_note"]
    assert "client identifiers" in checks["legal-document-fact-consistency-benchmark"]["manual_note"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in checks[
        "legal-document-fact-consistency-benchmark"
    ]["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in checks[
        "legal-document-fact-consistency-benchmark"
    ]["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in checks["legal-document-fact-consistency-benchmark"]["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in checks["legal-document-fact-consistency-benchmark"]["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in checks[
        "legal-document-fact-consistency-benchmark"
    ]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in checks["legal-document-fact-consistency-benchmark"][
        "evidence_paths"
    ]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in checks[
        "legal-document-fact-consistency-benchmark"
    ]["evidence_paths"]
    assert "browser-level network-mocking automation gaps" in checks["frontend-ui-regression-gate"]["manual_note"]
    assert "does not claim public benchmark scores" in checks["legal-benchmark-research-registry"]["manual_note"]
    assert "does not download datasets" in checks["legal-benchmark-research-refresh"]["manual_note"]
    assert "public benchmark scores" in checks["legal-benchmark-research-refresh"]["manual_note"]
    assert "store external legal text" in checks["legal-benchmark-research-refresh"]["manual_note"]
    assert "call models" in checks["legal-benchmark-research-refresh"]["manual_note"]
    assert "handle credentials" in checks["legal-benchmark-research-refresh"]["manual_note"]
    assert "app/backend/services/legal_benchmark_research_refresh.py" in checks["legal-benchmark-research-refresh"]["evidence_paths"]
    assert "app/backend/tests/test_legal_benchmark_research_refresh.py" in checks["legal-benchmark-research-refresh"]["evidence_paths"]
    assert "docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md" in checks["legal-benchmark-research-refresh"]["evidence_paths"]
    assert "metadata-only public legal benchmark license-gate evidence" in checks[
        "legal-public-benchmark-license-gate"
    ]["manual_note"]
    assert "does not download datasets" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "import public benchmark text" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "claim public benchmark scores" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "call NewAPI" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "Gemini" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "gateways" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "network" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "raw legal text" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "prompts" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "model outputs" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "payloads" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "credentials" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "guarantee legal/license compliance" in checks["legal-public-benchmark-license-gate"]["manual_note"]
    assert "app/backend/services/legal_public_benchmark_license_gate.py" in checks[
        "legal-public-benchmark-license-gate"
    ]["evidence_paths"]
    assert "app/backend/tests/test_legal_public_benchmark_license_gate.py" in checks[
        "legal-public-benchmark-license-gate"
    ]["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in checks[
        "legal-public-benchmark-license-gate"
    ]["evidence_paths"]
    assert "docs/LEGAL_PUBLIC_BENCHMARK_LICENSE_GATE.md" in checks[
        "legal-public-benchmark-license-gate"
    ]["evidence_paths"]
    assert "metadata-only risk queue evidence" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "does not call gateways" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "download datasets" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "public benchmark scores" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "raw legal text" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "credentials" in checks["model-route-legal-benchmark-risk-queue"]["manual_note"]
    assert "app/backend/services/model_route_legal_benchmark_risk_queue.py" in checks["model-route-legal-benchmark-risk-queue"]["evidence_paths"]
    assert "app/backend/tests/test_model_route_legal_benchmark_risk_queue.py" in checks["model-route-legal-benchmark-risk-queue"]["evidence_paths"]
    assert "docs/MODEL_ROUTE_LEGAL_BENCHMARK_RISK_QUEUE.md" in checks["model-route-legal-benchmark-risk-queue"]["evidence_paths"]
    assert "metadata-only user-need implementation priority queue evidence" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "high-priority user needs" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "legal benchmark coverage gaps" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "cheap-first calibration/model routing risk" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "product execution actions" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "download public datasets" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "call NewAPI" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "Gemini" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "OpenAI" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "Google" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "gateways" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "network" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "real env values" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "raw legal text" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "prompts" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "payloads" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "model outputs" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "credentials" in checks["user-need-implementation-priority-queue"]["manual_note"]
    assert "app/backend/services/release_readiness.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "docs/USER_NEED_BENCHMARK_COVERAGE.md" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "docs/USER_NEEDS_RADAR.md" in checks["user-need-implementation-priority-queue"]["evidence_paths"]
    assert "metadata-only Gemini/NewAPI cheap-first coverage-gate evidence" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "Gemini-like defaults" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "cheap-first alignment" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "premium exceptions" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "unknown models" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "pricing" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "lifecycle" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "reasoning" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "gateway compatibility" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "claim/privacy boundaries" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "Gemini" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "OpenAI" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "Google" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "gateways" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "network" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "raw prompts" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "payloads" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "model outputs" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "credentials" in checks["modelops-gemini-cheap-first-coverage-gate"]["manual_note"]
    assert "app/backend/services/modelops_gemini_cheap_first_coverage_gate.py" in checks["modelops-gemini-cheap-first-coverage-gate"]["evidence_paths"]
    assert "app/backend/tests/test_modelops_gemini_cheap_first_coverage_gate.py" in checks["modelops-gemini-cheap-first-coverage-gate"]["evidence_paths"]
    assert "docs/MODELOPS_GEMINI_CHEAP_FIRST_COVERAGE_GATE.md" in checks["modelops-gemini-cheap-first-coverage-gate"]["evidence_paths"]
    assert "metadata-only small legal-document cheap-first Gemini benchmark/risk gate evidence" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "redacted fixture ids" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "document case ids" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "fact-consistency case ids" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "expected issue counts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "amount/date/fact consistency counts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "cost metadata" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "document benchmark pass/fail counts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "coverage-gap counts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "escalation metadata" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "Gemini" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "OpenAI" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "Google" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "gateways" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "network" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "real legal text" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "fixture snippets" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "prompts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "generated document text" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "model outputs" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "credentials" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "emails" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["manual_note"]
    assert "app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_CHEAP_FIRST_BENCHMARK_GATE.md" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-legal-fixture-cheap-first-benchmark-gate"]["evidence_paths"]
    assert "metadata-only maintainer review packet evidence" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "cheap-first legal fixture default promotion" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "fixture ids" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "document case ids" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "fact-consistency case ids" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "document benchmark pass/fail counts" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "amount/date/fact consistency counts" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "coverage-gap counts" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "required signoff roles" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "never writes configuration" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "never calls NewAPI" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "traffic" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "real legal text" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "generated document text" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "model outputs" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "credentials" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "emails" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["manual_note"]
    assert "app/backend/services/modelops_legal_fixture_default_promotion_packet.py" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/backend/tests/test_modelops_legal_fixture_default_promotion_packet.py" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/backend/services/legal_document_fact_consistency_benchmark.py" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/backend/tests/test_legal_document_fact_consistency_benchmark.py" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/backend/routers/maintenance.py" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/frontend/src/lib/maintenanceApi.ts" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/frontend/src/pages/MaintenanceEvidencePage.tsx" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "docs/MODELOPS_LEGAL_FIXTURE_DEFAULT_PROMOTION_PACKET.md" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "docs/LEGAL_DOCUMENT_FACT_CONSISTENCY_BENCHMARK.md" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-legal-fixture-cheap-first-default-promotion-packet"]["evidence_paths"]
    assert "metadata-only/default routing change evidence" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "APP_AI_AGENTIC_MODEL -> gemini-3.1-flash-lite" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "APP_AI_GROUNDED_RESEARCH_MODEL -> gemini-3.1-flash-lite" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "agentic and grounded-research task defaults" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "ready rather than blocked" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "Gemini" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "OpenAI" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "Google" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "gateways" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "network" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "real environment values" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "raw prompts" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "payloads" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "model outputs" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "credentials" in checks["modelops-agentic-grounded-defaults"]["manual_note"]
    assert "app/backend/core/config.py" in checks["modelops-agentic-grounded-defaults"]["evidence_paths"]
    assert "app/backend/services/model_catalog.py" in checks["modelops-agentic-grounded-defaults"]["evidence_paths"]
    assert "app/backend/services/modelops_gemini_cheap_first_coverage_gate.py" in checks["modelops-agentic-grounded-defaults"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-agentic-grounded-defaults"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-agentic-grounded-defaults"]["evidence_paths"]
    assert "metadata-only ModelOps env/template alignment audit evidence" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "Settings defaults" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "app/backend/.env.example" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "README env block" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "docs/AI_MODEL_STRATEGY" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "Gemini cheap-first defaults" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "APP_AI_AGENTIC_MODEL -> gemini-3.1-flash-lite" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "APP_AI_GROUNDED_RESEARCH_MODEL -> gemini-3.1-flash-lite" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "Gemini" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "OpenAI" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "Google" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "gateways" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "network" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "real environment values" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "raw prompts" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "payloads" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "model outputs" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "credentials" in checks["modelops-default-template-alignment"]["manual_note"]
    assert "app/backend/core/config.py" in checks["modelops-default-template-alignment"]["evidence_paths"]
    assert "app/backend/.env.example" in checks["modelops-default-template-alignment"]["evidence_paths"]
    assert "README.md" in checks["modelops-default-template-alignment"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-default-template-alignment"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-default-template-alignment"]["evidence_paths"]
    assert "metadata-only Gemini default change proposal review evidence" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "cost tier" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "lifecycle" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "capabilities" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "gateway compatibility" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "premium/manual review boundary" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "new Gemini variant" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "Gemini" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "OpenAI" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "Google" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "gateways" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "network" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "real environment values" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "raw prompts" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "payloads" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "model outputs" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "credentials" in checks["modelops-gemini-default-change-review"]["manual_note"]
    assert "app/backend/services/release_readiness.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-gemini-default-change-review"]["evidence_paths"]
    assert "metadata-only Gemini default change cost impact forecast evidence" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "estimated monthly cost delta" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "cheap-first savings or regression" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "unknown pricing" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "premium exception/manual review boundary" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "new Gemini variant" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "Gemini" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "OpenAI" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "Google" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "gateways" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "network" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "real environment values" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "raw prompts" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "payloads" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "model outputs" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "credentials" in checks["modelops-gemini-default-cost-impact"]["manual_note"]
    assert "app/backend/services/release_readiness.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-gemini-default-cost-impact"]["evidence_paths"]
    assert "metadata-only ModelOps observed Gemini model intake queue evidence" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "OpenAI-compatible gateway /models" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "manually observed Gemini-like model ids" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "known or unknown status" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "price" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "lifecycle" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "cost tier" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "cheap-first eligibility" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "default-promotion block/review/ready state" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "Gemini" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "OpenAI" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "Google" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "gateways" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "network" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "real environment values" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "raw prompts" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "payloads" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "model outputs" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "credentials" in checks["modelops-observed-gemini-model-intake-queue"]["manual_note"]
    assert "app/backend/services/gemini_newapi_observed_model_extraction.py" in checks[
        "modelops-observed-gemini-model-intake-queue"
    ]["evidence_paths"]
    assert "app/backend/services/model_ops_observed_gemini_model_intake_queue.py" in checks[
        "modelops-observed-gemini-model-intake-queue"
    ]["evidence_paths"]
    assert "app/backend/tests/test_gemini_newapi_observed_model_extraction.py" in checks[
        "modelops-observed-gemini-model-intake-queue"
    ]["evidence_paths"]
    assert "app/backend/tests/test_model_ops_observed_gemini_model_intake_queue.py" in checks[
        "modelops-observed-gemini-model-intake-queue"
    ]["evidence_paths"]
    assert "app/backend/services/release_readiness.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "app/backend/services/continuous_update_ledger.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "app/backend/services/maintenance_evidence.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "app/backend/tests/test_release_readiness.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "app/backend/tests/test_continuous_update_ledger.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "app/backend/tests/test_maintenance_evidence.py" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks["modelops-observed-gemini-model-intake-queue"]["evidence_paths"]
    assert "metadata-only ModelOps observed Gemini coverage gap evidence" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["manual_note"]
    assert "Gemini family coverage" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "high-frequency cheap-first task coverage" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["manual_note"]
    assert "unknown/unpriced/preview/media risk" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["manual_note"]
    assert "default-promotion review actions" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["manual_note"]
    assert "does not call NewAPI" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "Gemini" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "OpenAI" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "Google" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "gateways" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "network" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "real environment values" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "raw prompts" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "payloads" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "model outputs" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "credentials" in checks["modelops-observed-gemini-coverage-gap-queue"]["manual_note"]
    assert "app/backend/services/model_ops_observed_gemini_coverage_gap_queue.py" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "app/backend/services/model_ops_observed_gemini_model_intake_queue.py" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "app/backend/services/gemini_model_variant_matrix.py" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "app/backend/tests/test_model_ops_observed_gemini_coverage_gap_queue.py" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "app/frontend/src/pages/ModelOpsPage.tsx" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "app/frontend/scripts/ui-regression.mjs" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "docs/MODELOPS_OBSERVED_GEMINI_COVERAGE_GAP_QUEUE.md" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "docs/AI_MODEL_STRATEGY.md" in checks["modelops-observed-gemini-coverage-gap-queue"]["evidence_paths"]
    assert "docs/CONTINUOUS_UPDATE_LEDGER.md" in checks[
        "modelops-observed-gemini-coverage-gap-queue"
    ]["evidence_paths"]
    assert "metadata-only Legal RAG authority and citation gate evidence" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "Gemini" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "gateways" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "download datasets" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "raw legal text" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "prompts" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "model outputs" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "credentials" in checks["legal-rag-authority-citation-gate"]["manual_note"]
    assert "app/backend/services/legal_rag_authority_citation_gate.py" in checks["legal-rag-authority-citation-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_authority_citation_gate.py" in checks["legal-rag-authority-citation-gate"]["evidence_paths"]
    assert "docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md" in checks["legal-rag-authority-citation-gate"]["evidence_paths"]
    assert "metadata-only Legal RAG hallucination triage gate evidence" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "Gemini" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "gateways" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "download datasets" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "raw legal text" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "retrieved snippets" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "prompts" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "model outputs" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "credentials" in checks["legal-rag-hallucination-triage-gate"]["manual_note"]
    assert "app/backend/services/legal_rag_hallucination_triage_gate.py" in checks["legal-rag-hallucination-triage-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_hallucination_triage_gate.py" in checks["legal-rag-hallucination-triage-gate"]["evidence_paths"]
    assert "docs/LEGAL_RAG_HALLUCINATION_TRIAGE_GATE.md" in checks["legal-rag-hallucination-triage-gate"]["evidence_paths"]
    assert "metadata-only Legal RAG abstention escalation gate evidence" in checks["legal-rag-abstention-escalation-gate"]["manual_note"]
    assert "raw retrieved context" in checks["legal-rag-abstention-escalation-gate"]["manual_note"]
    assert "credentials" in checks["legal-rag-abstention-escalation-gate"]["manual_note"]
    assert "app/backend/services/legal_rag_abstention_escalation_gate.py" in checks["legal-rag-abstention-escalation-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_abstention_escalation_gate.py" in checks["legal-rag-abstention-escalation-gate"]["evidence_paths"]
    assert "docs/LEGAL_RAG_ABSTENTION_ESCALATION_GATE.md" in checks["legal-rag-abstention-escalation-gate"]["evidence_paths"]
    assert "metadata-only Legal RAG retrieval diagnostics gate evidence" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "query intent" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "authority coverage" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "top-k depth" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "jurisdiction/freshness" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "citation gaps" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "retrieval gaps" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "index binding linkage" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "authority citation linkage" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "abstention escalation linkage" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "cheap-first defaults" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "premium-exception boundaries" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "models" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "gateways" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "network" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "raw query" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "raw retrieved context" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "raw legal text" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "prompts" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "model outputs" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "credentials" in checks["legal-rag-retrieval-diagnostics-gate"]["manual_note"]
    assert "app/backend/services/legal_rag_retrieval_diagnostics_gate.py" in checks["legal-rag-retrieval-diagnostics-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_retrieval_diagnostics_gate.py" in checks["legal-rag-retrieval-diagnostics-gate"]["evidence_paths"]
    assert "docs/LEGAL_RAG_RETRIEVAL_DIAGNOSTICS_GATE.md" in checks["legal-rag-retrieval-diagnostics-gate"]["evidence_paths"]
    assert "metadata-only Legal RAG retrieval observation gate evidence" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "sanitized local retrieval observations" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "selected-source citation validation counts" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "top-k depth" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "cheap-first routing decisions" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "does not call NewAPI" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "store or return source ids" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "raw query" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "raw retrieved context" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "raw legal text" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "credentials" in checks["legal-rag-retrieval-observation-gate"]["manual_note"]
    assert "app/backend/services/legal_rag_retrieval_observation_gate.py" in checks["legal-rag-retrieval-observation-gate"]["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_retrieval_observation_gate.py" in checks["legal-rag-retrieval-observation-gate"]["evidence_paths"]
    assert "docs/LEGAL_RAG_RETRIEVAL_OBSERVATION_GATE.md" in checks["legal-rag-retrieval-observation-gate"]["evidence_paths"]
    assert "maintenance evidence page" in checks["legal-benchmark-research-registry-ui"]["manual_note"]
    assert "does not claim law-firm adoption" in checks["legal-adoption-research-bridge"]["manual_note"]
