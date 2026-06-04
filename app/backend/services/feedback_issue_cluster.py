from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any


MAX_ITEMS = 250
MAX_TEXT_CHARS_PER_ITEM = 1600

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_ALIASES = {
    "p0": "critical",
    "critical": "critical",
    "blocker": "critical",
    "urgent": "critical",
    "p1": "high",
    "high": "high",
    "major": "high",
    "p2": "medium",
    "medium": "medium",
    "normal": "medium",
    "p3": "low",
    "low": "low",
    "minor": "low",
    "trivial": "low",
}

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)")
NATIONAL_ID_PATTERN = re.compile(r"(?<!\d)\d{17}[\dXx](?![A-Za-z0-9])")
API_KEY_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{12,}|"
    r"(?:api[_-]?key|token|secret|password)\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})",
    re.IGNORECASE,
)
SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{12,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)|"
    r"(?<!\d)\d{17}[\dXx](?![A-Za-z0-9])|"
    r"(?:api[_-]?key|token|secret|password)\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TopicRule:
    normalized_topic: str
    severity_floor: str
    keywords: tuple[str, ...]


TOPIC_RULES: tuple[TopicRule, ...] = (
    TopicRule(
        "privacy_or_security_exposure",
        "critical",
        (
            "privacy",
            "security",
            "data leak",
            "leak",
            "breach",
            "delete my data",
            "personal information",
            "id card",
            "api key",
            "prompt injection",
            "\u9690\u79c1",
            "\u6cc4\u9732",
            "\u5220\u9664",
            "\u8eab\u4efd\u8bc1",
            "\u5b89\u5168",
        ),
    ),
    TopicRule(
        "payment_or_access_blocker",
        "high",
        (
            "payment",
            "paid feature",
            "refund",
            "invoice",
            "subscription",
            "entitlement",
            "cannot login",
            "login failed",
            "access denied",
            "\u652f\u4ed8",
            "\u4ed8\u6b3e",
            "\u9000\u6b3e",
            "\u53d1\u7968",
            "\u767b\u5f55",
            "\u6743\u9650",
        ),
    ),
    TopicRule(
        "legal_output_quality_risk",
        "high",
        (
            "wrong law",
            "incorrect citation",
            "false citation",
            "hallucination",
            "missed risk",
            "legal advice",
            "report is wrong",
            "wrong conclusion",
            "\u5f15\u7528\u9519\u8bef",
            "\u9519\u8bef\u6cd5\u6761",
            "\u5e7b\u89c9",
            "\u6f0f\u6389\u98ce\u9669",
            "\u62a5\u544a\u9519",
        ),
    ),
    TopicRule(
        "document_upload_or_extraction_failure",
        "medium",
        (
            "upload",
            "ocr",
            "pdf",
            "extract",
            "parse",
            "scanned",
            "blank",
            "file failed",
            "document failed",
            "\u4e0a\u4f20",
            "\u8bc6\u522b",
            "\u89e3\u6790",
            "\u626b\u63cf",
            "\u7a7a\u767d",
            "\u6587\u4ef6",
        ),
    ),
    TopicRule(
        "export_or_delivery_format_issue",
        "medium",
        (
            "export",
            "download",
            "docx",
            "format",
            "template",
            "layout",
            "watermark",
            "\u5bfc\u51fa",
            "\u4e0b\u8f7d",
            "\u6a21\u677f",
            "\u683c\u5f0f",
            "\u7248\u5f0f",
        ),
    ),
    TopicRule(
        "performance_or_reliability_issue",
        "medium",
        (
            "slow",
            "timeout",
            "crash",
            "500",
            "502",
            "503",
            "failed",
            "unavailable",
            "stuck",
            "\u6162",
            "\u8d85\u65f6",
            "\u5d29\u6e83",
            "\u5931\u8d25",
            "\u5361\u4f4f",
        ),
    ),
    TopicRule(
        "feature_or_usability_request",
        "low",
        (
            "feature",
            "suggestion",
            "workflow",
            "ui",
            "ux",
            "hard to use",
            "button",
            "filter",
            "\u5efa\u8bae",
            "\u529f\u80fd",
            "\u6d41\u7a0b",
            "\u754c\u9762",
            "\u4f53\u9a8c",
            "\u7b5b\u9009",
        ),
    ),
)

