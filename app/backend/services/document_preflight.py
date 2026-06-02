from __future__ import annotations

import re
from typing import Any

from services.document_strategy import build_strategy_pending_facts, get_document_strategy
from services.model_budget import model_budget_decision


LEGAL_MARKERS = (
    "甲方",
    "乙方",
    "合同",
    "协议",
    "违约责任",
    "争议解决",
    "人民法院",
    "仲裁委员会",
    "起诉状",
    "答辩状",
    "律师函",
    "申请人",
    "被申请人",
    "出租人",
    "承租人",
    "出卖人",
    "买受人",
    "借款人",
    "保证人",
)

COMPLEXITY_SIGNALS = {
    "cross_border": ("涉外", "跨境", "境外", "外币", "英文", "国际贸易"),
    "dispute": ("起诉", "仲裁", "诉讼", "保全", "执行", "管辖异议"),
    "financing": ("担保", "抵押", "质押", "保证", "借款", "融资", "回购"),
    "equity": ("股权", "投资", "增资", "股东", "对赌", "估值"),
    "privacy": ("个人信息", "隐私", "数据", "敏感信息", "用户信息"),
    "high_value": ("金额巨大", "重大交易", "分期付款", "违约金", "赔偿上限"),
}


class DocumentReviewPreflightService:
    """Rule-first preflight before expensive deep-review model calls."""

    def evaluate(
        self,
        *,
        document_text: str,
        document_type: str = "合同",
        user_role: str = "甲方",
        review_goal: str = "签署前审查",
        known_facts: list[str] | None = None,
        extraction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = document_text or ""
        known_facts = known_facts or []
        strategy = get_document_strategy(document_type=document_type, document_text=text, user_role=user_role)
        pending_facts = build_strategy_pending_facts(strategy, text)
        legal_signal_count = sum(1 for marker in LEGAL_MARKERS if marker in text[:8000])
        complexity = self._complexity(text, extraction or {})
        route_task = self._route_task(text=text, complexity=complexity, extraction=extraction or {})
        budget = model_budget_decision(None, task=route_task).to_api()
        blockers = self._blocking_reasons(text, legal_signal_count)
        warnings = self._warning_reasons(text, pending_facts, complexity, known_facts, extraction or {})
        status = self._status(blockers, warnings)

        return {
            "status": status,
            "strategy": strategy.to_report_dict(),
            "document_signals": {
                "char_count": len(text),
                "legal_marker_count": legal_signal_count,
                "known_fact_count": len(known_facts),
                "detected_complexity_signals": complexity["signals"],
                "complexity_score": complexity["score"],
                "complexity_level": complexity["level"],
            },
            "routing": {
                "recommended_task": route_task,
                "recommended_model": budget["recommended_model"],
                "resolved_model": budget["resolved_model"],
                "budget_mode": budget["budget_mode"],
                "cost_tier": budget["cost_tier"],
                "reason": self._route_reason(route_task, complexity),
            },
            "missing_required_facts": pending_facts,
            "blocking_reasons": blockers,
            "warning_reasons": warnings,
            "recommended_actions": self._recommended_actions(blockers, warnings, pending_facts, route_task),
        }

    def _complexity(self, text: str, extraction: dict[str, Any]) -> dict[str, Any]:
        normalized = re.sub(r"\s+", "", text)
        signals: list[str] = []
        for name, keywords in COMPLEXITY_SIGNALS.items():
            if any(keyword in normalized for keyword in keywords):
                signals.append(name)

        char_count = len(text)
        page_count = _safe_int(extraction.get("page_count"), 0)
        score = len(signals) * 18
        if char_count > 80_000 or page_count > 80:
            score += 35
        elif char_count > 35_000 or page_count > 35:
            score += 20
        elif char_count > 12_000 or page_count > 12:
            score += 10

        if _safe_int(extraction.get("low_text_page_count"), 0) or extraction.get("low_text_pages"):
            score += 8

        score = max(0, min(100, score))
        if score >= 70:
            level = "complex"
        elif score >= 35:
            level = "moderate"
        else:
            level = "simple"
        return {"score": score, "level": level, "signals": signals}

    def _route_task(self, *, text: str, complexity: dict[str, Any], extraction: dict[str, Any]) -> str:
        page_count = _safe_int(extraction.get("page_count"), 0)
        if complexity["level"] == "complex" or len(text) > 80_000 or page_count > 80:
            return "pdf"
        if complexity["level"] == "moderate" or len(text) > 12_000:
            return "review"
        return "fast"

    def _blocking_reasons(self, text: str, legal_signal_count: int) -> list[str]:
        if not text.strip():
            return ["Document text is empty."]
        if len(text.strip()) < 20:
            return ["Document text is too short for legal review."]
        if legal_signal_count == 0 and len(text) < 3000:
            return ["No clear legal-document markers were found in the supplied text."]
        return []

    def _warning_reasons(
        self,
        text: str,
        pending_facts: list[dict[str, str]],
        complexity: dict[str, Any],
        known_facts: list[str],
        extraction: dict[str, Any],
    ) -> list[str]:
        warnings: list[str] = []
        if pending_facts:
            warnings.append(f"{len(pending_facts)} strategy-required facts appear missing.")
        if complexity["level"] == "complex":
            warnings.append("Document has complex signals and may require premium review routing.")
        if not known_facts and any(signal in complexity["signals"] for signal in ("dispute", "financing", "equity")):
            warnings.append("Known facts are empty for a dispute, financing, or equity-related matter.")
        if extraction.get("ocr_pages"):
            warnings.append("OCR pages are present; source text should be checked for extraction errors.")
        if len(text) > 80_000:
            warnings.append("Document is long enough to require chunking or premium-context review.")
        return warnings

    def _status(self, blockers: list[str], warnings: list[str]) -> str:
        if blockers:
            return "blocked"
        if warnings:
            return "needs_context"
        return "ready"

    def _route_reason(self, route_task: str, complexity: dict[str, Any]) -> str:
        if route_task == "pdf":
            return "Complexity or document size justifies premium-exception routing."
        if route_task == "review":
            return "Moderate complexity uses balanced legal-review routing."
        return "Simple preflight can start with cheap-first routing."

    def _recommended_actions(
        self,
        blockers: list[str],
        warnings: list[str],
        pending_facts: list[dict[str, str]],
        route_task: str,
    ) -> list[str]:
        actions: list[str] = []
        if blockers:
            actions.append("Stop before model review and ask the user to upload a reviewable legal document.")
        if pending_facts:
            fields = ", ".join(item["field"] for item in pending_facts[:6])
            actions.append(f"Ask user to confirm or supplement missing facts: {fields}.")
        if route_task == "pdf":
            actions.append("Use premium routing only after operator review or when long-context review is necessary.")
        elif route_task == "review":
            actions.append("Use balanced review routing and keep early extraction/classification on cheap models.")
        else:
            actions.append("Use cheap-first routing for initial classification and light extraction.")
        if not warnings and not blockers:
            actions.append("Proceed to staged deep review.")
        return actions


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
