from __future__ import annotations

from typing import Any


class ModelOpsCheapFirstCanaryApprovalPacketService:
    """Build a metadata-only maintainer approval packet for canary promotion decisions."""

    def build_packet(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        promotion_decision = _dict(data.get("cheap_first_canary_promotion_decision"))
        source_status = _status(promotion_decision.get("status"), "not_supplied")
        promotion_items = [
            item for item in _list(promotion_decision.get("promotion_items")) if isinstance(item, dict)
        ]
        approval_items = [self._approval_item(item) for item in promotion_items]
        ready = [item for item in approval_items if item["approval_status"] == "ready_for_maintainer_approval"]
        blocked = [item for item in approval_items if item["approval_status"] == "blocked_until_review"]
        rollback = [item for item in approval_items if item["approval_status"] == "rollback_review_required"]
        monitor = [item for item in approval_items if item["approval_status"] == "monitor_only"]
        source_not_ready = [item for item in approval_items if item["approval_status"] == "source_not_ready"]
        status = self._status(source_status, ready, blocked, rollback, monitor, source_not_ready)

        return {
            "status": status,
            "approval_policy": {
                "approval_required": True,
                "approval_record_written": False,
                "configuration_change_allowed": False,
                "traffic_shift_allowed": False,
                "requires_current_observation_review": True,
                "requires_rollback_review_for_failed_steps": True,
            },
            "method": {
                "type": "model-ops-cheap-first-canary-approval-packet",
                "notes": [
                    "Consumes the metadata-only canary promotion decision.",
                    "Returns maintainer signoff requirements and pre-approval checks only.",
                    "Does not record approver identity, write configuration, shift traffic, call a gateway, or persist rollout state.",
                ],
            },
            "summary": {
                "approval_item_count": len(approval_items),
                "ready_for_approval_count": len(ready),
                "blocked_approval_count": len(blocked),
                "rollback_review_count": len(rollback),
                "monitor_only_count": len(monitor),
                "source_not_ready_count": len(source_not_ready),
                "required_signoff_count": sum(len(item["required_signoffs"]) for item in approval_items),
                "approved_count": 0,
                "source_promotion_status": source_status,
                "approval_record_written": False,
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
            },
            "approval_items": approval_items,
            "ready_item_ids": [item["id"] for item in ready],
            "blocked_item_ids": [item["id"] for item in blocked],
            "rollback_review_item_ids": [item["id"] for item in rollback],
            "recommended_actions": self._recommended_actions(status, ready, blocked, rollback, monitor, source_not_ready),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "approver_identity_included": False,
                "approval_record_written": False,
                "configuration_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "output_scope": "canary step ids, promotion statuses, signoff roles, pre-approval checks, and validation commands only",
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "automatic_canary_rollout_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_canary_approval_packet.py tests/test_model_ops_cheap_first_canary_promotion_decision.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _approval_item(self, item: dict[str, Any]) -> dict[str, Any]:
        promotion_status = _status(item.get("promotion_status"), "missing")
        source_step_id = str(item.get("source_step_id") or "unknown-step")
        approval_status = self._approval_status(promotion_status)
        required_signoffs = self._required_signoffs(approval_status)
        reason_codes = [str(code) for code in _list(item.get("reason_codes")) if str(code).strip()]

        return {
            "id": f"approval-{source_step_id}",
            "source_promotion_item_id": str(item.get("id") or f"promotion-{source_step_id}"),
            "source_step_id": source_step_id,
            "task": str(item.get("task") or "unknown"),
            "phase": str(item.get("phase") or "unknown"),
            "promotion_status": promotion_status,
            "approval_status": approval_status,
            "matched_observation_count": _safe_int(item.get("matched_observation_count")),
            "batch_percentage": _safe_int(item.get("batch_percentage")),
            "holdout_percentage": _safe_int(item.get("holdout_percentage")),
            "required_signoffs": required_signoffs,
            "pre_approval_checks": self._pre_approval_checks(approval_status),
            "blocking_reason_codes": self._blocking_reason_codes(approval_status, reason_codes),
            "approval_record_written": False,
            "configuration_change_allowed": False,
            "traffic_shift_allowed": False,
            "action": self._action(approval_status, item),
        }

    def _approval_status(self, promotion_status: str) -> str:
        if promotion_status == "advance_next_batch":
            return "ready_for_maintainer_approval"
        if promotion_status == "rollback_required":
            return "rollback_review_required"
        if promotion_status == "monitor_only":
            return "monitor_only"
        if promotion_status == "not_ready":
            return "source_not_ready"
        return "blocked_until_review"

    def _required_signoffs(self, approval_status: str) -> list[str]:
        if approval_status == "ready_for_maintainer_approval":
            return ["maintainer_owner", "model_ops_reviewer"]
        if approval_status == "rollback_review_required":
            return ["maintainer_owner", "model_ops_reviewer"]
        if approval_status in {"blocked_until_review", "source_not_ready"}:
            return ["model_ops_reviewer"]
        return []

    def _pre_approval_checks(self, approval_status: str) -> list[str]:
        if approval_status == "ready_for_maintainer_approval":
            return [
                "confirm-current-observation-window",
                "confirm-no-rollback-trigger-breach",
                "confirm-holdout-remains-active",
                "prepare-config-change-outside-this-service",
            ]
        if approval_status == "rollback_review_required":
            return [
                "confirm-failing-observation-evidence",
                "keep-previous-default-or-rollback-outside-this-service",
                "record-maintainer-review-outside-this-service",
            ]
        if approval_status == "monitor_only":
            return ["continue-cheap-first-monitoring"]
        return [
            "attach-passing-aggregate-observations",
            "resolve-source-plan-or-observation-blockers",
            "record-maintainer-review-outside-this-service",
        ]

    def _blocking_reason_codes(self, approval_status: str, reason_codes: list[str]) -> list[str]:
        if approval_status in {"ready_for_maintainer_approval", "monitor_only"}:
            return []
        return reason_codes or ["approval-evidence-not-ready"]

    def _action(self, approval_status: str, item: dict[str, Any]) -> str:
        task = str(item.get("task") or "unknown")
        if approval_status == "ready_for_maintainer_approval":
            return f"Collect maintainer signoff for the next {task} canary batch; this packet will not apply it."
        if approval_status == "rollback_review_required":
            return f"Review rollback evidence for {task} and keep the previous default unless a maintainer resolves it."
        if approval_status == "monitor_only":
            return f"No approval is queued for {task}; continue monitoring the current cheap-first default."
        if approval_status == "source_not_ready":
            return f"Resolve source canary blockers for {task} before requesting approval."
        return f"Hold {task} approval until aggregate observations pass and maintainer review is attached."

    def _status(
        self,
        source_status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
        source_not_ready: list[dict[str, Any]],
    ) -> str:
        if rollback:
            return "rollback_review_required"
        if blocked or source_not_ready:
            return "approval_blocked"
        if ready:
            return "approval_ready"
        if monitor:
            return "monitor_only"
        return source_status if source_status != "not_supplied" else "not_supplied"

    def _recommended_actions(
        self,
        status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
        source_not_ready: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if rollback:
            actions.append("Review rollback-required canary rows before any default movement.")
        if blocked:
            actions.append("Hold approval until aggregate observations pass and reviewer evidence is attached.")
        if source_not_ready:
            actions.append("Resolve source canary plan blockers before requesting approval.")
        if ready:
            actions.append("Collect maintainer and model-ops reviewer signoff outside this service before changing defaults.")
        if status == "monitor_only" and monitor:
            actions.append("No canary approval is queued; continue monitoring current cheap-first defaults.")
        return actions or ["Submit canary promotion evidence before requesting maintainer approval."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _status(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0
