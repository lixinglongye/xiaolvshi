from services import model_budget


def test_budget_policy_prefers_cheap_fast_tasks(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_cheap_model", "gemini-2.5-flash-lite", raising=False)

    decision = model_budget.model_budget_decision(None, task="classification")

    assert decision.task == "classification"
    assert decision.resolved_model == "gemini-2.5-flash-lite"
    assert decision.budget_mode == "cheap-first"
    assert decision.cost_tier == "lowest"
    assert not decision.is_over_budget


def test_budget_policy_flags_premium_model_for_fast_task(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_premium_requires_review", True, raising=False)

    decision = model_budget.model_budget_decision("gemini-2.5-pro", task="fast")

    assert decision.resolved_model == "gemini-2.5-pro"
    assert decision.cost_tier == "premium"
    assert decision.is_over_budget
    assert decision.requires_operator_review
    assert decision.recommended_model == model_budget.task_default_model("fast")


def test_budget_policy_allows_pdf_premium_exception(monkeypatch):
    monkeypatch.setattr(model_budget.settings, "app_ai_pdf_model", "gemini-2.5-pro", raising=False)

    decision = model_budget.model_budget_decision(None, task="pdf")

    assert decision.budget_mode == "premium-exception"
    assert decision.resolved_model == "gemini-2.5-pro"
    assert not decision.is_over_budget
    assert not decision.requires_operator_review


def test_budget_policy_for_api_lists_all_core_tasks():
    payload = model_budget.budget_policy_for_api()
    tasks = {item["task"] for item in payload["task_decisions"]}

    assert tasks == {"fast", "ocr", "classification", "review", "pdf", "image"}
    assert payload["premium_requires_review"] in {True, False}
