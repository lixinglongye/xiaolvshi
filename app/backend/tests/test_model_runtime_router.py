from services.model_runtime_router import resolve_runtime_model, runtime_router_policy_for_api


def test_runtime_router_uses_review_default_when_task_declared():
    route = resolve_runtime_model(None, task="review")

    assert route.task == "review"
    assert route.resolved_model == "gemini-2.5-flash"
    assert route.budget_mode == "balanced"
    assert route.routed_to_recommended_model is False
    assert route.explicit_model_requested is False
    assert route.explicit_model_fit_status == "default"


def test_runtime_router_downgrades_fast_premium_without_explicit_allowance():
    route = resolve_runtime_model("gemini-2.5-pro", task="fast")

    assert route.task == "fast"
    assert route.requested_resolved_model == "gemini-2.5-pro"
    assert route.resolved_model == "gemini-2.5-flash-lite"
    assert route.is_over_budget is True
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is True
    assert route.explicit_model_requested is True
    assert route.explicit_model_fit_status == "enforced"
    assert route.reason_codes == (
        "known_catalog_model",
        "over_task_budget",
        "operator_review_required",
        "routed_to_recommended_model",
        "resolved_to_recommended_model",
    )
    assert route.to_api()["reason_codes"] == list(route.reason_codes)


def test_runtime_router_allows_over_budget_model_when_explicit():
    route = resolve_runtime_model("gemini-2.5-pro", task="fast", allow_over_budget_model=True)

    assert route.resolved_model == "gemini-2.5-pro"
    assert route.allow_over_budget_model is True
    assert route.routed_to_recommended_model is False
    assert route.explicit_model_fit_status == "allowed_review_exception"
    assert "explicit_over_budget_allowed" in route.reason_codes
    assert "operator_review_required" in route.reason_codes
    assert "allowed explicitly" in route.reason


def test_runtime_router_downgrades_unknown_gateway_model_by_default():
    route = resolve_runtime_model("gateway-private-gemini", task="classification")

    assert route.requested_resolved_model == "gateway-private-gemini"
    assert route.resolved_model == "gemini-2.5-flash-lite"
    assert route.requested_model_status == "unknown"
    assert route.is_known_model is True
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is True
    assert route.explicit_model_requested is True
    assert route.explicit_model_fit_status == "enforced"
    assert "unknown_catalog_model" in route.reason_codes
    assert "unverified_price_tier" in route.reason_codes
    assert "unknown_gateway_routed_to_recommended" in route.reason_codes
    assert "gateway_passthrough" not in route.reason_codes
    assert "routed to gemini-2.5-flash-lite" in route.reason
    assert "sk-" not in str(route.to_api())


def test_runtime_router_allows_unknown_gateway_model_when_explicitly_reviewed():
    route = resolve_runtime_model("gateway-private-gemini", task="classification", allow_over_budget_model=True)

    assert route.resolved_model == "gateway-private-gemini"
    assert route.is_known_model is False
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is False
    assert route.explicit_model_fit_status == "allowed_review_exception"
    assert "gateway_passthrough" in route.reason_codes
    assert "explicit_gateway_passthrough_allowed" in route.reason_codes
    assert "explicit_over_budget_allowed" not in route.reason_codes
    assert "within_task_budget" not in route.reason_codes
    assert "sk-" not in str(route.to_api())


def test_runtime_router_downgrades_preview_lifecycle_model_by_default():
    route = resolve_runtime_model("gemini-3-flash-preview", task="review")

    assert route.requested_canonical_model == "gemini-3-flash-preview"
    assert route.requested_model_status == "preview"
    assert route.requested_cost_tier == "medium"
    assert route.resolved_model == "gemini-2.5-flash"
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is True
    assert route.explicit_model_fit_status == "enforced"
    assert "lifecycle_preview" in route.reason_codes
    assert "non_stable_model_routed_to_recommended" in route.reason_codes
    assert "gateway_passthrough" not in route.reason_codes


def test_runtime_router_uses_image_default_for_auto_image_task():
    route = resolve_runtime_model("auto", task="image")

    assert route.task == "image"
    assert route.requested_resolved_model == "gemini-2.5-flash-image"
    assert route.resolved_model == "gemini-2.5-flash-image"
    assert route.budget_mode == "explicit-media"
    assert route.cost_tier == "low"
    assert route.is_known_model is True
    assert route.routed_to_recommended_model is False
    assert route.explicit_model_requested is False
    assert route.explicit_model_fit_status == "default"
    assert "task_default_selected" in route.reason_codes
    assert "within_task_budget" in route.reason_codes


