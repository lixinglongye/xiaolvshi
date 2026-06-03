import json
import re

from services.legal_benchmark_research_registry import LegalBenchmarkResearchRegistryService


SOURCE_FIELDS = {
    "public_name",
    "public_link",
    "experience_takeaways",
    "project_mapping",
    "low_resource_action",
    "forbidden_claims",
}

SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN PRIVATE KEY")
NETWORK_COMMAND_PATTERN = re.compile(r"\b(curl|wget|Invoke-WebRequest|iwr)\b", re.IGNORECASE)
RISKY_CLAIM_PATTERN = re.compile(
    r"external adoption|production (effects?|accuracy|quality|retrieval|classification|legal qa)|"
    r"real (customer|client)|customer-data|client matters",
    re.IGNORECASE,
)


def test_registry_returns_api_ready_local_metadata_only_dict():
    registry = LegalBenchmarkResearchRegistryService().build_registry()

    assert registry["status"] == "ready"
    assert registry["method"]["type"] == "local-legal-benchmark-research-registry"
    assert registry["summary"]["source_count"] == 3
    assert registry["validation_commands"]
    assert registry["low_resource_strategy"]["network_access"] == "disabled_for_local_validation"
    assert registry["low_resource_strategy"]["dataset_downloads"] == "forbidden_in_default_tests"
    assert registry["low_resource_strategy"]["sensitive_data"] == "not_allowed"
    assert not SECRET_PATTERN.search(str(registry))
    json.dumps(registry)


def test_registry_covers_legalbench_lexglue_and_coliee_sources():
    registry = LegalBenchmarkResearchRegistryService().build_registry()
    sources_by_name = {source["public_name"]: source for source in registry["sources"]}

    assert set(sources_by_name) == {"LegalBench", "LexGLUE", "COLIEE"}
    assert all(set(source) == SOURCE_FIELDS for source in registry["sources"])
    assert all(source["public_link"].startswith("https://") for source in registry["sources"])
    assert "task-family coverage reference" in sources_by_name["LegalBench"]["low_resource_action"]
    assert "label-discipline reference" in sources_by_name["LexGLUE"]["low_resource_action"]
    assert "retrieval-and-entailment reference" in sources_by_name["COLIEE"]["low_resource_action"]


def test_registry_maps_public_benchmark_experience_to_local_low_resource_tests():
    registry = LegalBenchmarkResearchRegistryService().build_registry()
    mappings = {source["public_name"]: source["project_mapping"] for source in registry["sources"]}
    low_resource_actions = registry["low_resource_strategy"]["actions"]

    assert mappings["LegalBench"]["local_area"] == "legal_review_benchmark"
    assert "citation grounding" in mappings["LegalBench"]["fixture_focus"]
    assert mappings["LexGLUE"]["local_area"] == "legal_fixture_quick_suite"
    assert "classification" in mappings["LexGLUE"]["fixture_focus"]
    assert mappings["COLIEE"]["local_area"] == "legal_rag_evaluation"
    assert "missing-authority" in mappings["COLIEE"]["fixture_focus"]
    assert len(low_resource_actions) == 3
    assert all("synthetic" in action.lower() for action in low_resource_actions)
    assert registry["low_resource_strategy"]["fixture_cap"]["max_fixtures_per_source_without_review"] == 3


def test_registry_blocks_external_adoption_production_and_customer_data_claims():
    registry = LegalBenchmarkResearchRegistryService().build_registry()
    forbidden_text = " ".join(registry["forbidden_claims"])
    source_forbidden_text = " ".join(
        claim for source in registry["sources"] for claim in source["forbidden_claims"]
    )

    assert "external adoption" in forbidden_text
    assert "production effects" in forbidden_text
    assert "real customer data" in forbidden_text
    assert "real client" in source_forbidden_text
    assert all(not RISKY_CLAIM_PATTERN.search(claim) for claim in registry["allowed_claims"])


def test_validation_commands_are_local_pytest_commands_only():
    registry = LegalBenchmarkResearchRegistryService().build_registry()

    assert "python -m pytest tests/test_legal_benchmark_research_registry.py -q" in registry["validation_commands"]
    assert all(command.startswith("python -m pytest ") for command in registry["validation_commands"])
    assert all("http" not in command.lower() for command in registry["validation_commands"])
    assert not NETWORK_COMMAND_PATTERN.search(" ".join(registry["validation_commands"]))


def test_registry_route_returns_public_benchmark_mapping():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/research-registry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["source_names"] == ["LegalBench", "LexGLUE", "COLIEE"]
    assert payload["data"]["low_resource_strategy"]["dataset_downloads"] == "forbidden_in_default_tests"
