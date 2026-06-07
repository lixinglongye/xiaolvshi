"""
AI Hub router module.
Provides text, image, video, audio, PDF analysis,
and speech transcription API endpoints.
"""

import ast
from copy import deepcopy
import json
import logging
from time import monotonic
from typing import Any

from fastapi import APIRouter, HTTPException, status
from schemas.aihub import (
    AnalyzePdfRequest,
    AnalyzePdfResponse,
    GenAudioRequest,
    GenAudioResponse,
    GenImgRequest,
    GenImgResponse,
    GenTxtRequest,
    GenVideoRequest,
    GenVideoResponse,
    TranscribeAudioRequest,
    TranscribeAudioResponse,
)
from services.aihub import (
    AIHubService,
    InvalidAudioInputError,
    InvalidImageInputError,
    InvalidPdfInputError,
)
from services.gemini_newapi_alias_capability_coverage import GeminiNewapiAliasCapabilityCoverageService
from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_budget import budget_policy_for_api
from services.model_callsite_audit import ModelCallsiteAuditService
from services.model_cache_policy import ModelCachePolicyService
from services.model_catalog_candidate_impact_replay import ModelCatalogCandidateImpactReplayService
from services.model_catalog_candidate_patch_plan import ModelCatalogCandidatePatchPlanService
from services.model_catalog_source_audit import ModelCatalogSourceAuditService
from services.model_catalog import catalog_for_api, task_default_model
from services.model_configuration_audit import ModelConfigurationAuditService
from services.model_cost_forecast import ModelCostForecastService
from services.model_cost_guardrails import ModelCostGuardrailService
from services.model_default_optimization import ModelDefaultOptimizationService
from services.model_default_recommendation_snapshot import ModelDefaultRecommendationSnapshotService
from services.model_default_template_audit import ModelDefaultTemplateAuditService
from services.model_escalation_policy import ModelEscalationPolicyService
from services.model_fallback_chains import ModelFallbackChainService
from services.model_failure_upgrade_budget import ModelFailureUpgradeBudgetService
from services.model_gateway_compatibility import ModelGatewayCompatibilityService
from services.model_gateway_connection_profile import ModelGatewayConnectionProfileService
from services.model_gateway_health_plan import ModelGatewayHealthPlanService
from services.model_gateway_probe_evaluation import ModelGatewayProbeEvaluationService, model_gateway_probe_evaluation_registry
from services.model_gateway_request_compatibility_gate import ModelGatewayRequestCompatibilityGateService
from services.model_lifecycle_policy import ModelLifecyclePolicyService
from services.modelops_gemini_cheap_first_coverage_gate import ModelOpsGeminiCheapFirstCoverageGateService
from services.model_ops_gemini_cheap_first_route_preflight import (
    ModelOpsGeminiCheapFirstRoutePreflightService,
)
from services.model_ops_aihub_endpoint_route_coverage_gate import (
    ModelOpsAIHubEndpointRouteCoverageGateService,
)
from services.model_ops_gentxt_task_guard import ModelOpsGenTxtTaskGuardService
from services.model_ops_runtime_explicit_model_fit_gate import ModelOpsRuntimeExplicitModelFitGateService
from services.model_ops_readiness import ModelOpsReadinessService
from services.model_ops_cheap_first_escalation_budget import ModelOpsCheapFirstEscalationBudgetService
from services.model_ops_cheap_first_release_decision import ModelOpsCheapFirstReleaseDecisionService
from services.model_ops_cheap_first_canary_approval_packet import ModelOpsCheapFirstCanaryApprovalPacketService
from services.model_ops_cheap_first_canary_change_manifest import ModelOpsCheapFirstCanaryChangeManifestService
from services.model_ops_cheap_first_canary_observation import ModelOpsCheapFirstCanaryObservationService
from services.model_ops_cheap_first_canary_plan import ModelOpsCheapFirstCanaryPlanService
from services.model_ops_cheap_first_canary_promotion_decision import ModelOpsCheapFirstCanaryPromotionDecisionService
from services.model_ops_cheap_first_canary_rollback_drill import ModelOpsCheapFirstCanaryRollbackDrillService
from services.model_ops_cheap_first_maintainer_execution_checklist import (
    ModelOpsCheapFirstMaintainerExecutionChecklistService,
)
from services.model_ops_cheap_first_priority_queue import ModelOpsCheapFirstPriorityQueueService
from services.model_ops_default_change_queue import ModelOpsDefaultChangeQueueService
from services.model_ops_gemini_default_change_review import ModelOpsGeminiDefaultChangeReviewService
from services.model_ops_gemini_default_cost_impact import ModelOpsGeminiDefaultCostImpactService
from services.model_ops_legal_benchmark_risk_bridge import ModelOpsLegalBenchmarkRiskBridgeService
from services.model_ops_observed_gemini_coverage_gap_queue import ModelOpsObservedGeminiCoverageGapQueueService
from services.model_ops_observed_gemini_model_intake_queue import ModelOpsObservedGeminiModelIntakeQueueService
from services.model_ops_performance_budget import (
    ModelOpsPerformanceBudgetService,
    model_ops_performance_budget_registry,
)
from services.modelops_observed_gateway_model_fit_matrix import ModelOpsObservedGatewayModelFitMatrixService
from services.modelops_legal_micro_benchmark_preflight import ModelOpsLegalMicroBenchmarkPreflightService
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService
from services.model_routing_replay import ModelRoutingReplayService
from services.model_request_cost_bounds import ModelRequestCostBoundsService
from services.model_runtime_router import runtime_router_policy_for_api
from services.model_reasoning_policy import reasoning_policy_for_api
from services.model_request_policy import generation_request_policy_for_api
from services.model_route_guardrails import ModelRouteGuardrailService
from services.model_route_quality_budget import ModelRouteQualityBudgetService
from services.model_route_telemetry import model_route_telemetry_registry
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService
from services.route_telemetry_remediation_plan import RouteTelemetryRemediationPlanService
from services.model_usage import model_usage_registry
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS = 10.0
_model_ops_payload_cache: dict[str, Any] | None = None
_model_ops_payload_cache_at = 0.0
_model_ops_payload_cache_probe_version = -1
_model_ops_payload_cache_route_telemetry_version = -1
_model_ops_payload_cache_performance_version = -1


