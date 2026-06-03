import re

from services.contract_clause_extraction_schema import ContractClauseExtractionSchemaService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _complete_clauses() -> list[dict]:
    return [
        {
            "clause_id": clause_type,
            "clause_type": clause_type,
            "heading": clause_type.replace("_", " ").title(),
            "summary": "metadata-only summary",
            "risk_level": "low",
            "source_anchor": f"section-{index}",
        }
        for index, clause_type in enumerate(
            [
                "parties",
                "payment",
                "delivery",
                "term",
                "termination",
                "liability",
                "dispute_resolution",
            ],
            start=1,
        )
    ]


def test_contract_clause_extraction_schema_returns_template():
    payload = ContractClauseExtractionSchemaService().build_schema()

    assert payload["status"] == "template"
    assert payload["summary"]["submitted_clause_count"] == 0
    assert payload["schema_version"] == "contract-clause-extraction-v1"
    assert "payment" in payload["clause_types"]
    assert any(field["id"] == "source_anchor" for field in payload["fields"])


def test_contract_clause_extraction_schema_allows_complete_low_risk_set():
    payload = ContractClauseExtractionSchemaService().build_schema(_complete_clauses())

    assert payload["status"] == "ready"
    assert payload["summary"]["ready_for_clause_level_review"] is True
    assert payload["summary"]["missing_required_clause_types"] == []
    assert payload["risk_flags"] == []
    assert {review["status"] for review in payload["clause_reviews"]} == {"pass"}


def test_contract_clause_extraction_schema_blocks_missing_required_and_source_anchor():
    clauses = _complete_clauses()[:3]
    clauses[0]["source_anchor"] = ""

    payload = ContractClauseExtractionSchemaService().build_schema(clauses)
    flag_ids = {flag["id"] for flag in payload["risk_flags"]}

    assert payload["status"] == "blocked"
    assert "missing-required-clause-types" in flag_ids
    assert "missing_source_anchor" in flag_ids
    assert "termination" in payload["summary"]["missing_required_clause_types"]


def test_contract_clause_extraction_schema_blocks_high_risk_without_review():
    clauses = _complete_clauses()
    clauses[1]["risk_level"] = "critical"
    clauses[1]["lawyer_review_required"] = False
    clauses[1]["proposed_edit_required"] = False

    payload = ContractClauseExtractionSchemaService().build_schema(clauses)
    flag_ids = {flag["id"] for flag in payload["risk_flags"]}

    assert payload["status"] == "blocked"
    assert "high_risk_without_lawyer_review" in flag_ids
    assert "critical_clause_without_proposed_edit" in flag_ids


def test_contract_clause_extraction_schema_sanitizes_sensitive_metadata():
    clauses = _complete_clauses()
    clauses[0]["heading"] = "client@example.com"
    clauses[0]["summary"] = "password " + "s" + "k-" + "a" * 24

    payload = ContractClauseExtractionSchemaService().build_schema(clauses)
    rendered = str(payload)

    assert "[redacted]" in rendered
    assert not SECRET_PATTERN.search(rendered)
    assert "password sk-" not in rendered.lower()


def test_contract_clause_extraction_schema_validation_commands_are_local():
    payload = ContractClauseExtractionSchemaService().build_schema()

    assert payload["validation_commands"] == [
        "python -m pytest tests/test_contract_clause_extraction_schema.py -q",
        "python -m compileall services/contract_clause_extraction_schema.py tests/test_contract_clause_extraction_schema.py",
    ]


def test_contract_clause_extraction_schema_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/contract-clause-extraction-schema")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "template"

    reviewed = client.post("/api/v1/maintenance/contract-clause-extraction-schema", json=_complete_clauses())

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "ready"
