import json
import re

from fastapi.testclient import TestClient

from main import app
from services.legal_public_benchmark_license_gate import LegalPublicBenchmarkLicenseGateService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_public_benchmark_license_gate_blocks_unreviewed_public_sources():
    gate = LegalPublicBenchmarkLicenseGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)
    source_rows = {row["source_id"]: row for row in gate["source_rows"]}

    assert gate["status"] == "review_required"
    assert gate["summary"]["source_count"] >= 7
    assert gate["summary"]["license_review_required_source_count"] >= 6
    assert gate["summary"]["catalog_only_source_count"] >= 1
    assert gate["summary"]["approved_source_count"] == 0
    assert gate["summary"]["release_claim_blocked_source_count"] == gate["summary"]["source_count"]
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["dataset_downloaded"] is False
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert source_rows["legalbench"]["decision"] == "block_public_sample_import"
    assert source_rows["legalbench"]["raw_text_import_allowed"] is False
    assert source_rows["legalbench"]["public_score_claim_allowed"] is False
    assert source_rows["pile-of-law"]["decision"] == "keep_catalog_only"
    assert "traceable-legal-review" in source_rows["legalbench"]["linked_user_need_ids"]
    assert "legal-review-balanced" in source_rows["legalbench"]["linked_route_task_ids"]
    assert "source:legalbench" in gate["blocking_check_ids"]
    assert "source:legalbench" in gate["warning_check_ids"]
    assert "public benchmark evidence metadata-only" in gate["recommended_actions"][0]
    assert "returns_public_benchmark_text" in gate["privacy_boundary"]
    assert gate["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert gate["claim_boundary"]["public_benchmark_scores_claimed"] is False
    assert not SECRET_PATTERN.search(serialized)
    assert "raw_output" not in serialized
    assert "gateway_response" not in serialized


def test_public_benchmark_license_gate_allows_only_capped_metadata_sampling_after_explicit_review():
    gate = LegalPublicBenchmarkLicenseGateService().build_gate(
        {
            "license_reviews": {
                "legalbench": "approved",
                "cuad": "approved",
            }
        }
    )
    source_rows = {row["source_id"]: row for row in gate["source_rows"]}
    legalbench = source_rows["legalbench"]
    cuad = source_rows["cuad"]

    assert gate["status"] == "review_required"
    assert gate["summary"]["approved_source_count"] == 2
    assert gate["summary"]["sampling_ready_source_count"] == 2
    assert legalbench["review_state"] == "approved"
    assert legalbench["decision"] == "allow_capped_metadata_sampling"
    assert legalbench["raw_text_import_allowed"] is False
    assert legalbench["dataset_download_allowed"] is False
    assert cuad["decision"] == "allow_capped_metadata_sampling"
    assert "source:legalbench" not in gate["blocking_check_ids"]
    assert "source:cuad" not in gate["blocking_check_ids"]
    assert all(check["status"] == "pass" for check in legalbench["required_checks"])
    assert source_rows["pile-of-law"]["decision"] == "keep_catalog_only"
    assert source_rows["pile-of-law"]["release_claim_blocked"] is True


def test_public_benchmark_license_gate_user_need_rows_preserve_claim_blocks():
    gate = LegalPublicBenchmarkLicenseGateService().build_gate()
    need_rows = {row["need_id"]: row for row in gate["user_need_rows"]}

    assert gate["summary"]["linked_user_need_count"] >= 4
    assert need_rows["cheap-first-review-routing"]["release_claim_blocked"] is True
    assert need_rows["traceable-legal-review"]["blocked_source_ids"]
    assert "Keep public benchmark claims blocked" in need_rows["traceable-legal-review"]["next_action"]


def test_public_benchmark_license_gate_endpoint_get_and_post():
    client = TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/public-license-gate")
    assert get_response.status_code == 200
    get_payload = get_response.json()["data"]
    assert get_payload["id"] == "legal-public-benchmark-license-gate"
    assert get_payload["status"] == "review_required"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/public-license-gate",
        json={"license_reviews": {"legalbench": "approved"}},
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()["data"]
    source_rows = {row["source_id"]: row for row in post_payload["source_rows"]}
    assert source_rows["legalbench"]["decision"] == "allow_capped_metadata_sampling"
