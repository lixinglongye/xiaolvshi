from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable


PLAN_ID = "case-workbench-persistence-plan-v1"
STATE_EVENT_TYPE = "case_workbench_state_event"

SUPPORTED_SECTIONS = (
    "parties",
    "facts",
    "tasks",
    "deadlines",
    "evidence_graph",
)

SUPPORTED_OPERATIONS = (
    "upsert_snapshot",
    "append_delta",
    "delete_item",
    "compact_snapshot",
    "restore_snapshot",
)

SUPPORTED_PAYLOAD_KINDS = (
    "metadata_snapshot",
    "metadata_delta",
    "aggregate_summary",
)

REQUIRED_EVENT_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "case_ref_hash",
    "section",
    "operation",
    "state_version",
    "payload_kind",
)

RECOMMENDED_EVENT_FIELDS = (
    "idempotency_key",
    "actor_ref_hash",
    "source_component",
    "schema_version",
    "previous_state_version",
    "changed_item_refs",
    "changed_field_names",
    "policy_version",
)

ALLOWED_EVENT_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "idempotency_key",
    "case_ref_hash",
    "matter_ref_hash",
    "actor_ref_hash",
    "section",
    "operation",
    "state_version",
    "previous_state_version",
    "schema_version",
    "source_component",
    "payload_kind",
    "item_count",
    "changed_item_refs",
    "changed_field_names",
    "state_delta",
    "retention_bucket",
    "policy_version",
    "review_required",
    "validation_status",
    "created_at",
)

COMMON_STATE_FIELDS = (
    "schema_version",
    "section",
    "state_version",
    "summary",
    "item_count",
    "updated_at",
    "updated_by_role",
    "source_component",
    "policy_version",
)

SUMMARY_FIELDS = (
    "party_count",
    "fact_count",
    "task_count",
    "deadline_count",
    "node_count",
    "edge_count",
    "gap_count",
    "blocking_gap_count",
    "warning_gap_count",
    "active_count",
    "completed_count",
    "overdue_count",
    "urgent_count",
    "review_required_count",
)

