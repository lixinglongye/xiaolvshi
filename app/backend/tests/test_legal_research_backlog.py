import re

from services.legal_research_backlog import LegalResearchBacklogService, priority_band, priority_score


def test_legal_research_backlog_tracks_primary_research_sources():
    backlog = LegalResearchBacklogService().build_backlog()
    source_ids = {source["id"] for source in backlog["method"]["input_sources"]}

    assert backlog["status"] == "ready"
    assert {"legalbench", "frugalgpt", "ragas", "crag", "cuad", "legalbench-rag", "lexeval", "casegen"}.issubset(
        source_ids
    )
    assert backlog["summary"]["source_count"] >= 8
    assert backlog["summary"]["backlog_item_count"] >= 8
    assert backlog["summary"]["high_priority_count"] >= 2
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", str(backlog))


def test_legal_research_backlog_prioritizes_cheap_first_local_runs():
    backlog = LegalResearchBacklogService().build_backlog()
    top_item = backlog["backlog"][0]
    cheap_item = next(item for item in backlog["backlog"] if item["id"] == "cheap-first-cascade-evaluation")

    assert top_item["id"] == "cheap-first-cascade-evaluation"
    assert cheap_item["priority_band"] == "high"
    assert "frugalgpt" in cheap_item["source_ids"]
    assert "cheap-first-review-routing" in cheap_item["user_need_ids"]
    assert cheap_item["local_run_fit"] >= 8
    assert any("Gemini/NewAPI" in action for action in cheap_item["next_actions"])


def test_legal_research_backlog_maps_rag_sources_to_grounding_gates():
    backlog = LegalResearchBacklogService().build_backlog()
    grounding = next(item for item in backlog["backlog"] if item["id"] == "rag-grounding-metric-gates")

    assert {"ragas", "crag"}.issubset(set(grounding["source_ids"]))
    assert "legal-rag-evaluation" in grounding["release_gate_links"]
    assert "citation_audit" in grounding["release_gate_links"]
    assert any(path.endswith("legal_rag_evaluation.py") for path in grounding["evidence_paths"])


def test_legal_research_backlog_maps_chinese_benchmark_sources_to_fixture_work():
    backlog = LegalResearchBacklogService().build_backlog()
    refresh = next(item for item in backlog["backlog"] if item["id"] == "chinese-legal-benchmark-fixture-refresh")
    output_gates = next(item for item in backlog["backlog"] if item["id"] == "casegen-document-output-gates")

    assert {"lexeval", "legalbench-rag", "casegen"}.issubset(set(refresh["source_ids"]))
    assert "user-need-benchmark-coverage" in refresh["release_gate_links"]
    assert "legal_document_benchmark_fixtures.py" in " ".join(output_gates["evidence_paths"])
    assert "plain-language-actionability" in output_gates["user_need_ids"]


def test_legal_research_backlog_builds_workstream_plan_and_queue():
    backlog = LegalResearchBacklogService().build_backlog()
    plan_by_stream = {row["workstream"]: row for row in backlog["workstream_plan"]}

    assert {"model_ops", "benchmark_design", "retrieval_quality"}.issubset(plan_by_stream)
    assert backlog["next_iteration_queue"][0]["item_id"] == "cheap-first-cascade-evaluation"
    assert all(row["release_gate_links"] for row in backlog["next_iteration_queue"])
    assert any("cheap-first" in action for action in backlog["maintenance_actions"])


def test_research_backlog_priority_score_and_band_are_bounded():
    assert priority_score(impact=10, effort=0, confidence=10, cost_sensitivity=10, local_run_fit=10) == 100
    assert priority_score(impact=1, effort=20, confidence=1, cost_sensitivity=0, local_run_fit=0) == 0
    assert priority_band(70) == "high"
    assert priority_band(45) == "medium"
    assert priority_band(44) == "low"


def test_legal_research_backlog_route_returns_backlog():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/research-backlog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["backlog_item_count"] >= 6
