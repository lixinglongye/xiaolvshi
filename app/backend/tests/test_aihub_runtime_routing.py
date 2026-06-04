import pytest

from schemas.aihub import ChatMessage, GenTxtRequest
from services import route_telemetry_repository
from services.model_route_telemetry import model_route_telemetry_registry
from services.model_usage import model_usage_registry
from services.route_telemetry_repository import RouteTelemetryRepositoryService

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


class _FailingCompletions:
    async def create(self, **params):
        raise RuntimeError("provider timeout")


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FailingChat:
    def __init__(self) -> None:
        self.completions = _FailingCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


class _FailingClient:
    def __init__(self) -> None:
        self.chat = _FailingChat()


@pytest.fixture(autouse=True)
def _isolated_route_telemetry_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))


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
    assert fake_client.chat.completions.calls[0]["temperature"] == 0
    assert fake_client.chat.completions.calls[0]["max_tokens"] == 4096
    assert response.model == "gemini-2.5-flash"
    assert response.task == "review"
    assert response.budget_decision["budget_mode"] == "balanced"
    assert response.budget_decision["routed_to_recommended_model"] is False
    assert response.reasoning_policy["effective_effort"] == "low"
    assert response.request_policy["effective_max_tokens"] == 4096

    usage = model_usage_registry.snapshot()["models"]["gemini-2.5-flash"]
    assert usage["tasks"] == {"review": 1}
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["request_count"] == 1
    assert route_snapshot["by_task"]["review"]["explicit_task"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["summary"]["stored_event_count"] == 1
    assert repository["totals"]["request_count"] == 1
    assert repository["daily_buckets"][0]["task"] == "review"
    assert "review this clause" not in str(repository)


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
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["daily_buckets"][0]["inference_source"] == "auto"
    assert "Review this contract clause" not in str(repository)


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
    assert fake_client.chat.completions.calls[0]["temperature"] == 0.1
    assert fake_client.chat.completions.calls[0]["max_tokens"] == 1024
    assert response.model == "gemini-2.5-flash-lite"
    assert response.budget_decision["requested_resolved_model"] == "gemini-2.5-pro"
    assert response.budget_decision["routed_to_recommended_model"] is True
    assert response.reasoning_policy["cost_mode"] == "thinking-disabled"
    assert response.request_policy["cost_mode"] == "policy-default"
    assert "sk-" not in str(response.model_dump())
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["downgrade_ratio"] == 1.0
    assert route_snapshot["summary"]["operator_review_request_count"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["totals"]["downgrade_count"] == 1
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert repository["daily_buckets"][0]["routed_to_recommended_model"] is True


@pytest.mark.asyncio
async def test_gentxt_persists_sanitized_route_failure_without_prompt_text():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    service.client = _FailingClient()

    with pytest.raises(RuntimeError):
        await service.gentxt(
            GenTxtRequest(
                messages=[ChatMessage(role="user", content="PRIVATE CLIENT PROMPT SHOULD NOT PERSIST")],
                task="fast",
                model="gemini-2.5-pro",
            )
        )

    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["request_count"] == 1
    assert route_snapshot["summary"]["failure_rate"] == 1.0
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["totals"]["request_count"] == 1
    assert repository["totals"]["failure_count"] == 1
    assert repository["daily_buckets"][0]["success"] is False
    assert "PRIVATE CLIENT PROMPT" not in rendered
    assert "provider timeout" not in rendered
