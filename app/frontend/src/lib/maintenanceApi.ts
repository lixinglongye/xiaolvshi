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

export type ProductFeatureGap = {
  id: string;
  title: string;
  module: string;
  current_state: string;
  target_capability: string;
  user_segments: string[];
  impact: number;
  urgency: number;
  effort: number;
  confidence: number;
  dependencies: string[];
  evidence_paths: string[];
  next_actions: string[];
  priority_score: number;
  priority_band: string;
  completion_state: string;
};

export type ProductFeatureGapDeliveryPhase = {
  id: string;
  title: string;
  objective: string;
  gap_ids: string[];
  exit_criteria: string[];
};

export type ProductFeatureGapRadar = {
  status: string;
  summary: {
    feature_gap_count: number;
    high_priority_count: number;
    module_count: number;
    top_gap_ids: string[];
    modules: string[];
    ready_for_public_feature_claim: boolean;
    completion_policy: string[];
  };
  feature_gaps: ProductFeatureGap[];
  delivery_phases: ProductFeatureGapDeliveryPhase[];
  validation_commands: string[];
  privacy_note: string;
};

type ProductFeatureGapRadarResponse = {
  success: boolean;
  data: ProductFeatureGapRadar;
};

export type LegalResearchSource = {
  id: string;
  title: string;
  url: string;
  source_type: string;
  signal: string;
  project_application: string;
};

export type LegalResearchBacklogItem = {
  id: string;
  title: string;
  workstream: string;
  source_ids: string[];
  user_need_ids: string[];
  release_gate_links: string[];
  evidence_paths: string[];
  impact: number;
  effort: number;
  confidence: number;
  cost_sensitivity: number;
  local_run_fit: number;
  next_actions: string[];
  priority_score: number;
  priority_band: string;
};

export type LegalResearchBacklog = {
  status: string;
  method: {
    type: string;
    scoring: string;
    input_sources: LegalResearchSource[];
    limitations: string[];
  };
  summary: {
    source_count: number;
    backlog_item_count: number;
    high_priority_count: number;
    cheap_first_item_count: number;
    local_run_item_count: number;
    workstream_count: number;
    source_coverage: Record<string, number>;
  };
  backlog: LegalResearchBacklogItem[];
  workstream_plan: Array<{
    workstream: string;
    item_ids: string[];
    top_priority_score: number;
    primary_release_gates: string[];
  }>;
  next_iteration_queue: Array<{
    item_id: string;
    title: string;
    priority_score: number;
    first_action: string;
    release_gate_links: string[];
  }>;
  maintenance_actions: string[];
  privacy_note: string;
};

