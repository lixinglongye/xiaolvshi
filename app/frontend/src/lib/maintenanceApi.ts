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

export type LegalFixturePromptPlan = {
  fixture_id: string;
  title: string;
  matter_type: string;
  expected_route: string;
  recommended_task: string;
  recommended_model: string;
  recommended_model_cost_tier?: string | null;
  cheap_trial_model: string;
  cheap_trial_cost_tier?: string | null;
  prompt_tokens_estimate: number;
  completion_tokens_budget: number;
  estimated_request_cost_usd?: number | null;
  request_parameters: {
    temperature: number;
    max_tokens: number;
    response_format: {
      type: string;
    };
  };
  system_prompt: string;
  user_prompt: string;
  output_schema: {
    type: string;
    required: string[];
    properties: Record<string, unknown>;
  };
  follow_up_endpoints: string[];
};

export type LegalFixturePromptPack = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    fixture_count: number;
    priced_prompt_count: number;
    estimated_total_request_cost_usd: number;
    unknown_model_count: number;
    cheap_trial_model: string;
  };
  prompts: LegalFixturePromptPlan[];
  warning_fixture_ids: string[];
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalFixtureRunStep = {
  step_id: string;
  order: number;
  phase: string;
  batch_id: string;
  fixture_id: string;
  title: string;
  task: string;
  model: string;
  model_cost_tier?: string | null;
  endpoint_path: string;
  run_condition: string;
  prompt_tokens_estimate: number;
  completion_tokens_budget: number;
  estimated_request_cost_usd?: number | null;
  max_parallel_requests: number;
  smoke_route: string;
  observation_target: string;
  improvement_target: string;
  required_response_fields: string[];
  command_hint: string;
};

export type LegalFixtureRunBatch = {
  batch_id: string;
  phase: string;
  task: string;
  model: string;
  model_cost_tier?: string | null;
  step_ids: string[];
  fixture_ids: string[];
  max_parallel_requests: number;
  estimated_batch_cost_usd?: number | null;
  run_after: string;
};

export type LegalFixtureRunPlan = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    fixture_count: number;
    batch_count: number;
    total_step_count: number;
    cheap_first_step_count: number;
    escalation_step_count: number;
    priced_step_count: number;
    unknown_model_step_count: number;
    estimated_min_cost_usd: number;
    estimated_max_cost_usd: number;
    max_parallel_requests: number;
  };
  batches: LegalFixtureRunBatch[];
  steps: LegalFixtureRunStep[];
  warning_step_ids: string[];
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalFixtureLocalRunPackageRequestFile = {
  file_name: string;
  fixture_id: string;
  title: string;
  phase: string;
  task: string;
  model: string;
  model_cost_tier?: string | null;
  endpoint_url: string;
  body: Record<string, unknown>;
  prompt_tokens_estimate: number;
  completion_tokens_budget: number;
  estimated_request_cost_usd?: number | null;
  response_capture: {
    gateway_json_path: string;
    normalized_observation_path: string;
    raw_output_policy: string;
  };
};

export type LegalFixtureLocalRunPackageStep = {
  order: number;
  step_id: string;
  fixture_id: string;
  title: string;
  run_condition: string;
  max_parallel_requests: number;
  request_file_name: string;
  endpoint_url: string;
  command_templates: {
    powershell: string;
    curl: string;
  };
  next_local_action: string;
};

export type LegalFixtureLocalRunPackage = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    requested_fixture_limit: number;
    selected_fixture_count: number;
    request_file_count: number;
    run_step_count: number;
    max_parallel_requests: number;
    estimated_cheap_first_cost_usd: number;
    unknown_cost_request_count: number;
    follow_up_endpoint_count: number;
  };
  environment: {
    required_env: string[];
    base_url_rule: string;
    secret_policy: string;
  };
  request_files: LegalFixtureLocalRunPackageRequestFile[];
  run_steps: LegalFixtureLocalRunPackageStep[];
  observation_template: Record<string, unknown>;
  run_report_payload_template: {
    observations: Record<string, unknown>;
    run_metadata: Record<string, unknown>;
  };
  follow_up_endpoints: string[];
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  validation_commands: string[];
  privacy_note: string;
};

export type LegalFixtureResponseNormalizerTemplate = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  payload_shape: Record<string, unknown>;
  validation_command: string;
};

