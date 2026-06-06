import json
import re

from services.gemini_newapi_observed_model_extraction import (
    EXTRACTOR_VERSION,
    extract_observed_model_ids,
    safe_model_id,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_observed_model_extraction_supports_gateway_and_gemini_native_shapes():
    extraction = extract_observed_model_ids(
        {
            "models_response": {
                "models": [
                    {"name": "models/gemini-2.5-flash-lite"},
                    {"id": "google/gemini-2.5-flash"},
                ]
            },
            "availableModels": [
                {"id": "publishers/google/models/gemini-2.5-flash:generateContent"},
            ],
            "result": {
                "items": [
                    {"model_id": "newapi/google/gemini-3.2-flash-lite"},
                ]
            },
            "data": {
                "items": [
                    {"id": "openrouter/google/gemini-3.1-flash-lite@latest"},
                ]
            },
            "gateway_probe_evaluation": {
                "model_rows": [
                    {"model": "yibuapi/google/gemini-3.1-pro-preview"},
                ]
            },
            "observed_gemini_model_intake_queue": {
                "queue_items": [
                    {"raw_model": "yibu/gemini-3.1-flash-image"},
                ]
            },
        }
    )

    assert extraction["observed_models"] == [
        "models/gemini-2.5-flash-lite",
        "google/gemini-2.5-flash",
        "publishers/google/models/gemini-2.5-flash:generatecontent",
        "newapi/google/gemini-3.2-flash-lite",
        "openrouter/google/gemini-3.1-flash-lite@latest",
        "yibuapi/google/gemini-3.1-pro-preview",
        "yibu/gemini-3.1-flash-image",
    ]
    summary = extraction["summary"]
    assert summary["extractor_version"] == EXTRACTOR_VERSION
    assert summary["candidate_count"] == 7
    assert summary["accepted_model_count"] == 7
    assert summary["dropped_model_count"] == 0
    assert set(summary["source_fields"]) == {
        "models_response.models",
        "availableModels",
        "result.items",
        "data.items",
        "gateway_probe_evaluation.model_rows",
        "observed_gemini_model_intake_queue.queue_items",
    }
    assert summary["raw_payload_echoed"] is False


def test_observed_model_extraction_dedupes_and_redacts_sensitive_values():
    secret = "s" + "k-" + "x" * 24
    extraction = extract_observed_model_ids(
        {
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                {"model_id": "models/gemini-2.5-flash-lite"},
                secret,
                {"name": "client@example.com"},
                {"not_model": "ignored"},
            ],
        }
    )
    serialized = json.dumps(extraction, ensure_ascii=False)

    assert extraction["observed_models"] == ["models/gemini-2.5-flash-lite"]
    assert extraction["summary"]["candidate_count"] == 5
    assert extraction["summary"]["accepted_model_count"] == 1
    assert extraction["summary"]["dropped_model_count"] == 4
    assert extraction["summary"]["rejected_sensitive_count"] == 3
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "ignored" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_safe_model_id_keeps_lifecycle_action_and_query_alias_metadata():
    assert (
        safe_model_id("Publishers/Google/Models/Gemini-2.5-Flash-Lite:GenerateContent?alt=sse")
        == "publishers/google/models/gemini-2.5-flash-lite:generatecontent?alt=sse"
    )
    assert safe_model_id("newapi/google/gemini-3.1-flash-lite@latest") == "newapi/google/gemini-3.1-flash-lite@latest"
    assert safe_model_id({"model_id": "yibuapi/google/gemini-3.2-flash-lite"}) == "yibuapi/google/gemini-3.2-flash-lite"
