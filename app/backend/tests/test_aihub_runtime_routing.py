import io
import json

import pytest

from schemas.aihub import (
    AnalyzePdfRequest,
    ChatMessage,
    GenAudioRequest,
    GenImgRequest,
    GenTxtRequest,
    GenVideoRequest,
    TranscribeAudioRequest,
)
from services import route_telemetry_repository
from services.model_catalog import estimate_token_cost_usd
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
    content = "MODEL_OUTPUT_SHOULD_NOT_PERSIST"


class _FakeChoice:
    message = _FakeMessage()


class _FakeResponse:
    choices = [_FakeChoice()]
    usage = _FakeUsage()


class _FakeStreamDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeStreamChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = _FakeStreamDelta(content)


class _FakeStreamChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeStreamChoice(content)]


async def _fake_stream_chunks():
    for content in ("hello", " stream"):
        yield _FakeStreamChunk(content)


class _FakeImageItem:
    url = "https://cdn.example.test/generated-private-output.png"
    revised_prompt = "sanitized revised prompt"


class _FakeImageResponse:
    data = [_FakeImageItem()]


class _FakeVideoResponse:
    id = "video-1"
    status = "completed"
    url = "https://cdn.example.test/generated-private-video.mp4"
    seconds = "4"
    revised_prompt = "sanitized video prompt"


class _FakeSpeechResponse:
    url = "https://cdn.example.test/generated-private-audio.mp3"


class _FakeTranscriptionResponse:
    text = "TRANSCRIBED_OUTPUT_SHOULD_NOT_PERSIST"


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def create(self, **params):
        self.calls.append(params)
        return _FakeResponse()


class _FakeStreamingCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def create(self, **params):
        self.calls.append(params)
        return _fake_stream_chunks()


class _FailingCompletions:
    async def create(self, **params):
        raise RuntimeError("provider timeout")


class _FakeImages:
    def __init__(self) -> None:
        self.generate_calls: list[dict] = []
        self.edit_calls: list[dict] = []

    async def generate(self, **params):
        self.generate_calls.append(params)
        return _FakeImageResponse()

    async def edit(self, **params):
        self.edit_calls.append(params)
        return _FakeImageResponse()


class _FakeVideos:
    def __init__(self) -> None:
        self.create_calls: list[dict] = []
        self.retrieve_calls: list[str] = []

    async def create(self, **params):
        self.create_calls.append(params)
        return _FakeVideoResponse()

    async def retrieve(self, video_id):
        self.retrieve_calls.append(video_id)
        return _FakeVideoResponse()


class _FakeSpeech:
    def __init__(self) -> None:
        self.create_calls: list[dict] = []

    async def create(self, **params):
        self.create_calls.append(params)
        return _FakeSpeechResponse()


class _FakeTranscriptions:
    def __init__(self) -> None:
        self.create_calls: list[dict] = []

    async def create(self, **params):
        self.create_calls.append(params)
        return _FakeTranscriptionResponse()


class _FakeAudio:
    def __init__(self) -> None:
        self.speech = _FakeSpeech()
        self.transcriptions = _FakeTranscriptions()


class _FailingImages:
    async def generate(self, **params):
        raise RuntimeError("provider leaked raw image prompt")

    async def edit(self, **params):
        raise RuntimeError("provider leaked raw image prompt")


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeStreamingChat:
    def __init__(self) -> None:
        self.completions = _FakeStreamingCompletions()


class _FailingChat:
    def __init__(self) -> None:
        self.completions = _FailingCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()
        self.images = _FakeImages()
        self.videos = _FakeVideos()
        self.audio = _FakeAudio()


class _FakeStreamingClient(_FakeClient):
    def __init__(self) -> None:
        super().__init__()
        self.chat = _FakeStreamingChat()


class _FailingClient:
    def __init__(self) -> None:
        self.chat = _FailingChat()
        self.images = _FailingImages()


@pytest.fixture(autouse=True)
def _isolated_route_telemetry_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))


