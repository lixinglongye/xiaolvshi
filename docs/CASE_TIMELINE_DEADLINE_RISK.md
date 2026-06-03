# Case Timeline Deadline Risk

`CaseTimelineDeadlineRiskService` defines deterministic deadline-risk metadata for the case workspace. It does not read the current date or perform calendar arithmetic; it only uses supplied event fields such as `days_until_deadline`, explicit `urgency`, event type, and key-date presence.

## Endpoints

```http
GET /api/v1/maintenance/case-timeline-deadline-risk
POST /api/v1/maintenance/case-timeline-deadline-risk
```

The `GET` endpoint returns the template. The `POST` endpoint accepts a list of event metadata objects and returns normalized events, risk flags, blocking urgent items, and reviewer next actions.

## Event Metadata

Example event:

```json
{
  "event_id": "answer-1",
  "event_type": "answer_deadline",
  "title": "Answer deadline",
  "key_date": "YYYY-MM-DD",
  "days_until_deadline": 3,
  "urgency": "normal",
  "source": "court_notice_or_case_file_reference",
  "jurisdiction": "court_or_forum"
}
```

Supported event families include service received, answer deadline, evidence deadline, limitation period deadline, performance deadline, appeal deadline, enforcement deadline, and hearing.

## Risk Rules

- `days_until_deadline <= 3` creates an `urgent_deadline` flag and a blocking urgent item.
- Explicit urgency values such as `urgent`, `critical`, `blocking`, `overdue`, or `immediate` also create a blocking urgent item.
- Missing `key_date`, `deadline_date`, or `event_date` creates a `missing_fact` flag.
- `days_until_deadline <= 7` creates a high-risk near-deadline flag.
- `days_until_deadline <= 14` creates a watch-window flag.

## Product Gate

Blocking urgent items should pause client delivery until a responsible lawyer confirms the controlling date, source reliability, owner, filing path, evidence plan, and any client fact requests.

`missing_fact` does not mean the deadline is safe. It means the system lacks the field needed for a final deadline assessment.

## Low Resource Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_timeline_deadline_risk.py -q
```

## Privacy Notes

Timeline metadata should not store raw evidence text, direct contact details, credentials, or unnecessary identity information. Source references, actor IDs, audit logs, and permission records should stay in controlled case storage. Client-visible deadline summaries require lawyer review and privilege screening.
