/**
 * Deep Review API - Calls backend AI endpoints for real legal review reports
 */
import { createClient } from '@metagptx/web-sdk';

const client = createClient();
const DEEP_REVIEW_TIMEOUT_MS = 15 * 60 * 1000;
const DEEP_REVIEW_POLL_TIMEOUT_MS = 30 * 1000;

function unwrapApiResponse<T>(response: unknown): T {
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

export interface DeepReviewRequest {
  document_text: string;
  document_type?: string;
  user_role?: string;
  review_goal?: string;
  known_facts?: string[];
  jurisdiction?: string;
}

export interface DeepReviewResponse {
  success: boolean;
  report?: DeepReviewReport;
  error?: string;
}

export interface AnalyzeUploadedDocumentRequest {
  document_id: number;
  document_type?: string;
  user_role?: string;
  review_goal?: string;
  known_facts?: string[];
  jurisdiction?: string;
  bucket_name?: string;
  force_reextract?: boolean;
  enable_ocr?: boolean;
}

export interface UploadedOcrReadiness {
  status?: string;
  policy_id?: string;
  summary?: {
    ready_for_parse?: boolean;
    ocr_required?: boolean;
    blocked?: boolean;
    manual_review_required?: boolean;
    low_text_page_count?: number;
    scanned_page_count?: number;
    ocr_attempt_count?: number;
  };
  retry_state?: {
    attempt_count?: number;
    retry_budget_remaining?: number;
    latest_failure_reason?: string | null;
    retry_allowed?: boolean;
  };
  blocking_conditions?: Array<{ id?: string; title?: string; reviewer_action?: string }>;
  manual_review_conditions?: Array<{ id?: string; title?: string; reviewer_action?: string }>;
  recommended_next_actions?: string[];
}

interface AnalyzeUploadedDocumentResponse {
  success: boolean;
  report_id?: number;
  review_id?: number;
  report?: DeepReviewReport;
  extraction?: {
    parser?: string;
    page_count?: number | null;
    char_count?: number;
    warnings?: string[];
    text_layer_pages?: number[];
    low_text_pages?: number[];
    ocr_pages?: number[];
    extraction_quality?: {
      status?: string;
      score?: number;
      chars_per_page?: number | null;
      text_layer_page_count?: number;
      low_text_page_count?: number;
      ocr_page_count?: number;
      blocking_reasons?: string[];
      warning_reasons?: string[];
      recommended_actions?: string[];
    };
    ocr_readiness?: UploadedOcrReadiness;
  };
  ocr_readiness?: UploadedOcrReadiness;
  error?: string;
}

export interface AnalyzeUploadedDocumentStartResponse {
  success: boolean;
  document_id: number;
  status: string;
  message: string;
  error?: string;
}

export interface AnalyzeUploadedDocumentStatusResponse {
  success: boolean;
  document_id: number;
  status: 'queued' | 'extracting' | 'analyzing' | 'completed' | 'failed' | string;
  report_id?: number;
  review_id?: number;
  extraction?: AnalyzeUploadedDocumentResponse['extraction'];
  ocr_readiness?: UploadedOcrReadiness;
  progress?: {
    phase?: string;
    stage_id?: string;
    stage_name?: string;
    detail?: string;
    percent?: number;
    status?: string;
    updated_at?: string;
    preflight_status?: string;
    preflight_strategy_id?: string;
    recommended_task?: string;
    recommended_model?: string;
    privacy_risk_level?: string;
    privacy_finding_count?: number;
    instruction_risk_level?: string;
    instruction_finding_count?: number;
    completed_stages?: Array<{ stage_id?: string; stage_name?: string; completed_at?: string }>;
    [key: string]: unknown;
  };
  pipeline_preview?: Array<{
    stage_id?: string;
    stage_name?: string;
    status?: string;
    duration_ms?: number;
  }>;
  error?: string;
  message?: string;
}

export interface DeepReviewReportSummary {
  success: boolean;
  report_id: number;
  review_id: number;
  document_id: number;
  status: string;
  risk_score?: number | null;
  risk_level?: string | null;
  signing_recommendation?: string | null;
  executive_summary: string;
  summary?: {
    top_risks?: unknown[];
    priority_actions?: string[];
    missing_facts?: string[];
  };
  citation_audit?: CitationAuditResult;
  evidence_audit?: EvidenceAuditResult;
  release_decision?: ReleaseDecisionResult;
  risk_scoring?: RiskScoringResult;
  top_risks: Array<string | { title?: string; severity?: string }>;
  missing_clauses: unknown[];
  favorable_clauses: unknown[];
  next_steps: string[];
  pipeline_trace: unknown[];
  is_paid: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PipelineTraceStage {
  stage_id: string;
  stage_name: string;
  status: string;
  model?: string;
  duration_ms?: number;
  usage?: unknown;
  error?: string;
}

export interface PipelineTraceResponse {
  success: boolean;
  report_id: number | null;
  document_id: number | null;
  status: string;
  generated_at?: string | null;
  total_duration_ms: number;
  trace: PipelineTraceStage[];
}

export interface RiskScoringResult {
  schema_version?: string;
  overall_score: number;
  overall_level: string;
  risk_count: number;
  counts?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
  };
  top_risk_ids?: string[];
  score_distribution?: {
    max?: number;
    average?: number;
    top3_average?: number;
  };
  calibration?: {
    method?: string;
    weights?: Record<string, number>;
    penalties?: Record<string, number>;
  };
  risk_scores?: Array<{
    risk_id: string;
    title?: string;
    normalized_level?: string;
    score: number;
    score_level?: string;
    level_score?: number;
    severity_score?: number;
    probability_score?: number;
    citation_score?: number;
    grounding_score?: number;
    revision_score?: number;
    evidence_confidence_score?: number;
    penalty?: number;
    source_priority?: number;
    priority_rank?: number;
    explanation?: string;
  }>;
}

export interface CitationAuditResult {
  schema_version?: string;
  status?: 'pass' | 'warn' | 'fail' | string;
  score?: number;
  source_count?: number;
  citation_count?: number;
  risk_count?: number;
  cited_risk_count?: number;
  verified_source_count?: number;
  reviewable_source_count?: number;
  verified_ratio?: number;
  reviewable_ratio?: number;
  risk_citation_coverage?: number;
  source_type_counts?: Record<string, number>;
  authority_counts?: Record<string, number>;
  weak_source_ids?: string[];
  verified_source_ids?: string[];
  reviewable_source_ids?: string[];
  high_risk_without_reviewable_citation?: string[];
  high_risk_without_verified_citation?: string[];
  risks_without_any_citation?: string[];
  missing_appendix_source_ids?: string[];
  orphan_appendix_source_ids?: string[];
  duplicate_source_ids?: string[];
  recommended_actions?: string[];
  source_quality?: Array<{
    source_id?: string;
    source_name?: string;
    source_type?: string;
    authority_level?: string;
    verification_status?: string;
    confidence?: number;
    reviewable?: boolean;
    verified?: boolean;
    cited_by_risks?: string[];
  }>;
}

export interface EvidenceAuditResult {
  schema_version?: string;
  status?: 'pass' | 'warn' | 'fail' | string;
  score?: number;
  risk_count?: number;
  risk_with_evidence_count?: number;
  risk_evidence_coverage?: number;
  evidence_suggestion_count?: number;
  framework_evidence_count?: number;
  pending_fact_count?: number;
  blocking_pending_fact_count?: number;
  risks_without_evidence_plan?: string[];
  high_risk_without_evidence_plan?: string[];
  blocking_pending_fact_ids?: string[];
  duplicate_evidence_suggestions?: string[];
  recommended_actions?: string[];
  risk_evidence?: Array<{
    risk_id?: string;
    risk_level?: string;
    suggestion_count?: number;
    has_evidence_plan?: boolean;
    sample_suggestions?: string[];
  }>;
  pending_fact_items?: Array<{
    fact_id?: string;
    field?: string;
    reason?: string;
    impact?: string;
    blocking?: boolean;
  }>;
  evidence_tasks?: Array<{
    task_id?: string;
    type?: string;
    target?: unknown;
    priority?: string;
    description?: string;
  }>;
}

export interface ReleaseDecisionResult {
  schema_version?: string;
  status?: 'blocked' | 'lawyer_review_required' | 'ready_for_spot_check' | string;
  release_level?: string;
  readiness_score?: number;
  client_delivery_allowed?: boolean;
  lawyer_review_required?: boolean;
  triage_level?: string;
  blocking_reasons?: string[];
  warning_reasons?: string[];
  required_actions?: string[];
  summary?: string;
  decision_factors?: {
    quality_gate_status?: string;
    citation_audit_status?: string;
    evidence_audit_status?: string;
    risk_score?: number;
    risk_level?: string;
    critical_risk_count?: number;
    high_risk_count?: number;
  };
}

export interface DeepReviewReport {
  report_meta: {
    report_id: string;
    generated_at: string;
    document_type: string;
    jurisdiction: string;
    user_role: string;
    review_strategy_id?: string;
    review_strategy_name?: string;
    professional_grade?: string;
    overall_risk_level: string;
    risk_score?: number;
    recommendation: string;
    lawyer_review_required: boolean;
  };
  executive_summary: {
    top_risks: string[];
    priority_actions: string[];
    missing_facts: string[];
  };
  contract_summary: {
    purpose: string;
    main_obligations: string[];
    payment_terms: string;
    term: string;
    dispute_resolution: string;
  };
  risk_matrix: Array<{
    risk_id: string;
    title: string;
    risk_level: string;
    risk_type: string;
    clause_reference: string;
    probability: string;
    severity: string;
    priority: number;
    risk_score?: number;
    risk_score_rank?: number;
    risk_score_level?: string;
  }>;
  risk_items: Array<{
    risk_id: string;
    title: string;
    risk_level: string;
    risk_score?: number;
    risk_score_rank?: number;
    risk_score_level?: string;
    risk_score_explanation?: string;
    evidence_confidence_score?: number;
    original_clause: {
      clause_number: string;
      page_number: number;
      text: string;
    };
    issue_location: string;
    legal_analysis: {
      legal_relationship: string;
      applicable_rule: string;
      application_to_clause: string;
      user_impact: string;
      counterparty_argument: string;
      court_or_arbitration_focus: string;
      burden_of_proof: string;
      evidence_suggestion: string[];
    };
    citations: Array<{
      source_id: string;
      source_name: string;
      article_or_case_number: string;
      source_type: string;
      authority_level: string;
      legal_effect_note: string;
      text_excerpt_or_holding: string;
      relevance_reason: string;
      verification_status: string;
      confidence: number;
    }>;
    revision_plan: {
      delete: string[];
      add: string[];
      replace: string[];
      conservative_clause: string;
      balanced_clause: string;
      bottom_line_clause: string;
      negotiation_strategy: string;
    };
    status: string;
  }>;
  citation_audit?: CitationAuditResult;
  evidence_audit?: EvidenceAuditResult;
  release_decision?: ReleaseDecisionResult;
  risk_scoring?: RiskScoringResult;
  missing_clauses: Array<{
    name: string;
    risk: string;
    recommended_clause: string;
    citations: string[];
  }>;
  favorable_clauses: Array<{
    clause_reference: string;
    reason: string;
    keep_or_modify: string;
  }>;
  pending_facts?: Array<{
    field: string;
    reason: string;
    impact: string;
  }>;
  legal_authority_appendix: Array<{
    source_id: string;
    source_name: string;
    article_or_case_number?: string;
    source_type: string;
    authority_level: string;
    legal_effect_note: string;
    text_excerpt_or_holding?: string;
    relevance_reason?: string;
    verification_status?: string;
    confidence?: number;
    cited_by_risks: string[];
    cited_by_missing_clauses?: string[];
  }>;
  review_strategy?: {
    strategy_id: string;
    display_name: string;
    matter_type: string;
    required_fields: string[];
    review_dimensions: string[];
    evidence_checklist: string[];
    authority_queries: string[];
    report_focus: string[];
    lawyer_review_triggers: string[];
  };
  professional_review_framework?: {
    strategy_id?: string;
    document_type?: string;
    matter_type?: string;
    must_review_dimensions?: string[];
    required_fields?: string[];
    evidence_checklist?: string[];
    authority_queries?: string[];
    lawyer_review_triggers?: string[];
    report_focus?: string[];
  };
  coverage_audit?: {
    total_extracted_clauses?: number;
    clauses_selected_for_issue_model?: number;
    rule_candidate_count?: number;
    missing_clause_candidate_count?: number;
    strategy_id?: string;
    strategy_name?: string;
    strategy_required_field_count?: number;
    strategy_pending_fact_count?: number;
    coverage_note?: string;
  };
  quality_audit?: {
    quality_score?: number;
    quality_level?: string;
    warnings?: string[];
    checks?: Array<{ name: string; value: unknown }>;
    lawyer_review_required?: boolean;
    source_policy?: string;
  };
  quality_gate?: {
    status?: 'pass' | 'warn' | 'fail' | string;
    release_level?: string;
    score?: number;
    pass_count?: number;
    warn_count?: number;
    fail_count?: number;
    blocking_gate_ids?: string[];
    warning_gate_ids?: string[];
    evaluations?: Array<{
      gate_id?: string;
      status?: string;
      severity?: string;
      description?: string;
      evidence?: Record<string, unknown>;
    }>;
  };
  delivery_audit?: {
    positioning?: string;
    readiness_level?: string;
    readiness_score?: number;
    blocking_issues?: string[];
    verified_source_ratio?: number;
    reviewable_source_ratio?: number;
    risk_evidence_coverage?: number;
    blocking_pending_fact_count?: number;
    release_decision_status?: string;
    reviewable_artifacts?: string[];
    export_formats?: string[];
    risk_count?: number;
    legal_source_count?: number;
  };
  human_review_workflow?: {
    status?: string;
    triage_level?: string;
    reasons?: string[];
    review_tasks?: Array<{
      task_id?: string;
      title?: string;
      target?: unknown;
      owner_role?: string;
      status?: string;
    }>;
    handoff_note?: string;
  };
  disclaimer: string;
}

/**
 * Call the deep review AI endpoint to analyze a legal document
 */
export async function analyzeDocument(req: DeepReviewRequest): Promise<DeepReviewResponse> {
  try {
    const response = await client.apiCall.invoke({
      url: '/api/v1/deep-review/analyze',
      method: 'POST',
      data: {
        document_text: req.document_text,
        document_type: req.document_type || '合同',
        user_role: req.user_role || '甲方',
        review_goal: req.review_goal || '签署前审查',
        known_facts: req.known_facts || [],
        jurisdiction: req.jurisdiction || '中国大陆',
      },
      options: { timeout: DEEP_REVIEW_TIMEOUT_MS },
    });
    return unwrapApiResponse<DeepReviewResponse>(response);
  } catch (error: unknown) {
    return { success: false, error: apiErrorMessage(error) };
  }
}

/**
 * Start uploaded-document analysis in the backend background worker.
 */
export async function startUploadedDocumentAnalysis(
  req: AnalyzeUploadedDocumentRequest,
): Promise<AnalyzeUploadedDocumentStartResponse> {
  try {
    const response = await client.apiCall.invoke({
      url: '/api/v1/deep-review/analyze-uploaded/start',
      method: 'POST',
      data: {
        document_id: req.document_id,
        document_type: req.document_type,
        user_role: req.user_role,
        review_goal: req.review_goal || '签署前审查',
        known_facts: req.known_facts || [],
        jurisdiction: req.jurisdiction || '中国大陆',
        bucket_name: req.bucket_name || 'law-radar-docs',
        force_reextract: req.force_reextract || false,
        enable_ocr: req.enable_ocr ?? true,
      },
      options: { timeout: DEEP_REVIEW_POLL_TIMEOUT_MS },
    });
    return unwrapApiResponse<AnalyzeUploadedDocumentStartResponse>(response);
  } catch (error: unknown) {
    return {
      success: false,
      document_id: req.document_id,
      status: 'failed',
      message: '启动审查失败',
      error: apiErrorMessage(error),
    };
  }
}

/**
 * Poll backend status for an uploaded-document analysis job.
 */
export async function getUploadedDocumentAnalysisStatus(
  documentId: number,
): Promise<AnalyzeUploadedDocumentStatusResponse> {
  try {
    const response = await client.apiCall.invoke({
      url: `/api/v1/deep-review/analyze-uploaded/status/${documentId}`,
      method: 'GET',
      options: { timeout: DEEP_REVIEW_POLL_TIMEOUT_MS },
    });
    return unwrapApiResponse<AnalyzeUploadedDocumentStatusResponse>(response);
  } catch (error: unknown) {
    return {
      success: false,
      document_id: documentId,
      status: 'failed',
      error: apiErrorMessage(error),
    };
  }
}

export async function getLatestReportByDocument(
  documentId: number,
): Promise<DeepReviewReportSummary | null> {
  try {
    const response = await client.apiCall.invoke({
      url: `/api/v1/deep-review/reports/by-document/${documentId}`,
      method: 'GET',
      options: { timeout: DEEP_REVIEW_POLL_TIMEOUT_MS },
    });
    return unwrapApiResponse<DeepReviewReportSummary>(response);
  } catch {
    return null;
  }
}

export async function getLatestPipelineTrace(): Promise<PipelineTraceResponse> {
  try {
    const response = await client.apiCall.invoke({
      url: '/api/v1/deep-review/pipeline/latest',
      method: 'GET',
      options: { timeout: DEEP_REVIEW_POLL_TIMEOUT_MS },
    });
    return unwrapApiResponse<PipelineTraceResponse>(response);
  } catch {
    return {
      success: false,
      report_id: null,
      document_id: null,
      status: 'error',
      total_duration_ms: 0,
      trace: [],
    };
  }
}

/**
 * Fetch a persisted deep review report by report id.
 */
export async function getDeepReviewReport(reportId: string | number): Promise<DeepReviewResponse> {
  try {
    const response = await client.apiCall.invoke({
      url: `/api/v1/deep-review/reports/${reportId}`,
      method: 'GET',
      options: { timeout: DEEP_REVIEW_POLL_TIMEOUT_MS },
    });
    return unwrapApiResponse<DeepReviewResponse>(response);
  } catch (error: unknown) {
    return { success: false, error: apiErrorMessage(error) };
  }
}

export async function downloadDeepReviewReport(
  reportId: string | number,
  format: 'pdf' | 'doc' | 'md' | 'json',
): Promise<void> {
  const token = typeof window !== 'undefined' ? window.localStorage.getItem('token') : null;
  const fallback = `deep-review-report.${format === 'doc' ? 'doc' : format}`;
  if (!token) {
    throw new Error('登录状态已过期，请重新登录后下载');
  }

  const params = new URLSearchParams({
    download_token: token,
    t: String(Date.now()),
  });
  const url = `/api/v1/deep-review/reports/${reportId}/export/${format}?${params.toString()}`;
  const link = document.createElement('a');
  link.href = url;
  link.download = fallback;
  link.target = '_blank';
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