SECTION_SCHEMAS: dict[str, dict[str, Any]] = {
    "parties": {
        "purpose": "Track party roles, representation, conflict, and identity-review state without names or contacts.",
        "collections": {
            "party_states": {
                "required_fields": ("party_ref_hash", "party_role", "party_type", "status"),
                "recommended_fields": (
                    "representation_status",
                    "conflict_status",
                    "identity_verification_status",
                    "authority_status",
                ),
                "allowed_fields": (
                    "party_ref_hash",
                    "party_role",
                    "party_type",
                    "status",
                    "representation_status",
                    "conflict_status",
                    "identity_verification_status",
                    "authority_status",
                    "claim_alignment_codes",
                    "risk_flags",
                    "source_refs",
                    "sort_order",
                    "updated_at",
                ),
            }
        },
    },
    "facts": {
        "purpose": "Track normalized fact state, chronology, dispute posture, and evidence links without fact prose.",
        "collections": {
            "fact_states": {
                "required_fields": ("fact_ref_hash", "fact_type", "status", "materiality", "dispute_status"),
                "recommended_fields": (
                    "chronology_date",
                    "date_precision",
                    "confidence_level",
                    "source_evidence_refs",
                ),
                "allowed_fields": (
                    "fact_ref_hash",
                    "fact_type",
                    "status",
                    "materiality",
                    "dispute_status",
                    "chronology_date",
                    "date_precision",
                    "confidence_level",
                    "source_evidence_refs",
                    "legal_issue_codes",
                    "party_refs",
                    "deadline_refs",
                    "risk_refs",
                    "sort_order",
                    "updated_at",
                ),
            }
        },
    },
    "tasks": {
        "purpose": "Track workbench task workflow state, ownership role, dependencies, and escalation status.",
        "collections": {
            "task_states": {
                "required_fields": ("task_ref_hash", "task_type", "status", "priority"),
                "recommended_fields": ("owner_role", "due_at", "escalation_status", "blocker_codes"),
                "allowed_fields": (
                    "task_ref_hash",
                    "task_type",
                    "status",
                    "priority",
                    "owner_role",
                    "due_at",
                    "due_date_status",
                    "escalation_status",
                    "blocker_codes",
                    "dependency_refs",
                    "related_party_refs",
                    "related_fact_refs",
                    "related_evidence_refs",
                    "review_required",
                    "completed_at",
                    "updated_at",
                ),
            }
        },
    },
    "deadlines": {
        "purpose": "Track computed deadline state, trigger metadata, urgency, and review flags without narrative notes.",
        "collections": {
            "deadline_states": {
                "required_fields": ("deadline_ref_hash", "deadline_type", "status", "due_at"),
                "recommended_fields": (
                    "trigger_date",
                    "trigger_source_type",
                    "urgency",
                    "computed_by_policy_version",
                ),
                "allowed_fields": (
                    "deadline_ref_hash",
                    "deadline_type",
                    "status",
                    "due_at",
                    "trigger_date",
                    "trigger_source_type",
                    "urgency",
                    "days_until_due_bucket",
                    "limitation_basis_code",
                    "computed_by_policy_version",
                    "review_required",
                    "linked_fact_refs",
                    "linked_task_refs",
                    "risk_codes",
                    "reminder_state",
                    "updated_at",
                ),
            }
        },
    },
    "evidence_graph": {
        "purpose": "Track graph nodes, edges, and gap flags by opaque references and controlled codes only.",
        "collections": {
            "graph_nodes": {
                "required_fields": ("node_ref_hash", "node_type", "entity_ref_hash"),
                "recommended_fields": ("review_status", "source_section", "updated_at"),
                "allowed_fields": (
                    "node_ref_hash",
                    "node_type",
                    "entity_ref_hash",
                    "review_status",
                    "source_section",
                    "fact_ref_hash",
                    "evidence_ref_hash",
                    "risk_ref_hash",
                    "citation_ref_hash",
                    "requirement_ref_hash",
                    "updated_at",
                ),
            },
            "graph_edges": {
                "required_fields": ("edge_ref_hash", "edge_type", "from_ref_hash", "to_ref_hash"),
                "recommended_fields": ("support_strength", "review_status", "updated_at"),
                "allowed_fields": (
                    "edge_ref_hash",
                    "edge_type",
                    "from_ref_hash",
                    "to_ref_hash",
                    "support_strength",
                    "review_status",
                    "source_section",
                    "updated_at",
                ),
            },
            "gap_flags": {
                "required_fields": ("gap_ref_hash", "gap_code", "severity"),
                "recommended_fields": ("source_section", "risk_ref_hash", "review_status"),
                "allowed_fields": (
                    "gap_ref_hash",
                    "gap_code",
                    "severity",
                    "source_section",
                    "risk_ref_hash",
                    "fact_ref_hash",
                    "evidence_ref_hash",
                    "deadline_ref_hash",
                    "review_status",
                    "updated_at",
                ),
            },
        },
    },
}

PRIVACY_SAFE_EVENT_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "idempotency_key",
    "case_ref_hash",
    "matter_ref_hash",
    "actor_ref_hash",
    "section",
    "operation",
    "state_version",
    "previous_state_version",
    "schema_version",
    "source_component",
    "payload_kind",
    "item_count",
    "changed_item_refs",
    "changed_field_names",
    "retention_bucket",
    "policy_version",
    "review_required",
    "validation_status",
)

FORBIDDEN_FIELD_PATTERNS = (
    "access_token",
    "address",
    "api_key",
    "authorization",
    "bearer_token",
    "client_email",
    "client_info",
    "client_name",
    "client_phone",
    "contact",
    "contract_text",
    "document_text",
    "email",
    "evidence_file_name",
    "fact_narrative",
    "fact_text",
    "file_name",
    "file_path",
    "file_url",
    "full_document",
    "headers",
    "id_card",
    "id_number",
    "legal_text",
    "message",
    "model_output",
    "note",
    "party_name",
    "password",
    "phone",
    "prompt",
    "raw",
    "raw_content",
    "raw_document",
    "refresh_token",
    "request_body",
    "response_body",
    "secret",
    "session_token",
    "storage_key",
    "summary_text",
    "user_email",
)

