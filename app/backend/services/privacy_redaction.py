from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class PrivacyPattern:
    finding_type: str
    severity: str
    pattern: Pattern[str]
    replacement: str


PATTERNS: tuple[PrivacyPattern, ...] = (
    PrivacyPattern(
        finding_type="chinese_resident_id",
        severity="critical",
        pattern=re.compile(r"(?<!\d)([1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?!\d)"),
        replacement="[身份证号]",
    ),
    PrivacyPattern(
        finding_type="mobile_phone",
        severity="high",
        pattern=re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)"),
        replacement="[手机号]",
    ),
    PrivacyPattern(
        finding_type="bank_card",
        severity="high",
        pattern=re.compile(r"(?<!\d)(?:\d[ -]?){16,19}(?!\d)"),
        replacement="[银行卡号]",
    ),
    PrivacyPattern(
        finding_type="email",
        severity="medium",
        pattern=re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9._%+-])"),
        replacement="[邮箱]",
    ),
)

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


class PrivacyRedactionService:
    """Detect and mask common personal data in legal document text."""

    def scan(self, text: str, *, max_findings_per_type: int = 5) -> dict:
        findings: list[dict] = []
        redacted = text or ""
        counts: dict[str, int] = {}

        for item in PATTERNS:
            matches = list(item.pattern.finditer(text or ""))
            if not matches:
                continue
            counts[item.finding_type] = len(matches)
            for match in matches[:max_findings_per_type]:
                findings.append(
                    {
                        "type": item.finding_type,
                        "severity": item.severity,
                        "start": match.start(),
                        "end": match.end(),
                        "masked_sample": self._mask(match.group(0), item.finding_type),
                    }
                )
            redacted = item.pattern.sub(item.replacement, redacted)

        highest = self._highest_severity(findings)
        risk_level = self._risk_level(highest, sum(counts.values()))
        return {
            "status": "warn" if findings else "pass",
            "risk_level": risk_level,
            "highest_severity": highest,
            "finding_count": sum(counts.values()),
            "counts_by_type": counts,
            "findings": findings,
            "redacted_preview": redacted[:1200],
            "recommended_actions": self._recommended_actions(findings),
        }

    def _mask(self, value: str, finding_type: str) -> str:
        if finding_type == "email":
            name, _, domain = value.partition("@")
            return f"{name[:2]}***@{domain}"
        digits = re.sub(r"\D", "", value)
        if len(digits) <= 6:
            return "*" * len(value)
        return f"{value[:3]}***{value[-4:]}"

    def _highest_severity(self, findings: list[dict]) -> str:
        if not findings:
            return "none"
        return max((item["severity"] for item in findings), key=lambda item: SEVERITY_RANK.get(item, 0))

    def _risk_level(self, highest: str, count: int) -> str:
        if highest == "critical" or count >= 10:
            return "high"
        if highest == "high" or count >= 3:
            return "medium"
        if highest == "medium":
            return "low"
        return "none"

    def _recommended_actions(self, findings: list[dict]) -> list[str]:
        if not findings:
            return ["No common personal data patterns detected."]
        actions = ["Avoid storing prompts or logs with raw personal data."]
        if any(item["severity"] == "critical" for item in findings):
            actions.append("Mask resident ID numbers before sharing screenshots, logs, or benchmark artifacts.")
        if any(item["type"] == "bank_card" for item in findings):
            actions.append("Mask bank card numbers and payment identifiers before review handoff.")
        return actions
