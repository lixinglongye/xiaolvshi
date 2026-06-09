from services import model_budget


def test_budget_policy_prefers_cheap_fast_tasks(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_cheap_model", "gemini-2.5-flash-lite", raising=False)

    decision = model_budget.model_budget_decision(None, task="classification")

    assert decision.task == "classification"
    assert decision.resolved_model == "gemini-2.5-flash-lite"
    assert decision.budget_mode == "cheap-first"
    assert decision.cost_tier == "lowest"
    assert not decision.is_over_budget


def test_budget_policy_flags_premium_model_for_fast_task(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_premium_requires_review", True, raising=False)

    decision = model_budget.model_budget_decision("gemini-2.5-pro", task="fast")

    assert decision.resolved_model == "gemini-2.5-pro"
    assert decision.cost_tier == "premium"
    assert decision.is_over_budget
    assert decision.requires_operator_review
    assert decision.recommended_model == "gemini-2.5-flash-lite"


def test_budget_policy_keeps_bad_fast_default_visible_but_recommends_catalog_safe_model(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)
    monkeypatch.setattr(model_budget.settings, "app_ai_premium_requires_review", True, raising=False)

    decision = model_budget.model_budget_decision(None, task="fast")

    assert decision.resolved_model == "gemini-2.5-pro"
    assert decision.recommended_model == "gemini-2.5-flash-lite"
    assert decision.is_over_budget is True
    assert decision.requires_operator_review is True
    assert "catalog-safe recommendation" in decision.reason


def test_budget_policy_recommends_catalog_safe_model_for_unknown_classifier_default(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_classifier_model", "gateway-private-gemini", raising=False)

    decision = model_budget.model_budget_decision("auto", task="classification")

    assert decision.resolved_model == "gateway-private-gemini"
    assert decision.recommended_model == "gemini-2.5-flash-lite"
    assert decision.is_known_model is False
    assert decision.is_over_budget is False
    assert "pricing and tier are unverified" in decision.reason


def test_budget_policy_recommends_catalog_safe_model_for_preview_ocr_default(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ocr_model", "gemini-3-flash-preview", raising=False)

    decision = model_budget.model_budget_decision(None, task="ocr")

    assert decision.resolved_model == "gemini-3-flash-preview"
    assert decision.recommended_model == "gemini-2.5-flash-lite"
    assert decision.cost_tier == "medium"
    assert decision.is_over_budget is True


def test_budget_policy_allows_pdf_premium_exception(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_pdf_model", "gemini-2.5-pro", raising=False)

    decision = model_budget.model_budget_decision(None, task="pdf")

    assert decision.budget_mode == "premium-exception"
    assert decision.resolved_model == "gemini-2.5-pro"
    assert not decision.is_over_budget
    assert not decision.requires_operator_review


def test_budget_policy_uses_gemini_image_default(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_image_model", "gemini-2.5-flash-image", raising=False)

    decision = model_budget.model_budget_decision("auto", task="image")

    assert decision.task == "image"
    assert decision.budget_mode == "explicit-media"
    assert decision.resolved_model == "gemini-2.5-flash-image"
    assert decision.recommended_model == "gemini-2.5-flash-image"
    assert decision.cost_tier == "low"
    assert not decision.is_over_budget


def test_budget_policy_uses_media_and_speech_defaults(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_video_model", "wan2.6-t2v", raising=False)
    monkeypatch.setattr(model_budget.settings, "app_ai_audio_model", "qwen3-tts-flash", raising=False)
    monkeypatch.setattr(model_budget.settings, "app_ai_transcription_model", "scribe_v2", raising=False)
    monkeypatch.setattr(model_budget.settings, "app_ai_premium_requires_review", True, raising=False)

    video = model_budget.model_budget_decision(None, task="genvideo")
    audio = model_budget.model_budget_decision("auto-audio", task="tts")
    transcription = model_budget.model_budget_decision(None, task="speech-to-text")

    assert video.task == "video"
    assert video.budget_mode == "explicit-video-media"
    assert video.resolved_model == "wan2.6-t2v"
    assert video.recommended_model == "wan2.6-t2v"
    assert video.max_cost_tier == "premium"
    assert not video.requires_operator_review
    assert audio.task == "audio"
    assert audio.budget_mode == "explicit-speech-media"
    assert audio.resolved_model == "qwen3-tts-flash"
    assert audio.recommended_model == "qwen3-tts-flash"
    assert not audio.requires_operator_review
    assert transcription.task == "transcription"
    assert transcription.budget_mode == "explicit-transcription"
    assert transcription.resolved_model == "scribe_v2"
    assert transcription.recommended_model == "scribe_v2"
    assert not transcription.requires_operator_review


def test_budget_policy_uses_low_cost_agentic_and_grounded_defaults(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_agentic_model", "gemini-3.1-flash-lite", raising=False)
    monkeypatch.setattr(model_budget.settings, "app_ai_grounded_research_model", "gemini-3.1-flash-lite", raising=False)

    agentic = model_budget.model_budget_decision(None, task="agentic-routing")
    grounded = model_budget.model_budget_decision(None, task="grounded_research")

    assert agentic.task == "agentic"
    assert agentic.resolved_model == "gemini-3.1-flash-lite"
    assert agentic.budget_mode == "cheap-first-agentic"
    assert agentic.cost_tier == "lowest"
    assert agentic.max_cost_tier == "low"
    assert not agentic.is_over_budget
    assert grounded.task == "grounded-research"
    assert grounded.resolved_model == "gemini-3.1-flash-lite"
    assert grounded.budget_mode == "cheap-first-grounded"
    assert grounded.cost_tier == "lowest"
    assert grounded.max_cost_tier == "low"
    assert not grounded.is_over_budget


def test_budget_policy_uses_cheap_first_embedding_default(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_embedding_model", "gemini-embedding-001", raising=False)

    text_embedding = model_budget.model_budget_decision(None, task="text-embedding")
    multimodal_embedding = model_budget.model_budget_decision("gemini-embedding-2", task="rag-index")

    assert text_embedding.task == "embedding"
    assert text_embedding.resolved_model == "gemini-embedding-001"
    assert text_embedding.budget_mode == "cheap-first-embedding"
    assert text_embedding.cost_tier == "lowest"
    assert text_embedding.max_cost_tier == "lowest"
    assert not text_embedding.is_over_budget
    assert multimodal_embedding.task == "embedding"
    assert multimodal_embedding.resolved_model == "gemini-embedding-2"
    assert multimodal_embedding.cost_tier == "low"
    assert multimodal_embedding.is_over_budget
    assert multimodal_embedding.recommended_model == "gemini-embedding-001"


def test_budget_policy_for_api_lists_all_core_tasks():
    payload = model_budget.budget_policy_for_api()
    tasks = {item["task"] for item in payload["task_decisions"]}

    assert tasks == {
        "fast",
        "ocr",
        "classification",
        "review",
        "grounded-research",
        "agentic",
        "pdf",
        "image",
        "video",
        "audio",
        "transcription",
        "embedding",
    }
    assert payload["premium_requires_review"] in {True, False}
