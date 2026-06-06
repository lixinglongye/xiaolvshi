from __future__ import annotations

from typing import Any

from services.model_route_legal_benchmark_risk_queue import ModelRouteLegalBenchmarkRiskQueueService


class ModelOpsLegalBenchmarkRiskBridgeService:
    """Bridge legal benchmark route-risk metadata into ModelOps default reviews."""

    def __init__(self, risk_queue_service: ModelRouteLegalBenchmarkRiskQueueService | None = None) -> None:
        self.risk_queue_service = risk_queue_service or ModelRouteLegalBenchmarkRiskQueueService()

    def build_bridge(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        risk_queue = _dict(data.get("model_route_legal_benchmark_risk_queue")) or self.risk_queue_service.build_queue()
        release_decision = _dict(data.get("cheap_first_release_decision"))
        default_change_queue = _dict(data.get("default_change_queue"))
        route_reviews = [self._route_review(row) for row in _list_of_dicts(risk_queue.get("queue_rows"))]
        user_need_reviews = [self._user_need_review(row) for row in _list_of_dicts(risk_queue.get("user_need_rows"))]
        route_reviews.sort(key=lambda row: row["priority"], reverse=True)
        user_need_reviews.sort(key=lambda row: row["priority_score"], reverse=True)

        blocking_reviews = [row for row in route_reviews if row["risk_level"] == "block"]
        watch_reviews = [
            row
            for row in route_reviews
            if row["risk_level"] in {"watch", "operator_exception"} or row["premium_exception_required"]
        ]
        license_watch_reviews = [
            row for row in route_reviews if "benchmark-license-review" in row["reason_codes"]
        ]
        default_change_items = _list_of_dicts(default_change_queue.get("queue_items"))
        status = self._status(blocking_reviews, watch_reviews, license_watch_reviews)

        return {
            "id": "modelops-legal-benchmark-risk-bridge",
            "title": "ModelOps legal benchmark risk bridge",
            "status": status,
            "method": {
                "type": "modelops-legal-benchmark-risk-bridge",
                "notes": [
                    "Summarizes legal benchmark route-risk metadata for cheap-first default-model reviews.",
                    "Consumes the maintenance risk queue and ModelOps release/default-change metadata only.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, public datasets, or model probes.",
                    "Does not return legal text, benchmark samples, prompts, model outputs, credentials, or raw payloads.",
                ],
            },
            "summary": {
                "route_review_count": len(route_reviews),
                "user_need_review_count": len(user_need_reviews),
                "blocking_route_count": len(blocking_reviews),
                "watch_route_count": len(watch_reviews),
                "premium_exception_route_count": sum(1 for row in route_reviews if row["premium_exception_required"]),
                "benchmark_license_watch_count": len(license_watch_reviews),
                "cheap_first_allowed_route_count": sum(1 for row in route_reviews if row["cheap_first_allowed"]),
                "balanced_precheck_route_count": sum(1 for row in route_reviews if row["balanced_precheck_required"]),
                "default_change_queue_item_count": len(default_change_items),
                "source_risk_queue_status": str(risk_queue.get("status") or "missing"),
                "source_release_decision_status": str(release_decision.get("status") or "missing"),
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "raw_payload_echoed": False,
            },
            "route_reviews": route_reviews,
            "user_need_reviews": user_need_reviews,
            "bridge_policy": {
                "current_cheap_first_defaults_allowed": not blocking_reviews,
                "new_default_promotion_allowed": status == "pass",
                "premium_exception_default_allowed": False,
                "requires_fixture_backed_evidence": True,
                "requires_license_review_for_public_benchmarks": True,
                "requires_user_need_mapping": True,
                "configuration_write_allowed": False,
                "gateway_call_allowed": False,
                "dataset_download_allowed": False,
            },
            "blocking_check_ids": [f"route:{row['task_id']}" for row in blocking_reviews],
            "warning_check_ids": _dedupe([f"route:{row['task_id']}" for row in watch_reviews + license_watch_reviews]),
            "recommended_actions": self._recommended_actions(blocking_reviews, watch_reviews, license_watch_reviews),
            "privacy_boundary": {
                "returns_raw_benchmark_samples": False,
                "returns_public_benchmark_text": False,
                "returns_raw_legal_text": False,
                "returns_fixture_snippets": False,
                "returns_prompts": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "output_scope": "task ids, user-need ids, source ids, risk levels, reason codes, and validation commands only",
            },
            "claim_boundary": {
                "public_benchmark_scores_claimed": False,
                "external_dataset_execution_claimed": False,
                "production_accuracy_claimed": False,
                "default_model_changed": False,
                "routing_change_applied": False,
                "live_gateway_quality_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_legal_benchmark_risk_bridge.py tests/test_model_route_legal_benchmark_risk_queue.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _route_review(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": _safe_text(row.get("id"), "unknown-route"),
            "task_id": _safe_text(row.get("task_id"), "unknown"),
            "task": _safe_text(row.get("task"), "unknown"),
            "product_area": _safe_text(row.get("product_area"), "unknown"),
            "risk_level": _safe_text(row.get("risk_level"), "watch"),
            "priority": _safe_int(row.get("priority")),
            "calibration_status": _safe_text(row.get("calibration_status"), "unknown"),
            "calibration_decision": _safe_text(row.get("calibration_decision"), "unknown"),
            "cheap_first_allowed": bool(row.get("cheap_first_allowed")),
            "balanced_precheck_required": bool(row.get("balanced_precheck_required")),
            "premium_exception_required": bool(row.get("premium_exception_required")),
            "cost_tier": _safe_text(row.get("cost_tier"), "unknown"),
            "research_source_ids": _safe_string_list(row.get("research_source_ids")),
            "user_need_ids": _safe_string_list(row.get("user_need_ids")),
            "coverage_statuses": _safe_string_list(row.get("coverage_statuses")),
            "public_benchmark_statuses": _safe_string_list(row.get("public_benchmark_statuses")),
            "release_gate_links": _safe_string_list(row.get("release_gate_links")),
            "reason_codes": _safe_string_list(row.get("reason_codes")),
            "next_action": _safe_text(row.get("next_action"), "Review route before default changes."),
        }

    def _user_need_review(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "need_id": _safe_text(row.get("need_id"), "unknown"),
            "title": _safe_text(row.get("title"), "unknown"),
            "priority_band": _safe_text(row.get("priority_band"), "unknown"),
            "priority_score": _safe_int(row.get("priority_score")),
            "coverage_status": _safe_text(row.get("coverage_status"), "unknown"),
            "public_benchmark_status": _safe_text(row.get("public_benchmark_status"), "unknown"),
            "calibration_status": _safe_text(row.get("calibration_status"), "unknown"),
            "highest_risk_level": _safe_text(row.get("highest_risk_level"), "watch"),
            "queue_row_ids": _safe_string_list(row.get("queue_row_ids")),
            "task_ids": _safe_string_list(row.get("task_ids")),
            "research_source_ids": _safe_string_list(row.get("research_source_ids")),
            "cheap_first_allowed_count": _safe_int(row.get("cheap_first_allowed_count")),
            "premium_exception_count": _safe_int(row.get("premium_exception_count")),
            "next_action": _safe_text(row.get("next_action"), "Review user need before default changes."),
        }

    def _status(
        self,
        blocking_reviews: list[dict[str, Any]],
        watch_reviews: list[dict[str, Any]],
        license_watch_reviews: list[dict[str, Any]],
    ) -> str:
        if blocking_reviews:
            return "fail"
        if watch_reviews or license_watch_reviews:
            return "review_required"
        return "pass"

    def _recommended_actions(
        self,
        blocking_reviews: list[dict[str, Any]],
        watch_reviews: list[dict[str, Any]],
        license_watch_reviews: list[dict[str, Any]],
    ) -> list[str]:
        if blocking_reviews:
            return [
                f"Repair legal benchmark route evidence before changing defaults for {row['task_id']}."
                for row in blocking_reviews[:5]
            ]
        actions = [
            "Keep current cheap-first legal routes unless fixture-backed and user-need evidence supports a change.",
            "Review this bridge before promoting any Gemini/NewAPI default for legal review, extraction, OCR, or PDF tasks.",
        ]
        if watch_reviews:
            actions.append(
                "Review watchlist routes: " + ", ".join(row["task_id"] for row in watch_reviews[:5]) + "."
            )
        if license_watch_reviews:
            actions.append("Keep public benchmark mappings metadata-only until license review passes.")
        return _dedupe(actions)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _safe_text(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text[:180] if text else fallback


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_text(item, "") for item in value if _safe_text(item, "")]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
