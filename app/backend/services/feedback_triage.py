from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TriageRule:
    id: str
    priority: str
    assignee: str
    sla_hours: int
    labels: tuple[str, ...]
    keywords: tuple[str, ...]
    reason: str
    operator_actions: tuple[str, ...]


PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


class FeedbackTriageService:
    """Deterministic issue triage for user feedback and maintenance queues."""

    RULES: tuple[TriageRule, ...] = (
        TriageRule(
            id="privacy-or-security",
            priority="P0",
            assignee="security_privacy_owner",
            sla_hours=4,
            labels=("privacy", "security", "urgent"),
            keywords=(
                "privacy",
                "security",
                "data leak",
                "leak",
                "breach",
                "delete my data",
                "data deletion",
                "personal information",
                "隐私",
                "泄露",
                "数据删除",
                "个人信息",
                "安全",
            ),
            reason="Potential privacy, data deletion, or security impact.",
            operator_actions=(
                "Acknowledge receipt without exposing details.",
                "Preserve audit trail and route to privacy/security owner.",
                "Do not mark resolved until deletion or security review is complete.",
            ),
        ),
        TriageRule(
            id="payment-or-access-blocker",
            priority="P1",
            assignee="support_ops",
            sla_hours=12,
            labels=("payment", "access", "revenue_blocker"),
            keywords=(
                "payment",
                "paid",
                "refund",
                "invoice",
                "subscription",
                "cannot login",
                "login failed",
                "付款",
                "支付",
                "退款",
                "发票",
                "订阅",
                "无法登录",
                "登录失败",
            ),
            reason="Payment or account access issue can block paid usage.",
            operator_actions=(
                "Check order, entitlement, and authentication records.",
                "Confirm whether the user is blocked from paid features.",
                "Escalate unresolved payment state to operator review.",
            ),
        ),
        TriageRule(
            id="legal-output-risk",
            priority="P1",
            assignee="legal_review_owner",
            sla_hours=24,
            labels=("legal_quality", "high_risk_output"),
            keywords=(
                "wrong law",
                "incorrect citation",
                "hallucination",
                "false citation",
                "missed risk",
                "legal advice",
                "错法条",
                "引用错误",
                "虚假引用",
                "幻觉",
                "漏掉风险",
                "法律建议",
                "误导",
            ),
            reason="Legal output may be inaccurate or misleading.",
            operator_actions=(
                "Attach the affected report ID or source document if available.",
                "Run citation, evidence, quality gate, and release decision checks.",
                "Require lawyer review before reusing the affected report.",
            ),
        ),
        TriageRule(
            id="pipeline-or-upload-failure",
            priority="P2",
            assignee="engineering",
            sla_hours=48,
            labels=("bug", "pipeline", "document_processing"),
            keywords=(
                "upload",
                "ocr",
                "pdf",
                "extract",
                "crash",
                "timeout",
                "failed",
                "blank",
                "上传",
                "识别",
                "解析",
                "崩溃",
                "超时",
                "失败",
                "空白",
            ),
            reason="Document processing or review pipeline failure.",
            operator_actions=(
                "Collect document type, size, and pipeline stage.",
                "Check extraction warnings and backend error logs.",
                "Re-run with a safe sample if the original file contains sensitive data.",
            ),
        ),
        TriageRule(
            id="feature-or-usability",
            priority="P3",
            assignee="product_maintainer",
            sla_hours=168,
            labels=("feature_request", "usability"),
            keywords=(
                "feature",
                "suggestion",
                "workflow",
                "template",
                "export",
                "ui",
                "ux",
                "建议",
                "功能",
                "流程",
                "模板",
                "导出",
                "界面",
                "体验",
            ),
            reason="Product improvement or usability feedback.",
            operator_actions=(
                "Cluster with similar user requests.",
                "Decide whether it affects core legal review workflow.",
                "Schedule after higher priority blockers unless it reduces review risk.",
            ),
        ),
    )

    DEFAULT_RULE = TriageRule(
        id="general-feedback",
        priority="P3",
        assignee="support_ops",
        sla_hours=168,
        labels=("general_feedback",),
        keywords=(),
        reason="General feedback without urgent legal, security, payment, or pipeline signals.",
        operator_actions=(
            "Acknowledge and request missing context if needed.",
            "Cluster with related feedback before scheduling product work.",
        ),
    )

    def triage(self, item: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        source = {**(item or {}), **kwargs}
        category = _text(source.get("category"))
        content = _text(source.get("content"))
        haystack = f"{category} {content}".lower()

        matches = [rule for rule in self.RULES if _matches(haystack, rule.keywords)]
        selected = min(matches, key=lambda rule: PRIORITY_RANK[rule.priority]) if matches else self.DEFAULT_RULE
        labels = _unique([label for rule in matches for label in rule.labels] or list(selected.labels))
        reasons = _unique([rule.reason for rule in matches] or [selected.reason])
        actions = _unique([action for rule in matches for action in rule.operator_actions] or list(selected.operator_actions))

        return {
            "status": "triaged",
            "priority": selected.priority,
            "assignee": selected.assignee,
            "sla_hours": selected.sla_hours,
            "labels": labels,
            "matched_rule_ids": [rule.id for rule in matches] or [selected.id],
            "reasons": reasons,
            "operator_actions": actions,
            "summary": self._summary(selected, labels),
        }

    def apply_to_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        triage = self.triage(payload)
        enriched = dict(payload)
        enriched["status"] = enriched.get("status") or triage["status"]
        enriched["priority"] = enriched.get("priority") or triage["priority"]
        enriched["assignee"] = enriched.get("assignee") or triage["assignee"]
        enriched["resolution_note"] = enriched.get("resolution_note") or self._resolution_note(triage)
        return enriched

    def _summary(self, rule: TriageRule, labels: list[str]) -> str:
        return f"{rule.priority} -> {rule.assignee}; labels: {', '.join(labels)}"

    def _resolution_note(self, triage: dict[str, Any]) -> str:
        actions = "; ".join(triage.get("operator_actions") or [])
        labels = ", ".join(triage.get("labels") or [])
        return f"Auto-triage {triage['priority']} for {triage['assignee']}. Labels: {labels}. Actions: {actions}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _matches(haystack: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in haystack for keyword in keywords)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
