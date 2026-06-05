from __future__ import annotations

from typing import Any


class ModelOpsCheapFirstCanaryRollbackDrillService:
    """Build a metadata-only rollback rehearsal packet for canary approval rows."""

    def build_drill(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        approval_packet = _dict(data.get("cheap_first_canary_approval_packet"))
        promotion_decision = _dict(data.get("cheap_first_canary_promotion_decision"))
        source_approval_status = _status(approval_packet.get("status"), "not_supplied")
        source_promotion_status = _status(promotion_decision.get("status"), "not_supplied")
        approval_items = [
            item for item in _list(approval_packet.get("approval_items")) if isinstance(item, dict)
        ]
        drill_items = [
            self._drill_item(item, source_approval_status, source_promotion_status)
            for item in approval_items
        ]
        ready = [item for item in drill_items if item["drill_status"] == "drill_ready"]
        blocked = [item for item in drill_items if item["drill_status"] == "drill_blocked"]
        rollback = [item for item in drill_items if item["drill_status"] == "rollback_drill_required"]
        monitor = [item for item in drill_items if item["drill_status"] == "monitor_only"]
        status = self._status(source_approval_status, ready, blocked, rollback, monitor)

        return {
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-canary-rollback-drill",
                "notes": [
                    "Consumes the metadata-only canary approval packet and promotion decision.",
                    "Produces rollback rehearsal tasks and trigger-review checkpoints only.",
                    "Does not execute rollback, write configuration, shift traffic, call a gateway, or persist drill state.",
                ],
            },
            "summary": {
                "drill_item_count": len(drill_items),
                "ready_drill_count": len(ready),
                "blocked_drill_count": len(blocked),
                "rollback_required_count": len(rollback),
                "monitor_only_count": len(monitor),
                "source_approval_status": source_approval_status,
                "source_promotion_status": source_promotion_status,
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
                "rollback_executed": False,
                "drill_record_written": False,
            },
            "rollback_drill_policy": {
                "drill_required_before_approval": True,
                "rollback_execution_allowed": False,
                "configuration_change_allowed": False,
                "traffic_shift_allowed": False,
                "requires_trigger_review": True,
                "requires_holdout_confirmation": True,
            },
            "rollback_drill_items": drill_items,
            "ready_drill_item_ids": [item["id"] for item in ready],
            "blocked_drill_item_ids": [item["id"] for item in blocked],
            "rollback_required_item_ids": [item["id"] for item in rollback],
            "recommended_actions": self._recommended_actions(status, ready, blocked, rollback, monitor),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "approver_identity_included": False,
                "approval_record_written": False,
                "drill_record_written": False,
                "configuration_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "rollback_executed": False,
                "output_scope": "canary approval ids, task names, trigger ids, role names, and rehearsal checklist text only",
            },
            "claim_boundary": {
                "rollback_executed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "automatic_canary_rollout_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_canary_approval_packet.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _drill_item(
        self,
        approval_item: dict[str, Any],
        source_approval_status: str,
        source_promotion_status: str,
    ) -> dict[str, Any]:
        source_step_id = str(approval_item.get("source_step_id") or "unknown-step")
        task = str(approval_item.get("task") or "unknown")
        approval_status = _status(approval_item.get("approval_status"), "missing")
        promotion_status = _status(approval_item.get("promotion_status"), source_promotion_status)
        reason_codes = [str(code) for code in _list(approval_item.get("blocking_reason_codes")) if str(code).strip()]
        rollback_trigger_ids = _trigger_ids(approval_item)
        drill_status = self._drill_status(approval_status, source_approval_status)

        return {
            "id": f"rollback-drill-{source_step_id}",
            "source_approval_item_id": str(approval_item.get("id") or f"approval-{source_step_id}"),
            "source_step_id": source_step_id,
            "task": task,
            "phase": str(approval_item.get("phase") or "unknown"),
            "approval_status": approval_status,
            "promotion_status": promotion_status,
            "drill_status": drill_status,
            "trigger_review_status": self._trigger_review_status(drill_status),
            "rollback_trigger_ids": rollback_trigger_ids,
            "reason_codes": reason_codes,
            "required_roles": self._required_roles(drill_status),
            "rehearsal_steps": self._rehearsal_steps(task, drill_status, rollback_trigger_ids),
            "configuration_written": False,
            "gateway_called": False,
            "traffic_shifted": False,
            "rollback_executed": False,
            "drill_record_written": False,
            "action": self._action(task, drill_status),
        }

    def _drill_status(self, approval_status: str, source_approval_status: str) -> str:
        if approval_status == "rollback_review_required":
            return "rollback_drill_required"
        if approval_status == "ready_for_maintainer_approval":
            return "drill_ready"
        if approval_status == "monitor_only":
            return "monitor_only"
        if approval_status in {"blocked_until_review", "source_not_ready"}:
            return "drill_blocked"
        if source_approval_status in {"approval_blocked", "not_supplied"}:
            return "drill_blocked"
        return "drill_blocked"

    def _trigger_review_status(self, drill_status: str) -> str:
        if drill_status == "rollback_drill_required":
            return "failed_trigger_review_required"
        if drill_status == "drill_ready":
            return "trigger_checklist_ready"
        if drill_status == "monitor_only":
            return "monitor_only"
        return "trigger_review_blocked"

    def _required_roles(self, drill_status: str) -> list[str]:
        if drill_status == "drill_ready":
            return ["maintainer_owner", "model_ops_reviewer", "release_operator"]
        if drill_status == "rollback_drill_required":
            return ["maintainer_owner", "model_ops_reviewer", "incident_reviewer"]
        if drill_status == "drill_blocked":
            return ["model_ops_reviewer"]
        return []

    def _rehearsal_steps(self, task: str, drill_status: str, rollback_trigger_ids: list[str]) -> list[str]:
        trigger_text = ", ".join(rollback_trigger_ids) if rollback_trigger_ids else "source approval blockers"
        if drill_status == "rollback_drill_required":
            return [
                f"Keep the previous {task} default active outside this service.",
                f"Review failed rollback triggers: {trigger_text}.",
                "Document maintainer rollback review in the external release record.",
                "Do not advance canary batch size until a new passing observation packet is attached.",
            ]
        if drill_status == "drill_ready":
            return [
                f"Snapshot the current and previous {task} defaults outside this service.",
                f"Confirm rollback trigger checklist: {trigger_text}.",
                "Confirm holdout traffic remains active before maintainer approval.",
                "Prepare the external rollback command path, but do not execute it from this service.",
            ]
        if drill_status == "monitor_only":
            return [
                f"Continue monitoring the current {task} default.",
                "No rollback rehearsal is queued because no canary traffic movement is pending.",
            ]
        return [
            f"Resolve approval blockers for {task} before scheduling a rollback drill.",
            "Attach current aggregate canary observations before requesting maintainer review.",
        ]

    def _action(self, task: str, drill_status: str) -> str:
        if drill_status == "rollback_drill_required":
            return f"Run a maintainer review of rollback evidence for {task}; this service will not execute rollback."
        if drill_status == "drill_ready":
            return f"Prepare a maintainer-approved rollback rehearsal for {task} before any default movement."
        if drill_status == "monitor_only":
            return f"No rollback drill is queued for {task}; continue cheap-first monitoring."
        return f"Hold the {task} rollback drill until approval evidence and observations are ready."

    def _status(
        self,
        source_approval_status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
    ) -> str:
        if rollback:
            return "rollback_drill_required"
        if blocked:
            return "drill_blocked"
        if ready:
            return "drill_ready"
        if monitor:
            return "monitor_only"
        return source_approval_status if source_approval_status != "not_supplied" else "not_supplied"

    def _recommended_actions(
        self,
        status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if rollback:
            actions.append("Review rollback-required canary rows before any default movement.")
        if blocked:
            actions.append("Resolve approval or observation blockers before scheduling rollback drills.")
        if ready:
            actions.append("Attach rollback rehearsal evidence to the maintainer approval packet before changing defaults.")
        if status == "monitor_only" and monitor:
            actions.append("No rollback drill is queued; continue monitoring current cheap-first defaults.")
        return actions or ["Submit canary approval evidence before preparing rollback drill rehearsal."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _status(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def _trigger_ids(approval_item: dict[str, Any]) -> list[str]:
    if isinstance(approval_item.get("rollback_trigger_ids"), list):
        return [str(item) for item in approval_item["rollback_trigger_ids"] if str(item).strip()]
    checks = _list(approval_item.get("pre_approval_checks"))
    trigger_like = [str(check) for check in checks if "rollback" in str(check)]
    return trigger_like or ["route-failure-rate", "over-budget-route-ratio", "premium-request-ratio"]
