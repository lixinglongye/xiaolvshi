from typing import Any, Literal

from fastapi import APIRouter, Query
from services.billing_entitlement_gap import BillingEntitlementGapService
from services.case_evidence_graph import CaseEvidenceGraphService
from services.case_intake_completeness import CaseIntakeCompletenessService
from services.case_timeline_deadline_risk import CaseTimelineDeadlineRiskService
from services.case_team_access_policy import CaseTeamAccessPolicyService
from services.case_task_notification_policy import CaseTaskNotificationPolicyService
from services.client_delivery_risk_checklist import ClientDeliveryRiskChecklistService
from services.continuous_update_ledger import ContinuousUpdateLedgerService
from services.evidence_exhibit_package_policy import EvidenceExhibitPackagePolicyService
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
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
from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_document_export_readiness import LegalDocumentExportReadinessService
from services.legal_document_template_matrix import LegalDocumentTemplateMatrixService
from services.lawyer_review_workflow_policy import LawyerReviewWorkflowPolicyService
from services.legal_external_research_digest import LegalExternalResearchDigestService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_research_backlog import LegalResearchBacklogService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.maintenance_evidence import MaintenanceEvidenceService
from services.matter_audit_retention_policy import MatterAuditRetentionPolicyService
from services.ocr_import_readiness_policy import OcrImportReadinessPolicyService
from services.product_feature_gap_radar import ProductFeatureGapRadarService
from services.release_readiness import ReleaseReadinessService
from services.user_needs_radar import UserNeedsRadarService


router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


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


@router.get("/feedback-roadmap")
async def get_feedback_roadmap_mapping():
    """Return feedback-to-roadmap mapping rules for maintenance planning."""
    return {
        "success": True,
        "data": FeedbackRoadmapAlignmentService().build_mapping_catalog(),
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