def _clear_model_ops_payload_cache() -> None:
    global _model_ops_payload_cache, _model_ops_payload_cache_at, _model_ops_payload_cache_probe_version
    global _model_ops_payload_cache_route_telemetry_version, _model_ops_payload_cache_performance_version
    _model_ops_payload_cache = None
    _model_ops_payload_cache_at = 0.0
    _model_ops_payload_cache_probe_version = -1
    _model_ops_payload_cache_route_telemetry_version = -1
    _model_ops_payload_cache_performance_version = -1


def _try_extract_message_from_dict(data: dict) -> str | None:
    """Try to extract message field from a dictionary."""
    # Try to extract error.message format
    if "error" in data and isinstance(data["error"], dict):
        if "message" in data["error"]:
            return data["error"]["message"]
    # Try to extract message field directly
    if "message" in data:
        return data["message"]
    return None


def _try_parse_dict(s: str) -> dict | None:
    """
    Try to parse a string as a dictionary.
    First attempts JSON parsing, then falls back to Python literal eval (for single quotes).
    """
    # Try JSON parsing (double quotes format)
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    # Try Python literal eval (single quotes format)
    try:
        data = ast.literal_eval(s)
        if isinstance(data, dict):
            return data
    except (ValueError, SyntaxError, TypeError):
        pass

    return None


def extract_error_message(error: Any) -> str:
    """
    Extract a readable error message from an error object.
    Attempts to parse JSON/Python dict format and extract the message field.
    Falls back to the full error string if parsing fails.

    Supported formats:
    - Pure JSON: {"error": {"message": "..."}}
    - Python dict: {'error': {'message': '...'}}
    - With prefix: Error code: 400 - {'error': {'message': '...'}}

    Args:
        error: Error object, can be an Exception or other types

    Returns:
        Extracted error message string
    """
    error_str = str(error)

    # Try to parse the entire string directly
    error_data = _try_parse_dict(error_str)
    if error_data:
        message = _try_extract_message_from_dict(error_data)
        if message:
            return message

    # Try to extract dict portion from string (handles "Error code: 400 - {...}" format)
    start_idx = error_str.find("{")
    end_idx = error_str.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        dict_str = error_str[start_idx : end_idx + 1]
        error_data = _try_parse_dict(dict_str)
        if error_data:
            message = _try_extract_message_from_dict(error_data)
            if message:
                return message

    # If parsing fails, return the original error string
    return error_str


router = APIRouter(prefix="/api/v1/aihub", tags=["aihub"])


def _model_ops_performance_budget_input(observations: Any = None) -> dict[str, Any]:
    data = {
        "models_payload_cache_enabled": True,
        "backend_cache_ttl_seconds": MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS,
        "same_origin_fetch_first": True,
        "fallback_after_timeout_disabled": True,
        "duplicate_calibration_fetch_removed": True,
        "frontend_abort_controller_required": True,
    }
    if observations is not None:
        data["observations"] = observations
    return data


def _observed_gateway_model_ids(gateway_compatibility: dict[str, Any] | None = None) -> list[Any]:
    gateway_compatibility = gateway_compatibility or ModelGatewayCompatibilityService().evaluate()
    return [
        item.get("model")
        for item in gateway_compatibility.get("configured_roles", []) + gateway_compatibility.get("gateway_examples", [])
        if item.get("model")
    ]


