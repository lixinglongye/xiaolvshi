from __future__ import annotations

from typing import Any

from schemas.aihub import ChatMessage
from services.model_catalog import task_default_model
from services.model_task_inference import infer_gentxt_task


MEDIA_TASK_GUARD_CASES: tuple[dict[str, str], ...] = (
    {"id": "block-image-task", "requested_task": "image", "normalized_task": "image"},
    {"id": "block-video-task", "requested_task": "video", "normalized_task": "video"},
    {"id": "block-audio-task", "requested_task": "audio", "normalized_task": "audio"},
    {"id": "block-transcription-task", "requested_task": "transcription", "normalized_task": "transcription"},
    {"id": "block-tts-alias", "requested_task": "tts", "normalized_task": "audio"},
    {"id": "block-stt-alias", "requested_task": "speech-to-text", "normalized_task": "transcription"},
)

TEXT_TASK_ALLOW_CASES: tuple[dict[str, str], ...] = (
    {"id": "allow-fast-task", "requested_task": "fast", "expected_task": "fast"},
    {"id": "allow-classification-task", "requested_task": "classification", "expected_task": "classification"},
    {"id": "allow-review-task", "requested_task": "review", "expected_task": "review"},
    {"id": "allow-agentic-task", "requested_task": "agentic", "expected_task": "agentic"},
    {
        "id": "allow-grounded-research-task",
        "requested_task": "grounded-research",
        "expected_task": "grounded-research",
    },
)

MEDIA_ALIAS_TASKS = ("video", "audio", "transcription")


