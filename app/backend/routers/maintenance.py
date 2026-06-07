from typing import Any, Literal

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, ConfigDict, Field
from services.billing_entitlement_gap import BillingEntitlementGapService
from services.billing_quota_migration_plan import BillingQuotaMigrationPlanService
from services.billing_quota_persistence_plan import BillingQuotaPersistencePlanService
from services.billing_usage_quota_policy import BillingUsageQuotaPolicyService, UsageRequest, UsageSnapshot
from services.case_evidence_graph import CaseEvidenceGraphService
from services.case_intake_completeness import CaseIntakeCompletenessService
from services.case_role_permission_matrix import CaseRolePermissionMatrixService
from services.case_timeline_deadline_risk import CaseTimelineDeadlineRiskService
from services.case_team_access_policy import CaseTeamAccessPolicyService
from services.case_task_notification_policy import CaseTaskNotificationPolicyService
from services.case_workbench_payload import CaseWorkbenchPayloadService
from services.case_workbench_persistence_plan import CaseWorkbenchPersistencePlanService
from services.case_export_readiness import CaseExportReadinessService
from services.client_delivery_transparency_policy import ClientDeliveryTransparencyPolicyService
from services.client_delivery_risk_checklist import ClientDeliveryRiskChecklistService
from services.continuous_update_ledger import ContinuousUpdateLedgerService
from services.continuous_session_evidence import ContinuousSessionEvidenceService
from services.continuous_session_run_monitor import ContinuousSessionRunMonitorService
from services.continuous_session_review_packet import ContinuousSessionReviewPacketService
from services.continuous_session_timeline import ContinuousSessionTimelineService
from services.contract_clause_extraction_schema import ContractClauseExtractionSchemaService
from services.deadline_validation_policy import DeadlineValidationPolicyService
from services.document_delivery_package_manifest import DocumentDeliveryPackageManifestService
from services.document_version_diff_checklist import DocumentVersionDiffChecklistService
from services.evidence_bundle_integrity import EvidenceBundleIntegrityService
from services.evidence_exhibit_package_policy import EvidenceExhibitPackagePolicyService
from services.feedback_issue_cluster import FeedbackIssueClusterService
from services.feedback_lifecycle_policy import FeedbackLifecyclePolicyService
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.frontend_ui_regression_gate import FrontendUiRegressionGateService
from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService
from services.gemini_newapi_alias_capability_coverage import GeminiNewapiAliasCapabilityCoverageService
from services.gemini_newapi_model_alias_matrix import GeminiNewapiModelAliasMatrixService
from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService
from services.gemini_newapi_selector_replay import GeminiNewapiSelectorReplayService
from services.git_history_evidence import GitHistoryEvidenceService
from services.deep_review_selected_source_binding import DeepReviewSelectedSourceBindingService
from services.legal_document_benchmark_fixtures import LegalDocumentBenchmarkFixturesService
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_document_coverage_claim_policy import LegalDocumentCoverageClaimPolicyService
from services.legal_benchmark_fixture_crosswalk import LegalBenchmarkFixtureCrosswalkService
from services.legal_benchmark_research_registry import LegalBenchmarkResearchRegistryService
from services.legal_benchmark_research_refresh import LegalBenchmarkResearchRefreshService
from services.legal_rag_failure_fixtures import LegalRagFailureFixturesService
from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
from services.legal_fixture_gateway_manifest import LegalFixtureGatewayManifestService
from services.legal_fixture_improvement import LegalFixtureImprovementService
from services.legal_fixture_local_run_package import LegalFixtureLocalRunPackageService
from services.legal_fixture_local_run_review import LegalFixtureLocalRunReviewService
from services.legal_fixture_model_matrix import LegalFixtureModelMatrixService
from services.legal_fixture_prompt_pack import LegalFixturePromptPackService
from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService
from services.legal_fixture_response_normalizer import LegalFixtureResponseNormalizerService
from services.legal_fixture_result_archive import LegalFixtureResultArchiveService
from services.legal_fixture_regression import LegalFixtureRegressionService
from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_document_export_readiness import LegalDocumentExportReadinessService
from services.legal_document_template_matrix import LegalDocumentTemplateMatrixService
from services.lawyer_review_workflow_policy import LawyerReviewWorkflowPolicyService
from services.legal_adoption_research_bridge import LegalAdoptionResearchBridgeService
from services.legal_external_research_digest import LegalExternalResearchDigestService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_public_benchmark_license_gate import LegalPublicBenchmarkLicenseGateService
from services.legal_research_backlog import LegalResearchBacklogService
from services.legal_rag_authority_citation_gate import LegalRagAuthorityCitationGateService
from services.legal_rag_abstention_escalation_gate import LegalRagAbstentionEscalationGateService
from services.legal_rag_benchmark_alignment import LegalRagBenchmarkAlignmentService
from services.legal_rag_hallucination_triage_gate import LegalRagHallucinationTriageGateService
from services.legal_rag_retrieval_diagnostics_gate import LegalRagRetrievalDiagnosticsGateService
from services.legal_rag_retrieval_observation_gate import LegalRagRetrievalObservationGateService
from services.legal_rag_selected_source_validation import LegalRagSelectedSourceValidationService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.legal_source_durable_index_plan import LegalSourceDurableIndexPlanService
from services.legal_source_ingestion_metadata import LegalSourceIngestionMetadataService
from services.legal_source_freshness_policy import LegalSourceFreshnessPolicyService
from services.maintenance_evidence import MaintenanceEvidenceService
from services.maintenance_heartbeat_evidence import MaintenanceHeartbeatEvidenceService
from services.matter_audit_retention_policy import MatterAuditRetentionPolicyService
from services.matter_intake_readiness_policy import MatterIntakeReadinessPolicyService
from services.model_route_legal_benchmark_risk_queue import ModelRouteLegalBenchmarkRiskQueueService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import ModelOpsLegalFixtureCheapFirstBenchmarkGateService
from services.modelops_legal_fixture_default_promotion_packet import ModelOpsLegalFixtureDefaultPromotionPacketService
from services.modelops_legal_micro_benchmark_preflight import ModelOpsLegalMicroBenchmarkPreflightService
from services.model_cost_regression_snapshots import ModelCostRegressionSnapshotService
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService
from services.ocr_import_readiness_policy import OcrImportReadinessPolicyService
from services.privacy_retention_rules import PrivacyRetentionRulesService
from services.product_feature_gap_radar import ProductFeatureGapRadarService
from services.quota_delivery_decision import QuotaDeliveryDecisionService
from services.release_claim_compliance import ReleaseClaimComplianceService
from services.release_readiness import ReleaseReadinessService
from services.route_telemetry_persistence_plan import RouteTelemetryPersistencePlanService
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService
from services.route_telemetry_remediation_plan import RouteTelemetryRemediationPlanService
from services.small_legal_document_corpus_expansion import SmallLegalDocumentCorpusExpansionService
from services.user_needs_radar import UserNeedsRadarService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_need_gemini_route_coverage import UserNeedGeminiRouteCoverageService
from services.user_need_implementation_priority_queue import UserNeedImplementationPriorityQueueService
from services.admin_audit_policy import AdminAuditPolicyService
from services.validation_event_evidence import ValidationEventEvidenceService


router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


class LegalRagSelectedSourceValidationRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    citation_map: Any | None = None
    generation_plan: Any | None = None

    model_config = ConfigDict(extra="ignore")