SENSITIVE_VALUE_PATTERNS = (
    ("api_key_like", re.compile(r"\bs[k]-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)),
    ("bearer_token_like", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{12,}\b", re.IGNORECASE)),
    ("email_like", re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")),
    ("phone_like", re.compile(r"\b(?:\+?86[- ]?)?1[3-9]\d{9}\b")),
    ("phone_like", re.compile(r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b")),
    ("id_number_like", re.compile(r"\b\d{17}[\dXx]\b")),
    ("credential_marker", re.compile(r"\b(password|secret|api[_ -]?key|authorization)\b", re.IGNORECASE)),
)

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^cwp:v1:[A-Za-z0-9:_-]{12,200}$")


@dataclass(frozen=True)
class StateFieldRule:
    name: str
    type: str
    required: bool
    privacy_classification: str
    description: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class CaseWorkbenchPersistencePlanService:
    """Describe and validate future local persistence for case workbench state.

    This service is intentionally local and side-effect free. It does not read
    or write databases, routers, release artifacts, ledgers, files, environment
    variables, network services, or model gateways.
    """

    def build_plan(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        event_checks = self.validate_sample_events(events)
        fail_count = sum(1 for item in event_checks if item["status"] == "fail")
        warn_count = sum(1 for item in event_checks if item["status"] == "warn")

        if events is None:
            status = "template"
        elif fail_count:
            status = "fail"
        elif warn_count:
            status = "warn"
        else:
            status = "pass"

        return {
            "status": status,
            "summary": {
                "plan_id": PLAN_ID,
                "checked_event_count": 0 if events is None else len(event_checks),
                "passing_event_count": sum(1 for item in event_checks if item["status"] == "pass"),
                "warning_event_count": warn_count,
                "failing_event_count": fail_count,
                "supported_section_count": len(SUPPORTED_SECTIONS),
                "allowed_event_field_count": len(ALLOWED_EVENT_FIELDS),
                "required_event_field_count": len(REQUIRED_EVENT_FIELDS),
                "forbidden_field_pattern_count": len(FORBIDDEN_FIELD_PATTERNS),
                "database_migration_required": False,
                "router_integration_required": False,
                "release_or_ledger_integration_required": False,
                "case_workbench_payload_changes_required": False,
                "raw_payload_storage_allowed": False,
                "network_required": False,
            },
            "state_schema": self._state_schema(),
            "state_event_schema": self._state_event_schema(),
            "repository_method_contracts": self._repository_method_contracts(),
            "privacy_safe_fields": self._privacy_safe_fields(),
            "forbidden_raw_content_fields": list(FORBIDDEN_FIELD_PATTERNS),
            "retention_policy": self._retention_policy(),
            "sample_state_events_validation": {
                "event_type": STATE_EVENT_TYPE,
                "supported_sections": list(SUPPORTED_SECTIONS),
                "supported_operations": list(SUPPORTED_OPERATIONS),
                "supported_payload_kinds": list(SUPPORTED_PAYLOAD_KINDS),
                "checks": event_checks or self._template_checks(),
            },
            "persistence_checks": event_checks or self._template_checks(),
            "recommended_actions": self._recommended_actions(status, event_checks),
            "integration_boundaries": [
                "Do not connect this plan service to database sessions.",
                "Do not modify routers, release readiness, continuous update ledger, or case_workbench_payload in this slice.",
                "Later integration may implement the repository behind these contracts after privacy review.",
            ],
            "privacy_note": (
                "Case workbench persistence must store only opaque references, statuses, controlled codes, dates, "
                "counts, graph references, and reviewer workflow flags. It must not store raw case content, party "
                "names, contact data, fact narratives, legal text, document text, filenames, prompts, model output, "
                "credentials, raw request or response bodies, or private notes."
            ),
            "validation_commands": [
                "python -m pytest tests/test_case_workbench_persistence_plan.py -q",
                "python -m compileall services/case_workbench_persistence_plan.py tests/test_case_workbench_persistence_plan.py",
            ],
        }

    def build_policy(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.build_plan(events)

    def validate_sample_events(self, events: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if events is None:
            return []
        checks: list[dict[str, Any]] = []
        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                checks.append(self._non_object_event_check(index))
            else:
                checks.append(self._check_event(index, event))
        return checks

    def _state_schema(self) -> dict[str, Any]:
        return {
            "schema_id": "case-workbench-state-v1",
            "sections": {
                section: {
                    "purpose": schema["purpose"],
                    "section_fields": list(COMMON_STATE_FIELDS),
                    "collections": {
                        name: {
                            "required_fields": list(collection["required_fields"]),
                            "recommended_fields": list(collection["recommended_fields"]),
                            "allowed_fields": list(collection["allowed_fields"]),
                            "field_rules": [
                                StateFieldRule(
                                    name=field,
                                    type=self._field_type(field),
                                    required=field in collection["required_fields"],
                                    privacy_classification=self._privacy_classification(field),
                                    description=self._field_description(field),
                                ).to_api()
                                for field in collection["allowed_fields"]
                            ],
                        }
                        for name, collection in schema["collections"].items()
                    },
                }
                for section, schema in SECTION_SCHEMAS.items()
            },
            "common_summary_fields": list(SUMMARY_FIELDS),
            "schema_notes": [
                "Each section is persisted as metadata state, not as raw case content.",
                "Use opaque refs or hashes for parties, facts, tasks, deadlines, evidence, risks, citations, and graph objects.",
                "Render display copy from live authorized case content at the UI boundary, not from this persistence layer.",
            ],
        }

    def _state_event_schema(self) -> dict[str, Any]:
        return {
            "event_type": STATE_EVENT_TYPE,
            "allowed_fields": list(ALLOWED_EVENT_FIELDS),
            "required_fields": list(REQUIRED_EVENT_FIELDS),
            "recommended_fields": list(RECOMMENDED_EVENT_FIELDS),
            "supported_sections": list(SUPPORTED_SECTIONS),
            "supported_operations": list(SUPPORTED_OPERATIONS),
            "supported_payload_kinds": list(SUPPORTED_PAYLOAD_KINDS),
            "idempotency_key_policy": {
                "required_before_durable_write": True,
                "format": "cwp:v1:{case_ref_hash}:{section}:{state_version}:{source_event_hash}",
                "regex": IDEMPOTENCY_KEY_PATTERN.pattern,
                "collision_behavior": "same_key_same_state_transition_no_duplicate_event",
                "privacy_note": "The key must not embed names, emails, phone numbers, file names, document titles, or raw facts.",
            },
        }

    def _repository_method_contracts(self) -> dict[str, Any]:
        return {
            "interface_name": "CaseWorkbenchStateRepository",
            "implementation_status": "contract_only_no_database_binding",
            "methods": [
                {
                    "name": "get_state",
                    "purpose": "Return the latest sanitized state envelope for one case and optional section filter.",
                    "parameters": ["case_ref_hash", "sections", "as_of_state_version"],
                    "returns": "CaseWorkbenchStateEnvelope",
                    "privacy_contract": "Returns metadata-only section state and aggregate counters.",
                },
                {
                    "name": "upsert_section_state",
                    "purpose": "Create or replace a section metadata snapshot after sample-event validation passes.",
                    "parameters": [
                        "case_ref_hash",
                        "section",
                        "state_version",
                        "state_delta",
                        "idempotency_key",
                        "actor_ref_hash",
                    ],
                    "returns": "CaseWorkbenchStateEnvelope",
                    "privacy_contract": "Rejects raw content fields and stores only schema-approved state fields.",
                },
                {
                    "name": "append_state_event",
                    "purpose": "Append one sanitized state event for replay and audit of local workspace changes.",
                    "parameters": ["state_event"],
                    "returns": "CaseWorkbenchStateEventReceipt",
                    "privacy_contract": "Persists event metadata and changed refs only; no raw payload or legal content.",
                },
                {
                    "name": "list_state_events",
                    "purpose": "List sanitized state events for a case, section, and version range.",
                    "parameters": ["case_ref_hash", "section", "from_state_version", "to_state_version", "limit"],
                    "returns": "CaseWorkbenchStateEventPage",
                    "privacy_contract": "Returns event IDs, versions, operations, controlled codes, and opaque refs.",
                },
                {
                    "name": "compact_state_events",
                    "purpose": "Roll validated deltas into the current section snapshot while keeping replay-safe receipts.",
                    "parameters": ["case_ref_hash", "section", "through_state_version"],
                    "returns": "CaseWorkbenchCompactionReceipt",
                    "privacy_contract": "Compaction cannot introduce fields outside the section state schema.",
                },
                {
                    "name": "delete_state",
                    "purpose": "Delete local workbench state for a case or section using a controlled deletion reason.",
                    "parameters": ["case_ref_hash", "section", "deletion_reason_code", "actor_ref_hash"],
                    "returns": "CaseWorkbenchDeletionReceipt",
                    "privacy_contract": "Deletion receipts contain reason codes and opaque refs only.",
                },
            ],
            "method_invariants": [
                "All writes must call validate_sample_events or equivalent checks first.",
                "Repository implementations must not import router or release modules.",
                "Repository implementations must not store raw case content or client identifiers.",
            ],
        }

    def _privacy_safe_fields(self) -> dict[str, Any]:
        return {
            "event_fields": list(PRIVACY_SAFE_EVENT_FIELDS),
            "field_classes": [
                "opaque_ref_hash",
                "controlled_status_code",
                "controlled_type_code",
                "role_code",
                "boolean_review_flag",
                "integer_count",
                "date_or_timestamp_without_free_text",
                "policy_or_schema_version",
                "graph_edge_reference",
            ],
            "section_item_fields": {
                section: {
                    collection_name: list(collection["allowed_fields"])
                    for collection_name, collection in schema["collections"].items()
                }
                for section, schema in SECTION_SCHEMAS.items()
            },
        }

    def _retention_policy(self) -> dict[str, Any]:
        return {
            "raw_event_retention": {
                "rejected_events": "delete_immediately",
                "passing_sanitized_debug_samples": "up_to_7_days",
                "durable_raw_payload_allowed": False,
            },
            "state_snapshot_retention": {
                "latest_section_snapshot": "while_case_workbench_is_active",
                "previous_section_snapshots": "last_20_versions_or_90_days",
                "deleted_case_state": "delete_on_case_deletion_or_privacy_request",
            },
            "event_receipt_retention": {
                "state_event_receipts": "400_days_metadata_only",
                "idempotency_keys": "90_days_after_state_version_superseded",
                "compaction_receipts": "400_days_metadata_only",
            },
            "deletion_policy": (
                "Rejected events and any event containing forbidden fields must not be durably written. "
                "Delete state by opaque case reference and keep only deletion reason codes where required."
            ),
        }

    def _template_checks(self) -> list[dict[str, Any]]:
        return [
            {
                "check_id": "case-workbench-persistence-template",
                "status": "pass",
                "event_index": None,
                "blocking": False,
                "warnings": [],
                "failures": [],
                "notes": [
                    "No sample state events were supplied.",
                    "Run build_plan(events) with sanitized workbench state events before implementing repository writes.",
                ],
            }
        ]

    def _non_object_event_check(self, index: int) -> dict[str, Any]:
        return {
            "check_id": f"case-workbench-state-event-{index}",
            "status": "fail",
            "event_index": index,
            "blocking": True,
            "missing_required_fields": list(REQUIRED_EVENT_FIELDS),
            "missing_recommended_fields": list(RECOMMENDED_EVENT_FIELDS),
            "unknown_fields": [],
            "unknown_nested_fields": [],
            "forbidden_fields_present": [],
            "forbidden_nested_fields": [],
            "sensitive_value_findings": [],
            "section_schema_findings": [],
            "idempotency_key_findings": [],
            "state_version_findings": [],
            "changed_field_findings": [],
            "warnings": [],
            "failures": ["event_must_be_object"],
            "allowed_to_persist": False,
        }

    def _check_event(self, index: int, event: dict[str, Any]) -> dict[str, Any]:
        fields = set(event)
        missing_required = [field for field in REQUIRED_EVENT_FIELDS if not _has_value(event.get(field))]
        missing_recommended = [field for field in RECOMMENDED_EVENT_FIELDS if not _has_value(event.get(field))]
        unknown_fields = sorted(_safe_field_name(field) for field in fields - set(ALLOWED_EVENT_FIELDS))
        forbidden_fields = [
            _safe_field_name(field)
            for field in sorted(fields)
            if self._matches_forbidden_field(field)
        ]
        forbidden_nested_fields = self._forbidden_nested_fields(event)
        sensitive_value_findings = self._sensitive_value_findings(event)
        section_schema_findings = self._section_schema_findings(event)
        idempotency_key_findings = self._idempotency_key_findings(event)
        state_version_findings = self._state_version_findings(event)
        changed_field_findings = self._changed_field_findings(event)
        enum_findings = self._enum_findings(event)

        failures = []
        if missing_required:
            failures.append("missing_required_fields")
        if forbidden_fields or forbidden_nested_fields:
            failures.append("forbidden_fields_present")
        if sensitive_value_findings:
            failures.append("sensitive_values_present")
        if any(item["severity"] == "fail" for item in section_schema_findings):
            failures.append("invalid_section_state_schema")
        if idempotency_key_findings:
            failures.append("invalid_idempotency_key")
        if state_version_findings:
            failures.append("invalid_state_version")
        if any(item["severity"] == "fail" for item in changed_field_findings):
            failures.append("invalid_changed_field_names")
        if any(item["severity"] == "fail" for item in enum_findings):
            failures.append("invalid_event_enum")

        warnings = []
        if missing_recommended:
            warnings.append("missing_recommended_fields")
        if unknown_fields:
            warnings.append("unknown_fields_not_in_event_schema")
        if any(item["severity"] == "warn" for item in section_schema_findings):
            warnings.append("section_state_schema_warning")
        if any(item["severity"] == "warn" for item in changed_field_findings):
            warnings.append("changed_field_name_warning")

        status = "fail" if failures else ("warn" if warnings else "pass")
        return {
            "check_id": f"case-workbench-state-event-{index}",
            "status": status,
            "event_index": index,
            "blocking": bool(failures),
            "missing_required_fields": missing_required,
            "missing_recommended_fields": missing_recommended,
            "unknown_fields": unknown_fields,
            "unknown_nested_fields": [
                item["path"] for item in section_schema_findings if item["type"] == "unknown_nested_field"
            ],
            "forbidden_fields_present": forbidden_fields,
            "forbidden_nested_fields": forbidden_nested_fields,
            "sensitive_value_findings": sensitive_value_findings,
            "section_schema_findings": section_schema_findings,
            "idempotency_key_findings": idempotency_key_findings,
            "state_version_findings": state_version_findings,
            "changed_field_findings": changed_field_findings,
            "warnings": warnings,
            "failures": failures,
            "allowed_to_persist": status != "fail",
        }

    def _forbidden_nested_fields(self, value: Any, path: str = "$") -> list[str]:
        findings: list[str] = []
        if isinstance(value, dict):
            for key, nested in value.items():
                next_path = f"{path}.{_safe_field_name(key)}"
                if self._matches_forbidden_field(str(key)):
                    findings.append(next_path)
                findings.extend(self._forbidden_nested_fields(nested, next_path))
        elif isinstance(value, (list, tuple, set)):
            for item_index, nested in enumerate(value):
                findings.extend(self._forbidden_nested_fields(nested, f"{path}[{item_index}]"))
        return findings

    def _section_schema_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        section = event.get("section")
        if not _has_value(section):
            return findings
        if section not in SECTION_SCHEMAS:
            return [{"path": "$.section", "type": "unsupported_section", "severity": "fail"}]

        state_delta = event.get("state_delta")
        if state_delta is None:
            return findings
        if not isinstance(state_delta, dict):
            return [{"path": "$.state_delta", "type": "state_delta_must_be_object", "severity": "fail"}]

        schema = SECTION_SCHEMAS[str(section)]
        collection_names = set(schema["collections"])
        allowed_top_level = set(COMMON_STATE_FIELDS) | collection_names
        for key, nested in state_delta.items():
            key_text = str(key)
            key_path = f"$.state_delta.{_safe_field_name(key_text)}"
            if key_text in collection_names:
                collection = schema["collections"][key_text]
                findings.extend(self._collection_findings(key_path, nested, collection))
            elif key_text == "summary":
                findings.extend(self._summary_findings(key_path, nested))
            elif key_text not in allowed_top_level:
                findings.append({"path": key_path, "type": "unknown_nested_field", "severity": "warn"})
        return findings

    def _collection_findings(
        self,
        path: str,
        value: Any,
        collection: dict[str, Any],
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if not isinstance(value, list):
            return [{"path": path, "type": "collection_must_be_list", "severity": "fail"}]

        allowed_fields = set(collection["allowed_fields"])
        required_fields = collection["required_fields"]
        for item_index, item in enumerate(value):
            item_path = f"{path}[{item_index}]"
            if not isinstance(item, dict):
                findings.append({"path": item_path, "type": "collection_item_must_be_object", "severity": "fail"})
                continue
            missing = [field for field in required_fields if not _has_value(item.get(field))]
            for field in missing:
                findings.append(
                    {
                        "path": f"{item_path}.{field}",
                        "type": "missing_required_section_field",
                        "severity": "fail",
                    }
                )
            for field in item:
                field_name = str(field)
                field_path = f"{item_path}.{_safe_field_name(field_name)}"
                if self._matches_forbidden_field(field_name):
                    findings.append({"path": field_path, "type": "forbidden_section_field", "severity": "fail"})
                elif field_name not in allowed_fields:
                    findings.append({"path": field_path, "type": "unknown_nested_field", "severity": "warn"})
        return findings

    def _summary_findings(self, path: str, value: Any) -> list[dict[str, str]]:
        if not isinstance(value, dict):
            return [{"path": path, "type": "summary_must_be_object", "severity": "fail"}]
        findings: list[dict[str, str]] = []
        for field in value:
            field_name = str(field)
            if self._matches_forbidden_field(field_name):
                findings.append({"path": f"{path}.{_safe_field_name(field_name)}", "type": "forbidden_summary_field", "severity": "fail"})
            elif field_name not in SUMMARY_FIELDS:
                findings.append({"path": f"{path}.{_safe_field_name(field_name)}", "type": "unknown_nested_field", "severity": "warn"})
        return findings

    def _sensitive_value_findings(self, value: Any, path: str = "$") -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                next_path = f"{path}.{_safe_field_name(key_text)}"
                if _contains_sensitive_value(key_text):
                    findings.append({"path": next_path, "type": "sensitive_field_name"})
                findings.extend(self._sensitive_value_findings(nested, next_path))
            return findings
        if isinstance(value, (list, tuple, set)):
            for item_index, nested in enumerate(value):
                findings.extend(self._sensitive_value_findings(nested, f"{path}[{item_index}]"))
            return findings
        if isinstance(value, str):
            for finding_type, pattern in SENSITIVE_VALUE_PATTERNS:
                if pattern.search(value):
                    findings.append({"path": path, "type": finding_type})
        return findings

    def _idempotency_key_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        value = event.get("idempotency_key")
        if not _has_value(value):
            return []
        if not isinstance(value, str):
            return [{"field": "idempotency_key", "type": "not_a_string"}]
        if not IDEMPOTENCY_KEY_PATTERN.match(value):
            return [{"field": "idempotency_key", "type": "invalid_format"}]
        return []

    def _state_version_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        for field in ("state_version", "previous_state_version"):
            if field in event and event[field] is not None:
                if not isinstance(event[field], int) or isinstance(event[field], bool) or event[field] < 0:
                    findings.append({"field": field, "type": "must_be_non_negative_integer"})
        if isinstance(event.get("state_version"), int) and event["state_version"] <= 0:
            findings.append({"field": "state_version", "type": "must_be_positive_integer"})
        return findings

    def _changed_field_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        fields = event.get("changed_field_names")
        section = event.get("section")
        if fields is None or not _has_value(section) or section not in SECTION_SCHEMAS:
            return []
        if not isinstance(fields, list):
            return [{"path": "$.changed_field_names", "type": "must_be_list", "severity": "fail"}]
        allowed_fields = set(COMMON_STATE_FIELDS) | set(SUMMARY_FIELDS)
        for collection in SECTION_SCHEMAS[str(section)]["collections"].values():
            allowed_fields.update(collection["allowed_fields"])
        findings: list[dict[str, str]] = []
        for item_index, field in enumerate(fields):
            if not isinstance(field, str) or not field.strip():
                findings.append({"path": f"$.changed_field_names[{item_index}]", "type": "must_be_non_empty_string", "severity": "fail"})
                continue
            if self._matches_forbidden_field(field):
                findings.append({"path": f"$.changed_field_names[{item_index}]", "type": "forbidden_changed_field", "severity": "fail"})
            elif field not in allowed_fields:
                findings.append({"path": f"$.changed_field_names[{item_index}]", "type": "unknown_changed_field", "severity": "warn"})
        return findings

    def _enum_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        enum_specs = (
            ("event_type", STATE_EVENT_TYPE),
            ("section", SUPPORTED_SECTIONS),
            ("operation", SUPPORTED_OPERATIONS),
            ("payload_kind", SUPPORTED_PAYLOAD_KINDS),
        )
        for field, expected in enum_specs:
            if not _has_value(event.get(field)):
                continue
            value = event[field]
            if isinstance(expected, str):
                if value != expected:
                    findings.append({"field": field, "type": "unexpected_value", "severity": "fail"})
            elif value not in expected:
                findings.append({"field": field, "type": "unsupported_value", "severity": "fail"})
        return findings

    def _recommended_actions(self, status: str, checks: list[dict[str, Any]]) -> list[str]:
        if status == "template":
            return [
                "Review the section state schema and repository method contracts before implementing durable storage.",
                "Run this plan against sanitized sample state events for parties, facts, tasks, deadlines, and evidence_graph.",
            ]

        failing = [item for item in checks if item["status"] == "fail"]
        warning = [item for item in checks if item["status"] == "warn"]
        actions: list[str] = []
        if failing:
            actions.append("Reject failing case workbench state events before any repository write.")
        if any(item["missing_required_fields"] for item in failing):
            actions.append("Populate required event metadata: event_id, event_type, timestamp, case_ref_hash, section, operation, state_version, and payload_kind.")
        if any(item["forbidden_fields_present"] or item["forbidden_nested_fields"] for item in failing):
            actions.append("Replace names, contact details, fact prose, legal text, documents, filenames, prompts, model output, and credentials with opaque refs or controlled codes.")
        if any(item["section_schema_findings"] for item in failing):
            actions.append("Conform state_delta items to the section-specific schema before persistence.")
        if warning:
            actions.append("Backfill recommended idempotency, actor, source, schema, and changed-field metadata for replay-safe local storage.")
        if not actions:
            actions.append("Use the repository contracts to persist sanitized metadata snapshots and append replay-safe state events.")
        return actions

    def _matches_forbidden_field(self, field_name: str) -> bool:
        normalized = _normalize_field(field_name)
        return any(pattern in normalized for pattern in FORBIDDEN_FIELD_PATTERNS)

    def _field_type(self, field: str) -> str:
        if field in {"review_required"}:
            return "boolean"
        if field in {"sort_order", "item_count"} or field.endswith("_count"):
            return "integer"
        if field.endswith("_refs") or field.endswith("_codes") or field.endswith("_flags"):
            return "array"
        if field.endswith("_at") or field.endswith("_date"):
            return "timestamp_or_date"
        return "string"

    def _privacy_classification(self, field: str) -> str:
        if field.endswith("_hash") or field.endswith("_ref") or field.endswith("_refs"):
            return "opaque_reference"
        if field.endswith("_codes") or field.endswith("_type") or field in {"status", "severity", "priority", "urgency"}:
            return "controlled_code"
        if field.endswith("_at") or field.endswith("_date"):
            return "date_metadata"
        if field.endswith("_count"):
            return "aggregate_count"
        return "metadata_only"

    def _field_description(self, field: str) -> str:
        descriptions = {
            "party_ref_hash": "Opaque party reference; never a party name or contact detail.",
            "fact_ref_hash": "Opaque fact reference; never fact narrative text.",
            "task_ref_hash": "Opaque task reference used for workflow state.",
            "deadline_ref_hash": "Opaque deadline reference used for computed deadline state.",
            "node_ref_hash": "Opaque evidence graph node reference.",
            "edge_ref_hash": "Opaque evidence graph edge reference.",
            "entity_ref_hash": "Opaque reference to the party, fact, evidence, risk, citation, or requirement represented by a node.",
            "status": "Controlled workflow status code.",
            "updated_at": "Timestamp metadata for replay and conflict detection.",
            "source_refs": "Opaque references to source materials, not filenames or text.",
        }
        return descriptions.get(field, "Privacy-safe case workbench metadata field.")


def _normalize_field(field_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", field_name.lower()).strip("_")


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _contains_sensitive_value(value: str) -> bool:
    return any(pattern.search(value) for _, pattern in SENSITIVE_VALUE_PATTERNS)


def _safe_field_name(field_name: Any) -> str:
    text = str(field_name)
    if any(pattern.search(text) for finding_type, pattern in SENSITIVE_VALUE_PATTERNS if finding_type != "credential_marker"):
        return "<redacted-field-name>"
    return text
