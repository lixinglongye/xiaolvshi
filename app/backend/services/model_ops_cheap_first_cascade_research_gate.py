from __future__ import annotations

import re
from typing import Any

from services.model_failure_upgrade_budget import ModelFailureUpgradeBudgetService
from services.model_ops_cheap_first_escalation_budget import ModelOpsCheapFirstEscalationBudgetService
from services.model_route_quality_budget import ModelRouteQualityBudgetService


FORBIDDEN_KEY_PATTERN = re.compile(
    r"(api[_-]?key|authorization|password|secret|prompt|headers?|raw[_-]?(model[_-]?)?output|raw[_-]?response|legal[_-]?text|document[_-]?text|client[_-]?email|email|request[_-]?body|response[_-]?body|messages?|content|choices|run[_-]?report[_-]?payload)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b)"
)


RESEARCH_BASIS: tuple[dict[str, str], ...] = (
    {
        "id": "frugalgpt",
        "url": "https://arxiv.org/abs/2305.05176",
        "signal": "LLM cascades should start with cheaper models and escalate only when quality or task-fit evidence requires it.",
    },
    {
        "id": "gemini-flash-lite-model-card",
        "url": "https://ai.google.dev/models/gemini",
        "signal": "Gemini 2.5 Flash-Lite is the official cheap-start candidate for high-throughput text and multimodal inputs.",
    },
    {
        "id": "gemini-flash-lite-pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "signal": "Gemini 2.5 Flash-Lite is the smallest cost-effective Gemini Developer API model for at-scale usage.",
    },
)