class LegalRagRetrievalObservationGateRequest(BaseModel):
    retrieval_observations: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class DeepReviewSelectedSourceBindingRequest(BaseModel):
    report: dict[str, Any] = Field(default_factory=dict)
    request_metadata: dict[str, Any] = Field(default_factory=dict)
    block_on_failure: bool = True

    model_config = ConfigDict(extra="ignore")


class QuotaDeliveryDecisionRequest(BaseModel):
    action: str = "export_report"
    quota_summary: dict[str, Any] = Field(default_factory=dict)
    release_decision: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class PrivacyRetentionRulesRequest(BaseModel):
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ReleaseClaimComplianceRequest(BaseModel):
    claims: list[Any] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class LegalDocumentCoverageClaimPolicyRequest(BaseModel):
    claims: list[Any] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class CaseExportReadinessRequest(BaseModel):
    report: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class AdminAuditPolicyRequest(BaseModel):
    actions: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


@router.get("/oss-evidence")
async def get_oss_maintenance_evidence(
    language: Literal["en", "zh"] = Query(default="en", description="Form answer language."),
):
    """Return reviewable OSS maintenance evidence for support applications."""
    return {
        "success": True,
        "data": MaintenanceEvidenceService().build_profile(language),
    }


@router.get("/user-needs")
async def get_user_needs_radar():
    """Return deterministic user-need priorities for roadmap and release planning."""
    return {
        "success": True,
        "data": UserNeedsRadarService().build_radar(),
    }


@router.get("/user-needs/benchmark-coverage")
async def get_user_need_benchmark_coverage():
    """Return metadata-only coverage between user needs and local benchmark evidence."""
    return {
        "success": True,
        "data": UserNeedBenchmarkCoverageService().build_coverage(),
    }


@router.get("/user-needs/gemini-route-coverage")
async def get_user_need_gemini_route_coverage():
    """Return metadata-only coverage between user needs and Gemini route evidence."""
    return {
        "success": True,
        "data": UserNeedGeminiRouteCoverageService().build_coverage(),
    }


@router.get("/user-needs/implementation-priority-queue")
async def get_user_need_implementation_priority_queue():
    """Return metadata-only queue for user-need implementation priorities."""
    return {
        "success": True,
        "data": UserNeedImplementationPriorityQueueService().build_queue(),
    }


@router.get("/feedback-roadmap")
async def get_feedback_roadmap_mapping():
    """Return feedback-to-roadmap mapping rules for maintenance planning."""
    return {
        "success": True,
        "data": FeedbackRoadmapAlignmentService().build_mapping_catalog(),
    }


@router.get("/frontend-ui-regression-gate")
async def get_frontend_ui_regression_gate():
    """Return metadata-only frontend UI regression gate coverage."""
    return {
        "success": True,
        "data": FrontendUiRegressionGateService().build_gate(),
    }


@router.get("/feedback-lifecycle-policy")
async def get_feedback_lifecycle_policy():
    """Return the feedback lifecycle state machine and closure checks."""
    return {
        "success": True,
        "data": FeedbackLifecyclePolicyService().build_policy(),
    }


@router.post("/feedback-lifecycle-policy")
async def evaluate_feedback_lifecycle_policy(payload: dict[str, Any]):
    """Evaluate a feedback ticket lifecycle transition without storing raw feedback."""
    return {
        "success": True,
        "data": FeedbackLifecyclePolicyService().evaluate_ticket(payload),
    }


@router.post("/feedback/issue-clusters")
async def build_feedback_issue_clusters(payload: Any = Body(...)):
    """Cluster feedback items into privacy-safe repeated issue groups."""
    items = payload.get("items") if isinstance(payload, dict) else payload
    return {
        "success": True,
        "data": FeedbackIssueClusterService().cluster(items if isinstance(items, list) else []),
    }


@router.get("/product-feature-gaps")
async def get_product_feature_gap_radar():
    """Return product-wide feature gaps that still need implementation."""
    return {
        "success": True,
        "data": ProductFeatureGapRadarService().build_radar(),
    }


@router.get("/billing-entitlement-gap")
async def get_billing_entitlement_gap_evidence():
    """Return deterministic billing and entitlement gap evidence."""
    return {
        "success": True,
        "data": BillingEntitlementGapService().build_gap_evidence(),
    }


@router.get("/billing-usage-quota-policy")
async def get_billing_usage_quota_policy():
    """Return local billing usage and quota policy evidence."""
    return {
        "success": True,
        "data": BillingUsageQuotaPolicyService().build_policy_evidence(),
    }


@router.post("/billing-usage-quota-policy")
async def evaluate_billing_usage_quota_policy(payload: dict[str, Any]):
    """Evaluate a quota request from explicit usage counters without payment calls."""
    snapshot_source = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
    request_source = payload.get("request") if isinstance(payload.get("request"), dict) else payload
    snapshot_fields = {
        key: snapshot_source[key]
        for key in UsageSnapshot.__dataclass_fields__
        if key in snapshot_source
    }
    request_fields = {
        key: request_source[key]
        for key in UsageRequest.__dataclass_fields__
        if key in request_source
    }
    request_fields.setdefault("action", "review")
    return {
        "success": True,
        "data": BillingUsageQuotaPolicyService().evaluate(
            UsageSnapshot(**snapshot_fields),
            UsageRequest(**request_fields),
        ),
    }


@router.get("/billing-quota-persistence-plan")
async def get_billing_quota_persistence_plan():
    """Return privacy-safe billing quota counter persistence plan metadata."""
    return {
        "success": True,
        "data": BillingQuotaPersistencePlanService().build_plan(),
    }


@router.post("/billing-quota-persistence-plan")
async def evaluate_billing_quota_persistence_plan(events: list[dict[str, Any]]):
    """Evaluate sample billing quota events before durable persistence."""
    return {
        "success": True,
        "data": BillingQuotaPersistencePlanService().build_plan(events),
    }


@router.get("/billing-quota-migration-plan")
async def get_billing_quota_migration_plan():
    """Return database migration planning metadata for billing quota counters."""
    return {
        "success": True,
        "data": BillingQuotaMigrationPlanService().build_plan(),
    }


@router.post("/billing-quota-migration-plan")
async def evaluate_billing_quota_migration_plan(sample_checks: list[dict[str, Any]]):
    """Evaluate sample billing quota migration checks without connecting to a database."""
    return {
        "success": True,
        "data": BillingQuotaMigrationPlanService().build_plan(sample_checks),
    }


@router.get("/case-evidence-graph")
async def get_case_evidence_graph_template():
    """Return the backend contract for case fact-evidence-citation-risk graphs."""
    return {
        "success": True,
        "data": CaseEvidenceGraphService().build_graph(),
    }


@router.post("/case-evidence-graph")
async def build_case_evidence_graph(payload: dict[str, Any]):
    """Build a graph summary from normalized report fields without reading client files."""
    return {
        "success": True,
        "data": CaseEvidenceGraphService().build_graph(payload),
    }


@router.get("/case-workbench-payload")
async def get_case_workbench_payload_template():
    """Return the frontend case workbench payload template."""
    return {
        "success": True,
        "data": CaseWorkbenchPayloadService().build_payload(),
    }


