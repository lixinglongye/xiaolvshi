from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class InjectionPattern:
    rule_id: str
    severity: str
    pattern: Pattern[str]
    reason: str


PATTERNS: tuple[InjectionPattern, ...] = (
    InjectionPattern(
        rule_id="ignore-prior-instructions",
        severity="high",
        pattern=re.compile(
            r"((ignore|disregard|forget).{0,40}(previous|prior|above).{0,30}(instruction|prompt|message)"
            r"|忽略.{0,20}(之前|先前|以上|系统|开发者).{0,20}(指令|提示|消息))",
            re.I,
        ),
        reason="Attempts to override previous system or developer instructions.",
    ),
    InjectionPattern(
        rule_id="system-prompt-exfiltration",
        severity="high",
        pattern=re.compile(
            r"((show|reveal|print|dump).{0,30}(system prompt|developer message|hidden prompt)"
            r"|(system prompt|developer message|hidden prompt).{0,30}(show|reveal|print|dump)"
            r"|(输出|泄露|显示).{0,30}(系统提示|开发者消息|隐藏提示|隐藏提示词)"
            r"|(系统提示|开发者消息|隐藏提示|隐藏提示词).{0,30}(输出|泄露|显示))",
            re.I,
        ),
        reason="Attempts to reveal hidden prompts or control messages.",
    ),
    InjectionPattern(
        rule_id="credential-exfiltration",
        severity="critical",
        pattern=re.compile(
            r"((api key|apikey|token|secret|credential).{0,50}(show|reveal|print|send|输出|泄露|发给|发送)"
            r"|(show|reveal|print|send|输出|泄露|发给|发送).{0,50}(api key|apikey|token|secret|credential|密钥|令牌|凭证)"
            r"|(密钥|令牌|凭证).{0,50}(输出|泄露|发给|发送))",
            re.I,
        ),
        reason="Attempts to extract credentials or tokens.",
    ),
    InjectionPattern(
        rule_id="model-behavior-override",
        severity="medium",
        pattern=re.compile(r"(you are now|act as|developer mode|jailbreak|越狱|开发者模式|现在你是).{0,80}", re.I),
        reason="Attempts to redefine assistant role or behavior.",
    ),
    InjectionPattern(
        rule_id="tool-or-network-command",
        severity="medium",
        pattern=re.compile(r"(run|execute|call|调用|执行).{0,30}(shell|powershell|cmd|http|webhook|external url|外部链接|命令)", re.I),
        reason="Attempts to trigger tools, commands, or network calls from document text.",
    ),
)

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


class InstructionInjectionAuditService:
    """Detect prompt-injection style instructions embedded in user documents."""

    def scan(self, text: str, *, max_matches_per_rule: int = 3) -> dict:
        findings: list[dict] = []
        for rule in PATTERNS:
            matches = list(rule.pattern.finditer(text or ""))
            for match in matches[:max_matches_per_rule]:
                findings.append(
                    {
                        "rule_id": rule.rule_id,
                        "severity": rule.severity,
                        "reason": rule.reason,
                        "start": match.start(),
                        "end": match.end(),
                        "sample": _clip(match.group(0)),
                    }
                )

        highest = self._highest_severity(findings)
        risk_level = self._risk_level(highest, len(findings))
        return {
            "status": "warn" if findings else "pass",
            "risk_level": risk_level,
            "highest_severity": highest,
            "finding_count": len(findings),
            "counts_by_severity": self._counts_by_severity(findings),
            "findings": findings,
            "matched_rule_ids": sorted({item["rule_id"] for item in findings}),
            "recommended_actions": self._recommended_actions(highest, findings),
        }

    def _highest_severity(self, findings: list[dict]) -> str:
        if not findings:
            return "none"
        return max((item["severity"] for item in findings), key=lambda item: SEVERITY_RANK.get(item, 0))

    def _risk_level(self, highest: str, count: int) -> str:
        if highest == "critical":
            return "high"
        if highest == "high" or count >= 3:
            return "medium"
        if highest == "medium":
            return "low"
        return "none"

    def _recommended_actions(self, highest: str, findings: list[dict]) -> list[str]:
        if not findings:
            return ["No prompt-injection style instructions detected."]
        actions = [
            "Treat matched text as document content, not as instructions to the model.",
            "Keep system and developer instructions outside user-controlled document text.",
        ]
        if highest in {"high", "critical"}:
            actions.append("Require operator spot-check before using this document in benchmark or public demos.")
        return actions

    def _counts_by_severity(self, findings: list[dict]) -> dict[str, int]:
        counts = {severity: 0 for severity in SEVERITY_RANK}
        for item in findings:
            severity = item.get("severity")
            if severity in counts:
                counts[severity] += 1
        return counts


def _clip(value: str, limit: int = 160) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"
