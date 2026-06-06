from __future__ import annotations

import re
from typing import Any


SECRET_LIKE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


class ModelOpsCheapFirstMaintainerExecutionChecklistService:
    """Build a maintainer-only execution checklist for cheap-first default work."""

    def build_checklist(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        priority_queue = _dict(data.get("cheap_first_priority_queue"))
        release_decision = _dict(data.get("cheap_first_release_decision"))
        canary_plan = _dict(data.get("cheap_first_canary_plan"))
        promotion_decision = _dict(data.get("cheap_first_canary_promotion_decision"))
        approval_packet = _dict(data.get("cheap_first_canary_approval_packet"))
        rollback_drill = _dict(data.get("cheap_first_canary_rollback_drill"))
        change_manifest = _dict(data.get("cheap_first_canary_change_manifest"))

        canary_by_task = _by_task(canary_plan.get("canary_steps"))
        promotion_by_task = _by_task(promotion_decision.get("promotion_items"))
        approval_by_task = _by_task(approval_packet.get("approval_items"))
        rollback_by_task = _by_task(rollback_drill.get("rollback_drill_items"))
        manifest_by_task = _by_task(change_manifest.get("change_manifest_items"))
        priority_items = [row for row in _list(priority_queue.get("priority_items")) if isinstance(row, dict)]
        tasks = _ordered_tasks(
            priority_items,
            canary_plan.get("canary_steps"),
            promotion_decision.get("promotion_items"),
            approval_packet.get("approval_items"),
            rollback_drill.get("rollback_drill_items"),
            change_manifest.get("change_manifest_items"),
        )

        items = [
            self._execution_item(
                task,
                priority_item=_first_by_task(priority_items, task),
                release_decision=release_decision,
                canary_step=canary_by_task.get(task, {}),
                promotion_item=promotion_by_task.get(task, {}),
                approval_item=approval_by_task.get(task, {}),
                rollback_item=rollback_by_task.get(task, {}),
                manifest_item=manifest_by_task.get(task, {}),
            )
            for task in tasks
        ]
        items.sort(key=lambda item: (-item["priority_score"], item["task"]))
        for index, item in enumerate(items, start=1):
            item["execution_rank"] = index

        blocked = [item for item in items if item["execution_status"] == "blocked"]
        review = [item for item in items if item["execution_status"] == "review_required"]
        ready = [item for item in items if item["execution_status"] == "ready_for_external_change"]
        monitor = [item for item in items if item["execution_status"] == "monitor_only"]
        rollback = [item for item in items if item["execution_status"] == "rollback_review_required"]
        status = self._status(ready, blocked, review, rollback, monitor)

        return {
            "id": "model-ops-cheap-first-maintainer-execution-checklist",
            "title": "ModelOps cheap-first maintainer execution checklist",
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-maintainer-execution-checklist",
                "notes": [
                    "Consolidates the priority queue, release decision, canary plan, promotion decision, approval packet, rollback drill, and change manifest.",
                    "Creates maintainer execution evidence only; it does not write environment files, update defaults, shift traffic, or persist approvals.",
                    "Keeps cheap-first promotion work gated by release status, canary evidence, approval readiness, rollback drill readiness, and metadata-only boundaries.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, any gateway, or the network.",
                ],
            },
            "summary": {
                "execution_item_count": len(items),
                "ready_for_external_change_count": len(ready),
                "review_required_count": len(review),
                "blocked_count": len(blocked),
                "rollback_review_count": len(rollback),
                "monitor_only_count": len(monitor),
                "priority_queue_status": _status(priority_queue.get("status"), "missing"),
                "release_decision_status": _status(release_decision.get("status"), "missing"),
                "canary_plan_status": _status(canary_plan.get("status"), "missing"),
                "promotion_decision_status": _status(promotion_decision.get("status"), "missing"),
                "approval_packet_status": _status(approval_packet.get("status"), "missing"),
                "rollback_drill_status": _status(rollback_drill.get("status"), "missing"),
                "change_manifest_status": _status(change_manifest.get("status"), "missing"),
                "configuration_written": False,
                "env_file_written": False,
                "approval_record_written": False,
                "gateway_called": False,
                "network_called": False,
                "traffic_shifted": False,
                "raw_payload_echoed": False,
                "secret_value_included": False,
            },
            "execution_policy": {
                "external_execution_required": True,
                "configuration_write_allowed": False,
                "env_file_write_allowed": False,
                "approval_record_write_allowed": False,
                "traffic_shift_allowed": False,
                "gateway_call_allowed": False,
                "requires_release_pass": True,
                "requires_canary_evidence": True,
                "requires_maintainer_approval": True,
                "requires_rollback_drill_ready": True,
                "requires_metadata_only_boundary": True,
            },
            "execution_items": items,
            "ready_execution_item_ids": [item["id"] for item in ready],
            "blocked_execution_item_ids": [item["id"] for item in blocked],
            "review_execution_item_ids": [item["id"] for item in review],
            "rollback_review_item_ids": [item["id"] for item in rollback],
            "recommended_actions": self._recommended_actions(ready, blocked, review, rollback, monitor),
            "privacy_boundary": {
                "metadata_only": True,
                "credentials_included": False,
                "secret_values_included": False,
                "prompts_included": False,
                "raw_payloads_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "configuration_written": False,
                "env_file_written": False,
                "approval_record_written": False,
                "network_called": False,
                "gateway_called": False,
                "traffic_shifted": False,
                "output_scope": "task ids, status labels, model ids, env var names, missing evidence ids, operator actions, and validation commands only",
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "automatic_default_change_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_quality_claimed": False,
                "twenty_four_hour_completion_claimed": False,
                "hundred_update_completion_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_maintainer_execution_checklist.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_priority_queue.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _execution_item(
        self,
        task: str,
        *,
        priority_item: dict[str, Any],
        release_decision: dict[str, Any],
        canary_step: dict[str, Any],
        promotion_item: dict[str, Any],
        approval_item: dict[str, Any],
        rollback_item: dict[str, Any],
        manifest_item: dict[str, Any],
    ) -> dict[str, Any]:
        release_status = _status(release_decision.get("status"), "missing")
        priority_status = _status(priority_item.get("work_status"), "missing")
        canary_status = _status(canary_step.get("step_status"), "missing")
        promotion_status = _status(promotion_item.get("promotion_status"), _status(promotion_item.get("decision_status"), "missing"))
        approval_status = _status(approval_item.get("approval_status"), "missing")
        rollback_status = _status(rollback_item.get("drill_status"), "missing")
        manifest_status = _status(manifest_item.get("manifest_status"), "missing")
        requires_change = bool(priority_item.get("requires_change") or manifest_item.get("change_applied") is True)
        reason_codes = _dedupe(
            [
                *_strings(priority_item.get("reason_codes")),
                *self._derived_reason_codes(
                    priority_status=priority_status,
                    release_status=release_status,
                    canary_status=canary_status,
                    promotion_status=promotion_status,
                    approval_status=approval_status,
                    rollback_status=rollback_status,
                    manifest_status=manifest_status,
                    requires_change=requires_change,
                ),
            ]
        )
        execution_status = self._execution_status(
            priority_status=priority_status,
            release_status=release_status,
            rollback_status=rollback_status,
            manifest_status=manifest_status,
            reason_codes=reason_codes,
            requires_change=requires_change,
        )
        missing_evidence = self._missing_evidence(
            execution_status=execution_status,
            release_status=release_status,
            canary_status=canary_status,
            promotion_status=promotion_status,
            approval_status=approval_status,
            rollback_status=rollback_status,
            manifest_status=manifest_status,
        )
        env_var = _safe_optional_text(priority_item.get("env_var") or manifest_item.get("env_var"))
        current_model = _safe_text(priority_item.get("current_model") or manifest_item.get("current_model"))
        recommended_model = _safe_text(priority_item.get("recommended_model") or manifest_item.get("recommended_model"))
        return {
            "id": f"cheap-first-execution-{task}",
            "task": task,
            "execution_rank": 0,
            "execution_status": execution_status,
            "priority_rank": _safe_int(priority_item.get("priority_rank")),
            "priority_score": _safe_int(priority_item.get("priority_score")),
            "priority_label": _safe_text(priority_item.get("priority_label") or "P3"),
            "priority_work_status": priority_status,
            "release_decision_status": release_status,
            "canary_step_status": canary_status,
            "promotion_decision_status": promotion_status,
            "approval_status": approval_status,
            "rollback_drill_status": rollback_status,
            "manifest_status": manifest_status,
            "env_var": env_var,
            "current_model": current_model,
            "recommended_model": recommended_model,
            "requires_change": requires_change,
            "external_change_allowed": execution_status == "ready_for_external_change",
            "configuration_written": False,
            "env_file_written": False,
            "approval_record_written": False,
            "gateway_called": False,
            "traffic_shifted": False,
            "missing_evidence": missing_evidence,
            "required_evidence": [
                "release decision pass",
                "canary observation/promotion evidence attached",
                "maintainer approval packet ready",
                "rollback drill ready",
                "manual change manifest ready",
                "metadata-only privacy boundary",
            ],
            "reason_codes": reason_codes,
            "operator_action": self._operator_action(
                task=task,
                execution_status=execution_status,
                env_var=env_var,
                current_model=current_model,
                recommended_model=recommended_model,
                missing_evidence=missing_evidence,
            ),
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_maintainer_execution_checklist.py -q",
                "python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py tests/test_model_ops_cheap_first_priority_queue.py -q",
            ],
        }

    def _derived_reason_codes(
        self,
        *,
        priority_status: str,
        release_status: str,
        canary_status: str,
        promotion_status: str,
        approval_status: str,
        rollback_status: str,
        manifest_status: str,
        requires_change: bool,
    ) -> list[str]:
        codes: list[str] = []
        if not requires_change and priority_status == "monitor_only":
            codes.append("current-default-monitor-only")
        if release_status in {"fail", "failed", "blocked"}:
            codes.append("release-decision-blocked")
        elif release_status not in {"pass", "ready", "ok", "success"}:
            codes.append("release-decision-review-required")
        if canary_status in {"missing", "not_supplied"}:
            codes.append("canary-step-missing")
        if promotion_status not in {"advance_next_batch", "ready", "pass", "monitor_only"}:
            codes.append("promotion-decision-not-ready")
        if approval_status not in {"ready_for_maintainer_approval", "monitor_only"}:
            codes.append("approval-packet-not-ready")
        if rollback_status not in {"drill_ready", "monitor_only"}:
            codes.append("rollback-drill-not-ready")
        if manifest_status == "rollback_review_required":
            codes.append("rollback-review-required")
        elif manifest_status not in {"manifest_ready", "monitor_only"}:
            codes.append("change-manifest-not-ready")
        return codes

    def _execution_status(
        self,
        *,
        priority_status: str,
        release_status: str,
        rollback_status: str,
        manifest_status: str,
        reason_codes: list[str],
        requires_change: bool,
    ) -> str:
        if "rollback-review-required" in reason_codes or manifest_status == "rollback_review_required":
            return "rollback_review_required"
        if priority_status == "monitor_only" and not requires_change:
            return "monitor_only"
        if priority_status == "blocked" or release_status in {"fail", "failed", "blocked"}:
            return "blocked"
        if rollback_status == "rollback_drill_required" or manifest_status == "manifest_blocked":
            return "blocked"
        if (
            release_status in {"pass", "ready", "ok", "success"}
            and rollback_status == "drill_ready"
            and manifest_status == "manifest_ready"
            and not any(code.endswith("not-ready") or code.endswith("missing") for code in reason_codes)
        ):
            return "ready_for_external_change"
        return "review_required"

    def _missing_evidence(
        self,
        *,
        execution_status: str,
        release_status: str,
        canary_status: str,
        promotion_status: str,
        approval_status: str,
        rollback_status: str,
        manifest_status: str,
    ) -> list[str]:
        if execution_status == "monitor_only":
            return []
        missing: list[str] = []
        if release_status not in {"pass", "ready", "ok", "success"}:
            missing.append("release-decision-pass")
        if canary_status in {"missing", "not_supplied"}:
            missing.append("canary-plan-step")
        if promotion_status not in {"advance_next_batch", "ready", "pass", "monitor_only"}:
            missing.append("promotion-decision-ready")
        if approval_status not in {"ready_for_maintainer_approval", "monitor_only"}:
            missing.append("approval-packet-ready")
        if rollback_status not in {"drill_ready", "monitor_only"}:
            missing.append("rollback-drill-ready")
        if manifest_status not in {"manifest_ready", "monitor_only"}:
            missing.append("change-manifest-ready")
        return _dedupe(missing)

    def _operator_action(
        self,
        *,
        task: str,
        execution_status: str,
        env_var: str | None,
        current_model: str,
        recommended_model: str,
        missing_evidence: list[str],
    ) -> str:
        target = env_var or f"{task} explicit model route"
        if execution_status == "ready_for_external_change":
            return (
                f"Prepare manual external change for {target} from {current_model or 'the recorded current model'} "
                f"to {recommended_model or 'the reviewed recommended model'} after maintainer signoff."
            )
        if execution_status == "blocked":
            return f"Do not change {target}; resolve blocking evidence first: {', '.join(missing_evidence[:4])}."
        if execution_status == "rollback_review_required":
            return f"Hold {target}; review rollback evidence before any cheap-first default promotion."
        if execution_status == "monitor_only":
            return f"Keep monitoring {task}; no external default change is queued."
        return f"Complete maintainer review for {target}; missing evidence: {', '.join(missing_evidence[:4]) or 'review notes'}."

    def _status(
        self,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
    ) -> str:
        if rollback:
            return "rollback_review_required"
        if blocked:
            return "blocked"
        if ready:
            return "ready_for_external_change"
        if review:
            return "review_required"
        if monitor:
            return "monitor_only"
        return "not_supplied"

    def _recommended_actions(
        self,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        rollback: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
    ) -> list[str]:
        if rollback:
            return ["Review rollback-required canary rows before preparing any external default change."]
        if blocked:
            return ["Resolve blocked release, rollback, or manifest evidence before any cheap-first default change."]
        if ready:
            return ["Attach this checklist to the external release record before a maintainer applies changes outside the service."]
        if review:
            return ["Complete maintainer review and missing canary evidence before creating an external change request."]
        if monitor:
            return ["No cheap-first external change is queued; continue monitoring current defaults."]
        return ["Attach cheap-first priority, release, canary, approval, rollback, and manifest evidence before execution review."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


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


def _by_task(value: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _list(value):
        if not isinstance(row, dict):
            continue
        task = str(row.get("task") or "").strip()
        if task and task not in rows:
            rows[task] = row
    return rows


def _first_by_task(rows: list[dict[str, Any]], task: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("task") or "") == task:
            return row
    return {}


def _ordered_tasks(*row_sets: Any) -> list[str]:
    tasks: list[str] = []
    seen: set[str] = set()
    for rows in row_sets:
        for row in _list(rows):
            if not isinstance(row, dict):
                continue
            task = str(row.get("task") or "").strip()
            if not task or task in seen:
                continue
            seen.add(task)
            tasks.append(task)
    return tasks


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
