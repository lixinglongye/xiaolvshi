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

export type UserNeedBenchmarkCoverageRow = {
  need_id: string;
  title: string;
  category: string;
  priority_band: string;
  priority_score: number;
  linked_benchmark_case_ids: string[];
  linked_fixture_ids: string[];
  linked_document_fixture_ids: string[];
  linked_public_source_ids: string[];
  linked_public_sampling_batch_ids: string[];
  public_sampling_states: Record<string, string>;
  public_benchmark_status: string;
  linked_calibration_task_ids: string[];
  linked_calibration_release_gates: string[];
  calibration_status: string;
  calibration_decisions: Record<string, string>;
  linked_backlog_item_ids: string[];
  linked_release_gates: string[];
  coverage_status: string;
  gap_reasons: string[];
  next_actions: string[];
};

export type UserNeedBenchmarkCoverage = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    need_count: number;
    high_priority_need_count: number;
    covered_need_count: number;
    partial_need_count: number;
    gap_need_count: number;
    high_priority_gap_count: number;
    benchmark_case_count: number;
    synthetic_fixture_count: number;
    document_fixture_count: number;
    research_backlog_item_count: number;
    public_benchmark_source_count: number;
    public_benchmark_ready_source_count: number;
    public_benchmark_license_review_required_source_count: number;
    public_benchmark_catalog_only_source_count: number;
    public_benchmark_mapped_need_count: number;
    public_benchmark_ready_need_count: number;
    public_benchmark_license_review_required_need_count: number;
    public_sampler_endpoint: string;
    public_sampler_network_access: string;
    cheap_first_calibration_status: string;
    cheap_first_calibration_task_count: number;
    cheap_first_calibration_mapped_need_count: number;
    cheap_first_calibration_pass_need_count: number;
    cheap_first_calibration_attention_need_count: number;
    local_run_only: boolean;
    model_calls: string;
    network_access: string;
  };
  coverage_rows: UserNeedBenchmarkCoverageRow[];
  gap_need_ids: string[];
  high_priority_gap_need_ids: string[];
  public_benchmark_gap_need_ids: string[];
  calibration_attention_need_ids: string[];
  source_summaries: {
    public_sampler: {
      source_count: number;
      sampling_ready_source_count: number;
      license_review_required_source_count: number;
      catalog_only_source_count: number;
      local_fixture_count: number;
      benchmark_case_count: number;
      max_samples_per_source: number;
      max_local_sample_chars: number;
    };
    public_sampler_resource_policy: {
      default_mode: string;
      network_access: string;
      max_samples_per_source: number;
      max_local_sample_chars: number;
      storage_policy: string;
    };
    cheap_first_calibration: {
      task_count: number;
      pass_count: number;
      warn_count: number;
      fail_count: number;
      cheap_first_retained_count: number;
      balanced_precheck_count: number;
      premium_exception_count: number;
      fixture_count: number;
      observed_fixture_count: number;
      selector_scenario_count: number;
      cost_guardrail_status: string;
      estimated_savings_ratio: number | null;
      external_research_source_count: number;
      research_mapped_task_count: number;
      forbidden_payload_field_count: number;
      secret_like_value_count: number;
      newapi_called: boolean;
      raw_payload_echoed: boolean;
    };
  };
  recommended_actions: string[];
  privacy_boundary: {
    returns_fixture_snippets: boolean;
    returns_raw_benchmark_samples: boolean;
    returns_public_benchmark_text: boolean;
    returns_raw_model_output: boolean;
    returns_calibration_payloads: boolean;
    returns_user_feedback_text: boolean;
    external_dataset_downloads: boolean;
    model_calls: boolean;
    source: string;
  };
  validation_commands: string[];
};

type UserNeedBenchmarkCoverageResponse = {
  success: boolean;
  data: UserNeedBenchmarkCoverage;
};

export type UserNeedGeminiRouteCoverageRow = {
  id: string;
  need_id: string;
  title: string;
  category: string;
  priority_band: string;
  priority_score: number;
  benchmark_coverage_status: string;
  public_benchmark_status: string;
  calibration_status: string;
  route_coverage_status: string;
  linked_calibration_task_ids: string[];
  linked_route_tasks: string[];
  route_task_source: string;
  linked_default_models: string[];
  route_modes: string[];
  cost_tiers: string[];
  cheap_first_route_count: number;
  balanced_route_count: number;
  premium_exception_route_count: number;
  high_frequency_route_ready: boolean;
  default_allowed_without_review: boolean;
  calibration_decisions: Record<string, string>;
  blocked_reason_codes: string[];
  review_reason_codes: string[];
  next_actions: string[];
  release_gate_links: string[];
};

export type UserNeedGeminiRouteCoverage = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    need_count: number;
    high_priority_need_count: number;
    ready_need_count: number;
    review_required_need_count: number;
    blocked_need_count: number;
    unmapped_need_count: number;
    high_priority_route_protected_count: number;
    cheap_first_route_need_count: number;
    balanced_route_need_count: number;
    premium_exception_need_count: number;
    source_user_need_coverage_status: string;
    source_route_preflight_status: string;
    source_calibration_status: string;
    official_source_count: number;
    route_task_count: number;
    model_calls: string;
    network_access: string;
    configuration_written: boolean;
    raw_text_returned: boolean;
  };
  coverage_rows: UserNeedGeminiRouteCoverageRow[];
  blocked_need_ids: string[];
  review_need_ids: string[];
  unmapped_need_ids: string[];
  recommended_actions: string[];
  source_summaries: {
    user_need_benchmark_coverage: UserNeedBenchmarkCoverage['summary'];
    gemini_route_preflight: {
      official_source_count: number;
      route_task_count: number;
      cheap_first_route_count: number;
      balanced_route_count: number;
      premium_exception_count: number;
      model_called: boolean;
      gateway_called: boolean;
      network_called: boolean;
      configuration_written: boolean;
      credentials_included: boolean;
      raw_payload_echoed: boolean;
    };
    cheap_first_calibration: UserNeedBenchmarkCoverage['source_summaries']['cheap_first_calibration'];
  };
  source_boundaries: {
    coverage_endpoint: string;
    route_preflight_endpoint: string;
    official_source_urls: string[];
    uses_public_benchmark_metadata: boolean;
    imports_public_benchmark_samples: boolean;
    uses_route_preflight_metadata: boolean;
    changes_default_routes: boolean;
  };
  privacy_boundary: {
    metadata_only: boolean;
    returns_raw_benchmark_samples: boolean;
    returns_public_benchmark_text: boolean;
    returns_fixture_snippets: boolean;
    returns_calibration_payloads: boolean;
    returns_route_payloads: boolean;
    returns_raw_legal_text: boolean;
    returns_prompts: boolean;
    returns_raw_model_output: boolean;
    returns_user_feedback_text: boolean;
    returns_credentials: boolean;
    returns_emails: boolean;
    model_calls: boolean;
    gateway_calls: boolean;
    network_access: boolean;
    configuration_written: boolean;
  };
  claim_boundary: {
    claims_24h_completion: boolean;
    claims_public_benchmark_scores: boolean;
    claims_live_gateway_execution: boolean;
    claims_production_quality: boolean;
    claims_default_route_changed: boolean;
    allowed_claim: string;
  };
  validation_commands: string[];
};

type UserNeedGeminiRouteCoverageResponse = {
  success: boolean;
  data: UserNeedGeminiRouteCoverage;
};

export type UserNeedImplementationPriorityQueueItem = {
  id: string;
  need_id: string;
  title: string;
  category: string;
  priority_band: string;
  user_need_priority_score: number;
  queue_priority_score: number;
  coverage_status: string;
  public_benchmark_status: string;
  calibration_status: string;
  action_status: string;
  implementation_tracks: string[];
  blocker_codes: string[];
  review_reason_codes: string[];
  linked_benchmark_case_ids: string[];
  linked_fixture_ids: string[];
  linked_public_source_ids: string[];
  linked_calibration_task_ids: string[];
  linked_backlog_item_ids: string[];
  next_actions: string[];
  release_gate_links: string[];
};

export type UserNeedImplementationPriorityQueue = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    queue_item_count: number;
    ready_action_count: number;
    review_required_action_count: number;
    blocked_action_count: number;
    high_priority_item_count: number;
    public_benchmark_review_item_count: number;
    calibration_attention_item_count: number;
    source_coverage_status: string;
    source_high_priority_gap_count: number;
    source_public_benchmark_license_review_required_need_count: number;
    source_cheap_first_calibration_attention_need_count: number;
    local_run_only: boolean;
    network_access: string;
    model_calls: string;
    external_dataset_downloads: boolean;
    raw_text_returned: boolean;
  };
  queue_items: UserNeedImplementationPriorityQueueItem[];
  blocked_need_ids: string[];
  review_need_ids: string[];
  ready_need_ids: string[];
  recommended_actions: string[];
  source_boundary: {
    coverage_endpoint: string;
    public_sampler_endpoint: string;
    uses_public_benchmark_metadata: boolean;
    imports_public_benchmark_samples: boolean;
    uses_raw_user_feedback: boolean;
    uses_raw_legal_text: boolean;
    uses_model_outputs: boolean;
    uses_credentials: boolean;
  };
  privacy_boundary: {
    returns_raw_benchmark_samples: boolean;
    returns_public_benchmark_text: boolean;
    returns_fixture_snippets: boolean;
    returns_calibration_payloads: boolean;
    returns_raw_model_output: boolean;
    returns_user_feedback_text: boolean;
    external_dataset_downloads: boolean;
    model_calls: boolean;
    network_access: boolean;
  };
  validation_commands: string[];
};

type UserNeedImplementationPriorityQueueResponse = {
  success: boolean;
  data: UserNeedImplementationPriorityQueue;
};

export type FrontendUiRegressionCommandGate = {
  id: string;
  command: string;
  purpose: string;
  required: boolean;
  script_present: boolean;
  ready: boolean;
  gap_reason: string;
};

export type FrontendUiRegressionPageRow = {
  route: string;
  page: string;
  source_path: string;
  source_exists: boolean;
  risk_area: string;
  protected_panels: string[];
  covered_by: string[];
  ready_cover: string[];
  missing_cover: string[];
  missing_automation: string[];
  status: string;
};

export type FrontendUiRegressionFailureMode = {
  id: string;
  page: string;
  current_control: string;
  regression_target: string;
};

export type FrontendUiRegressionGate = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    page_count: number;
    command_gate_count: number;
    ready_command_gate_count: number;
    required_command_gate_count: number;
    missing_required_command_count: number;
    protected_panel_count: number;
    missing_page_automation_count: number;
    manual_browser_smoke_required: boolean;
    model_calls: string;
    network_access: string;
  };
  command_gates: FrontendUiRegressionCommandGate[];
  page_rows: FrontendUiRegressionPageRow[];
  failure_modes: FrontendUiRegressionFailureMode[];
  recommended_actions: string[];
  privacy_boundary: {
    reads_package_script_names: boolean;
    reads_page_source_paths: boolean;
    returns_source_code: boolean;
    returns_raw_browser_storage: boolean;
    returns_raw_model_output: boolean;
    returns_credentials: boolean;
  };
  validation_commands: string[];
};