@router.post("/case-workbench-payload")
async def build_case_workbench_payload(payload: dict[str, Any]):
    """Build a case workbench payload from explicit metadata only."""
    return {
        "success": True,
        "data": CaseWorkbenchPayloadService().build_payload(
            case_id=payload.get("case_id"),
            matter_id=payload.get("matter_id"),
            intake=payload.get("intake") if isinstance(payload.get("intake"), dict) else None,
            deadlines=payload.get("deadlines") if isinstance(payload.get("deadlines"), list) else None,
            timeline_events=payload.get("timeline_events") if isinstance(payload.get("timeline_events"), list) else None,
            tasks=payload.get("tasks") if isinstance(payload.get("tasks"), list) else None,
            evidence_report=payload.get("evidence_report") if isinstance(payload.get("evidence_report"), dict) else None,
            reference_date=payload.get("reference_date"),
        ),
    }


@router.get("/case-workbench-persistence-plan")
async def get_case_workbench_persistence_plan():
    """Return the privacy-safe persistence plan for case workbench state."""
    return {
        "success": True,
        "data": CaseWorkbenchPersistencePlanService().build_plan(),
    }


@router.post("/case-workbench-persistence-plan")
async def evaluate_case_workbench_persistence_plan(events: list[dict[str, Any]]):
    """Evaluate sample case workbench state events before durable persistence."""
    return {
        "success": True,
        "data": CaseWorkbenchPersistencePlanService().build_plan(events),
    }


@router.get("/case-intake-completeness")
async def get_case_intake_completeness_template():
    """Return the case intake completeness checklist template."""
    return {
        "success": True,
        "data": CaseIntakeCompletenessService().build_checklist(),
    }


@router.post("/case-intake-completeness")
async def evaluate_case_intake_completeness(payload: dict[str, Any]):
    """Evaluate structured case intake field completeness without reading raw files."""
    return {
        "success": True,
        "data": CaseIntakeCompletenessService().build_checklist(payload),
    }


@router.get("/matter-intake-readiness-policy")
async def get_matter_intake_readiness_policy_template():
    """Return matter-intake completeness, conflict, and lawyer-review readiness metadata."""
    return {
        "success": True,
        "data": MatterIntakeReadinessPolicyService().build_policy(),
    }


@router.post("/matter-intake-readiness-policy")
async def evaluate_matter_intake_readiness_policy(payload: dict[str, Any]):
    """Evaluate matter intake readiness from metadata without echoing raw case content."""
    return {
        "success": True,
        "data": MatterIntakeReadinessPolicyService().build_policy(payload),
    }


@router.get("/case-timeline-deadline-risk")
async def get_case_timeline_deadline_risk_template():
    """Return deterministic case timeline and deadline-risk metadata."""
    return {
        "success": True,
        "data": CaseTimelineDeadlineRiskService().build_assessment(),
    }


@router.post("/case-timeline-deadline-risk")
async def evaluate_case_timeline_deadline_risk(events: list[dict[str, Any]]):
    """Evaluate deadline risk from supplied event metadata without using the current date."""
    return {
        "success": True,
        "data": CaseTimelineDeadlineRiskService().build_assessment(events),
    }


@router.get("/deadline-validation-policy")
async def get_deadline_validation_policy_template():
    """Return deterministic legal deadline validation and reminder policy metadata."""
    return {
        "success": True,
        "data": DeadlineValidationPolicyService().build_policy(),
    }


@router.post("/deadline-validation-policy")
async def evaluate_deadline_validation_policy(payload: dict[str, Any]):
    """Evaluate deadline metadata using explicit dates and an optional reference date."""
    deadlines = payload.get("deadlines")
    return {
        "success": True,
        "data": DeadlineValidationPolicyService().build_policy(
            deadlines if isinstance(deadlines, list) else None,
            reference_date=payload.get("reference_date"),
        ),
    }


@router.get("/case-task-notification-policy")
async def get_case_task_notification_policy_template():
    """Return deterministic case task notification and escalation policy metadata."""
    return {
        "success": True,
        "data": CaseTaskNotificationPolicyService().build_policy(),
    }


@router.post("/case-task-notification-policy")
async def evaluate_case_task_notification_policy(tasks: list[dict[str, Any]]):
    """Evaluate task notification triggers from deterministic task metadata."""
    return {
        "success": True,
        "data": CaseTaskNotificationPolicyService().build_policy(tasks),
    }


@router.get("/case-team-access-policy")
async def get_case_team_access_policy():
    """Return least-privilege case collaboration and audit policy metadata."""
    return {
        "success": True,
        "data": CaseTeamAccessPolicyService().build_policy(),
    }


@router.get("/case-role-permission-matrix")
async def get_case_role_permission_matrix():
    """Return privacy-safe case role and operation permission matrix metadata."""
    return {
        "success": True,
        "data": CaseRolePermissionMatrixService().build_privacy_safe_api_payload(),
    }


@router.post("/case-role-permission-matrix")
async def evaluate_case_role_permission_matrix(payload: dict[str, Any]):
    """Evaluate one role-operation permission decision."""
    return {
        "success": True,
        "data": CaseRolePermissionMatrixService().evaluate_permission(
            str(payload.get("role") or ""),
            str(payload.get("operation") or ""),
        ),
    }


@router.get("/lawyer-review-workflow-policy")
async def get_lawyer_review_workflow_policy_template():
    """Return lawyer review state machine and role-gate policy metadata."""
    return {
        "success": True,
        "data": LawyerReviewWorkflowPolicyService().build_policy(),
    }


@router.post("/lawyer-review-workflow-policy")
async def evaluate_lawyer_review_workflow_policy(payload: dict[str, Any]):
    """Evaluate a proposed lawyer-review workflow transition."""
    return {
        "success": True,
        "data": LawyerReviewWorkflowPolicyService().build_policy(payload),
    }


@router.get("/client-delivery-risk-checklist")
async def get_client_delivery_risk_checklist():
    """Return client-delivery disclosure, lawyer-review, and evidence gates."""
    return {
        "success": True,
        "data": ClientDeliveryRiskChecklistService().build_checklist(),
    }


@router.get("/client-delivery-transparency-policy")
async def get_client_delivery_transparency_policy_template():
    """Return client confirmation, version diff, risk notice, and delivery audit gates."""
    return {
        "success": True,
        "data": ClientDeliveryTransparencyPolicyService().build_policy(),
    }


@router.post("/client-delivery-transparency-policy")
async def evaluate_client_delivery_transparency_policy(payload: dict[str, Any]):
    """Evaluate client-delivery transparency metadata before external release."""
    return {
        "success": True,
        "data": ClientDeliveryTransparencyPolicyService().build_policy(payload),
    }


@router.get("/document-delivery-package-manifest")
async def get_document_delivery_package_manifest_template():
    """Return legal document delivery package manifest requirements."""
    return {
        "success": True,
        "data": DocumentDeliveryPackageManifestService().build_manifest(),
    }


@router.post("/document-delivery-package-manifest")
async def evaluate_document_delivery_package_manifest(payload: dict[str, Any]):
    """Evaluate document delivery package metadata before client release."""
    return {
        "success": True,
        "data": DocumentDeliveryPackageManifestService().build_manifest(payload),
    }


@router.get("/document-version-diff-checklist")
async def get_document_version_diff_checklist_template():
    """Return client-visible document version diff checklist metadata."""
    return {
        "success": True,
        "data": DocumentVersionDiffChecklistService().build_checklist(),
    }