@router.get("/models")
async def list_models():
    """
    Return the configured model catalog and task routing defaults.

    NewAPI and Gemini OpenAI-compatible gateways may expose additional model
    names; those can still be sent directly in request payloads.
    """
    global _model_ops_payload_cache, _model_ops_payload_cache_at, _model_ops_payload_cache_probe_version
    global _model_ops_payload_cache_route_telemetry_version, _model_ops_payload_cache_performance_version

    now = monotonic()
    gateway_probe_version = model_gateway_probe_evaluation_registry.version
    route_telemetry_version = model_route_telemetry_registry.version
    performance_observation_version = model_ops_performance_budget_registry.version
    if (
        _model_ops_payload_cache is not None
        and _model_ops_payload_cache_probe_version == gateway_probe_version
        and _model_ops_payload_cache_route_telemetry_version == route_telemetry_version
        and _model_ops_payload_cache_performance_version == performance_observation_version
        and now - _model_ops_payload_cache_at <= MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS
    ):
        return deepcopy(_model_ops_payload_cache)

    usage = model_usage_registry.snapshot()
    forecast = ModelCostForecastService().build_forecast()
    route_telemetry = model_route_telemetry_registry.snapshot()
    route_telemetry_repository = RouteTelemetryRepositoryService().build_repository()
    route_telemetry_ops_summary = RouteTelemetryOpsSummaryService().build_summary(route_telemetry_repository)
    route_telemetry_triage = RouteTelemetryTriageQueueService().build_queue(route_telemetry_ops_summary)
    runtime_router = runtime_router_policy_for_api()
    model_configuration_audit = ModelConfigurationAuditService().audit()
    default_template_audit = ModelDefaultTemplateAuditService().build_audit()
    reasoning_policy = reasoning_policy_for_api()
    request_policy = generation_request_policy_for_api()
    gateway_request_compatibility_gate = ModelGatewayRequestCompatibilityGateService().build_gate()
    route_guardrails = ModelRouteGuardrailService().evaluate(route_telemetry)
    callsite_audit = ModelCallsiteAuditService().audit()
    budget_policy = budget_policy_for_api()
    capability_matrix = ModelCapabilityMatrixService().build_matrix()
    escalation_policy = ModelEscalationPolicyService().build_policy()
    fallback_chains = ModelFallbackChainService().build_chains()
    failure_upgrade_budget = ModelFailureUpgradeBudgetService().build_decision()
    routing_replay = ModelRoutingReplayService().run_replay()
    cost_guardrails = ModelCostGuardrailService().evaluate(usage, forecast)
    default_optimization = ModelDefaultOptimizationService().build_plan(capability_matrix, forecast)
    route_telemetry_remediation = RouteTelemetryRemediationPlanService().build_plan(
        route_telemetry_triage,
        default_optimization,
    )
    gateway_compatibility = ModelGatewayCompatibilityService().evaluate()
    observed_gateway_models = _observed_gateway_model_ids(gateway_compatibility)
    default_recommendation_snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot(observed_gateway_models)
    gateway_connection_profile = ModelGatewayConnectionProfileService().build_profile()
    gateway_health_plan = ModelGatewayHealthPlanService().build_plan()
    gateway_probe_evaluation = model_gateway_probe_evaluation_registry.latest()
    request_cost_bounds = ModelRequestCostBoundsService().evaluate()
    cache_policy = ModelCachePolicyService().build_policy(forecast)
    lifecycle_policy = ModelLifecyclePolicyService().build_policy()
    cheap_first_calibration = GeminiNewapiCheapFirstCalibrationService().build_calibration()
    gemini_variant_matrix = GeminiModelVariantMatrixService().build_matrix(
        {"observed_models": observed_gateway_models}
    )
    catalog_source_audit = ModelCatalogSourceAuditService().build_audit()
    price_refresh_monitor = ModelPriceRefreshMonitorService().build_monitor(
        observed_gateway_models,
        forecast,
    )
    observed_gemini_model_intake_queue = ModelOpsObservedGeminiModelIntakeQueueService().build_queue(
        {"observed_models": observed_gateway_models}
    )
    observed_gemini_coverage_gap_queue = ModelOpsObservedGeminiCoverageGapQueueService().build_queue(
        {"observed_models": observed_gateway_models}
    )
    observed_gateway_model_fit_matrix = ModelOpsObservedGatewayModelFitMatrixService().build_matrix(
        {"observed_models": observed_gateway_models}
    )
    runtime_explicit_model_fit_gate = ModelOpsRuntimeExplicitModelFitGateService().build_gate(
        {
            "observed_models": observed_gateway_models,
            "observed_gateway_model_fit_matrix": observed_gateway_model_fit_matrix,
        }
    )
    gemini_newapi_alias_capability_coverage = GeminiNewapiAliasCapabilityCoverageService().build_coverage(
        {"observed_models": observed_gateway_models}
    )
    catalog_candidate_patch_plan = ModelCatalogCandidatePatchPlanService().build_plan(
        signals={
            "gateway_probe_evaluation": gateway_probe_evaluation,
            "observed_gemini_model_intake_queue": observed_gemini_model_intake_queue,
        }
    )
    catalog_candidate_impact_replay = ModelCatalogCandidateImpactReplayService().build_replay(
        signals={
            "catalog_candidate_patch_plan": catalog_candidate_patch_plan,
        }
    )
    gemini_cheap_first_coverage_gate = ModelOpsGeminiCheapFirstCoverageGateService().build_gate(
        {
            "capability_matrix": capability_matrix,
            "lifecycle_policy": lifecycle_policy,
            "gateway_compatibility": gateway_compatibility,
        }
    )
    gemini_cheap_first_route_preflight = ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight(
        {
            "observed_models": observed_gateway_models,
            "gemini_variant_matrix": gemini_variant_matrix,
            "gemini_newapi_alias_capability_coverage": gemini_newapi_alias_capability_coverage,
            "gemini_cheap_first_coverage_gate": gemini_cheap_first_coverage_gate,
        }
    )
    aihub_endpoint_route_coverage_gate = ModelOpsAIHubEndpointRouteCoverageGateService().build_gate()
    gentxt_routing_guard = ModelOpsGenTxtTaskGuardService().build_gate()
    route_quality_budget = ModelRouteQualityBudgetService().build_budget()
    cheap_first_escalation_budget = ModelOpsCheapFirstEscalationBudgetService().build_budget()
    default_model_ops_performance_budget = ModelOpsPerformanceBudgetService().build_budget(
        _model_ops_performance_budget_input(),
        cache_ttl_seconds=MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS,
    )
    model_ops_performance_budget = (
        model_ops_performance_budget_registry.latest() or default_model_ops_performance_budget
    )
    legal_micro_benchmark_preflight = ModelOpsLegalMicroBenchmarkPreflightService().build_packet()
    model_ops_signals = {
        "runtime_router": runtime_router,
        "model_configuration_audit": model_configuration_audit,
        "default_template_audit": default_template_audit,
        "default_optimization": default_optimization,
        "default_recommendation_snapshot": default_recommendation_snapshot,
        "gateway_compatibility": gateway_compatibility,
        "gateway_connection_profile": gateway_connection_profile,
        "gateway_health_plan": gateway_health_plan,
        "gateway_probe_evaluation": gateway_probe_evaluation,
        "lifecycle_policy": lifecycle_policy,
        "request_cost_bounds": request_cost_bounds,
        "cache_policy": cache_policy,
        "reasoning_policy": reasoning_policy,
        "request_policy": request_policy,
        "gateway_request_compatibility_gate": gateway_request_compatibility_gate,
        "route_telemetry": route_telemetry,
        "route_telemetry_repository": route_telemetry_repository,
        "route_telemetry_ops_summary": route_telemetry_ops_summary,
        "route_telemetry_triage": route_telemetry_triage,
        "route_telemetry_remediation": route_telemetry_remediation,
        "route_guardrails": route_guardrails,
        "callsite_audit": callsite_audit,
        "budget_policy": budget_policy,
        "capability_matrix": capability_matrix,
        "escalation_policy": escalation_policy,
        "fallback_chains": fallback_chains,
        "failure_upgrade_budget": failure_upgrade_budget,
        "routing_replay": routing_replay,
        "cost_forecast": forecast,
        "cost_guardrails": cost_guardrails,
        "cheap_first_calibration": cheap_first_calibration,
        "gemini_variant_matrix": gemini_variant_matrix,
        "catalog_source_audit": catalog_source_audit,
        "price_refresh_monitor": price_refresh_monitor,
        "observed_gemini_model_intake_queue": observed_gemini_model_intake_queue,
        "observed_gemini_coverage_gap_queue": observed_gemini_coverage_gap_queue,
        "observed_gateway_model_fit_matrix": observed_gateway_model_fit_matrix,
        "runtime_explicit_model_fit_gate": runtime_explicit_model_fit_gate,
        "gemini_newapi_alias_capability_coverage": gemini_newapi_alias_capability_coverage,
        "catalog_candidate_patch_plan": catalog_candidate_patch_plan,
        "catalog_candidate_impact_replay": catalog_candidate_impact_replay,
        "gemini_cheap_first_coverage_gate": gemini_cheap_first_coverage_gate,
        "gemini_cheap_first_route_preflight": gemini_cheap_first_route_preflight,
        "aihub_endpoint_route_coverage_gate": aihub_endpoint_route_coverage_gate,
        "gentxt_routing_guard": gentxt_routing_guard,
        "route_quality_budget": route_quality_budget,
        "cheap_first_escalation_budget": cheap_first_escalation_budget,
        "model_ops_performance_budget": model_ops_performance_budget,
        "legal_micro_benchmark_preflight": legal_micro_benchmark_preflight,
    }
    base_model_ops_readiness = ModelOpsReadinessService().evaluate(model_ops_signals)
    model_ops_signals["model_ops_readiness"] = base_model_ops_readiness
    cheap_first_release_decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(model_ops_signals)
    model_ops_signals["cheap_first_release_decision"] = cheap_first_release_decision
    default_change_queue = ModelOpsDefaultChangeQueueService().build_queue(model_ops_signals)
    model_ops_signals["default_change_queue"] = default_change_queue
    legal_benchmark_risk_bridge = ModelOpsLegalBenchmarkRiskBridgeService().build_bridge(model_ops_signals)
    model_ops_signals["legal_benchmark_risk_bridge"] = legal_benchmark_risk_bridge
    cheap_first_priority_queue = ModelOpsCheapFirstPriorityQueueService().build_queue(model_ops_signals)
    model_ops_signals["cheap_first_priority_queue"] = cheap_first_priority_queue
    gemini_default_change_review = ModelOpsGeminiDefaultChangeReviewService().build_review()
    model_ops_signals["gemini_default_change_review"] = gemini_default_change_review
    gemini_default_cost_impact = ModelOpsGeminiDefaultCostImpactService().build_impact()
    model_ops_signals["gemini_default_cost_impact"] = gemini_default_cost_impact
    cheap_first_canary_plan = ModelOpsCheapFirstCanaryPlanService().build_plan(model_ops_signals)
    model_ops_signals["cheap_first_canary_plan"] = cheap_first_canary_plan
    cheap_first_canary_observation = ModelOpsCheapFirstCanaryObservationService().build_review(None, model_ops_signals)
    model_ops_signals["cheap_first_canary_observation"] = cheap_first_canary_observation
    cheap_first_canary_promotion_decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(model_ops_signals)
    model_ops_signals["cheap_first_canary_promotion_decision"] = cheap_first_canary_promotion_decision
    cheap_first_canary_approval_packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(model_ops_signals)
    model_ops_signals["cheap_first_canary_approval_packet"] = cheap_first_canary_approval_packet
    cheap_first_canary_rollback_drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(model_ops_signals)
    model_ops_signals["cheap_first_canary_rollback_drill"] = cheap_first_canary_rollback_drill
    cheap_first_canary_change_manifest = ModelOpsCheapFirstCanaryChangeManifestService().build_manifest(model_ops_signals)
    model_ops_signals["cheap_first_canary_change_manifest"] = cheap_first_canary_change_manifest
    cheap_first_maintainer_execution_checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(
        model_ops_signals
    )
    model_ops_signals["cheap_first_maintainer_execution_checklist"] = cheap_first_maintainer_execution_checklist
    model_ops_readiness = ModelOpsReadinessService().evaluate(model_ops_signals)
    payload = {
        "success": True,
        "routing_aliases": {
            "auto-fast": task_default_model("fast"),
            "auto-cheap": task_default_model("cheap"),
            "auto-ocr": task_default_model("ocr"),
            "auto-review": task_default_model("review"),
            "auto-pdf": task_default_model("pdf"),
            "auto-image": task_default_model("image"),
            "auto-video": task_default_model("video"),
            "auto-audio": task_default_model("audio"),
            "auto-transcription": task_default_model("transcription"),
            "auto-agentic": task_default_model("agentic"),
            "auto-grounded-research": task_default_model("grounded-research"),
        },
        "model_ops_readiness": model_ops_readiness,
        "runtime_router": runtime_router,
        "model_configuration_audit": model_configuration_audit,
        "default_template_audit": default_template_audit,
        "default_optimization": default_optimization,
        "default_recommendation_snapshot": default_recommendation_snapshot,
        "gateway_compatibility": gateway_compatibility,
        "gateway_connection_profile": gateway_connection_profile,
        "gateway_health_plan": gateway_health_plan,
        "gateway_probe_evaluation": gateway_probe_evaluation,
        "lifecycle_policy": lifecycle_policy,
        "request_cost_bounds": request_cost_bounds,
        "cache_policy": cache_policy,
        "reasoning_policy": reasoning_policy,
        "request_policy": request_policy,
        "gateway_request_compatibility_gate": gateway_request_compatibility_gate,
        "route_telemetry": route_telemetry,
        "route_telemetry_repository": route_telemetry_repository,
        "route_telemetry_ops_summary": route_telemetry_ops_summary,
        "route_telemetry_triage": route_telemetry_triage,
        "route_telemetry_remediation": route_telemetry_remediation,
        "route_guardrails": route_guardrails,
        "callsite_audit": callsite_audit,
        "budget_policy": budget_policy,
        "capability_matrix": capability_matrix,
        "escalation_policy": escalation_policy,
        "fallback_chains": fallback_chains,
        "failure_upgrade_budget": failure_upgrade_budget,
        "routing_replay": routing_replay,
        "cost_forecast": forecast,
        "cost_guardrails": cost_guardrails,
        "cheap_first_calibration": cheap_first_calibration,
        "gemini_variant_matrix": gemini_variant_matrix,
        "catalog_source_audit": catalog_source_audit,
        "price_refresh_monitor": price_refresh_monitor,
        "observed_gemini_model_intake_queue": observed_gemini_model_intake_queue,
        "observed_gemini_coverage_gap_queue": observed_gemini_coverage_gap_queue,
        "observed_gateway_model_fit_matrix": observed_gateway_model_fit_matrix,
        "runtime_explicit_model_fit_gate": runtime_explicit_model_fit_gate,
        "gemini_newapi_alias_capability_coverage": gemini_newapi_alias_capability_coverage,
        "catalog_candidate_patch_plan": catalog_candidate_patch_plan,
        "catalog_candidate_impact_replay": catalog_candidate_impact_replay,
        "gemini_cheap_first_coverage_gate": gemini_cheap_first_coverage_gate,
        "gemini_cheap_first_route_preflight": gemini_cheap_first_route_preflight,
        "aihub_endpoint_route_coverage_gate": aihub_endpoint_route_coverage_gate,
        "gentxt_routing_guard": gentxt_routing_guard,
        "route_quality_budget": route_quality_budget,
        "cheap_first_escalation_budget": cheap_first_escalation_budget,
        "model_ops_performance_budget": model_ops_performance_budget,
        "legal_micro_benchmark_preflight": legal_micro_benchmark_preflight,
        "cheap_first_release_decision": cheap_first_release_decision,
        "default_change_queue": default_change_queue,
        "legal_benchmark_risk_bridge": legal_benchmark_risk_bridge,
        "cheap_first_priority_queue": cheap_first_priority_queue,
        "gemini_default_change_review": gemini_default_change_review,
        "gemini_default_cost_impact": gemini_default_cost_impact,
        "cheap_first_canary_plan": cheap_first_canary_plan,
        "cheap_first_canary_observation": cheap_first_canary_observation,
        "cheap_first_canary_promotion_decision": cheap_first_canary_promotion_decision,
        "cheap_first_canary_approval_packet": cheap_first_canary_approval_packet,
        "cheap_first_canary_rollback_drill": cheap_first_canary_rollback_drill,
        "cheap_first_canary_change_manifest": cheap_first_canary_change_manifest,
        "cheap_first_maintainer_execution_checklist": cheap_first_maintainer_execution_checklist,
        "models": catalog_for_api(),
        "usage": usage,
    }
    _model_ops_payload_cache = deepcopy(payload)
    _model_ops_payload_cache_at = monotonic()
    _model_ops_payload_cache_probe_version = gateway_probe_version
    _model_ops_payload_cache_route_telemetry_version = route_telemetry_version
    _model_ops_payload_cache_performance_version = performance_observation_version
    return payload