type FrontendUiRegressionGateResponse = {
  success: boolean;
  data: FrontendUiRegressionGate;
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

export type LegalAdoptionResearchSource = {
  id: string;
  title: string;
  url: string;
  source_type: string;
  signal: string;
  local_interpretation: string;
};

export type LegalAdoptionResearchBridgeAction = {
  id: string;
  title: string;
  product_area: string;
  source_ids: string[];
  user_need_ids: string[];
  product_gap_ids: string[];
  release_gate_links: string[];
  evidence_paths: string[];
  impact: number;
  urgency: number;
  effort: number;
  confidence: number;
  low_cost_fit: number;
  next_actions: string[];
  validation_commands: string[];
  priority_score: number;
  priority_band: string;
};

export type LegalAdoptionResearchBridge = {
  status: string;
  method: {
    type: string;
    scoring: string;
    input_sources: LegalAdoptionResearchSource[];
    limitations: string[];
  };
  summary: {
    source_count: number;
    action_count: number;
    high_priority_count: number;
    cheap_first_action_count: number;
    governance_action_count: number;
    legal_benchmark_action_count: number;
    product_area_counts: Record<string, number>;
    research_digest_signal_count: number;
    known_need_count: number;
    known_gap_count: number;
    source_coverage: Record<string, number>;
    unmapped_need_ids: string[];
    unmapped_gap_ids: string[];
  };
  implementation_queue: Array<{
    action_id: string;
    title: string;
    priority_score: number;
    first_action: string;
    release_gate_links: string[];
    validation_commands: string[];
  }>;
  actions: LegalAdoptionResearchBridgeAction[];
  survey_intake_questions: Array<{
    id: string;
    prompt: string;
    privacy_rule: string;
    maps_to_need_ids: string[];
  }>;
  release_guardrails: string[];
  validation_commands: string[];
  privacy_note: string;
};

type LegalAdoptionResearchBridgeResponse = {
  success: boolean;
  data: LegalAdoptionResearchBridge;
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

export type MaintenanceLowResourceFixtureEvidence = {
  status: string;
  summary: {
    review_status: string;
    archive_status: string;
    release_decision: string;
    archive_release_decision: string;
    observed_fixture_count: number;
    archived_fixture_count: number;
    not_run_fixture_count: number;
    redacted_response_count: number;
    dropped_raw_field_count: number;
    blocking_check_count: number;
    warning_check_count: number;
    observed_request_count: number;
    observed_cost_usd?: number | null;
    release_ready: boolean;
    updates_count_mutated: boolean;
    completion_ready_mutated: boolean;
  };
  source_endpoints: {
    review: string;
    archive: string;
  };
  check_ids: {
    blocking: string[];
    warning: string[];
  };
  recommended_actions: string[];
  privacy_boundary: {
    raw_payload_echoed: boolean;
    raw_gateway_response_included: boolean;
    raw_model_output_included: boolean;
    raw_legal_text_included: boolean;
    credentials_included: boolean;
    emails_included: boolean;
    returns_archive_summaries_only: boolean;
  };
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
  low_resource_fixture_evidence: MaintenanceLowResourceFixtureEvidence;
  twenty_four_hour_evidence_requirements: string[];
  hundred_update_evidence_requirements: string[];
  low_resource_test_policy: {
    default_fixture_limit: number;
    max_parallel_requests: number;
    network_access: string;
    model_call_policy: string;
    recommended_endpoint: string;
    review_endpoint?: string;
    archive_endpoint?: string;
    ledger_review_endpoint?: string;
    run_monitor_review_endpoint?: string;
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

export type MatterAuditEventPolicy = {
  event_type: string;
  category: string;
  required_fields: string[];
  forbidden_fields: string[];
  retention_bucket: string;
  reviewer_value: string;
  blocking_if_missing: string[];
  missing_fields: string[];
  forbidden_fields_present: string[];
  status: string;
  blocks_release: boolean;
};

export type MatterAuditRetentionPolicy = {
  status: string;
  policy_id: string;
  summary: {
    event_type_count: number;
    checked_event_count: number;
    blocking_issue_count: number;
    retention_bucket_count: number;
    privacy_minimized: boolean;
  };
  event_policies: MatterAuditEventPolicy[];
  blocking_items: Array<{
    event_type: string;
    missing_fields: string[];
    forbidden_fields_present: string[];
    reviewer_value: string;
  }>;
  retention_buckets: Array<{
    id: string;
    description: string;
    default_retention: string;
  }>;
  data_minimization_rules: string[];
  validation_commands: string[];
  privacy_note: string;
};

type MatterAuditRetentionPolicyResponse = {
  success: boolean;
  data: MatterAuditRetentionPolicy;
};

export type LawyerReviewStateDefinition = {
  status: string;
  meaning: string;
  responsible_roles: string[];
  client_visible: boolean;
  terminal?: boolean;
};

export type LawyerReviewTransitionRule = {
  from_status: string;
  to_status: string;
  allowed_roles: string[];
  required_fields: string[];
  audit_event: string;
  reason_required?: boolean;
};

export type LawyerReviewWorkflowPolicy = {
  status: string;
  policy_id: string;
  summary: {
    state_count: number;
    transition_count: number;
    lawyer_gate_required: boolean;
    draft_direct_to_client_deliverable_allowed: boolean;
    blocking_condition_count: number;
  };
  state_enumeration: LawyerReviewStateDefinition[];
  allowed_state_transitions: LawyerReviewTransitionRule[];
  forbidden_state_transitions: Array<{
    from_status: string;
    to_status: string;
    reason: string;
  }>;
  blocking_conditions: Array<{
    code: string;
    message: string;
    allowed_roles?: string[];
    missing_fields?: string[];
    required_for?: string[];
  }>;
  role_requirements: Array<{
    gate: string;
    required_roles: string[];
    required_fields?: string[];
    notes: string;
  }>;
  audit_log_requirements: Array<{
    event: string;
    required_fields: string[];
  }>;
  low_resource_validation_commands: string[];
  privacy_notes: string[];
};

type LawyerReviewWorkflowPolicyResponse = {
  success: boolean;
  data: LawyerReviewWorkflowPolicy;
};

export type EvidenceExhibitPackagePolicy = {
  status: string;
  policy_id: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    exhibit_count: number;
    blocking_issue_count: number;
    ready_for_export: boolean;
    required_core_field_count: number;
    required_anchor_field_count: number;
    three_factor_review_count: number;
    export_manifest_field_count: number;
  };
  exhibit_metadata_schema: Array<{
    name: string;
    required: boolean;
    purpose: string;
    example: string;
  }>;
  package_checks: Array<{
    id: string;
    label: string;
    required_before_export: boolean;
    product_gap_closed: string;
    status: string;
    blocking_issue_ids: string[];
  }>;
  blocking_issues: Array<{
    id: string;
    severity: string;
    exhibit_ref: string;
    check_id: string;
    field: string;
    message: string;
    reviewer_action: string;
  }>;
  review_actions: Array<{
    id: string;
    label: string;
    required_role: string;
    action: string;
  }>;
  export_manifest_fields: Array<{
    name: string;
    required: boolean;
    purpose: string;
  }>;
  delivery_policy: string[];
  low_resource_validation_commands: Array<{
    id: string;
    command: string;
    resource_note: string;
  }>;
  privacy_notes: string[];
  future_api: Record<string, string>;
};

type EvidenceExhibitPackagePolicyResponse = {
  success: boolean;
  data: EvidenceExhibitPackagePolicy;
};

export type CaseTaskNotificationPolicy = {
  status: string;
  policy_id: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    task_count: number;
    active_task_count: number;
    done_task_count: number;
    notification_count: number;
    urgent_escalation_count: number;
    missing_owner_count: number;
    blocking_urgent_count: number;
  };
  notification_channels: Array<{
    channel: string;
    purpose: string;
    default_audience: string[];
    allowed_payload_fields: string[];
    cadence: string;
  }>;
  trigger_rules: Array<{
    rule_id: string;
    trigger: string;
    severity: string;
    channel_order: string[];
    reviewer_action: string;
  }>;
  escalation_rules: Array<{
    rule_id: string;
    applies_when: string;
    escalate_to: string[];
    action: string;
    audit_required: boolean;
  }>;
  owner_assignment_requirements: string[];
  notification_queue: Array<{
    case_id: string;
    task_id: string;
    status: string;
    priority: string;
    days_until_due: number | null;
    owner_missing: boolean;
    urgent_escalation: boolean;
    triggers: string[];
    recommended_channels: string[];
    blocking_reasons: string[];
  }>;
  blocking_urgent_tasks: Array<{
    case_id: string;
    task_id: string;
    status: string;
    priority: string;
    days_until_due: number | null;
    owner_missing: boolean;
    urgent_escalation: boolean;
    triggers: string[];
    recommended_channels: string[];
    blocking_reasons: string[];
  }>;
  evaluated_tasks: Array<{
    case_id: string;
    task_id: string;
    status: string;
    priority: string;
    days_until_due: number | null;
    owner_missing: boolean;
    urgent_escalation: boolean;
    requires_client_materials?: boolean;
    requires_lawyer_review?: boolean;
    done?: boolean;
    triggers: string[];
    recommended_channels: string[];
    blocking_reasons: string[];
  }>;
  audit_record_requirements: string[];
  low_resource_validation_commands: Array<{
    id: string;
    command: string;
    resource_note: string;
  }>;
  privacy_notes: string[];
  future_api_contract: Record<string, string>;
};

type CaseTaskNotificationPolicyResponse = {
  success: boolean;
  data: CaseTaskNotificationPolicy;
};

export type CaseWorkbenchMetric = {
  id: string;
  label: string;
  value: string | number | boolean | null;
};

export type CaseWorkbenchSection = {
  id: string;
  title: string;
  source: string;
  input_state: string;
  status: string;
  raw_status: string;
  severity: string;
  summary: Record<string, string | number | boolean | null>;
  metrics: CaseWorkbenchMetric[];
  preview_items: Array<Record<string, string | number | boolean | string[] | null>>;
  empty_state?: {
    title: string;
    message: string;
  } | null;
};

export type CaseWorkbenchBlocker = {
  id: string;
  source_section: string;
  source: string;
  severity: string;
  title: string;
  reason: string;
  required_action: string;
};

export type CaseWorkbenchNextAction = {
  id: string;
  source_section: string;
  priority: string;
  owner: string;
  action: string;
};

export type CaseWorkbenchPayload = {
  payload_id: string;
  version: number;
  status: string;
  case_ref: string;
  matter_ref: string;
  method: {
    type: string;
    notes: string[];
  };
  dashboard: {
    status: string;
    deterministic: boolean;
    section_count: number;
    evaluated_section_count: number;
    blocker_count: number;
    next_action_count: number;
    critical_action_count: number;
    cards: Array<{
      section_id: string;
      title: string;
      status: string;
      severity: string;
      primary_metric: CaseWorkbenchMetric | null;
    }>;
    primary_blocker: CaseWorkbenchBlocker | null;
    primary_next_action: CaseWorkbenchNextAction | null;
  };
  sections: CaseWorkbenchSection[];
  blockers: CaseWorkbenchBlocker[];
  next_actions: CaseWorkbenchNextAction[];
  source_contracts: Array<{
    section_id: string;
    source: string;
    input_state: string;
    status: string;
    validation_commands: string[];
  }>;
  validation_commands: string[];
  privacy_note: string;
};

type CaseWorkbenchPayloadResponse = {
  success: boolean;
  data: CaseWorkbenchPayload;
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

export type LegalFixtureLocalRunReview = {
  status: string;
  release_decision: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    response_count: number;
    normalized_observation_count: number;
    redacted_response_count: number;
    smoke_status: string;
    smoke_score: number;
    observed_fixture_count: number;
    not_run_fixture_count: number;
    escalation_required_count: number;
    observed_request_count: number;
    observed_cost_usd?: number | null;
    evidence_bundle_status: string;
    evidence_component_count: number;
    blocking_check_count: number;
    warning_check_count: number;
  };
  normalizer_summary: LegalFixtureResponseNormalizer['summary'];
  response_summaries: LegalFixtureResponseNormalizer['response_summaries'];
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

export type GeminiNewApiModelSelectorRecommendation = {
  task: string;
  selected_model: string;
  canonical_model?: string;
  cost_tier?: string;
  route_mode?: string;
  decision?: string;
  escalation_chain?: string[];
  warnings?: string[];
};

export type GeminiNewApiObservedModelReview = {
  raw_model: string;
  canonical_model?: string | null;
  status: string;
  action?: string;
  warnings?: string[];
};

export type GeminiNewApiCheapFirstLadder = {
  task_group: string;
  tasks?: string[];
  ladder?: Array<{
    order: number;
    model: string;
    cost_tier: string;
    candidate_stage?: string;
    review_required?: boolean;
    promotion_blockers?: string[];
    pricing_status?: string;
    catalog_status?: string;
    role?: string;
  }>;
};

export type GeminiNewApiModelSelectorEvidence = {
  status: string;
  summary: {
    task_count?: number;
    recommendation_count?: number;
    cheap_first_ready_count?: number;
    premium_exception_count?: number;
    catalog_review_count?: number;
    unknown_model_count?: number;
    raw_payload_echoed?: boolean;
  };
  task_recommendations: GeminiNewApiModelSelectorRecommendation[];
  observed_model_reviews: GeminiNewApiObservedModelReview[];
  cheap_first_ladders: GeminiNewApiCheapFirstLadder[];
  privacy_boundary: Record<string, unknown>;
  validation_commands: string[];
};

export type GeminiNewApiModelAliasMatrixRow = {
  id: string;
  source: string;
  alias_model: string;
  sanitized_model_id?: string;
  canonical_model?: string | null;
  alias_shape: string;
  alias_status: string;
  default_class: string;
  known_catalog_model: boolean;
  model_family?: string;
  cost_tier?: string | null;
  lifecycle_status?: string;
  cheap_first_candidate: boolean;
  high_frequency_default_allowed: boolean;
  balanced_after_precheck_allowed?: boolean;
  premium_exception: boolean;
  default_allowed_without_review: boolean;
  reason_codes?: string[];
  recommended_action?: string;
  configuration_write_allowed?: boolean;
  gateway_call_allowed?: boolean;
  traffic_shift_allowed?: boolean;
};

export type GeminiNewApiModelAliasMatrixEvidence = {
  id?: string;
  title?: string;
  status: string;
  summary: {
    alias_row_count?: number;
    catalog_model_count?: number;
    observed_model_count?: number;
    known_alias_count?: number;
    catalog_review_count?: number;
    external_model_count?: number;
    rejected_sensitive_count?: number;
    rejected_invalid_count?: number;
    rejected_model_count?: number;
    cheap_first_candidate_count?: number;
    high_frequency_default_allowed_count?: number;
    premium_exception_count?: number;
    canonical_catalog_count?: number;
    configuration_written?: boolean;
    gateway_called?: boolean;
    network_called?: boolean;
    raw_payload_echoed?: boolean;
    credentials_included?: boolean;
  };
  alias_rows: GeminiNewApiModelAliasMatrixRow[];
  accepted_alias_shapes?: string[];
  default_policy?: Record<string, unknown>;
  privacy_boundary: Record<string, unknown>;
  claim_boundary?: Record<string, unknown>;
  recommended_actions?: string[];
  validation_commands: string[];
};

export type GeminiNewApiSelectorReplayCheck = {
  id: string;
  status: string;
  expected?: unknown;
  actual?: unknown;
  reason?: string;
};

export type GeminiNewApiSelectorReplayResult = {
  id: string;
  status: string;
  scenario?: Record<string, unknown>;
  actual?: {
    selected_model?: string;
    canonical_model?: string | null;
    decision?: string;
    cost_tier?: string;
    route_mode?: string;
    warnings?: string[];
  };
  checks?: GeminiNewApiSelectorReplayCheck[];
  recommended_action?: string;
};

export type GeminiNewApiSelectorReplayEvidence = {
  status: string;
  summary: {
    scenario_count?: number;
    pass_count?: number;
    warn_count?: number;
    fail_count?: number;
    cheap_first_pass_count?: number;
    premium_exception_count?: number;
    catalog_review_count?: number;
    raw_payload_echoed?: boolean;
  };
  replay_results: GeminiNewApiSelectorReplayResult[];
  privacy_boundary: Record<string, unknown>;
  validation_commands: string[];
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
    document_fixture_ids?: string[];
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
    document_fixture_ids?: string[];
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

export type LegalPublicBenchmarkLicenseGate = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    source_count: number;
    approved_source_count: number;
    license_review_required_source_count: number;
    catalog_only_source_count: number;
    release_claim_blocked_source_count: number;
    linked_user_need_count: number;
    linked_route_task_count: number;
    sampling_ready_source_count: number;
    network_called: boolean;
    dataset_downloaded: boolean;
    model_called: boolean;
    gateway_called: boolean;
    raw_public_text_returned: boolean;
    configuration_written: boolean;
  };
  source_rows: Array<{
    id: string;
    source_id: string;
    title: string;
    url: string;
    priority: string;
    resource_profile: string;
    sampling_state: string;
    review_state: string;
    decision: string;
    release_claim_blocked: boolean;
    max_samples: number;
    license_gate: string;
    source_license_note: string;
    linked_user_need_ids: string[];
    linked_route_task_ids: string[];
    validation_targets: string[];
    required_checks: Array<{
      id: string;
      status: string;
      required: boolean;
      detail: string;
    }>;
    next_action: string;
    raw_text_import_allowed: boolean;
    public_score_claim_allowed: boolean;
    dataset_download_allowed: boolean;
    network_call_allowed: boolean;
  }>;
  user_need_rows: Array<{
    need_id: string;
    title: string;
    priority_band: string;
    coverage_status: string;
    linked_source_ids: string[];
    approved_source_ids: string[];
    blocked_source_ids: string[];
    release_claim_blocked: boolean;
    next_action: string;
  }>;
  review_policy: Record<string, boolean | string | number | null>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type LegalBenchmarkFixtureCrosswalk = {
  status: string;
  method: {
    type: string;
    purpose: string;
    source_services: string[];
    claim_boundary: string;
  };
  summary: {
    source_count: number;
    source_with_benchmark_case_count: number;
    source_with_local_fixture_count: number;
    source_with_document_fixture_count: number;
    source_with_small_corpus_count: number;
    gap_count: number;
    public_benchmark_score_claimed: boolean;
    model_calls: string;
    network_access: string;
  };
  source_rows: Array<{
    source_id: string;
    title: string;
    priority: string;
    resource_profile: string;
    sampling_state: string;
    license_gate: string;
    validation_targets: string[];
    benchmark_case_ids: string[];
    benchmark_case_rows: Array<{
      case_id: string;
      title: string;
      matter_type: string;
      task_family: string;
      user_segment: string;
      expected_route: string;
      required_metrics: string[];
      benchmark_sources: string[];
      release_gate_links: string[];
    }>;
    local_fixture_ids: string[];
    local_fixture_rows: Array<{
      fixture_id: string;
      title: string;
      matter_type: string;
      linked_case_ids: string[];
      expected_task_count: number;
      expected_signal_count: number;
      source_relation: string;
    }>;
    document_fixture_ids: string[];
    document_fixture_rows: Array<{
      case_id: string;
      title: string;
      document_type: string;
      matter_type: string;
      required_section_count: number;
      expected_citation_count: number;
      expected_risk_label_count: number;
      banned_pii_category_count: number;
      local_run_fit: string;
    }>;
    small_corpus_item_ids: string[];
    small_corpus_item_rows: Array<{
      item_id: string;
      title: string;
      domain: string;
      matter_type: string;
      document_type: string;
      source_type: string;
      language: string;
      task_count: number;
      risk_tag_count: number;
      difficulty: string;
      local_checks: string[];
    }>;
    coverage_status: string;
  }>;
  gap_queue: Array<{
    source_id: string;
    priority: string;
    gap_reasons: string[];
    recommended_action: string;
    validation_target: string;
  }>;
  privacy_boundary: {
    returns_public_benchmark_text: boolean;
    returns_local_fixture_snippets: boolean;
    returns_small_corpus_excerpts: boolean;
    returns_generated_text: boolean;
    returns_raw_model_output: boolean;
    returns_credentials: boolean;
    downloads_datasets: boolean;
    model_calls: boolean;
  };
  recommended_actions: string[];
  validation_commands: string[];
};

export type LegalBenchmarkResearchRegistry = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    source_count: number;
    source_names: string[];
    low_resource_action_count: number;
    forbidden_claim_count: number;
  };
  sources: Array<{
    public_name: string;
    public_link: string;
    experience_takeaways: string[];
    project_mapping: Record<string, unknown>;
    low_resource_action: string;
    forbidden_claims: string[];
  }>;
  low_resource_strategy: {
    default_mode: string;
    network_access: string;
    dataset_downloads: string;
    sensitive_data: string;
    fixture_cap: {
      default_sources: number;
      default_fixtures_per_source: number;
      max_fixtures_per_source_without_review: number;
    };
    actions: string[];
  };
  allowed_claims: string[];
  forbidden_claims: string[];
  validation_commands: string[];
  privacy_note: string;
};

export type LegalBenchmarkResearchRefreshSource = {
  id?: string;
  source_id?: string;
  title?: string;
  public_name?: string;
  url?: string;
  public_link?: string;
  source_type?: string;
  benchmark_family?: string;
  benchmark_signal?: string;
  local_interpretation?: string;
  import_policy?: string;
  license_status?: string;
  metadata_status?: string;
  refresh_status?: string;
  last_reviewed_at?: string | null;
  next_refresh_due?: string | null;
  cheap_first_fit?: string;
  local_validation?: string;
  notes?: string[];
  [key: string]: unknown;
};

export type LegalBenchmarkResearchRefreshRow = {
  id?: string;
  source_id?: string;
  source_name?: string;
  title?: string;
  product_area?: string;
  benchmark_signal?: string;
  local_validation_target?: string;
  local_evidence_paths?: string[];
  refresh_status?: string;
  fields_reviewed?: string[];
  refreshed_metadata_fields?: string[];
  stale_fields?: string[];
  changed_fields?: string[];
  user_need_ids?: string[];
  validation_command?: string;
  validation_commands?: string[];
  recommended_action?: string;
  cheap_first_local_validation?: string;
  cheap_first_policy?: string;
  next_actions?: string[];
  release_gate_links?: string[];
  priority?: number;
  cheap_first_relevant?: boolean;
  network_access?: string;
  model_calls?: string;
  metadata_only?: boolean;
  benchmark_score_claimed?: boolean;
  dataset_download_required?: boolean;
  model_call_required?: boolean;
  public_score_claimed?: boolean;
  external_legal_text_included?: boolean;
  [key: string]: unknown;
};

export type LegalBenchmarkResearchRefreshUserNeedRow = {
  need_id?: string;
  title?: string;
  category?: string;
  priority_band?: string;
  priority_score?: number;
  linked_source_ids?: string[];
  linked_refresh_row_ids?: string[];
  source_ids?: string[];
  refresh_row_ids?: string[];
  product_areas?: string[];
  coverage_status?: string;
  local_coverage_status?: string;
  public_benchmark_status?: string;
  calibration_status?: string;
  cheap_first_local_validation?: string;
  cheap_first_relevant?: boolean;
  validation_commands?: string[];
  gap_reasons?: string[];
  next_action?: string;
  next_actions?: string[];
  [key: string]: unknown;
};

export type LegalBenchmarkResearchRefresh = {
  status: string;
  summary: {
    source_count?: number;
    refresh_row_count?: number;
    user_need_row_count?: number;
    stale_source_count?: number;
    refreshed_source_count?: number;
    recommended_action_count?: number;
    cheap_first_signal_count?: number;
    retrieval_or_entailment_signal_count?: number;
    cheap_first_local_validation_status?: string;
    local_validation_command_count?: number;
    metadata_only?: boolean;
    network_access?: string;
    model_calls?: string;
    external_dataset_downloads?: boolean;
    benchmark_score_claims?: boolean;
    dataset_downloaded?: boolean;
    network_called?: boolean;
    model_called?: boolean;
    public_benchmark_score_claimed?: boolean;
    external_legal_text_included?: boolean;
    secret_value_included?: boolean;
    [key: string]: unknown;
  };
  research_sources: LegalBenchmarkResearchRefreshSource[];
  refresh_rows: LegalBenchmarkResearchRefreshRow[];
  user_need_rows: LegalBenchmarkResearchRefreshUserNeedRow[];
  recommended_actions: string[];
  privacy_boundary: {
    metadata_only?: boolean;
    returns_raw_benchmark_text?: boolean;
    returns_public_benchmark_text?: boolean;
    returns_dataset_samples?: boolean;
    returns_raw_legal_text?: boolean;
    returns_raw_model_output?: boolean;
    returns_user_feedback_text?: boolean;
    returns_credentials?: boolean;
    external_dataset_downloads?: boolean;
    model_calls?: boolean;
    network_called?: boolean;
    model_called?: boolean;
    network_access?: string;
    source?: string;
    [key: string]: unknown;
  };
  claim_boundary: {
    benchmark_score_claims?: boolean;
    public_benchmark_scores_claimed?: boolean;
    leaderboard_claims?: boolean;
    leaderboard_rank_claimed?: boolean;
    external_benchmark_run_claimed?: boolean;
    dataset_download_claimed?: boolean;
    external_dataset_download_claimed?: boolean;
    production_accuracy_claimed?: boolean;
    real_client_document_coverage_claimed?: boolean;
    automatic_model_improvement_claimed?: boolean;
    allowed_claims?: string[];
    forbidden_claims?: string[];
    source?: string;
    [key: string]: unknown;
  };
  validation_commands: string[];
};

export type ModelRouteLegalBenchmarkRiskQueueRow = {
  id?: string;
  task_id?: string;
  task?: string;
  route_id?: string;
  route?: string;
  route_name?: string;
  model?: string;
  model_id?: string;
  selected_model?: string | null;
  canonical_model?: string | null;
  task_family?: string;
  product_area?: string;
  risk_level?: string;
  risk_status?: string;
  status?: string;
  priority?: string | number;
  calibration_status?: string;
  calibration_decision?: string;
  cheap_first_allowed?: boolean;
  balanced_precheck_required?: boolean;
  premium_exception_required?: boolean;
  cheap_first_status?: string;
  cheap_first_decision?: string;
  cheap_first_gate?: string;
  cost_tier?: string;
  fixture_ids?: string[];
  fixture_score?: number | null;
  quality_floor?: number | null;
  research_source_ids?: string[];
  missing_user_need_ids?: string[];
  coverage_statuses?: string[];
  public_benchmark_statuses?: string[];
  calibration_statuses?: string[];
  linked_refresh_row_ids?: string[];
  release_gate_links?: string[];
  reason_codes?: string[];
  next_action?: string;
  newapi_called?: boolean;
  network_called?: boolean;
  dataset_download_required?: boolean;
  public_score_claimed?: boolean;
  raw_legal_text_included?: boolean;
  secret_value_included?: boolean;
  legal_benchmark_status?: string;
  benchmark_status?: string;
  user_need_status?: string;
  coverage_status?: string;
  benchmark_case_ids?: string[];
  legal_benchmark_case_ids?: string[];
  linked_benchmark_case_ids?: string[];
  user_need_ids?: string[];
  linked_user_need_ids?: string[];
  gap_reasons?: string[];
  risk_reasons?: string[];
  recommended_action?: string;
  next_actions?: string[];
  validation_command?: string;
  validation_commands?: string[];
  [key: string]: unknown;
};

export type ModelRouteLegalBenchmarkRiskQueueUserNeedRow = {
  need_id?: string;
  title?: string;
  category?: string;
  priority_band?: string;
  priority_score?: number;
  linked_route_ids?: string[];
  route_ids?: string[];
  linked_queue_row_ids?: string[];
  queue_row_ids?: string[];
  task_ids?: string[];
  refresh_row_ids?: string[];
  research_source_ids?: string[];
  public_benchmark_status?: string;
  calibration_status?: string;
  highest_risk_level?: string;
  cheap_first_allowed_count?: number;
  premium_exception_count?: number;
  cheap_first_status?: string;
  legal_benchmark_status?: string;
  user_need_status?: string;
  coverage_status?: string;
  gap_reasons?: string[];
  next_action?: string;
  next_actions?: string[];
  validation_commands?: string[];
  [key: string]: unknown;
};

export type ModelRouteLegalBenchmarkRiskQueue = {
  status: string;
  summary: {
    queue_row_count?: number;
    user_need_row_count?: number;
    high_risk_count?: number;
    medium_risk_count?: number;
    cheap_first_risk_count?: number;
    cheap_first_blocked_count?: number;
    cheap_first_allowed_count?: number;
    balanced_precheck_count?: number;
    premium_exception_count?: number;
    watch_count?: number;
    block_count?: number;
    benchmark_license_watch_count?: number;
    need_gap_watch_count?: number;
    legal_benchmark_gap_count?: number;
    user_need_gap_count?: number;
    recommended_action_count?: number;
    validation_command_count?: number;
    calibration_status?: string;
    benchmark_refresh_status?: string;
    benchmark_coverage_status?: string;
    newapi_called?: boolean;
    network_called?: boolean;
    dataset_downloaded?: boolean;
    public_benchmark_score_claimed?: boolean;
    raw_payload_echoed?: boolean;
    secret_value_included?: boolean;
    model_calls?: string;
    network_access?: string;
    metadata_only?: boolean;
    [key: string]: unknown;
  };
  queue_rows: ModelRouteLegalBenchmarkRiskQueueRow[];
  user_need_rows: ModelRouteLegalBenchmarkRiskQueueUserNeedRow[];
  routing_policy: {
    default_strategy?: string;
    cheap_model_start?: string;
    balanced_precheck_requires?: string[];
    premium_exception_requires?: string[];
    configuration_write_allowed?: boolean;
    gateway_call_allowed?: boolean;
    traffic_shift_allowed?: boolean;
    cheap_first_default?: string;
    default_route?: string;
    escalation_policy?: string;
    legal_benchmark_gate?: string;
    user_need_gate?: string;
    max_cost_tier?: string;
    local_validation_first?: boolean;
    [key: string]: unknown;
  };
  privacy_boundary: {
    metadata_only?: boolean;
    returns_raw_benchmark_text?: boolean;
    returns_public_benchmark_text?: boolean;
    returns_raw_legal_text?: boolean;
    returns_raw_model_output?: boolean;
    returns_routing_payloads?: boolean;
    returns_prompts?: boolean;
    returns_gateway_payloads?: boolean;
    returns_user_feedback_text?: boolean;
    returns_credentials?: boolean;
    network_called?: boolean;
    newapi_called?: boolean;
    dataset_downloaded?: boolean;
    external_dataset_downloads?: boolean;
    model_calls?: boolean | string;
    network_access?: string;
    source?: string;
    [key: string]: unknown;
  };
  claim_boundary: {
    cheap_first_default_change_claimed?: boolean;
    public_benchmark_scores_claimed?: boolean;
    benchmark_score_claims?: boolean;
    leaderboard_rank_claimed?: boolean;
    external_dataset_execution_claimed?: boolean;
    live_gateway_quality_claimed?: boolean;
    default_model_changed?: boolean;
    external_benchmark_run_claimed?: boolean;
    legal_advice_claimed?: boolean;
    production_accuracy_claimed?: boolean;
    automatic_routing_change_claimed?: boolean;
    allowed_claims?: string[];
    forbidden_claims?: string[];
    source?: string;
    [key: string]: unknown;
  };
  recommended_actions: string[];
  validation_commands: string[];
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkGateRow = {
  id: string;
  fixture_id: string;
  title: string;
  matter_type: string;
  task: string;
  cheap_first_model?: string | null;
  cheap_first_cost_tier?: string | null;
  cheap_first_known_model: boolean;
  estimated_request_cost_usd?: number | null;
  expected_signal_count: number;
  expected_task_count: number;
  linked_case_count: number;
  public_source_ids: string[];
  public_source_sampling_states: string[];
  model_matrix_status: string;
  run_report_status: string;
  linked_calibration_task_ids: string[];
  calibration_status: string;
  calibration_decisions: string[];
  calibration_release_gates: string[];
  run_report_score?: number | null;
  matched_signal_count: number;
  missing_signal_count: number;
  missing_task_count: number;
  high_priority_action_count: number;
  premium_escalation_candidate: boolean;
  gate_status: string;
  release_action: string;
  default_change_evidence_allowed: boolean;
  reason_codes: string[];
  validation_targets: string[];
  raw_fixture_text_returned: boolean;
  raw_model_output_returned: boolean;
  gateway_called: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkDocumentRow = {
  id: string;
  case_id: string;
  title: string;
  document_type: string;
  matter_type: string;
  benchmark_status: string;
  gate_status: string;
  score: number;
  structure_score: number;
  citation_score: number;
  pii_score: number;
  risk_score: number;
  missing_section_count: number;
  missing_citation_count: number;
  missing_risk_label_count: number;
  pii_finding_count: number;
  hard_pii_block: boolean;
  default_change_blocker: boolean;
  reason_codes: string[];
  validation_target: string;
  raw_document_snippet_returned: boolean;
  raw_candidate_text_returned: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkDocumentSummary = {
  status: string;
  score: number;
  case_count: number;
  passed_case_count: number;
  warning_case_count: number;
  failed_case_count: number;
  not_run_case_count: number;
  blocking_case_count: number;
  review_case_count: number;
  coverage_status: string;
  covered_document_type_count: number;
  target_document_type_count: number;
  missing_document_type_count: number;
  max_local_fixtures_per_run: number;
  model_calls: string;
  network_access: string;
  raw_document_snippets_returned: boolean;
  raw_candidate_text_returned: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkFactConsistencyRow = {
  id: string;
  case_id: string;
  title: string;
  benchmark_status: string;
  gate_status: string;
  score: number;
  amount_score: number;
  deadline_score: number;
  fact_score: number;
  contradiction_score: number;
  privacy_score: number;
  missing_amount_count: number;
  mismatched_amount_count: number;
  missing_deadline_count: number;
  mismatched_deadline_count: number;
  missing_fact_count: number;
  contradiction_count: number;
  raw_input_field_count: number;
  default_change_blocker: boolean;
  reason_codes: string[];
  validation_target: string;
  raw_document_text_returned: boolean;
  raw_candidate_text_returned: boolean;
  gateway_called: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkFactConsistencySummary = {
  status: string;
  score: number;
  case_count: number;
  passed_case_count: number;
  warning_case_count: number;
  failed_case_count: number;
  not_run_case_count: number;
  blocking_case_count: number;
  review_case_count: number;
  amount_mismatch_count: number;
  deadline_mismatch_count: number;
  contradiction_count: number;
  raw_input_field_count: number;
  model_calls: string;
  network_access: string;
  raw_document_text_returned: boolean;
  raw_candidate_text_returned: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkGatePrivacyBoundary = {
  metadata_only: boolean;
  returns_fixture_ids: boolean;
  returns_document_case_ids?: boolean;
  returns_fact_consistency_case_ids?: boolean;
  returns_calibration_task_ids?: boolean;
  returns_expected_signal_counts: boolean;
  returns_raw_fixture_text: boolean;
  returns_fixture_excerpt: boolean;
  returns_document_snippets?: boolean;
  returns_fact_consistency_raw_text?: boolean;
  returns_candidate_text?: boolean;
  returns_document_missing_labels?: boolean;
  returns_prompt_text: boolean;
  returns_raw_model_output: boolean;
  returns_gateway_payloads: boolean;
  returns_credentials: boolean;
  returns_calibration_payloads?: boolean;
  external_dataset_downloads?: boolean;
  model_calls?: boolean;
  network_called: boolean;
  newapi_called: boolean;
  output_scope: string;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkGateClaimBoundary = {
  automatic_default_change_claimed: boolean;
  public_benchmark_scores_claimed: boolean;
  legal_document_benchmark_scores_claimed?: boolean;
  fact_consistency_benchmark_scores_claimed?: boolean;
  external_dataset_execution_claimed: boolean;
  live_gateway_quality_claimed: boolean;
  production_legal_accuracy_claimed: boolean;
  legal_advice_claimed: boolean;
};

export type ModelOpsLegalFixtureCheapFirstBenchmarkGate = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    selected_fixture_count: number;
    evaluated_fixture_count: number;
    pass_count: number;
    review_required_count: number;
    blocked_count: number;
    not_run_count: number;
    default_evidence_allowed_count: number;
    default_change_evidence_allowed: boolean;
    cheap_first_model_count: number;
    premium_escalation_candidate_count: number;
    license_review_source_count: number;
    quick_suite_status: string;
    model_matrix_status: string;
    run_report_status: string;
    evidence_bundle_status: string;
    document_benchmark_status: string;
    document_benchmark_score: number;
    document_benchmark_case_count: number;
    document_benchmark_passed_case_count: number;
    document_benchmark_warning_case_count: number;
    document_benchmark_failed_case_count: number;
    document_benchmark_not_run_case_count: number;
    document_benchmark_blocking_case_count: number;
    document_benchmark_review_case_count: number;
    fact_consistency_status?: string;
    fact_consistency_score?: number;
    fact_consistency_case_count?: number;
    fact_consistency_passed_case_count?: number;
    fact_consistency_warning_case_count?: number;
    fact_consistency_failed_case_count?: number;
    fact_consistency_not_run_case_count?: number;
    fact_consistency_blocking_case_count?: number;
    fact_consistency_review_case_count?: number;
    fact_consistency_amount_mismatch_count?: number;
    fact_consistency_deadline_mismatch_count?: number;
    fact_consistency_contradiction_count?: number;
    calibration_status: string;
    calibration_task_count: number;
    linked_calibration_task_count: number;
    calibration_blocking_count: number;
    calibration_warning_count: number;
    calibration_pass_count: number;
    calibration_payload_returned: boolean;
    document_coverage_status: string;
    document_coverage_target_type_count: number;
    document_coverage_covered_type_count: number;
    document_coverage_missing_type_count: number;
    estimated_cheap_first_cost_usd: number;
    max_parallel_requests: number;
    raw_input_field_count: number;
    raw_fixture_text_returned: boolean;
    raw_model_output_returned: boolean;
    newapi_called: boolean;
    network_called: boolean;
    configuration_written: boolean;
    traffic_shifted: boolean;
  };
  gate_rows: ModelOpsLegalFixtureCheapFirstBenchmarkGateRow[];
  document_benchmark_summary?: ModelOpsLegalFixtureCheapFirstBenchmarkDocumentSummary;
  fact_consistency_summary?: ModelOpsLegalFixtureCheapFirstBenchmarkFactConsistencySummary;
  document_benchmark_rows?: ModelOpsLegalFixtureCheapFirstBenchmarkDocumentRow[];
  fact_consistency_rows?: ModelOpsLegalFixtureCheapFirstBenchmarkFactConsistencyRow[];
  blocking_fixture_ids: string[];
  review_fixture_ids: string[];
  blocking_document_case_ids?: string[];
  review_document_case_ids?: string[];
  blocking_fact_consistency_case_ids?: string[];
  review_fact_consistency_case_ids?: string[];
  default_evidence_fixture_ids: string[];
  default_change_evidence_allowed?: boolean;
  routing_policy: {
    default_strategy: string;
    cheap_first_models: string[];
    default_evidence_requires: string[];
    blocked_actions: string[];
    max_parallel_requests: number;
    document_benchmark_required_for_default_change?: boolean;
    fact_consistency_required_for_default_change?: boolean;
    calibration_required_for_default_change?: boolean;
    default_change_evidence_allowed?: boolean;
    configuration_write_allowed: boolean;
    gateway_call_allowed: boolean;
    traffic_shift_allowed: boolean;
  };
  recommended_actions: string[];
  privacy_boundary: ModelOpsLegalFixtureCheapFirstBenchmarkGatePrivacyBoundary;
  claim_boundary: ModelOpsLegalFixtureCheapFirstBenchmarkGateClaimBoundary;
  validation_commands: string[];
};

export type ModelOpsLegalFixtureCheapFirstDefaultPromotionPacketItem = {
  id: string;
  fixture_id: string;
  title: string;
  task: string;
  matter_type: string;
  proposed_default_model?: string | null;
  proposed_cost_tier?: string | null;
  gate_status: string;
  document_benchmark_status: string;
  document_coverage_status: string;
  fact_consistency_status: string;
  calibration_status: string;
  linked_calibration_task_ids: string[];
  calibration_decisions: string[];
  calibration_release_gates: string[];
  promotion_status: string;
  default_change_evidence_allowed: boolean;
  premium_escalation_candidate: boolean;
  required_evidence: string[];
  required_signoffs: string[];
  reason_codes: string[];
  configuration_change_allowed: boolean;
  gateway_call_allowed: boolean;
  traffic_shift_allowed: boolean;
  action: string;
};

export type ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket = {
  status: string;
  decision: {
    status: string;
    label: string;
    approval_required: boolean;
    configuration_change_allowed: boolean;
    gateway_call_allowed: boolean;
    traffic_shift_allowed: boolean;
    default_change_allowed_by_packet: boolean;
    requires_gate_ready: boolean;
    requires_document_benchmark_pass: boolean;
    requires_fact_consistency_pass?: boolean;
    requires_cheap_first_calibration_pass: boolean;
    requires_document_coverage_ready: boolean;
  };
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    promotion_item_count: number;
    ready_for_review_count: number;
    blocked_count: number;
    review_required_count: number;
    not_ready_count: number;
    source_gate_status: string;
    source_default_change_evidence_allowed: boolean;
    source_selected_fixture_count: number;
    source_default_evidence_allowed_count: number;
    document_benchmark_status: string;
    document_benchmark_score: number;
    document_coverage_status: string;
    document_coverage_missing_type_count: number;
    fact_consistency_status: string;
    fact_consistency_score: number;
    fact_consistency_case_count: number;
    fact_consistency_blocking_case_count: number;
    fact_consistency_amount_mismatch_count: number;
    fact_consistency_deadline_mismatch_count: number;
    fact_consistency_contradiction_count: number;
    calibration_status: string;
    calibration_task_count: number;
    linked_calibration_task_count: number;
    calibration_blocking_count: number;
    calibration_warning_count: number;
    calibration_pass_count: number;
    privacy_boundary_passed: boolean;
    raw_input_field_count: number;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    raw_text_returned: boolean;
    newapi_called: boolean;
  };
  promotion_items: ModelOpsLegalFixtureCheapFirstDefaultPromotionPacketItem[];
  ready_item_ids: string[];
  blocked_item_ids: string[];
  review_item_ids: string[];
  not_ready_item_ids: string[];
  required_signoffs: string[];
  evidence_checklist: {
    id: string;
    status: string;
    passed: boolean;
    source_status: string;
  }[];
  recommended_actions: string[];
  source_gate_links: Record<string, string>;
  privacy_boundary: {
    metadata_only: boolean;
    returns_fixture_ids: boolean;
    returns_document_case_ids: boolean;
    returns_fact_consistency_case_ids?: boolean;
    returns_calibration_task_ids?: boolean;
    returns_raw_fixture_text: boolean;
    returns_calibration_payloads?: boolean;
    returns_document_snippets: boolean;
    returns_candidate_text: boolean;
    returns_prompt_text: boolean;
    returns_raw_model_output: boolean;
    returns_gateway_payloads: boolean;
    returns_credentials: boolean;
    network_called: boolean;
    newapi_called: boolean;
    configuration_written: boolean;
    traffic_shifted: boolean;
    output_scope: string;
  };
  claim_boundary: {
    maintainer_approval_claimed: boolean;
    automatic_default_change_claimed: boolean;
    configuration_change_claimed: boolean;
    live_gateway_execution_claimed: boolean;
    public_benchmark_scores_claimed: boolean;
    legal_document_benchmark_scores_claimed: boolean;
    production_accuracy_claimed: boolean;
    legal_advice_claimed: boolean;
  };
  validation_commands: string[];
};

export type LegalRagAuthorityCitationGateSourceRow = {
  id?: string;
  source_id?: string;
  title?: string;
  source_title?: string;
  source_tier?: string;
  tier?: string;
  authority?: string;
  authority_level?: string;
  jurisdiction?: string;
  jurisdiction_status?: string;
  freshness?: string;
  freshness_status?: string;
  last_reviewed_at?: string | null;
  last_updated_at?: string | null;
  citation_mismatch_count?: number;
  citation_mismatches?: number;
  retrieval_gap_count?: number;
  retrieval_gaps?: number;
  claim_boundary_status?: string;
  privacy_boundary_status?: string;
  status?: string;
  reason_codes?: string[];
  recommended_actions?: string[];
  validation_command?: string;
  validation_commands?: string[];
  [key: string]: unknown;
};

export type LegalRagAuthorityCitationGate = {
  status: string;
  summary: {
    source_count?: number;
    source_tier_count?: number;
    authority_review_count?: number;
    jurisdiction_count?: number;
    freshness_gap_count?: number;
    stale_source_count?: number;
    citation_mismatch_count?: number;
    retrieval_gap_count?: number;
    claim_boundary_gap_count?: number;
    privacy_boundary_gap_count?: number;
    recommended_action_count?: number;
    validation_command_count?: number;
    metadata_only?: boolean;
    raw_legal_text_included?: boolean;
    prompt_included?: boolean;
    model_output_included?: boolean;
    credentials_included?: boolean;
    [key: string]: unknown;
  };
  source_rows: LegalRagAuthorityCitationGateSourceRow[];
  recommended_actions: string[];
  validation_commands: string[];
  privacy_boundary: {
    metadata_only?: boolean;
    returns_raw_legal_text?: boolean;
    returns_raw_source_text?: boolean;
    returns_prompts?: boolean;
    returns_prompt?: boolean;
    returns_raw_model_output?: boolean;
    returns_model_output?: boolean;
    returns_credentials?: boolean;
    returns_secrets?: boolean;
    source?: string;
    [key: string]: unknown;
  };
  claim_boundary: {
    legal_advice_claimed?: boolean;
    unsupported_claims_allowed?: boolean;
    citation_without_source_allowed?: boolean;
    jurisdiction_mismatch_allowed?: boolean;
    freshness_gap_allowed?: boolean;
    allowed_claims?: string[];
    forbidden_claims?: string[];
    source?: string;
    [key: string]: unknown;
  };
  source_tiers?: Record<string, string | number>;
  authority_counts?: Record<string, number>;
  jurisdiction_counts?: Record<string, number>;
  freshness_counts?: Record<string, number>;
  citation_mismatch_rows?: LegalRagAuthorityCitationGateSourceRow[];
  retrieval_gap_rows?: LegalRagAuthorityCitationGateSourceRow[];
  claim_boundary_rows?: LegalRagAuthorityCitationGateSourceRow[];
};

export type LegalRagHallucinationTriageGateRow = {
  case_id: string;
  title: string;
  scenario?: string;
  severity: string;
  failure_labels: string[];
  evidence_signals: string[];
  reviewer_actions: string[];
  release_action: string;
  block_release: boolean;
  linked_authority_row_ids: string[];
  linked_gate_ids: string[];
  privacy_boundary: {
    user_question_returned?: boolean;
    retrieved_context_returned?: boolean;
    unsafe_answer_returned?: boolean;
    raw_legal_text_returned?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type LegalRagHallucinationTriageGate = {
  id: string;
  status: string;
  title: string;
  summary: {
    triage_row_count: number;
    fixture_case_count: number;
    taxonomy_count: number;
    blocker_row_count: number;
    critical_row_count: number;
    high_row_count: number;
    medium_row_count: number;
    failure_label_count: number;
    authority_gate_status: string;
    citation_mismatch_count: number;
    retrieval_gap_count: number;
    model_called: boolean;
    gateway_called: boolean;
    newapi_called: boolean;
    network_called: boolean;
    dataset_downloaded: boolean;
    raw_retrieved_context_included: boolean;
    raw_legal_text_included: boolean;
    prompt_included: boolean;
    model_output_included: boolean;
    credentials_included: boolean;
    [key: string]: unknown;
  };
  triage_rows: LegalRagHallucinationTriageGateRow[];
  failure_label_counts: Record<string, number>;
  severity_counts: Record<string, number>;
  research_basis: Array<{
    id: string;
    url: string;
    signal: string;
  }>;
  release_policy: {
    default_action: string;
    allowed_without_lawyer_review: string[];
    requires_lawyer_review: string[];
    linked_gate_ids: string[];
  };
  claim_boundary: {
    hallucination_free_claimed: boolean;
    legal_answer_accuracy_claimed: boolean;
    public_benchmark_score_claimed: boolean;
    live_gateway_quality_claimed: boolean;
    automatic_client_delivery_claimed: boolean;
    allowed_claims: string[];
    forbidden_claims: string[];
    [key: string]: unknown;
  };
  privacy_boundary: {
    metadata_only: boolean;
    returns_user_question: boolean;
    returns_retrieved_context: boolean;
    returns_unsafe_answer: boolean;
    returns_raw_legal_text: boolean;
    returns_prompts: boolean;
    returns_model_outputs: boolean;
    returns_credentials: boolean;
    network_called: boolean;
    dataset_downloaded: boolean;
    [key: string]: unknown;
  };
  recommended_actions: string[];
  validation_commands: string[];
};

export type LegalRagAbstentionEscalationDecisionRow = {
  id?: string;
  case_id?: string;
  fixture_id?: string;
  mode?: string;
  decision_mode?: string;
  decision?: string;
  answer_mode?: string;
  evidence_sufficiency?: string;
  evidence_sufficiency_status?: string;
  block_release?: boolean;
  blocker_ids?: string[];
  linked_gate_ids?: string[];
  [key: string]: unknown;
};

export type LegalRagAbstentionEscalationGate = {
  id?: string;
  status: string;
  title?: string;
  summary: {
    decision_row_count?: number;
    row_count?: number;
    answer_count?: number;
    answer_with_warning_count?: number;
    abstain_count?: number;
    ask_clarification_count?: number;
    lawyer_review_count?: number;
    premium_exception_count?: number;
    cheap_first_count?: number;
    cheap_first_route_count?: number;
    blocker_count?: number;
    evidence_sufficient_count?: number;
    evidence_gap_count?: number;
    evidence_insufficient_count?: number;
    authority_gate_status?: string;
    authority_citation_gate_status?: string;
    hallucination_gate_status?: string;
    hallucination_triage_gate_status?: string;
    decision_counts?: Record<string, number>;
    evidence_sufficiency_counts?: Record<string, number>;
    [key: string]: unknown;
  };
  decision_rows: LegalRagAbstentionEscalationDecisionRow[];
  decision_counts?: Record<string, number>;
  evidence_sufficiency_counts?: Record<string, number>;
  linkage?: {
    authority_gate_status?: string;
    authority_citation_gate_status?: string;
    hallucination_gate_status?: string;
    hallucination_triage_gate_status?: string;
    linked_gate_ids?: string[];
    [key: string]: unknown;
  };
  routing_policy?: {
    cheap_first_route?: string | boolean;
    cheap_first_allowed?: boolean;
    premium_exception_boundary?: string;
    premium_exception_allowed?: boolean;
    premium_exception_requires_lawyer_review?: boolean;
    [key: string]: unknown;
  };
  claim_boundary: {
    legal_advice_claimed?: boolean;
    legal_answer_accuracy_claimed?: boolean;
    automatic_escalation_claimed?: boolean;
    premium_exception_delivery_claimed?: boolean;
    [key: string]: unknown;
  };
  privacy_boundary: {
    metadata_only?: boolean;
    model_called?: boolean;
    gateway_called?: boolean;
    network_called?: boolean;
    returns_raw_fixture?: boolean;
    returns_raw_fixture_payload?: boolean;
    returns_retrieved_context?: boolean;
    returns_raw_legal_text?: boolean;
    returns_raw_model_output?: boolean;
    returns_gateway_payload?: boolean;
    [key: string]: unknown;
  };
  recommended_actions: string[];
  validation_commands: string[];
};

export type LegalRagRetrievalDiagnosticsGateRow = {
  id?: string;
  diagnostic_id?: string;
  query_intent: string;
  retrieval_status: string;
  source_coverage_status: string;
  source_coverage_score?: number;
  expected_source_count?: number;
  selected_source_count?: number;
  top_k_depth?: number;
  top_k_depth_status: string;
  jurisdiction_status: string;
  freshness_status: string;
  citation_gap?: boolean;
  retrieval_gap?: boolean;
  cheap_first_action: {
    task?: string;
    decision?: string;
    starts_cheap?: boolean;
    recommended_model_alias?: string;
    signals?: string[];
    requires_operator_review?: boolean;
    model_called?: boolean;
    gateway_called?: boolean;
    [key: string]: unknown;
  };
  release_action: string;
  linked_gate_ids: string[];
  linked_authority_row_ids?: string[];
  linked_abstention_modes?: string[];
  authority_coverage_status?: string;
  retrieval_depth_gap?: boolean;
  jurisdiction_freshness_gap?: boolean;
  reason_codes?: string[];
  validation_commands?: string[];
  privacy_boundary?: {
    raw_query_returned?: boolean;
    retrieved_context_returned?: boolean;
    raw_legal_text_returned?: boolean;
    prompt_returned?: boolean;
    model_output_returned?: boolean;
    credentials_returned?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type LegalRagRetrievalDiagnosticsGate = {
  id: 'legal-rag-retrieval-diagnostics-gate' | string;
  status: string;
  title?: string;
  summary: {
    diagnostic_row_count?: number;
    ready_row_count?: number;
    review_row_count?: number;
    blocked_row_count?: number;
    authority_coverage?: number | string;
    authority_coverage_count?: number;
    authority_coverage_status?: string;
    retrieval_depth_gap_count?: number;
    retrieval_depth_gaps?: number;
    jurisdiction_freshness_gap_count?: number;
    jurisdiction_gap_count?: number;
    freshness_gap_count?: number;
    cheap_first_retry_count?: number;
    cheap_first_retry_rows?: number;
    retrieval_recall_weight?: number;
    citation_precision_weight?: number;
    model_called?: boolean;
    gateway_called?: boolean;
    newapi_called?: boolean;
    network_called?: boolean;
    dataset_downloaded?: boolean;
    raw_query_included?: boolean;
    raw_retrieved_context_included?: boolean;
    raw_legal_text_included?: boolean;
    prompt_included?: boolean;
    model_output_included?: boolean;
    credentials_included?: boolean;
    [key: string]: unknown;
  };
  diagnostic_rows: LegalRagRetrievalDiagnosticsGateRow[];
  retrieval_status_counts?: Record<string, number>;
  release_action_counts?: Record<string, number>;
  linked_gate_summary?: {
    legal_rag_index_binding?: string;
    authority_gate_id?: string;
    abstention_gate_id?: string;
    authority_review_rows?: number;
    authority_citation_mismatch_count?: number;
    authority_retrieval_gap_count?: number;
    abstention_decision_rows?: number;
    abstention_blocker_count?: number;
    [key: string]: unknown;
  };
  diagnostic_policy?: {
    method?: string;
    minimum_ready_selected_source_count?: number;
    minimum_top_k_depth?: number;
    requires_jurisdiction_filter?: boolean;
    requires_fresh_or_review_due_sources?: boolean;
    blocks_on_empty_index_coverage?: boolean;
    blocks_on_forbidden_query_filters?: boolean;
    premium_exception_default_allowed?: boolean;
    cheap_first_default?: boolean;
    [key: string]: unknown;
  };
  research_basis?: Array<{
    id?: string;
    url?: string;
    signal?: string;
    [key: string]: unknown;
  }>;
  linkage?: {
    linked_gate_ids?: string[];
    gate_statuses?: Record<string, string>;
    legal_rag_index_binding_status?: string;
    legal_rag_authority_citation_gate_status?: string;
    legal_rag_abstention_escalation_gate_status?: string;
    [key: string]: unknown;
  };
  claim_boundary?: {
    model_claimed?: boolean;
    gateway_claimed?: boolean;
    network_claimed?: boolean;
    raw_query_included?: boolean;
    raw_context_included?: boolean;
    raw_legal_text_included?: boolean;
    prompts_included?: boolean;
    model_output_included?: boolean;
    credentials_included?: boolean;
    [key: string]: unknown;
  };
  privacy_boundary: {
    metadata_only?: boolean;
    model_called?: boolean;
    model_calls?: boolean;
    gateway_called?: boolean;
    network_called?: boolean;
    network_access?: boolean | string;
    returns_raw_query?: boolean;
    returns_query_text?: boolean;
    returns_raw_context?: boolean;
    returns_context_text?: boolean;
    returns_raw_legal_text?: boolean;
    returns_legal_text?: boolean;
    returns_prompts?: boolean;
    returns_model_output?: boolean;
    returns_raw_model_output?: boolean;
    returns_credentials?: boolean;
    credentials_included?: boolean;
    [key: string]: unknown;
  };
  recommended_actions: string[];
  validation_commands: string[];
};

export type LegalRagBenchmarkAlignmentRow = {
  id: string;
  title: string;
  benchmark_signal_ids: string[];
  alignment_status: string;
  release_action: string;
  coverage_score: number;
  required_gate_ids: string[];
  gate_statuses: Record<string, string>;
  required_validation_targets: string[];
  observed_validation_targets: string[];
  missing_validation_targets: string[];
  expected_local_fixture_ids: string[];
  observed_local_fixture_ids: string[];
  missing_local_fixture_ids: string[];
  public_source_sampling_states: Record<string, string>;
  cheap_first_policy: string;
  starts_cheap: boolean;
  premium_exception_allowed: boolean;
  gap_reasons: string[];
  linked_gate_ids: string[];
  privacy_boundary: {
    public_benchmark_text_returned?: boolean;
    raw_query_returned?: boolean;
    retrieved_context_returned?: boolean;
    raw_legal_text_returned?: boolean;
    prompt_returned?: boolean;
    model_output_returned?: boolean;
    credentials_returned?: boolean;
    [key: string]: unknown;
  };
};

export type LegalRagBenchmarkAlignment = {
  id: 'legal-rag-benchmark-alignment' | string;
  title: string;
  status: string;
  summary: {
    dimension_count: number;
    aligned_count: number;
    review_count: number;
    gap_count: number;
    blocked_claim_count: number;
    maintainer_review_count: number;
    benchmark_signal_count: number;
    diagnostic_row_count: number;
    retrieval_blocked_row_count: number;
    abstention_blocker_count: number;
    public_sampler_source_count: number;
    public_sampler_ready_source_count: number;
    fixture_crosswalk_gap_count: number;
    cheap_first_default: boolean;
    model_called: boolean;
    gateway_called: boolean;
    newapi_called: boolean;
    network_called: boolean;
    dataset_downloaded: boolean;
    raw_public_benchmark_text_included: boolean;
    raw_query_included: boolean;
    raw_retrieved_context_included: boolean;
    raw_legal_text_included: boolean;
    prompt_included: boolean;
    model_output_included: boolean;
    credentials_included: boolean;
    [key: string]: unknown;
  };
  alignment_rows: LegalRagBenchmarkAlignmentRow[];
  alignment_status_counts: Record<string, number>;
  release_action_counts: Record<string, number>;
  benchmark_dimensions: Array<{
    id: string;
    title: string;
    benchmark_signal_ids: string[];
    required_gate_ids: string[];
    required_validation_targets: string[];
    expected_local_fixture_ids: string[];
    cheap_first_policy: string;
  }>;
  linked_gate_summary: Record<string, unknown>;
  research_basis: Array<{
    id: string;
    url: string;
    signal: string;
  }>;
  claim_boundary: {
    legal_advice_claimed: boolean;
    legal_rag_quality_claimed: boolean;
    public_benchmark_score_claimed: boolean;
    leaderboard_claimed: boolean;
    live_gateway_quality_claimed: boolean;
    automatic_client_delivery_claimed: boolean;
    allowed_claims: string[];
    forbidden_claims: string[];
    [key: string]: unknown;
  };
  privacy_boundary: {
    metadata_only: boolean;
    returns_public_benchmark_text: boolean;
    returns_raw_query: boolean;
    returns_retrieved_context: boolean;
    returns_raw_legal_text: boolean;
    returns_prompts: boolean;
    returns_model_outputs: boolean;
    returns_credentials: boolean;
    returns_gateway_payloads: boolean;
    calls_newapi: boolean;
    calls_gemini: boolean;
    calls_gateway: boolean;
    downloads_datasets: boolean;
    network_called: boolean;
    [key: string]: unknown;
  };
  recommended_actions: string[];
  validation_commands: string[];
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

export type LegalDocumentBenchmarkCoverageDimensionRow = {
  label: string;
  coverage_count: number;
  case_ids: string[];
  document_types: string[];
  covered: boolean;
};

export type LegalDocumentBenchmarkCoverageCaseRow = {
  case_id: string;
  title: string;
  document_type: string;
  matter_type: string;
  required_section_count: number;
  expected_citation_count: number;
  expected_risk_label_count: number;
  banned_pii_category_count: number;
  coverage_axes: {
    structure: string[];
    citations: string[];
    risk_labels: string[];
    pii: string[];
  };
  local_run_fit: string;
};

export type LegalDocumentBenchmarkCoverageQueueItem = {
  id: string;
  priority: string;
  document_type: string;
  reason: string;
  recommended_fixture_shape: string;
  validation_target: string;
};

export type LegalDocumentBenchmarkCoverage = {
  status: string;
  summary: {
    case_count: number;
    target_document_type_count: number;
    covered_document_type_count: number;
    missing_document_type_count: number;
    section_label_count: number;
    citation_label_count: number;
    risk_label_count: number;
    pii_category_count: number;
    max_local_fixtures_per_run: number;
    model_calls: string;
    network_access: string;
  };
  target_document_types: string[];
  missing_document_types: string[];
  case_rows: LegalDocumentBenchmarkCoverageCaseRow[];
  dimensions: {
    document_types: LegalDocumentBenchmarkCoverageDimensionRow[];
    required_sections: LegalDocumentBenchmarkCoverageDimensionRow[];
    expected_citations: LegalDocumentBenchmarkCoverageDimensionRow[];
    expected_risk_labels: LegalDocumentBenchmarkCoverageDimensionRow[];
    banned_pii_categories: LegalDocumentBenchmarkCoverageDimensionRow[];
  };
  next_fixture_queue: LegalDocumentBenchmarkCoverageQueueItem[];
  recommended_actions: string[];
  validation_commands: string[];
  privacy_boundary: Record<string, unknown>;
  privacy_note: string;
};

export type LegalDocumentFactConsistencyAmountExpectation = {
  id: string;
  value: number;
  currency: string;
  formula: string;
};

export type LegalDocumentFactConsistencyDeadlineExpectation = {
  id: string;
  value: string;
  rule: string;
};

export type LegalDocumentFactConsistencyContradictionPair = {
  id: string;
  fact_ids: string[];
};

export type LegalDocumentFactConsistencyCase = {
  id: string;
  title: string;
  document_type: string;
  matter_type: string;
  amount_expectations: LegalDocumentFactConsistencyAmountExpectation[];
  deadline_expectations: LegalDocumentFactConsistencyDeadlineExpectation[];
  required_fact_ids: string[];
  contradiction_pairs: LegalDocumentFactConsistencyContradictionPair[];
};

export type LegalDocumentFactConsistencyCheck = {
  id: string;
  target: string;
  local_check: string;
  weight: number;
  hard_fail?: boolean;
};

export type LegalDocumentFactConsistencyBenchmark = {
  status: string;
  summary: {
    case_count: number;
    check_count: number;
    max_cases: number;
    language: string;
    data_source: string;
    model_calls: string;
    network_access: string;
    external_datasets: string;
    amount_tolerance: number;
  };
  benchmark_cases: LegalDocumentFactConsistencyCase[];
  checks: LegalDocumentFactConsistencyCheck[];
  resource_policy: Record<string, unknown>;
  privacy_boundary: Record<string, unknown>;
  validation_commands: string[];
};

export type LegalDocumentFactConsistencyCaseResult = {
  case_id: string;
  title: string;
  status: string;
  score: number;
  metric_scores: Record<string, number>;
  missing_amount_ids: string[];
  mismatched_amount_ids: string[];
  missing_deadline_ids: string[];
  mismatched_deadline_ids: string[];
  missing_fact_ids: string[];
  contradiction_pair_ids: string[];
  raw_input_field_count: number;
  hard_consistency_block: boolean;
  reason_codes: string[];
};

export type LegalDocumentFactConsistencyEvaluation = {
  status: string;
  score: number;
  case_count: number;
  passed_case_count: number;
  warning_case_count: number;
  failed_case_count: number;
  not_run_case_count: number;
  amount_mismatch_count: number;
  deadline_mismatch_count: number;
  contradiction_count: number;
  raw_input_field_count: number;
  blocking_case_ids: string[];
  case_results: LegalDocumentFactConsistencyCaseResult[];
  privacy_boundary: Record<string, unknown>;
};

type LegalReviewBenchmarkResponse = {
  success: boolean;
  data: LegalReviewBenchmark;
};

type LegalDocumentBenchmarkCoverageResponse = {
  success: boolean;
  data: LegalDocumentBenchmarkCoverage;
};

type LegalDocumentFactConsistencyBenchmarkResponse = {
  success: boolean;
  data: LegalDocumentFactConsistencyBenchmark;
};

type LegalDocumentFactConsistencyEvaluationResponse = {
  success: boolean;
  data: LegalDocumentFactConsistencyEvaluation;
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

type LegalFixtureLocalRunReviewResponse = {
  success: boolean;
  data: LegalFixtureLocalRunReview;
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

type GeminiNewApiModelSelectorEvidenceResponse = {
  success: boolean;
  data: GeminiNewApiModelSelectorEvidence;
};

type GeminiNewApiModelAliasMatrixEvidenceResponse = {
  success: boolean;
  data: GeminiNewApiModelAliasMatrixEvidence;
};

type GeminiNewApiSelectorReplayEvidenceResponse = {
  success: boolean;
  data: GeminiNewApiSelectorReplayEvidence;
};

type LegalFixtureEvidenceBundleResponse = {
  success: boolean;
  data: LegalFixtureEvidenceBundle;
};

type LegalPublicBenchmarkSamplerResponse = {
  success: boolean;
  data: LegalPublicBenchmarkSampler;
};

type LegalPublicBenchmarkLicenseGateResponse = {
  success: boolean;
  data: LegalPublicBenchmarkLicenseGate;
};

type LegalBenchmarkFixtureCrosswalkResponse = {
  success: boolean;
  data: LegalBenchmarkFixtureCrosswalk;
};

type LegalBenchmarkResearchRegistryResponse = {
  success: boolean;
  data: LegalBenchmarkResearchRegistry;
};

type LegalBenchmarkResearchRefreshResponse = {
  success: boolean;
  data: LegalBenchmarkResearchRefresh;
};

type ModelRouteLegalBenchmarkRiskQueueResponse = {
  success: boolean;
  data: ModelRouteLegalBenchmarkRiskQueue;
};

type LegalRagAuthorityCitationGateResponse = {
  success: boolean;
  data:
    | LegalRagAuthorityCitationGate
    | {
        legalRagAuthorityCitationGate: LegalRagAuthorityCitationGate;
      };
};

type LegalRagHallucinationTriageGateResponse = {
  success: boolean;
  data:
    | LegalRagHallucinationTriageGate
    | {
        legalRagHallucinationTriageGate: LegalRagHallucinationTriageGate;
      };
};

type LegalRagAbstentionEscalationGateResponse = {
  success: boolean;
  data:
    | LegalRagAbstentionEscalationGate
    | {
        legalRagAbstentionEscalationGate?: LegalRagAbstentionEscalationGate;
        legal_rag_abstention_escalation_gate?: LegalRagAbstentionEscalationGate;
      };
};

type LegalRagRetrievalDiagnosticsGateResponse = {
  success: boolean;
  data: LegalRagRetrievalDiagnosticsGate;
};

type LegalRagBenchmarkAlignmentResponse = {
  success: boolean;
  data: LegalRagBenchmarkAlignment;
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

export type MaintenancePrivacyBoundary = {
  raw_feedback_echoed?: boolean;
  raw_document_text_included?: boolean;
  raw_legal_text_included?: boolean;
  raw_claim_text_included?: boolean;
  raw_payload_included?: boolean;
  pii_returned?: boolean;
  pii_included?: boolean;
  secret_included?: boolean;
  provider_payload_included?: boolean;
  billing_provider_payload_included?: boolean;
  user_claims_included?: boolean;
  output_scope?: string;
  [key: string]: unknown;
};

export type MaintenanceFeedbackIssueCluster = {
  cluster_id: string;
  normalized_topic: string;
  severity: string;
  count: number;
  counts: Record<string, number>;
  affected_user_segment_tags: string[];
  evidence_refs: string[];
};

export type MaintenanceFeedbackIssueClusters = {
  status: string;
  method: {
    mode?: string;
    model_calls?: number;
    external_network_calls?: number;
    stores_raw_feedback?: boolean;
    max_input_items?: number;
    max_text_chars_per_item?: number;
    [key: string]: unknown;
  };
  summary: {
    input_item_count: number;
    processed_item_count: number;
    ignored_item_count: number;
    truncated_item_count: number;
    cluster_count: number;
    raw_payload_echoed: boolean;
    [key: string]: unknown;
  };
  clusters: MaintenanceFeedbackIssueCluster[];
  privacy: MaintenancePrivacyBoundary & {
    retained_fields?: string[];
    redacted_patterns?: string[];
  };
};

type MaintenanceFeedbackIssueClustersResponse = {
  success: boolean;
  data: MaintenanceFeedbackIssueClusters;
};

export type MaintenanceEvidenceBundleIntegrity = {
  status: string;
  score: number;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    evidence_count: number;
    duplicate_group_count: number;
    missing_source_count: number;
    missing_proof_purpose_count: number;
    metadata_gap_total: number;
    ready_for_review: boolean;
  };
  duplicate_groups: Array<{
    group_id: string;
    match_on: string;
    count: number;
    evidence_ids: string[];
    recommended_action: string;
  }>;
  missing_source_ids: string[];
  missing_proof_purpose_ids: string[];
  metadata_gap_counts: Record<string, number>;
  item_reviews: Array<{
    evidence_id: string;
    safe_hash: string;
    status: string;
    missing_fields: string[];
    metadata_gaps: string[];
    duplicate_group_ids: string[];
    privacy_flags: string[];
  }>;
  recommended_actions: string[];
  privacy_notes: string[];
  validation_commands: string[];
};

type MaintenanceEvidenceBundleIntegrityResponse = {
  success: boolean;
  data: MaintenanceEvidenceBundleIntegrity;
};

export type MaintenancePrivacyRetentionRules = {
  status: string;
  policy_version: string;
  default_rules: Array<{
    artifact_type: string;
    retention_days: number;
    delete_trigger: string;
    requires_reviewer_confirmation: boolean;
  }>;
  evaluations: Array<{
    artifact_id: string;
    retention_class: string;
    retention_days: number | null;
    delete_trigger: string;
    requires_reviewer_confirmation: boolean;
    reason_codes: string[];
  }>;
  summary: {
    rule_count: number;
    evaluated_artifact_count: number;
    manual_confirmation_count: number;
    unknown_artifact_count: number;
  };
  recommended_actions: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenancePrivacyRetentionRulesResponse = {
  success: boolean;
  data: MaintenancePrivacyRetentionRules;
};

export type MaintenanceReleaseClaimCompliance = {
  status: string;
  policy_version: string;
  claim_checks: Array<{
    claim_hash: string;
    status: string;
    reason_codes: string[];
    matched_document_types?: string[];
    unsupported_document_types?: string[];
  }>;
  summary: {
    claim_count: number;
    blocked_count: number;
    review_required_count: number;
    ready_count: number;
    supported_type_claim_count?: number;
    unsupported_type_claim_count?: number;
  };
  recommended_actions: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenanceReleaseClaimComplianceResponse = {
  success: boolean;
  data: MaintenanceReleaseClaimCompliance;
};

export type MaintenanceLegalDocumentCoverageClaimPolicy = MaintenanceReleaseClaimCompliance & {
  coverage_summary: {
    coverage_status: string;
    target_document_type_count: number;
    covered_document_type_count: number;
    missing_document_type_count: number;
    covered_document_types: string[];
    source_endpoint: string;
  };
  allowed_claim_template: string;
  forbidden_claim_examples: string[];
  research_calibration: Array<{
    id: string;
    source_url: string;
    scope: string;
    local_boundary: string;
  }>;
};

type MaintenanceLegalDocumentCoverageClaimPolicyResponse = {
  success: boolean;
  data: MaintenanceLegalDocumentCoverageClaimPolicy;
};

export type MaintenanceCaseExportReadiness = {
  status: string;
  required_sections: string[];
  present_sections: string[];
  missing_sections: string[];
  selected_source_validation_status: string;
  reason_codes: string[];
  recommended_actions: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenanceCaseExportReadinessResponse = {
  success: boolean;
  data: MaintenanceCaseExportReadiness;
};

export type MaintenanceAdminAuditPolicy = {
  status: string;
  policy_version: string;
  checks: Array<{
    action_type: string;
    risk_level: string;
    approval_required: boolean;
    audit_required: boolean;
    reason_codes: string[];
  }>;
  summary: {
    action_count: number;
    approval_required_count: number;
    high_risk_count: number;
  };
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenanceAdminAuditPolicyResponse = {
  success: boolean;
  data: MaintenanceAdminAuditPolicy;
};

export type MaintenanceQuotaDeliveryDecision = {
  status: string;
  action: string;
  action_label: string;
  reason_codes: string[];
  quota_window?: string | null;
  reports_remaining?: number | null;
  report_quota_monthly?: number | null;
  decision: string;
  required_next_steps: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenanceQuotaDeliveryDecisionResponse = {
  success: boolean;
  data: MaintenanceQuotaDeliveryDecision;
};

export type MaintenanceSelectedSourceBinding = {
  status: string;
  binding: {
    status: string;
    delivery_status: string;
    reason_codes: string[];
    selected_source_ids: string[];
    cited_source_ids: string[];
    unexpected_source_ids: string[];
    missing_selected_source_ids: string[];
    stale_source_ids: string[];
    unknown_source_ids: string[];
    counts: Record<string, number>;
    privacy_boundary: MaintenancePrivacyBoundary;
  };
  privacy_boundary: MaintenancePrivacyBoundary;
};

type MaintenanceSelectedSourceBindingResponse = {
  success: boolean;
  data: MaintenanceSelectedSourceBinding;
};

export type MaintenanceLegalRagExportReadinessPacket = {
  id: 'legal-rag-export-readiness-packet' | string;
  title: string;
  status: string;
  release_action: string;
  summary: {
    check_count: number;
    ready_check_count: number;
    review_check_count: number;
    blocked_check_count: number;
    selected_source_count: number;
    cited_source_count: number;
    unexpected_source_count: number;
    missing_required_section_count: number;
    reason_code_count: number;
    raw_report_returned: boolean;
    model_calls: boolean;
    network_calls: boolean;
    [key: string]: unknown;
  };
  checks: Array<{
    id: string;
    title: string;
    status: string;
    reason_codes: string[];
    release_gate_link: string;
  }>;
  selected_source_binding: {
    status: string;
    delivery_status: string;
    reason_codes: string[];
    counts: Record<string, number>;
    unexpected_source_ids: string[];
    missing_selected_source_ids: string[];
    stale_source_ids: string[];
    unknown_source_ids: string[];
  };
  export_readiness: {
    status: string;
    present_sections: string[];
    missing_sections: string[];
    selected_source_validation_status?: string;
    reason_codes: string[];
  };
  linked_release_gates: string[];
  reason_codes: string[];
  recommended_actions: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceLegalRagExportReadinessPacketResponse = {
  success: boolean;
  data: MaintenanceLegalRagExportReadinessPacket;
};

export type MaintenanceContinuousSessionTimelineEvent = {
  id: string;
  event_type: string;
  title?: string;
  timestamp?: string | null;
  status?: string;
  ledger_entry_id?: string | null;
  evidence_paths?: string[];
  notes?: string[];
  [key: string]: unknown;
};

export type MaintenanceContinuousSessionTimelineBlocker = {
  id?: string;
  code?: string;
  title?: string;
  detail?: string;
  required_action?: string;
  [key: string]: unknown;
};

export type MaintenanceContinuousSessionTimeline = {
  status: string;
  summary: {
    verified_hours?: number;
    remaining_hours?: number;
    verified_continuous_hours?: number;
    continuous_hours_remaining?: number;
    ledger_count?: number;
    completed_medium_large_update_count?: number;
    event_count?: number;
    [key: string]: unknown;
  };
  timeline_events: MaintenanceContinuousSessionTimelineEvent[];
  blockers: Array<string | MaintenanceContinuousSessionTimelineBlocker>;
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceContinuousSessionTimelineResponse = {
  success: boolean;
  data: MaintenanceContinuousSessionTimeline;
};

export type MaintenanceContinuousSessionRunMonitorRequiredEvidence = {
  event_type: string;
  status: string;
  description: string;
  fixture_evidence_status?: string;
  observed_fixture_count?: number;
  archived_fixture_count?: number;
  release_ready?: boolean;
  source_endpoints?: Record<string, string>;
  [key: string]: unknown;
};

export type MaintenanceContinuousSessionRunMonitorBlocker = {
  id: string;
  severity?: string;
  detail?: string;
  [key: string]: unknown;
};

export type MaintenanceContinuousSessionRunMonitorAction = {
  id: string;
  priority?: string;
  detail?: string;
  [key: string]: unknown;
};

export type MaintenanceContinuousSessionRunMonitor = {
  status: string;
  summary: {
    target_continuous_hours: number;
    target_medium_large_update_count: number;
    completed_medium_large_update_count: number;
    update_count_ready: boolean;
    event_count: number;
    submitted_event_count: number;
    valid_event_count: number;
    invalid_event_count: number;
    verified_continuous_hours: number;
    continuous_hours_remaining: number;
    elapsed_hours_since_start: number;
    max_allowed_gap_hours: number;
    current_gap_hours: number | null;
    checkpoint_interval_hours: number;
    next_checkpoint_due_at: string | null;
    next_checkpoint_due_in_hours: number;
    required_evidence_ready_count: number;
    required_evidence_count: number;
    blocker_count: number;
    low_resource_fixture_evidence_status?: string;
    low_resource_fixture_evidence_ready?: boolean;
    low_resource_fixture_evidence_release_ready?: boolean;
    low_resource_fixture_evidence_observed_count?: number;
    low_resource_fixture_evidence_archived_count?: number;
    low_resource_fixture_evidence_blocking_count?: number;
    low_resource_fixture_evidence_raw_payload_echoed?: boolean;
    raw_payload_echoed: boolean;
    newapi_called: boolean;
    completion_ready: boolean;
    [key: string]: unknown;
  };
  run_window: {
    start_timestamp: string | null;
    latest_event_timestamp: string | null;
    current_timestamp: string | null;
    best_window: Record<string, unknown>;
  };
  low_resource_fixture_evidence?: MaintenanceLowResourceFixtureEvidence;
  required_evidence: MaintenanceContinuousSessionRunMonitorRequiredEvidence[];
  blockers: MaintenanceContinuousSessionRunMonitorBlocker[];
  next_actions: MaintenanceContinuousSessionRunMonitorAction[];
  checkpoint_policy: {
    checkpoint_interval_hours: number;
    max_allowed_gap_hours: number;
    required_event_types: string[];
    rule: string;
    [key: string]: unknown;
  };
  source_summaries: {
    ledger: Record<string, unknown>;
    timeline: Record<string, unknown>;
    review_packet: Record<string, unknown>;
    low_resource_fixture_evidence?: {
      status?: string;
      review_status?: string;
      archive_status?: string;
      observed_fixture_count?: number;
      archived_fixture_count?: number;
      blocking_check_count?: number;
      warning_check_count?: number;
      release_ready?: boolean;
      raw_payload_echoed?: boolean;
      raw_gateway_response_included?: boolean;
      raw_model_output_included?: boolean;
      [key: string]: unknown;
    };
  };
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceContinuousSessionRunMonitorResponse = {
  success: boolean;
  data: MaintenanceContinuousSessionRunMonitor;
};

export type MaintenanceGitHistoryEvidenceCommitEvent = {
  commit_hash: string;
  timestamp?: string | null;
  committed_at?: string;
  title?: string;
  subject?: string;
  status?: string;
  missing_fields?: string[];
  author?: string;
  evidence_paths?: string[];
  [key: string]: unknown;
};

export type MaintenanceGitHistoryEvidenceGap = {
  id?: string;
  start?: string | null;
  end?: string | null;
  gap_hours?: number;
  status?: string;
  detail?: string;
  [key: string]: unknown;
};

export type MaintenanceGitHistoryEvidence = {
  status: string;
  summary: {
    commit_count?: number;
    longest_window_hours?: number;
    max_observed_gap_hours?: number;
    max_gap_hours?: number;
    start_timestamp?: string | null;
    end_timestamp?: string | null;
    commit_cadence_ready?: boolean;
    ready_for_goal_claim?: boolean;
    completion_claim_ready?: boolean;
    completion_claim_blocked?: boolean;
    [key: string]: unknown;
  };
  longest_window: {
    start_timestamp?: string | null;
    end_timestamp?: string | null;
    verified_hours?: number;
    duration_hours?: number;
    commit_count?: number;
    max_observed_gap_hours?: number;
    max_gap_hours?: number;
    [key: string]: unknown;
  };
  commit_events: MaintenanceGitHistoryEvidenceCommitEvent[];
  gap_analysis: MaintenanceGitHistoryEvidenceGap[];
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceGitHistoryEvidenceResponse = {
  success: boolean;
  data: MaintenanceGitHistoryEvidence;
};

export type MaintenanceValidationEventType = 'test' | 'credential_scan' | 'push' | 'review' | 'legal_fixture';

export type MaintenanceValidationEventEvidenceReview = {
  event_type: MaintenanceValidationEventType | string;
  status?: string;
  count?: number;
  missing?: boolean;
  reviewer_note?: string;
  [key: string]: unknown;
};

export type MaintenanceValidationEventEvidence = {
  status: string;
  summary: {
    event_type_counts?: Partial<Record<MaintenanceValidationEventType | string, number>>;
    counts?: Partial<Record<MaintenanceValidationEventType | string, number>>;
    test_count?: number;
    credential_scan_count?: number;
    push_count?: number;
    review_count?: number;
    legal_fixture_count?: number;
    normalized_event_count?: number;
    normalized_session_event_count?: number;
    [key: string]: unknown;
  };
  normalized_session_events: Array<{
    event_type?: MaintenanceValidationEventType | string;
    timestamp?: string | null;
    status?: string;
    [key: string]: unknown;
  }>;
  event_reviews: MaintenanceValidationEventEvidenceReview[];
  missing_event_types: Array<MaintenanceValidationEventType | string>;
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceValidationEventEvidenceResponse = {
  success: boolean;
  data: MaintenanceValidationEventEvidence;
};

export type MaintenanceContinuousSessionReviewPacketSection = {
  id: string;
  title: string;
  status: string;
  severity?: string;
  detail?: string;
  evidence_paths?: string[];
};

export type MaintenanceContinuousSessionReviewPacketBlocker = {
  id: string;
  severity?: string;
  detail?: string;
};

export type MaintenanceContinuousSessionReviewPacket = {
  status: string;
  summary: {
    update_count_ready?: boolean;
    timeline_completion_ready?: boolean;
    git_cadence_ready?: boolean;
    validation_events_ready?: boolean;
    low_resource_fixture_review_status?: string;
    low_resource_fixture_review_ready?: boolean;
    low_resource_fixture_review_release_ready?: boolean;
    low_resource_fixture_review_observed_count?: number;
    low_resource_fixture_review_not_run_count?: number;
    low_resource_fixture_review_redacted_count?: number;
    low_resource_fixture_review_blocking_count?: number;
    low_resource_fixture_review_warning_count?: number;
    low_resource_fixture_review_blocked?: boolean;
    low_resource_fixture_review_raw_payload_echoed?: boolean;
    packet_ready_for_support_claim?: boolean;
    blocker_count?: number;
    packet_hash?: string;
    raw_payload_echoed?: boolean;
    [key: string]: unknown;
  };
  source_summaries?: {
    low_resource_fixture_review?: {
      status?: string;
      release_ready?: boolean;
      observed_fixture_count?: number;
      not_run_fixture_count?: number;
      redacted_response_count?: number;
      blocking_check_count?: number;
      warning_check_count?: number;
      raw_payload_echoed?: boolean;
      raw_gateway_response_included?: boolean;
      raw_model_output_included?: boolean;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  packet_sections: MaintenanceContinuousSessionReviewPacketSection[];
  reviewer_questions: string[];
  blockers: MaintenanceContinuousSessionReviewPacketBlocker[];
  privacy_boundary: MaintenancePrivacyBoundary;
  validation_commands: string[];
};

type MaintenanceContinuousSessionReviewPacketResponse = {
  success: boolean;
  data: MaintenanceContinuousSessionReviewPacket;
};

export type MaintenanceContinuousSessionEvidence = {
  status: string;
  summary: {
    target_continuous_hours: number;
    target_medium_large_update_count: number;
    completed_medium_large_update_count: number;
    remaining_medium_large_update_count: number;
    event_count: number;
    valid_event_count: number;
    invalid_event_count: number;
    max_allowed_gap_hours: number;
    verified_continuous_hours: number;
    continuous_hours_remaining: number;
    required_event_types: string[];
    missing_event_types: string[];
    low_resource_test_evidence: boolean;
    ready_for_goal_claim: boolean;
    raw_payload_echoed: boolean;
  };
  best_window: {
    start_timestamp: string | null;
    end_timestamp: string | null;
    record_count: number;
    event_types: string[];
    record_ids: string[];
    verified_continuous_hours: number;
    max_observed_gap_hours: number;
  };
  gap_analysis: Array<{
    id: string;
    status: string;
    detail: string;
  }>;
  privacy_note: string;
  validation_commands: string[];
};

type MaintenanceContinuousSessionEvidenceResponse = {
  success: boolean;
  data: MaintenanceContinuousSessionEvidence;
};

export type MaintenanceGateSnapshotCount = {
  label: string;
  value: string | number | boolean | null | undefined;
};

export type MaintenanceGateSnapshotItem = {
  id: string;
  label: string;
  endpoint: string;
  method: 'GET' | 'POST';
  status: string;
  counts: MaintenanceGateSnapshotCount[];
  reason_codes: string[];
  privacy_boundary: MaintenancePrivacyBoundary;
};

export type MaintenanceGateSnapshot = {
  status: string;
  summary: {
    gate_count: number;
    ready_count: number;
    blocked_count: number;
    review_required_count: number;
    reason_code_count: number;
    metadata_only_count: number;
    raw_boundary_violation_count: number;
    unsupported_claim_reason_count: number;
  };
  labels: string[];
  gates: MaintenanceGateSnapshotItem[];
};

const syntheticFeedbackIssueClusterPayload = {
  items: [
    {
      id: 'ticket-upload-1',
      content: 'PDF upload timed out during extraction for a lawyer.',
      segment: 'lawyer',
      tags: ['desktop'],
    },
    {
      id: 'ticket-export-1',
      content: 'Exported DOCX layout needs review before delivery.',
      segment: 'legal_ops',
    },
  ],
};

const syntheticEvidenceBundleIntegrityPayload = {
  items: [
    {
      evidence_id: 'EV-001',
      source_id: 'upload-001',
      proof_purpose: 'Proves contract formation metadata.',
      evidence_date: '2026-05-01',
      amount: '120000.00',
      content_hash: 'sha256:contract-001',
      file_name: 'contract.pdf',
    },
    {
      evidence_id: 'EV-002',
      source_id: 'upload-002',
      proof_purpose: '',
      evidence_date: '2026-05-03',
      amount: '30000',
      content_hash: 'sha256:contract-001',
      file_name: 'payment-record.pdf',
    },
  ],
};

const syntheticPrivacyRetentionRulesPayload = {
  artifacts: [
    { artifact_id: 'report-001', artifact_type: 'deep_review_report' },
    { artifact_id: 'quota-001', artifact_type: 'quota_usage_event' },
  ],
};

const syntheticReleaseClaimCompliancePayload = {
  claims: [
    'Repository-backed maintenance evidence is available.',
    'LegalBench score and payment provider verified claims require removal.',
  ],
};

const syntheticLegalDocumentCoverageClaimPolicyPayload = {
  claims: [
    'Repository tests include synthetic local fixtures covering civil complaint, lawyer letter, contract review, evidence catalog, settlement agreement, and legal opinion.',
    'The product supports every legal document and is validated on real client documents with LegalBench leaderboard results.',
  ],
};

const syntheticCaseExportReadinessPayload = {
  report: {
    report_meta: { selected_source_validation: { delivery_status: 'ready' } },
    risk_scoring: { overall_score: 20 },
    citations: [{ source_id: 'law:contract-001' }],
    evidence: [{ evidence_id: 'EV-001' }],
    release_decision: { status: 'ready' },
  },
};

const syntheticAdminAuditPolicyPayload = {
  actions: [
    { action_type: 'override_quota', actor_role: 'admin' },
    { action_type: 'view_dashboard', actor_role: 'admin' },
  ],
};

const syntheticQuotaDeliveryDecisionPayload = {
  action: 'deliver_to_client',
  quota_summary: {
    decision_status: 'blocked',
    reason_codes: ['report_quota_exhausted'],
    reports_remaining: 0,
    report_quota_monthly: 20,
    quota_window: '2026-06',
  },
  release_decision: { status: 'ready' },
};

const syntheticSelectedSourceBindingPayload = {
  report: {
    report_meta: { report_id: 'RPT-001' },
    citation_map: { citations: [{ source_id: 'law:contract-001' }] },
    generation_plan: { steps: [{ selected_source_binding_checked: true }] },
  },
  request_metadata: { legal_rag_selected_source_ids: ['law:contract-001'] },
  block_on_failure: true,
};

const syntheticLegalRagExportReadinessPacketPayload = {
  report: {
    report_meta: { report_id: 'RAG-EXPORT-001' },
    risk_scoring: { overall_score: 18, overall_level: 'low' },
    citations: [{ source_id: 'law:contract-001' }],
    citation_map: { citations: [{ source_id: 'law:contract-001' }] },
    generation_plan: { steps: [{ selected_source_binding_checked: true }] },
    evidence: [{ evidence_id: 'EV-001' }],
    release_decision: { status: 'ready' },
  },
  request_metadata: { legal_rag_selected_source_ids: ['law:contract-001'] },
  block_on_failure: true,
};

function unwrapMaintenanceData<T>(resp: unknown): T {
  const outer = resp as { data?: unknown } | null | undefined;
  const payload = (outer?.data ?? resp) as { success: boolean; data: T } | T;
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return (payload as { success: boolean; data: T }).data;
  }
  return payload as T;
}

function uniqueCodes(...values: Array<string[] | undefined>): string[] {
  return Array.from(new Set(values.flatMap((value) => value ?? []).filter(Boolean))).sort();
}

function allClaimReasonCodes(claims: MaintenanceReleaseClaimCompliance): string[] {
  return uniqueCodes(...claims.claim_checks.map((claim) => claim.reason_codes));
}

function isRawBoundaryClean(boundary: MaintenancePrivacyBoundary): boolean {
  return !(
    boundary.raw_feedback_echoed === true ||
    boundary.raw_document_text_included === true ||
    boundary.raw_legal_text_included === true ||
    boundary.raw_claim_text_included === true ||
    boundary.raw_payload_included === true ||
    boundary.pii_returned === true ||
    boundary.pii_included === true ||
    boundary.secret_included === true ||
    boundary.provider_payload_included === true ||
    boundary.billing_provider_payload_included === true ||
    boundary.user_claims_included === true
  );
}

function snapshotStatus(gates: MaintenanceGateSnapshotItem[]): string {
  if (gates.some((gate) => gate.status === 'blocked' || gate.status === 'fail')) return 'blocked';
  if (gates.some((gate) => gate.status === 'review_required' || gate.status === 'review_recommended')) {
    return 'review_required';
  }
  if (gates.some((gate) => gate.status === 'collecting' || gate.status === 'in_progress')) {
    return 'in_progress';
  }
  return 'ready';
}

function unsupportedClaimReasonCount(reasonCodes: string[]): number {
  return reasonCodes.filter((code) => code.includes('benchmark') || code.includes('payment')).length;
}

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

export async function getUserNeedBenchmarkCoverage(): Promise<UserNeedBenchmarkCoverage> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/user-needs/benchmark-coverage',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as UserNeedBenchmarkCoverageResponse | UserNeedBenchmarkCoverage;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as UserNeedBenchmarkCoverage;
}

export async function getUserNeedGeminiRouteCoverage(): Promise<UserNeedGeminiRouteCoverage> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/user-needs/gemini-route-coverage',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as UserNeedGeminiRouteCoverageResponse | UserNeedGeminiRouteCoverage;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as UserNeedGeminiRouteCoverage;
}

export async function getUserNeedImplementationPriorityQueue(): Promise<UserNeedImplementationPriorityQueue> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/user-needs/implementation-priority-queue',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as
    | UserNeedImplementationPriorityQueueResponse
    | UserNeedImplementationPriorityQueue;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as UserNeedImplementationPriorityQueue;
}

export async function getFrontendUiRegressionGate(): Promise<FrontendUiRegressionGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/frontend-ui-regression-gate',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as FrontendUiRegressionGateResponse | FrontendUiRegressionGate;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as FrontendUiRegressionGate;
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

export async function reviewContinuousUpdateLedger(payload: Record<string, unknown>): Promise<ContinuousUpdateLedger> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-update-ledger',
    method: 'POST',
    data: payload,
  });
  const response = (resp?.data ?? resp) as ContinuousUpdateLedgerResponse | ContinuousUpdateLedger;
  if ('success' in response && 'data' in response) {
    return response.data;
  }
  return response as ContinuousUpdateLedger;
}

export async function getMaintenanceContinuousSessionTimeline(): Promise<MaintenanceContinuousSessionTimeline> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-timeline',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionTimelineResponse['data']>(resp);
}

export async function getMaintenanceContinuousSessionRunMonitor(): Promise<MaintenanceContinuousSessionRunMonitor> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-run-monitor',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionRunMonitorResponse['data']>(resp);
}

export async function postMaintenanceContinuousSessionRunMonitor(
  payload: Record<string, unknown> = {},
): Promise<MaintenanceContinuousSessionRunMonitor> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-run-monitor',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionRunMonitorResponse['data']>(resp);
}

export async function getMaintenanceGitHistoryEvidence(): Promise<MaintenanceGitHistoryEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/git-history-evidence',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceGitHistoryEvidenceResponse['data']>(resp);
}

export async function getMaintenanceValidationEventEvidence(): Promise<MaintenanceValidationEventEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/validation-event-evidence',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceValidationEventEvidenceResponse['data']>(resp);
}

export async function postMaintenanceValidationEventEvidence(
  payload: Record<string, unknown>,
): Promise<MaintenanceValidationEventEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/validation-event-evidence',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceValidationEventEvidenceResponse['data']>(resp);
}

export async function getMaintenanceContinuousSessionReviewPacket(): Promise<MaintenanceContinuousSessionReviewPacket> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-review-packet',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionReviewPacketResponse['data']>(resp);
}

export async function postMaintenanceContinuousSessionReviewPacket(
  payload: Record<string, unknown>,
): Promise<MaintenanceContinuousSessionReviewPacket> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-review-packet',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionReviewPacketResponse['data']>(resp);
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

export async function getMatterAuditRetentionPolicy(): Promise<MatterAuditRetentionPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/matter-audit-retention-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as MatterAuditRetentionPolicyResponse | MatterAuditRetentionPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as MatterAuditRetentionPolicy;
}

export async function getLawyerReviewWorkflowPolicy(): Promise<LawyerReviewWorkflowPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/lawyer-review-workflow-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LawyerReviewWorkflowPolicyResponse | LawyerReviewWorkflowPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LawyerReviewWorkflowPolicy;
}

export async function getEvidenceExhibitPackagePolicy(): Promise<EvidenceExhibitPackagePolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/evidence-exhibit-package-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as EvidenceExhibitPackagePolicyResponse | EvidenceExhibitPackagePolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as EvidenceExhibitPackagePolicy;
}

export async function getCaseTaskNotificationPolicy(): Promise<CaseTaskNotificationPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case-task-notification-policy',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as CaseTaskNotificationPolicyResponse | CaseTaskNotificationPolicy;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as CaseTaskNotificationPolicy;
}

export async function getCaseWorkbenchPayload(): Promise<CaseWorkbenchPayload> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case-workbench-payload',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as CaseWorkbenchPayloadResponse | CaseWorkbenchPayload;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as CaseWorkbenchPayload;
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

export async function getLegalDocumentBenchmarkCoverage(): Promise<LegalDocumentBenchmarkCoverage> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/document-coverage',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as
    | LegalDocumentBenchmarkCoverageResponse
    | LegalDocumentBenchmarkCoverage;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalDocumentBenchmarkCoverage;
}

export async function getLegalDocumentFactConsistencyBenchmark(): Promise<LegalDocumentFactConsistencyBenchmark> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/document-fact-consistency',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as
    | LegalDocumentFactConsistencyBenchmarkResponse
    | LegalDocumentFactConsistencyBenchmark;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalDocumentFactConsistencyBenchmark;
}

export async function evaluateLegalDocumentFactConsistencyBenchmark(
  outputs: Record<string, unknown> = {},
): Promise<LegalDocumentFactConsistencyEvaluation> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/document-fact-consistency',
    method: 'POST',
    data: outputs,
  });
  const payload = (resp?.data ?? resp) as
    | LegalDocumentFactConsistencyEvaluationResponse
    | LegalDocumentFactConsistencyEvaluation;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalDocumentFactConsistencyEvaluation;
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

export async function getLegalAdoptionResearchBridge(): Promise<LegalAdoptionResearchBridge> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/adoption-research-bridge',
    method: 'GET',
  });
  return unwrapMaintenanceData<LegalAdoptionResearchBridgeResponse['data']>(resp);
}