export type LegalFixtureResponseNormalizer = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    response_count: number;
    normalized_observation_count: number;
    run_metadata_count: number;
    known_fixture_count: number;
    parsed_json_content_count: number;
    redacted_response_count: number;
    blocking_check_count: number;
    warning_check_count: number;
  };
  observations: Record<string, unknown>;
  run_report_payload: {
    observations: Record<string, unknown>;
    run_metadata: Record<string, unknown>;
  };
  response_summaries: Array<{
    fixture_id: string;
    known_fixture: boolean;
    http_status?: number | null;
    model: string;
    route?: string | null;
    content_length: number;
    json_content_parsed: boolean;
    redacted: boolean;
    status: string;
  }>;
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalFixtureRunReportRow = {
  fixture_id: string;
  title: string;
  smoke_status: string;
  score: number;
  observed_route: string;
  expected_routes: string[];
  matched_signal_count: number;
  missing_signal_count: number;
  missing_task_count: number;
  high_priority_action_count: number;
  cheap_first_step_id?: string | null;
  cheap_first_model?: string | null;
  escalation_step_id?: string | null;
  escalation_model?: string | null;
  observed_model?: string | null;
  observed_phase?: string | null;
  observed_cost_usd?: number | null;
  recommended_next_step: string;
  missing_signals: string[];
  missing_tasks: string[];
};

export type LegalFixtureRunReport = {
  status: string;
  release_decision: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    fixture_count: number;
    observed_fixture_count: number;
    passed_fixture_count: number;
    warning_fixture_count: number;
    failed_fixture_count: number;
    not_run_fixture_count: number;
    escalation_required_count: number;
    high_priority_improvement_count: number;
    observed_request_count: number;
    observed_cost_usd?: number | null;
    cheap_first_estimated_cost_usd: number;
    worst_case_estimated_cost_usd: number;
  };
  fixture_reports: LegalFixtureRunReportRow[];
  escalation_fixture_ids: string[];
  improvement_summary: LegalFixtureImprovementPlan['summary'];
  run_evidence_template: {
    source_endpoint: string;
    inputs_to_archive: string[];
    validation_command: string;
    expected_cheap_first_cost_usd: number;
    expected_worst_case_cost_usd: number;
  };
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalFixtureModelCandidate = {
  role: string;
  model: string;
  known_model: boolean;
  provider: string;
  family: string;
  status: string;
  cost_tier: string;
  latency_tier: string;
  context_window_tokens?: number | null;
  input_usd_per_million_tokens?: number | null;
  output_usd_per_million_tokens?: number | null;
  over_fixture_budget: boolean;
  requires_operator_review: boolean;
  source: string;
  trigger: string;
};

export type LegalFixtureModelMatrixRow = {
  fixture_id: string;
  title: string;
  task: string;
  smoke_route: string;
  status: string;
  budget_mode: string;
  max_cost_tier: string;
  runtime_default_model?: string | null;
  capability_recommended_model?: string | null;
  candidate_ladder: LegalFixtureModelCandidate[];
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  recommended_action: string;
};

export type LegalFixtureModelMatrix = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    fixture_count: number;
    pass_count: number;
    warning_count: number;
    cheap_first_candidate_count: number;
    premium_candidate_count: number;
    operator_review_candidate_count: number;
    unknown_candidate_count: number;
  };
  fixtures: LegalFixtureModelMatrixRow[];
  warning_fixture_ids: string[];
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalFixtureEvidenceBundle = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    component_count: number;
    blocking_component_count: number;
    warning_component_count: number;
    not_run_component_count: number;
    fixture_count: number;
    prompt_count: number;
    cheap_first_candidate_count: number;
    observed_fixture_count: number;
    public_sampler_source_count: number;
    release_decision: string;
    estimated_cheap_first_cost_usd: number;
    estimated_worst_case_cost_usd: number;
  };
  components: Array<{
    id: string;
    status: string;
    endpoint: string;
  }>;
  artifacts: Array<{
    id: string;
    title: string;
    evidence_paths: string[];
    archive_fields: string[];
  }>;
  validation_commands: string[];
  release_claims: {
    can_claim: string[];
    claim_after_run: string[];
    must_not_claim: string[];
  };
  recommended_actions: string[];
  privacy_note: string;
};