@router.get("/models/usage")
async def model_usage():
    """Return in-process aggregate model usage without prompts, files, or secrets."""
    return {
        "success": True,
        "usage": model_usage_registry.snapshot(),
    }


@router.get("/models/gateway-probe-template")
async def gateway_probe_template():
    """Return the sanitized payload shape for evaluating manual gateway probes."""
    return {
        "success": True,
        "data": ModelGatewayProbeEvaluationService().template(),
    }


@router.post("/models/gateway-probe-evaluation")
async def evaluate_gateway_probe(payload: dict[str, Any]):
    """Evaluate sanitized gateway model-list, tiny chat, and image smoke probe results."""
    result = ModelGatewayProbeEvaluationService().evaluate(payload)
    model_gateway_probe_evaluation_registry.record(result)
    _clear_model_ops_payload_cache()
    return {
        "success": True,
        "data": result,
    }


@router.get("/models/gateway-connection-profile")
async def model_gateway_connection_profile():
    """Return safe OpenAI-compatible gateway connection profile evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gateway_connection_profile"],
    }


@router.post("/models/gateway-connection-profile")
async def evaluate_model_gateway_connection_profile(payload: dict[str, Any]):
    """Evaluate sanitized gateway URL/key-presence metadata without network calls."""
    return {
        "success": True,
        "data": ModelGatewayConnectionProfileService().build_profile(payload),
    }


@router.get("/models/cheap-first-calibration")
async def cheap_first_calibration():
    """Return metadata-only Gemini/NewAPI cheap-first calibration evidence."""
    return {
        "success": True,
        "data": GeminiNewapiCheapFirstCalibrationService().build_calibration(),
    }


@router.post("/models/cheap-first-calibration")
async def evaluate_cheap_first_calibration(payload: dict[str, Any]):
    """Evaluate sanitized cheap-first calibration metadata without calling NewAPI."""
    return {
        "success": True,
        "data": GeminiNewapiCheapFirstCalibrationService().build_calibration(payload),
    }


@router.get("/models/gemini-variant-matrix")
async def gemini_variant_matrix():
    """Return metadata-only Gemini/NewAPI variant routing matrix evidence."""
    return {
        "success": True,
        "data": GeminiModelVariantMatrixService().build_matrix(),
    }


@router.post("/models/gemini-variant-matrix")
async def evaluate_gemini_variant_matrix(payload: dict[str, Any]):
    """Evaluate observed Gemini-like model ids without calling NewAPI."""
    return {
        "success": True,
        "data": GeminiModelVariantMatrixService().build_matrix(payload),
    }


@router.get("/models/gemini-newapi-alias-capability-coverage")
async def gemini_newapi_alias_capability_coverage():
    """Return metadata-only alias capability coverage for Gemini/NewAPI model ids."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gemini_newapi_alias_capability_coverage"],
    }