@router.post("/document-version-diff-checklist")
async def evaluate_document_version_diff_checklist(payload: dict[str, Any]):
    """Evaluate version diff metadata before client-visible delivery."""
    return {
        "success": True,
        "data": DocumentVersionDiffChecklistService().build_checklist(payload),
    }


@router.get("/contract-clause-extraction-schema")
async def get_contract_clause_extraction_schema_template():
    """Return contract clause extraction and review schema metadata."""
    return {
        "success": True,
        "data": ContractClauseExtractionSchemaService().build_schema(),
    }


@router.post("/contract-clause-extraction-schema")
async def evaluate_contract_clause_extraction_schema(clauses: list[dict[str, Any]]):
    """Evaluate extracted contract clause metadata before clause-level review."""
    return {
        "success": True,
        "data": ContractClauseExtractionSchemaService().build_schema(clauses),
    }


@router.get("/evidence-exhibit-package-policy")
async def get_evidence_exhibit_package_policy_template():
    """Return evidence exhibit package metadata, review, and export policy."""
    return {
        "success": True,
        "data": EvidenceExhibitPackagePolicyService().build_policy(),
    }


@router.post("/evidence-exhibit-package-policy")
async def evaluate_evidence_exhibit_package_policy(payload: dict[str, Any]):
    """Evaluate evidence exhibit package metadata without reading files."""
    return {
        "success": True,
        "data": EvidenceExhibitPackagePolicyService().build_policy(payload),
    }


@router.post("/evidence/bundle-integrity")
async def evaluate_evidence_bundle_integrity(payload: Any = Body(...)):
    """Evaluate evidence bundle duplicates and metadata gaps without reading files."""
    return {
        "success": True,
        "data": EvidenceBundleIntegrityService().build_report(payload),
    }


@router.post("/case/export-readiness")
async def evaluate_case_export_readiness(payload: CaseExportReadinessRequest):
    """Evaluate report export readiness without echoing raw report text."""
    return {
        "success": True,
        "data": CaseExportReadinessService().evaluate(payload.report),
    }


@router.get("/legal-document-template-matrix")
async def get_legal_document_template_matrix():
    """Return legal document template, format, export, and review gate coverage."""
    return {
        "success": True,
        "data": LegalDocumentTemplateMatrixService().build_matrix(),
    }


@router.get("/legal-document-export-readiness")
async def get_legal_document_export_readiness_template():
    """Return final-export gate metadata for generated legal documents."""
    return {
        "success": True,
        "data": LegalDocumentExportReadinessService().build_readiness(),
    }


@router.post("/legal-document-export-readiness")
async def evaluate_legal_document_export_readiness(payload: dict[str, Any]):
    """Evaluate final-export readiness from status metadata without reading files."""
    return {
        "success": True,
        "data": LegalDocumentExportReadinessService().build_readiness(payload),
    }


@router.get("/ocr-import-readiness-policy")
async def get_ocr_import_readiness_policy_template():
    """Return OCR/import readiness state policy metadata."""
    return {
        "success": True,
        "data": OcrImportReadinessPolicyService().build_policy(),
    }


@router.post("/ocr-import-readiness-policy")
async def evaluate_ocr_import_readiness_policy(payload: dict[str, Any]):
    """Evaluate OCR/import readiness from upload preflight metadata."""
    return {
        "success": True,
        "data": OcrImportReadinessPolicyService().build_policy(payload),
    }


@router.get("/matter-audit-retention-policy")
async def get_matter_audit_retention_policy_template():
    """Return privacy-minimized matter audit retention policy metadata."""
    return {
        "success": True,
        "data": MatterAuditRetentionPolicyService().build_policy(),
    }


@router.post("/matter-audit-retention-policy")
async def evaluate_matter_audit_retention_policy(sample_events: list[dict[str, Any]]):
    """Evaluate sample audit event metadata against retention and minimization policy."""
    return {
        "success": True,
        "data": MatterAuditRetentionPolicyService().build_policy(sample_events),
    }


@router.get("/continuous-update-ledger")
async def get_continuous_update_ledger():
    """Return the long-running update ledger without claiming completion early."""
    return {
        "success": True,
        "data": ContinuousUpdateLedgerService().build_ledger(),
    }


@router.post("/continuous-update-ledger")
async def build_continuous_update_ledger_with_fixture_evidence(payload: Any = Body(default=None)):
    """Return the ledger with archive-safe low-resource fixture evidence summary."""
    return {
        "success": True,
        "data": ContinuousUpdateLedgerService().build_ledger(payload),
    }


@router.get("/maintenance-heartbeat-evidence")
async def get_maintenance_heartbeat_evidence_template():
    """Return a privacy-safe template for 24-hour maintenance heartbeat evidence."""
    return {
        "success": True,
        "data": MaintenanceHeartbeatEvidenceService().build_evidence(),
    }


@router.post("/maintenance-heartbeat-evidence")
async def build_maintenance_heartbeat_evidence(events: list[dict[str, Any]]):
    """Build heartbeat evidence from explicit commit, test, push, and review events."""
    return {
        "success": True,
        "data": MaintenanceHeartbeatEvidenceService().build_evidence(events),
    }


@router.get("/continuous-session-evidence")
async def get_continuous_session_evidence_template():
    """Return a stricter continuous-session evidence template for the 24-hour goal."""
    return {
        "success": True,
        "data": ContinuousSessionEvidenceService().build_report(),
    }


@router.post("/continuous-session-evidence")
async def build_continuous_session_evidence(payload: Any = Body(default=None)):
    """Evaluate explicit session events without claiming 24-hour completion early."""
    return {
        "success": True,
        "data": ContinuousSessionEvidenceService().build_report(payload),
    }


@router.get("/continuous-session-timeline")
async def get_continuous_session_timeline_template():
    """Return a combined timeline template for 100+ updates and 24-hour evidence."""
    return {
        "success": True,
        "data": ContinuousSessionTimelineService().build_timeline(),
    }


@router.post("/continuous-session-timeline")
async def build_continuous_session_timeline(payload: Any = Body(default=None)):
    """Build a metadata-only reviewer timeline without echoing raw legal text."""
    return {
        "success": True,
        "data": ContinuousSessionTimelineService().build_timeline(payload),
    }


@router.get("/continuous-session-run-monitor")
async def get_continuous_session_run_monitor_template():
    """Return active-run monitoring metadata for the 24-hour maintenance goal."""
    return {
        "success": True,
        "data": ContinuousSessionRunMonitorService().build_monitor(),
    }


@router.post("/continuous-session-run-monitor")
async def build_continuous_session_run_monitor(payload: Any = Body(default=None)):
    """Build a metadata-only active-run monitor without echoing raw logs or legal text."""
    return {
        "success": True,
        "data": ContinuousSessionRunMonitorService().build_monitor(payload),
    }


@router.get("/continuous-session-review-packet")
async def get_continuous_session_review_packet_template():
    """Return a metadata-only reviewer packet for continuous maintenance evidence."""
    return {
        "success": True,
        "data": ContinuousSessionReviewPacketService().build_packet(),
    }


@router.post("/continuous-session-review-packet")
async def build_continuous_session_review_packet(payload: Any = Body(default=None)):
    """Build a reviewer packet without echoing raw logs, legal text, or credentials."""
    return {
        "success": True,
        "data": ContinuousSessionReviewPacketService().build_packet(payload),
    }


