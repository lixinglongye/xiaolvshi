import json
import re

from services.legal_benchmark_research_refresh import LegalBenchmarkResearchRefreshService


SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN PRIVATE KEY|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
NETWORK_COMMAND_PATTERN = re.compile(r"\b(curl|wget|Invoke-WebRequest|iwr)\b", re.IGNORECASE)


def test_research_refresh_maps_four_sources_without_downloads_or_model_calls():
    refresh = LegalBenchmarkResearchRefreshService().build_refresh()

    assert refresh["status"] == "ready"
    assert refresh["method"]["type"] == "legal-benchmark-research-refresh"
    assert refresh["summary"]["source_count"] == 4
    assert {source["id"] for source in refresh["research_sources"]} == {
        "legalbench",
        "lexglue",
        "coliee",
        "frugalgpt",
    }
    assert refresh["summary"]["dataset_downloaded"] is False
    assert refresh["summary"]["network_called"] is False
    assert refresh["summary"]["model_called"] is False
    assert refresh["summary"]["public_benchmark_score_claimed"] is False
    assert refresh["privacy_boundary"]["returns_dataset_samples"] is False
    assert refresh["privacy_boundary"]["returns_raw_legal_text"] is False
    assert refresh["claim_boundary"]["public_benchmark_scores_claimed"] is False
    assert refresh["claim_boundary"]["external_dataset_download_claimed"] is False
    json.dumps(refresh)


def test_research_refresh_links_sources_to_user_needs_and_local_evidence():
    refresh = LegalBenchmarkResearchRefreshService().build_refresh()
    rows = {row["source_id"]: row for row in refresh["refresh_rows"]}

    assert rows["legalbench"]["user_need_ids"] == [
        "traceable-legal-review",
        "plain-language-actionability",
    ]
    assert "robust-extraction-quality" in rows["lexglue"]["user_need_ids"]
    assert "prompt-injection-resilience" in rows["coliee"]["user_need_ids"]
    assert "cheap-first-review-routing" in rows["frugalgpt"]["user_need_ids"]
    assert all(row["local_evidence_paths"] for row in rows.values())
    assert all(row["release_gate_links"] for row in rows.values())
    assert all(row["dataset_download_required"] is False for row in rows.values())
    assert all(row["model_call_required"] is False for row in rows.values())
    assert all(row["public_score_claimed"] is False for row in rows.values())


def test_research_refresh_aggregates_user_need_rows_from_existing_coverage():
    refresh = LegalBenchmarkResearchRefreshService().build_refresh()
    need_rows = {row["need_id"]: row for row in refresh["user_need_rows"]}

    cheap_first = need_rows["cheap-first-review-routing"]
    traceable = need_rows["traceable-legal-review"]

    assert "frugalgpt" in cheap_first["source_ids"]
    assert cheap_first["cheap_first_relevant"] is True
    assert {"legalbench", "coliee"}.issubset(set(traceable["source_ids"]))
    assert traceable["public_benchmark_status"] in {
        "sampling_ready",
        "license_review_required",
        "catalog_only",
        "not_mapped",
    }
    assert all(command.startswith("python -m pytest ") for command in cheap_first["validation_commands"])


def test_research_refresh_validation_commands_are_local_only_and_secret_free():
    refresh = LegalBenchmarkResearchRefreshService().build_refresh()
    payload_text = json.dumps(refresh, ensure_ascii=False)
    commands_text = "\n".join(refresh["validation_commands"])

    assert not SECRET_PATTERN.search(payload_text)
    assert not NETWORK_COMMAND_PATTERN.search(commands_text)
    assert all(command.startswith("python -m pytest ") for command in refresh["validation_commands"])
    assert all("http" not in command.lower() for command in refresh["validation_commands"])
    assert all("://" not in command for command in refresh["validation_commands"])


def test_research_refresh_routes_return_refresh_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    for path in (
        "/api/v1/maintenance/legal-benchmark-research-refresh",
        "/api/v1/maintenance/legal-review-benchmark/research-refresh",
    ):
        response = client.get(path)

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["summary"]["source_count"] == 4
        assert payload["data"]["privacy_boundary"]["network_called"] is False
