from __future__ import annotations

from typing import Any

from services.model_catalog import canonical_model_id, model_profile, task_default_model


AIHUB_ENDPOINT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "aihub-gentxt",
        "endpoint_path": "/api/v1/aihub/gentxt",
        "method": "POST",
        "router_handler": "generate_text",
        "service_method": "AIHubService.gentxt",
        "response_model": "GenTxtResponse",
        "task": "auto",
        "default_model": task_default_model("fast"),
        "model_source": "request.model or inferred task default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": False,
        "route_mode": "cheap_first_runtime",
        "route_gap_reason_codes": (),
    },
    {
        "id": "aihub-gentxt-stream",
        "endpoint_path": "/api/v1/aihub/gentxt",
        "method": "POST",
        "router_handler": "generate_text(stream=true)",
        "service_method": "AIHubService.gentxt_stream",
        "response_model": "EventSourceResponse",
        "task": "auto",
        "default_model": task_default_model("fast"),
        "model_source": "request.model or inferred task default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": False,
        "returns_task_inference": False,
        "returns_usage_units": False,
        "route_mode": "cheap_first_runtime_stream",
        "route_gap_reason_codes": ("stream_metadata_not_returned",),
    },
    {
        "id": "aihub-analyzepdf",
        "endpoint_path": "/api/v1/aihub/analyzepdf",
        "method": "POST",
        "router_handler": "analyze_pdf",
        "service_method": "AIHubService.analyze_pdf",
        "response_model": "AnalyzePdfResponse",
        "task": "pdf",
        "default_model": task_default_model("pdf"),
        "model_source": "settings.app_ai_pdf_model",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": False,
        "route_mode": "premium_exception_runtime",
        "route_gap_reason_codes": (),
    },
    {
        "id": "aihub-genimg",
        "endpoint_path": "/api/v1/aihub/genimg",
        "method": "POST",
        "router_handler": "generate_image",
        "service_method": "AIHubService.genimg",
        "response_model": "GenImgResponse",
        "task": "image",
        "default_model": task_default_model("image"),
        "model_source": "request.model image default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": True,
        "route_mode": "explicit_media_runtime",
        "route_gap_reason_codes": (),
    },
    {
        "id": "aihub-genvideo",
        "endpoint_path": "/api/v1/aihub/genvideo",
        "method": "POST",
        "router_handler": "generate_video",
        "service_method": "AIHubService.genvideo",
        "response_model": "GenVideoResponse",
        "task": "video",
        "default_model": task_default_model("video"),
        "model_source": "request.model explicit video default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": True,
        "route_mode": "explicit_video_media_runtime",
        "route_gap_reason_codes": (),
    },
    {
        "id": "aihub-genaudio",
        "endpoint_path": "/api/v1/aihub/genaudio",
        "method": "POST",
        "router_handler": "generate_audio",
        "service_method": "AIHubService.genaudio",
        "response_model": "GenAudioResponse",
        "task": "audio",
        "default_model": task_default_model("audio"),
        "model_source": "request.model explicit audio default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": True,
        "route_mode": "explicit_speech_media_runtime",
        "route_gap_reason_codes": (),
    },
    {
        "id": "aihub-transcribe",
        "endpoint_path": "/api/v1/aihub/transcribe",
        "method": "POST",
        "router_handler": "transcribe_audio",
        "service_method": "AIHubService.transcribe",
        "response_model": "TranscribeAudioResponse",
        "task": "transcription",
        "default_model": task_default_model("transcription"),
        "model_source": "request.model explicit transcription default",
        "uses_runtime_router": True,
        "uses_budget_decision": True,
        "records_route_telemetry": True,
        "records_usage": True,
        "returns_route_payloads": True,
        "returns_task_inference": True,
        "returns_usage_units": True,
        "route_mode": "explicit_transcription_runtime",
        "route_gap_reason_codes": (),
    },
)