@router.get("/git-history-evidence")
async def get_git_history_evidence():
    """Return metadata-only git commit cadence evidence for maintenance review."""
    return {
        "success": True,
        "data": GitHistoryEvidenceService().build_evidence(),
    }


@router.post("/git-history-evidence")
async def build_git_history_evidence(payload: Any = Body(default=None)):
    """Evaluate submitted git commit metadata without reading raw diffs."""
    return {
        "success": True,
        "data": GitHistoryEvidenceService().build_evidence(payload),
    }


@router.get("/validation-event-evidence")
async def get_validation_event_evidence_template():
    """Return metadata-only validation event evidence for session timelines."""
    return {
        "success": True,
        "data": ValidationEventEvidenceService().build_evidence(),
    }


@router.post("/validation-event-evidence")
async def build_validation_event_evidence(payload: Any = Body(default=None)):
    """Normalize validation event metadata without echoing raw logs or legal text."""
    return {
        "success": True,
        "data": ValidationEventEvidenceService().build_evidence(payload),
    }


@router.get("/gemini-newapi-cheap-first-policy")
async def get_gemini_newapi_cheap_first_policy():
    """Return cheap-first Gemini/NewAPI family and default-selection policy metadata."""
    return {
        "success": True,
        "data": GeminiNewapiCheapFirstPolicyService().build_policy(),
    }


@router.post("/gemini-newapi-cheap-first-policy")
async def evaluate_gemini_newapi_cheap_first_policy(payload: dict[str, Any]):
    """Review observed model ids against the cheap-first Gemini/NewAPI policy."""
    observed_models = payload.get("observed_models")
    return {
        "success": True,
        "data": GeminiNewapiCheapFirstPolicyService().build_policy(
            observed_models if isinstance(observed_models, list) else None
        ),
    }


@router.get("/gemini-newapi-model-selector")
async def get_gemini_newapi_model_selector():
    """Return metadata-only Gemini/NewAPI model selection recommendations."""
    return {
        "success": True,
        "data": GeminiNewapiModelSelectorService().build_selector(),
    }


@router.post("/gemini-newapi-model-selector")
async def evaluate_gemini_newapi_model_selector(payload: Any = Body(default=None)):
    """Evaluate Gemini/NewAPI model ids and task routes without calling the gateway."""
    return {
        "success": True,
        "data": GeminiNewapiModelSelectorService().build_selector(payload),
    }


@router.get("/gemini-newapi-model-alias-matrix")
async def get_gemini_newapi_model_alias_matrix():
    """Return metadata-only Gemini/NewAPI alias normalization evidence."""
    return {
        "success": True,
        "data": GeminiNewapiModelAliasMatrixService().build_matrix(),
    }


@router.post("/gemini-newapi-model-alias-matrix")
async def evaluate_gemini_newapi_model_alias_matrix(payload: Any = Body(default=None)):
    """Evaluate sanitized Gemini/NewAPI alias ids without calling the gateway."""
    return {
        "success": True,
        "data": GeminiNewapiModelAliasMatrixService().build_matrix(payload),
    }


@router.get("/gemini-newapi-alias-capability-coverage")
async def get_gemini_newapi_alias_capability_coverage():
    """Return metadata-only Gemini/NewAPI alias capability coverage evidence."""
    return {
        "success": True,
        "data": GeminiNewapiAliasCapabilityCoverageService().build_coverage(),
    }


@router.post("/gemini-newapi-alias-capability-coverage")
async def evaluate_gemini_newapi_alias_capability_coverage(payload: Any = Body(default=None)):
    """Evaluate sanitized Gemini/NewAPI aliases against local capability metadata."""
    return {
        "success": True,
        "data": GeminiNewapiAliasCapabilityCoverageService().build_coverage(payload),
    }


@router.get("/gemini-newapi-selector-replay")
async def get_gemini_newapi_selector_replay():
    """Return deterministic replay evidence for Gemini/NewAPI selector scenarios."""
    return {
        "success": True,
        "data": GeminiNewapiSelectorReplayService().run_replay(),
    }


@router.post("/gemini-newapi-selector-replay")
async def evaluate_gemini_newapi_selector_replay(payload: Any = Body(default=None)):
    """Replay submitted selector scenarios without calling NewAPI."""
    return {
        "success": True,
        "data": GeminiNewapiSelectorReplayService().run_replay(payload),
    }


@router.get("/model-price-refresh-monitor")
async def get_model_price_refresh_monitor():
    """Return local Gemini/NewAPI price-refresh drift checks."""
    return {
        "success": True,
        "data": ModelPriceRefreshMonitorService().build_monitor(),
    }


@router.post("/model-price-refresh-monitor")
async def evaluate_model_price_refresh_monitor(payload: dict[str, Any]):
    """Review observed gateway model ids against local price-refresh metadata."""
    observed_models = payload.get("observed_models")
    return {
        "success": True,
        "data": ModelPriceRefreshMonitorService().build_monitor(
            observed_models if isinstance(observed_models, list) else None
        ),
    }


@router.get("/model-cost-regression-snapshots")
async def get_model_cost_regression_snapshots():
    """Return deterministic cheap-first model cost regression snapshots."""
    return {
        "success": True,
        "data": ModelCostRegressionSnapshotService().build_snapshots(),
    }


@router.get("/route-telemetry-persistence-plan")
async def get_route_telemetry_persistence_plan_template():
    """Return privacy-safe route telemetry persistence schema and retention plan."""
    return {
        "success": True,
        "data": RouteTelemetryPersistencePlanService().build_plan(),
    }


@router.post("/route-telemetry-persistence-plan")
async def evaluate_route_telemetry_persistence_plan(events: list[dict[str, Any]]):
    """Evaluate sanitized route telemetry samples before durable persistence."""
    return {
        "success": True,
        "data": RouteTelemetryPersistencePlanService().build_plan(events),
    }


@router.get("/route-telemetry-repository")
async def get_route_telemetry_repository():
    """Return local privacy-safe route telemetry repository aggregates."""
    return {
        "success": True,
        "data": RouteTelemetryRepositoryService().build_repository(),
    }


@router.post("/route-telemetry-repository")
async def append_route_telemetry_repository_events(events: list[dict[str, Any]]):
    """Append sanitized route telemetry events and rebuild daily aggregates."""
    return {
        "success": True,
        "data": RouteTelemetryRepositoryService().append_events(events),
    }


@router.get("/route-telemetry-ops-summary")
async def get_route_telemetry_ops_summary():
    """Return cheap-first operations summary from persisted route telemetry."""
    return {
        "success": True,
        "data": RouteTelemetryOpsSummaryService().build_summary(),
    }


@router.get("/route-telemetry-triage")
async def get_route_telemetry_triage_queue():
    """Return actionable triage queue from persisted route telemetry operations."""
    return {
        "success": True,
        "data": RouteTelemetryTriageQueueService().build_queue(),
    }


@router.get("/route-telemetry-remediation")
async def get_route_telemetry_remediation_plan():
    """Return operator-reviewed remediation plan for route telemetry triage."""
    return {
        "success": True,
        "data": RouteTelemetryRemediationPlanService().build_plan(),
    }


@router.get("/legal-review-benchmark")
async def get_legal_review_benchmark_suite():
    """Return the deterministic benchmark suite for legal-review pipeline changes."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate(),
    }


@router.post("/legal-review-benchmark")
async def evaluate_legal_review_benchmark(run_results: dict[str, dict]):
    """Evaluate supplied benchmark results for release planning."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate(run_results),
    }


