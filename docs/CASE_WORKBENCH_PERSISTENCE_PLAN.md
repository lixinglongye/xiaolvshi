# Case Workbench Persistence Plan

This plan defines a pure local contract for future case workbench state persistence. It is limited to schema, repository method contracts, privacy-safe field rules, forbidden raw-content fields, retention guidance, and sample state event validation.

It does not connect to a database, router, release workflow, continuous update ledger, network service, model gateway, or `case_workbench_payload`. The main thread can later integrate storage behind these contracts.

## Scope

- Service: `app/backend/services/case_workbench_persistence_plan.py`
- Tests: `app/backend/tests/test_case_workbench_persistence_plan.py`
- Documentation: `docs/CASE_WORKBENCH_PERSISTENCE_PLAN.md`

The service is descriptive and validating only. It returns a plan from `CaseWorkbenchPersistencePlanService.build_plan(events)` and an alias from `build_policy(events)`.

## State Sections

The supported persistent workbench sections are:

- `parties`
- `facts`
- `tasks`
- `deadlines`
- `evidence_graph`

Each section is metadata-only. Store opaque references, controlled codes, dates, counts, state versions, and review flags. Do not store display prose or raw case content.

## Section Schemas

### Parties

Collection: `party_states`

Required fields:

- `party_ref_hash`
- `party_role`
- `party_type`
- `status`

Recommended metadata includes representation status, conflict status, identity verification status, authority status, claim alignment codes, risk flags, source refs, sort order, and update timestamp.

Do not store party names, client names, emails, phone numbers, addresses, ID numbers, private notes, or contact details.

### Facts

Collection: `fact_states`

Required fields:

- `fact_ref_hash`
- `fact_type`
- `status`
- `materiality`
- `dispute_status`

Recommended metadata includes chronology date, date precision, confidence level, evidence refs, legal issue codes, party refs, deadline refs, risk refs, sort order, and update timestamp.

Do not store fact narratives, fact text, legal text, raw document text, copied contract clauses, summaries, messages, or notes.

### Tasks

Collection: `task_states`

Required fields:

- `task_ref_hash`
- `task_type`
- `status`
- `priority`

Recommended metadata includes owner role, due timestamp, due-date status, escalation status, blocker codes, dependency refs, related party/fact/evidence refs, review flag, completion timestamp, and update timestamp.

Do not store task descriptions, private instructions, client messages, document names, or free-text notes.

### Deadlines

Collection: `deadline_states`

Required fields:

- `deadline_ref_hash`
- `deadline_type`
- `status`
- `due_at`

Recommended metadata includes trigger date, trigger source type, urgency, due-date bucket, limitation basis code, policy version, review flag, linked fact refs, linked task refs, risk codes, reminder state, and update timestamp.

Do not store raw deadline explanations, copied judgment text, legal narrative, document filenames, or private comments.

### Evidence Graph

Collections:

- `graph_nodes`
- `graph_edges`
- `gap_flags`

Required node fields:

- `node_ref_hash`
- `node_type`
- `entity_ref_hash`

Required edge fields:

- `edge_ref_hash`
- `edge_type`
- `from_ref_hash`
- `to_ref_hash`

Required gap fields:

- `gap_ref_hash`
- `gap_code`
- `severity`

Recommended metadata includes source section, support strength, review status, fact/evidence/risk/citation/requirement refs, and update timestamp.

Do not store evidence filenames, file paths, file URLs, storage keys, document text, quoted evidence content, raw citations, or model output.

## State Event Schema

The supported event type is `case_workbench_state_event`.

Required event fields:

- `event_id`
- `event_type`
- `timestamp`
- `case_ref_hash`
- `section`
- `operation`
- `state_version`
- `payload_kind`

Recommended event fields:

- `idempotency_key`
- `actor_ref_hash`
- `source_component`
- `schema_version`
- `previous_state_version`
- `changed_item_refs`
- `changed_field_names`
- `policy_version`

