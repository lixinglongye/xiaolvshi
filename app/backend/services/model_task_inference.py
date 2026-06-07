from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import normalize_budget_task


GENTXT_TEXT_OUTPUT_TASKS = {"fast", "ocr", "classification", "review", "pdf", "grounded-research", "agentic"}

CLASSIFICATION_KEYWORDS = (
    "classify",
    "classification",
    "category",
    "categorize",
    "label",
    "triage",
    "route",
    "doc_type",
    "evidence_category",
    "material type",
    "file type",
    "材料分类",
    "分类",
    "标签",
    "文件类型",
    "证据分类",
)

OCR_KEYWORDS = (
    "ocr",
    "extract text",
    "recognize text",
    "scan",
    "scanned",
    "image text",
    "pdf page",
    "visible text",
    "识别文字",
    "文字识别",
    "扫描",
    "图片文字",
    "可见的原文",
    "原文文本",
)

REVIEW_KEYWORDS = (
    "legal",
    "lawyer",
    "contract",
    "clause",
    "agreement",
    "risk",
    "liability",
    "indemnity",
    "breach",
    "jurisdiction",
    "lawsuit",
    "litigation",
    "evidence",
    "citation",
    "statute",
    "case fact",
    "legal review",
    "合同",
    "条款",
    "法律",
    "律师",
    "风险",
    "责任",
    "违约",
    "管辖",
    "诉讼",
    "起诉",
    "证据",
    "法条",
    "审查",
    "案件",
)

FAST_KEYWORDS = (
    "preflight",
    "planning",
    "plan mode",
    "summary",
    "summarize",
    "rewrite",
    "format",
    "json repair",
    "理解用户目标",
    "规划",
    "预检",
    "摘要",
    "总结",
    "改写",
)


@dataclass(frozen=True)
class TaskInference:
    requested_task: str | None
    task: str
    source: str
    confidence: float
    signals: tuple[str, ...]
    reason: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["signals"] = list(self.signals)
        return data


def infer_gentxt_task(
    requested_task: str | None,
    messages: list[Any] | tuple[Any, ...],
    *,
    response_format: dict[str, Any] | None = None,
) -> TaskInference:
    """Infer a cheap-first text task before runtime model routing."""

    normalized_request = (requested_task or "auto").strip().lower()
    if normalized_request and normalized_request != "auto":
        normalized = normalize_budget_task(normalized_request)
        if normalized not in GENTXT_TEXT_OUTPUT_TASKS:
            return TaskInference(
                requested_task=requested_task,
                task="review",
                source="explicit",
                confidence=0.7,
                signals=(f"requested:{normalized_request}", f"unsupported_for_gentxt:{normalized}"),
                reason="Caller provided a media or unsupported routing task for text generation; using the review text budget.",
            )
        return TaskInference(
            requested_task=requested_task,
            task=normalized,
            source="explicit",
            confidence=1.0,
            signals=(f"requested:{normalized_request}",),
            reason="Caller provided an explicit routing task.",
        )

    text, image_count = _message_text_and_image_count(messages)
    normalized_text = text.lower()
    signals: list[str] = []

    classification_hits = _hits(normalized_text, CLASSIFICATION_KEYWORDS)
    ocr_hits = _hits(normalized_text, OCR_KEYWORDS)
    review_hits = _hits(normalized_text, REVIEW_KEYWORDS)
    fast_hits = _hits(normalized_text, FAST_KEYWORDS)

    if response_format and response_format.get("type") == "json_object":
        signals.append("json-response")
    if image_count:
        signals.append(f"image-input:{image_count}")
    signals.extend(f"classification:{item}" for item in classification_hits[:3])
    signals.extend(f"ocr:{item}" for item in ocr_hits[:3])
    signals.extend(f"review:{item}" for item in review_hits[:3])
    signals.extend(f"fast:{item}" for item in fast_hits[:3])

    task, confidence, reason = _choose_task(
        has_json_response=bool(response_format and response_format.get("type") == "json_object"),
        image_count=image_count,
        classification_hits=classification_hits,
        ocr_hits=ocr_hits,
        review_hits=review_hits,
        fast_hits=fast_hits,
        text_length=len(text),
    )
    return TaskInference(
        requested_task=requested_task,
        task=task,
        source="auto",
        confidence=confidence,
        signals=tuple(signals[:12]),
        reason=reason,
    )


def task_inference_policy_for_api() -> dict[str, Any]:
    return {
        "status": "ready",
        "default_task": "auto",
        "rules": [
            "Explicit task values are honored before inference.",
            "Classification keywords plus JSON response format route to classification.",
            "OCR keywords or image text extraction prompts route to ocr.",
            "Legal review, contract, litigation, evidence, or citation terms route to review.",
            "Planning, preflight, summary, rewrite, and JSON repair terms stay on fast routing.",
            "Media tasks such as image, video, audio, and transcription are rejected for gentxt and routed to the review text budget.",
            "Unmatched requests stay on fast routing.",
        ],
        "safeguards": [
            "Inference is deterministic and does not call an AI model.",
            "Only metadata and matched keyword signals are returned; prompt text is not stored.",
            "Explicit model budget enforcement still runs after task inference.",
        ],
    }


def _choose_task(
    *,
    has_json_response: bool,
    image_count: int,
    classification_hits: list[str],
    ocr_hits: list[str],
    review_hits: list[str],
    fast_hits: list[str],
    text_length: int,
) -> tuple[str, float, str]:
    if classification_hits and (has_json_response or len(classification_hits) >= 2):
        return "classification", 0.9, "Classification signals were detected in a structured-output request."
    if ocr_hits and (image_count or len(ocr_hits) >= 2):
        return "ocr", 0.9, "OCR or visible-text extraction signals were detected."
    if fast_hits and not review_hits:
        return "fast", 0.82, "Planning, preflight, summary, or formatting signals were detected."
    if review_hits:
        confidence = 0.88 if len(review_hits) >= 2 else 0.76
        return "review", confidence, "Legal review signals were detected."
    if image_count:
        return "ocr", 0.72, "Multimodal image input without stronger signals defaults to OCR routing."
    if text_length > 12000:
        return "review", 0.7, "Long legal-style text is routed to balanced review by default."
    return "fast", 0.65, "No stronger task signal was detected; defaulting to fast routing."


def _message_text_and_image_count(messages: list[Any] | tuple[Any, ...]) -> tuple[str, int]:
    parts: list[str] = []
    image_count = 0
    for msg in messages or []:
        content = getattr(msg, "content", None)
        if isinstance(content, str):
            parts.append(content)
            continue
        if isinstance(content, list):
            for item in content:
                item_type = _content_value(item, "type")
                if item_type == "image_url":
                    image_count += 1
                text = _content_value(item, "text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(parts), image_count


def _content_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword.lower() in text]