@router.post("/models/gemini-newapi-alias-capability-coverage")
async def evaluate_gemini_newapi_alias_capability_coverage(payload: dict[str, Any]):
    """Evaluate sanitized Gemini/NewAPI aliases against local capability metadata."""
    return {
        "success": True,
        "data": GeminiNewapiAliasCapabilityCoverageService().build_coverage(payload),
    }


@router.get("/models/observed-gemini-model-intake-queue")
async def model_ops_observed_gemini_model_intake_queue():
    """Return metadata-only intake queue for observed Gemini-like model ids."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["observed_gemini_model_intake_queue"],
    }


@router.post("/models/observed-gemini-model-intake-queue")
async def evaluate_model_ops_observed_gemini_model_intake_queue(payload: dict[str, Any]):
    """Evaluate observed Gemini-like model ids before default promotion."""
    return {
        "success": True,
        "data": ModelOpsObservedGeminiModelIntakeQueueService().build_queue(payload),
    }


@router.get("/models/observed-gemini-coverage-gap-queue")
async def model_ops_observed_gemini_coverage_gap_queue():
    """Return metadata-only Gemini family and cheap-first task coverage gaps."""
    observed_gateway_models = _observed_gateway_model_ids()
    return {
        "success": True,
        "data": ModelOpsObservedGeminiCoverageGapQueueService().build_queue(
            {"observed_models": observed_gateway_models}
        ),
    }


@router.post("/models/observed-gemini-coverage-gap-queue")
async def evaluate_model_ops_observed_gemini_coverage_gap_queue(payload: dict[str, Any]):
    """Evaluate sanitized observed Gemini ids into family and cheap-first task coverage gaps."""
    return {
        "success": True,
        "data": ModelOpsObservedGeminiCoverageGapQueueService().build_queue(payload),
    }


@router.get("/models/observed-gateway-model-fit-matrix")
async def modelops_observed_gateway_model_fit_matrix():
    """Return metadata-only observed gateway model task-fit matrix evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["observed_gateway_model_fit_matrix"],
    }


