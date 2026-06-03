import json
import re

from services.ocr_import_readiness_policy import (
    IMPORT_STATUSES,
    OcrImportReadinessPolicyService,
)


def test_ocr_import_readiness_policy_contains_required_sections():
    policy = OcrImportReadinessPolicyService().build_policy()

    assert policy["status"] == "uploaded"
    assert policy["policy_id"] == "ocr-import-readiness-policy-v1"
    assert policy["status_enumeration"]
    assert policy["scanned_or_low_text_detection"]
    assert policy["retry_policy"]
    assert policy["blocking_conditions"] == []
    assert policy["manual_review_conditions"] == []
    assert policy["low_resource_validation_commands"]
    assert policy["privacy_notes"]


def test_ocr_import_readiness_statuses_cover_required_import_states():
    policy = OcrImportReadinessPolicyService().build_policy()
    statuses = {item["status"] for item in policy["status_enumeration"]}

    assert statuses == set(IMPORT_STATUSES)
    assert {
        "uploaded",
        "preflight",
        "ocr_needed",
        "ocr_failed",
        "parsed",
        "blocked",
        "manual_review",
    }.issubset(statuses)


def test_scanned_page_triggers_ocr_needed():
    payload = {
        "preflight_complete": True,
        "page_count": 2,
        "pages": [
            {"page_number": 1, "text_char_count": 1200, "has_text_layer": True},
            {"page_number": 2, "text_char_count": 0, "has_text_layer": False, "image_only": True},
        ],
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "ocr_needed"
    assert policy["summary"]["ocr_required"] is True
    assert policy["scanned_or_low_text_detection"]["scanned_page_count"] >= 1
    assert policy["scanned_or_low_text_detection"]["low_text_page_count"] >= 1


def test_low_text_page_triggers_ocr_needed():
    payload = {
        "preflight_complete": True,
        "page_count": 3,
        "pages": [
            {"page_number": 1, "text_char_count": 40, "has_text_layer": True},
            {"page_number": 2, "text_char_count": 1400, "has_text_layer": True},
            {"page_number": 3, "text_char_count": 1600, "has_text_layer": True},
        ],
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "ocr_needed"
    assert policy["scanned_or_low_text_detection"]["low_text_pages"] == [1]
    assert policy["summary"]["ready_for_parse"] is False


def test_too_many_ocr_failures_block_import():
    payload = {
        "preflight_complete": True,
        "scan_detected": True,
        "ocr_status": "failed",
        "ocr_attempt_count": 3,
        "ocr_last_error": "engine_timeout",
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "blocked"
    assert policy["summary"]["blocked"] is True
    assert policy["retry_state"]["blocked_by_retry_budget"] is True
    assert any(item["id"] == "ocr-retry-budget-exhausted" for item in policy["blocking_conditions"])


def test_ocr_failure_before_retry_budget_is_not_blocked():
    payload = {
        "preflight_complete": True,
        "scan_detected": True,
        "ocr_status": "failed",
        "ocr_attempt_count": 1,
        "ocr_last_error": "transient_engine_error",
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "ocr_failed"
    assert policy["retry_state"]["retry_allowed"] is True
    assert not policy["blocking_conditions"]


def test_manual_review_conditions_are_visible_for_quality_risks():
    payload = {
        "preflight_complete": True,
        "handwriting_detected": True,
        "page_count": 1,
        "pages": [{"page_number": 1, "text_char_count": 30, "has_text_layer": True}],
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "manual_review"
    condition_ids = {item["id"] for item in policy["manual_review_conditions"]}
    assert "handwriting-detected" in condition_ids
    assert "all-pages-low-text" in condition_ids


def test_parsed_status_when_preflight_has_sufficient_text():
    payload = {
        "preflight_complete": True,
        "page_count": 2,
        "pages": [
            {"page_number": 1, "text_char_count": 1200, "has_text_layer": True},
            {"page_number": 2, "text_char_count": 900, "has_text_layer": True},
        ],
    }

    policy = OcrImportReadinessPolicyService().build_policy(payload)

    assert policy["status"] == "parsed"
    assert policy["summary"]["ready_for_parse"] is True
    assert policy["summary"]["ocr_required"] is False


def test_ocr_import_readiness_payload_has_no_credentials_addresses_or_passwords():
    policy = OcrImportReadinessPolicyService().build_policy(
        {
            "preflight_complete": True,
            "page_count": 1,
            "pages": [{"page_number": 1, "text_char_count": 1000, "has_text_layer": True}],
        }
    )
    serialized = json.dumps(policy, ensure_ascii=False)
    address_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    credential_patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"(?i)(pwd|pass\s*word|token)\s*[:=]",
    ]

    assert not re.search(address_pattern, serialized)
    assert all(not re.search(pattern, serialized) for pattern in credential_patterns)


def test_ocr_import_readiness_policy_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/ocr-import-readiness-policy")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "uploaded"

    post_response = client.post(
        "/api/v1/maintenance/ocr-import-readiness-policy",
        json={
            "preflight_complete": True,
            "page_count": 1,
            "pages": [{"page_number": 1, "text_char_count": 10, "has_text_layer": False}],
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ocr_needed"