def test_aihub_service_normalizes_bare_remote_gateway_base_url(monkeypatch):
    from services import aihub

    monkeypatch.setattr(aihub.settings, "app_ai_base_url", "https://yibuapi.com")
    monkeypatch.setattr(aihub.settings, "app_ai_key", "local-redacted-key")

    service = AIHubService()

    assert service.client is not None
    assert str(service.client.base_url).rstrip("/") == "https://yibuapi.com/v1"
    assert "local-redacted-key" not in str(service.client.base_url)


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
    expected_cost = estimate_token_cost_usd("gemini-2.5-flash", 11, 7)
    assert repository["summary"]["stored_event_count"] == 1
    assert repository["totals"]["request_count"] == 1
    assert repository["totals"]["estimated_cost_usd_sum"] == expected_cost
    assert repository["daily_buckets"][0]["task"] == "review"
    assert repository["daily_buckets"][0]["estimated_cost_usd_sum"] == expected_cost
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
    assert repository["daily_buckets"][0]["reason_code_counts"]["task_default_selected"] == 1
    assert repository["daily_buckets"][0]["reason_code_counts"]["resolved_to_recommended_model"] == 1
    assert "Review this contract clause" not in str(repository)


@pytest.mark.parametrize(
    ("requested_task", "normalized_task", "forbidden_model"),
    [
        ("image", "image", "gemini-2.5-flash-image"),
        ("video", "video", "wan2.6-t2v"),
        ("audio", "audio", "qwen3-tts-flash"),
        ("transcription", "transcription", "scribe_v2"),
        ("tts", "audio", "qwen3-tts-flash"),
        ("speech-to-text", "transcription", "scribe_v2"),
    ],
)
@pytest.mark.asyncio
async def test_gentxt_blocks_media_tasks_from_media_defaults(requested_task, normalized_task, forbidden_model):
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[ChatMessage(role="user", content="Generate text only.")],
            task=requested_task,
            temperature=0,
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash"
    assert fake_client.chat.completions.calls[0]["model"] != forbidden_model
    assert response.model == "gemini-2.5-flash"
    assert response.task == "review"
    assert response.task_inference["task"] == "review"
    assert response.task_inference["source"] == "explicit"
    assert f"unsupported_for_gentxt:{normalized_task}" in response.task_inference["signals"]
    assert response.budget_decision["budget_mode"] == "balanced"
    assert response.budget_decision["requested_model"] is None
    assert response.budget_decision["explicit_model_requested"] is False
    assert response.budget_decision["explicit_model_fit_status"] == "default"
    assert "task_default_selected" in response.budget_decision["reason_codes"]
    assert "sk-" not in str(response.model_dump())

    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["review"]["explicit_task"] == 1
    assert route_snapshot["by_task"].get(normalized_task) is None
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["daily_buckets"][0]["task"] == "review"
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-flash"
    assert forbidden_model not in str(repository)
    assert "Generate text only." not in str(repository)


