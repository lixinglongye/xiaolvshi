from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from typing import Any

from services.legal_document_benchmark_route_plan_execution_review_packet import (
    LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService,
)


CLAIM_GATE_ID = "legal-document-benchmark-route-plan-execution-claim-gate"

CLAIM_PATTERNS = {
    "metadata_only_execution_evidence": re.compile(
        r"\b(metadata-only|sanitized|repository-backed|local)\b.{0,80}"
        r"\b(route-plan|benchmark|execution|review packet|release evidence)\b",
        re.I,
    ),
    "public_benchmark_score": re.compile(
        r"\b(legalbench|lexglue|coliee|leaderboard|public benchmark score|benchmark score|ranked)\b",
        re.I,
    ),
    "live_provider_execution": re.compile(
        r"\b(live newapi|live gemini|called gemini|called newapi|provider run|gateway run|model run)\b",
        re.I,
    ),
    "approval_recorded": re.compile(
        r"\b(maintainer approved|maintainers approved|release approved|approval recorded|signed off|signoff recorded)\b",
        re.I,
    ),
    "default_or_traffic_change": re.compile(
        r"\b(default model changed|traffic shifted|rolled out|production default|default promotion)\b",
        re.I,
    ),
    "production_quality": re.compile(
        r"\b(production accuracy|lawyer-grade|guaranteed legal accuracy|real client documents?)\b",
        re.I,
    ),
}
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.I,
)