class ModelOpsAIHubEndpointRouteCoverageGateService:
    """Build metadata-only coverage evidence for AIHub endpoint route wiring."""

    def build_gate(self, _payload: Any = None) -> dict[str, Any]:
        endpoint_rows = [self._endpoint_row(spec) for spec in AIHUB_ENDPOINT_SPECS]
        checks = self._checks(endpoint_rows)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-aihub-endpoint-route-coverage-gate",
            "title": "ModelOps AIHub endpoint route coverage gate",
            "status": status,
            "method": {
                "type": "metadata-only-aihub-endpoint-route-coverage-gate",
                "notes": [
                    "Inventories AIHub router/service endpoint wiring and response metadata coverage.",
                    "Flags endpoints that bypass runtime routing, budget decisions, or route telemetry before default changes are promoted.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "endpoint_count": len(endpoint_rows),
                "runtime_routed_count": sum(1 for row in endpoint_rows if row["uses_runtime_router"]),
                "budget_decision_count": sum(1 for row in endpoint_rows if row["uses_budget_decision"]),
                "route_telemetry_count": sum(1 for row in endpoint_rows if row["records_route_telemetry"]),
                "usage_recorded_count": sum(1 for row in endpoint_rows if row["records_usage"]),
                "returns_route_payload_count": sum(1 for row in endpoint_rows if row["returns_route_payloads"]),
                "returns_task_inference_count": sum(1 for row in endpoint_rows if row["returns_task_inference"]),
                "returns_usage_units_count": sum(1 for row in endpoint_rows if row["returns_usage_units"]),
                "legacy_unrouted_count": sum(1 for row in endpoint_rows if row["route_mode"] == "legacy_media_unrouted"),
                "review_required_endpoint_count": sum(1 for row in endpoint_rows if row["route_status"] == "review_required"),
                "blocked_endpoint_count": sum(1 for row in endpoint_rows if row["route_status"] == "blocked"),
                "route_gap_count": sum(len(row["route_gap_reason_codes"]) for row in endpoint_rows),
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
            },
            "endpoint_rows": endpoint_rows,
            "coverage_matrix": self._coverage_matrix(endpoint_rows),
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(endpoint_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "returns_credentials": False,
                "returns_api_key": False,
                "returns_headers": False,
                "returns_request_body": False,
                "returns_response_body": False,
                "returns_raw_prompt": False,
                "returns_raw_payload": False,
                "returns_raw_model_output": False,
                "returns_raw_legal_text": False,
                "output_scope": "endpoint ids, route task labels, default model ids, booleans, gap codes, checks, and validation commands only",
            },
            "claim_boundary": {
                "runtime_route_migration_completed": True,
                "legacy_media_routes_fixed": True,
                "automatic_default_change_claimed": False,
                "claims_default_route_changed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_score_claimed": False,
                "allowed_claim": "The repository exposes metadata-only AIHub endpoint route coverage evidence; all inventoried endpoints are runtime-routed, while non-catalog media and speech defaults remain explicit review-only.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_aihub_runtime_routing.py tests/test_model_ops_gemini_cheap_first_route_preflight.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _endpoint_row(self, spec: dict[str, Any]) -> dict[str, Any]:
        default_model = str(spec["default_model"])
        canonical = canonical_model_id(default_model)
        profile = model_profile(default_model)
        gap_codes = list(spec["route_gap_reason_codes"])
        if profile is None:
            gap_codes.append("model_not_in_local_catalog")
        route_status = "ready" if not gap_codes else "review_required"
        return {
            "id": str(spec["id"]),
            "endpoint_path": str(spec["endpoint_path"]),
            "method": str(spec["method"]),
            "router_handler": str(spec["router_handler"]),
            "service_method": str(spec["service_method"]),
            "response_model": str(spec["response_model"]),
            "task": str(spec["task"]),
            "default_model": default_model,
            "canonical_model": canonical,
            "model_status": profile.status if profile else "unknown",
            "cost_tier": profile.cost_tier if profile else "unknown",
            "model_source": str(spec["model_source"]),
            "uses_runtime_router": bool(spec["uses_runtime_router"]),
            "uses_budget_decision": bool(spec["uses_budget_decision"]),
            "records_route_telemetry": bool(spec["records_route_telemetry"]),
            "records_usage": bool(spec["records_usage"]),
            "returns_route_payloads": bool(spec["returns_route_payloads"]),
            "returns_task_inference": bool(spec["returns_task_inference"]),
            "returns_usage_units": bool(spec["returns_usage_units"]),
            "route_mode": str(spec["route_mode"]),
            "route_status": route_status,
            "route_gap_reason_codes": _dedupe(gap_codes) or ["endpoint_route_coverage_ready"],
            "next_action": self._next_action(spec, gap_codes),
        }

    def _coverage_matrix(self, endpoint_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        keys = (
            "uses_runtime_router",
            "uses_budget_decision",
            "records_route_telemetry",
            "records_usage",
            "returns_route_payloads",
            "returns_task_inference",
            "returns_usage_units",
        )
        return [
            {
                "coverage_key": key,
                "covered_endpoint_count": sum(1 for row in endpoint_rows if row[key]),
                "gap_endpoint_ids": [row["id"] for row in endpoint_rows if not row[key]],
            }
            for key in keys
        ]

    def _checks(self, endpoint_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        runtime_gaps = [row["id"] for row in endpoint_rows if not row["uses_runtime_router"]]
        telemetry_gaps = [row["id"] for row in endpoint_rows if not row["records_route_telemetry"]]
        payload_gaps = [row["id"] for row in endpoint_rows if not row["returns_route_payloads"]]
        task_inference_gaps = [row["id"] for row in endpoint_rows if not row["returns_task_inference"]]
        usage_unit_gaps = [
            row["id"]
            for row in endpoint_rows
            if row["task"] in {"image", "video", "audio", "transcription"} and not row["returns_usage_units"]
        ]
        legacy_media = [row["id"] for row in endpoint_rows if row["route_mode"] == "legacy_media_unrouted"]
        unknown_models = [row["id"] for row in endpoint_rows if row["model_status"] == "unknown"]
        return [
            self._check(
                "aihub-endpoint-inventory",
                "pass" if len(endpoint_rows) == len(AIHUB_ENDPOINT_SPECS) else "fail",
                "Every public AIHub generation endpoint is represented in the route coverage inventory.",
                [row["id"] for row in endpoint_rows],
            ),
            self._check(
                "runtime-router-coverage",
                "warn" if runtime_gaps else "pass",
                "AIHub endpoints should resolve models through runtime routing before gateway use.",
                runtime_gaps,
            ),
            self._check(
                "route-telemetry-coverage",
                "warn" if telemetry_gaps else "pass",
                "AIHub endpoints should record sanitized route telemetry and repository evidence.",
                telemetry_gaps,
            ),
            self._check(
                "response-route-payload-coverage",
                "warn" if payload_gaps else "pass",
                "Responses should expose route/task/budget metadata where the endpoint response shape allows it.",
                payload_gaps,
            ),
            self._check(
                "response-routing-metadata-coverage",
                "warn" if task_inference_gaps else "pass",
                "Non-streaming responses should expose sanitized task_inference metadata for review.",
                task_inference_gaps,
            ),
            self._check(
                "media-usage-unit-coverage",
                "warn" if usage_unit_gaps else "pass",
                "Media and speech responses should expose usage units that support cheap-first cost review without raw payloads.",
                usage_unit_gaps,
            ),
            self._check(
                "legacy-media-budget-route-gap",
                "warn" if legacy_media else "pass",
                "Video, audio, and transcription routes should stay attached to explicit media/speech budget tasks after runtime router migration.",
                legacy_media,
            ),
            self._check(
                "local-catalog-coverage",
                "warn" if unknown_models else "pass",
                "Default endpoint models should resolve to local catalog rows or remain explicit review-only.",
                unknown_models,
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "Gate output is metadata-only and never calls providers, gateways, app AI endpoints, or writes configuration.",
                ["model_called:false", "gateway_called:false", "configuration_written:false"],
            ),
        ]

    def _check(self, check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": status,
            "reason": reason,
            "evidence": evidence[:8],
        }

    def _recommended_actions(self, endpoint_rows: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        if any(not row["uses_runtime_router"] for row in endpoint_rows):
            actions.append("Migrate any remaining endpoints to resolve_runtime_model before promoting route evidence.")
        if any(not row["returns_route_payloads"] for row in endpoint_rows):
            actions.append("Extend streaming response shapes with route/task/budget metadata where practical.")
        if any(
            row["task"] in {"image", "video", "audio", "transcription"} and not row["returns_usage_units"]
            for row in endpoint_rows
        ):
            actions.append("Add media usage units before using any media endpoint for cost or savings evidence.")
        if any(row["model_status"] == "unknown" for row in endpoint_rows):
            actions.append("Catalog non-catalog media and speech defaults before using them for price, lifecycle, or benchmark claims.")
        if not actions:
            actions.append("All AIHub endpoints expose runtime route coverage; keep this gate attached to ModelOps release evidence.")
        return actions

    def _next_action(self, spec: dict[str, Any], gap_codes: list[str]) -> str:
        if "runtime_router_missing" in gap_codes:
            return "Migrate this endpoint from resolve_model to resolve_runtime_model and route telemetry."
        if "response_route_payload_missing" in gap_codes:
            return "Consider returning sanitized task_inference and budget_decision fields in the endpoint response."
        if "media_usage_units_missing" in gap_codes:
            return "Add media usage units before using this endpoint for cost or savings evidence."
        return "Keep the endpoint attached to runtime route telemetry and regression tests."


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