class ModelOpsGenTxtTaskGuardService:
    """Build metadata-only guard evidence for text generation task routing."""

    def build_gate(self, _payload: Any = None) -> dict[str, Any]:
        media_rows = [self._media_row(case) for case in MEDIA_TASK_GUARD_CASES]
        text_rows = [self._text_row(case) for case in TEXT_TASK_ALLOW_CASES]
        alias_rows = [self._alias_row(task) for task in MEDIA_ALIAS_TASKS]
        checks = self._checks(media_rows, text_rows, alias_rows)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "fail" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-gentxt-routing-guard",
            "title": "ModelOps gentxt routing guard",
            "status": status,
            "method": {
                "type": "metadata-only-gentxt-routing-guard",
                "notes": [
                    "Runs deterministic task inference against sanitized dummy text messages.",
                    "Verifies media and speech task aliases do not route the text endpoint to media model defaults.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "media_task_case_count": len(media_rows),
                "media_task_blocked_count": sum(1 for row in media_rows if row["guard_status"] == "blocked_to_review_text_budget"),
                "text_task_case_count": len(text_rows),
                "text_task_allowed_count": sum(1 for row in text_rows if row["guard_status"] == "allowed_text_budget"),
                "media_alias_count": len(alias_rows),
                "media_alias_default_count": sum(1 for row in alias_rows if bool(row["default_model"])),
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
            },
            "media_task_rows": media_rows,
            "text_task_rows": text_rows,
            "media_alias_rows": alias_rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(checks),
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "returns_credentials": False,
                "returns_api_key": False,
                "returns_headers": False,
                "returns_request_body": False,
                "returns_response_body": False,
                "returns_raw_prompt": False,
                "returns_raw_payload": False,
                "returns_raw_model_output": False,
                "returns_raw_legal_text": False,
                "output_scope": "requested task labels, normalized task labels, booleans, guard status, checks, and validation commands only",
            },
            "claim_boundary": {
                "gentxt_media_route_guard_verified": not blocking,
                "media_endpoint_defaults_changed": False,
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_score_claimed": False,
                "allowed_claim": (
                    "The repository exposes metadata-only evidence that gentxt blocks media/speech task aliases "
                    "from routing the text endpoint to media default models."
                ),
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gentxt_task_guard.py tests/test_model_task_inference.py tests/test_model_ops_readiness.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _media_row(self, case: dict[str, str]) -> dict[str, Any]:
        inference = infer_gentxt_task(
            case["requested_task"],
            [ChatMessage(role="user", content="Generate text only for this local guard check.")],
        )
        expected_signal = f"unsupported_for_gentxt:{case['normalized_task']}"
        blocked = inference.task == "review" and expected_signal in inference.signals
        return {
            "id": case["id"],
            "requested_task": case["requested_task"],
            "normalized_task": case["normalized_task"],
            "resolved_text_task": inference.task,
            "expected_text_task": "review",
            "inference_source": inference.source,
            "expected_signal": expected_signal,
            "signal_present": expected_signal in inference.signals,
            "guard_status": "blocked_to_review_text_budget" if blocked else "guard_failed",
            "model_default_if_media_endpoint": task_default_model(case["normalized_task"]),
            "reason_code": "media_task_rejected_for_gentxt" if blocked else "media_task_guard_missing",
        }

    def _text_row(self, case: dict[str, str]) -> dict[str, Any]:
        inference = infer_gentxt_task(
            case["requested_task"],
            [ChatMessage(role="user", content="Generate text only for this local guard check.")],
        )
        allowed = inference.task == case["expected_task"] and inference.source == "explicit"
        return {
            "id": case["id"],
            "requested_task": case["requested_task"],
            "resolved_text_task": inference.task,
            "expected_text_task": case["expected_task"],
            "inference_source": inference.source,
            "guard_status": "allowed_text_budget" if allowed else "text_task_guard_failed",
            "reason_code": "text_task_allowed_for_gentxt" if allowed else "text_task_allowlist_missing",
        }

    def _alias_row(self, task: str) -> dict[str, Any]:
        default_model = task_default_model(task)
        return {
            "alias": f"auto-{task}",
            "task": task,
            "default_model": default_model,
            "alias_status": "available" if default_model else "missing",
            "gentxt_allowed": False,
            "endpoint_scope": f"/api/v1/aihub/{'transcribe' if task == 'transcription' else 'gen' + task}",
        }

    def _checks(
        self,
        media_rows: list[dict[str, Any]],
        text_rows: list[dict[str, Any]],
        alias_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        media_failures = [row["id"] for row in media_rows if row["guard_status"] != "blocked_to_review_text_budget"]
        text_failures = [row["id"] for row in text_rows if row["guard_status"] != "allowed_text_budget"]
        alias_failures = [row["alias"] for row in alias_rows if row["alias_status"] != "available"]
        return [
            self._check(
                "gentxt-media-route-rejection",
                "fail" if media_failures else "pass",
                "Media and speech task aliases must not route gentxt to media default models.",
                media_failures,
            ),
            self._check(
                "gentxt-text-route-allowlist",
                "fail" if text_failures else "pass",
                "Supported text output tasks should remain explicit task routes for gentxt.",
                text_failures,
            ),
            self._check(
                "media-alias-default-coverage",
                "warn" if alias_failures else "pass",
                "Media endpoint aliases should resolve to explicit endpoint defaults for operator review.",
                alias_failures,
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "The guard uses deterministic local task inference and does not call providers or gateways.",
                [],
            ),
        ]

    def _check(self, check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": status,
            "reason": reason,
            "evidence": evidence,
        }

    def _recommended_actions(self, checks: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        if any(check["id"] == "gentxt-media-route-rejection" and check["status"] == "fail" for check in checks):
            actions.append("Restore the gentxt task allowlist before promoting media endpoint defaults.")
        if any(check["id"] == "gentxt-text-route-allowlist" and check["status"] == "fail" for check in checks):
            actions.append("Restore explicit text task handling before changing cheap-first defaults.")
        if any(check["id"] == "media-alias-default-coverage" and check["status"] == "warn" for check in checks):
            actions.append("Review media endpoint alias defaults before exposing them in operator copy.")
        if not actions:
            actions.append("Keep gentxt media task rejection attached to ModelOps readiness and UI regression evidence.")
        return actions