type LegalResearchBacklogResponse = {
  success: boolean;
  data: LegalResearchBacklog;
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

export type ContinuousUpdateLedgerEntry = {
  id: string;
  title: string;
  category: string;
  size: 'medium' | 'large';
  status: 'shipped' | 'planned';
  impact: string;
  evidence_paths: string[];
  release_gate_links: string[];
  user_need_ids: string[];
  commit_hint?: string | null;
};

export type ContinuousUpdateLedger = {
  status: string;
  goal: {
    target_continuous_hours: number;
    target_medium_large_update_count: number;
    completion_policy: string[];
  };
  summary: {
    completed_medium_large_update_count: number;
    remaining_medium_large_update_count: number;
    planned_update_count: number;
    large_update_count: number;
    medium_update_count: number;
    category_counts: Record<string, number>;
    continuous_hours_verified: number;
    continuous_hours_remaining: number;
    completion_ready: boolean;
  };
  completed_updates: ContinuousUpdateLedgerEntry[];
  next_update_queue: ContinuousUpdateLedgerEntry[];
  twenty_four_hour_evidence_requirements: string[];
  hundred_update_evidence_requirements: string[];
  low_resource_test_policy: {
    default_fixture_limit: number;
    max_parallel_requests: number;
    network_access: string;
    model_call_policy: string;
    recommended_endpoint: string;
  };
  release_guardrails: string[];
  validation_commands: string[];
};

type ContinuousUpdateLedgerResponse = {
  success: boolean;
  data: ContinuousUpdateLedger;
};

export type CaseIntakeRequirement = {
  id: string;
  title: string;
  category: string;
  required_fields: string[];
  evidence_needed: string[];
  blocks_next_step: boolean;
  reviewer_action: string;
  missing_fields: string[];
  status: string;
  blocks: boolean;
};

export type CaseIntakeCompleteness = {
  status: string;
  summary: {
    requirement_count: number;
    complete_requirement_count: number;
    missing_requirement_count: number;
    blocking_requirement_count: number;
    ready_for_document_generation: boolean;
    ready_for_lawyer_review: boolean;
  };
  requirements: CaseIntakeRequirement[];
  blocking_items: Array<{
    id: string;
    title: string;
    missing_fields: string[];
    reviewer_action: string;
  }>;
  next_actions: string[];
  validation_commands: string[];
  privacy_note: string;
};

type CaseIntakeCompletenessResponse = {
  success: boolean;
  data: CaseIntakeCompleteness;
};

export type CaseTeamRolePolicy = {
  role: string;
  purpose: string;
  default_scope: string;
  allowed_actions: string[];
  denied_actions: string[];
  approval_required_for: string[];
};

export type CaseTeamSensitiveOperation = {
  operation: string;
  allowed_roles: string[];
  audit_required: boolean;
  approval_required: boolean;
  rationale: string;
};

export type CaseTeamAccessPolicy = {
  status: string;
  policy_id: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    role_count: number;
    sensitive_operation_count: number;
    default_posture: string;
    client_scope: string;
  };
  role_matrix: CaseTeamRolePolicy[];
  sensitive_operations: CaseTeamSensitiveOperation[];
  audit_log_requirements: Array<{
    event: string;
    required_fields: string[];
    retention: string;
  }>;
  least_privilege_defaults: string[];
  privacy_and_firm_compliance: string[];
  future_api_contract: Record<string, string>;
  validation_commands: string[];
};

type CaseTeamAccessPolicyResponse = {
  success: boolean;
  data: CaseTeamAccessPolicy;
};

export type ClientDeliveryChecklistItem = {
  id: string;
  title: string;
  severity: string;
  owner: string;
  product_gap: string;
  required_evidence: string[];
  acceptance_criteria: string[];
  client_visible: boolean;
};

export type ClientDeliveryDisclosure = {
  id: string;
  audience: string;
  i18n_key: string;
  display_text: string;
  acceptance_signal: string;
  required_before_delivery: boolean;
};

export type ClientDeliveryRiskChecklist = {
  status: string;
  purpose: string;
  delivery_allowed_by_default: boolean;
  checklist_items: ClientDeliveryChecklistItem[];
  blocking_items: ClientDeliveryChecklistItem[];
  client_disclosures: ClientDeliveryDisclosure[];
  lawyer_review_items: Array<{
    id: string;
    title: string;
    must_confirm: string[];
  }>;
  displayable_statements: Record<string, ClientDeliveryDisclosure[]>;
  perspectives: Record<
    string,
    {
      summary: string;
      must_see_before_delivery?: string[];
      must_confirm_before_delivery?: string[];
    }
  >;
  audit_record_requirements: Array<{
    field: string;
    reason: string;
    retention_note: string;
  }>;
  low_resource_validation_commands: Array<{
    id: string;
    command: string;
    resource_note: string;
  }>;
  privacy_notes: string[];
  future_api: Record<string, string>;
};

type ClientDeliveryRiskChecklistResponse = {
  success: boolean;
  data: ClientDeliveryRiskChecklist;
};

export type LegalDocumentReviewGate = {
  id: string;
  label: string;
  critical: boolean;
  required_before: string[];
  review_scope: string[];
  failure_behavior: string;
};

export type LegalDocumentTemplateRow = {
  id: string;
  document_type: string;
  product_gap_closed: string;
  required_fields: string[];
  format_requirements: string[];
  pre_generation_blockers: string[];
  review_gate: LegalDocumentReviewGate;
  export_formats: string[];
  delivery_checklist: string[];
  low_resource_validation_command: string;
  privacy_notes: string[];
};

export type LegalDocumentTemplateMatrix = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    document_type_count: number;
    review_gate_required_count: number;
    blocking_condition_count: number;
    export_format_count: number;
    ready_for_delivery_count: number;
  };
  lawyer_review_gate: LegalDocumentReviewGate;
  document_types: LegalDocumentTemplateRow[];
  low_resource_validation_commands: string[];
  delivery_policy: string[];
  privacy_notes: string[];
};

