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

export type UserNeed = {
  id: string;
  title: string;
  category: string;
  user_segments: string[];
  pain_point: string;
  product_response: string;
  impact: number;
  effort: number;
  confidence: number;
  source_ids: string[];
  evidence_paths: string[];
  release_gate_links: string[];
  next_actions: string[];
  priority_score: number;
  priority_band: string;
};

export type UserNeedsRadar = {
  status: string;
  method: {
    scoring: string;
    input_sources: Array<{
      id: string;
      title: string;
      url: string;
      signal: string;
    }>;
    limitations: string[];
  };
  summary: {
    need_count: number;
    top_need_ids: string[];
    high_priority_count: number;
    source_coverage: Record<string, number>;
  };
  needs: UserNeed[];
  roadmap: Array<{
    phase: string;
    focus_need_ids: string[];
    exit_criteria: string[];
  }>;
  maintenance_actions: string[];
};

type UserNeedsRadarResponse = {
  success: boolean;
  data: UserNeedsRadar;
};

export type FeedbackRoadmapRule = {
  id: string;
  need_id: string;
  triage_rule_ids: string[];
  labels: string[];
  keywords: string[];
  reason: string;
};

export type FeedbackRoadmapCatalog = {
  status: string;
  rule_count: number;
  mapped_need_count: number;
  mapped_need_ids: string[];
  rules: FeedbackRoadmapRule[];
  coverage: {
    radar_need_count: number;
    unmapped_need_ids: string[];
  };
  maintenance_actions: string[];
};

type FeedbackRoadmapCatalogResponse = {
  success: boolean;
  data: FeedbackRoadmapCatalog;
};

export type LegalReviewBenchmarkCaseResult = {
  case_id: string;
  title: string;
  status: string;
  score: number;
  expected_route: string;
  metric_scores: Record<string, number>;
  missing_metrics: string[];
  release_gate_links: string[];
};

export type LegalReviewFixtureTemplateRow = {
  id: string;
  title: string;
  matter_type: string;
  linked_case_ids: string[];
  expected_routes: string[];
  expected_tasks: string[];
  expected_signals: string[];
  input_excerpt: string;
  observation_template: {
    output_text: string;
    route: string;
    structured_outputs: Record<string, unknown>;
  };
};

export type LegalReviewFixtureSmokeResult = {
  fixture_id: string;
  title: string;
  status: string;
  score: number;
  metric_scores: Record<string, number>;
  matched_signals: string[];
  missing_signals: string[];
  matched_tasks: string[];
  missing_tasks: string[];
  expected_routes: string[];
  observed_route: string;
};

export type LegalReviewFixtureSmoke = {
  status: string;
  score: number;
  fixture_count: number;
  passed_fixture_count: number;
  warning_fixture_count: number;
  failed_fixture_count: number;
  not_run_fixture_count: number;
  blocking_fixture_ids: string[];
  recommended_actions: string[];
  fixture_results: LegalReviewFixtureSmokeResult[];
  template: {
    status: string;
    method: {
      type: string;
      score_formula: string;
      pass_thresholds: Record<string, number>;
      local_resource_policy: string;
    };
    fixture_count: number;
    fixtures: LegalReviewFixtureTemplateRow[];
    default_observations: Record<
      string,
      {
        output_text: string;
        route: string;
        structured_outputs: Record<string, unknown>;
      }
    >;
  };
};

export type LegalFixtureImprovementAction = {
  id: string;
  label: string;
  label_type: 'signal' | 'task_output' | string;
  priority: 'high' | 'medium' | string;
  report_section: string;
  schema_target: string;
  prompt_clause: string;
  validation_hint: string;
  fixture_id: string;
  fixture_title: string;
  current_fixture_score: number;
};

export type LegalFixtureImprovementPlan = {
  status: string;
  smoke_status: string;
  score: number;
  summary: {
    fixture_count: number;
    affected_fixture_count: number;
    action_count: number;
    high_priority_action_count: number;
    missing_signal_count: number;
    missing_task_output_count: number;
  };
  actions: LegalFixtureImprovementAction[];
  grouped_actions: Record<string, LegalFixtureImprovementAction[]>;
  smoke_result: LegalReviewFixtureSmoke;
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalReviewBenchmark = {
  status: string;
  score: number;
  case_count: number;
  passed_case_count: number;
  warning_case_count: number;
  failed_case_count: number;
  not_run_case_count: number;
  blocking_case_ids: string[];
  recommended_actions: string[];
  case_results: LegalReviewBenchmarkCaseResult[];
  suite: {
    status: string;
    case_count: number;
    task_family_counts: Record<string, number>;
    required_metric_counts: Record<string, number>;
    public_source_count?: number;
    document_fixture_count?: number;
    public_sources?: Array<{
      id: string;
      title: string;
      url: string;
      source_type: string;
      task_fit: string[];
      import_policy: string;
      size_note: string;
      license_note: string;
    }>;
    document_fixtures?: Array<{
      id: string;
      title: string;
      matter_type: string;
      linked_case_ids: string[];
      sample_text: string;
      expected_tasks: string[];
      expected_signals: string[];
      source_relation: string;
      license_note: string;
    }>;
    fixture_smoke_template?: LegalReviewFixtureSmoke['template'];
    cases: Array<{
      id: string;
      title: string;
      matter_type: string;
      task_family: string;
      user_segment: string;
      scenario: string;
      expected_route: string;
      expected_outputs: string[];
      required_metrics: string[];
      benchmark_sources: string[];
      release_gate_links: string[];
    }>;
  };
};

type LegalReviewBenchmarkResponse = {
  success: boolean;
  data: LegalReviewBenchmark;
};

type LegalReviewFixtureSmokeResponse = {
  success: boolean;
  data: LegalReviewFixtureSmoke;
};

type LegalFixtureImprovementPlanResponse = {
  success: boolean;
  data: LegalFixtureImprovementPlan;
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

export async function getUserNeedsRadar(): Promise<UserNeedsRadar> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/user-needs',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as UserNeedsRadarResponse | UserNeedsRadar;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as UserNeedsRadar;
}

export async function getFeedbackRoadmapCatalog(): Promise<FeedbackRoadmapCatalog> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/feedback-roadmap',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as FeedbackRoadmapCatalogResponse | FeedbackRoadmapCatalog;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as FeedbackRoadmapCatalog;
}

export async function getLegalReviewBenchmark(): Promise<LegalReviewBenchmark> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalReviewBenchmarkResponse | LegalReviewBenchmark;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalReviewBenchmark;
}

export async function getLegalReviewFixtureSmoke(): Promise<LegalReviewFixtureSmoke> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-smoke',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalReviewFixtureSmokeResponse | LegalReviewFixtureSmoke;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalReviewFixtureSmoke;
}

export async function getLegalFixtureImprovementPlan(): Promise<LegalFixtureImprovementPlan> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-improvements',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureImprovementPlanResponse | LegalFixtureImprovementPlan;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureImprovementPlan;
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
