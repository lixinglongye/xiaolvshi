from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from typing import Any


FORBIDDEN_PATTERNS = {
    "external_adoption_claim": re.compile(r"\b(thousands of users|widely adopted|external adoption|ecosystem leading)\b", re.I),
    "public_benchmark_score_claim": re.compile(r"\b(legalbench score|lexglue score|coliee rank|leaderboard)\b", re.I),
    "payment_provider_settlement_claim": re.compile(r"\b(stripe settled|payment provider verified|webhook verified|invoice collected)\b", re.I),
    "production_accuracy_claim": re.compile(r"\b(production accuracy|guaranteed legal accuracy|lawyer-grade accuracy)\b", re.I),
    "third_party_pr_claim": re.compile(r"\b(third-party pr|community pull requests|issue triage volume)\b", re.I),
}

PRIVACY_BOUNDARY = {
    "raw_claim_text_included": False,
    "pii_included": False,
    "secret_included": False,
    "output_scope": "claim hashes, category counts, status, and reason codes only",
}


class ReleaseClaimComplianceService:
    """Check public release/support-application claims against evidence guardrails."""

    def evaluate(self, claims: Iterable[Any] | None = None) -> dict[str, Any]:
        checks = [self._check_claim(str(claim or "")) for claim in claims or []]
        blocked = [item for item in checks if item["status"] == "blocked"]
        review = [item for item in checks if item["status"] == "review_required"]
        status = "blocked" if blocked else "review_required" if review else "ready"
        return {
            "status": status,
            "policy_version": "release-claim-compliance-v1",
            "claim_checks": checks,
            "summary": {
                "claim_count": len(checks),
                "blocked_count": len(blocked),
                "review_required_count": len(review),
                "ready_count": sum(1 for item in checks if item["status"] == "ready"),
            },
            "recommended_actions": self._actions(status),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _check_claim(self, claim: str) -> dict[str, Any]:
        reason_codes = [code for code, pattern in FORBIDDEN_PATTERNS.items() if pattern.search(claim)]
        if "sk-" in claim.lower() or "@" in claim:
            reason_codes.append("sensitive_material_dropped")
        if not claim.strip():
            reason_codes.append("empty_claim")
        status = "blocked" if any(code != "sensitive_material_dropped" for code in reason_codes) else "review_required" if reason_codes else "ready"
        return {
            "claim_hash": hashlib.sha256(claim.encode("utf-8")).hexdigest()[:24],
            "status": status,
            "reason_codes": sorted(dict.fromkeys(reason_codes)),
        }

    def _actions(self, status: str) -> list[str]:
        if status == "ready":
            return ["Claims are limited to repository-backed maintenance evidence."]
        if status == "blocked":
            return [
                "Remove unsupported adoption, benchmark, payment, production-accuracy, or third-party contribution claims.",
                "Replace public claims with repository-backed code, test, and documentation evidence.",
            ]
        return [
            "Review sensitive material before using the claim in support applications.",
            "Keep secrets, emails, and raw client facts out of public release evidence.",
        ]
