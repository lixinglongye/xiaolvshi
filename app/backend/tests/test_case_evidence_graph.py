import re

from services.case_evidence_graph import CaseEvidenceGraphService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def _supported_report() -> dict:
    return {
        "professional_review_framework": {
            "evidence_checklist": ["Signed contract", "Payment records"],
        },
        "legal_authority_appendix": [
            {
                "source_id": "civil-code-509",
                "source_name": "Civil Code Article 509",
                "source_type": "law",
                "authority_level": "primary",
            }
        ],
        "risk_items": [
            {
                "risk_id": "R-001",
                "title": "Payment default",
                "risk_level": "high",
                "legal_analysis": {
                    "evidence_suggestion": ["Keep signed contract.", "Keep transfer records."],
                },
                "citations": [
                    {
                        "source_id": "civil-code-509",
                        "source_name": "Civil Code Article 509",
                    }
                ],
            },
            {
                "risk_id": "R-002",
                "title": "Notice defect",
                "risk_level": "medium",
                "legal_analysis": {
                    "evidence_suggestion": ["Keep delivery notice screenshots."],
                },
            },
        ],
        "pending_facts": [
            {
                "field": "delivery date",
                "reason": "Needed for chronology",
                "impact": "May affect limitation analysis",
            }
        ],
    }


def test_case_evidence_graph_builds_review_ready_summary():
    graph = CaseEvidenceGraphService().build_graph(_supported_report())

    assert graph["status"] == "ready"
    assert graph["summary"]["risk_count"] == 2
    assert graph["summary"]["evidence_requirement_count"] == 3
    assert graph["summary"]["citation_count"] == 1
    assert graph["summary"]["blocking_gap_count"] == 0
    assert any(edge["type"] == "supports_risk_review" for edge in graph["edges"])
    assert any(edge["type"] == "cites_authority_for" for edge in graph["edges"])


def test_case_evidence_graph_flags_missing_high_risk_support():
    report = _supported_report()
    report["risk_items"][0]["legal_analysis"]["evidence_suggestion"] = []
    report["risk_items"][0]["citations"] = []
    report["pending_facts"] = [
        {
            "field": "signature authority",
            "reason": "Must confirm before filing",
            "impact": "Unable to judge authorization",
        }
    ]

    graph = CaseEvidenceGraphService().build_graph(report)
    flag_ids = {flag["id"] for flag in graph["gap_flags"]}

    assert graph["status"] == "blocked"
    assert "R-001-no-supporting-edge" in flag_ids
    assert "R-001-missing-reviewable-citation-edge" in flag_ids
    assert any(flag["severity"] == "blocking" for flag in graph["gap_flags"])


def test_case_evidence_graph_returns_template_without_report_data():
    graph = CaseEvidenceGraphService().build_graph()

    assert graph["status"] == "template"
    assert graph["summary"]["risk_count"] == 0
    assert graph["gap_flags"][0]["id"] == "no-risk-items"
    assert graph["validation_commands"]


def test_case_evidence_graph_uses_safe_metadata_only():
    graph = CaseEvidenceGraphService().build_graph(_supported_report())

    assert "privacy" in graph["privacy_note"].lower()
    assert not SECRET_PATTERN.search(str(graph))
    assert "raw client documents" in graph["privacy_note"]


def test_case_evidence_graph_route_returns_template_and_graph():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/case-evidence-graph")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post("/api/v1/maintenance/case-evidence-graph", json=_supported_report())
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