export async function getLegalBenchmarkResearchRegistry(): Promise<LegalBenchmarkResearchRegistry> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/research-registry',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalBenchmarkResearchRegistryResponse | LegalBenchmarkResearchRegistry;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalBenchmarkResearchRegistry;
}

export async function getLegalBenchmarkResearchRefresh(): Promise<LegalBenchmarkResearchRefresh> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-benchmark-research-refresh',
    method: 'GET',
  });
  return unwrapMaintenanceData<LegalBenchmarkResearchRefreshResponse['data']>(resp);
}

export async function getModelRouteLegalBenchmarkRiskQueue(): Promise<ModelRouteLegalBenchmarkRiskQueue> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/model-route-legal-benchmark-risk-queue',
    method: 'GET',
  });
  return unwrapMaintenanceData<ModelRouteLegalBenchmarkRiskQueueResponse['data']>(resp);
}

export async function getModelOpsLegalFixtureCheapFirstBenchmarkGate(): Promise<ModelOpsLegalFixtureCheapFirstBenchmarkGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate',
    method: 'GET',
  });
  return unwrapMaintenanceData<ModelOpsLegalFixtureCheapFirstBenchmarkGate>(resp);
}

export async function getModelOpsLegalFixtureCheapFirstDefaultPromotionPacket(): Promise<ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet',
    method: 'GET',
  });
  return unwrapMaintenanceData<ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket>(resp);
}