SEGMENT_KEYWORDS = {
    "lawyer": ("lawyer", "attorney", "firm", "\u5f8b\u5e08", "\u5f8b\u6240"),
    "legal_ops": ("legal ops", "paralegal", "operator", "\u6cd5\u52a1", "\u8fd0\u8425"),
    "individual": ("individual", "consumer", "personal", "\u4e2a\u4eba", "\u5f53\u4e8b\u4eba"),
    "enterprise": ("enterprise", "company", "organization", "\u4f01\u4e1a", "\u516c\u53f8"),
    "paid_user": ("paid", "subscription", "pro", "premium", "\u4ed8\u8d39", "\u8ba2\u9605"),
    "trial_user": ("trial", "free", "\u8bd5\u7528", "\u514d\u8d39"),
    "mobile": ("mobile", "ios", "android", "wechat", "\u624b\u673a", "\u5fae\u4fe1"),
    "desktop": ("desktop", "windows", "mac", "browser", "\u7535\u8111", "\u6d4f\u89c8\u5668"),
}

DECLARATION = {
    "mode": "deterministic_local_rules",
    "model_calls": 0,
    "external_network_calls": 0,
    "stores_raw_feedback": False,
    "max_input_items": MAX_ITEMS,
    "max_text_chars_per_item": MAX_TEXT_CHARS_PER_ITEM,
}


class FeedbackIssueClusterService:
    """Cluster feedback into privacy-safe repeated issue groups without model calls."""

    def cluster(self, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        raw_items = items if isinstance(items, list) else []
        clusters: dict[str, dict[str, Any]] = {}
        accepted_count = 0

        for index, item in enumerate(raw_items[:MAX_ITEMS], start=1):
            if not isinstance(item, dict):
                continue
            accepted_count += 1
            redacted_text = _redact_sensitive(_feedback_text(item))
            normalized_text = _normalize_text(redacted_text)
            rule = _select_topic_rule(normalized_text)
            severity = _item_severity(item, normalized_text, rule)
            segments = _segments(item, normalized_text)
            evidence_ref = _evidence_ref(item, redacted_text, index)
            cluster = clusters.setdefault(
                rule.normalized_topic,
                {
                    "normalized_topic": rule.normalized_topic,
                    "severity": severity,
                    "count": 0,
                    "affected_user_segment_tags": set(),
                    "evidence_refs": [],
                    "hashed_evidence_count": 0,
                    "safe_id_evidence_count": 0,
                },
            )

            cluster["count"] += 1
            cluster["severity"] = _worse_severity(cluster["severity"], severity)
            cluster["affected_user_segment_tags"].update(segments)
            cluster["evidence_refs"].append(evidence_ref)
            if evidence_ref.startswith("hash:"):
                cluster["hashed_evidence_count"] += 1
            if evidence_ref.startswith("id:"):
                cluster["safe_id_evidence_count"] += 1

        cluster_list = [self._finalize_cluster(cluster) for cluster in clusters.values()]
        cluster_list.sort(
            key=lambda item: (
                SEVERITY_RANK[item["severity"]],
                -item["count"],
                item["normalized_topic"],
            )
        )

        return {
            "status": "ready",
            "method": dict(DECLARATION),
            "summary": {
                "input_item_count": len(raw_items),
                "processed_item_count": accepted_count,
                "ignored_item_count": max(0, min(len(raw_items), MAX_ITEMS) - accepted_count),
                "truncated_item_count": max(0, len(raw_items) - MAX_ITEMS),
                "cluster_count": len(cluster_list),
                "raw_payload_echoed": False,
            },
            "clusters": cluster_list,
            "privacy": {
                "raw_feedback_echoed": False,
                "pii_returned": False,
                "retained_fields": [
                    "normalized_topic",
                    "severity",
                    "count",
                    "counts",
                    "affected_user_segment_tags",
                    "evidence_refs",
                ],
                "redacted_patterns": ["email", "phone", "national_id", "api_key_or_secret"],
            },
        }

    def _finalize_cluster(self, cluster: dict[str, Any]) -> dict[str, Any]:
        count = int(cluster["count"])
        refs = list(cluster["evidence_refs"])
        segments = sorted(cluster["affected_user_segment_tags"]) or ["unspecified"]
        return {
            "cluster_id": _cluster_id(cluster["normalized_topic"]),
            "normalized_topic": cluster["normalized_topic"],
            "severity": cluster["severity"],
            "count": count,
            "counts": {
                "feedback_items": count,
                "safe_id_refs": int(cluster["safe_id_evidence_count"]),
                "hashed_refs": int(cluster["hashed_evidence_count"]),
            },
            "affected_user_segment_tags": segments,
            "evidence_refs": refs,
        }


def _feedback_text(item: dict[str, Any]) -> str:
    fields = (
        "title",
        "summary",
        "category",
        "topic",
        "content",
        "description",
        "message",
        "body",
        "error",
        "severity",
        "priority",
    )
    parts: list[str] = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, str):
            parts.append(value)
    tags = item.get("tags")
    if isinstance(tags, list):
        parts.extend(str(tag) for tag in tags[:12] if isinstance(tag, (str, int, float)))
    return " ".join(parts)[:MAX_TEXT_CHARS_PER_ITEM]