class ModelOpsCheapFirstCascadeResearchGateService:
    """Aggregate cheap-first cascade research and local gate evidence."""

    def __init__(
        self,
        route_quality_budget_service: ModelRouteQualityBudgetService | None = None,
        escalation_budget_service: ModelOpsCheapFirstEscalationBudgetService | None = None,
        failure_upgrade_budget_service: ModelFailureUpgradeBudgetService | None = None,
    ) -> None:
        self.route_quality_budget_service = route_quality_budget_service or ModelRouteQualityBudgetService()
        self.escalation_budget_service = escalation_budget_service or ModelOpsCheapFirstEscalationBudgetService()
        self.failure_upgrade_budget_service = failure_upgrade_budget_service or ModelFailureUpgradeBudgetService()

    def build_gate(self, signals: Any = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        forbidden_field_count = _count_forbidden_keys(data)
        secret_like_value_count = _count_secret_like_values(data)
        route_quality_budget = _dict(data.get("route_quality_budget")) or self.route_quality_budget_service.build_budget()
        cheap_first_escalation_budget = (
            _dict(data.get("cheap_first_escalation_budget"))
            or self.escalation_budget_service.build_budget()
        )
        failure_upgrade_budget = _dict(data.get("failure_upgrade_budget")) or self.failure_upgrade_budget_service.build_decision()
        gemini_cheap_first_route_preflight = _dict(data.get("gemini_cheap_first_route_preflight"))
        user_need_cheap_first_handoff = _dict(data.get("user_need_cheap_first_handoff"))
        cheap_first_calibration = _dict(data.get("cheap_first_calibration"))

        source_rows = [
            self._source_row(
                "frugalgpt-cascade-research",
                "FrugalGPT cost-aware cascade basis",
                "research",
                {"status": "pass", "warning_check_ids": [], "blocking_check_ids": []},
                "Require low-cost primary routing plus bounded escalation evidence before default promotion.",
            ),
            self._source_row(
                "gemini-flash-lite-cheap-primary",
                "Gemini Flash-Lite cheap primary evidence",
                "official_model_card",
                gemini_cheap_first_route_preflight or {"status": "review_required", "warning_check_ids": ["gemini-route-preflight-not-attached"]},
                "Keep high-frequency text, OCR, and classification starts on Flash-Lite-compatible cheap routes.",
            ),
            self._source_row(
                "route-quality-budget",
                "Cheap-first route quality budget",
                "local_gate",
                route_quality_budget,
                "Cheap starts require deterministic quality gates before escalation.",
            ),
            self._source_row(
                "cheap-first-escalation-budget",
                "Cheap-first escalation budget",
                "local_gate",
                cheap_first_escalation_budget,
                "Escalation must stay bounded by failure, retry, wasted-cost, and premium-review thresholds.",
            ),
            self._source_row(
                "failure-upgrade-budget",
                "Failure upgrade budget",
                "local_gate",
                failure_upgrade_budget,
                "Failure paths need attempt, quota, and incremental-cost review before retry-up or premium escalation.",
            ),
            self._source_row(
                "cheap-first-calibration",
                "Gemini/NewAPI cheap-first calibration",
                "local_gate",
                cheap_first_calibration or {"status": "review_required", "warning_check_ids": ["cheap-first-calibration-not-attached"]},
                "Calibration evidence should stay attached before changing default model routes.",
            ),
            self._source_row(
                "user-need-cheap-first-handoff",
                "User-need cheap-first handoff",
                "product_evidence",
                user_need_cheap_first_handoff or {"status": "review_required", "warning_check_ids": ["user-need-handoff-not-attached"]},
                "User-facing cheap-first changes need product-need coverage and maintainer handoff evidence.",
            ),
        ]
        checks = self._checks(
            source_rows,
            forbidden_field_count=forbidden_field_count,
            secret_like_value_count=secret_like_value_count,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "fail" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "model-ops-cheap-first-cascade-research-gate",
            "title": "Cheap-first cascade research gate",
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-cascade-research-gate",
                "notes": [
                    "Aggregates external cascade research, official Gemini Flash-Lite positioning, and local cheap-first gate evidence.",
                    "Treats FrugalGPT-style cascades as a policy justification only when local quality, escalation, and failure-upgrade gates are attached.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, model endpoints, public datasets, or the network.",
                    "Does not write configuration, change default routes, shift traffic, or claim production accuracy.",
                ],
                "research_basis": list(RESEARCH_BASIS),
            },
            "summary": {
                "source_count": len(source_rows),
                "passing_source_count": sum(1 for row in source_rows if row["status"] == "pass"),
                "review_source_count": sum(1 for row in source_rows if row["status"] == "review_required"),
                "blocked_source_count": sum(1 for row in source_rows if row["status"] == "fail"),
                "research_source_count": sum(1 for row in source_rows if row["source_type"] == "research"),
                "official_source_count": sum(1 for row in source_rows if row["source_type"] == "official_model_card"),
                "local_gate_count": sum(1 for row in source_rows if row["source_type"] == "local_gate"),
                "forbidden_payload_field_count": forbidden_field_count,
                "secret_like_value_count": secret_like_value_count,
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "frugalgpt_basis_attached": True,
                "gemini_flash_lite_basis_attached": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "default_routes_changed": False,
                "raw_payload_echoed": False,
            },
            "cascade_policy": {
                "cheap_primary": "Start high-frequency eligible tasks on Gemini Flash-Lite or another lowest/low-tier model with required capabilities.",
                "verification_step": "Run deterministic quality gates before any retry-up or escalation.",
                "escalation_step": "Escalate only when local failure signals, attempt budget, incremental cost, and operator-review rules allow it.",
                "premium_exception": "Premium, Pro, preview, unknown, media, and legal high-risk routes stay explicit-only unless maintainer evidence approves them.",
                "default_change": "This gate never changes defaults; it only makes maintainer review evidence visible.",
            },
            "source_rows": source_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(status, source_rows, blocking, warnings),
            "source_boundaries": {
                "changes_default_routes": False,
                "writes_configuration": False,
                "uses_live_gateway": False,
                "downloads_public_benchmarks": False,
                "claims_public_benchmark_scores": False,
                "claims_twenty_four_hour_completion": False,
                "mutates_update_counts": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "headers_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "phone_numbers_included": False,
                "identity_numbers_included": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "source ids, source statuses, check ids, research URLs, counts, and policy labels only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "external_research_freshness_claimed": False,
                "automatic_default_change_claimed": False,
                "production_accuracy_claimed": False,
                "public_benchmark_scores_included": False,
                "twenty_four_hour_completion_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_cascade_research_gate.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _source_row(
        self,
        row_id: str,
        label: str,
        source_type: str,
        source: dict[str, Any],
        required_action: str,
    ) -> dict[str, Any]:
        status = _source_status(source)
        blocking_ids = _safe_ids(source.get("blocking_check_ids"))
        warning_ids = _safe_ids(source.get("warning_check_ids"))
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
        return {
            "id": row_id,
            "label": label,
            "source_type": source_type,
            "status": status,
            "source_status": _safe_token(source.get("status"), "missing") if source else "missing",
            "blocking_ids": blocking_ids,
            "warning_ids": warning_ids,
            "summary_counts": {
                "blocking_check_count": len(blocking_ids),
                "warning_check_count": len(warning_ids),
                "source_warning_count": _safe_int(summary.get("warning_check_count") or summary.get("warning_signal_count")),
                "source_blocking_count": _safe_int(summary.get("blocking_check_count") or summary.get("blocking_signal_count")),
            },
            "required_action": required_action,
        }

    def _checks(
        self,
        source_rows: list[dict[str, Any]],
        *,
        forbidden_field_count: int,
        secret_like_value_count: int,
    ) -> list[dict[str, Any]]:
        missing_or_review_rows = [row for row in source_rows if row["status"] == "review_required"]
        blocked_rows = [row for row in source_rows if row["status"] == "fail"]
        return [
            {
                "id": "sanitized-source-signals",
                "status": "fail" if forbidden_field_count or secret_like_value_count else "pass",
                "reason": (
                    "Source signals contain forbidden field names or secret-like values."
                    if forbidden_field_count or secret_like_value_count
                    else "Source signals are metadata-only."
                ),
            },
            {
                "id": "research-basis-attached",
                "status": "pass",
                "reason": "FrugalGPT cascade and Gemini Flash-Lite official source references are attached.",
            },
            {
                "id": "local-gates-attached",
                "status": "fail" if blocked_rows else ("warn" if missing_or_review_rows else "pass"),
                "reason": (
                    "One or more local cheap-first source gates are blocked."
                    if blocked_rows
                    else (
                        "One or more local cheap-first source gates require maintainer review."
                        if missing_or_review_rows
                        else "Local cheap-first route, escalation, failure-upgrade, calibration, and user-need evidence is attached."
                    )
                ),
            },
            {
                "id": "no-default-or-traffic-mutation",
                "status": "pass",
                "reason": "The gate is review evidence only and does not mutate defaults, configuration, or traffic.",
            },
            {
                "id": "no-network-or-gateway-call",
                "status": "pass",
                "reason": "The gate does not call gateways, models, public datasets, or external networks.",
            },
        ]

    def _recommended_actions(
        self,
        status: str,
        source_rows: list[dict[str, Any]],
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if blocking:
            actions.append("Block cheap-first default changes until cascade research source blockers are resolved.")
        if warnings:
            actions.append("Attach maintainer notes for every cascade source row that requires review.")
        for row in source_rows:
            if row["status"] != "pass":
                actions.append(f"Review cascade source: {row['label']}.")
        if status == "pass":
            actions.append("Keep Flash-Lite cheap starts tied to deterministic quality gates and bounded escalation budgets.")
        return _dedupe(actions)


def _source_status(source: dict[str, Any]) -> str:
    if not source:
        return "review_required"
    status = str(source.get("status") or "").strip().lower()
    if _safe_ids(source.get("blocking_check_ids")) or status in {"fail", "failed", "blocked", "error"}:
        return "fail"
    if _safe_ids(source.get("warning_check_ids")) or status in {
        "warn",
        "warning",
        "review_required",
        "manual_review",
        "needs_review",
        "not_ready",
        "not_supplied",
        "not_run",
    }:
        return "review_required"
    if status in {"pass", "ready", "ok", "success", "advance_next_batch"}:
        return "pass"
    return "review_required"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_token(item, "unknown") for item in value[:50] if _safe_token(item, "")]


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "-")[:100]
    if not text or SECRET_VALUE_PATTERN.search(text):
        return fallback
    cleaned = re.sub(r"[^a-z0-9_.:-]+", "-", text).strip("-")
    return cleaned or fallback


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _count_forbidden_keys(value: Any) -> int:
    if isinstance(value, dict):
        count = sum(1 for key in value if FORBIDDEN_KEY_PATTERN.search(str(key)))
        return count + sum(_count_forbidden_keys(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_forbidden_keys(item) for item in value)
    return 0


def _count_secret_like_values(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_count_secret_like_values(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_secret_like_values(item) for item in value)
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return 1
    return 0


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