@router.post("/models/observed-gateway-model-fit-matrix")
async def evaluate_modelops_observed_gateway_model_fit_matrix(payload: dict[str, Any]):
    """Evaluate sanitized gateway model inventory against cheap-first task fit."""
    return {
        "success": True,
        "data": ModelOpsObservedGatewayModelFitMatrixService().build_matrix(payload),
    }


@router.get("/models/runtime-explicit-model-fit-gate")
async def modelops_runtime_explicit_model_fit_gate():
    """Return metadata-only runtime explicit model fit evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["runtime_explicit_model_fit_gate"],
    }


@router.post("/models/runtime-explicit-model-fit-gate")
async def evaluate_modelops_runtime_explicit_model_fit_gate(payload: dict[str, Any]):
    """Evaluate sanitized explicit runtime model scenarios before live routing reliance."""
    return {
        "success": True,
        "data": ModelOpsRuntimeExplicitModelFitGateService().build_gate(payload),
    }


@router.get("/models/catalog-candidate-patch-plan")
async def model_catalog_candidate_patch_plan():
    """Return metadata-only catalog patch candidates for observed Gemini-like ids."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["catalog_candidate_patch_plan"],
    }


@router.post("/models/catalog-candidate-patch-plan")
async def evaluate_model_catalog_candidate_patch_plan(payload: dict[str, Any]):
    """Evaluate sanitized observed model ids into catalog patch candidates."""
    return {
        "success": True,
        "data": ModelCatalogCandidatePatchPlanService().build_plan(payload),
    }


@router.get("/models/catalog-candidate-impact-replay")
async def model_catalog_candidate_impact_replay():
    """Return metadata-only virtual catalog impact replay for candidate Gemini ids."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["catalog_candidate_impact_replay"],
    }


@router.post("/models/catalog-candidate-impact-replay")
async def evaluate_model_catalog_candidate_impact_replay(payload: dict[str, Any]):
    """Replay sanitized candidate profiles without editing catalog or defaults."""
    patch_plan = ModelCatalogCandidatePatchPlanService().build_plan(payload)
    return {
        "success": True,
        "data": ModelCatalogCandidateImpactReplayService().build_replay(
            payload,
            signals={"catalog_candidate_patch_plan": patch_plan},
        ),
    }


@router.get("/models/gateway-request-compatibility-gate")
async def model_gateway_request_compatibility_gate():
    """Return metadata-only OpenAI-compatible Gemini request-shape gate evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gateway_request_compatibility_gate"],
    }


@router.post("/models/gateway-request-compatibility-gate")
async def evaluate_model_gateway_request_compatibility_gate(payload: dict[str, Any]):
    """Evaluate sanitized task/model request-shape metadata without sending requests."""
    return {
        "success": True,
        "data": ModelGatewayRequestCompatibilityGateService().build_gate(payload),
    }


@router.get("/models/catalog-source-audit")
async def model_catalog_source_audit():
    """Return metadata-only Gemini catalog source and default-role audit evidence."""
    return {
        "success": True,
        "data": ModelCatalogSourceAuditService().build_audit(),
    }


@router.get("/models/gemini-cheap-first-coverage-gate")
async def modelops_gemini_cheap_first_coverage_gate():
    """Return metadata-only Gemini cheap-first default coverage gate evidence."""
    return {
        "success": True,
        "data": ModelOpsGeminiCheapFirstCoverageGateService().build_gate(),
    }


@router.get("/models/gemini-cheap-first-route-preflight")
async def modelops_gemini_cheap_first_route_preflight():
    """Return metadata-only Gemini cheap-first route preflight evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gemini_cheap_first_route_preflight"],
    }


@router.post("/models/gemini-cheap-first-route-preflight")
async def evaluate_modelops_gemini_cheap_first_route_preflight(payload: dict[str, Any]):
    """Evaluate sanitized Gemini route preflight metadata without gateway calls."""
    return {
        "success": True,
        "data": ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight(payload),
    }


@router.get("/models/aihub-endpoint-route-coverage-gate")
async def modelops_aihub_endpoint_route_coverage_gate():
    """Return metadata-only AIHub endpoint route coverage evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["aihub_endpoint_route_coverage_gate"],
    }


@router.post("/models/aihub-endpoint-route-coverage-gate")
async def evaluate_modelops_aihub_endpoint_route_coverage_gate(payload: dict[str, Any]):
    """Evaluate metadata-only AIHub endpoint route coverage without provider calls."""
    return {
        "success": True,
        "data": ModelOpsAIHubEndpointRouteCoverageGateService().build_gate(payload),
    }


@router.get("/models/gentxt-routing-guard")
async def modelops_gentxt_routing_guard():
    """Return metadata-only gentxt routing guard evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gentxt_routing_guard"],
    }


@router.post("/models/gentxt-routing-guard")
async def evaluate_modelops_gentxt_routing_guard(payload: dict[str, Any]):
    """Evaluate metadata-only gentxt routing guard evidence without provider calls."""
    return {
        "success": True,
        "data": ModelOpsGenTxtTaskGuardService().build_gate(payload),
    }


@router.get("/models/cheap-first-release-decision")
async def model_ops_cheap_first_release_decision():
    """Return metadata-only cheap-first ModelOps release decision evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_release_decision"],
    }


