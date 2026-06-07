from schemas.aihub import ChatMessage, ContentPartImage, ContentPartText, ImageUrl
from services.model_task_inference import infer_gentxt_task, task_inference_policy_for_api


def test_task_inference_honors_explicit_task():
    result = infer_gentxt_task(
        "classification",
        [ChatMessage(role="user", content="Please review this contract.")],
    )

    assert result.task == "classification"
    assert result.source == "explicit"
    assert result.confidence == 1.0


def test_task_inference_blocks_media_tasks_on_gentxt():
    for requested_task, normalized in (
        ("image", "image"),
        ("video", "video"),
        ("audio", "audio"),
        ("transcription", "transcription"),
        ("tts", "audio"),
        ("speech-to-text", "transcription"),
    ):
        result = infer_gentxt_task(
            requested_task,
            [ChatMessage(role="user", content="Generate text only.")],
        )

        assert result.task == "review"
        assert result.source == "explicit"
        assert f"unsupported_for_gentxt:{normalized}" in result.signals
        assert "media" in result.reason


def test_task_inference_routes_structured_classification_to_cheap_task():
    result = infer_gentxt_task(
        "auto",
        [ChatMessage(role="user", content="Classify this material and output doc_type and evidence_category.")],
        response_format={"type": "json_object"},
    )

    assert result.task == "classification"
    assert result.source == "auto"
    assert any(signal.startswith("classification:") for signal in result.signals)


def test_task_inference_routes_contract_risk_text_to_review():
    result = infer_gentxt_task(
        None,
        [ChatMessage(role="user", content="Review this contract clause for liability, breach, and jurisdiction risk.")],
    )

    assert result.task == "review"
    assert result.confidence >= 0.76
    assert any(signal.startswith("review:") for signal in result.signals)


def test_task_inference_routes_multimodal_ocr_prompt_to_ocr():
    result = infer_gentxt_task(
        "auto",
        [
            ChatMessage(
                role="user",
                content=[
                    ContentPartText(text="OCR this scanned page and return only visible text."),
                    ContentPartImage(image_url=ImageUrl(url="data:image/png;base64,abc")),
                ],
            )
        ],
    )

    assert result.task == "ocr"
    assert "image-input:1" in result.signals


def test_task_inference_keeps_preflight_and_summary_fast():
    result = infer_gentxt_task(
        "auto",
        [ChatMessage(role="user", content="Plan Mode preflight: summarize the user goal and return JSON.")],
        response_format={"type": "json_object"},
    )

    assert result.task == "fast"
    assert "sk-" not in str(result.to_api())


def test_task_inference_policy_is_safe_for_api():
    policy = task_inference_policy_for_api()

    assert policy["status"] == "ready"
    assert policy["default_task"] == "auto"
    assert len(policy["rules"]) >= 5
    assert "sk-" not in str(policy)
