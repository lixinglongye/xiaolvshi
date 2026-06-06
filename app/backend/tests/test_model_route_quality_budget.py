import json
import re

from services import model_catalog
from services.model_catalog import ModelProfile
from services.model_route_quality_budget import ModelRouteQualityBudgetService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_route_quality_budget_exposes_cheap_first_quality_gates():
    budget = ModelRouteQualityBudgetService().build_budget()
    rows = {row["task"]: row for row in budget["task_quality_budgets"]}

    assert budget["status"] == "pass"
    assert budget["summary"]["task_count"] >= 8
    assert budget["summary"]["cheap_start_task_count"] >= 6
    assert budget["summary"]["quality_gate_count"] >= 20
    assert budget["summary"]["raw_payload_echoed"] is False
    assert budget["warning_check_ids"] == []
    assert rows["fast"]["cheap_start_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["review_action"] == "cheap_first_with_quality_gate"
    assert rows["review"]["quality_gate_count"] >= 3
    assert rows["grounded-research"]["runtime_default_model"] == "gemini-3.1-flash-lite"
    assert rows["grounded-research"]["runtime_default_has_required_capabilities"] is True
    assert rows["agentic"]["runtime_default_model"] == "gemini-3.1-flash-lite"
    assert rows["agentic"]["runtime_default_has_required_capabilities"] is True
    assert budget["privacy_boundary"]["raw_model_output_included"] is False


def test_route_quality_budget_can_filter_to_passing_low_cost_tasks():
    budget = ModelRouteQualityBudgetService().build_budget({"tasks": ["fast", "ocr", "classification"]})
    rows = {row["task"]: row for row in budget["task_quality_budgets"]}

    assert budget["status"] == "pass"
    assert set(rows) == {"fast", "ocr", "classification"}
    assert budget["warning_check_ids"] == []
    assert all(row["cheap_start_model"] == "gemini-2.5-flash-lite" for row in rows.values())


def test_route_quality_budget_cheap_start_follows_catalog_derived_selector(monkeypatch):
    future_model = ModelProfile(
        id="gemini-4.0-flash-lite",
        provider="google",
        family="gemini",
        cost_tier="lowest",
        latency_tier="fastest",
        capabilities=("text", "vision", "json", "ocr", "classification", "grounding", "agentic"),
        best_for=("routing", "ocr", "classification", "agentic-routing"),
        input_usd_per_million_tokens=0.05,
        output_usd_per_million_tokens=0.20,
        status="stable",
        context_window_tokens=1_000_000,
    )
    monkeypatch.setattr(
        model_catalog,
        "GEMINI_MODEL_CATALOG",
        (future_model, *model_catalog.GEMINI_MODEL_CATALOG),
    )

    budget = ModelRouteQualityBudgetService().build_budget({"tasks": ["fast", "review", "agentic"]})
    rows = {row["task"]: row for row in budget["task_quality_budgets"]}

    assert budget["status"] == "pass"
    assert rows["fast"]["cheap_start_model"] == "gemini-4.0-flash-lite"
    assert rows["review"]["cheap_start_model"] == "gemini-2.5-flash"
    assert rows["agentic"]["cheap_start_model"] == "gemini-4.0-flash-lite"
    assert rows["fast"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["review"]["recommended_model"] == "gemini-2.5-flash"


def test_route_quality_budget_drops_sensitive_task_filters():
    secret = "s" + "k-" + "a" * 24
    budget = ModelRouteQualityBudgetService().build_budget(
        {"tasks": ["fast", f"{secret}", "client@example.com"]}
    )
    serialized = json.dumps(budget, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert {row["task"] for row in budget["task_quality_budgets"]} == {"fast"}
    assert budget["summary"]["raw_payload_echoed"] is False


def test_route_quality_budget_endpoint_returns_metadata_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models/route-quality-budget")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["cheap_start_task_count"] >= 6
    assert payload["data"]["privacy_boundary"]["prompts_included"] is False
