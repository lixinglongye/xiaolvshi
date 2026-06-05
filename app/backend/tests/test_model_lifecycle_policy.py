from services import model_lifecycle_policy
from services.model_lifecycle_policy import ModelLifecyclePolicyService


def _role(plan: dict, role: str) -> dict:
    return next(item for item in plan["configured_roles"] if item["role"] == role)


def test_lifecycle_policy_passes_stable_cheap_first_defaults(monkeypatch):
    monkeypatch.setattr(model_lifecycle_policy, "cheap_text_model", lambda: "gemini-2.5-flash-lite")
    monkeypatch.setattr(
        model_lifecycle_policy,
        "task_default_model",
        lambda task: {
            "cheap": "gemini-2.5-flash-lite",
            "fast": "gemini-2.5-flash-lite",
            "ocr": "gemini-2.5-flash-lite",
            "classification": "gemini-2.5-flash-lite",
            "review": "gemini-2.5-flash",
            "grounded-research": "gemini-3.1-flash-lite",
            "agentic": "gemini-3.1-flash-lite",
            "pdf": "gemini-2.5-pro",
        }.get(task, "gemini-2.5-flash"),
    )

    plan = ModelLifecyclePolicyService().build_policy()

    assert plan["status"] == "pass"
    assert plan["summary"]["deprecated_default_count"] == 0
    assert plan["summary"]["latest_alias_default_count"] == 0
    assert _role(plan, "fast")["cheap_first_aligned"] is True
    assert _role(plan, "agentic")["model"] == "gemini-3.1-flash-lite"
    assert _role(plan, "grounded-research")["model"] == "gemini-3.1-flash-lite"
    assert "sk-" not in str(plan)


def test_lifecycle_policy_warns_on_preview_and_latest_defaults(monkeypatch):
    monkeypatch.setattr(model_lifecycle_policy, "cheap_text_model", lambda: "gemini-2.5-flash-lite")
    monkeypatch.setattr(
        model_lifecycle_policy,
        "task_default_model",
        lambda task: {
            "fast": "gemini-2.5-flash-lite",
            "ocr": "gemini-2.5-flash-lite",
            "classification": "gemini-2.5-flash-lite",
            "review": "gemini-3.1-pro-preview",
            "grounded-research": "gemini-3.1-flash-lite",
            "agentic": "gemini-3.1-flash-lite",
            "pdf": "gemini-2.5-pro-latest",
        }.get(task, "gemini-2.5-flash"),
    )

    plan = ModelLifecyclePolicyService().build_policy()

    assert plan["status"] == "warn"
    assert plan["summary"]["preview_default_count"] >= 1
    assert plan["summary"]["latest_alias_default_count"] >= 1
    assert "preview-default-review" in plan["warning_check_ids"]
    assert _role(plan, "review")["lifecycle_state"] == "preview"
    assert _role(plan, "pdf")["lifecycle_state"] == "unstable_alias"


def test_lifecycle_policy_blocks_deprecated_defaults(monkeypatch):
    monkeypatch.setattr(model_lifecycle_policy, "cheap_text_model", lambda: "gemini-2.0-flash-lite")
    monkeypatch.setattr(model_lifecycle_policy, "task_default_model", lambda task: "gemini-2.0-flash-lite")

    plan = ModelLifecyclePolicyService().build_policy()

    assert plan["status"] == "fail"
    assert plan["summary"]["deprecated_default_count"] >= 1
    assert "no-deprecated-defaults" in plan["blocking_check_ids"]
    assert "default-allow-list" in plan["blocking_check_ids"]


def test_lifecycle_policy_warns_unknown_gateway_defaults(monkeypatch):
    monkeypatch.setattr(model_lifecycle_policy, "cheap_text_model", lambda: "newapi/gemini-custom-cheap")
    monkeypatch.setattr(model_lifecycle_policy, "task_default_model", lambda task: "newapi/gemini-custom-cheap")

    plan = ModelLifecyclePolicyService().build_policy()

    assert plan["status"] == "warn"
    assert plan["summary"]["unknown_default_count"] >= 1
    assert "known-default-lifecycle" in plan["warning_check_ids"]


def test_model_ops_route_includes_lifecycle_policy():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lifecycle_policy"]["status"] in {"pass", "warn", "fail"}
    assert any(check["source_key"] == "lifecycle_policy" for check in payload["model_ops_readiness"]["checks"])
