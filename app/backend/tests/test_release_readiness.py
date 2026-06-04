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
            "case-edit-runtime-event-binding",
            "legal-rag-case-research-ui",
            "legal-rag-research-context-cache",
            "billing-usage-workspace-badge",
            "document-generation-quota-consumption-attempt",
        }
    }
    result = service.evaluate({
        "case-workbench-frontend-state-events": "not_run",
        "case-edit-runtime-event-binding": "not_run",
        "legal-rag-case-research-ui": "not_run",
        "legal-rag-research-context-cache": "not_run",
        "billing-usage-workspace-badge": "not_run",
        "document-generation-quota-consumption-attempt": "not_run",
    })
    checks = {check["id"]: check for check in result["checks"]}

    assert commands == {
        "case-workbench-frontend-state-events": "npm run typecheck",
        "case-edit-runtime-event-binding": "npm run typecheck",
        "legal-rag-case-research-ui": "npm run typecheck",
        "legal-rag-research-context-cache": "npm run typecheck",
        "billing-usage-workspace-badge": "npm run typecheck",
        "document-generation-quota-consumption-attempt": "npm run typecheck",
    }
    assert checks["case-workbench-frontend-state-events"]["required"] is False
    assert checks["case-edit-runtime-event-binding"]["required"] is False
    assert checks["legal-rag-case-research-ui"]["required"] is False
    assert checks["legal-rag-research-context-cache"]["required"] is False
    assert checks["billing-usage-workspace-badge"]["required"] is False
    assert checks["document-generation-quota-consumption-attempt"]["required"] is False
    assert checks["case-workbench-frontend-state-events"]["blocks_release"] is False
    assert checks["case-edit-runtime-event-binding"]["blocks_release"] is False
    assert checks["legal-rag-case-research-ui"]["blocks_release"] is False
    assert checks["legal-rag-research-context-cache"]["blocks_release"] is False
    assert checks["billing-usage-workspace-badge"]["blocks_release"] is False
    assert checks["document-generation-quota-consumption-attempt"]["blocks_release"] is False
    assert "app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx" in checks["case-workbench-frontend-state-events"]["evidence_paths"]
    assert "app/frontend/src/pages/CaseDetailPage.tsx" in checks["case-edit-runtime-event-binding"]["evidence_paths"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in checks["legal-rag-case-research-ui"]["evidence_paths"]
    assert "app/frontend/src/components/cases/LegalRagResearchPanel.tsx" in checks["legal-rag-research-context-cache"]["evidence_paths"]
    assert "app/frontend/src/components/billing/BillingUsageBadge.tsx" in checks["billing-usage-workspace-badge"]["evidence_paths"]
    assert "app/frontend/src/lib/billingUsageApi.ts" in checks["document-generation-quota-consumption-attempt"]["evidence_paths"]


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


def test_recent_backend_product_slices_are_optional_release_evidence():
    service = ReleaseReadinessService()
    expected_commands = {
        "generated-documents-crud-quota-guard": "python -m pytest tests/test_generated_documents_quota.py tests/test_billing_entitlement_quota_binding.py tests/test_billing_usage_router.py -q",
        "case-generation-quota-guard": "python -m pytest tests/test_case_generation_quota.py tests/test_billing_entitlement_quota_binding.py -q",
        "deep-review-document-generation-quota-guard": "python -m pytest tests/test_deep_review_document_quota.py tests/test_billing_entitlement_quota_binding.py -q",
        "legal-rag-selected-source-request-metadata": "python -m pytest tests/test_legal_rag_request_metadata.py -q",
        "legal-rag-selected-source-citation-validation": "python -m pytest tests/test_legal_rag_selected_source_validation.py tests/test_maintenance_legal_rag_selected_source_validation_route.py tests/test_legal_rag_request_metadata.py -q",
        "deep-review-selected-source-binding": "python -m pytest tests/test_deep_review_selected_source_binding.py tests/test_legal_rag_selected_source_validation.py -q",
        "quota-delivery-decision": "python -m pytest tests/test_quota_delivery_decision.py tests/test_deep_review_document_quota.py -q",
        "feedback-issue-cluster": "python -m pytest tests/test_feedback_issue_cluster.py -q",
        "evidence-bundle-integrity": "python -m pytest tests/test_evidence_bundle_integrity.py -q",
        "privacy-retention-rules": "python -m pytest tests/test_privacy_retention_rules.py -q",
        "release-claim-compliance": "python -m pytest tests/test_release_claim_compliance.py -q",
        "case-export-readiness": "python -m pytest tests/test_case_export_readiness.py tests/test_deep_review_selected_source_binding.py -q",
        "admin-audit-policy": "python -m pytest tests/test_admin_audit_policy.py -q",
        "continuous-session-evidence": "python -m pytest tests/test_continuous_session_evidence.py -q",
        "billing-payment-reconciliation-policy": "python -m pytest tests/test_billing_payment_reconciliation.py -q",
        "case-task-runtime-notification-summary": "python -m pytest tests/test_case_task_notification_policy.py -q",
        "legal-document-benchmark-suite": "python -m pytest tests/test_legal_document_benchmark_suite.py -q",
        "legal-benchmark-research-registry": "python -m pytest tests/test_legal_benchmark_research_registry.py -q",
        "legal-benchmark-research-registry-ui": "npm run typecheck",
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
    assert "blocks exhausted users without calling the AI generator" in checks["deep-review-document-generation-quota-guard"]["manual_note"]
    assert "metadata only" in checks["legal-rag-selected-source-request-metadata"]["manual_note"]
    assert "citation_map and generation_plan source IDs" in checks["legal-rag-selected-source-citation-validation"]["manual_note"]
    assert "metadata-only maintenance self-check route" in checks["legal-rag-selected-source-citation-validation"]["manual_note"]
    assert "deep-review report metadata" in checks["deep-review-selected-source-binding"]["manual_note"]
    assert "account-plan review decisions" in checks["quota-delivery-decision"]["manual_note"]
    assert "repeated user feedback" in checks["feedback-issue-cluster"]["manual_note"]
    assert "missing proof purposes" in checks["evidence-bundle-integrity"]["manual_note"]
    assert "retention and deletion review rules" in checks["privacy-retention-rules"]["manual_note"]
    assert "unsupported public claims" in checks["release-claim-compliance"]["manual_note"]
    assert "selected-source validation before case export" in checks["case-export-readiness"]["manual_note"]
    assert "sensitive admin actions" in checks["admin-audit-policy"]["manual_note"]
    assert "does not create proof by itself" in checks["continuous-session-evidence"]["manual_note"]
    assert "does not verify real payment provider settlement" in checks["billing-payment-reconciliation-policy"]["manual_note"]
    assert "does not claim public benchmark scores" in checks["legal-benchmark-research-registry"]["manual_note"]
    assert "maintenance evidence page" in checks["legal-benchmark-research-registry-ui"]["manual_note"]