@router.get("/models/default-change-queue")
async def model_ops_default_change_queue():
    """Return metadata-only queue for cheap-first default model changes."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["default_change_queue"],
    }


@router.get("/models/legal-benchmark-risk-bridge")
async def model_ops_legal_benchmark_risk_bridge():
    """Return metadata-only legal benchmark risk bridge for default reviews."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["legal_benchmark_risk_bridge"],
    }


@router.get("/models/legal-micro-benchmark-preflight")
async def model_ops_legal_micro_benchmark_preflight():
    """Return metadata-only low-resource legal benchmark preflight packet."""
    return {
        "success": True,
        "data": ModelOpsLegalMicroBenchmarkPreflightService().build_packet(),
    }


@router.get("/models/cheap-first-priority-queue")
async def model_ops_cheap_first_priority_queue():
    """Return ranked cheap-first ModelOps priority work."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_priority_queue"],
    }


@router.get("/models/gemini-default-change-review")
async def model_ops_gemini_default_change_review():
    """Return metadata-only review for proposed Gemini default changes."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gemini_default_change_review"],
    }


@router.post("/models/gemini-default-change-review")
async def evaluate_model_ops_gemini_default_change_review(payload: dict[str, Any]):
    """Evaluate sanitized default-change proposals without writing configuration."""
    return {
        "success": True,
        "data": ModelOpsGeminiDefaultChangeReviewService().build_review(payload),
    }


@router.get("/models/gemini-default-cost-impact")
async def model_ops_gemini_default_cost_impact():
    """Return metadata-only cost impact for proposed Gemini default changes."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["gemini_default_cost_impact"],
    }


@router.post("/models/gemini-default-cost-impact")
async def evaluate_model_ops_gemini_default_cost_impact(payload: dict[str, Any]):
    """Evaluate default-change cost impact without writing configuration."""
    return {
        "success": True,
        "data": ModelOpsGeminiDefaultCostImpactService().build_impact(payload),
    }


@router.get("/models/cheap-first-canary-plan")
async def model_ops_cheap_first_canary_plan():
    """Return metadata-only canary plan for queued cheap-first default changes."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_plan"],
    }


@router.get("/models/cheap-first-canary-observation")
async def model_ops_cheap_first_canary_observation():
    """Return metadata-only canary observation review template evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_observation"],
    }


@router.post("/models/cheap-first-canary-observation")
async def evaluate_model_ops_cheap_first_canary_observation(payload: dict[str, Any]):
    """Evaluate sanitized aggregate canary observations without executing rollout."""
    models_payload = await list_models()
    observation = ModelOpsCheapFirstCanaryObservationService().build_review(
        payload,
        {"cheap_first_canary_plan": models_payload["cheap_first_canary_plan"]},
    )
    promotion_decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {
            "cheap_first_canary_plan": models_payload["cheap_first_canary_plan"],
            "cheap_first_canary_observation": observation,
        }
    )
    approval_packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion_decision}
    )
    rollback_drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion_decision,
            "cheap_first_canary_approval_packet": approval_packet,
        }
    )
    change_manifest = ModelOpsCheapFirstCanaryChangeManifestService().build_manifest(
        {
            "cheap_first_canary_plan": models_payload["cheap_first_canary_plan"],
            "cheap_first_canary_promotion_decision": promotion_decision,
            "cheap_first_canary_approval_packet": approval_packet,
            "cheap_first_canary_rollback_drill": rollback_drill,
        }
    )
    return {
        "success": True,
        "data": {
            **observation,
            "promotion_decision": promotion_decision,
            "approval_packet": approval_packet,
            "rollback_drill": rollback_drill,
            "change_manifest": change_manifest,
        },
    }


@router.get("/models/cheap-first-canary-promotion-decision")
async def model_ops_cheap_first_canary_promotion_decision():
    """Return metadata-only canary promotion decision evidence."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_promotion_decision"],
    }


@router.get("/models/cheap-first-canary-approval-packet")
async def model_ops_cheap_first_canary_approval_packet():
    """Return metadata-only maintainer approval packet for canary decisions."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_approval_packet"],
    }


@router.get("/models/cheap-first-canary-rollback-drill")
async def model_ops_cheap_first_canary_rollback_drill():
    """Return metadata-only rollback rehearsal packet for canary decisions."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_rollback_drill"],
    }


