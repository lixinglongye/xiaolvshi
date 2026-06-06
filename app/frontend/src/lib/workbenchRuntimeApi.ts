import { client } from '@/lib/api';

export type CaseWorkbenchSectionId = 'parties' | 'facts' | 'tasks' | 'deadlines' | 'evidence_graph' | string;

export type CaseWorkbenchSectionState = {
  id: CaseWorkbenchSectionId;
  status: string;
  schema_version: string;
  state_version: number;
  summary: Record<string, unknown>;
  state: Record<string, unknown>;
  collection_counts: Record<string, number>;
  latest_event_id?: string | null;
  policy_version?: string | null;
  validation_status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CaseWorkbenchStatePayload = {
  payload_id: string;
  case_id: string;
  workspace_id: string;
  schema_version: string;
  status: string;
  section_order: CaseWorkbenchSectionId[];
  section_count: number;
  populated_section_count: number;
  created_at?: string | null;
  updated_at?: string | null;
  sections: Record<string, CaseWorkbenchSectionState>;
  risk_refresh_plan?: CaseWorkbenchRiskRefreshPlan;
};

export type CaseWorkbenchRiskRefreshSectionRow = {
  section: string;
  status: string;
  state_version: number;
  latest_event_id?: string | null;
  validation_status?: string | null;
  refresh_required: boolean;
  refresh_targets: string[];
  reason_codes: string[];
  active_count?: number;
  blocked_count?: number;
  urgent_count?: number;
  blocking_gap_count?: number;
  review_required_count?: number;
  raw_content_returned: boolean;
};

export type CaseWorkbenchRiskRefreshEventRow = {
  event_id: string;
  section: string;
  operation: string;
  state_version: number;
  validation_status: string;
  changed_item_count: number;
  changed_field_names: string[];
  requires_risk_state_refresh: boolean;
  requires_evidence_graph_refresh: boolean;
  raw_event_payload_returned: boolean;
  reason_codes: string[];
};

export type CaseWorkbenchRiskRefreshPlan = {
  id: string;
  status: string;
  summary: {
    section_count: number;
    populated_section_count: number;
    refresh_required_count: number;
    blocking_section_count: number;
    review_section_count: number;
    recent_event_count: number;
    risk_affecting_event_count: number;
    evidence_graph_affecting_event_count: number;
    task_active_count: number;
    task_blocked_count: number;
    deadline_urgent_count: number;
    evidence_graph_blocking_gap_count: number;
    review_required_count: number;
    raw_text_returned: boolean;
    event_payloads_returned: boolean;
    risk_state_written: boolean;
    evidence_graph_written: boolean;
    notification_sent: boolean;
  };
  section_refresh_rows: CaseWorkbenchRiskRefreshSectionRow[];
  event_trigger_rows: CaseWorkbenchRiskRefreshEventRow[];
  refresh_required_section_ids: string[];
  risk_affecting_event_ids: string[];
  evidence_graph_affecting_event_ids: string[];
  blocking_section_ids: string[];
  review_section_ids: string[];
  evidence_graph_plan: {
    status: string;
    required_before_client_delivery: boolean;
    source_sections: string[];
    blocking_gap_count: number;
    trigger_event_count: number;
    writes_graph: boolean;
    action: string;
  };
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type CaseWorkbenchStateEvent = {
  event_id: string;
  event_type?: string;
  timestamp?: string;
  idempotency_key?: string;
  case_ref_hash?: string;
  matter_ref_hash?: string;
  actor_ref_hash?: string;
  section: CaseWorkbenchSectionId;
  operation: string;
  state_version: number;
  previous_state_version?: number;
  schema_version?: string;
  source_component?: string;
  payload_kind?: string;
  item_count?: number;
  changed_item_refs?: string[];
  changed_field_names?: string[];
  state_delta?: Record<string, unknown>;
  retention_bucket?: string;
  policy_version?: string;
  review_required?: boolean;
  validation_status?: string;
  created_at?: string;
  [key: string]: unknown;
};

export type CaseWorkbenchStateEventRecord = {
  event_id: string;
  case_id: string;
  section: CaseWorkbenchSectionId;
  operation: string;
  state_version: number;
  event_hash: string;
  actor_id?: string | null;
  schema_version: string;
  policy_version?: string | null;
  validation_status?: string | null;
  created_at?: string | null;
  event_json: Record<string, unknown>;
  created?: boolean;
  idempotent_replay?: boolean;
};

export type CaseWorkbenchApplyEventResponse = {
  status: string;
  case_id: string;
  workspace_id: string;
  section: CaseWorkbenchSectionId;
  event: CaseWorkbenchStateEventRecord;
  section_state: CaseWorkbenchSectionState;
  payload?: CaseWorkbenchStatePayload;
};

export type CaseWorkbenchStateEventsResponse = {
  case_id: string;
  section?: CaseWorkbenchSectionId | null;
  limit: number;
  offset: number;
  event_count: number;
  events: CaseWorkbenchStateEventRecord[];
};

export type CaseWorkbenchStateOptions = {
  workspace_id?: string;
  section?: CaseWorkbenchSectionId;
  sections?: CaseWorkbenchSectionId[];
};

export type CaseWorkbenchStateEventsOptions = {
  section?: CaseWorkbenchSectionId;
  limit?: number;
  offset?: number;
};

const CASE_WORKBENCH_RUNTIME_TIMEOUT_MS = 30_000;

function unwrapData<T>(response: unknown): T {
  const payload = response && typeof response === 'object' && 'data' in response
    ? (response as { data: unknown }).data
    : response;
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function buildQuery(params: Record<string, string | number | boolean | string[] | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined) return;
    if (Array.isArray(value)) {
      if (value.length > 0) search.set(key, value.join(','));
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

async function invoke<T>(url: string, method = 'GET', data?: unknown): Promise<T> {
  const response = await client.apiCall.invoke({
    url,
    method,
    data,
    options: { timeout: CASE_WORKBENCH_RUNTIME_TIMEOUT_MS },
  });
  return unwrapData<T>(response);
}

export function getCaseWorkbenchState(
  caseId: number | string,
  opts: CaseWorkbenchStateOptions = {},
): Promise<CaseWorkbenchStatePayload> {
  const section = opts.section ?? (opts.sections?.length === 1 ? opts.sections[0] : undefined);
  const query = buildQuery({
    workspace_id: opts.workspace_id,
    section,
  });
  return invoke<CaseWorkbenchStatePayload>(`/api/v1/cases/${caseId}/workbench/state${query}`);
}

export function applyCaseWorkbenchStateEvent(
  caseId: number | string,
  event: CaseWorkbenchStateEvent,
): Promise<CaseWorkbenchApplyEventResponse> {
  return invoke<CaseWorkbenchApplyEventResponse>(
    `/api/v1/cases/${caseId}/workbench/state-events`,
    'POST',
    event,
  );
}

export function listCaseWorkbenchStateEvents(
  caseId: number | string,
  opts: CaseWorkbenchStateEventsOptions = {},
): Promise<CaseWorkbenchStateEventsResponse> {
  const query = buildQuery({
    section: opts.section,
    limit: opts.limit,
    offset: opts.offset,
  });
  return invoke<CaseWorkbenchStateEventsResponse>(`/api/v1/cases/${caseId}/workbench/state-events${query}`);
}