@pytest.mark.asyncio
async def test_gentxt_stream_events_emit_sanitized_route_metadata_before_content():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeStreamingClient()
    service.client = fake_client

    events = [
        event
        async for event in service.gentxt_stream_events(
            GenTxtRequest(
                messages=[ChatMessage(role="user", content="Review this contract clause for risk.")],
                stream=True,
                temperature=0,
            )
        )
    ]

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash"
    assert fake_client.chat.completions.calls[0]["stream"] is True
    assert events[0]["type"] == "metadata"
    assert events[0]["content"] == ""
    assert events[0]["metadata"]["model"] == "gemini-2.5-flash"
    assert events[0]["metadata"]["task"] == "review"
    assert events[0]["metadata"]["budget_decision"]["budget_mode"] == "balanced"
    assert events[0]["metadata"]["task_inference"]["task"] == "review"
    assert events[0]["metadata"]["request_policy"]["effective_temperature"] == 0
    assert [event["content"] for event in events[1:]] == ["hello", " stream"]
    serialized = json.dumps(events, ensure_ascii=False)
    assert "Review this contract clause" not in serialized
    assert "sk-" not in serialized

    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["totals"]["stream_requests"] == 1
    assert route_snapshot["by_task"]["review"]["stream_requests"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["daily_buckets"][0]["task"] == "review"
    assert "Review this contract clause" not in str(repository)


@pytest.mark.asyncio
async def test_gentxt_stream_legacy_wrapper_returns_content_only():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeStreamingClient()
    service.client = fake_client

    chunks = [
        chunk
        async for chunk in service.gentxt_stream(
            GenTxtRequest(
                messages=[ChatMessage(role="user", content="Review this contract clause for risk.")],
                stream=True,
            )
        )
    ]

    assert chunks == ["hello", " stream"]
    assert all("metadata" not in chunk for chunk in chunks)
    assert all("budget_decision" not in chunk for chunk in chunks)
    assert model_route_telemetry_registry.snapshot()["totals"]["stream_requests"] == 1


def test_gentxt_stream_route_emits_metadata_sse_before_content(monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    import routers.aihub as aihub_router

    class FakeStreamService:
        async def gentxt_stream_events(self, request):
            yield {
                "type": "metadata",
                "content": "",
                "metadata": {
                    "model": "gemini-2.5-flash-lite",
                    "task": "fast",
                    "budget_decision": {"budget_mode": "cheap-first"},
                    "task_inference": {"task": "fast", "source": "auto"},
                },
            }
            yield {"type": "content", "content": "hello"}

    monkeypatch.setattr(aihub_router, "AIHubService", FakeStreamService)
    app = fastapi.FastAPI()
    app.include_router(aihub_router.router)

    response = testclient.TestClient(app).post(
        "/api/v1/aihub/gentxt",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    body = response.text
    assert '"type": "metadata"' in body
    assert '"metadata": {"model": "gemini-2.5-flash-lite"' in body
    assert '"type": "content"' in body
    assert '"content": "hello"' in body
    assert "[DONE]" in body


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
    expected_cost = estimate_token_cost_usd("gemini-2.5-flash-lite", 11, 7)
    assert repository["totals"]["downgrade_count"] == 1
    assert repository["totals"]["estimated_cost_usd_sum"] == expected_cost
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert repository["daily_buckets"][0]["routed_to_recommended_model"] is True
    assert repository["daily_buckets"][0]["reason_code_counts"]["over_task_budget"] == 1
    assert repository["daily_buckets"][0]["reason_code_counts"]["operator_review_required"] == 1
    assert repository["daily_buckets"][0]["reason_code_counts"]["routed_to_recommended_model"] == 1
    assert repository["daily_buckets"][0]["estimated_cost_usd_sum"] == expected_cost


@pytest.mark.asyncio
async def test_gentxt_downgrades_unknown_gateway_model_by_default():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[ChatMessage(role="user", content="classify this")],
            task="classification",
            model="yibu/gemini-9.9-flash-lite",
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash-lite"
    assert response.model == "gemini-2.5-flash-lite"
    assert response.budget_decision["requested_resolved_model"] == "yibu/gemini-9.9-flash-lite"
    assert response.budget_decision["requested_model_status"] == "unknown"
    assert response.budget_decision["explicit_model_fit_status"] == "enforced"
    assert response.budget_decision["routed_to_recommended_model"] is True
    assert "unknown_gateway_routed_to_recommended" in response.budget_decision["reason_codes"]
    assert "gateway_passthrough" not in response.budget_decision["reason_codes"]
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["downgrade_ratio"] == 1.0
    assert route_snapshot["summary"]["operator_review_request_count"] == 1
    assert route_snapshot["summary"]["unknown_price_model_count"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["totals"]["downgrade_count"] == 1
    assert repository["totals"]["unknown_model_count"] == 1
    assert repository["daily_buckets"][0]["reason_code_counts"]["unknown_gateway_routed_to_recommended"] == 1
    assert "classify this" not in str(repository)


@pytest.mark.asyncio
async def test_gentxt_allows_unknown_gateway_model_with_explicit_review_flag():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.gentxt(
        GenTxtRequest(
            messages=[ChatMessage(role="user", content="classify this")],
            task="classification",
            model="yibu/gemini-9.9-flash-lite",
            allow_over_budget_model=True,
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "yibu/gemini-9.9-flash-lite"
    assert response.model == "yibu/gemini-9.9-flash-lite"
    assert response.budget_decision["explicit_model_fit_status"] == "allowed_review_exception"
    assert response.budget_decision["routed_to_recommended_model"] is False
    assert "gateway_passthrough" in response.budget_decision["reason_codes"]
    assert "explicit_gateway_passthrough_allowed" in response.budget_decision["reason_codes"]
    assert "within_task_budget" not in response.budget_decision["reason_codes"]
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["downgrade_ratio"] == 0.0
    assert route_snapshot["summary"]["operator_review_request_count"] == 1
    assert route_snapshot["summary"]["allowed_over_budget_count"] == 0
    assert route_snapshot["summary"]["unknown_price_model_count"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    assert repository["totals"]["unknown_model_count"] == 1
    assert repository["daily_buckets"][0]["reason_code_counts"]["explicit_gateway_passthrough_allowed"] == 1


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


@pytest.mark.asyncio
async def test_analyze_pdf_records_sanitized_pdf_route_telemetry(monkeypatch):
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    async def fake_pdf_source_to_bytes(pdf: str):
        return b"%PDF-test", "private-client-contract.pdf"

    def fake_prepare_pdf_attachment(**kwargs):
        return "JVBERi0=", 1, 1, 1

    monkeypatch.setattr(service, "_pdf_source_to_bytes", fake_pdf_source_to_bytes)
    monkeypatch.setattr(service, "_prepare_pdf_attachment", fake_prepare_pdf_attachment)

    response = await service.analyze_pdf(
        AnalyzePdfRequest(
            pdf="data:application/pdf;base64,JVBERi0=",
            instruction="PRIVATE PDF INSTRUCTION SHOULD NOT PERSIST",
            mode="qa",
        )
    )

    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-pro"
    assert response.model == "gemini-2.5-pro"
    assert response.mode == "qa"
    assert response.task == "pdf"
    assert response.task_inference["task"] == "pdf"
    assert response.task_inference["source"] == "explicit"
    assert response.budget_decision["budget_mode"] == "premium-exception"
    assert response.usage == {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["pdf"]["explicit_task"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "pdf"
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-pro"
    assert "PRIVATE PDF INSTRUCTION" not in rendered
    assert "private-client-contract.pdf" not in rendered
    assert "MODEL_OUTPUT_SHOULD_NOT_PERSIST" not in rendered


@pytest.mark.asyncio
async def test_genimg_records_sanitized_image_route_telemetry():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.genimg(
        GenImgRequest(
            prompt="PRIVATE IMAGE PROMPT SHOULD NOT PERSIST",
            model="gemini-2.5-flash-image",
        )
    )

    assert fake_client.images.generate_calls[0]["model"] == "gemini-2.5-flash-image"
    assert response.model == "gemini-2.5-flash-image"
    assert response.task == "image"
    assert response.task_inference["task"] == "image"
    assert response.budget_decision["budget_mode"] == "explicit-media"
    assert response.usage_units == {
        "unit": "image",
        "requested_image_count": 1,
        "generated_image_count": 1,
        "input_image_count": 0,
        "mode": "generate",
    }
    assert response.images == ["https://cdn.example.test/generated-private-output.png"]
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["image"]["explicit_task"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "image"
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-flash-image"
    assert "PRIVATE IMAGE PROMPT" not in rendered
    assert "generated-private-output" not in rendered
    assert "sanitized revised prompt" not in rendered


@pytest.mark.asyncio
async def test_genimg_auto_model_uses_gemini_image_default():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.genimg(
        GenImgRequest(
            prompt="PRIVATE AUTO IMAGE PROMPT SHOULD NOT PERSIST",
            model="auto",
        )
    )

    assert fake_client.images.generate_calls[0]["model"] == "gemini-2.5-flash-image"
    assert response.model == "gemini-2.5-flash-image"
    assert response.budget_decision["requested_model"] == "auto"
    assert response.usage_units["unit"] == "image"
    assert response.usage_units["generated_image_count"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "image"
    assert repository["daily_buckets"][0]["resolved_model"] == "gemini-2.5-flash-image"
    assert "PRIVATE AUTO IMAGE PROMPT" not in rendered


@pytest.mark.asyncio
async def test_genvideo_records_sanitized_runtime_route_telemetry():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.genvideo(
        GenVideoRequest(
            prompt="PRIVATE VIDEO PROMPT SHOULD NOT PERSIST",
        )
    )

    assert fake_client.videos.create_calls[0]["model"] == "wan2.6-t2v"
    assert fake_client.videos.create_calls[0]["seconds"] == "4"
    assert response.model == "wan2.6-t2v"
    assert response.task == "video"
    assert response.task_inference["task"] == "video"
    assert response.usage_units["unit"] == "second"
    assert response.usage_units["generated_duration_seconds"] == 4
    assert response.budget_decision["requested_model"] is None
    assert response.budget_decision["explicit_model_requested"] is False
    assert response.budget_decision["explicit_model_fit_status"] == "default"
    assert "unknown_catalog_model" in response.budget_decision["reason_codes"]
    assert "gateway_passthrough" in response.budget_decision["reason_codes"]
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["video"]["explicit_task"] == 1
    assert route_snapshot["summary"]["unknown_price_model_count"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "video"
    assert repository["daily_buckets"][0]["resolved_model"] == "wan2.6-t2v"
    assert repository["daily_buckets"][0]["unknown_model_count"] == 1
    assert "PRIVATE VIDEO PROMPT" not in rendered
    assert "generated-private-video" not in rendered
    assert "sanitized video prompt" not in rendered


@pytest.mark.asyncio
async def test_genaudio_records_sanitized_runtime_route_telemetry():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    response = await service.genaudio(
        GenAudioRequest(
            text="PRIVATE AUDIO TEXT SHOULD NOT PERSIST",
            gender="male",
        )
    )

    assert fake_client.audio.speech.create_calls[0]["model"] == "qwen3-tts-flash"
    assert fake_client.audio.speech.create_calls[0]["voice"] == response.voice
    assert response.model == "qwen3-tts-flash"
    assert response.task == "audio"
    assert response.gender == "male"
    assert response.task_inference["task"] == "audio"
    assert response.usage_units["unit"] == "character"
    assert response.usage_units["input_character_count"] == len("PRIVATE AUDIO TEXT SHOULD NOT PERSIST")
    assert response.budget_decision["budget_mode"] == "explicit-speech-media"
    assert response.budget_decision["requested_model"] is None
    assert "unknown_catalog_model" in response.budget_decision["reason_codes"]
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["audio"]["explicit_task"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "audio"
    assert repository["daily_buckets"][0]["resolved_model"] == "qwen3-tts-flash"
    assert repository["daily_buckets"][0]["unknown_model_count"] == 1
    assert "PRIVATE AUDIO TEXT" not in rendered
    assert "generated-private-audio" not in rendered


@pytest.mark.asyncio
async def test_transcribe_records_sanitized_runtime_route_telemetry(monkeypatch):
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    fake_client = _FakeClient()
    service.client = fake_client

    async def fake_audio_str_to_upload_file(audio: str, name_prefix: str = "input_audio"):
        audio_file = io.BytesIO(b"private audio bytes")
        audio_file.name = "private-client-call.mp3"
        return audio_file

    monkeypatch.setattr(service, "_audio_str_to_upload_file", fake_audio_str_to_upload_file)

    response = await service.transcribe(
        TranscribeAudioRequest(
            audio="data:audio/mp3;base64,AA==",
        )
    )

    assert fake_client.audio.transcriptions.create_calls[0]["model"] == "scribe_v2"
    assert fake_client.audio.transcriptions.create_calls[0]["response_format"] == "json"
    assert response.model == "scribe_v2"
    assert response.task == "transcription"
    assert response.source_name == "input_audio"
    assert response.text == "TRANSCRIBED_OUTPUT_SHOULD_NOT_PERSIST"
    assert response.task_inference["task"] == "transcription"
    assert response.usage_units == {"unit": "audio", "audio_count": 1}
    assert response.budget_decision["budget_mode"] == "explicit-transcription"
    assert response.budget_decision["requested_model"] is None
    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["by_task"]["transcription"]["explicit_task"] == 1
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["daily_buckets"][0]["task"] == "transcription"
    assert repository["daily_buckets"][0]["resolved_model"] == "scribe_v2"
    assert repository["daily_buckets"][0]["unknown_model_count"] == 1
    assert "private-client-call" not in rendered
    assert "TRANSCRIBED_OUTPUT_SHOULD_NOT_PERSIST" not in rendered


@pytest.mark.asyncio
async def test_genimg_persists_sanitized_route_failure_without_prompt_or_provider_text():
    model_usage_registry.reset()
    model_route_telemetry_registry.reset()
    service = AIHubService()
    service.client = _FailingClient()

    with pytest.raises(RuntimeError):
        await service.genimg(
            GenImgRequest(
                prompt="PRIVATE FAILED IMAGE PROMPT SHOULD NOT PERSIST",
                model="gemini-2.5-flash-image",
            )
        )

    route_snapshot = model_route_telemetry_registry.snapshot()
    assert route_snapshot["summary"]["failure_rate"] == 1.0
    repository = RouteTelemetryRepositoryService().build_repository()
    rendered = str(repository)
    assert repository["totals"]["failure_count"] == 1
    assert repository["daily_buckets"][0]["task"] == "image"
    assert repository["daily_buckets"][0]["success"] is False
    assert "PRIVATE FAILED IMAGE PROMPT" not in rendered
    assert "provider leaked raw image prompt" not in rendered
