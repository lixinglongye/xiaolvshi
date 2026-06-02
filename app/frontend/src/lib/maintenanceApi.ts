import { client } from '@/lib/api';

export type MaintenanceLanguage = 'en' | 'zh';

export type MaintenanceSignal = {
  id: string;
  category: string;
  title: string;
  description: string;
  responsibility: string;
  cadence: string;
  evidence_paths: string[];
  weight: number;
};

export type MaintenanceEvidenceProfile = {
  project: {
    name: string;
    display_name: string;
    repository_url: string;
    domain: string;
  };
  maintainer_role: string;
  evidence_score: number;
  active_maintenance_summary: string;
  form_answer: string;
  signals: MaintenanceSignal[];
  responsibilities: string[];
  release_management: {
    current_stage: string;
    release_readiness_controls: string[];
    client_delivery_policy: string;
  };
  application_guardrails: string[];
};

type MaintenanceEvidenceResponse = {
  success: boolean;
  data: MaintenanceEvidenceProfile;
};

export type ReleaseValidationState = 'pass' | 'fail' | 'not_run' | 'waived';

export type ReleaseCheck = {
  id: string;
  title: string;
  category: string;
  required: boolean;
  owner: string;
  evidence_paths: string[];
  validation_command?: string | null;
  manual_note?: string | null;
  validation_state: ReleaseValidationState;
  blocks_release: boolean;
};

export type ReleaseReadinessResult = {
  status: string;
  release_allowed: boolean;
  required_check_count: number;
  passed_or_waived_required_count: number;
  blocking_check_ids: string[];
  failed_check_ids: string[];
  not_run_check_ids: string[];
  checks: ReleaseCheck[];
  summary: string;
};

export type ReleaseValidationCommand = {
  check_id: string;
  command: string;
};

type ReleaseReadinessResponse = {
  success: boolean;
  data: ReleaseReadinessResult;
  validation_commands: ReleaseValidationCommand[];
};

export type LegalKnowledgeAudit = {
  status: string;
  score: number;
  seed_path: string;
  schema_version?: string;
  generated_at?: string;
  age_days?: number | null;
  max_age_days: number;
  record_count: number;
  duplicate_source_ids: string[];
  missing_required_fields: Array<{
    index: number;
    source_id: string;
    fields: string[];
  }>;
  reviewable_ratio: number;
  verified_count: number;
  source_type_counts: Record<string, number>;
  authority_level_counts: Record<string, number>;
  topic_counts: Record<string, number>;
  missing_critical_topics: string[];
  recommended_actions: string[];
};

type LegalKnowledgeAuditResponse = {
  success: boolean;
  data: LegalKnowledgeAudit;
};

export type LegalRagEvaluationPolicy = {
  status_thresholds: Record<string, number>;
  metric_weights: Record<string, number>;
  required_metrics: string[];
  blocking_conditions: string[];
  evaluation_inputs: string[];
};

type LegalRagEvaluationPolicyResponse = {
  success: boolean;
  data: LegalRagEvaluationPolicy;
};

export async function getMaintenanceEvidence(language: MaintenanceLanguage): Promise<MaintenanceEvidenceProfile> {
  const resp = await client.apiCall.invoke({
    url: `/api/v1/maintenance/oss-evidence?language=${language}`,
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as MaintenanceEvidenceResponse | MaintenanceEvidenceProfile;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as MaintenanceEvidenceProfile;
}

export async function getReleaseReadiness(): Promise<ReleaseReadinessResponse> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/release-readiness',
    method: 'GET',
  });
  return (resp?.data ?? resp) as ReleaseReadinessResponse;
}

export async function getLegalKnowledgeAudit(): Promise<LegalKnowledgeAudit> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/legal-knowledge/audit',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalKnowledgeAuditResponse | LegalKnowledgeAudit;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalKnowledgeAudit;
}

export async function getLegalRagEvaluationPolicy(): Promise<LegalRagEvaluationPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/legal-knowledge/rag-evaluation-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalRagEvaluationPolicyResponse | LegalRagEvaluationPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalRagEvaluationPolicy;
}