export async function getLegalRagAuthorityCitationGate(): Promise<LegalRagAuthorityCitationGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag-authority-citation-gate',
    method: 'GET',
  });
  const payload = unwrapMaintenanceData<LegalRagAuthorityCitationGateResponse['data']>(resp);
  if ('legalRagAuthorityCitationGate' in payload) {
    return payload.legalRagAuthorityCitationGate;
  }
  return payload;
}

export async function getLegalRagHallucinationTriageGate(): Promise<LegalRagHallucinationTriageGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag-hallucination-triage-gate',
    method: 'GET',
  });
  const payload = unwrapMaintenanceData<LegalRagHallucinationTriageGateResponse['data']>(resp);
  if ('legalRagHallucinationTriageGate' in payload) {
    return payload.legalRagHallucinationTriageGate;
  }
  return payload;
}

export async function getLegalRagAbstentionEscalationGate(): Promise<LegalRagAbstentionEscalationGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag-abstention-escalation-gate',
    method: 'GET',
  });
  const payload = unwrapMaintenanceData<LegalRagAbstentionEscalationGateResponse['data']>(resp);
  if ('legal_rag_abstention_escalation_gate' in payload && payload.legal_rag_abstention_escalation_gate) {
    return payload.legal_rag_abstention_escalation_gate;
  }
  if ('legalRagAbstentionEscalationGate' in payload && payload.legalRagAbstentionEscalationGate) {
    return payload.legalRagAbstentionEscalationGate;
  }
  return payload as LegalRagAbstentionEscalationGate;
}

