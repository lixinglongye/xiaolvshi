import { client } from '@/lib/api';

export type LegalRagRetrievalPlanRequest = {
  jurisdiction?: string;
  document_type?: string;
  source_type?: string;
  effective_on?: string;
  effective_on_or_before?: string;
  source_ids?: string[];
  source_id?: string;
  freshness_status?: string | string[];
  last_verified_at_min?: string;
  authority_level?: string;
  issuer?: string;
  use_case?: string;
  index_version?: string;
  retention_bucket?: string;
};

export type LegalRagSourceMetadata = {
  source_id: string;
  index_entry_id: string;
  index_version: string;
  source_type: string;
  jurisdiction: string;
  effective_date: string;
  citation: string;
  citation_key?: string;
  freshness_status: string;
  freshness_expires_at: string;
  metadata_hash: string;
  use_case?: string;
  title: string;
  source_title?: string;
  last_verified_at: string;
  authority_level?: string;
  issuer?: string;
  publication_date?: string;
  amendment_date?: string;
  official_url?: string;
  retrieval_locator?: string;
  retention_bucket?: string;
};

export type LegalRagRetrievalPlan = {
  status: string;
  blocked: boolean;
  reason_codes: string[];
  filters: Record<string, unknown>;
  repository_filters: Record<string, unknown>;
  selected_source_ids: string[];
  selected_sources: LegalRagSourceMetadata[];
  blocked_source_ids: string[];
  stale_source_ids: string[];
  missing_requested_source_ids: string[];
  unusable_requested_source_ids: string[];
  coverage_counts: {
    candidate_source_count: number;
    selected_source_count: number;
    blocked_source_count: number;
    stale_source_count: number;
    requested_source_count: number;
    missing_requested_source_count: number;
    unusable_requested_source_count: number;
    [key: string]: number;
  };
  validation: {
    status?: string;
    failures: string[];
    warnings: string[];
    forbidden_fields_present: string[];
    sensitive_value_findings: Array<{ path: string; type: string }>;
    active_index_query_safe: boolean;
  };
};

export type LegalRagEvaluationPayload = {
  filters?: LegalRagRetrievalPlanRequest;
  retrieved_source_ids?: string[];
  answer_citation_source_ids?: string[];
  verified_claim_count?: number;
  total_claim_count?: number;
  unsupported_claims?: Array<Record<string, unknown>>;
  pii_findings?: Array<Record<string, unknown>>;
};

export type LegalRagEvaluation = {
  status: string;
  score: number;
  metric_scores: Record<string, number>;
  required_metrics?: string[];
  blocking_reasons?: string[];
  warnings?: string[];
  recommended_actions?: string[];
  [key: string]: unknown;
};

export type LegalRagEvaluationResponse = LegalRagEvaluation | {
  retrieval_plan: Pick<
    LegalRagRetrievalPlan,
    'status' | 'blocked' | 'reason_codes' | 'selected_source_ids' | 'coverage_counts'
  >;
  evaluation_input: Record<string, unknown>;
  evaluation: LegalRagEvaluation;
};

const LEGAL_RAG_TIMEOUT_MS = 30_000;

function unwrapData<T>(response: unknown): T {
  const payload = response && typeof response === 'object' && 'data' in response
    ? (response as { data: unknown }).data
    : response;
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

async function invoke<T>(url: string, method = 'GET', data?: unknown): Promise<T> {
  const response = await client.apiCall.invoke({
    url,
    method,
    data,
    options: { timeout: LEGAL_RAG_TIMEOUT_MS },
  });
  return unwrapData<T>(response);
}

export function buildLegalRagRetrievalPlan(
  payload: LegalRagRetrievalPlanRequest,
): Promise<LegalRagRetrievalPlan> {
  return invoke<LegalRagRetrievalPlan>('/api/v1/legal-rag/retrieval-plan', 'POST', payload);
}

export function evaluateLegalRag(payload: LegalRagEvaluationPayload): Promise<LegalRagEvaluationResponse> {
  return invoke<LegalRagEvaluationResponse>('/api/v1/legal-rag/evaluate', 'POST', payload);
}
