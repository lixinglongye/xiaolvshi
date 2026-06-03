import json
import re

from services.legal_document_template_matrix import LegalDocumentTemplateMatrixService


SENSITIVE_PATTERN = re.compile(
    "(sk-[A-Za-z0-9]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|"
    "password\\s*[=:]|secret\\s*[=:]|\u5bc6\u7801\\s*[=:])",
    re.IGNORECASE,
)


def test_legal_document_template_matrix_covers_core_document_types():
    matrix = LegalDocumentTemplateMatrixService().build_matrix()
    document_types = {row["document_type"] for row in matrix["document_types"]}

    assert matrix["status"] == "ready"
    assert matrix["summary"]["document_type_count"] >= 5
    assert {
        "\u6c11\u4e8b\u8d77\u8bc9\u72b6",
        "\u7b54\u8fa9\u72b6",
        "\u8bc1\u636e\u76ee\u5f55",
        "\u5f8b\u5e08\u51fd",
        "\u5408\u540c\u5ba1\u67e5\u62a5\u544a",
    }.issubset(document_types)


def test_each_document_type_has_delivery_contract_fields():
    matrix = LegalDocumentTemplateMatrixService().build_matrix()

    for row in matrix["document_types"]:
        assert row["required_fields"], row["document_type"]
        assert row["format_requirements"], row["document_type"]
        assert row["pre_generation_blockers"], row["document_type"]
        assert row["export_formats"], row["document_type"]
        assert {"docx", "pdf"}.issubset(set(row["export_formats"]))
        assert row["review_gate"]["id"] == "lawyer-review-required"
        assert row["review_gate"]["critical"] is True


def test_lawyer_review_is_critical_gate_for_every_document():
    matrix = LegalDocumentTemplateMatrixService().build_matrix()
    gate = matrix["lawyer_review_gate"]

    assert gate["critical"] is True
    assert "client_delivery" in gate["required_before"]
    assert "court_filing" in gate["required_before"]
    assert matrix["summary"]["review_gate_required_count"] == matrix["summary"]["document_type_count"]
    assert all(row["review_gate"]["critical"] for row in matrix["document_types"])
    assert all("\u5f8b\u5e08" in row["review_gate"]["label"] for row in matrix["document_types"])


def test_matrix_includes_low_resource_validation_commands():
    matrix = LegalDocumentTemplateMatrixService().build_matrix()

    assert matrix["low_resource_validation_commands"]
    assert any(
        "test_legal_document_template_matrix.py" in command
        for command in matrix["low_resource_validation_commands"]
    )
    assert all(command.startswith("python -m pytest ") for command in matrix["low_resource_validation_commands"])
    assert all(row["low_resource_validation_command"].startswith("python -m pytest ") for row in matrix["document_types"])


def test_matrix_does_not_expose_sensitive_patterns():
    matrix = LegalDocumentTemplateMatrixService().build_matrix()
    text = json.dumps(matrix, ensure_ascii=False)

    assert SENSITIVE_PATTERN.search(text) is None


def test_legal_document_template_matrix_route_returns_matrix():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-document-template-matrix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["document_type_count"] >= 5