@router.get("/legal-review-benchmark/research-backlog")
async def get_legal_review_research_backlog():
    """Return research-backed engineering backlog for legal-review benchmark work."""
    return {
        "success": True,
        "data": LegalResearchBacklogService().build_backlog(),
    }


@router.get("/legal-review-benchmark/external-research-digest")
async def get_legal_external_research_digest():
    """Return external legal-AI research signals mapped to local engineering work."""
    return {
        "success": True,
        "data": LegalExternalResearchDigestService().build_digest(),
    }


@router.get("/legal-review-benchmark/adoption-research-bridge")
async def get_legal_adoption_research_bridge():
    """Return public adoption and research signals mapped to local product work."""
    return {
        "success": True,
        "data": LegalAdoptionResearchBridgeService().build_bridge(),
    }


@router.get("/legal-review-benchmark/research-registry")
async def get_legal_benchmark_research_registry():
    """Return public legal benchmark lessons mapped to local low-resource validation."""
    return {
        "success": True,
        "data": LegalBenchmarkResearchRegistryService().build_registry(),
    }


def _build_legal_benchmark_research_refresh_response() -> dict[str, Any]:
    return {
        "success": True,
        "data": LegalBenchmarkResearchRefreshService().build_refresh(),
    }


@router.get("/legal-benchmark-research-refresh")
async def get_legal_benchmark_research_refresh():
    """Return refreshed legal benchmark research mapped to local validation."""
    return _build_legal_benchmark_research_refresh_response()


@router.get("/legal-review-benchmark/research-refresh")
async def get_legal_review_benchmark_research_refresh():
    """Return refreshed legal benchmark research under the benchmark namespace."""
    return _build_legal_benchmark_research_refresh_response()


@router.get("/model-route-legal-benchmark-risk-queue")
async def get_model_route_legal_benchmark_risk_queue():
    """Return cheap-first model route risks joined to legal benchmark evidence."""
    return {
        "success": True,
        "data": ModelRouteLegalBenchmarkRiskQueueService().build_queue(),
    }


@router.get("/legal-review-benchmark/public-sampler")
async def get_legal_public_benchmark_sampler():
    """Return a resource-capped public benchmark sampling plan."""
    return {
        "success": True,
        "data": LegalPublicBenchmarkSamplerService().build_plan(),
    }


@router.post("/legal-review-benchmark/public-sampler")
async def build_legal_public_benchmark_sampler(config: dict[str, Any]):
    """Build a public benchmark sampling plan from explicit source review settings."""
    return {
        "success": True,
        "data": LegalPublicBenchmarkSamplerService().build_plan(config),
    }


@router.get("/legal-review-benchmark/public-license-gate")
async def get_legal_public_benchmark_license_gate():
    """Return public legal benchmark source license review gate evidence."""
    return {
        "success": True,
        "data": LegalPublicBenchmarkLicenseGateService().build_gate(),
    }


@router.post("/legal-review-benchmark/public-license-gate")
async def build_legal_public_benchmark_license_gate(config: dict[str, Any]):
    """Build public benchmark license review evidence from explicit review settings."""
    return {
        "success": True,
        "data": LegalPublicBenchmarkLicenseGateService().build_gate(config),
    }


@router.get("/legal-review-benchmark/fixture-crosswalk")
async def get_legal_benchmark_fixture_crosswalk():
    """Return public benchmark to local fixture crosswalk metadata."""
    return {
        "success": True,
        "data": LegalBenchmarkFixtureCrosswalkService().build_crosswalk(),
    }


@router.get("/legal-review-benchmark/document-fixtures")
async def get_legal_document_benchmark_fixtures():
    """Return tiny local Chinese legal-document benchmark fixtures for laptop tests."""
    return {
        "success": True,
        "data": LegalDocumentBenchmarkFixturesService().build_suite(),
    }


@router.get("/legal-review-benchmark/document-coverage")
async def get_legal_document_benchmark_coverage():
    """Return a metadata-only coverage matrix for local legal-document fixtures."""
    return {
        "success": True,
        "data": LegalDocumentBenchmarkCoverageService().build_matrix(),
    }


@router.post("/legal-review-benchmark/document-coverage/claims")
async def evaluate_legal_document_coverage_claims(payload: LegalDocumentCoverageClaimPolicyRequest):
    """Check legal document coverage claims without echoing raw claim text."""
    return {
        "success": True,
        "data": LegalDocumentCoverageClaimPolicyService().evaluate(payload.claims),
    }


@router.post("/legal-review-benchmark/document-fixtures")
async def evaluate_legal_document_benchmark_fixtures(predictions: dict[str, Any]):
    """Evaluate local structured predictions against deterministic document fixtures."""
    return {
        "success": True,
        "data": LegalDocumentBenchmarkFixturesService().evaluate_predictions(predictions),
    }


@router.get("/legal-review-benchmark/document-fact-consistency")
async def get_legal_document_fact_consistency_benchmark():
    """Return structured fact consistency benchmark expectations for legal documents."""
    return {
        "success": True,
        "data": LegalDocumentFactConsistencyBenchmarkService().build_suite(),
    }


@router.post("/legal-review-benchmark/document-fact-consistency")
async def evaluate_legal_document_fact_consistency_benchmark(outputs: dict[str, Any]):
    """Evaluate structured amount, deadline, and fact consistency outputs."""
    return {
        "success": True,
        "data": LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs(outputs),
    }


@router.get("/legal-review-benchmark/small-corpus-expansion")
async def get_small_legal_document_corpus_expansion():
    """Return expanded small synthetic legal-document corpus metadata."""
    return {
        "success": True,
        "data": SmallLegalDocumentCorpusExpansionService().build_corpus(),
    }


@router.get("/legal-review-benchmark/rag-failure-fixtures")
async def get_legal_rag_failure_fixtures():
    """Return tiny legal RAG failure fixtures for local grounding tests."""
    return {
        "success": True,
        "data": LegalRagFailureFixturesService().build_suite(),
    }


@router.post("/legal-review-benchmark/rag-failure-fixtures")
async def evaluate_legal_rag_failure_fixtures(observations: dict[str, Any]):
    """Evaluate local RAG failure observations against deterministic fixtures."""
    return {
        "success": True,
        "data": LegalRagFailureFixturesService().evaluate_observations(observations),
    }


@router.post("/legal-rag/selected-source-validation")
async def validate_legal_rag_selected_source_citations(payload: LegalRagSelectedSourceValidationRequest):
    """Run a metadata-only self-check for selected-source citation validation."""
    return {
        "success": True,
        "data": LegalRagSelectedSourceValidationService().validate(
            request_metadata=payload.metadata,
            citation_map=payload.citation_map,
            generation_plan=payload.generation_plan,
        ),
    }


@router.get("/legal-rag-authority-citation-gate")
async def get_legal_rag_authority_citation_gate():
    """Return metadata-only Legal RAG authority and citation gate evidence."""
    return {
        "success": True,
        "data": LegalRagAuthorityCitationGateService().build_gate(),
    }


@router.get("/legal-rag-hallucination-triage-gate")
async def get_legal_rag_hallucination_triage_gate():
    """Return metadata-only Legal RAG hallucination triage gate evidence."""
    return {
        "success": True,
        "data": LegalRagHallucinationTriageGateService().build_gate(),
    }


