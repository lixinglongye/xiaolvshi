from __future__ import annotations

from typing import Any


class ModelOpsCheapFirstPriorityQueueService:
    """Rank cheap-first ModelOps work without changing runtime configuration."""

    def build_queue(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        default_optimization = _dict(data.get("default_optimization"))
        coverage_gate = _dict(data.get("gemini_cheap_first_coverage_gate"))
        route_quality_budget = _dict(data.get("route_quality_budget"))
        default_change_queue = _dict(data.get("default_change_queue"))
        release_decision = _dict(data.get("cheap_first_release_decision"))
        price_refresh = _dict(data.get("price_refresh_monitor"))
        catalog_source_audit = _dict(data.get("catalog_source_audit"))

        default_rows = _by_task(default_optimization.get("recommendations"))
        coverage_rows = _by_task(coverage_gate.get("coverage_rows"))
        quality_rows = _by_task(route_quality_budget.get("task_quality_budgets"))
        change_rows = _by_task(default_change_queue.get("queue_items"))
        tasks = _ordered_tasks(
            default_optimization.get("recommendations"),
            default_change_queue.get("queue_items"),
            coverage_gate.get("coverage_rows"),
            route_quality_budget.get("task_quality_budgets"),
        )
        release_summary = _dict(release_decision.get("summary"))
        release_gate_status = str(release_decision.get("status") or "missing").lower()
        release_gate_blocked = bool(release_summary.get("default_promotion_blocked")) or release_gate_status in {
            "fail",
            "failed",
            "blocked",
        }
        release_gate_review = bool(release_summary.get("maintainer_review_required")) or release_gate_status in {
            "warn",
            "warning",
            "review_required",
        }

        items = [
            self._priority_item(
                task,
                default_row=default_rows.get(task, {}),
                coverage_row=coverage_rows.get(task, {}),
                quality_row=quality_rows.get(task, {}),
                change_row=change_rows.get(task, {}),
                release_gate_status=release_gate_status,
                release_gate_blocked=release_gate_blocked,
                release_gate_review=release_gate_review,
            )
            for task in tasks
        ]
        items.sort(key=lambda item: (-item["priority_score"], item["task"]))
        for index, item in enumerate(items, start=1):
            item["priority_rank"] = index

        blocked = [item for item in items if item["work_status"] == "blocked"]
        review = [item for item in items if item["work_status"] == "review_required"]
        ready = [item for item in items if item["work_status"] == "ready"]
        monitor = [item for item in items if item["work_status"] == "monitor_only"]
        status = "blocked" if blocked else ("review_required" if review else "ready")

        return {
            "id": "model-ops-cheap-first-priority-queue",
            "title": "ModelOps cheap-first priority queue",
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-priority-queue",
                "notes": [
                    "Ranks existing cheap-first ModelOps signals into a maintainer execution order.",
                    "Consumes default optimization, Gemini coverage, route quality, default-change queue, release decision, pricing, and catalog metadata.",
                    "Does not write environment files, change defaults, call NewAPI/Gemini/OpenAI/Google, call a gateway, or run probes.",
                    "Priority is an operator triage score, not approval to promote a default model automatically.",
                ],
            },
            "summary": {
                "priority_item_count": len(items),
                "p0_count": sum(1 for item in items if item["priority_label"] == "P0"),
                "p1_count": sum(1 for item in items if item["priority_label"] == "P1"),
                "p2_count": sum(1 for item in items if item["priority_label"] == "P2"),
                "p3_count": sum(1 for item in items if item["priority_label"] == "P3"),
                "blocked_count": len(blocked),
                "review_required_count": len(review),
                "ready_count": len(ready),
                "monitor_only_count": len(monitor),
                "change_request_count": sum(1 for item in items if item["requires_change"]),
                "estimated_monthly_savings_usd": round(
                    sum(float(item["estimated_monthly_savings_usd"] or 0.0) for item in items),
                    6,
                ),
                "release_gate_status": release_gate_status,
                "default_change_queue_status": str(default_change_queue.get("status") or "missing").lower(),
                "coverage_gate_status": str(coverage_gate.get("status") or "missing").lower(),
                "route_quality_status": str(route_quality_budget.get("status") or "missing").lower(),
                "price_refresh_status": str(price_refresh.get("status") or "missing").lower(),
                "catalog_source_audit_status": str(catalog_source_audit.get("status") or "missing").lower(),
                "configuration_written": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
            },
            "priority_items": items,
            "blocking_item_ids": [item["id"] for item in blocked],
            "review_item_ids": [item["id"] for item in review],
            "recommended_actions": self._recommended_actions(items),
            "privacy_boundary": {
                "metadata_only": True,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payloads_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "configuration_written": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "output_scope": "task ids, model ids, env var names, status labels, priority scores, reason codes, and validation commands only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_included": False,
                "production_quality_claimed": False,
                "twenty_four_hour_completion_claimed": False,
                "hundred_update_completion_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_priority_queue.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_release_decision.py tests/test_model_route_quality_budget.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _priority_item(
        self,
        task: str,
        *,
        default_row: dict[str, Any],
        coverage_row: dict[str, Any],
        quality_row: dict[str, Any],
        change_row: dict[str, Any],
        release_gate_status: str,
        release_gate_blocked: bool,
        release_gate_review: bool,
    ) -> dict[str, Any]:
        requires_change = bool(default_row.get("requires_change") or change_row.get("requires_change"))
        queue_status = str(change_row.get("queue_status") or ("ready" if requires_change else "no_action")).lower()
        coverage_status = str(coverage_row.get("coverage_status") or "missing").lower()
        default_status = str(default_row.get("status") or "missing").lower()
        quality_score = _safe_int(quality_row.get("quality_score"))
        quality_floor = _safe_int(quality_row.get("quality_floor"), default=75)
        quality_review_action = str(quality_row.get("review_action") or "missing")
        estimated_savings = _safe_float(default_row.get("estimated_monthly_savings_usd"))
        reason_codes = _dedupe(
            [
                *_strings(change_row.get("reason_codes")),
                *_strings(coverage_row.get("reason_codes")),
                *self._derived_reason_codes(
                    release_gate_blocked=release_gate_blocked,
                    release_gate_review=release_gate_review,
                    queue_status=queue_status,
                    coverage_status=coverage_status,
                    default_status=default_status,
                    requires_change=requires_change,
                    quality_row=quality_row,
                    quality_score=quality_score,
                    quality_floor=quality_floor,
                    estimated_savings=estimated_savings,
                ),
            ]
        )
        work_status = self._work_status(
            queue_status=queue_status,
            coverage_status=coverage_status,
            default_status=default_status,
            requires_change=requires_change,
            reason_codes=reason_codes,
        )
        priority_score = self._priority_score(
            work_status=work_status,
            requires_change=requires_change,
            release_gate_blocked=release_gate_blocked,
            release_gate_review=release_gate_review,
            queue_status=queue_status,
            coverage_status=coverage_status,
            quality_score=quality_score,
            quality_floor=quality_floor,
            estimated_savings=estimated_savings,
            reason_codes=reason_codes,
        )
        return {
            "id": f"cheap-first-priority-{task}",
            "task": task,
            "priority_rank": 0,
            "priority_score": priority_score,
            "priority_label": self._priority_label(priority_score),
            "risk_level": self._risk_level(priority_score),
            "work_status": work_status,
            "release_gate_status": release_gate_status,
            "default_change_queue_status": queue_status,
            "coverage_status": coverage_status,
            "default_optimization_status": default_status,
            "quality_review_action": quality_review_action,
            "env_var": default_row.get("env_var") or change_row.get("env_var"),
            "current_model": str(default_row.get("current_model") or change_row.get("current_model") or quality_row.get("runtime_default_model") or ""),
            "recommended_model": str(
                default_row.get("recommended_model")
                or change_row.get("recommended_model")
                or quality_row.get("recommended_model")
                or coverage_row.get("recommended_model")
                or ""
            ),
            "cheap_start_model": str(quality_row.get("cheap_start_model") or ""),
            "current_cost_tier": default_row.get("current_cost_tier") or change_row.get("current_cost_tier") or quality_row.get("runtime_default_cost_tier"),
            "recommended_cost_tier": default_row.get("recommended_cost_tier") or change_row.get("recommended_cost_tier") or quality_row.get("recommended_model_cost_tier"),
            "requires_change": requires_change,
            "requires_operator_review": bool(default_row.get("requires_operator_review") or change_row.get("requires_operator_review")),
            "runtime_default_has_required_capabilities": bool(quality_row.get("runtime_default_has_required_capabilities", True)),
            "runtime_default_over_budget": bool(quality_row.get("runtime_default_over_budget", False)),
            "quality_score": quality_score,
            "quality_floor": quality_floor,
            "estimated_monthly_savings_usd": estimated_savings,
            "reason_codes": reason_codes,
            "next_action": self._next_action(
                task=task,
                work_status=work_status,
                env_var=default_row.get("env_var") or change_row.get("env_var"),
                recommended_model=str(default_row.get("recommended_model") or change_row.get("recommended_model") or ""),
                reason_codes=reason_codes,
            ),
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_priority_queue.py -q",
                "python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_route_quality_budget.py -q",
            ],
            "privacy_boundary": {
                "raw_prompt_returned": False,
                "raw_payload_returned": False,
                "raw_model_output_returned": False,
                "credentials_returned": False,
            },
        }

    def _derived_reason_codes(
        self,
        *,
        release_gate_blocked: bool,
        release_gate_review: bool,
        queue_status: str,
        coverage_status: str,
        default_status: str,
        requires_change: bool,
        quality_row: dict[str, Any],
        quality_score: int,
        quality_floor: int,
        estimated_savings: float | None,
    ) -> list[str]:
        codes: list[str] = []
        actionable = requires_change or queue_status != "no_action"
        if release_gate_blocked and actionable:
            codes.append("release-gate-blocked")
        elif release_gate_review and actionable:
            codes.append("release-gate-review")
        if queue_status == "blocked":
            codes.append("default-change-blocked")
        if queue_status == "review_required":
            codes.append("default-change-review-required")
        if coverage_status == "blocked":
            codes.append("gemini-coverage-blocked")
        if coverage_status == "review_required":
            codes.append("gemini-coverage-review-required")
        if default_status == "fail":
            codes.append("default-optimization-failed")
        if default_status == "warn":
            codes.append("default-optimization-review")
        if requires_change:
            codes.append("default-change-requested")
        if not bool(quality_row.get("runtime_default_has_required_capabilities", True)):
            codes.append("runtime-default-capability-gap")
        if bool(quality_row.get("runtime_default_over_budget", False)):
            codes.append("runtime-default-over-budget")
        if quality_score and quality_score < quality_floor:
            codes.append("quality-score-below-floor")
        if estimated_savings is not None and estimated_savings > 0:
            codes.append("estimated-savings-available")
        return codes

    def _work_status(
        self,
        *,
        queue_status: str,
        coverage_status: str,
        default_status: str,
        requires_change: bool,
        reason_codes: list[str],
    ) -> str:
        blocking_codes = {
            "release-gate-blocked",
            "default-change-blocked",
            "gemini-coverage-blocked",
            "default-optimization-failed",
            "unknown_model",
            "cheap_first_not_aligned",
            "runtime-default-capability-gap",
        }
        if queue_status == "blocked" or coverage_status == "blocked" or default_status == "fail":
            return "blocked"
        if any(code in blocking_codes or code.startswith("gateway:fail") for code in reason_codes):
            return "blocked"
        if queue_status == "review_required" or coverage_status == "review_required" or default_status == "warn":
            return "review_required"
        if any(code.endswith("review") or code.endswith("review-required") or code == "quality-score-below-floor" for code in reason_codes):
            return "review_required"
        return "ready" if requires_change else "monitor_only"

    def _priority_score(
        self,
        *,
        work_status: str,
        requires_change: bool,
        release_gate_blocked: bool,
        release_gate_review: bool,
        queue_status: str,
        coverage_status: str,
        quality_score: int,
        quality_floor: int,
        estimated_savings: float | None,
        reason_codes: list[str],
    ) -> int:
        score = 0
        if work_status == "blocked":
            score += 45
        elif work_status == "review_required":
            score += 25
        elif work_status == "ready":
            score += 15
        if release_gate_blocked:
            score += 20
        elif release_gate_review:
            score += 10
        if requires_change:
            score += 20
        if queue_status == "blocked":
            score += 20
        elif queue_status == "review_required":
            score += 12
        if coverage_status == "blocked":
            score += 20
        elif coverage_status == "review_required":
            score += 10
        if quality_score and quality_score < quality_floor:
            score += 10
        if estimated_savings is not None and estimated_savings > 0:
            score += min(20, max(5, int(round(estimated_savings * 10))))
        if "unknown_model" in reason_codes:
            score += 18
        if any(code.startswith("price:") or "missing-pric" in code for code in reason_codes):
            score += 12
        if "premium_exception_requires_review" in reason_codes:
            score += 8
        return min(score, 100)

    def _priority_label(self, score: int) -> str:
        if score >= 85:
            return "P0"
        if score >= 60:
            return "P1"
        if score >= 30:
            return "P2"
        return "P3"

    def _risk_level(self, score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    def _next_action(self, *, task: str, work_status: str, env_var: Any, recommended_model: str, reason_codes: list[str]) -> str:
        target = str(env_var or "explicit model request")
        if work_status == "blocked":
            return f"Resolve {task} blockers before changing {target}; first blockers: {', '.join(reason_codes[:3])}."
        if work_status == "review_required":
            return f"Complete maintainer review for {task} before setting {target} to {recommended_model or 'a new default'}."
        if work_status == "ready":
            return f"Run validation commands, then maintainer may queue {target}={recommended_model} through the approved change path."
        return f"Keep monitoring {task}; no cheap-first default change is currently prioritized."

    def _recommended_actions(self, items: list[dict[str, Any]]) -> list[str]:
        active = [item for item in items if item["work_status"] != "monitor_only"]
        if active:
            return [item["next_action"] for item in active[:5]]
        return [
            "No cheap-first default changes are currently prioritized; rerun after catalog, pricing, gateway, or route-quality evidence changes.",
        ]


def _by_task(value: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in _list(value):
        if not isinstance(row, dict):
            continue
        task = str(row.get("task") or "").strip()
        if task and task not in result:
            result[task] = row
    return result


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


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
