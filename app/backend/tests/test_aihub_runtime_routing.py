import pytest

from schemas.aihub import ChatMessage, GenTxtRequest
from services.model_route_telemetry import model_route_telemetry_registry
from services.model_usage import model_usage_registry

pytest.importorskip("httpx")
from services.aihub import AIHubService


class _FakeUsage:
    prompt_tokens = 11
    completion_tokens = 7
    total_tokens = 18


class _FakeMessage:
    content = "ok"


class _FakeChoice:
    message = _FakeMessage()


class _FakeResponse:
    choices = [_FakeChoice()]
    usage = _FakeUsage()


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def create(self, **params):
        self.calls.append(params)
        return _FakeResponse()


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


@pytest.mark.asyncio
async def test_gentxt_uses_declared_review_task_default_model():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[ChatMessage(role="user", content="review this clause")],
            task="review",
            temperature=0,
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash"
    assert fake_client.chat.completions.calls[0]["reasoning_effort"] == "low"
    assert response.model == "gemini-2.5-flash"
    assert response.task == "review"
    assert response.budget_decision["budget_mode"] == "balanced"
    assert response.budget_decision["routed_to_recommended_model"] is False
    assert response.reasoning_policy["effective_effort"] == "low"

    usage = model_usage_registry.snapshot()["models"]["gemini-2.5-flash"]
    assert usage["tasks"] == {"review": 1}
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["request_count"] == 1
    assert route_snapshot["by_task"]["review"]["explicit_task"] == 1


@pytest.mark.asyncio
async def test_gentxt_auto_infers_legal_review_task():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content="Review this contract clause for liability and breach risk.",
                )
            ],
            temperature=0,
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash"
    assert response.task == "review"
    assert response.task_inference["source"] == "auto"
    assert response.task_inference["task"] == "review"
    assert response.budget_decision["budget_mode"] == "balanced"
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["auto_inferred_ratio"] == 1.0
    assert route_snapshot["by_inference_source"]["auto"]["models"] == {"gemini-2.5-flash": 1}


@pytest.mark.asyncio
async def test_gentxt_downgrades_fast_premium_request_by_default():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[ChatMessage(role="user", content="classify this")],
            task="fast",
            model="gemini-2.5-pro",
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash-lite"
    assert fake_client.chat.completions.calls[0]["reasoning_effort"] == "none"
    assert response.model == "gemini-2.5-flash-lite"
    assert response.budget_decision["requested_resolved_model"] == "gemini-2.5-pro"
    assert response.budget_decision["routed_to_recommended_model"] is True
    assert response.reasoning_policy["cost_mode"] == "thinking-disabled"
    assert "sk-" not in str(response.model_dump())
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["downgrade_ratio"] == 1.0
    assert route_snapshot["summary"]["operator_review_request_count"] == 1