export async function getLegalRagRetrievalDiagnosticsGate(): Promise<LegalRagRetrievalDiagnosticsGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag-retrieval-diagnostics-gate',
    method: 'GET',
  });
  return unwrapMaintenanceData<LegalRagRetrievalDiagnosticsGateResponse['data']>(resp);
}

export async function getLegalRagBenchmarkAlignment(): Promise<LegalRagBenchmarkAlignment> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag-benchmark-alignment',
    method: 'GET',
  });
  return unwrapMaintenanceData<LegalRagBenchmarkAlignmentResponse['data']>(resp);
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

export async function getLegalPublicBenchmarkLicenseGate(): Promise<LegalPublicBenchmarkLicenseGate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/public-license-gate',
    method: 'GET',
  });
  return unwrapMaintenanceData<LegalPublicBenchmarkLicenseGateResponse['data']>(resp);
}

export async function getLegalBenchmarkFixtureCrosswalk(): Promise<LegalBenchmarkFixtureCrosswalk> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk',
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as LegalBenchmarkFixtureCrosswalkResponse | LegalBenchmarkFixtureCrosswalk;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as LegalBenchmarkFixtureCrosswalk;
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

export async function reviewLegalFixtureLocalRun(payload: Record<string, unknown>): Promise<LegalFixtureLocalRunReview> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/local-run-review',
    method: 'POST',
    data: payload,
  });
  const response = (resp?.data ?? resp) as LegalFixtureLocalRunReviewResponse | LegalFixtureLocalRunReview;
  if ('success' in response && 'data' in response) {
    return response.data;
  }
  return response as LegalFixtureLocalRunReview;
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