type LegalDocumentTemplateMatrixResponse = {
  success: boolean;
  data: LegalDocumentTemplateMatrix;
};

export type LegalDocumentExportReadiness = {
  status: string;
  summary: {
    gate_count: number;
    passed_gate_count: number;
    blocking_gate_count: number;
    supported_export_formats: string[];
    ready_for_final_export: boolean;
  };
  format_gate: {
    id: string;
    title: string;
    observed_value: string | null;
    supported_values: string[];
    status: string;
    blocks_export: boolean;
    reviewer_action: string;
  };
  gates: Array<{
    id: string;
    title: string;
    required_field: string;
    pass_values: unknown[];
    blocking: boolean;
    reviewer_action: string;
    observed_value: unknown;
    status: string;
    blocks_export: boolean;
  }>;
  blocking_items: Array<{
    id: string;
    title: string;
    observed_value: unknown;
    reviewer_action: string;
  }>;
  audit_record_requirements: Array<{
    field: string;
    reason: string;
  }>;
  next_actions: string[];
  validation_commands: string[];
  privacy_note: string;
};

type LegalDocumentExportReadinessResponse = {
  success: boolean;
  data: LegalDocumentExportReadiness;
};

export type OcrImportReadinessPolicy = {
  status: string;
  policy_id: string;
  status_enumeration: Array<{
    status: string;
    meaning: string;
    next_action: string;
    terminal?: boolean;
  }>;
  summary: {
    ready_for_parse: boolean;
    ocr_required: boolean;
    blocked: boolean;
    manual_review_required: boolean;
    low_text_page_count: number;
    scanned_page_count: number;
    ocr_attempt_count: number;
  };
  scanned_or_low_text_detection: {
    ocr_needed: boolean;
    page_count: number;
    low_text_page_count: number;
    scanned_page_count: number;
    unreadable_page_count: number;
    low_text_pages: number[];
    scanned_pages: number[];
    unreadable_pages: number[];
  };
  retry_policy: {
    max_attempts: number;
    retryable_statuses: string[];
    backoff_seconds: number[];
    blocked_after_attempts: number;
    manual_review_after_attempts: number;
  };
  retry_state: {
    attempt_count: number;
    retry_budget_remaining: number;
    latest_failure_reason: string | null;
    retry_allowed: boolean;
    blocked_by_retry_budget: boolean;
    manual_review_recommended: boolean;
  };
  blocking_conditions: Array<{
    id: string;
    title: string;
    reviewer_action: string;
  }>;
  manual_review_conditions: Array<{
    id: string;
    title: string;
    reviewer_action: string;
  }>;
  recommended_next_actions: string[];
  audit_record_requirements: string[];
  low_resource_validation_commands: Array<{
    id: string;
    command: string;
    resource_note: string;
  }>;
  privacy_notes: string[];
  future_api: Record<string, string>;
};

type OcrImportReadinessPolicyResponse = {
  success: boolean;
  data: OcrImportReadinessPolicy;
};

export type CaseTimelineDeadlineRisk = {
  status: string;
  assessment_id: string;
  summary: {
    assessed_event_count: number;
    risk_flag_count: number;
    blocking_urgent_count: number;
    missing_fact_count: number;
    deterministic: boolean;
  };
  event_type_standards: Array<{
    event_type: string;
    display_name: string;
    purpose: string;
    required_fields: string[];
    deadline_family: string;
    default_risk_tags: string[];
  }>;
  deadline_rules_metadata: Array<{
    rule_id: string;
    applies_to_event_types: string[];
    trigger: string;
    severity: string;
    blocking: boolean;
    deterministic_input: string;
    recommended_action: string;
  }>;
  normalized_events?: Array<Record<string, unknown>>;
  event_template?: Record<string, unknown>;
  risk_flags: Array<{
    event_id: string;
    event_type: string;
    risk_type: string;
    severity: string;
    blocking: boolean;
    reason: string;
    owner_action: string;
  }>;
  blocking_urgent_items: Array<{
    event_id: string;
    event_type: string;
    reason: string;
    required_owner_action: string;
  }>;
  next_actions: string[];
  validation_commands: string[];
  privacy_note: string[] | string;
};