@router.get("/legal-rag-abstention-escalation-gate")
async def get_legal_rag_abstention_escalation_gate():
    """Return metadata-only Legal RAG answer abstention and escalation evidence."""
    return {
        "success": True,
        "data": LegalRagAbstentionEscalationGateService().build_gate(),
    }


@router.get("/legal-rag-retrieval-diagnostics-gate")
async def get_legal_rag_retrieval_diagnostics_gate():
    """Return metadata-only Legal RAG retrieval diagnostic evidence."""
    return {
        "success": True,
        "data": LegalRagRetrievalDiagnosticsGateService().build_gate(),
    }


@router.get("/legal-rag-benchmark-alignment")
async def get_legal_rag_benchmark_alignment():
    """Return metadata-only public benchmark alignment evidence for Legal RAG."""
    return {
        "success": True,
        "data": LegalRagBenchmarkAlignmentService().build_scorecard(),
    }


@router.post("/legal-rag-retrieval-observation-gate")
async def evaluate_legal_rag_retrieval_observation_gate(payload: LegalRagRetrievalObservationGateRequest):
    """Evaluate sanitized Legal RAG retrieval observations without raw text echo."""
    return {
        "success": True,
        "data": LegalRagRetrievalObservationGateService().build_gate(payload.model_dump()),
    }


@router.post("/deep-review/selected-source-binding")
async def bind_deep_review_selected_source_validation(payload: DeepReviewSelectedSourceBindingRequest):
    """Attach selected-source validation to a deep-review report without raw text echo."""
    return {
        "success": True,
        "data": DeepReviewSelectedSourceBindingService().evaluate(
            report=payload.report,
            request_metadata=payload.request_metadata,
            block_on_failure=payload.block_on_failure,
        ),
    }


@router.post("/billing/quota-delivery-decision")
async def evaluate_quota_delivery_decision(payload: QuotaDeliveryDecisionRequest):
    """Evaluate export, delivery, or account-plan action from sanitized quota metadata."""
    return {
        "success": True,
        "data": QuotaDeliveryDecisionService().decide(
            action=payload.action,
            quota_summary=payload.quota_summary,
            release_decision=payload.release_decision,
        ),
    }


@router.get("/privacy/retention-rules")
async def get_privacy_retention_rules():
    """Return privacy-safe retention and deletion rules for legal workflow artifacts."""
    return {
        "success": True,
        "data": PrivacyRetentionRulesService().build_policy(),
    }


@router.post("/privacy/retention-rules")
async def evaluate_privacy_retention_rules(payload: PrivacyRetentionRulesRequest):
    """Evaluate artifact retention metadata without raw legal text or PII echo."""
    return {
        "success": True,
        "data": PrivacyRetentionRulesService().build_policy(payload.artifacts),
    }


@router.post("/compliance/release-claims")
async def evaluate_release_claim_compliance(payload: ReleaseClaimComplianceRequest):
    """Check public release/support-application claims without echoing raw claim text."""
    return {
        "success": True,
        "data": ReleaseClaimComplianceService().evaluate(payload.claims),
    }


@router.post("/admin/audit-policy")
async def evaluate_admin_audit_policy(payload: AdminAuditPolicyRequest):
    """Evaluate sensitive admin action audit requirements without raw payload echo."""
    return {
        "success": True,
        "data": AdminAuditPolicyService().evaluate(payload.actions),
    }


@router.get("/legal-review-benchmark/source-freshness-policy")
async def get_legal_source_freshness_policy_template():
    """Return legal source freshness, citation, and jurisdiction review metadata."""
    return {
        "success": True,
        "data": LegalSourceFreshnessPolicyService().build_policy(),
    }


@router.post("/legal-review-benchmark/source-freshness-policy")
async def evaluate_legal_source_freshness_policy(payload: dict[str, Any]):
    """Evaluate legal source metadata without reading raw legal materials."""
    sources = payload.get("sources")
    return {
        "success": True,
        "data": LegalSourceFreshnessPolicyService().build_policy(sources if isinstance(sources, list) else None),
    }


@router.get("/legal-review-benchmark/source-ingestion-metadata")
async def get_legal_source_ingestion_metadata_template():
    """Return legal source ingestion metadata schema and sample evaluation."""
    return {
        "success": True,
        "data": LegalSourceIngestionMetadataService().build_metadata_contract(),
    }


@router.post("/legal-review-benchmark/source-ingestion-metadata")
async def evaluate_legal_source_ingestion_metadata(payload: dict[str, Any]):
    """Evaluate legal source ingestion metadata records without raw legal text."""
    records = payload.get("records")
    return {
        "success": True,
        "data": LegalSourceIngestionMetadataService().build_metadata_contract(
            records if isinstance(records, list) else None
        ),
    }


@router.get("/legal-source-durable-index-plan")
@router.get("/legal-review-benchmark/source-durable-index-plan")
async def get_legal_source_durable_index_plan():
    """Return legal source durable index planning metadata."""
    return {
        "success": True,
        "data": LegalSourceDurableIndexPlanService().build_plan(),
    }


@router.post("/legal-source-durable-index-plan")
@router.post("/legal-review-benchmark/source-durable-index-plan")
async def evaluate_legal_source_durable_index_plan(payload: dict[str, Any]):
    """Evaluate metadata-only source records for durable index readiness."""
    records = payload.get("source_records")
    if not isinstance(records, list):
        records = payload.get("records")
    return {
        "success": True,
        "data": LegalSourceDurableIndexPlanService().build_plan(
            records if isinstance(records, list) else None
        ),
    }


@router.get("/legal-review-benchmark/quick-suite")
async def get_legal_review_fixture_quick_suite(
    fixture_limit: int = Query(default=3, ge=1, le=4, description="Number of small local fixtures to include."),
):
    """Return the smallest laptop-safe legal fixture benchmark run plan."""
    return {
        "success": True,
        "data": LegalFixtureQuickSuiteService().build_suite(fixture_limit),
    }


