from services import model_catalog


def test_resolve_model_prefers_cost_first_aliases(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_cheap_model", "cheap-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "fast-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ocr_model", "ocr-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_classifier_model", "classifier-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_review_model", "review-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_pdf_model", "pdf-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_image_model", "image-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_video_model", "video-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_audio_model", "audio-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_transcription_model", "transcription-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_embedding_model", "embedding-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_agentic_model", "agentic-model", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_grounded_research_model", "grounded-model", raising=False)

    assert model_catalog.resolve_model("cheap", task="review") == "cheap-model"
    assert model_catalog.resolve_model("auto-fast", task="review") == "fast-model"
    assert model_catalog.resolve_model("auto-ocr", task="review") == "ocr-model"
    assert model_catalog.resolve_model(None, task="classification") == "classifier-model"
    assert model_catalog.resolve_model("auto-review", task="fast") == "review-model"
    assert model_catalog.resolve_model(None, task="agentic") == "agentic-model"
    assert model_catalog.resolve_model(None, task="grounded-research") == "grounded-model"
    assert model_catalog.resolve_model("auto-agentic", task="fast") == "agentic-model"
    assert model_catalog.resolve_model("auto-grounded-research", task="fast") == "grounded-model"
    assert model_catalog.resolve_model("auto-pdf", task="fast") == "pdf-model"
    assert model_catalog.resolve_model("auto", task="image") == "image-model"
    assert model_catalog.resolve_model("auto-image", task="fast") == "image-model"
    assert model_catalog.resolve_model(None, task="video") == "video-model"
    assert model_catalog.resolve_model("auto-video", task="fast") == "video-model"
    assert model_catalog.resolve_model(None, task="audio") == "audio-model"
    assert model_catalog.resolve_model("auto-audio", task="fast") == "audio-model"
    assert model_catalog.resolve_model(None, task="transcription") == "transcription-model"
    assert model_catalog.resolve_model("auto-transcription", task="fast") == "transcription-model"
    assert model_catalog.resolve_model(None, task="embedding") == "embedding-model"
    assert model_catalog.resolve_model("auto-embedding", task="fast") == "embedding-model"


def test_resolve_model_passes_gateway_specific_names_through():
    assert model_catalog.resolve_model("provider-custom-model", task="fast") == "provider-custom-model"


def test_canonical_model_id_recognizes_gateway_prefixes():
    assert model_catalog.canonical_model_id("gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("models/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("google/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("openrouter/google/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("newapi/google/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("yibuapi/google/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"
    assert model_catalog.canonical_model_id("publishers/google/models/gemini-3-flash-preview") == "gemini-3-flash-preview"
    assert model_catalog.canonical_model_id("models/gemini-3.1-pro") == "gemini-3.1-pro"
    assert model_catalog.canonical_model_id("yibu/gemini-3.1-flash-image") == "gemini-3.1-flash-image"
    assert model_catalog.canonical_model_id("models/gemini-embedding-001") == "gemini-embedding-001"
    assert model_catalog.canonical_model_id("google/gemini-embedding-2") == "gemini-embedding-2"
    assert model_catalog.canonical_model_id("provider-custom-model") is None


def test_model_profile_and_cost_work_with_gateway_prefixed_names():
    profile = model_catalog.model_profile("google/gemini-2.5-flash-lite")

    assert profile is not None
    assert profile.id == "gemini-2.5-flash-lite"
    assert profile.cost_tier == "lowest"
    assert model_catalog.estimate_token_cost_usd("models/gemini-2.5-flash-lite", 1_000_000, 500_000) == 0.30


def test_catalog_marks_configured_roles(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_cheap_model", "gemini-2.5-flash-lite", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_balanced_model", "gemini-2.5-flash", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_premium_model", "gemini-2.5-pro", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_review_model", "gemini-2.5-flash", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_pdf_model", "gemini-2.5-pro", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_image_model", "gemini-2.5-flash-image", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_embedding_model", "gemini-embedding-001", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_agentic_model", "gemini-3.1-flash-lite", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_grounded_research_model", "gemini-3.1-flash-lite", raising=False)

    catalog = {item["id"]: item for item in model_catalog.catalog_for_api()}

    assert "cheap" in catalog["gemini-2.5-flash-lite"]["configured_roles"]
    assert "ocr" in catalog["gemini-2.5-flash-lite"]["configured_roles"]
    assert "review" in catalog["gemini-2.5-flash"]["configured_roles"]
    assert "pdf" in catalog["gemini-2.5-pro"]["configured_roles"]
    assert "image" in catalog["gemini-2.5-flash-image"]["configured_roles"]
    assert "embedding" in catalog["gemini-embedding-001"]["configured_roles"]
    assert "agentic" in catalog["gemini-3.1-flash-lite"]["configured_roles"]
    assert "grounded-research" in catalog["gemini-3.1-flash-lite"]["configured_roles"]
    assert catalog["gemini-2.5-flash-lite"]["pricing"]["input_usd_per_million_tokens"] == 0.10
    assert catalog["gemini-3.1-flash-lite"]["pricing"]["input_usd_per_million_tokens"] == 0.25
    assert catalog["gemini-3-flash-preview"]["status"] == "preview"
    assert catalog["gemini-3-flash-preview"]["pricing"]["input_usd_per_million_tokens"] == 0.50
    assert catalog["gemini-3.5-flash"]["cost_tier"] == "premium"
    assert catalog["gemini-3.5-flash"]["status"] == "review"
    assert catalog["gemini-3.5-flash"]["pricing"]["input_usd_per_million_tokens"] is None
    assert catalog["gemini-3.5-flash"]["pricing"]["output_usd_per_million_tokens"] is None
    assert catalog["gemini-3.1-pro"]["status"] == "stable"
    assert catalog["gemini-3.1-pro-preview"]["status"] == "preview"
    assert catalog["gemini-3.1-flash-image"]["pricing"]["output_usd_per_image"] == 0.067
    assert "image-edit" in catalog["gemini-3.1-flash-image"]["capabilities"]
    assert catalog["gemini-embedding-001"]["cost_tier"] == "lowest"
    assert catalog["gemini-embedding-001"]["pricing"]["input_usd_per_million_tokens"] == 0.15
    assert "embedding" in catalog["gemini-embedding-001"]["capabilities"]
    assert catalog["gemini-embedding-2"]["cost_tier"] == "low"
    assert catalog["gemini-embedding-2"]["pricing"]["input_usd_per_million_tokens"] == 0.20
    assert "multimodal" in catalog["gemini-embedding-2"]["capabilities"]
    assert catalog["gemini-2.5-flash-lite"]["context_window_tokens"] >= 1_000_000


def test_catalog_marks_prefixed_configured_roles(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_cheap_model", "models/gemini-2.5-flash-lite", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "google/gemini-2.5-flash-lite", raising=False)
    monkeypatch.setattr(model_catalog.settings, "app_ocr_model", "openrouter/google/gemini-2.5-flash-lite", raising=False)

    catalog = {item["id"]: item for item in model_catalog.catalog_for_api()}

    assert "cheap" in catalog["gemini-2.5-flash-lite"]["configured_roles"]
    assert "fast" in catalog["gemini-2.5-flash-lite"]["configured_roles"]
    assert "ocr" in catalog["gemini-2.5-flash-lite"]["configured_roles"]


def test_estimate_token_cost_uses_catalog_pricing():
    cost = model_catalog.estimate_token_cost_usd("gemini-2.5-flash-lite", 1_000_000, 500_000)

    assert cost == 0.30
    assert model_catalog.estimate_token_cost_usd("google/gemini-2.5-flash", 1_000_000, 500_000) == 1.55
    assert model_catalog.estimate_token_cost_usd("newapi/google/gemini-3-flash-preview", 1_000_000, 500_000) == 2.0
    assert model_catalog.estimate_token_cost_usd("gemini-3.5-flash", 1_000_000, 500_000) is None
    assert model_catalog.estimate_token_cost_usd("gemini-3-pro-image", 1_000_000, 500_000) is None
    assert model_catalog.estimate_token_cost_usd("gemini-embedding-001", 1_000_000, 0) == 0.15
    assert model_catalog.estimate_token_cost_usd("google/gemini-embedding-2", 1_000_000, 0) == 0.20
    assert model_catalog.estimate_token_cost_usd("gemini-2.5-flash-lite", -100, -100) == 0.0
    assert model_catalog.estimate_token_cost_usd("provider-custom-model", 100, 100) is None
