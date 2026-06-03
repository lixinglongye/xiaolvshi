"""
AI Hub router module.
Provides text, image, video, audio, PDF analysis,
and speech transcription API endpoints.
"""

import ast
import json
import logging
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
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_budget import budget_policy_for_api
from services.model_callsite_audit import ModelCallsiteAuditService
from services.model_cache_policy import ModelCachePolicyService
from services.model_catalog import catalog_for_api, task_default_model
from services.model_configuration_audit import ModelConfigurationAuditService
from services.model_cost_forecast import ModelCostForecastService
from services.model_cost_guardrails import ModelCostGuardrailService
from services.model_default_optimization import ModelDefaultOptimizationService
from services.model_default_recommendation_snapshot import ModelDefaultRecommendationSnapshotService
from services.model_escalation_policy import ModelEscalationPolicyService
from services.model_fallback_chains import ModelFallbackChainService
from services.model_gateway_compatibility import ModelGatewayCompatibilityService
from services.model_gateway_health_plan import ModelGatewayHealthPlanService
from services.model_gateway_probe_evaluation import ModelGatewayProbeEvaluationService
from services.model_lifecycle_policy import ModelLifecyclePolicyService
from services.model_ops_readiness import ModelOpsReadinessService
from services.model_routing_replay import ModelRoutingReplayService
from services.model_request_cost_bounds import ModelRequestCostBoundsService
from services.model_runtime_router import runtime_router_policy_for_api
from services.model_reasoning_policy import reasoning_policy_for_api
from services.model_request_policy import generation_request_policy_for_api
from services.model_route_guardrails import ModelRouteGuardrailService
from services.model_route_telemetry import model_route_telemetry_registry
from services.model_usage import model_usage_registry
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)


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


@router.get("/models")
async def list_models():
    """
    Return the configured model catalog and task routing defaults.

    NewAPI and Gemini OpenAI-compatible gateways may expose additional model
    names; those can still be sent directly in request payloads.
    """
    usage = model_usage_registry.snapshot()
    forecast = ModelCostForecastService().build_forecast()
    route_telemetry = model_route_telemetry_registry.snapshot()
    runtime_router = runtime_router_policy_for_api()
    model_configuration_audit = ModelConfigurationAuditService().audit()
    reasoning_policy = reasoning_policy_for_api()
    request_policy = generation_request_policy_for_api()
    route_guardrails = ModelRouteGuardrailService().evaluate(route_telemetry)
    callsite_audit = ModelCallsiteAuditService().audit()
    budget_policy = budget_policy_for_api()
    capability_matrix = ModelCapabilityMatrixService().build_matrix()
    escalation_policy = ModelEscalationPolicyService().build_policy()
    fallback_chains = ModelFallbackChainService().build_chains()
    routing_replay = ModelRoutingReplayService().run_replay()
    cost_guardrails = ModelCostGuardrailService().evaluate(usage, forecast)
    default_optimization = ModelDefaultOptimizationService().build_plan(capability_matrix, forecast)
    gateway_compatibility = ModelGatewayCompatibilityService().evaluate()
    observed_gateway_models = [
        item.get("model")
        for item in gateway_compatibility.get("configured_roles", []) + gateway_compatibility.get("gateway_examples", [])
        if item.get("model")
    ]
    default_recommendation_snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot(observed_gateway_models)
    gateway_health_plan = ModelGatewayHealthPlanService().build_plan()
    request_cost_bounds = ModelRequestCostBoundsService().evaluate()
    cache_policy = ModelCachePolicyService().build_policy(forecast)
    lifecycle_policy = ModelLifecyclePolicyService().build_policy()
    model_ops_signals = {
        "runtime_router": runtime_router,
        "model_configuration_audit": model_configuration_audit,
        "default_optimization": default_optimization,
        "default_recommendation_snapshot": default_recommendation_snapshot,
        "gateway_compatibility": gateway_compatibility,
        "gateway_health_plan": gateway_health_plan,
        "lifecycle_policy": lifecycle_policy,
        "request_cost_bounds": request_cost_bounds,
        "cache_policy": cache_policy,
        "reasoning_policy": reasoning_policy,
        "request_policy": request_policy,
        "route_telemetry": route_telemetry,
        "route_guardrails": route_guardrails,
        "callsite_audit": callsite_audit,
        "budget_policy": budget_policy,
        "capability_matrix": capability_matrix,
        "escalation_policy": escalation_policy,
        "fallback_chains": fallback_chains,
        "routing_replay": routing_replay,
        "cost_forecast": forecast,
        "cost_guardrails": cost_guardrails,
    }
    return {
        "success": True,
        "routing_aliases": {
            "auto-fast": task_default_model("fast"),
            "auto-cheap": task_default_model("cheap"),
            "auto-ocr": task_default_model("ocr"),
            "auto-review": task_default_model("review"),
            "auto-pdf": task_default_model("pdf"),
        },
        "model_ops_readiness": ModelOpsReadinessService().evaluate(model_ops_signals),
        "runtime_router": runtime_router,
        "model_configuration_audit": model_configuration_audit,
        "default_optimization": default_optimization,
        "default_recommendation_snapshot": default_recommendation_snapshot,
        "gateway_compatibility": gateway_compatibility,
        "gateway_health_plan": gateway_health_plan,
        "lifecycle_policy": lifecycle_policy,
        "request_cost_bounds": request_cost_bounds,
        "cache_policy": cache_policy,
        "reasoning_policy": reasoning_policy,
        "request_policy": request_policy,
        "route_telemetry": route_telemetry,
        "route_guardrails": route_guardrails,
        "callsite_audit": callsite_audit,
        "budget_policy": budget_policy,
        "capability_matrix": capability_matrix,
        "escalation_policy": escalation_policy,
        "fallback_chains": fallback_chains,
        "routing_replay": routing_replay,
        "cost_forecast": forecast,
        "cost_guardrails": cost_guardrails,
        "models": catalog_for_api(),
        "usage": usage,
    }


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
    """Evaluate sanitized gateway model-list and tiny chat probe results."""
    return {
        "success": True,
        "data": ModelGatewayProbeEvaluationService().evaluate(payload),
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
            # Streaming response - wrap content in JSON for SSE
            async def event_generator():
                try:
                    async for content in service.gentxt_stream(request):
                        yield json.dumps({"content": content})
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield json.dumps({"content": f"[ERROR] {extract_error_message(e)}"})
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
