from __future__ import annotations

from typing import Any

from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


class UserNeedImplementationPriorityQueueService:
    """Turn user-need benchmark coverage into a metadata-only implementation queue."""

    def __init__(self, coverage_service: UserNeedBenchmarkCoverageService | None = None) -> None:
        self.coverage_service = coverage_service or UserNeedBenchmarkCoverageService()

    def build_queue(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        coverage = (
            data.get("user_need_benchmark_coverage")
            if isinstance(data.get("user_need_benchmark_coverage"), dict)
            else self.coverage_service.build_coverage()
        )
        items = [self._queue_item(row) for row in coverage["coverage_rows"]]
        items = sorted(items, key=lambda item: (-item["queue_priority_score"], item["need_id"]))
        blocked = [item for item in items if item["action_status"] == "blocked"]
        review = [item for item in items if item["action_status"] == "review_required"]
        ready = [item for item in items if item["action_status"] == "ready"]
        high_priority_items = [item for item in items if item["priority_band"] == "high"]
        public_review_items = [
            item for item in items if "public-benchmark-license-review" in item["implementation_tracks"]
        ]
        calibration_attention_items = [
            item for item in items if "cheap-first-calibration-review" in item["implementation_tracks"]
        ]

        return {
            "status": "blocked" if blocked else ("review_required" if review else "ready"),
            "method": {
                "type": "user-need-implementation-priority-queue",
                "notes": [
                    "Ranks user needs by priority score, local benchmark coverage, public benchmark license state, and cheap-first calibration state.",
                    "Uses metadata-only local coverage rows; it does not download public datasets or call model providers.",
                    "Queue items are implementation planning records, not production accuracy or public benchmark-score claims.",
                ],
            },
            "summary": {
                "queue_item_count": len(items),
                "ready_action_count": len(ready),
                "review_required_action_count": len(review),
                "blocked_action_count": len(blocked),
                "high_priority_item_count": len(high_priority_items),
                "public_benchmark_review_item_count": len(public_review_items),
                "calibration_attention_item_count": len(calibration_attention_items),
                "source_coverage_status": coverage["status"],
                "source_high_priority_gap_count": coverage["summary"]["high_priority_gap_count"],
                "source_public_benchmark_license_review_required_need_count": coverage["summary"][
                    "public_benchmark_license_review_required_need_count"
                ],
                "source_cheap_first_calibration_attention_need_count": coverage["summary"][
                    "cheap_first_calibration_attention_need_count"
                ],
                "local_run_only": True,
                "network_access": "disabled",
                "model_calls": "not_required",
                "external_dataset_downloads": False,
                "raw_text_returned": False,
            },
            "queue_items": items,
            "blocked_need_ids": [item["need_id"] for item in blocked],
            "review_need_ids": [item["need_id"] for item in review],
            "ready_need_ids": [item["need_id"] for item in ready],
            "recommended_actions": self._recommended_actions(blocked, review, ready),
            "source_boundary": {
                "coverage_endpoint": "/api/v1/maintenance/user-needs/benchmark-coverage",
                "public_sampler_endpoint": coverage["summary"]["public_sampler_endpoint"],
                "uses_public_benchmark_metadata": True,
                "imports_public_benchmark_samples": False,
                "uses_raw_user_feedback": False,
                "uses_raw_legal_text": False,
                "uses_model_outputs": False,
                "uses_credentials": False,
            },
            "privacy_boundary": {
                "returns_raw_benchmark_samples": False,
                "returns_public_benchmark_text": False,
                "returns_fixture_snippets": False,
                "returns_calibration_payloads": False,
                "returns_raw_model_output": False,
                "returns_user_feedback_text": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_access": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_user_need_implementation_priority_queue.py tests/test_user_need_benchmark_coverage.py -q",
                "python -m pytest tests/test_user_needs_radar.py tests/test_legal_public_benchmark_sampler.py tests/test_gemini_newapi_cheap_first_calibration.py -q",
            ],
        }

    def _queue_item(self, row: dict[str, Any]) -> dict[str, Any]:
        tracks = self._implementation_tracks(row)
        blockers = self._blockers(row)
        review_reasons = self._review_reasons(row)
        action_status = self._action_status(blockers, review_reasons)
        priority_score = self._queue_priority(row, blockers, review_reasons)
        return {
            "id": f"user-need-implementation-{row['need_id']}",
            "need_id": row["need_id"],
            "title": row["title"],
            "category": row["category"],
            "priority_band": row["priority_band"],
            "user_need_priority_score": row["priority_score"],
            "queue_priority_score": priority_score,
            "coverage_status": row["coverage_status"],
            "public_benchmark_status": row["public_benchmark_status"],
            "calibration_status": row["calibration_status"],
            "action_status": action_status,
            "implementation_tracks": tracks,
            "blocker_codes": blockers,
            "review_reason_codes": review_reasons,
            "linked_benchmark_case_ids": row["linked_benchmark_case_ids"],
            "linked_fixture_ids": row["linked_fixture_ids"],
            "linked_public_source_ids": row["linked_public_source_ids"],
            "linked_calibration_task_ids": row["linked_calibration_task_ids"],
            "linked_backlog_item_ids": row["linked_backlog_item_ids"],
            "next_actions": self._next_actions(row, blockers, review_reasons),
            "release_gate_links": row["linked_release_gates"],
        }

    def _implementation_tracks(self, row: dict[str, Any]) -> list[str]:
        tracks: list[str] = []
        if not row["linked_benchmark_case_ids"] or not row["linked_fixture_ids"]:
            tracks.append("local-benchmark-fixture")
        if not row["linked_backlog_item_ids"]:
            tracks.append("research-backlog-link")
        if row["public_benchmark_status"] == "license_review_required":
            tracks.append("public-benchmark-license-review")
        if row["calibration_status"] in {"warn", "fail"}:
            tracks.append("cheap-first-calibration-review")
        if row["coverage_status"] == "covered" and not tracks:
            tracks.append("release-gate-verification")
        return tracks

    def _blockers(self, row: dict[str, Any]) -> list[str]:
        blockers: list[str] = []
        if row["coverage_status"] == "gap":
            blockers.append("missing-local-benchmark-coverage")
        if row["priority_band"] == "high" and not row["linked_fixture_ids"]:
            blockers.append("high-priority-local-fixture-missing")
        if row["calibration_status"] == "fail":
            blockers.append("cheap-first-calibration-failing")
        return blockers

    def _review_reasons(self, row: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if row["coverage_status"] == "partial":
            reasons.append("partial-local-benchmark-coverage")
        if row["public_benchmark_status"] == "license_review_required":
            reasons.append("public-benchmark-license-review-required")
        if row["public_benchmark_status"] == "catalog_only":
            reasons.append("public-benchmark-catalog-only")
        if row["calibration_status"] == "warn":
            reasons.append("cheap-first-calibration-warning")
        if not row["linked_backlog_item_ids"]:
            reasons.append("research-backlog-link-missing")
        return reasons

    def _action_status(self, blockers: list[str], review_reasons: list[str]) -> str:
        if blockers:
            return "blocked"
        if review_reasons:
            return "review_required"
        return "ready"

    def _queue_priority(self, row: dict[str, Any], blockers: list[str], review_reasons: list[str]) -> int:
        score = int(row["priority_score"])
        score += 25 if row["priority_band"] == "high" else 10 if row["priority_band"] == "medium" else 0
        score += 20 * len(blockers)
        score += 8 * len(review_reasons)
        if row["public_benchmark_status"] == "license_review_required":
            score += 6
        if row["calibration_status"] in {"warn", "fail"}:
            score += 10
        return max(0, min(100, score))

    def _next_actions(
        self,
        row: dict[str, Any],
        blockers: list[str],
        review_reasons: list[str],
    ) -> list[str]:
        actions: list[str] = []
        if "missing-local-benchmark-coverage" in blockers:
            actions.append(f"Create a laptop-safe synthetic benchmark case and fixture for {row['need_id']}.")
        if "high-priority-local-fixture-missing" in blockers:
            actions.append("Attach at least one local fixture before using this need in release claims.")
        if "partial-local-benchmark-coverage" in review_reasons:
            actions.append("Close partial coverage by linking a backlog item, fixture, or benchmark case before release review.")
        if "public-benchmark-license-review-required" in review_reasons:
            actions.append("Keep public benchmark evidence metadata-only until license and attribution review are complete.")
        if "cheap-first-calibration-warning" in review_reasons or "cheap-first-calibration-failing" in blockers:
            actions.append("Rerun cheap-first calibration before changing Gemini/NewAPI routing defaults.")
        actions.extend(row.get("next_actions", [])[:2])
        return _dedupe(actions)[:4] or ["Keep this need attached to release gates and rerun coverage after implementation changes."]

    def _recommended_actions(
        self,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
    ) -> list[str]:
        if blocked:
            return [
                "Clear blocked user-need items before claiming full benchmark or roadmap coverage: "
                + ", ".join(item["need_id"] for item in blocked[:5])
                + ".",
                "Prioritize local synthetic fixtures and backlog links before importing public benchmark samples.",
                "Keep cheap-first routing changes tied to passing calibration and source-safe benchmark coverage.",
            ]
        if review:
            return [
                "Review public benchmark license states and partial coverage before release claims.",
                "Use this queue to choose the next laptop-safe fixture or product UI improvement.",
            ]
        if ready:
            return ["All queued user-need implementation items are ready for release-gate verification."]
        return ["Add user needs and benchmark coverage metadata before scheduling implementation work."]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
