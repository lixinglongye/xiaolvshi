from __future__ import annotations

import re
from typing import Any


SECRET_LIKE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


class ModelOpsCheapFirstCanaryChangeManifestService:
    """Build a metadata-only manual change manifest for approved canary rows."""

    def build_manifest(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        canary_plan = _dict(data.get("cheap_first_canary_plan"))
        approval_packet = _dict(data.get("cheap_first_canary_approval_packet"))
        rollback_drill = _dict(data.get("cheap_first_canary_rollback_drill"))

        source_approval_status = _status(approval_packet.get("status"), "not_supplied")
        source_rollback_drill_status = _status(rollback_drill.get("status"), "not_supplied")
        plan_index = {
            str(step.get("id")): step
            for step in _list(canary_plan.get("canary_steps"))
            if isinstance(step, dict) and step.get("id")
        }
        approval_index = {
            str(item.get("id")): item
            for item in _list(approval_packet.get("approval_items"))
            if isinstance(item, dict) and item.get("id")
        }
        approval_by_step = {
            str(item.get("source_step_id")): item
            for item in _list(approval_packet.get("approval_items"))
            if isinstance(item, dict) and item.get("source_step_id")
        }
        rollback_items = [
            item for item in _list(rollback_drill.get("rollback_drill_items")) if isinstance(item, dict)
        ]
        manifest_items = [
            self._manifest_item(item, plan_index, approval_index, approval_by_step)
            for item in rollback_items
        ]
        ready = [item for item in manifest_items if item["manifest_status"] == "manifest_ready"]
        blocked = [item for item in manifest_items if item["manifest_status"] == "manifest_blocked"]
        rollback = [item for item in manifest_items if item["manifest_status"] == "rollback_review_required"]
        monitor = [item for item in manifest_items if item["manifest_status"] == "monitor_only"]
        status = self._status(source_rollback_drill_status, ready, blocked, rollback, monitor)

        return {
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-canary-change-manifest",
                "notes": [
                    "Consumes the metadata-only canary plan, approval packet, and rollback drill.",
                    "Produces a manual external change set for maintainer review only.",
                    "Does not write environment files, write configuration, call a gateway, shift traffic, or persist a change record.",
                ],
            },
            "summary": {
                "manifest_item_count": len(manifest_items),
                "ready_change_count": len(ready),
                "blocked_change_count": len(blocked),
                "rollback_review_count": len(rollback),
                "monitor_only_count": len(monitor),
                "source_rollback_drill_status": source_rollback_drill_status,
                "source_approval_status": source_approval_status,
                "configuration_written": False,
                "env_file_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
                "change_applied": False,
                "manifest_record_written": False,
                "secret_value_included": False,
            },
            "change_manifest_policy": {
                "external_execution_required": True,
                "configuration_write_allowed": False,
                "env_file_write_allowed": False,
                "traffic_shift_allowed": False,
                "requires_maintainer_approval": True,
                "requires_rollback_drill_ready": True,
                "includes_secret_values": False,
            },
            "change_manifest_items": manifest_items,
            "ready_change_item_ids": [item["id"] for item in ready],
            "blocked_change_item_ids": [item["id"] for item in blocked],
            "rollback_review_item_ids": [item["id"] for item in rollback],
            "recommended_actions": self._recommended_actions(status, ready, blocked, rollback, monitor),
            "privacy_boundary": {
                "credentials_included": False,
                "secret_values_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "approver_identity_included": False,
                "configuration_written": False,
                "env_file_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "manifest_record_written": False,
                "output_scope": "canary step ids, task names, env var names, model ids, manual prerequisites, and validation commands only",
            },
            "claim_boundary": {
                "change_applied": False,
                "maintainer_approval_claimed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "automatic_canary_rollout_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_canary_approval_packet.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _manifest_item(
        self,
        rollback_item: dict[str, Any],
        plan_index: dict[str, dict[str, Any]],
        approval_index: dict[str, dict[str, Any]],
        approval_by_step: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        source_step_id = str(rollback_item.get("source_step_id") or "unknown-step")
        source_approval_item_id = str(rollback_item.get("source_approval_item_id") or f"approval-{source_step_id}")
        plan_step = plan_index.get(source_step_id, {})
        approval_item = approval_index.get(source_approval_item_id) or approval_by_step.get(source_step_id, {})
        approval_status = _status(approval_item.get("approval_status") or rollback_item.get("approval_status"), "missing")
        drill_status = _status(rollback_item.get("drill_status"), "missing")
        manifest_status = self._manifest_status(approval_status, drill_status)
        task = _safe_text(rollback_item.get("task") or approval_item.get("task") or plan_step.get("task") or "unknown")
        phase = _safe_text(rollback_item.get("phase") or approval_item.get("phase") or plan_step.get("phase") or "unknown")
        env_var = _safe_optional_text(plan_step.get("env_var"))
        current_model = _safe_text(plan_step.get("current_model"))
        recommended_model = _safe_text(plan_step.get("recommended_model"))
        batch_percentage = _safe_int(plan_step.get("batch_percentage") or approval_item.get("batch_percentage"))
        holdout_percentage = _safe_int(plan_step.get("holdout_percentage") or approval_item.get("holdout_percentage"))

        return {
            "id": f"change-manifest-{source_step_id}",
            "source_rollback_drill_item_id": str(rollback_item.get("id") or f"rollback-drill-{source_step_id}"),
            "source_approval_item_id": source_approval_item_id,
            "source_step_id": source_step_id,
            "task": task,
            "phase": phase,
            "approval_status": approval_status,
            "drill_status": drill_status,
            "manifest_status": manifest_status,
            "env_var": env_var,
            "current_model": current_model,
            "recommended_model": recommended_model,
            "batch_percentage": batch_percentage,
            "holdout_percentage": holdout_percentage,
            "external_change_set": {
                "env_var": env_var,
                "from_model": current_model,
                "to_model": recommended_model,
                "batch_percentage": batch_percentage,
                "holdout_percentage": holdout_percentage,
                "apply_mode": "manual_only",
                "secret_value_included": False,
            },
            "prerequisites": self._prerequisites(manifest_status),
            "operator_steps": self._operator_steps(task, env_var, current_model, recommended_model, manifest_status),
            "configuration_written": False,
            "env_file_written": False,
            "gateway_called": False,
            "traffic_shifted": False,
            "change_applied": False,
            "manifest_record_written": False,
            "action": self._action(task, manifest_status),
        }

    def _manifest_status(self, approval_status: str, drill_status: str) -> str:
        if drill_status == "rollback_drill_required" or approval_status == "rollback_review_required":
            return "rollback_review_required"
        if drill_status == "monitor_only" or approval_status == "monitor_only":
            return "monitor_only"
        if drill_status == "drill_ready" and approval_status == "ready_for_maintainer_approval":
            return "manifest_ready"
        return "manifest_blocked"

    def _prerequisites(self, manifest_status: str) -> list[str]:
        if manifest_status == "manifest_ready":
            return [
                "maintainer-owner-signoff",
                "model-ops-reviewer-signoff",
                "rollback-drill-ready",
                "passing-aggregate-canary-observation",
                "external-release-record-opened",
            ]
        if manifest_status == "rollback_review_required":
            return [
                "rollback-trigger-review-complete",
                "failing-observation-reviewed",
                "previous-default-retained-or-restored-outside-service",
            ]
        if manifest_status == "monitor_only":
            return ["no-default-change-queued", "continue-current-default-monitoring"]
        return [
            "approval-packet-ready",
            "rollback-drill-ready",
            "passing-aggregate-canary-observation-attached",
        ]

    def _operator_steps(
        self,
        task: str,
        env_var: str | None,
        current_model: str,
        recommended_model: str,
        manifest_status: str,
    ) -> list[str]:
        if manifest_status == "manifest_ready":
            target = env_var or f"{task} explicit routing default"
            return [
                f"Review the external change request for {target}.",
                f"Confirm the current model remains {current_model or 'recorded externally'}.",
                f"Prepare the manual default update to {recommended_model or 'the reviewed recommended model'} outside this service.",
                "Attach rollback drill evidence and keep holdout traffic active before applying any external change.",
            ]
        if manifest_status == "rollback_review_required":
            return [
                f"Do not advance the {task} canary.",
                "Review rollback trigger evidence outside this service.",
                "Keep the previous default active until maintainer review clears the rollback case.",
            ]
        if manifest_status == "monitor_only":
            return [
                f"Continue monitoring the current {task} default.",
                "No external change set is queued by this manifest.",
            ]
        return [
            f"Hold the {task} default change.",
            "Attach current aggregate observations and approval evidence before creating an external change request.",
        ]

    def _action(self, task: str, manifest_status: str) -> str:
        if manifest_status == "manifest_ready":
            return f"Review and execute the {task} default change manually outside this service after approval."
        if manifest_status == "rollback_review_required":
            return f"Review rollback evidence for {task}; this manifest will not apply a change."
        if manifest_status == "monitor_only":
            return f"No change manifest is queued for {task}; continue monitoring."
        return f"Hold the {task} change manifest until approval and rollback drill evidence are ready."

    def _status(
        self,
        source_rollback_drill_status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
    ) -> str:
        if rollback:
            return "rollback_review_required"
        if blocked:
            return "manifest_blocked"
        if ready:
            return "manifest_ready"
        if monitor:
            return "monitor_only"
        return source_rollback_drill_status if source_rollback_drill_status != "not_supplied" else "not_supplied"

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
            actions.append("Review rollback-required canary rows before preparing any external default change.")
        if blocked:
            actions.append("Resolve approval, observation, or rollback-drill blockers before creating a change request.")
        if ready:
            actions.append("Attach this manifest to the external release record and apply changes only after maintainer approval.")
        if status == "monitor_only" and monitor:
            actions.append("No external canary default change is queued; continue cheap-first monitoring.")
        return actions or ["Submit approval and rollback drill evidence before preparing a change manifest."]


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


def _safe_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = _safe_text(value)
    return text or None


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    if SECRET_LIKE_PATTERN.search(text):
        return "redacted-secret-like-value"
    return text
