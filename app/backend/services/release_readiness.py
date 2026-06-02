from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


ValidationState = Literal["pass", "fail", "not_run", "waived"]


@dataclass(frozen=True)
class ReleaseCheck:
    id: str
    title: str
    category: str
    required: bool
    owner: str
    evidence_paths: tuple[str, ...]
    validation_command: str | None = None
    manual_note: str | None = None

    def to_api(self, validation_state: ValidationState) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_paths"] = list(self.evidence_paths)
        data["validation_state"] = validation_state
        data["blocks_release"] = self.required and validation_state not in {"pass", "waived"}
        return data


class ReleaseReadinessService:
    """Evaluates maintainer release readiness without running shell commands."""

    def evaluate(self, validation_results: dict[str, str] | None = None) -> dict[str, Any]:
        results = validation_results or {}
        checks = [check.to_api(self._state(results.get(check.id))) for check in self._checks()]
        blocking = [check for check in checks if check["blocks_release"]]
        failed = [check for check in checks if check["validation_state"] == "fail"]
        not_run = [check for check in checks if check["validation_state"] == "not_run"]

        if failed:
            status = "blocked"
        elif blocking:
            status = "manual_validation_required"
        else:
            status = "ready_for_release_candidate"

        return {
            "status": status,
            "release_allowed": status == "ready_for_release_candidate",
            "required_check_count": sum(1 for check in checks if check["required"]),
            "passed_or_waived_required_count": sum(
                1 for check in checks if check["required"] and check["validation_state"] in {"pass", "waived"}
            ),
            "blocking_check_ids": [check["id"] for check in blocking],
            "failed_check_ids": [check["id"] for check in failed],
            "not_run_check_ids": [check["id"] for check in not_run],
            "checks": checks,
            "summary": self._summary(status, blocking, failed),
        }

    def default_validation_commands(self) -> list[dict[str, str]]:
        return [
            {
                "check_id": check.id,
                "command": check.validation_command,
            }
            for check in self._checks()
            if check.validation_command
        ]

    def _checks(self) -> list[ReleaseCheck]:
        return [
            ReleaseCheck(
                id="backend-tests",
                title="Backend regression tests",
                category="tests",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/tests/test_model_catalog.py",
                    "app/backend/tests/test_report_quality_gate.py",
                    "app/backend/tests/test_citation_audit.py",
                    "app/backend/tests/test_evidence_audit.py",
                    "app/backend/tests/test_release_decision.py",
                    "app/backend/tests/test_feedback_triage.py",
                ),
                validation_command="python -m pytest tests -q",
            ),
            ReleaseCheck(
                id="frontend-typecheck",
                title="Frontend TypeScript check",
                category="tests",
                required=True,
                owner="frontend",
                evidence_paths=(
                    "app/frontend/src/lib/deepReviewApi.ts",
                    "app/frontend/src/pages/DeepReportPage.tsx",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "app/frontend/src/pages/AdminPage.tsx",
                ),
                validation_command="npm run typecheck",
            ),
            ReleaseCheck(
                id="frontend-build",
                title="Frontend production build",
                category="tests",
                required=True,
                owner="frontend",
                evidence_paths=("app/frontend/package.json", "app/frontend/vite.config.ts"),
                validation_command="npm run build",
            ),
            ReleaseCheck(
                id="secret-scan",
                title="Secret and credential scan",
                category="security",
                required=True,
                owner="security_privacy_owner",
                evidence_paths=("README.md", "app/backend/.env.example"),
                validation_command="rg -n \"APP_AI_KEY=.*s[k]-|\\\\bs[k]-[A-Za-z0-9]{20,}\" . --glob '!app/frontend/node_modules/**'",
                manual_note="The command should return no matches for real keys or passwords.",
            ),
            ReleaseCheck(
                id="deep-review-release-decision",
                title="Deep-review release decision coverage",
                category="legal_quality",
                required=True,
                owner="legal_review_owner",
                evidence_paths=(
                    "app/backend/services/release_decision.py",
                    "app/backend/tests/test_release_decision.py",
                    "docs/DEEP_REVIEW_RELEASE_DECISION.md",
                ),
                validation_command="python -m pytest tests/test_release_decision.py -q",
            ),
            ReleaseCheck(
                id="feedback-triage",
                title="Feedback triage coverage",
                category="maintenance",
                required=True,
                owner="support_ops",
                evidence_paths=(
                    "app/backend/services/feedback_triage.py",
                    "app/backend/tests/test_feedback_triage.py",
                    "docs/FEEDBACK_TRIAGE.md",
                ),
                validation_command="python -m pytest tests/test_feedback_triage.py -q",
            ),
            ReleaseCheck(
                id="oss-maintenance-evidence",
                title="OSS maintenance evidence",
                category="maintenance",
                required=False,
                owner="project_maintainer",
                evidence_paths=(
                    "app/backend/services/maintenance_evidence.py",
                    "app/backend/tests/test_maintenance_evidence.py",
                    "docs/OSS_MAINTENANCE_EVIDENCE.md",
                ),
                validation_command="python -m pytest tests/test_maintenance_evidence.py -q",
            ),
        ]

    def _state(self, value: str | None) -> ValidationState:
        normalized = str(value or "not_run").strip().lower()
        if normalized in {"pass", "passed", "ok", "success"}:
            return "pass"
        if normalized in {"fail", "failed", "error"}:
            return "fail"
        if normalized in {"waive", "waived", "skip", "skipped"}:
            return "waived"
        return "not_run"

    def _summary(self, status: str, blocking: list[dict[str, Any]], failed: list[dict[str, Any]]) -> str:
        if status == "ready_for_release_candidate":
            return "All required release checks passed or were explicitly waived."
        if failed:
            return f"Release is blocked by failed checks: {', '.join(check['id'] for check in failed)}."
        return f"Release requires validation for: {', '.join(check['id'] for check in blocking)}."