Supported operations:

- `upsert_snapshot`
- `append_delta`
- `delete_item`
- `compact_snapshot`
- `restore_snapshot`

Supported payload kinds:

- `metadata_snapshot`
- `metadata_delta`
- `aggregate_summary`

The optional `state_delta` field must contain only section-approved metadata collections. It is not a raw payload field.

## Repository Method Contracts

Future storage should implement `CaseWorkbenchStateRepository` with these methods:

- `get_state(case_ref_hash, sections, as_of_state_version)` returns the latest sanitized state envelope.
- `upsert_section_state(case_ref_hash, section, state_version, state_delta, idempotency_key, actor_ref_hash)` creates or replaces a section metadata snapshot after validation.
- `append_state_event(state_event)` appends one sanitized event receipt for replay.
- `list_state_events(case_ref_hash, section, from_state_version, to_state_version, limit)` returns event metadata pages.
- `compact_state_events(case_ref_hash, section, through_state_version)` rolls deltas into section snapshots.
- `delete_state(case_ref_hash, section, deletion_reason_code, actor_ref_hash)` deletes local workbench state by opaque reference.

Required invariants:

- Validate every write before persistence.
- Store only schema-approved metadata fields.
- Use opaque refs or hashes for parties, facts, tasks, deadlines, evidence, risks, citations, and graph objects.
- Keep routers, release checks, ledgers, and payload assembly out of repository implementation.

## Privacy-Safe Fields

Allowed field classes:

- opaque reference hashes
- controlled status codes
- controlled type codes
- role codes
- boolean review flags
- integer counts
- date or timestamp metadata without free text
- policy or schema versions
- graph edge references

Examples include `case_ref_hash`, `matter_ref_hash`, `actor_ref_hash`, `party_ref_hash`, `fact_ref_hash`, `task_ref_hash`, `deadline_ref_hash`, `node_ref_hash`, `edge_ref_hash`, `status`, `priority`, `urgency`, `review_required`, `state_version`, `item_count`, and `policy_version`.

## Forbidden Raw Content Fields

Forbidden fields include:

- party or client identity fields such as party name, client name, email, phone, address, ID number, and contact fields
- raw fact fields such as fact text, fact narrative, summary text, notes, messages, and legal text
- document fields such as document text, contract text, full document, raw document, filenames, file paths, file URLs, storage keys, and evidence filenames
- model and request fields such as prompt, raw request, raw response, request body, response body, headers, and model output
- credential fields such as API keys, bearer tokens, access tokens, refresh tokens, session tokens, passwords, secrets, and authorization headers

The validator reports field names, paths, and finding types only. It does not echo sensitive values.

## Sample Event Validation

`build_plan(events)` validates sample events before any durable repository is implemented.

It fails events that:

- are not objects
- miss required event fields
- use unsupported section, operation, payload kind, or event type
- contain forbidden top-level or nested fields
- contain credential-like, email-like, phone-like, or ID-number-like values
- use invalid idempotency key format
- use invalid state version values
- have section state items missing required schema fields
- list forbidden changed field names

It warns when:

- recommended event metadata is missing
- unknown event fields are present
- unknown section metadata fields are present
- unknown changed field names are present

Warnings remain `allowed_to_persist=True` so later implementation can decide whether to backfill before durable writes. Failures are blocking.

## Retention

- Rejected events: delete immediately.
- Passing sanitized debug samples: keep up to 7 days if needed.
- Latest section snapshot: keep while the case workbench is active.
- Previous section snapshots: keep the last 20 versions or 90 days.
- State event receipts: keep 400 days, metadata only.
- Idempotency keys: keep 90 days after the state version is superseded.
- Compaction receipts: keep 400 days, metadata only.

This is not a matter audit log and must not retain raw legal content or client identity data.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_workbench_persistence_plan.py -q
python -m compileall services/case_workbench_persistence_plan.py tests/test_case_workbench_persistence_plan.py
```