export async function getGeminiNewApiModelSelectorEvidence(): Promise<GeminiNewApiModelSelectorEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-model-selector',
    method: 'GET',
  });
  return unwrapMaintenanceData<GeminiNewApiModelSelectorEvidenceResponse['data']>(resp);
}

export async function postGeminiNewApiModelSelectorEvidence(
  payload: Record<string, unknown> = {},
): Promise<GeminiNewApiModelSelectorEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-model-selector',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<GeminiNewApiModelSelectorEvidenceResponse['data']>(resp);
}

export async function getGeminiNewApiModelAliasMatrixEvidence(): Promise<GeminiNewApiModelAliasMatrixEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-model-alias-matrix',
    method: 'GET',
  });
  return unwrapMaintenanceData<GeminiNewApiModelAliasMatrixEvidenceResponse['data']>(resp);
}

export async function postGeminiNewApiModelAliasMatrixEvidence(
  payload: Record<string, unknown> = {},
): Promise<GeminiNewApiModelAliasMatrixEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-model-alias-matrix',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<GeminiNewApiModelAliasMatrixEvidenceResponse['data']>(resp);
}

export async function getGeminiNewApiSelectorReplayEvidence(): Promise<GeminiNewApiSelectorReplayEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-selector-replay',
    method: 'GET',
  });
  return unwrapMaintenanceData<GeminiNewApiSelectorReplayEvidenceResponse['data']>(resp);
}