def test_runtime_router_uses_media_and_speech_defaults_as_non_explicit_requests():
    video = resolve_runtime_model(None, task="video")
    audio = resolve_runtime_model(None, task="audio")
    transcription = resolve_runtime_model(None, task="transcription")

    assert video.task == "video"
    assert video.resolved_model == "wan2.6-t2v"
    assert video.budget_mode == "explicit-video-media"
    assert video.explicit_model_requested is False
    assert video.explicit_model_fit_status == "default"
    assert video.routed_to_recommended_model is False
    assert "unknown_catalog_model" in video.reason_codes
    assert "gateway_passthrough" in video.reason_codes
    assert audio.task == "audio"
    assert audio.resolved_model == "qwen3-tts-flash"
    assert audio.budget_mode == "explicit-speech-media"
    assert audio.explicit_model_requested is False
    assert audio.routed_to_recommended_model is False
    assert transcription.task == "transcription"
    assert transcription.resolved_model == "scribe_v2"
    assert transcription.budget_mode == "explicit-transcription"
    assert transcription.explicit_model_requested is False
    assert transcription.routed_to_recommended_model is False


def test_runtime_router_treats_gemini_tts_as_known_preview_review_model():
    route = resolve_runtime_model("models/gemini-2.5-flash-preview-tts", task="tts")

    assert route.task == "audio"
    assert route.requested_canonical_model == "gemini-2.5-flash-preview-tts"
    assert route.requested_model_status == "preview"
    assert route.requested_cost_tier == "medium"
    assert route.resolved_model == "qwen3-tts-flash"
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is True
    assert route.explicit_model_fit_status == "enforced"
    assert "lifecycle_preview" in route.reason_codes
    assert "non_stable_model_routed_to_recommended" in route.reason_codes

    allowed = resolve_runtime_model("models/gemini-2.5-flash-preview-tts", task="tts", allow_over_budget_model=True)
    assert allowed.resolved_model == "models/gemini-2.5-flash-preview-tts"
    assert allowed.explicit_model_fit_status == "allowed_review_exception"
    assert "explicit_non_stable_model_allowed" in allowed.reason_codes
    assert "sk-" not in str(allowed.to_api())


def test_runtime_router_uses_specialized_low_cost_defaults():
    agentic = resolve_runtime_model(None, task="workflow-planning")
    grounded = resolve_runtime_model(None, task="rag-research")

    assert agentic.task == "agentic"
    assert agentic.resolved_model == "gemini-3.1-flash-lite"
    assert agentic.budget_mode == "cheap-first-agentic"
    assert agentic.routed_to_recommended_model is False
    assert grounded.task == "grounded-research"
    assert grounded.resolved_model == "gemini-3.1-flash-lite"
    assert grounded.budget_mode == "cheap-first-grounded"
    assert grounded.routed_to_recommended_model is False


def test_runtime_router_policy_lists_task_defaults_without_secrets():
    policy = runtime_router_policy_for_api()

    assert policy["status"] == "ready"
    assert "task" in policy["request_fields"]
    assert policy["auto_task_inference"]["default_task"] == "auto"
    assert any("Unknown gateway-specific explicit model names" in item for item in policy["enforcement"])
    assert any("Preview or review-lifecycle explicit models" in item for item in policy["enforcement"])
    assert {item["task"] for item in policy["task_defaults"]} >= {
        "fast",
        "classification",
        "review",
        "grounded-research",
        "agentic",
        "pdf",
        "image",
        "video",
        "audio",
        "transcription",
    }
    image_default = next(item for item in policy["task_defaults"] if item["task"] == "image")
    video_default = next(item for item in policy["task_defaults"] if item["task"] == "video")
    agentic_default = next(item for item in policy["task_defaults"] if item["task"] == "agentic")
    assert image_default["resolved_model"] == "gemini-2.5-flash-image"
    assert video_default["resolved_model"] == "wan2.6-t2v"
    assert video_default["budget_mode"] == "explicit-video-media"
    assert agentic_default["resolved_model"] == "gemini-3.1-flash-lite"
    assert any("video, audio, and transcription exception paths" in item for item in policy["enforcement"])
    assert "sk-" not in str(policy)