@router.get("/models/cheap-first-canary-change-manifest")
async def model_ops_cheap_first_canary_change_manifest():
    """Return metadata-only manual change manifest for canary decisions."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_canary_change_manifest"],
    }


@router.get("/models/cheap-first-maintainer-execution-checklist")
async def model_ops_cheap_first_maintainer_execution_checklist():
    """Return maintainer-only execution checklist for cheap-first default work."""
    models_payload = await list_models()
    return {
        "success": True,
        "data": models_payload["cheap_first_maintainer_execution_checklist"],
    }


@router.get("/models/performance-budget")
async def model_ops_performance_budget():
    """Return metadata-only ModelOps page load and timeout budget evidence."""
    return {
        "success": True,
        "data": ModelOpsPerformanceBudgetService().build_budget(
            _model_ops_performance_budget_input(),
            cache_ttl_seconds=MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS,
        ),
    }


@router.post("/models/performance-budget")
async def evaluate_model_ops_performance_budget(payload: dict[str, Any]):
    """Evaluate sanitized ModelOps timing observations without echoing raw payloads."""
    observations = payload.get("observations") if isinstance(payload, dict) else None
    performance_budget = ModelOpsPerformanceBudgetService().build_budget(
        _model_ops_performance_budget_input(observations),
        cache_ttl_seconds=MODEL_OPS_PAYLOAD_CACHE_TTL_SECONDS,
    )
    recorded_budget = model_ops_performance_budget_registry.record(performance_budget)
    _clear_model_ops_payload_cache()
    models_payload = await list_models()
    return {
        "success": True,
        "data": recorded_budget,
        "model_ops_readiness": models_payload["model_ops_readiness"],
        "cheap_first_release_decision": models_payload["cheap_first_release_decision"],
    }


@router.get("/models/cheap-first-escalation-budget")
async def model_ops_cheap_first_escalation_budget():
    """Return metadata-only cheap-first escalation budget evidence."""
    return {
        "success": True,
        "data": ModelOpsCheapFirstEscalationBudgetService().build_budget(),
    }


@router.post("/models/cheap-first-escalation-budget")
async def evaluate_model_ops_cheap_first_escalation_budget(payload: dict[str, Any]):
    """Evaluate aggregate cheap-first cascade observations without gateway calls."""
    return {
        "success": True,
        "data": ModelOpsCheapFirstEscalationBudgetService().build_budget(payload),
    }


@router.get("/models/failure-upgrade-budget")
async def model_failure_upgrade_budget():
    """Return metadata-only cheap-first failure upgrade budget evidence."""
    return {
        "success": True,
        "data": ModelFailureUpgradeBudgetService().build_decision(),
    }


@router.get("/models/failure-upgrade-budget-template")
async def model_failure_upgrade_budget_template():
    """Return the sanitized input shape for failure upgrade budget review."""
    return {
        "success": True,
        "data": ModelFailureUpgradeBudgetService().payload_shape(),
    }


@router.post("/models/failure-upgrade-budget")
async def evaluate_model_failure_upgrade_budget(payload: dict[str, Any]):
    """Evaluate sanitized failure signals before any model retry or upgrade."""
    return {
        "success": True,
        "data": ModelFailureUpgradeBudgetService().build_decision(payload),
    }


@router.get("/models/default-template-audit")
async def model_default_template_audit():
    """Return metadata-only audit for checked-in model default templates."""
    return {
        "success": True,
        "data": ModelDefaultTemplateAuditService().build_audit(),
    }


@router.get("/models/route-quality-budget")
async def model_route_quality_budget():
    """Return metadata-only cheap-first route quality gate evidence."""
    return {
        "success": True,
        "data": ModelRouteQualityBudgetService().build_budget(),
    }


@router.post("/gentxt")
async def generate_text(
    request: GenTxtRequest,
):
    """
    Generate Text endpoint (supports text and image input).

    Use the `stream` request parameter to control streaming behavior:
    - stream=false: return a full JSON response
    - stream=true: return an SSE streaming response
    """
    try:
        service = AIHubService()

        # Decide response mode based on the `stream` parameter
        if request.stream:
            # Streaming response - emit metadata first, then content chunks.
            async def event_generator():
                try:
                    async for event in service.gentxt_stream_events(request):
                        yield json.dumps(event)
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield json.dumps({"type": "error", "content": f"[ERROR] {extract_error_message(e)}"})
                finally:
                    yield "[DONE]"

            return EventSourceResponse(event_generator(), media_type="text/event-stream")
        else:
            # Non-streaming response
            response = await service.gentxt(request)
            return response

    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=extract_error_message(e),
        )


@router.post("/genimg", response_model=GenImgResponse)
async def generate_image(
    request: GenImgRequest,
):
    """
    Text-to-Image / Image-to-Image endpoint.

    Generate images based on the given prompt.
    If `image` is provided, the endpoint uses the OpenAI-compatible `images/edits` API to edit the input image.

    Available models:
    - gemini-2.5-flash-image: visual creativity and editing, marketing asset generation, partial image editing
    - gemini-3-pro-image: higher quality image generation/editing

    Parameters:
    - image: optional input image(s). Supports a base64 data URI string or a list of base64 data URIs. If provided, runs image editing (img2img).
    - size: image size (1024x1024 / 1024x1792 / 1792x1024)
    - quality: image quality (standard / hd). Only effective for text-to-image; ignored when `image` is provided.
    - n: number of images to generate (1-4)
    """
    try:
        service = AIHubService()
        return await service.genimg(request)

    except InvalidImageInputError as e:
        logger.warning(f"Invalid image input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=extract_error_message(e),
        )


@router.post("/genvideo", response_model=GenVideoResponse)
async def generate_video(request: GenVideoRequest):
    """
    Text-to-Video / Image-to-Video endpoint.

    Generate videos based on the given prompt.
    Returns a JSON response with the CDN URL of the generated video file.

    Note: Video generation is async - the API will poll until completion.
    See GenVideoRequest schema for model-specific constraints.
    """
    try:
        service = AIHubService()
        return await service.genvideo(request)

    except InvalidImageInputError as e:
        logger.warning(f"Invalid image input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=extract_error_message(e))


@router.post("/genaudio", response_model=GenAudioResponse)
async def generate_audio(request: GenAudioRequest):
    """
    Text-to-Speech (TTS) endpoint.

    Generate audio from text using OpenAI-compatible TTS models.
    Returns a JSON response with the CDN URL of the generated audio file.

    Parameters:
    - text: Text content to convert to audio
    - model: TTS model name (default: qwen3-tts-flash)
    - gender: Voice gender (male or female), voice is auto-selected based on model and gender
    """
    try:
        service = AIHubService()
        return await service.genaudio(request)

    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=extract_error_message(e))


@router.post("/transcribe", response_model=TranscribeAudioResponse)
async def transcribe_audio(request: TranscribeAudioRequest):
    """
    Speech-to-Text (STT) endpoint.

    Transcribe audio to text using OpenAI-compatible transcription models.

    Parameters:
    - audio: audio source. Supports absolute path, http(s) URL, or base64 data URI
    - model: STT model name (default: scribe_v2)
    """
    try:
        service = AIHubService()
        return await service.transcribe(request)

    except (InvalidAudioInputError, FileNotFoundError) as e:
        logger.warning(f"Invalid audio transcription input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=extract_error_message(e))


@router.post("/analyzepdf", response_model=AnalyzePdfResponse)
async def analyze_pdf(request: AnalyzePdfRequest):
    """
    Analyze a single PDF using native PDF input.

    The endpoint accepts a single base64 PDF data URI and returns either a direct
    answer (`qa`) or structured extraction content (`extract`).
    """
    try:
        service = AIHubService()
        return await service.analyze_pdf(request)

    except InvalidPdfInputError as e:
        logger.warning(f"Invalid PDF analysis input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.error(f"AI service configuration error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=extract_error_message(e))
    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=extract_error_message(e))