@router.get("/legal-review-benchmark/fixture-smoke")
async def get_legal_review_fixture_smoke_template():
    """Return local synthetic legal document fixture smoke-test templates."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate_fixture_smoke(),
    }


@router.post("/legal-review-benchmark/fixture-smoke")
async def evaluate_legal_review_fixture_smoke(observations: dict[str, dict]):
    """Evaluate supplied legal fixture smoke-test observations."""
    service = LegalReviewBenchmarkService()
    return {
        "success": True,
        "data": service.evaluate_fixture_smoke(observations),
    }


@router.get("/legal-review-benchmark/fixture-improvements")
async def get_legal_review_fixture_improvement_template():
    """Return an empty legal fixture improvement plan template."""
    return {
        "success": True,
        "data": LegalFixtureImprovementService().build_plan(),
    }


@router.post("/legal-review-benchmark/fixture-improvements")
async def build_legal_review_fixture_improvement_plan(observations: dict[str, dict]):
    """Convert fixture smoke observations into prompt and report-schema improvement actions."""
    return {
        "success": True,
        "data": LegalFixtureImprovementService().build_plan(observations),
    }


@router.get("/legal-review-benchmark/prompt-pack")
async def get_legal_review_fixture_prompt_pack():
    """Return cheap-first model prompt payloads for local legal fixture evaluation."""
    return {
        "success": True,
        "data": LegalFixturePromptPackService().build_pack(),
    }


@router.get("/legal-review-benchmark/gateway-manifest")
async def get_legal_review_fixture_gateway_manifest():
    """Return safe OpenAI-compatible request manifests for local legal fixture evaluation."""
    return {
        "success": True,
        "data": LegalFixtureGatewayManifestService().build_manifest(),
    }


@router.get("/legal-review-benchmark/fixture-run-plan")
async def get_legal_review_fixture_run_plan():
    """Return a cheap-first local execution plan for legal fixture gateway requests."""
    return {
        "success": True,
        "data": LegalFixtureRunPlanService().build_plan(),
    }


@router.get("/legal-review-benchmark/local-run-package")
async def get_legal_review_fixture_local_run_package(
    fixture_limit: int = Query(default=2, ge=1, le=4, description="Number of cheap-first fixture request files to include."),
):
    """Return a one-at-a-time local gateway run package for low-resource machines."""
    return {
        "success": True,
        "data": LegalFixtureLocalRunPackageService().build_package(fixture_limit),
    }


@router.get("/legal-review-benchmark/micro-benchmark-preflight")
async def get_legal_review_micro_benchmark_preflight(
    fixture_limit: int = Query(default=2, ge=1, le=4, description="Number of cheap-first fixture rows."),
    document_case_limit: int = Query(default=2, ge=1, le=7, description="Number of document benchmark case rows."),
    fact_case_limit: int = Query(default=1, ge=1, le=4, description="Number of fact-consistency case rows."),
):
    """Return the smallest cheap-first legal benchmark preflight packet."""
    return {
        "success": True,
        "data": ModelOpsLegalMicroBenchmarkPreflightService().build_packet(
            fixture_limit,
            document_case_limit,
            fact_case_limit,
        ),
    }


@router.get("/legal-review-benchmark/local-response-normalizer")
async def get_legal_review_fixture_response_normalizer_template():
    """Return a template for normalizing local gateway responses into fixture observations."""
    return {
        "success": True,
        "data": LegalFixtureResponseNormalizerService().template(),
    }


@router.post("/legal-review-benchmark/local-response-normalizer")
async def normalize_legal_review_fixture_response(payload: dict[str, Any]):
    """Normalize local gateway responses into fixture-smoke and run-report payloads."""
    return {
        "success": True,
        "data": LegalFixtureResponseNormalizerService().normalize(payload),
    }


@router.get("/legal-review-benchmark/local-run-review")
async def get_legal_review_fixture_local_run_review_template():
    """Return a one-step template for reviewing local fixture gateway responses."""
    return {
        "success": True,
        "data": LegalFixtureLocalRunReviewService().template(),
    }


@router.post("/legal-review-benchmark/local-run-review")
async def review_legal_review_fixture_local_run(payload: dict[str, Any]):
    """Normalize and review local fixture gateway responses into release evidence."""
    return {
        "success": True,
        "data": LegalFixtureLocalRunReviewService().review(payload),
    }


@router.get("/legal-review-benchmark/fixture-run-report")
async def get_legal_review_fixture_run_report_template():
    """Return an empty cheap-first fixture run report template."""
    return {
        "success": True,
        "data": LegalFixtureRunReportService().build_report(),
    }


@router.get("/legal-review-benchmark/fixture-model-matrix")
async def get_legal_review_fixture_model_matrix():
    """Return fixture-level Gemini/NewAPI cheap-first candidate ladders."""
    return {
        "success": True,
        "data": LegalFixtureModelMatrixService().build_matrix(),
    }


@router.get("/legal-review-benchmark/cheap-first-benchmark-gate")
async def get_legal_review_fixture_cheap_first_benchmark_gate():
    """Return a metadata-only gate for cheap-first fixture default evidence."""
    return {
        "success": True,
        "data": ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(),
    }


@router.post("/legal-review-benchmark/cheap-first-benchmark-gate")
async def build_legal_review_fixture_cheap_first_benchmark_gate(payload: dict[str, Any]):
    """Evaluate normalized fixture observations before default-change evidence is allowed."""
    return {
        "success": True,
        "data": ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(payload),
    }


@router.get("/legal-review-benchmark/cheap-first-default-promotion-packet")
@router.get("/legal-review-benchmark/default-promotion-packet")
async def get_legal_review_fixture_default_promotion_packet():
    """Return a maintainer-only default promotion packet template for legal fixture evidence."""
    return {
        "success": True,
        "data": ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet(),
    }


@router.post("/legal-review-benchmark/cheap-first-default-promotion-packet")
@router.post("/legal-review-benchmark/default-promotion-packet")
async def build_legal_review_fixture_default_promotion_packet(payload: dict[str, Any]):
    """Build a metadata-only default promotion packet from legal fixture gate evidence."""
    return {
        "success": True,
        "data": ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet(payload),
    }


@router.get("/legal-review-benchmark/fixture-evidence-bundle")
async def get_legal_review_fixture_evidence_bundle_template():
    """Return a release evidence bundle for legal fixture maintenance."""
    return {
        "success": True,
        "data": LegalFixtureEvidenceBundleService().build_bundle(),
    }


@router.post("/legal-review-benchmark/fixture-run-report")
async def build_legal_review_fixture_run_report(payload: dict[str, dict]):
    """Summarize fixture observations into cheap-first release and escalation decisions."""
    return {
        "success": True,
        "data": LegalFixtureRunReportService().build_report(payload),
    }


@router.post("/legal-review-benchmark/fixture-evidence-bundle")
async def build_legal_review_fixture_evidence_bundle(payload: dict[str, dict]):
    """Bundle fixture observations, model routing, and validation evidence."""
    return {
        "success": True,
        "data": LegalFixtureEvidenceBundleService().build_bundle(payload),
    }


@router.get("/legal-review-benchmark/result-archive")
async def get_legal_review_fixture_result_archive_template():
    """Return a release-safe archive template for cheap-first fixture results."""
    return {
        "success": True,
        "data": LegalFixtureResultArchiveService().build_archive(),
    }


@router.post("/legal-review-benchmark/result-archive")
async def build_legal_review_fixture_result_archive(payload: dict[str, Any]):
    """Build a release-safe archive summary from normalized fixture observations."""
    return {
        "success": True,
        "data": LegalFixtureResultArchiveService().build_archive(payload),
    }


@router.get("/legal-review-benchmark/fixture-regression")
async def get_legal_review_fixture_regression_template():
    """Return a metadata-only baseline/current fixture regression comparison template."""
    return {
        "success": True,
        "data": LegalFixtureRegressionService().build_comparison(),
    }


@router.post("/legal-review-benchmark/fixture-regression")
async def compare_legal_review_fixture_regression(payload: dict[str, Any]):
    """Compare baseline and current cheap-first fixture runs without raw output echo."""
    return {
        "success": True,
        "data": LegalFixtureRegressionService().build_comparison(payload),
    }


@router.get("/release-readiness")
async def get_release_readiness():
    """Return the default release checklist before validation results are supplied."""
    service = ReleaseReadinessService()
    return {
        "success": True,
        "data": service.evaluate(),
        "validation_commands": service.default_validation_commands(),
    }


@router.post("/release-readiness")
async def evaluate_release_readiness(validation_results: dict[str, str]):
    """Evaluate release readiness from explicit check results."""
    service = ReleaseReadinessService()
    return {
        "success": True,
        "data": service.evaluate(validation_results),
        "validation_commands": service.default_validation_commands(),
    }