class LegalDocumentBenchmarkRoutePlanExecutionClaimGateService:
    """Validate benchmark route-plan execution claims against the review packet."""

    def __init__(
        self,
        review_packet_service: LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService | None = None,
    ) -> None:
        self.review_packet_service = review_packet_service or LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService()

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        review_packet = self.review_packet_service.build_packet(
            data.get("execution_review_packet") if isinstance(data.get("execution_review_packet"), dict) else data
        )
        claims = self._claims(data.get("claims"))
        claim_checks = [self._check_claim(claim, review_packet) for claim in claims]
        blocked = [claim for claim in claim_checks if claim["status"] == "blocked"]
        review = [claim for claim in claim_checks if claim["status"] == "review_required"]
        status = "blocked" if blocked else ("review_required" if review else "ready")

        return {
            "id": CLAIM_GATE_ID,
            "title": "Legal document benchmark route-plan execution claim gate",
            "status": status,
            "policy_version": "legal-document-route-plan-execution-claim-gate-v1",
            "summary": {
                "claim_count": len(claim_checks),
                "ready_claim_count": sum(1 for claim in claim_checks if claim["status"] == "ready"),
                "review_required_claim_count": len(review),
                "blocked_claim_count": len(blocked),
                "metadata_only_claim_count": sum(
                    1 for claim in claim_checks if "metadata_only_execution_evidence" in claim["detected_claim_types"]
                ),
                "review_packet_status": review_packet["status"],
                "ready_for_release_packet": review_packet["summary"]["ready_for_release_packet"],
                "release_action": review_packet["summary"]["release_action"],
                "raw_claim_text_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "benchmark_executed": False,
                "release_record_written": False,
                "maintainer_approval_recorded": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_checks": claim_checks,
            "blocking_claim_hashes": [claim["claim_hash"] for claim in blocked],
            "review_claim_hashes": [claim["claim_hash"] for claim in review],
            "source_summary": {
                "execution_review_packet": {
                    "id": review_packet["id"],
                    "status": review_packet["status"],
                    "ready_for_release_packet": review_packet["summary"]["ready_for_release_packet"],
                    "release_action": review_packet["summary"]["release_action"],
                    "blocking_check_ids": list(review_packet.get("blocking_check_ids", [])),
                    "warning_check_ids": list(review_packet.get("warning_check_ids", [])),
                },
            },
            "allowed_claim_template": (
                "Repository evidence includes a metadata-only legal-document route-plan execution review packet "
                "for sanitized manual observation metadata after readiness, archive, handoff, cheap-first, and "
                "low-resource checks."
            ),
            "forbidden_claim_types": [
                "public_benchmark_score",
                "live_provider_execution",
                "approval_recorded",
                "default_or_traffic_change",
                "production_quality",
            ],
            "privacy_boundary": {
                "metadata_only": True,
                "raw_claim_text_included": False,
                "claim_hashes_only": True,
                "returns_public_benchmark_text": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_request_bodies": False,
                "returns_response_bodies": False,
                "returns_headers": False,
                "returns_gateway_responses": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "writes_release_record": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "live_gateway_execution_claimed": False,
                "benchmark_executed_by_service": False,
                "maintainer_approval_claimed": False,
                "release_approval_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "allowed_claim_requires_ready_packet": True,
            },
            "recommended_actions": self._recommended_actions(status, review_packet),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_claim_gate.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_review_packet.py -q",
            ],
        }

    def _claims(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item or "") for item in value[:40]]
        if isinstance(value, dict):
            return [str(item or "") for _, item in sorted(value.items())[:40]]
        if isinstance(value, str):
            return [value]
        return [
            "Repository evidence includes a metadata-only legal-document route-plan execution review packet.",
            "The project achieved a public LegalBench benchmark score.",
            "Maintainers approved the benchmark release evidence.",
        ]

    def _check_claim(self, claim: str, review_packet: dict[str, Any]) -> dict[str, Any]:
        detected_types = [claim_type for claim_type, pattern in CLAIM_PATTERNS.items() if pattern.search(claim)]
        reason_codes: list[str] = []
        packet_ready = review_packet["status"] == "ready" and review_packet["summary"]["ready_for_release_packet"] is True
        forbidden_types = {
            "public_benchmark_score",
            "live_provider_execution",
            "approval_recorded",
            "default_or_traffic_change",
            "production_quality",
        }
        forbidden_hits = sorted(set(detected_types) & forbidden_types)
        if not claim.strip():
            reason_codes.append("empty_claim")
        if forbidden_hits:
            reason_codes.extend(f"forbidden_{claim_type}" for claim_type in forbidden_hits)
        if SENSITIVE_VALUE_PATTERN.search(claim[:4096]):
            reason_codes.append("sensitive_material_dropped")
        if "metadata_only_execution_evidence" in detected_types and not packet_ready:
            reason_codes.append("review_packet_not_ready")
        if detected_types == [] and claim.strip():
            reason_codes.append("benchmark_claim_scope_unclear")

        blocking_codes = {
            "empty_claim",
            "forbidden_public_benchmark_score",
            "forbidden_live_provider_execution",
            "forbidden_approval_recorded",
            "forbidden_default_or_traffic_change",
            "forbidden_production_quality",
        }
        status = (
            "blocked"
            if any(code in blocking_codes for code in reason_codes)
            else "review_required"
            if reason_codes
            else "ready"
        )
        return {
            "claim_hash": hashlib.sha256(claim.encode("utf-8")).hexdigest()[:24],
            "status": status,
            "detected_claim_types": sorted(set(detected_types)),
            "reason_codes": sorted(dict.fromkeys(reason_codes)),
            "allowed": status == "ready",
            "release_action": self._claim_release_action(status, reason_codes),
        }

    def _claim_release_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "allow_metadata_only_claim"
        if "review_packet_not_ready" in reason_codes:
            return "hold_until_review_packet_ready"
        if "benchmark_claim_scope_unclear" in reason_codes or "sensitive_material_dropped" in reason_codes:
            return "rewrite_and_review_claim"
        return "block_claim_before_public_release"

    def _recommended_actions(self, status: str, review_packet: dict[str, Any]) -> list[str]:
        if status == "ready":
            return [
                "Use only the metadata-only review-packet claim template for benchmark execution evidence.",
                "Keep public benchmark scores, provider execution, approvals, default changes, and traffic shifts out of public wording.",
            ]
        if review_packet["status"] != "ready":
            return [
                "Do not publish even metadata-only benchmark execution claims until the review packet is ready.",
                "Collect sanitized observations and clear review-packet blockers first.",
            ]
        if status == "blocked":
            return [
                "Remove public score, live provider execution, approval, default-change, traffic-shift, production-quality, or sensitive-material claims.",
                "Replace them with the allowed metadata-only repository evidence wording.",
            ]
        return [
            "Rewrite unclear benchmark execution wording to the metadata-only template and review before release.",
            "Keep raw claim text, credentials, emails, and legal content out of public evidence.",
        ]