type CaseTimelineDeadlineRiskResponse = {
  success: boolean;
  data: CaseTimelineDeadlineRisk;
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

export type LegalFixtureResultArchiveFixtureSummary = {
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
  observed_model?: string | null;
  observed_phase?: string | null;
  observed_cost_usd?: number | null;
  recommended_next_step: string;
};

export type LegalFixtureResultArchiveRequestSummary = {
  fixture_id: string;
  phase?: string | null;
  model?: string | null;
  estimated_cost_usd?: number | null;
  http_status?: number | null;
  archived_fields: string[];
};

export type LegalFixtureResultArchive = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    fixture_count: number;
    observed_fixture_count: number;
    archived_fixture_count: number;
    request_metadata_count: number;
    dropped_raw_field_count: number;
    input_observation_count: number;
    release_decision: string;
    evidence_bundle_status: string;
    observed_cost_usd?: number | null;
  };
  archive_record: {
    id: string;
    source_endpoint: string;
    source_report_endpoint: string;
    source_bundle_endpoint: string;
    archive_fields: string[];
    excluded_fields: string[];
  };
  fixture_result_summaries: LegalFixtureResultArchiveFixtureSummary[];
  request_metadata_summaries: LegalFixtureResultArchiveRequestSummary[];
  release_claims: {
    can_claim: string[];
    claim_after_run: string[];
    must_not_claim: string[];
  };
  validation_commands: string[];
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
    research_backlog_item_count?: number;
    research_high_priority_count?: number;
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

type LegalFixtureResultArchiveResponse = {
  success: boolean;
  data: LegalFixtureResultArchive;
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

export async function getProductFeatureGapRadar(): Promise<ProductFeatureGapRadar> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/product-feature-gaps',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as ProductFeatureGapRadarResponse | ProductFeatureGapRadar;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as ProductFeatureGapRadar;
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

export async function getContinuousUpdateLedger(): Promise<ContinuousUpdateLedger> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-update-ledger',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as ContinuousUpdateLedgerResponse | ContinuousUpdateLedger;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as ContinuousUpdateLedger;
}

export async function getCaseIntakeCompleteness(): Promise<CaseIntakeCompleteness> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case-intake-completeness',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as CaseIntakeCompletenessResponse | CaseIntakeCompleteness;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as CaseIntakeCompleteness;
}

export async function getCaseTeamAccessPolicy(): Promise<CaseTeamAccessPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case-team-access-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as CaseTeamAccessPolicyResponse | CaseTeamAccessPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as CaseTeamAccessPolicy;
}

export async function getClientDeliveryRiskChecklist(): Promise<ClientDeliveryRiskChecklist> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/client-delivery-risk-checklist',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as ClientDeliveryRiskChecklistResponse | ClientDeliveryRiskChecklist;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as ClientDeliveryRiskChecklist;
}

export async function getLegalDocumentTemplateMatrix(): Promise<LegalDocumentTemplateMatrix> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-document-template-matrix',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalDocumentTemplateMatrixResponse | LegalDocumentTemplateMatrix;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalDocumentTemplateMatrix;
}

export async function getLegalDocumentExportReadiness(): Promise<LegalDocumentExportReadiness> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-document-export-readiness',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalDocumentExportReadinessResponse | LegalDocumentExportReadiness;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalDocumentExportReadiness;
}

export async function getOcrImportReadinessPolicy(): Promise<OcrImportReadinessPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/ocr-import-readiness-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as OcrImportReadinessPolicyResponse | OcrImportReadinessPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as OcrImportReadinessPolicy;
}

export async function getCaseTimelineDeadlineRisk(): Promise<CaseTimelineDeadlineRisk> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case-timeline-deadline-risk',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as CaseTimelineDeadlineRiskResponse | CaseTimelineDeadlineRisk;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as CaseTimelineDeadlineRisk;
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

export async function getLegalResearchBacklog(): Promise<LegalResearchBacklog> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/research-backlog',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalResearchBacklogResponse | LegalResearchBacklog;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalResearchBacklog;
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

export async function getLegalFixtureResultArchive(): Promise<LegalFixtureResultArchive> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/result-archive',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalFixtureResultArchiveResponse | LegalFixtureResultArchive;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalFixtureResultArchive;
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
