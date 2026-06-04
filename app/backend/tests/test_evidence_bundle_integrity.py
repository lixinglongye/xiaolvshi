import json
import re

from services.evidence_bundle_integrity import EvidenceBundleIntegrityService


SENSITIVE_PATTERN = re.compile(
    "|".join(
        [
            r"sk-[A-Za-z0-9]{20,}",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"\b1[3-9]\d{9}\b",
            r"\b\d{17}[\dXx]\b",
        ]
    )
)


def _valid_items() -> list[dict]:
    return [
        {
            "evidence_id": "EV-001",
            "source_id": "upload-001",
            "proof_purpose": "Proves contract formation.",
            "evidence_date": "2026-05-01",
            "amount": "120000.00",
            "content_hash": "sha256:contract-001",
            "file_name": "contract.pdf",
        },
        {
            "evidence_id": "EV-002",
            "source_id": "upload-002",
            "proof_purpose": "Proves payment timeline.",
            "evidence_date": "2026-05-03",
            "amount": "30000",
            "content_hash": "sha256:payment-001",
            "file_name": "payment-record.pdf",
        },
    ]


def _report(payload: list[dict] | dict | None = None) -> dict:
    return EvidenceBundleIntegrityService().build_report(payload)


def test_evidence_bundle_integrity_detects_duplicate_content_hashes():
    items = _valid_items()
    items[1]["content_hash"] = items[0]["content_hash"]

    report = _report(items)
    duplicate_group = report["duplicate_groups"][0]

    assert report["status"] == "blocked"
    assert report["score"] < 100
    assert report["summary"]["duplicate_group_count"] == 1
    assert duplicate_group["match_on"] == "content_hash"
    assert duplicate_group["evidence_ids"] == ["EV-001", "EV-002"]
    assert all(review["duplicate_group_ids"] for review in report["item_reviews"])


def test_evidence_bundle_integrity_flags_missing_required_metadata():
    report = _report(
        [
            {
                "evidence_id": "EV-MISSING",
                "date": "",
                "amount": "not-a-number",
            }
        ]
    )

    assert report["status"] == "blocked"
    assert report["missing_source_ids"] == ["EV-MISSING"]
    assert report["missing_proof_purpose_ids"] == ["EV-MISSING"]
    assert report["metadata_gap_counts"]["missing_date"] == 1
    assert report["metadata_gap_counts"]["invalid_amount"] == 1
    assert report["metadata_gap_counts"]["missing_checksum"] == 1
    assert "source_id" in report["item_reviews"][0]["missing_fields"]
    assert "proof_purpose" in report["item_reviews"][0]["missing_fields"]


def test_evidence_bundle_integrity_does_not_echo_pii_filenames_or_long_text():
    secret = "s" + "k-" + "a" * 24
    raw_filename = "loan_client@example.com_13800138000_110101199003076832.pdf"
    report = _report(
        [
            {
                "evidence_id": "client@example.com",
                "source_id": "upload-001",
                "proof_purpose": "Proves payment.",
                "evidence_date": "2026-05-01",
                "amount": "120000.00",
                "content_hash": "sha256:safe-test",
                "file_name": raw_filename,
                "ocr_text": f"{secret} " + ("private text " * 40),
            }
        ]
    )
    serialized = json.dumps(report, ensure_ascii=False)

    assert report["item_reviews"][0]["evidence_id"].startswith("hash:")
    assert "private text private text private text" not in serialized
    assert raw_filename not in serialized
    assert SENSITIVE_PATTERN.search(serialized) is None
    assert report["metadata_gap_counts"]["raw_text_field_present"] == 1
    assert report["metadata_gap_counts"]["sensitive_value_detected"] >= 1


def test_evidence_bundle_integrity_route_is_callable():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post("/api/v1/maintenance/evidence/bundle-integrity", json={"items": _valid_items()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["score"] == 100