export type LegalPublicBenchmarkSampler = {
  status: string;
  method: {
    type: string;
    notes: string[];
    research_basis: Array<{
      id: string;
      url: string;
      use: string;
    }>;
  };
  summary: {
    source_count: number;
    sampling_ready_source_count: number;
    license_review_required_source_count: number;
    catalog_only_source_count: number;
    local_fixture_count: number;
    benchmark_case_count: number;
    max_samples_per_source: number;
    max_local_sample_chars: number;
  };
  source_plans: Array<{
    source_id: string;
    title: string;
    url: string;
    source_type: string;
    priority: string;
    resource_profile: string;
    sample_strategy: string;
    local_fixture_ids: string[];
    benchmark_case_ids: string[];
    validation_targets: string[];
    license_gate: string;
    task_fit: string[];
    source_license_note: string;
    source_size_note: string;
    sampling_state: string;
    max_samples: number;
    max_sample_chars: number;
    download_policy: string;
    recommended_action: string;
  }>;
  sampling_batches: Array<{
    id: string;
    source_ids: string[];
    local_fixture_ids: string[];
    target_endpoint: string;
    run_condition: string;
  }>;
  resource_policy: {
    default_mode: string;
    network_access: string;
    max_samples_per_source: number;
    max_local_sample_chars: number;
    storage_policy: string;
  };
  validation_commands: string[];
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

type LegalFixturePromptPackResponse = {
  success: boolean;
  data: LegalFixturePromptPack;
};

type LegalFixtureRunPlanResponse = {
  success: boolean;
  data: LegalFixtureRunPlan;
};

type LegalFixtureLocalRunPackageResponse = {
  success: boolean;
  data: LegalFixtureLocalRunPackage;
};

type LegalFixtureResponseNormalizerTemplateResponse = {
  success: boolean;
  data: LegalFixtureResponseNormalizerTemplate;
};

type LegalFixtureResponseNormalizerResponse = {
  success: boolean;
  data: LegalFixtureResponseNormalizer;
};

type LegalFixtureRunReportResponse = {
  success: boolean;
  data: LegalFixtureRunReport;
};

type LegalFixtureModelMatrixResponse = {
  success: boolean;
  data: LegalFixtureModelMatrix;
};

type LegalFixtureEvidenceBundleResponse = {
  success: boolean;
  data: LegalFixtureEvidenceBundle;
};

type LegalPublicBenchmarkSamplerResponse = {
  success: boolean;
  data: LegalPublicBenchmarkSampler;
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

export async function getLegalPublicBenchmarkSampler(): Promise<LegalPublicBenchmarkSampler> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/public-sampler',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalPublicBenchmarkSamplerResponse | LegalPublicBenchmarkSampler;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalPublicBenchmarkSampler;
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

export async function getLegalFixturePromptPack(): Promise<LegalFixturePromptPack> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/prompt-pack',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixturePromptPackResponse | LegalFixturePromptPack;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixturePromptPack;
}

export async function getLegalFixtureRunPlan(): Promise<LegalFixtureRunPlan> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-run-plan',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureRunPlanResponse | LegalFixtureRunPlan;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureRunPlan;
}

export async function getLegalFixtureLocalRunPackage(): Promise<LegalFixtureLocalRunPackage> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/local-run-package',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureLocalRunPackageResponse | LegalFixtureLocalRunPackage;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureLocalRunPackage;
}

export async function getLegalFixtureResponseNormalizerTemplate(): Promise<LegalFixtureResponseNormalizerTemplate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/local-response-normalizer',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as
    | LegalFixtureResponseNormalizerTemplateResponse
    | LegalFixtureResponseNormalizerTemplate;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureResponseNormalizerTemplate;
}

export async function normalizeLegalFixtureResponse(payload: Record<string, unknown>): Promise<LegalFixtureResponseNormalizer> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/local-response-normalizer',
    method: 'POST',
    data: payload,
  });
  const response = (resp?.data ?? resp) as LegalFixtureResponseNormalizerResponse | LegalFixtureResponseNormalizer;
  if ('success' in response && 'data' in response) {
    return response.data;
  }
  return response as LegalFixtureResponseNormalizer;
}

export async function getLegalFixtureRunReport(): Promise<LegalFixtureRunReport> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-run-report',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureRunReportResponse | LegalFixtureRunReport;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureRunReport;
}

export async function getLegalFixtureModelMatrix(): Promise<LegalFixtureModelMatrix> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-model-matrix',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureModelMatrixResponse | LegalFixtureModelMatrix;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureModelMatrix;
}

export async function getLegalFixtureEvidenceBundle(): Promise<LegalFixtureEvidenceBundle> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureEvidenceBundleResponse | LegalFixtureEvidenceBundle;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureEvidenceBundle;
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
