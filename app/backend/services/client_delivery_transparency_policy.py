from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


DeliveryCheckStatus = Literal["pass", "warn", "fail"]
DeliveryGateSeverity = Literal["blocking", "required", "advisory"]


@dataclass(frozen=True)
class DeliveryGateDefinition:
    id: str
    label: str
    severity: DeliveryGateSeverity
    owner: str
    required_before_delivery: bool
    required_evidence: tuple[str, ...]
    product_gap_closed: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_evidence"] = list(self.required_evidence)
        return data


class ClientDeliveryTransparencyPolicyService:
    """Evaluate client-facing delivery transparency gates for legal document release."""

    CONFIRMATION_PASS_VALUES = {
        "accepted",
        "acknowledged",
        "approved",
        "confirmed",
        "pass",
        "passed",
        "reviewed",
        "signed",
    }
    TASK_CLOSED_VALUES = {"done", "closed", "completed", "cancelled", "canceled", "not_required"}
    MATERIAL_CHANGE_KEYS = ("material_change_count", "changed_clause_count", "risk_change_count")

    def build_policy(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        checks = self._checks(payload)
        status = self._overall_status(checks)
        gates = self._delivery_gates(checks)
        recommended_actions = self._recommended_actions(checks, payload)

        return {
            "status": status,
            "policy_id": "client-delivery-transparency-policy-v1",
            "method": {
                "type": "deterministic-local-client-delivery-policy",
                "notes": [
                    "Evaluates metadata only; it does not read uploaded legal documents or call external services.",
                    "Designed to run after lawyer review and before export, share, send, or portal release.",
                    "The output intentionally avoids echoing raw client names, contact details, document text, or credentials.",
                ],
            },
            "summary": {
                "check_count": len(checks),
                "pass_count": self._count_status(checks, "pass"),
                "warning_count": self._count_status(checks, "warn"),
                "fail_count": self._count_status(checks, "fail"),
                "delivery_allowed": status == "pass",
                "client_confirmation_required": True,
                "risk_notice_required": True,
                "version_diff_required": True,
                "delivery_record_required": True,
                "follow_up_task_tracking_required": True,
                "raw_payload_echoed": False,
            },
            "checks": checks,
            "delivery_gates": gates,
            "recommended_actions": recommended_actions,
            "privacy_note": (
                "This policy returns only gate states, issue codes, counts, and field names. "
                "Keep client identity, contact details, document text, file paths, and credentials in protected case storage."
            ),
            "validation_commands": [
                {
                    "id": "client-delivery-transparency-policy-tests",
                    "command": "python -m pytest tests/test_client_delivery_transparency_policy.py -q",
                    "resource_note": "Runs deterministic local tests only; no network, model call, OCR, or large fixture is required.",
                },
                {
                    "id": "client-delivery-transparency-policy-compile",
                    "command": "python -m compileall services/client_delivery_transparency_policy.py",
                    "resource_note": "Checks import and syntax health for the new policy service.",
                },
            ],
        }

    def _gate_definitions(self) -> tuple[DeliveryGateDefinition, ...]:
        return (
            DeliveryGateDefinition(
                id="client-confirmation",
                label="Client confirmation matches the deliverable version",
                severity="blocking",
                owner="case_owner",
                required_before_delivery=True,
                required_evidence=(
                    "client_confirmation.status",
                    "client_confirmation.confirmed_at",
                    "client_confirmation.confirmed_version_id",
                ),
                product_gap_closed="Prevents release of a legal document version the client has not confirmed.",
            ),
            DeliveryGateDefinition(
                id="version-diff",
                label="Version differences are visible and acknowledged",
                severity="blocking",
                owner="responsible_lawyer",
                required_before_delivery=True,
                required_evidence=(
                    "version_diff.summary_available",
                    "version_diff.client_visible",
                    "version_diff.diff_acknowledged",
                ),
                product_gap_closed="Shows what changed between drafts so clients do not rely on stale instructions.",
            ),
            DeliveryGateDefinition(
                id="risk-notice",
                label="Risk notice and scope limits are shown before delivery",
                severity="blocking",
                owner="responsible_lawyer",
                required_before_delivery=True,
                required_evidence=(
                    "risk_notice.present",
                    "risk_notice.client_visible",
                    "risk_notice.acknowledged",
                ),
                product_gap_closed="Makes material legal risk, assumptions, deadlines, and scope limits client-visible.",
            ),
            DeliveryGateDefinition(
                id="delivery-record",
                label="Delivery record is ready for audit",
                severity="blocking",
                owner="legal_operations",
                required_before_delivery=True,
                required_evidence=(
                    "delivery_record.record_id",
                    "delivery_record.delivery_channel",
                    "delivery_record.prepared_at",
                    "delivery_record.package_version_id",
                ),
                product_gap_closed="Creates a traceable release record for the package version, channel, and accountable actor.",
            ),
            DeliveryGateDefinition(
                id="follow-up-tasks",
                label="Post-delivery follow-up tasks are assigned",
                severity="required",
                owner="case_owner",
                required_before_delivery=False,
                required_evidence=(
                    "follow_up_tasks[].task_id",
                    "follow_up_tasks[].owner_role",
                    "follow_up_tasks[].due_at",
                    "follow_up_tasks[].status",
                ),
                product_gap_closed="Keeps delivery from ending without tracked next steps, deadlines, or client requests.",
            ),
        )

    def _checks(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        evaluators = {
            "client-confirmation": self._client_confirmation_check,
            "version-diff": self._version_diff_check,
            "risk-notice": self._risk_notice_check,
            "delivery-record": self._delivery_record_check,
            "follow-up-tasks": self._follow_up_tasks_check,
        }
        checks: list[dict[str, Any]] = []
        for gate in self._gate_definitions():
            result = evaluators[gate.id](payload)
            checks.append(
                {
                    **gate.to_api(),
                    "status": result["status"],
                    "passed": result["status"] == "pass",
                    "issue_codes": result["issue_codes"],
                    "missing_fields": result["missing_fields"],
                    "notes": result["notes"],
                }
            )
        return checks

    def _client_confirmation_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        confirmation = self._section(payload, "client_confirmation")
        artifact_version = self._artifact_version(payload)
        confirmed_version = _text(
            confirmation.get("confirmed_version_id")
            or confirmation.get("version_id")
            or confirmation.get("artifact_version_id")
        )
        issues: list[str] = []
        missing: list[str] = []

        status_value = _text(confirmation.get("status") or confirmation.get("decision")).lower()
        if status_value not in self.CONFIRMATION_PASS_VALUES:
            issues.append("client_confirmation_missing")
            missing.append("client_confirmation.status")

        if not _present(confirmation.get("confirmed_at") or confirmation.get("acknowledged_at")):
            issues.append("client_confirmation_timestamp_missing")
            missing.append("client_confirmation.confirmed_at")

        if not confirmed_version:
            issues.append("confirmed_version_missing")
            missing.append("client_confirmation.confirmed_version_id")
        elif artifact_version and confirmed_version != artifact_version:
            issues.append("confirmed_version_mismatch")

        return self._result(
            status="fail" if issues else "pass",
            issue_codes=issues,
            missing_fields=missing,
            notes=(
                ["Client confirmation is recorded for the current deliverable version."]
                if not issues
                else ["Block delivery until the client confirmation references the exact package version."]
            ),
        )

    def _version_diff_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        version_diff = self._section(payload, "version_diff")
        previous_version = _text(
            version_diff.get("previous_version_id")
            or self._section(payload, "artifact").get("previous_version_id")
            or payload.get("previous_version_id")
        )
        material_change_count = self._material_change_count(version_diff)
        issues: list[str] = []
        warnings: list[str] = []
        missing: list[str] = []

        if not _truthy(version_diff.get("summary_available") or version_diff.get("summary_present")):
            issues.append("version_diff_summary_missing")
            missing.append("version_diff.summary_available")

        if not _truthy(version_diff.get("client_visible")):
            issues.append("version_diff_not_client_visible")
            missing.append("version_diff.client_visible")

        if previous_version or material_change_count > 0:
            if not _truthy(version_diff.get("diff_acknowledged") or version_diff.get("acknowledged")):
                issues.append("version_diff_not_acknowledged")
                missing.append("version_diff.diff_acknowledged")
        elif not version_diff:
            warnings.append("first_delivery_diff_baseline_missing")

        status: DeliveryCheckStatus = "pass"
        if issues:
            status = "fail"
        elif warnings:
            status = "warn"

        return self._result(
            status=status,
            issue_codes=issues + warnings,
            missing_fields=missing,
            notes=(
                ["Version differences are summarized, client-visible, and acknowledged."]
                if status == "pass"
                else ["Show the version-diff summary before delivery, especially when material terms changed."]
            ),
        )

    def _risk_notice_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        risk_notice = self._section(payload, "risk_notice")
        issues: list[str] = []
        missing: list[str] = []

        if not _truthy(risk_notice.get("present") or risk_notice.get("summary_available")):
            issues.append("risk_notice_missing")
            missing.append("risk_notice.present")

        if not _truthy(risk_notice.get("client_visible")):
            issues.append("risk_notice_not_client_visible")
            missing.append("risk_notice.client_visible")

        if not _truthy(risk_notice.get("acknowledged") or risk_notice.get("client_acknowledged")):
            issues.append("risk_notice_not_acknowledged")
            missing.append("risk_notice.acknowledged")

        if not _present(risk_notice.get("risk_level") or risk_notice.get("scope_limits") or risk_notice.get("risk_categories")):
            issues.append("risk_context_missing")
            missing.append("risk_notice.risk_level")

        return self._result(
            status="fail" if issues else "pass",
            issue_codes=issues,
            missing_fields=missing,
            notes=(
                ["Risk notice, scope limits, and client acknowledgement are present."]
                if not issues
                else ["Block delivery until the client can see and acknowledge material risks and limits."]
            ),
        )

    def _delivery_record_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = self._section(payload, "delivery_record")
        required_fields = {
            "delivery_record.record_id": record.get("record_id") or record.get("delivery_id"),
            "delivery_record.delivery_channel": record.get("delivery_channel") or record.get("channel"),
            "delivery_record.prepared_at": record.get("prepared_at") or record.get("delivered_at"),
            "delivery_record.package_version_id": record.get("package_version_id") or record.get("version_id"),
            "delivery_record.accountable_actor": record.get("accountable_actor") or record.get("prepared_by"),
        }
        missing = [field for field, value in required_fields.items() if not _present(value)]
        issues = [f"{field.replace('.', '_')}_missing" for field in missing]

        return self._result(
            status="fail" if missing else "pass",
            issue_codes=issues,
            missing_fields=missing,
            notes=(
                ["Delivery record contains package version, channel, timestamp, and accountable actor metadata."]
                if not missing
                else ["Create the audit record envelope before any external delivery action."]
            ),
        )

    def _follow_up_tasks_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        tasks = self._tasks(payload)
        follow_up_required = _truthy(payload.get("follow_up_required") or self._section(payload, "delivery_record").get("follow_up_required"))
        if not tasks:
            status: DeliveryCheckStatus = "fail" if follow_up_required else "warn"
            return self._result(
                status=status,
                issue_codes=["follow_up_tasks_missing" if follow_up_required else "follow_up_tasks_not_recorded"],
                missing_fields=["follow_up_tasks"],
                notes=["Record whether post-delivery tasks exist, even when no next action is required."],
            )

        missing_fields: list[str] = []
        for index, task in enumerate(tasks, start=1):
            prefix = f"follow_up_tasks[{index}]"
            for field in ("task_id", "owner_role", "due_at", "status"):
                if not _present(task.get(field)):
                    missing_fields.append(f"{prefix}.{field}")

        open_tasks = [
            task
            for task in tasks
            if _text(task.get("status")).lower() not in self.TASK_CLOSED_VALUES
        ]
        if missing_fields:
            return self._result(
                status="warn",
                issue_codes=["follow_up_task_metadata_incomplete"],
                missing_fields=missing_fields,
                notes=["Follow-up tasks exist but need owner, due date, and status metadata for reliable tracking."],
            )

        return self._result(
            status="pass",
            issue_codes=[],
            missing_fields=[],
            notes=[
                f"{len(tasks)} follow-up task record(s) tracked; {len(open_tasks)} remain open for case team visibility."
            ],
        )

    def _delivery_gates(self, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        gates: list[dict[str, Any]] = []
        for check in checks:
            gates.append(
                {
                    "id": f"gate-{check['id']}",
                    "check_id": check["id"],
                    "label": check["label"],
                    "status": check["status"],
                    "release_effect": self._release_effect(check),
                    "required_before_delivery": check["required_before_delivery"],
                    "owner": check["owner"],
                }
            )
        return gates

    def _release_effect(self, check: dict[str, Any]) -> str:
        if check["status"] == "pass":
            return "allow"
        if check["required_before_delivery"] or check["severity"] == "blocking":
            return "block"
        return "warn"

    def _recommended_actions(self, checks: list[dict[str, Any]], payload: dict[str, Any]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for check in checks:
            if check["status"] == "pass":
                continue
            actions.append(
                {
                    "id": f"resolve-{check['id']}",
                    "priority": "high" if check["status"] == "fail" else "medium",
                    "owner": check["owner"],
                    "action": self._action_for_check(check["id"]),
                    "missing_fields": check["missing_fields"],
                    "issue_codes": check["issue_codes"],
                }
            )

        if not actions:
            actions.append(
                {
                    "id": "release-with-transparent-audit",
                    "priority": "normal",
                    "owner": "case_owner",
                    "action": "Proceed only through the controlled delivery flow and persist the delivery record ID.",
                    "missing_fields": [],
                    "issue_codes": [],
                }
            )

        if not payload:
            actions.append(
                {
                    "id": "connect-real-delivery-payload",
                    "priority": "medium",
                    "owner": "product",
                    "action": "Wire this policy to the real document package, client acknowledgement, version diff, risk notice, and task records.",
                    "missing_fields": ["payload"],
                    "issue_codes": ["policy_template_payload_missing"],
                }
            )

        return actions

    def _action_for_check(self, check_id: str) -> str:
        actions = {
            "client-confirmation": "Collect client confirmation for the exact document version before release.",
            "version-diff": "Generate a client-visible version difference summary and require acknowledgement for material changes.",
            "risk-notice": "Show the risk notice, scope limits, assumptions, and deadline cautions in plain language.",
            "delivery-record": "Create the delivery record envelope with package version, channel, timestamp, and accountable actor.",
            "follow-up-tasks": "Assign follow-up tasks or explicitly record that no post-delivery action is required.",
        }
        return actions[check_id]

    def _overall_status(self, checks: list[dict[str, Any]]) -> DeliveryCheckStatus:
        statuses = {check["status"] for check in checks}
        if "fail" in statuses:
            return "fail"
        if "warn" in statuses:
            return "warn"
        return "pass"

    def _count_status(self, checks: list[dict[str, Any]], status: DeliveryCheckStatus) -> int:
        return sum(1 for check in checks if check["status"] == status)

    def _section(self, payload: dict[str, Any], name: str) -> dict[str, Any]:
        section = payload.get(name)
        return section if isinstance(section, dict) else {}

    def _tasks(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = payload.get("follow_up_tasks")
        if not isinstance(tasks, list):
            return []
        return [task for task in tasks if isinstance(task, dict)]

    def _artifact_version(self, payload: dict[str, Any]) -> str:
        artifact = self._section(payload, "artifact")
        return _text(
            artifact.get("current_version_id")
            or artifact.get("version_id")
            or payload.get("current_version_id")
            or payload.get("package_version_id")
        )

    def _material_change_count(self, version_diff: dict[str, Any]) -> int:
        for key in self.MATERIAL_CHANGE_KEYS:
            value = version_diff.get(key)
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, (int, float)):
                return max(int(value), 0)
            if isinstance(value, str) and value.strip().isdigit():
                return int(value.strip())
        changes = version_diff.get("changes")
        if isinstance(changes, list):
            return len(changes)
        return 0

    def _result(
        self,
        *,
        status: DeliveryCheckStatus,
        issue_codes: list[str],
        missing_fields: list[str],
        notes: list[str],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "issue_codes": issue_codes,
            "missing_fields": sorted(set(missing_fields)),
            "notes": notes,
        }


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "ok", "confirmed", "acknowledged"}
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()
