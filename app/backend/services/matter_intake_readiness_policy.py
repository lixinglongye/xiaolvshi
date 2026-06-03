from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_RANK = {"pass": 0, "warn": 1, "fail": 2}


@dataclass(frozen=True)
class IntakeReadinessCheck:
    id: str
    title: str
    category: str
    evidence_needed: tuple[str, ...]
    pass_message: str
    fail_action: str
    warn_action: str | None = None

    def to_api(
        self,
        *,
        status: str,
        missing_fields: list[str] | None = None,
        observations: list[str] | None = None,
    ) -> dict[str, Any]:
        action = self.fail_action if status == "fail" else self.warn_action
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "status": status,
            "blocks_matter_creation": status == "fail",
            "allows_restricted_creation": status == "warn",
            "missing_fields": missing_fields or [],
            "observations": observations or [self.pass_message],
            "evidence_needed": list(self.evidence_needed),
            "recommended_action": action,
        }


class MatterIntakeReadinessPolicyService:
    """Evaluate matter intake readiness before a legal matter is created."""

    def evaluate(self, intake: dict[str, Any] | None = None) -> dict[str, Any]:
        intake = intake or {}
        conflict_result = self._normalized_any(
            intake,
            (
                "conflict_result",
                "conflict.result",
                "conflict_screen.result",
                "conflicts.result",
            ),
        )
        lawyer_review_required = self._lawyer_review_required(intake, conflict_result)
        checks = [
            self._basic_information_check(intake),
            self._facts_and_deadlines_check(intake),
            self._conflict_check(intake, conflict_result),
            self._engagement_materials_check(intake),
            self._lawyer_review_check(intake, conflict_result, lawyer_review_required),
        ]
        status = self._overall_status(checks)

        return {
            "status": status,
            "summary": {
                "check_count": len(checks),
                "passed_check_count": sum(1 for item in checks if item["status"] == "pass"),
                "warning_check_count": sum(1 for item in checks if item["status"] == "warn"),
                "failed_check_count": sum(1 for item in checks if item["status"] == "fail"),
                "ready_for_matter_creation": status == "pass",
                "restricted_creation_allowed": status == "warn",
                "conflict_review_required": conflict_result
                in {"possible", "potential", "requires_waiver", "waiver_required"},
                "lawyer_review_required": lawyer_review_required,
                "privacy_minimized": True,
            },
            "checks": checks,
            "recommended_actions": self._recommended_actions(checks, status),
            "privacy_note": (
                "The readiness policy is metadata-only and evaluates presence flags, counts, "
                "and controlled review states only. "
                "It does not return party names, matter narratives, document text, contact details, "
                "login credentials, API keys, or attachment contents."
            ),
            "validation_commands": [
                "python -m pytest tests/test_matter_intake_readiness_policy.py -q",
            ],
        }

    def build_policy(self, intake: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.evaluate(intake)

    def _basic_information_check(self, intake: dict[str, Any]) -> dict[str, Any]:
        check = IntakeReadinessCheck(
            id="basic-matter-profile",
            title="Basic matter profile",
            category="required_information",
            evidence_needed=(
                "client identity reference",
                "opposing party identity reference",
                "matter type",
                "jurisdiction or venue",
                "requested objective",
            ),
            pass_message="Core matter profile fields are present.",
            fail_action="Collect missing client, opposing party, matter type, jurisdiction, and objective metadata.",
        )
        missing = self._missing_logical_fields(
            intake,
            {
                "client_identity": ("client_id", "client_name", "client", "parties.client"),
                "opposing_party_identity": (
                    "opposing_party",
                    "opposing_parties",
                    "parties.opposing_party",
                    "parties.opposing_parties",
                ),
                "matter_type": ("matter_type", "case_type"),
                "jurisdiction": ("jurisdiction", "venue_or_court"),
                "requested_objective": ("claim_objective", "requested_remedy", "desired_outcome"),
            },
        )
        if missing:
            return check.to_api(
                status="fail",
                missing_fields=missing,
                observations=["Matter creation needs a complete profile before an internal file is opened."],
            )
        return check.to_api(status="pass")

    def _facts_and_deadlines_check(self, intake: dict[str, Any]) -> dict[str, Any]:
        check = IntakeReadinessCheck(
            id="facts-and-deadlines",
            title="Facts, dates, and limitation risk",
            category="required_information",
            evidence_needed=(
                "fact summary",
                "key date list",
                "deadline assessment",
                "evidence inventory",
            ),
            pass_message="Fact, deadline, and evidence presence checks are complete.",
            fail_action="Add fact summary, key dates, deadline assessment, and evidence inventory metadata.",
            warn_action="Assign an owner for the urgent deadline before allowing drafting or delivery.",
        )
        missing = self._missing_logical_fields(
            intake,
            {
                "facts_summary": ("facts_summary", "fact_summary", "case_summary"),
                "key_dates": ("key_dates", "timeline.key_dates"),
                "deadline_assessment": (
                    "deadline_assessment",
                    "deadline_risks",
                    "timeline.deadline_assessment",
                ),
                "evidence_inventory": ("evidence_items", "evidence_inventory", "materials.evidence_items"),
            },
        )
        if missing:
            return check.to_api(
                status="fail",
                missing_fields=missing,
                observations=["The intake lacks enough metadata to evaluate time limits and source support."],
            )
        if self._bool_any(intake, ("urgent_deadline", "timeline.urgent_deadline")) and not self._has_any(
            intake,
            ("deadline_owner_id", "timeline.deadline_owner_id", "assigned_lawyer_id"),
        ):
            return check.to_api(
                status="warn",
                observations=["An urgent deadline is flagged but no deadline owner metadata is present."],
            )
        return check.to_api(status="pass")

    def _conflict_check(self, intake: dict[str, Any], conflict_result: str) -> dict[str, Any]:
        check = IntakeReadinessCheck(
            id="conflict-screening",
            title="Conflict screening",
            category="conflict_check",
            evidence_needed=(
                "conflict search completion flag",
                "controlled conflict result",
                "searched party count",
                "waiver or escalation reference when relevant",
            ),
            pass_message="Conflict search is complete and marked clear.",
            fail_action="Complete conflict screening or block creation until the conflict is resolved.",
            warn_action="Create only as restricted intake and keep lawyer conflict review attached.",
        )
        missing = self._missing_logical_fields(
            intake,
            {
                "conflict_search_completed": (
                    "conflict_search_completed",
                    "conflict.search_completed",
                    "conflict_screen.search_completed",
                ),
                "conflict_result": (
                    "conflict_result",
                    "conflict.result",
                    "conflict_screen.result",
                    "conflicts.result",
                ),
            },
        )
        if missing:
            return check.to_api(
                status="fail",
                missing_fields=missing,
                observations=["No complete conflict decision metadata is available."],
            )
        if not self._bool_any(
            intake,
            ("conflict_search_completed", "conflict.search_completed", "conflict_screen.search_completed"),
        ):
            return check.to_api(status="fail", observations=["Conflict search is not marked complete."])
        if conflict_result in {"blocked", "confirmed", "adverse", "conflict"}:
            return check.to_api(status="fail", observations=["Conflict result blocks matter creation."])
        if conflict_result in {"possible", "potential", "requires_waiver", "waiver_required"}:
            has_waiver = self._has_any(
                intake,
                ("conflict_waiver_id", "conflict.waiver_id", "conflict_screen.waiver_id"),
            )
            has_reviewer = self._has_any(
                intake,
                ("conflict_reviewer_id", "lawyer_review.reviewer_id", "assigned_lawyer_id"),
            )
            if has_waiver and has_reviewer:
                return check.to_api(
                    status="warn",
                    observations=["Potential conflict has waiver metadata and a lawyer reviewer."],
                )
            return check.to_api(
                status="fail",
                observations=["Potential conflict lacks waiver or lawyer reviewer metadata."],
            )
        if conflict_result in {"clear", "none", "no_conflict", "pass"}:
            return check.to_api(status="pass")
        return check.to_api(
            status="warn",
            observations=["Conflict result is present but not in the approved controlled vocabulary."],
        )

    def _engagement_materials_check(self, intake: dict[str, Any]) -> dict[str, Any]:
        check = IntakeReadinessCheck(
            id="engagement-materials",
            title="Engagement and authority materials",
            category="entrustment_materials",
            evidence_needed=(
                "identity material reference",
                "authorization material reference",
                "engagement scope acknowledgement",
            ),
            pass_message="Authority and engagement materials are present.",
            fail_action="Collect identity, authorization, and engagement-scope metadata before matter creation.",
        )
        missing = self._missing_logical_fields(
            intake,
            {
                "identity_materials": ("identity_materials", "materials.identity", "materials.identity_items"),
                "authorization_materials": (
                    "authorization_materials",
                    "materials.authorization",
                    "materials.authorization_items",
                ),
                "engagement_scope_acknowledged": (
                    "engagement_scope_acknowledged",
                    "engagement.scope_acknowledged",
                    "engagement_scope",
                ),
            },
        )
        if missing:
            return check.to_api(
                status="fail",
                missing_fields=missing,
                observations=["Entrustment materials are incomplete."],
            )
        return check.to_api(status="pass")

    def _lawyer_review_check(
        self,
        intake: dict[str, Any],
        conflict_result: str,
        lawyer_review_required: bool,
    ) -> dict[str, Any]:
        check = IntakeReadinessCheck(
            id="lawyer-review-gate",
            title="Lawyer review gate",
            category="lawyer_review",
            evidence_needed=(
                "review-required flag",
                "reviewer assignment",
                "review status for high-risk or conflict matters",
            ),
            pass_message="Lawyer review gate is satisfied for matter creation.",
            fail_action="Assign a qualified lawyer reviewer before opening this matter.",
            warn_action="Open only as restricted intake until lawyer review is approved.",
        )
        if not lawyer_review_required:
            return check.to_api(status="pass", observations=["No review trigger requires a lawyer gate."])

        reviewer_present = self._has_any(
            intake,
            ("lawyer_review.reviewer_id", "assigned_lawyer_id", "reviewer_id", "conflict_reviewer_id"),
        )
        if not reviewer_present:
            return check.to_api(
                status="fail",
                missing_fields=["lawyer_reviewer"],
                observations=["A lawyer review trigger is present without reviewer assignment metadata."],
            )

        review_status = self._normalized_any(
            intake,
            ("lawyer_review.status", "review_status", "lawyer_review_status"),
        )
        if review_status in {"approved", "complete", "passed", "pass"}:
            return check.to_api(status="pass")
        if conflict_result in {"blocked", "confirmed", "adverse", "conflict"}:
            return check.to_api(status="fail", observations=["Blocking conflict still requires lawyer resolution."])
        return check.to_api(
            status="warn",
            observations=["Reviewer is assigned but final review approval is not present."],
        )

    def _lawyer_review_required(self, intake: dict[str, Any], conflict_result: str) -> bool:
        risk_level = self._normalized_any(intake, ("risk_level", "risk.level"))
        return any(
            (
                self._bool_any(intake, ("lawyer_review_required", "lawyer_review.required")),
                risk_level in {"high", "critical", "major"},
                conflict_result
                in {
                    "possible",
                    "potential",
                    "requires_waiver",
                    "waiver_required",
                    "blocked",
                    "confirmed",
                    "adverse",
                    "conflict",
                },
                self._bool_any(intake, ("urgent_deadline", "timeline.urgent_deadline")),
                self._bool_any(intake, ("client_delivery_requested", "delivery.client_delivery_requested")),
            )
        )

    def _recommended_actions(self, checks: list[dict[str, Any]], status: str) -> list[str]:
        actions = [
            item["recommended_action"]
            for item in checks
            if item["status"] in {"fail", "warn"} and item.get("recommended_action")
        ]
        if actions:
            return list(dict.fromkeys(actions))
        if status == "pass":
            return [
                "Allow matter creation and archive this readiness result with the intake audit metadata.",
                "Continue to lawyer review, drafting, or client delivery gates according to downstream policy.",
            ]
        return ["Keep the matter in intake state until blocking checks are resolved."]

    def _overall_status(self, checks: list[dict[str, Any]]) -> str:
        return max((item["status"] for item in checks), key=lambda status: STATUS_RANK[status])

    def _missing_logical_fields(
        self,
        intake: dict[str, Any],
        field_paths: dict[str, tuple[str, ...]],
    ) -> list[str]:
        return [
            logical_name
            for logical_name, paths in field_paths.items()
            if not self._has_any(intake, paths)
        ]

    def _has_any(self, intake: dict[str, Any], paths: tuple[str, ...]) -> bool:
        return any(self._is_present(self._lookup_path(intake, path)) for path in paths)

    def _bool_any(self, intake: dict[str, Any], paths: tuple[str, ...]) -> bool:
        return any(self._as_bool(self._lookup_path(intake, path)) for path in paths)

    def _normalized_any(self, intake: dict[str, Any], paths: tuple[str, ...]) -> str:
        for path in paths:
            value = self._lookup_path(intake, path)
            if self._is_present(value):
                return str(value).strip().lower()
        return ""

    def _lookup_path(self, data: dict[str, Any], path: str) -> Any:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _is_present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return True

    def _as_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "required", "required_review"}
        return bool(value)