export async function postGeminiNewApiSelectorReplayEvidence(
  payload: Record<string, unknown> = {},
): Promise<GeminiNewApiSelectorReplayEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/gemini-newapi-selector-replay',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<GeminiNewApiSelectorReplayEvidenceResponse['data']>(resp);
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

export async function getMaintenanceFeedbackIssueClusters(
  payload: Record<string, unknown> = syntheticFeedbackIssueClusterPayload,
): Promise<MaintenanceFeedbackIssueClusters> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/feedback/issue-clusters',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceFeedbackIssueClustersResponse['data']>(resp);
}

export async function getMaintenanceEvidenceBundleIntegrity(
  payload: Record<string, unknown> = syntheticEvidenceBundleIntegrityPayload,
): Promise<MaintenanceEvidenceBundleIntegrity> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/evidence/bundle-integrity',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceEvidenceBundleIntegrityResponse['data']>(resp);
}

export async function getMaintenancePrivacyRetentionRules(
  payload: Record<string, unknown> = syntheticPrivacyRetentionRulesPayload,
): Promise<MaintenancePrivacyRetentionRules> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/privacy/retention-rules',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenancePrivacyRetentionRulesResponse['data']>(resp);
}

export async function getMaintenanceReleaseClaimCompliance(
  payload: Record<string, unknown> = syntheticReleaseClaimCompliancePayload,
): Promise<MaintenanceReleaseClaimCompliance> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/compliance/release-claims',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceReleaseClaimComplianceResponse['data']>(resp);
}