def _redact_sensitive(value: str) -> str:
    text = str(value or "")
    text = EMAIL_PATTERN.sub(" [email] ", text)
    text = NATIONAL_ID_PATTERN.sub(" [national_id] ", text)
    text = API_KEY_PATTERN.sub(" [secret] ", text)
    text = PHONE_PATTERN.sub(" [phone] ", text)
    return text


def _normalize_text(value: str) -> str:
    redacted = _redact_sensitive(value).lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", redacted)
    return re.sub(r"\s+", " ", normalized).strip()


def _select_topic_rule(normalized_text: str) -> TopicRule:
    for rule in TOPIC_RULES:
        if any(keyword.lower() in normalized_text for keyword in rule.keywords):
            return rule
    return TopicRule("general_feedback", "low", ())


def _item_severity(item: dict[str, Any], normalized_text: str, rule: TopicRule) -> str:
    explicit = _severity_alias(item.get("severity")) or _severity_alias(item.get("priority"))
    inferred = rule.severity_floor
    if any(token in normalized_text for token in ("breach", "data leak", "api key", "secret", "\u6cc4\u9732")):
        inferred = "critical"
    elif any(token in normalized_text for token in ("cannot login", "access denied", "wrong law", "incorrect citation", "crash", "timeout")):
        inferred = "high"
    return _worse_severity(explicit or inferred, inferred)


def _severity_alias(value: Any) -> str | None:
    token = str(value or "").strip().lower()
    return SEVERITY_ALIASES.get(token)


def _worse_severity(left: str, right: str) -> str:
    left = left if left in SEVERITY_RANK else "medium"
    right = right if right in SEVERITY_RANK else "medium"
    return left if SEVERITY_RANK[left] <= SEVERITY_RANK[right] else right


def _segments(item: dict[str, Any], normalized_text: str) -> set[str]:
    segments: set[str] = set()
    for field in ("segment", "user_segment", "user_type", "role", "plan", "platform"):
        segments.update(_safe_segment_tags(item.get(field)))
    tags = item.get("tags")
    if isinstance(tags, list):
        for tag in tags[:12]:
            segments.update(_safe_segment_tags(tag))
    for segment, keywords in SEGMENT_KEYWORDS.items():
        if any(keyword.lower() in normalized_text for keyword in keywords):
            segments.add(segment)
    return segments


def _safe_segment_tags(value: Any) -> set[str]:
    raw = str(value or "").strip().lower()
    if not raw or SENSITIVE_PATTERN.search(raw):
        return set()
    tokens = re.split(r"[^a-z0-9_+-]+", raw)
    result: set[str] = set()
    for token in tokens:
        if token in SEGMENT_KEYWORDS:
            result.add(token)
        elif token in {"paid", "pro", "premium", "subscriber"}:
            result.add("paid_user")
        elif token in {"trial", "free"}:
            result.add("trial_user")
        elif token in {"ios", "android", "wechat"}:
            result.add("mobile")
        elif token in {"web", "browser", "desktop"}:
            result.add("desktop")
    return result


def _evidence_ref(item: dict[str, Any], redacted_text: str, index: int) -> str:
    safe_id = _safe_id(item.get("id") or item.get("ticket_id") or item.get("feedback_id"))
    if safe_id:
        return f"id:{safe_id}"
    digest_source = f"{index}|{_normalize_text(redacted_text)}"
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
    return f"hash:{digest}"


def _safe_id(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw or len(raw) > 80 or SENSITIVE_PATTERN.search(raw):
        return ""
    token = re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")
    if not token or len(token) > 64 or SENSITIVE_PATTERN.search(token):
        return ""
    return token


def _cluster_id(normalized_topic: str) -> str:
    digest = hashlib.sha256(normalized_topic.encode("utf-8")).hexdigest()[:8]
    return f"fic-{digest}"
