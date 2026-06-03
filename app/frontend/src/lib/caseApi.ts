import { createClient } from '@metagptx/web-sdk';

const client = createClient();

function unwrap<T>(response: unknown): T {
  if (response && typeof response === 'object' && 'data' in response) {
    return (response as { data: T }).data;
  }
  return response as T;
}

function apiErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string; error?: string; message?: string } } }).response;
    const detail = response?.data?.detail || response?.data?.error || response?.data?.message;
    if (detail) return detail;
  }
  if (error instanceof Error) return error.message;
  return '网络错误';
}

async function rawApiFetch<T>(url: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? window.localStorage.getItem('token') : null;
  const headers = new Headers(init.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(url, { ...init, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail || data?.error || data?.message || response.statusText;
    throw new Error(detail);
  }
  return data as T;
}

async function invoke<T>(url: string, method = 'GET', data?: unknown, timeout = 30_000): Promise<T> {
  try {
    const response = await client.apiCall.invoke({
      url,
      method,
      data,
      options: { timeout },
    });
    return unwrap<T>(response);
  } catch (error) {
    throw new Error(apiErrorMessage(error));
  }
}

function queryParam(query?: Record<string, unknown>): string {
  return query ? `&query=${encodeURIComponent(JSON.stringify(query))}` : '';
}

export interface CaseRecord {
  id: number;
  user_id?: string;
  org_id?: number | null;
  client_name?: string | null;
  title: string;
  case_type?: string | null;
  stage?: string | null;
  jurisdiction?: string | null;
  court_or_arbitration?: string | null;
  role?: string | null;
  opposing_party?: string | null;
  amount?: number | null;
  summary?: string | null;
  dispute_focus?: string | null;
  claims?: string | null;
  legal_basis?: string | null;
  missing_materials?: string | null;
  next_steps?: string | null;
  risk_level?: string | null;
  owner_name?: string | null;
  team_members?: string | null;
  key_deadline?: string | null;
  material_count?: number | null;
  evidence_completeness?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CaseMaterialRecord {
  id: number;
  user_id?: string;
  case_id: number;
  material_no?: string | null;
  title: string;
  material_type?: string | null;
  file_url?: string | null;
  parsed_text?: string | null;
  ocr_status?: string | null;
  source?: string | null;
  is_evidence?: boolean | null;
  proof_purpose?: string | null;
  page_refs?: string | null;
  related_facts?: string | null;
  authenticity_status?: string | null;
  relevance_status?: string | null;
  legality_status?: string | null;
  admissibility_risk?: string | null;
  need_notarization?: boolean | null;
  source_reliability?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CaseFactRecord {
  id: number;
  user_id?: string;
  case_id: number;
  fact_no?: string | null;
  event_date?: string | null;
  fact_text: string;
  persons?: string | null;
  amount?: string | null;
  source_refs?: string | null;
  confidence?: string | null;
  verified_by_user?: boolean | null;
  contradiction_note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CaseTaskRecord {
  id: number;
  user_id?: string;
  case_id: number;
  title: string;
  description?: string | null;
  assigned_to?: string | null;
  due_date?: string | null;
  priority?: string | null;
  status?: string | null;
  related_object_type?: string | null;
  related_object_id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CasePartyRecord {
  id: number;
  user_id?: string;
  case_id: number;
  name: string;
  party_type?: string | null;
  identity_type?: string | null;
  id_number?: string | null;
  address?: string | null;
  contact?: string | null;
  lawyer?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface GeneratedCaseDocument {
  id: number;
  user_id?: string;
  case_id?: number | null;
  doc_type: string;
  user_role?: string | null;
  title?: string | null;
  content?: string | null;
  draft_label?: string | null;
  input_data_json?: string | null;
  citation_map?: string | null;
  status?: string | null;
  generated_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PlanModeSession {
  session_id: number;
  status: string;
  task_type: string;
  document_type?: string | null;
  case_id?: number | null;
  completeness_score: number;
  understanding: string;
  known_slots: Record<string, unknown>;
  missing_required: string[];
  missing_optional: string[];
  conflicts: Array<{ field?: string; message?: string }>;
  questions: Array<{
    question_id: string;
    priority: 'required' | 'optional' | string;
    field: string;
    question: string;
    why_needed: string;
    answer_type: string;
    options?: string[];
    can_skip?: boolean;
  }>;
  generation_plan: {
    document_type?: string;
    position?: string;
    structure?: string[];
    risk_focus?: string[];
    missing_fields?: string[];
    blocking?: boolean;
    next_action?: string;
  };
  can_generate_draft_with_assumptions: boolean;
  assumptions_if_generate_now: string[];
}

export interface CaseImportJob {
  import_job_id: number;
  status: string;
  upload_mode: string;
  upload_mode_inferred?: string | null;
  total_files: number;
  parsed_files: number;
  progress: number;
  clusters: Array<{
    cluster_id: string;
    suggested_case_name: string;
    confidence: number;
    file_count?: number;
    file_ids: string[];
    needs_human_review?: boolean;
    case_id?: number;
    reason?: string;
  }>;
  unclassified_files: number;
  warnings: string[];
  error?: string | null;
  created_case_ids?: number[];
  files?: Array<{
    file_id: string;
    case_id?: number | null;
    original_name: string;
    relative_path: string;
    doc_type?: string;
    evidence_category?: string;
    confidence?: number;
    processing_status?: string;
    ocr_required?: boolean;
  }>;
}

export interface CaseGeneratedDocumentResponse {
  success: boolean;
  requires_plan_mode?: boolean;
  document_id?: number;
  document?: GeneratedCaseDocument & {
    qa_report?: Record<string, unknown>;
    evidence_citations?: unknown[];
    legal_citations?: unknown[];
  };
  preflight?: {
    blocking: boolean;
    missing_required: string[];
    warnings: string[];
    checks: Record<string, boolean>;
    plan_mode_recommended: boolean;
  };
  qa_report?: Record<string, unknown>;
  message?: string;
}

export interface CaseAIChatResponse {
  success: boolean;
  response: string;
  model?: string;
  usage?: Record<string, unknown> | null;
  case_snapshot?: {
    case_id: number;
    title: string;
    material_count: number;
    imported_file_count: number;
    evidence_count: number;
    fact_count: number;
    claim_count: number;
    document_count: number;
  };
}

export type CaseRequestMetadata = Record<string, unknown>;

interface ListResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export function listCases() {
  return invoke<ListResponse<CaseRecord>>('/api/v1/entities/cases?limit=2000&sort=-updated_at');
}

export function getCase(id: number | string) {
  return invoke<CaseRecord>(`/api/v1/entities/cases/${id}`);
}

export function createCase(data: Partial<CaseRecord> & { title: string }) {
  return invoke<CaseRecord>('/api/v1/entities/cases', 'POST', data);
}

export function updateCase(id: number | string, data: Partial<CaseRecord>) {
  return invoke<CaseRecord>(`/api/v1/entities/cases/${id}`, 'PUT', data);
}

export function listCaseMaterials(caseId: number) {
  return invoke<ListResponse<CaseMaterialRecord>>(`/api/v1/entities/case_materials?limit=2000&sort=material_no${queryParam({ case_id: caseId })}`);
}

export function createCaseMaterial(data: Partial<CaseMaterialRecord> & { case_id: number; title: string }) {
  return invoke<CaseMaterialRecord>('/api/v1/entities/case_materials', 'POST', data);
}

export function updateCaseMaterial(id: number, data: Partial<CaseMaterialRecord>) {
  return invoke<CaseMaterialRecord>(`/api/v1/entities/case_materials/${id}`, 'PUT', data);
}

export function listCaseFacts(caseId: number) {
  return invoke<ListResponse<CaseFactRecord>>(`/api/v1/entities/case_facts?limit=2000&sort=event_date${queryParam({ case_id: caseId })}`);
}

export function createCaseFact(data: Partial<CaseFactRecord> & { case_id: number; fact_text: string }) {
  return invoke<CaseFactRecord>('/api/v1/entities/case_facts', 'POST', data);
}

export function listCaseTasks(caseId: number) {
  return invoke<ListResponse<CaseTaskRecord>>(`/api/v1/entities/case_tasks?limit=2000&sort=due_date${queryParam({ case_id: caseId })}`);
}

export function createCaseTask(data: Partial<CaseTaskRecord> & { case_id: number; title: string }) {
  return invoke<CaseTaskRecord>('/api/v1/entities/case_tasks', 'POST', data);
}

export function updateCaseTask(id: number, data: Partial<CaseTaskRecord>) {
  return invoke<CaseTaskRecord>(`/api/v1/entities/case_tasks/${id}`, 'PUT', data);
}

export function listCaseParties(caseId: number) {
  return invoke<ListResponse<CasePartyRecord>>(`/api/v1/entities/case_parties?limit=2000&sort=id${queryParam({ case_id: caseId })}`);
}

export function createCaseParty(data: Partial<CasePartyRecord> & { case_id: number; name: string }) {
  return invoke<CasePartyRecord>('/api/v1/entities/case_parties', 'POST', data);
}

export function listGeneratedCaseDocuments(caseId: number) {
  return invoke<ListResponse<GeneratedCaseDocument>>(`/api/v1/entities/generated_documents?limit=2000&sort=-created_at${queryParam({ case_id: caseId })}`);
}

export function createGeneratedCaseDocument(data: Partial<GeneratedCaseDocument> & { doc_type: string }) {
  return invoke<GeneratedCaseDocument>('/api/v1/entities/generated_documents', 'POST', data);
}

export function createPlanSession(data: {
  task_type?: string;
  case_id?: number;
  user_input: string;
  document_type?: string;
  context?: Record<string, unknown>;
}) {
  return invoke<PlanModeSession>('/api/v1/plan-mode/session', 'POST', data);
}

export function submitPlanAnswers(
  sessionId: number,
  answers: Array<{ question_id?: string; field: string; value: string }>,
) {
  return invoke<PlanModeSession>(`/api/v1/plan-mode/session/${sessionId}/answers`, 'POST', { answers });
}

export function generatePlanDraft(sessionId: number) {
  return invoke<{ success: boolean; session: PlanModeSession; draft: { title: string; content: string; missing_fields: string[]; assumptions: string[] } }>(
    `/api/v1/plan-mode/session/${sessionId}/generate`,
    'POST',
    { approval: true, generation_mode: 'draft', output_format: 'markdown' },
  );
}

export async function importCaseZip(file: File, uploadMode: 'single_case' | 'multi_case' | 'auto') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('upload_mode', uploadMode);
  return rawApiFetch<CaseImportJob>('/api/v1/cases/import-zip', {
    method: 'POST',
    body: formData,
  });
}

export function confirmCaseImportClusters(jobId: number, clusters: Array<{ cluster_id: string; case_name: string; file_ids: string[] }>) {
  return invoke<{ status: string; created_case_ids: number[] }>(`/api/v1/cases/import-jobs/${jobId}/confirm-clusters`, 'POST', { clusters });
}

export function generateCaseEvidenceCatalog(caseId: number, requestMetadata?: CaseRequestMetadata) {
  return invoke<CaseGeneratedDocumentResponse>(
    `/api/v1/cases/${caseId}/generate/evidence-catalog`,
    'POST',
    requestMetadata ? { request_metadata: requestMetadata } : {},
  );
}

export function generateCaseCivilComplaint(
  caseId: number,
  forceDraft = true,
  requestMetadata?: CaseRequestMetadata,
) {
  return invoke<CaseGeneratedDocumentResponse>(
    `/api/v1/cases/${caseId}/generate/civil-complaint`,
    'POST',
    {
      force_draft: forceDraft,
      ...(requestMetadata ? { request_metadata: requestMetadata } : {}),
    },
  );
}

export function caseAiChat(
  caseId: number,
  data: {
    message: string;
    conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>;
    request_metadata?: CaseRequestMetadata;
  },
) {
  return invoke<CaseAIChatResponse>(`/api/v1/cases/${caseId}/ai-chat`, 'POST', data, 180_000);
}