export async function getMaintenanceLegalDocumentCoverageClaimPolicy(
  payload: Record<string, unknown> = syntheticLegalDocumentCoverageClaimPolicyPayload,
): Promise<MaintenanceLegalDocumentCoverageClaimPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-review-benchmark/document-coverage/claims',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceLegalDocumentCoverageClaimPolicyResponse['data']>(resp);
}

export async function getMaintenanceCaseExportReadiness(
  payload: Record<string, unknown> = syntheticCaseExportReadinessPayload,
): Promise<MaintenanceCaseExportReadiness> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/case/export-readiness',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceCaseExportReadinessResponse['data']>(resp);
}

export async function getMaintenanceAdminAuditPolicy(
  payload: Record<string, unknown> = syntheticAdminAuditPolicyPayload,
): Promise<MaintenanceAdminAuditPolicy> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/admin/audit-policy',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceAdminAuditPolicyResponse['data']>(resp);
}

export async function getMaintenanceQuotaDeliveryDecision(
  payload: Record<string, unknown> = syntheticQuotaDeliveryDecisionPayload,
): Promise<MaintenanceQuotaDeliveryDecision> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/billing/quota-delivery-decision',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceQuotaDeliveryDecisionResponse['data']>(resp);
}

export async function getMaintenanceSelectedSourceBinding(
  payload: Record<string, unknown> = syntheticSelectedSourceBindingPayload,
): Promise<MaintenanceSelectedSourceBinding> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/deep-review/selected-source-binding',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceSelectedSourceBindingResponse['data']>(resp);
}

export async function getMaintenanceLegalRagExportReadinessPacket(
  payload: Record<string, unknown> = syntheticLegalRagExportReadinessPacketPayload,
): Promise<MaintenanceLegalRagExportReadinessPacket> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/legal-rag/export-readiness-packet',
    method: 'POST',
    data: payload,
  });
  return unwrapMaintenanceData<MaintenanceLegalRagExportReadinessPacketResponse['data']>(resp);
}

export async function getMaintenanceContinuousSessionEvidence(): Promise<MaintenanceContinuousSessionEvidence> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/continuous-session-evidence',
    method: 'GET',
  });
  return unwrapMaintenanceData<MaintenanceContinuousSessionEvidenceResponse['data']>(resp);
}

export async function getMaintenanceGateSnapshot(): Promise<MaintenanceGateSnapshot> {
  const [
    feedbackClusters,
    bundleIntegrity,
    privacyRetention,
    releaseClaims,
    legalDocumentCoverageClaims,
    caseExport,
    adminAudit,
    quotaDecision,
    selectedSourceBinding,
    legalRagExportReadinessPacket,
    continuousSessionEvidence,
  ] = await Promise.all([
    getMaintenanceFeedbackIssueClusters(),
    getMaintenanceEvidenceBundleIntegrity(),
    getMaintenancePrivacyRetentionRules(),
    getMaintenanceReleaseClaimCompliance(),
    getMaintenanceLegalDocumentCoverageClaimPolicy(),
    getMaintenanceCaseExportReadiness(),
    getMaintenanceAdminAuditPolicy(),
    getMaintenanceQuotaDeliveryDecision(),
    getMaintenanceSelectedSourceBinding(),
    getMaintenanceLegalRagExportReadinessPacket(),
    getMaintenanceContinuousSessionEvidence(),
  ]);

  const releaseClaimReasons = allClaimReasonCodes(releaseClaims);
  const legalDocumentClaimReasons = allClaimReasonCodes(legalDocumentCoverageClaims);
  const gates: MaintenanceGateSnapshotItem[] = [
    {
      id: 'feedback-issue-clusters',
      label: 'Feedback issue clusters',
      endpoint: '/api/v1/maintenance/feedback/issue-clusters',
      method: 'POST',
      status: feedbackClusters.status,
      counts: [
        { label: 'items', value: feedbackClusters.summary.processed_item_count },
        { label: 'clusters', value: feedbackClusters.summary.cluster_count },
        {
          label: 'hashed refs',
          value: feedbackClusters.clusters.reduce((total, cluster) => total + (cluster.counts.hashed_refs ?? 0), 0),
        },
      ],
      reason_codes: feedbackClusters.clusters.map((cluster) => cluster.normalized_topic),
      privacy_boundary: feedbackClusters.privacy,
    },
    {
      id: 'evidence-bundle-integrity',
      label: 'Evidence bundle integrity',
      endpoint: '/api/v1/maintenance/evidence/bundle-integrity',
      method: 'POST',
      status: bundleIntegrity.status,
      counts: [
        { label: 'evidence', value: bundleIntegrity.summary.evidence_count },
        { label: 'duplicates', value: bundleIntegrity.summary.duplicate_group_count },
        { label: 'metadata gaps', value: bundleIntegrity.summary.metadata_gap_total },
      ],
      reason_codes: uniqueCodes(
        bundleIntegrity.duplicate_groups.map((group) => `duplicate_${group.match_on}`),
        Object.entries(bundleIntegrity.metadata_gap_counts)
          .filter(([key, value]) => key !== 'total' && value > 0)
          .map(([key]) => key),
        bundleIntegrity.missing_source_ids.length ? ['missing_source_id'] : [],
        bundleIntegrity.missing_proof_purpose_ids.length ? ['missing_proof_purpose'] : [],
      ),
      privacy_boundary: {
        raw_document_text_included: false,
        pii_included: false,
        output_scope: bundleIntegrity.privacy_notes[2] ?? 'metadata-only integrity counts and safe hashes',
      },
    },
    {
      id: 'privacy-retention-rules',
      label: 'Privacy retention rules',
      endpoint: '/api/v1/maintenance/privacy/retention-rules',
      method: 'POST',
      status: privacyRetention.status,
      counts: [
        { label: 'rules', value: privacyRetention.summary.rule_count },
        { label: 'evaluated', value: privacyRetention.summary.evaluated_artifact_count },
        { label: 'manual confirms', value: privacyRetention.summary.manual_confirmation_count },
      ],
      reason_codes: uniqueCodes(...privacyRetention.evaluations.map((evaluation) => evaluation.reason_codes)),
      privacy_boundary: privacyRetention.privacy_boundary,
    },
    {
      id: 'release-claim-compliance',
      label: 'Release claim compliance',
      endpoint: '/api/v1/maintenance/compliance/release-claims',
      method: 'POST',
      status: releaseClaims.status,
      counts: [
        { label: 'claims', value: releaseClaims.summary.claim_count },
        { label: 'blocked', value: releaseClaims.summary.blocked_count },
        { label: 'review', value: releaseClaims.summary.review_required_count },
      ],
      reason_codes: releaseClaimReasons,
      privacy_boundary: releaseClaims.privacy_boundary,
    },
    {
      id: 'legal-document-coverage-claim-policy',
      label: 'Legal document coverage claim policy',
      endpoint: '/api/v1/maintenance/legal-review-benchmark/document-coverage/claims',
      method: 'POST',
      status: legalDocumentCoverageClaims.status,
      counts: [
        { label: 'claims', value: legalDocumentCoverageClaims.summary.claim_count },
        { label: 'blocked', value: legalDocumentCoverageClaims.summary.blocked_count },
        { label: 'covered types', value: legalDocumentCoverageClaims.coverage_summary.covered_document_type_count },
      ],
      reason_codes: legalDocumentClaimReasons,
      privacy_boundary: legalDocumentCoverageClaims.privacy_boundary,
    },
    {
      id: 'case-export-readiness',
      label: 'Case export readiness',
      endpoint: '/api/v1/maintenance/case/export-readiness',
      method: 'POST',
      status: caseExport.status,
      counts: [
        { label: 'required', value: caseExport.required_sections.length },
        { label: 'present', value: caseExport.present_sections.length },
        { label: 'missing', value: caseExport.missing_sections.length },
      ],
      reason_codes: caseExport.reason_codes,
      privacy_boundary: caseExport.privacy_boundary,
    },
    {
      id: 'admin-audit-policy',
      label: 'Admin audit policy',
      endpoint: '/api/v1/maintenance/admin/audit-policy',
      method: 'POST',
      status: adminAudit.status,
      counts: [
        { label: 'actions', value: adminAudit.summary.action_count },
        { label: 'approvals', value: adminAudit.summary.approval_required_count },
        { label: 'high risk', value: adminAudit.summary.high_risk_count },
      ],
      reason_codes: uniqueCodes(...adminAudit.checks.map((check) => check.reason_codes)),
      privacy_boundary: adminAudit.privacy_boundary,
    },
    {
      id: 'quota-delivery-decision',
      label: 'Quota delivery decision',
      endpoint: '/api/v1/maintenance/billing/quota-delivery-decision',
      method: 'POST',
      status: quotaDecision.status,
      counts: [
        { label: 'remaining', value: quotaDecision.reports_remaining },
        { label: 'monthly', value: quotaDecision.report_quota_monthly },
        { label: 'reasons', value: quotaDecision.reason_codes.length },
      ],
      reason_codes: quotaDecision.reason_codes,
      privacy_boundary: quotaDecision.privacy_boundary,
    },
    {
      id: 'selected-source-binding',
      label: 'Selected-source binding',
      endpoint: '/api/v1/maintenance/deep-review/selected-source-binding',
      method: 'POST',
      status: selectedSourceBinding.status,
      counts: [
        { label: 'selected', value: selectedSourceBinding.binding.counts.selected_source_count ?? 0 },
        { label: 'cited', value: selectedSourceBinding.binding.counts.cited_source_count ?? 0 },
        { label: 'unexpected', value: selectedSourceBinding.binding.unexpected_source_ids.length },
      ],
      reason_codes: selectedSourceBinding.binding.reason_codes,
      privacy_boundary: selectedSourceBinding.privacy_boundary,
    },
    {
      id: 'legal-rag-export-readiness-packet',
      label: 'Legal RAG export readiness',
      endpoint: '/api/v1/maintenance/legal-rag/export-readiness-packet',
      method: 'POST',
      status: legalRagExportReadinessPacket.status,
      counts: [
        { label: 'checks', value: legalRagExportReadinessPacket.summary.check_count },
        { label: 'blocked', value: legalRagExportReadinessPacket.summary.blocked_check_count },
        { label: 'missing sections', value: legalRagExportReadinessPacket.summary.missing_required_section_count },
      ],
      reason_codes: legalRagExportReadinessPacket.reason_codes,
      privacy_boundary: legalRagExportReadinessPacket.privacy_boundary,
    },
    {
      id: 'continuous-session-evidence',
      label: '24h session validator',
      endpoint: '/api/v1/maintenance/continuous-session-evidence',
      method: 'GET',
      status: continuousSessionEvidence.status,
      counts: [
        { label: 'verified hours', value: continuousSessionEvidence.summary.verified_continuous_hours },
        { label: 'remaining hours', value: continuousSessionEvidence.summary.continuous_hours_remaining },
        { label: 'events', value: continuousSessionEvidence.summary.event_count },
      ],
      reason_codes: uniqueCodes(
        continuousSessionEvidence.gap_analysis.map((gap) => gap.id),
        continuousSessionEvidence.summary.missing_event_types.map((eventType) => `missing_${eventType}`),
      ),
      privacy_boundary: {
        raw_payload_included: continuousSessionEvidence.summary.raw_payload_echoed,
        raw_legal_text_included: false,
        pii_included: false,
        output_scope: 'metadata-only 24h session template; no synthetic completion claim',
      },
    },
  ];
  const reasonCodes = uniqueCodes(...gates.map((gate) => gate.reason_codes));

  return {
    status: snapshotStatus(gates),
    summary: {
      gate_count: gates.length,
      ready_count: gates.filter((gate) => gate.status === 'ready').length,
      blocked_count: gates.filter((gate) => gate.status === 'blocked' || gate.status === 'fail').length,
      review_required_count: gates.filter((gate) =>
        ['review_required', 'review_recommended'].includes(gate.status),
      ).length,
      reason_code_count: reasonCodes.length,
      metadata_only_count: gates.filter((gate) => isRawBoundaryClean(gate.privacy_boundary)).length,
      raw_boundary_violation_count: gates.filter((gate) => !isRawBoundaryClean(gate.privacy_boundary)).length,
      unsupported_claim_reason_count: unsupportedClaimReasonCount(
        uniqueCodes(releaseClaimReasons, legalDocumentClaimReasons),
      ),
    },
    labels: ['metadata-only', 'no raw legal text', 'no benchmark or payment claims'],
    gates,
  };
}
