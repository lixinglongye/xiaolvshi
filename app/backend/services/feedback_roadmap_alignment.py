from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.feedback_triage import FeedbackTriageService, PRIORITY_RANK
from services.user_needs_radar import UserNeedsRadarService


@dataclass(frozen=True)
class RoadmapRule:
    id: str
    need_id: str
    triage_rule_ids: tuple[str, ...]
    labels: tuple[str, ...]
    keywords: tuple[str, ...]
    reason: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["triage_rule_ids"] = list(self.triage_rule_ids)
        data["labels"] = list(self.labels)
        data["keywords"] = list(self.keywords)
        return data


class FeedbackRoadmapAlignmentService:
    """Map feedback triage signals to user-need roadmap items."""

    def build_mapping_catalog(self) -> dict[str, Any]:
        rules = [rule.to_api() for rule in self._rules()]
        radar = UserNeedsRadarService().build_radar()
        needs = {need["id"]: need for need in radar["needs"]}
        mapped_need_ids = sorted({rule["need_id"] for rule in rules})
        return {
            "status": "ready",
            "rule_count": len(rules),
            "mapped_need_count": len(mapped_need_ids),
            "mapped_need_ids": mapped_need_ids,
            "rules": rules,
            "coverage": {
                "radar_need_count": len(needs),
                "unmapped_need_ids": sorted(set(needs) - set(mapped_need_ids)),
            },
            "maintenance_actions": [
                "Use this mapping when previewing feedback triage before creating tickets.",
                "Cluster repeated feedback by need_id before scheduling feature work.",
                "Promote feedback that maps to high-priority needs and failing release gates.",
            ],
        }

    def align(self, item: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        source = {**(item or {}), **kwargs}
        triage = FeedbackTriageService().triage(source)
        radar = UserNeedsRadarService().build_radar()
        needs = {need["id"]: need for need in radar["needs"]}
        haystack = f"{source.get('category', '')} {source.get('content', '')}".lower()
        rules = self._rules()

        matches: list[dict[str, Any]] = []
        for rule in rules:
            need = needs.get(rule.need_id)
            if not need:
                continue
            signals = self._matched_signals(rule, triage, haystack)
            if not signals:
                continue
            matches.append(self._match(rule, need, triage, signals))

        if not matches:
            fallback_need = needs.get("feedback-to-roadmap-loop")
            if fallback_need:
                matches.append(
                    self._match(
                        RoadmapRule(
                            id="fallback-roadmap-loop",
                            need_id="feedback-to-roadmap-loop",
                            triage_rule_ids=("general-feedback",),
                            labels=("general_feedback",),
                            keywords=(),
                            reason="General feedback should still be clustered before scheduling work.",
                        ),
                        fallback_need,
                        triage,
                        ["fallback"],
                    )
                )

        matches.sort(key=lambda item: (-item["confidence"], -item["need_priority_score"], item["need_id"]))
        top = matches[0] if matches else None
        return {
            "status": "aligned" if matches else "unmapped",
            "triage": triage,
            "top_need_id": top["need_id"] if top else None,
            "matches": matches,
            "recommended_actions": self._recommended_actions(matches, triage),
        }

    def _rules(self) -> tuple[RoadmapRule, ...]:
        return (
            RoadmapRule(
                id="privacy-feedback-to-privacy-upload",
                need_id="privacy-safe-upload",
                triage_rule_ids=("privacy-or-security",),
                labels=("privacy", "security"),
                keywords=("privacy", "personal information", "隐私", "个人信息", "泄露", "delete my data"),
                reason="Privacy/security feedback should improve safe upload and redaction flows.",
            ),
            RoadmapRule(
                id="instruction-feedback-to-prompt-injection",
                need_id="prompt-injection-resilience",
                triage_rule_ids=("privacy-or-security",),
                labels=("security",),
                keywords=("prompt", "instruction", "jailbreak", "system prompt", "提示词", "系统提示", "越狱"),
                reason="Prompt or instruction attacks should improve document-injection resilience.",
            ),
            RoadmapRule(
                id="legal-quality-feedback-to-traceability",
                need_id="traceable-legal-review",
                triage_rule_ids=("legal-output-risk",),
                labels=("legal_quality", "high_risk_output"),
                keywords=("wrong law", "incorrect citation", "hallucination", "错法条", "引用错误", "虚假引用", "幻觉"),
                reason="Legal output risk should improve traceability, citations, evidence, and release decisions.",
            ),
            RoadmapRule(
                id="pipeline-feedback-to-extraction",
                need_id="robust-extraction-quality",
                triage_rule_ids=("pipeline-or-upload-failure",),
                labels=("pipeline", "document_processing"),
                keywords=("upload", "ocr", "pdf", "extract", "blank", "上传", "识别", "解析", "空白"),
                reason="Upload and parsing failures should improve extraction-quality controls.",
            ),
            RoadmapRule(
                id="cost-feedback-to-cheap-routing",
                need_id="cheap-first-review-routing",
                triage_rule_ids=("feature-or-usability",),
                labels=("feature_request", "usability"),
                keywords=("cost", "expensive", "slow", "premium", "gemini", "model", "成本", "太贵", "很慢", "模型"),
                reason="Cost or model-routing feedback should improve cheap-first routing and model ops.",
            ),
            RoadmapRule(
                id="usability-feedback-to-plain-language",
                need_id="plain-language-actionability",
                triage_rule_ids=("feature-or-usability",),
                labels=("feature_request", "usability"),
                keywords=("ui", "ux", "summary", "next step", "plain", "界面", "体验", "摘要", "下一步", "看不懂"),
                reason="Usability feedback should improve plain-language actions and report readability.",
            ),
            RoadmapRule(
                id="general-feedback-to-roadmap-loop",
                need_id="feedback-to-roadmap-loop",
                triage_rule_ids=("general-feedback", "feature-or-usability", "payment-or-access-blocker"),
                labels=("general_feedback", "feature_request", "access", "payment"),
                keywords=("feedback", "suggestion", "workflow", "建议", "反馈", "流程"),
                reason="General feedback should be clustered into the maintenance roadmap before scheduling.",
            ),
        )

    def _matched_signals(self, rule: RoadmapRule, triage: dict[str, Any], haystack: str) -> list[str]:
        signals: list[str] = []
        triage_rule_ids = set(triage.get("matched_rule_ids") or [])
        labels = set(triage.get("labels") or [])
        if triage_rule_ids.intersection(rule.triage_rule_ids):
            signals.append("triage_rule")
        if labels.intersection(rule.labels):
            signals.append("label")
        if any(keyword.lower() in haystack for keyword in rule.keywords):
            signals.append("keyword")
        return _unique(signals)

    def _match(self, rule: RoadmapRule, need: dict[str, Any], triage: dict[str, Any], signals: list[str]) -> dict[str, Any]:
        base = 35 + len(signals) * 15
        priority_bonus = max(0, 12 - PRIORITY_RANK.get(str(triage.get("priority")), 3) * 3)
        need_bonus = 8 if need.get("priority_band") == "high" else 4 if need.get("priority_band") == "medium" else 0
        confidence = max(0, min(100, base + priority_bonus + need_bonus))
        return {
            "rule_id": rule.id,
            "need_id": rule.need_id,
            "title": need.get("title"),
            "category": need.get("category"),
            "need_priority_band": need.get("priority_band"),
            "need_priority_score": need.get("priority_score", 0),
            "confidence": confidence,
            "matched_signals": signals,
            "reason": rule.reason,
            "release_gate_links": need.get("release_gate_links") or [],
            "next_actions": need.get("next_actions") or [],
        }

    def _recommended_actions(self, matches: list[dict[str, Any]], triage: dict[str, Any]) -> list[str]:
        if not matches:
            return ["Ask for missing context and keep the ticket in general feedback until it can be mapped."]
        top = matches[0]
        actions = [
            f"Cluster this feedback under user need {top['need_id']}.",
            "Attach the triage priority and matched roadmap need to the operator note.",
        ]
        if triage.get("priority") in {"P0", "P1"}:
            actions.append("Review linked release gates before marking the ticket resolved.")
        return actions


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
