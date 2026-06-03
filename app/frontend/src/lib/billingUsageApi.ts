import { client } from '@/lib/api';

export type BillingUsageSummaryOptions = {
  quota_subject_hash?: string;
  quota_window?: string;
  requested_units?: number;
};

export type BillingReportUsagePayload = {
  quota_subject_hash?: string;
  source: string;
  event_id: string;
  units?: number;
  quota_window?: string;
  occurred_at?: string;
};

export type BillingUsageSnapshot = {
  event_count: number;
  units: number;
  used: number;
  remaining?: number | null;
};

export type BillingUsageEventResult = {
  recorded: boolean;
  idempotent_replay: boolean;
  decision_status: string;
  units: number;
  used: number;
  remaining?: number | null;
  reason_codes: string[];
};

export type BillingUsageSummary = {
  scope: string;
  quota_subject_hash: string;
  quota_window: string;
  action: string;
  usage_metric: string;
  plan_type: string;
  effective_plan_type: string;
  subscription_status: string;
  limit?: number | null;
  report_quota_monthly?: number | null;
  persisted_usage: number;
  reports_used_month: number;
  remaining?: number | null;
  reports_remaining?: number | null;
  can_create_report: boolean;
  decision_status: string;
  reason_codes: string[];
  usage_snapshot: BillingUsageSnapshot;
  last_usage_event?: BillingUsageEventResult | null;
};

const BILLING_USAGE_TIMEOUT_MS = 30_000;

function unwrapData<T>(response: unknown): T {
  const payload = response && typeof response === 'object' && 'data' in response
    ? (response as { data: unknown }).data
    : response;
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

async function invoke<T>(url: string, method = 'GET', data?: unknown): Promise<T> {
  const response = await client.apiCall.invoke({
    url,
    method,
    data,
    options: { timeout: BILLING_USAGE_TIMEOUT_MS },
  });
  return unwrapData<T>(response);
}

export function getBillingUsageSummary(opts: BillingUsageSummaryOptions = {}): Promise<BillingUsageSummary> {
  const query = buildQuery({
    quota_subject_hash: opts.quota_subject_hash,
    quota_window: opts.quota_window,
    requested_units: opts.requested_units,
  });
  return invoke<BillingUsageSummary>(`/api/v1/billing-usage/me${query}`);
}

export function consumeBillingReportUsage(payload: BillingReportUsagePayload): Promise<BillingUsageSummary> {
  return invoke<BillingUsageSummary>('/api/v1/billing-usage/consume-report', 'POST', payload);
}
