import json
import re

from services.model_ops_observed_gemini_premium_exception_review import (
    ModelOpsObservedGeminiPremiumExceptionReviewService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_observed_gemini_premium_exception_review_default_get_route():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/gemini/observed-premium-exception-review")
    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    data = payload["data"]
    assert data["status"] == "review_required"
    assert data["summary"]["premium_exception_review_count"] >= 1
    assert data["summary"]["configuration_written"] is False
    assert data["summary"]["gateway_called"] is False
    assert data["summary"]["network_called"] is False
    assert all(row["review_type"] == "premium_exception_review" for row in data["review_rows"])


def test_observed_gemini_premium_exception_review_metadata_only_boundaries():
    result = ModelOpsObservedGeminiPremiumExceptionReviewService().build_review(
        {"observed_models": ["models/gemini-2.5-pro", "gemini-2.5-flash-lite"]}
    )

    assert result["status"] == "review_required"
    assert result["summary"]["configuration_written"] is False
    assert result["summary"]["automatic_configuration_change_allowed"] is False
    assert result["summary"]["gateway_called"] is False
    assert result["summary"]["network_called"] is False
    assert result["summary"]["raw_payload_echoed"] is False
    assert result["summary"]["raw_model_output_included"] is False
    assert result["summary"]["credentials_included"] is False
    assert result["privacy_boundary"]["metadata_only"] is True
    assert result["privacy_boundary"]["configuration_written"] is False
    assert result["privacy_boundary"]["gateway_called"] is False
    assert result["privacy_boundary"]["network_called"] is False
    assert result["claim_boundary"]["automatic_default_change_claimed"] is False
    assert result["claim_boundary"]["high_frequency_default_allowed_for_premium_claimed"] is False
    assert all(row["high_frequency_default_allowed"] is False for row in result["review_rows"])
    assert all(row["automatic_configuration_change_allowed"] is False for row in result["review_rows"])


def test_observed_gemini_premium_exception_review_marks_pro_and_premium_rows():
    result = ModelOpsObservedGeminiPremiumExceptionReviewService().build_review(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-pro"},
                    {"id": "gemini-3.1-pro-preview"},
                    {"id": "google/gemini-3.5-flash"},
                    {"id": "gemini-2.5-flash-lite"},
                ]
            }
        }
    )
    rows = {row["raw_model"]: row for row in result["review_rows"]}

    assert result["status"] == "review_required"
    assert result["summary"]["premium_exception_review_count"] == 3
    assert result["summary"]["pro_variant_review_count"] == 2
    assert result["summary"]["explicit_premium_route_supported_count"] == 3
    assert result["summary"]["high_frequency_default_allowed_count"] == 0

    for model_id in ("models/gemini-2.5-pro", "gemini-3.1-pro-preview", "google/gemini-3.5-flash"):
        assert rows[model_id]["review_type"] == "premium_exception_review"
        assert rows[model_id]["review_status"] == "review_required"
        assert rows[model_id]["explicit_premium_route_supported"] is True
        assert rows[model_id]["explicit_route_only"] is True
        assert rows[model_id]["high_frequency_default_allowed"] is False
        assert rows[model_id]["allowed_high_frequency_default_tasks"] == []
        assert rows[model_id]["gateway_call_required"] is False
        assert rows[model_id]["network_call_required"] is False
        assert "premium-exception-review" in rows[model_id]["review_reason_codes"]

    assert "pro-variant" in rows["models/gemini-2.5-pro"]["review_reason_codes"]
    assert "premium-cost-tier" in rows["google/gemini-3.5-flash"]["review_reason_codes"]


def test_observed_gemini_premium_exception_review_does_not_echo_sensitive_payload():
    secret = "s" + "k-" + ("Q" * 24)
    email = "client@example.com"
    invalid_marker = "premium-invalid-marker-999"
    output_marker = "raw-model-output-marker-999"
    result = ModelOpsObservedGeminiPremiumExceptionReviewService().build_review(
        {
            "observed_models": [
                "gemini-2.5-pro",
                secret,
                email,
                {"metadata": {"source": invalid_marker}},
            ],
            "raw_model_output": output_marker,
        }
    )
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "blocked"
    assert result["summary"]["premium_exception_review_count"] == 1
    assert result["summary"]["source_rejected_observed_model_count"] == 3
    assert result["summary"]["source_rejected_sensitive_observed_model_count"] == 2
    assert result["summary"]["source_rejected_invalid_observed_model_count"] == 1
    assert result["summary"]["raw_payload_echoed"] is False
    assert result["privacy_boundary"]["raw_payload_echoed"] is False
    assert result["privacy_boundary"]["raw_model_output_included"] is False
    assert result["review_rows"][0]["raw_model"] == "gemini-2.5-pro"
    assert secret not in serialized
    assert email not in serialized
    assert invalid_marker not in serialized
    assert output_marker not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)
