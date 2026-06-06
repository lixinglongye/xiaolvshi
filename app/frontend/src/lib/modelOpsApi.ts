import { client } from '@/lib/api';

export type RoutingAliases = Record<string, string>;

export const MODEL_OPS_API_TIMEOUT_MS = 25_000;
export const MODEL_OPS_TOTAL_TIMEOUT_MS = 25_000;

export type ModelCatalogItem = {
  id: string;
  provider: string;
  family: string;
  cost_tier: string;
  latency_tier: string;
  status: string;
  context_window_tokens?: number | null;
  capabilities: string[];
  best_for: string[];
  notes?: string;
  pricing: {
    input_usd_per_million_tokens: number | null;
    output_usd_per_million_tokens: number | null;
    output_usd_per_image: number | null;
    note: string;
    source_url?: string;
  };
  configured_roles: string[];
};

export type ModelUsageItem = {
  requests: number;
  successes: number;
  failures: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  avg_latency_ms: number;
  last_seen_at: number;
  tasks: Record<string, number>;
  estimated_cost_usd: number | null;
};

export type ModelUsageSummary = {
  totals: {
    requests: number;
    successes: number;
    failures: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
    priced_model_count: number;
    unpriced_model_count: number;
  };
  models: Record<string, ModelUsageItem>;
};

export type ModelBudgetDecision = {
  task: string;
  requested_model?: string | null;
  resolved_model: string;
  budget_mode: string;
  cost_tier?: string | null;
  max_cost_tier: string;
  is_known_model: boolean;
  is_over_budget: boolean;
  requires_operator_review: boolean;
  recommended_model: string;
  reason: string;
};

export type ModelBudgetPolicy = {
  premium_requires_review: boolean;
  cost_tier_rank: Record<string, number>;
  task_decisions: ModelBudgetDecision[];
};

export type ModelRuntimeRouter = {
  status: string;
  request_fields: Record<string, string>;
  enforcement: string[];
  auto_task_inference?: {
    status: string;
    default_task: string;
    rules: string[];
    safeguards: string[];
  };
  task_defaults: ModelBudgetDecision[];
};

export type ModelConfigurationAuditCheck = {
  id: string;
  status: string;
  label: string;
  model: string;
  env_var?: string | null;
  is_known_model: boolean;
  cost_tier?: string | null;
  max_cost_tier: string;
  preferred_cost_tier?: string | null;
  required_capabilities: string[];
  preferred_capabilities: string[];
  missing_required_capabilities: string[];
  missing_preferred_capabilities: string[];
  over_budget: boolean;
  rationale: string;
  reason: string;
};

export type ModelConfigurationAudit = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    role_count: number;
    pass_count: number;
    warn_count: number;
    fail_count: number;
    unknown_model_count: number;
    premium_default_count: number;
  };
  checks: ModelConfigurationAuditCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelDefaultTemplateAuditRow = {
  id: string;
  env_var: string;
  settings_attr: string;
  task: string;
  required_for: string;
  expected_default: string;
  source_values: Record<string, string | null | undefined>;
  missing_sources: string[];
  mismatched_sources: string[];
  status: string;
  reason: string;
};

export type ModelDefaultTemplateAudit = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    default_count: number;
    source_count: number;
    aligned_count: number;
    drift_count: number;
    missing_value_count: number;
    mismatched_value_count: number;
    agentic_grounded_defaults_visible: boolean;
  };
  source_files: Array<{ id: string; path: string }>;
  default_targets: Array<{ env_var: string; settings_attr: string; task: string; required_for: string }>;
  rows: ModelDefaultTemplateAuditRow[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type ModelDefaultOptimizationRecommendation = {
  id: string;
  task: string;
  display_name: string;
  status: string;
  source: string;
  env_var?: string | null;
  current_model: string;
  recommended_model: string;
  current_cost_tier?: string | null;
  recommended_cost_tier?: string | null;
  max_cost_tier: string;
  required_capabilities: string[];
  missing_required_capabilities: string[];
  runtime_default_is_recommended: boolean;
  requires_change: boolean;
  requires_operator_review: boolean;
  estimated_monthly_savings_usd?: number | null;
  reason: string;
};

export type ModelDefaultOptimization = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    task_count: number;
    aligned_count: number;
    change_count: number;
    manual_review_count: number;
    estimated_monthly_savings_usd: number;
    priced_task_count: number;
  };
  recommendations: ModelDefaultOptimizationRecommendation[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelGatewayCompatibilityRole = {
  id: string;
  label: string;
  env_var: string;
  model: string;
  canonical_model?: string | null;
  is_known_model: boolean;
  is_gemini_like: boolean;
  is_gateway_prefixed: boolean;
  cost_tier?: string | null;
  max_cost_tier: string;
  status: string;
  reason: string;
};

export type ModelGatewayCompatibilityExample = {
  id: string;
  model: string;
  canonical_model?: string | null;
  is_known_model: boolean;
  is_gateway_prefixed: boolean;
  status: string;
  reason: string;
};

export type ModelGatewayCompatibility = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    configured_role_count: number;
    example_count: number;
    known_configured_count: number;
    prefixed_configured_count: number;
    unknown_gemini_count: number;
    non_gemini_default_count: number;
    warning_count: number;
    blocking_count: number;
  };
  configured_roles: ModelGatewayCompatibilityRole[];
  gateway_examples: ModelGatewayCompatibilityExample[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type GeminiVariantMatrixFamilyRow = {
  family: string;
  catalog_model_count: number;
  cost_posture: string;
  default_use: string;
  high_frequency_default_allowed: boolean;
  catalog_patterns: string[];
  catalog_models: string[];
};

export type GeminiVariantMatrixModelRow = {
  model_id: string;
  family: string;
  catalog_status: string;
  cost_tier: string;
  latency_tier: string;
  route_role: string;
  high_frequency_default_allowed: boolean;
  balanced_retry_allowed: boolean;
  premium_exception_required: boolean;
  media_route_only: boolean;
  pricing_status: string;
  configured_roles: string[];
  capabilities: string[];
  supported_request_shapes: string[];
  review_note: string;
};

export type GeminiVariantMatrixObservedReview = {
  raw_model: string;
  canonical_model?: string | null;
  status: string;
  action: string;
  cost_tier?: string | null;
  default_allowed_for_high_frequency: boolean;
  warnings: string[];
};

export type GeminiVariantMatrixObservedModelExtraction = {
  extractor_version?: string;
  candidate_count: number;
  accepted_model_count: number;
  dropped_model_count: number;
  rejected_sensitive_count?: number;
  rejected_invalid_count?: number;
  rejected_model_count?: number;
  rejection_counts?: {
    sensitive?: number;
    invalid?: number;
    total?: number;
  };
  source_fields: string[];
  max_candidate_count: number;
  max_accepted_model_count: number;
  raw_payload_echoed: boolean;
  raw_rejected_values_echoed?: boolean;
  supported_model_fields?: string[];
};

export type GeminiVariantMatrix = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    catalog_model_count: number;
    family_count: number;
    high_frequency_default_allowed_count: number;
    explicit_only_model_count: number;
    preview_model_count: number;
    unpriced_model_count: number;
    observed_model_count: number;
    catalog_review_count: number;
    observed_model_candidate_count: number;
    accepted_observed_model_count: number;
    dropped_observed_model_count: number;
    rejected_sensitive_observed_model_count?: number;
    rejected_invalid_observed_model_count?: number;
    rejected_observed_model_count?: number;
    observed_model_source_count: number;
    cheap_first_default_model: string;
    raw_payload_echoed: boolean;
  };
  source_summaries?: {
    observed_model_extraction?: GeminiVariantMatrixObservedModelExtraction;
  };
  family_rows: GeminiVariantMatrixFamilyRow[];
  model_rows: GeminiVariantMatrixModelRow[];
  observed_model_reviews: GeminiVariantMatrixObservedReview[];
  prefix_compatibility: {
    gateway: string;
    request_shape: string;
    openai_compatible: boolean;
    accepted_prefix_examples: Array<{
      shape: string;
      example: string;
      normalization: string;
    }>;
    pass_through_rule: string;
  };
  unknown_model_policy: Record<string, unknown>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: {
    raw_payload_echoed: boolean;
    credentials_included: boolean;
    prompts_included: boolean;
    raw_legal_text_included: boolean;
    raw_model_output_included: boolean;
    gateway_called: boolean;
    output_scope: string;
  };
  validation_commands: string[];
};

export type ModelOpsObservedGeminiModelIntakeQueueItem = {
  id: string;
  raw_model: string;
  canonical_model?: string | null;
  catalog_status: string;
  intake_status: string;
  intake_action: string;
  release_action: string;
  known_catalog_model: boolean;
  gemini_like: boolean;
  cost_tier: string;
  model_lifecycle_status: string;
  default_allowed_for_high_frequency: boolean;
  cheap_first_default_candidate: boolean;
  allowed_default_tasks: string[];
  capabilities: string[];
  pricing_status: string;
  reason_codes: string[];
  warnings: string[];
};

export type ModelOpsObservedGeminiModelIntakeQueue = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    observed_model_count: number;
    ready_count: number;
    review_required_count: number;
    blocked_count: number;
    cheap_first_candidate_count: number;
    unknown_gemini_count: number;
    external_non_gemini_count: number;
    source_catalog_review_count: number;
    source_accepted_observed_model_count: number;
    source_dropped_observed_model_count: number;
    source_rejected_sensitive_observed_model_count?: number;
    source_rejected_invalid_observed_model_count?: number;
    source_rejected_observed_model_count?: number;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
  };
  queue_items: ModelOpsObservedGeminiModelIntakeQueueItem[];
  ready_model_ids: string[];
  review_model_ids: string[];
  blocked_model_ids: string[];
  recommended_actions: string[];
  source_summaries: Record<string, unknown>;
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type GeminiNewApiAliasCapabilityCoverageRow = {
  id: string;
  source: string;
  alias_model: string;
  canonical_model?: string | null;
  alias_shape: string;
  coverage_status: string;
  known_catalog_model: boolean;
  model_family: string;
  cost_tier: string;
  latency_tier: string;
  lifecycle_status: string;
  capabilities: string[];
  covered_tasks: string[];
  covered_high_frequency_tasks: string[];
  high_frequency_default_allowed: boolean;
  balanced_after_precheck_allowed: boolean;
  premium_or_media_review_required: boolean;
  default_allowed_without_review: boolean;
  reason_codes: string[];
  recommended_action: string;
};

export type GeminiNewApiAliasCapabilityTaskCoverage = {
  task: string;
  alias_count: number;
  high_frequency: boolean;
  route_mode: string;
  status: string;
};

export type GeminiNewApiAliasCapabilityCoverage = {
  id: 'gemini-newapi-alias-capability-coverage' | string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    coverage_row_count: number;
    catalog_model_count: number;
    alias_shape_count: number;
    known_coverage_count: number;
    review_required_count: number;
    external_model_count?: number;
    blocked_count: number;
    cheap_first_high_frequency_alias_count: number;
    balanced_after_precheck_alias_count: number;
    premium_or_media_review_alias_count: number;
    text_json_capable_alias_count: number;
    vision_ocr_capable_alias_count: number;
    grounding_capable_alias_count: number;
    agentic_capable_alias_count: number;
    image_capable_alias_count: number;
    covered_task_count: number;
    high_frequency_task_count: number;
    raw_payload_echoed: boolean;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    credentials_included: boolean;
  };
  coverage_rows: GeminiNewApiAliasCapabilityCoverageRow[];
  capability_totals: Record<string, number>;
  task_alias_coverage: GeminiNewApiAliasCapabilityTaskCoverage[];
  accepted_alias_shapes: string[];
  coverage_policy: Record<string, string>;
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  recommended_actions: string[];
  validation_commands: string[];
};

export type ModelGatewayHealthPlanRole = {
  role: string;
  model: string;
  canonical_model?: string | null;
  is_known_model: boolean;
  cost_tier?: string | null;
  model_status: string;
  billing_unit: string;
  probe_type: string;
  cheap_first_aligned: boolean;
  estimated_probe_cost_usd?: number | null;
  output_usd_per_image?: number | null;
  reason: string;
};

export type ModelGatewayHealthPlan = {
  status: string;
  method: {
    type: string;
    notes: string[];
    source_urls: string[];
  };
  summary: {
    base_url_configured: boolean;
    api_key_configured: boolean;
    normalized_base_url: string;
    configured_role_count: number;
    known_low_resource_role_count: number;
    known_media_role_count: number;
    unknown_role_count: number;
    cheap_first_low_cost_count: number;
    blocking_check_count: number;
    warning_check_count: number;
    estimated_probe_cost_usd?: number | null;
  };
  gateway_config: {
    base_url_configured: boolean;
    base_url_display: string;
    api_key_configured: boolean;
    api_key_display: string;
    timeout_seconds?: number | null;
    requires_https: boolean;
  };
  role_models: ModelGatewayHealthPlanRole[];
  dry_run_contracts: Array<{
    id: string;
    method: string;
    url: string;
    headers: Record<string, string>;
    body?: Record<string, unknown>;
    purpose: string;
    expected_success: string;
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

export type ModelGatewayProbeTemplate = {
  status: string;
  method: {
    type: string;
    notes: string[];
    source_urls: string[];
  };
  payload_shape: Record<string, unknown>;
  validation_command: string;
};

export type ModelGatewayProbeEvaluation = {
  status: string;
  source?: string;
  stored_at?: string | null;
  method: {
    type: string;
    notes: string[];
    source_urls: string[];
  };
  summary: {
    observed_model_count: number;
    known_model_count: number;
    unknown_gemini_count: number;
    chat_probe_count: number;
    chat_probe_pass_count: number;
    image_probe_count: number;
    image_probe_pass_count: number;
    cheap_candidate_count: number;
    probed_cheap_candidate_count: number;
    image_candidate_count: number;
    probed_image_candidate_count: number;
    recommended_change_count: number;
    forbidden_payload_field_count: number;
    blocking_check_count: number;
    warning_check_count: number;
  };
  model_rows: Array<{
    model: string;
    canonical_model?: string | null;
    is_known_model: boolean;
    is_gemini_like: boolean;
    provider: string;
    cost_tier?: string | null;
    model_status: string;
    capabilities: string[];
    chat_probe_status: string;
    image_probe_status: string;
    http_status?: number | null;
    json_ok?: boolean | null;
    latency_ms?: number | null;
    image_http_status?: number | null;
    image_count?: number | null;
    image_latency_ms?: number | null;
    output_usd_per_image?: number | null;
    recommended_for_defaults: boolean;
    reason: string;
  }>;
  recommended_env: Array<{
    env_var: string;
    task: string;
    current_value: string;
    recommended_value: string;
    requires_change: boolean;
    reason: string;
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

export type ModelCheapFirstCalibration = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
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
  calibration_tasks: Array<{
    id: string;
    task: string;
    product_area: string;
    fixture_ids: string[];
    expected_decision: string;
    max_cost_tier: string;
    quality_floor: number;
    release_gate_links: string[];
    user_need_ids: string[];
  }>;
  calibration_rows: Array<{
    id: string;
    task: string;
    product_area: string;
    status: string;
    selected_model?: string | null;
    canonical_model?: string | null;
    decision?: string | null;
    cost_tier: string;
    fixture_ids: string[];
    fixture_score: number;
    quality_floor: number;
    estimated_savings_ratio?: number | null;
    research_source_ids: string[];
    calibration_decision: string;
    reason_codes: string[];
    checks: Array<{
      id: string;
      status: string;
      expected: string;
      actual: string | number | null;
      reason: string;
    }>;
    release_gate_links: string[];
    next_action: string;
  }>;
  external_research_mappings: Array<{
    source_id: string;
    title: string;
    url: string;
    task_signal: string;
    calibration_task_ids: string[];
    local_fixture_ids: string[];
    policy_impact: string;
    import_policy: string;
  }>;
  source_summaries: Record<string, Record<string, unknown>>;
  recommended_actions: string[];
  release_guardrails: string[];
  privacy_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelPriceRefreshMonitorCheck = {
  id: string;
  status: string;
  summary: Record<string, number | string | boolean | null>;
  rows: Array<Record<string, unknown>>;
  recommended_action: string;
};

export type ModelPriceRefreshMonitorSignal = {
  id: string;
  severity: string;
  signal_type: string;
  model?: string | null;
  reason: string;
  requires_price_refresh: boolean;
  recommended_action: string;
};

export type ModelPriceRefreshMonitor = {
  status: string;
  summary: {
    check_count: number;
    blocking_count: number;
    warning_count: number;
    drift_signal_count: number;
    refresh_needed_count: number;
    missing_price_metadata_count: number;
    high_frequency_tasks: string[];
    media_tasks: string[];
    forecast_profile_count: number;
    observed_model_count: number;
  };
  checks: ModelPriceRefreshMonitorCheck[];
  drift_signals: ModelPriceRefreshMonitorSignal[];
  recommended_actions: string[];
  privacy_note: string[];
  validation_commands: string[];
};

export type ModelCatalogSourceAudit = {
  status: string;
  method: {
    type: string;
    notes: string[];
    source_urls: string[];
  };
  summary: {
    catalog_model_count: number;
    source_reference_count: number;
    source_url_present_count: number;
    official_source_url_count: number;
    priced_model_count: number;
    missing_pricing_count: number;
    stable_model_count: number;
    preview_model_count: number;
    high_frequency_default_count: number;
    high_frequency_aligned_count: number;
    blocking_check_count: number;
    warning_check_count: number;
    raw_payload_echoed: boolean;
  };
  source_references: Array<{
    id: string;
    title: string;
    url: string;
    review_purpose: string;
  }>;
  high_frequency_defaults: Array<{
    task: string;
    default_model: string;
    canonical_model?: string | null;
  }>;
  catalog_rows: Array<{
    model_id: string;
    catalog_status: string;
    cost_tier: string;
    latency_tier: string;
    capability_count: number;
    best_for_count: number;
    configured_roles: string[];
    source_url: string;
    source_url_present: boolean;
    official_source_url: boolean;
    pricing_status: string;
    high_frequency_default_allowed: boolean;
    default_requires_review: boolean;
    review_note: string;
  }>;
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: {
    raw_payload_echoed: boolean;
    credentials_included: boolean;
    prompts_included: boolean;
    raw_legal_text_included: boolean;
    raw_model_output_included: boolean;
    network_called: boolean;
    output_scope: string;
  };
  validation_commands: string[];
};

export type ModelCatalogCandidatePatchRow = {
  id: string;
  row_type: string;
  observed_model: string;
  model_id?: string;
  proposed_catalog_id?: string | null;
  canonical_model?: string | null;
  known_catalog_model?: boolean;
  catalog_action?: string;
  patch_action: string;
  catalog_status?: string;
  cost_tier?: string;
  latency_tier?: string;
  source_url?: string;
  pricing_status?: string;
  default_allowed_for_high_frequency?: boolean;
  cheap_first_default_allowed?: boolean;
  requires_operator_review?: boolean;
  manual_review_required?: boolean;
  cheap_first_candidate_status?: string;
  default_promotion_state?: string;
  release_action?: string;
  reason?: string;
  recommended_action?: string;
  required_metadata_checks?: string[];
  proposed_profile_stub?: Record<string, unknown>;
  candidate_patch_written?: boolean;
  gateway_call_allowed?: boolean;
};

export type ModelCatalogCandidatePatchPlan = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
    source_urls?: string[];
  };
  summary: {
    observed_model_count: number;
    candidate_patch_count: number;
    add_count: number;
    update_count: number;
    review_required_count: number;
    blocked_count: number;
    pricing_watch_count: number;
    existing_catalog_review_count: number;
    external_ignore_count: number;
    cheap_first_candidate_count: number;
    premium_or_preview_candidate_count: number;
    rejected_sensitive_count: number;
    rejected_invalid_count?: number;
    rejected_model_count?: number;
    forbidden_payload_field_count: number;
    candidate_patch_written: boolean;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
  };
  candidate_patch_rows: ModelCatalogCandidatePatchRow[];
  candidate_patches?: ModelCatalogCandidatePatchRow[];
  existing_catalog_diffs: ModelCatalogCandidatePatchRow[];
  external_model_ignores: ModelCatalogCandidatePatchRow[];
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  manual_source_review: {
    required: boolean;
    source_urls: string[];
    required_checks: string[];
  };
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelCatalogCandidateImpactTaskRow = {
  id: string;
  task: string;
  baseline_model: string;
  replay_model: string;
  selected_model_changed: boolean;
  cheap_first_would_promote: boolean;
  high_frequency: boolean;
  route_mode: string;
  baseline_cost_tier?: string;
  replay_cost_tier?: string;
  replay_pricing_status?: string;
  replay_catalog_status?: string;
  eligible_candidate_count: number;
  candidate_count: number;
  reason: string;
};

export type ModelCatalogCandidateImpactRow = {
  id: string;
  observed_model: string;
  model_id: string;
  candidate_status: string;
  virtual_profile_accepted: boolean;
  default_candidate_allowed: boolean;
  cost_tier: string;
  latency_tier: string;
  catalog_status: string;
  pricing_status: string;
  capabilities: string[];
  reason_codes: string[];
  recommended_action: string;
};

export type ModelCatalogCandidateImpactReplay = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    candidate_profile_count: number;
    accepted_virtual_profile_count: number;
    review_required_candidate_count: number;
    blocked_candidate_count: number;
    task_impact_count: number;
    recommended_change_count: number;
    cheap_first_would_promote_count: number;
    high_frequency_change_count: number;
    forbidden_payload_field_count: number;
    patch_plan_status: string;
    virtual_catalog_model_count: number;
    baseline_catalog_model_count: number;
    configuration_written: boolean;
    catalog_file_written: boolean;
    env_file_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
    secret_value_included: boolean;
  };
  candidate_rows: ModelCatalogCandidateImpactRow[];
  task_impact_rows: ModelCatalogCandidateImpactTaskRow[];
  selector_delta: {
    changed_tasks: string[];
    cheap_first_promoted_tasks: string[];
    high_frequency_changed_tasks: string[];
  };
  capability_matrix_coverage?: {
    task_count: number;
    catalog_model_count: number;
    recommended_models: string[];
    premium_exception_tasks: string[];
  };
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsGeminiCheapFirstCoverageGateSummary = {
  coverage_row_count: number;
  ready_row_count: number;
  review_row_count: number;
  blocked_row_count: number;
  cheap_first_ready_count: number;
  premium_exception_count: number;
  unknown_model_count: number;
  non_gemini_default_count: number;
  missing_price_count: number;
  missing_reasoning_policy_count: number;
  gateway_review_count?: number;
  lifecycle_review_count?: number;
  model_called: boolean;
  gateway_called: boolean;
  network_called: boolean;
  configuration_written?: boolean;
  credentials_included: boolean;
};

export type ModelOpsGeminiCheapFirstCoverageRow = {
  id?: string;
  task: string;
  role?: string;
  runtime_default_model: string;
  runtime_canonical_model?: string | null;
  recommended_model: string;
  recommended_canonical_model?: string | null;
  coverage_status: string;
  release_action: string;
  cheap_first_aligned: boolean;
  premium_exception: boolean;
  model_family: string;
  cost_tier: string;
  max_cost_tier?: string;
  lifecycle_status: string;
  price_status: string;
  reasoning_policy_status: string;
  reasoning_effort?: string | null;
  reasoning_cost_mode?: string;
  gateway_compatibility_status: string;
  reason_codes: string[];
  linked_gate_ids: string[];
  privacy_boundary?: Record<string, unknown>;
};

export type ModelOpsGeminiCheapFirstCoverageGate = {
  id: 'modelops-gemini-cheap-first-coverage-gate' | string;
  status: string;
  title: string;
  summary: ModelOpsGeminiCheapFirstCoverageGateSummary;
  coverage_rows: ModelOpsGeminiCheapFirstCoverageRow[];
  research_basis?: Array<Record<string, unknown>>;
  linked_signal_summary?: Record<string, unknown>;
  privacy_boundary: Record<string, unknown>;
  claim_boundary: Record<string, unknown>;
  recommended_actions: string[];
  validation_commands: string[];
};

export type ModelLifecycleConfiguredRole = {
  role: string;
  model: string;
  task: string;
  max_cost_tier: string;
  canonical_model?: string | null;
  lifecycle_state: string;
  cost_tier?: string | null;
  model_status: string;
  default_allowed: boolean;
  cheap_first_aligned: boolean;
  reason: string;
};

export type ModelLifecyclePolicy = {
  status: string;
  method: {
    type: string;
    notes: string[];
    source_urls: string[];
  };
  summary: {
    catalog_model_count: number;
    stable_catalog_count: number;
    preview_catalog_count: number;
    configured_role_count: number;
    default_allowed_count: number;
    preview_default_count: number;
    deprecated_default_count: number;
    latest_alias_default_count: number;
    unknown_default_count: number;
    cheap_first_aligned_count: number;
  };
  configured_roles: ModelLifecycleConfiguredRole[];
  catalog_lifecycle: Array<{
    model: string;
    status: string;
    cost_tier: string;
    default_policy: string;
    preferred_default_role: string;
    pricing_source_url: string;
  }>;
  alias_policy: {
    canonical_prefixes: string[];
    pass_through: string;
    latest_alias_default_policy: string;
    deprecated_generations: string[];
    stable_default_examples: string[];
  };
  blocking_check_ids: string[];
  warning_check_ids: string[];
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  recommended_actions: string[];
  privacy_note: string;
};

export type ModelOpsReadinessCheck = {
  id: string;
  label: string;
  category: string;
  source_key: string;
  required: boolean;
  status: string;
  reason: string;
  blocking_ids: string[];
  warning_ids: string[];
};

export type ModelOpsReadinessWarningDrilldown = {
  id: string;
  label: string;
  status: string;
  required: boolean;
  source_key: string;
  component_category: string;
  warning_category: string;
  severity: string;
  priority: number;
  reason: string;
  blocking_ids: string[];
  warning_ids: string[];
  next_action: string;
  validation_hint: string;
  privacy_boundary: {
    metadata_only: boolean;
    model_called: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payloads_included: boolean;
    raw_model_output_included: boolean;
    credentials_included: boolean;
  };
};

export type ModelOpsReadiness = {
  status: string;
  release_recommendation: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    component_count: number;
    required_component_count: number;
    optional_component_count: number;
    pass_count: number;
    warn_count: number;
    fail_count: number;
    required_warning_count: number;
    optional_review_count: number;
    required_failure_count: number;
    optional_failure_count: number;
    blocking_count: number;
    warning_count: number;
    warning_drilldown_count: number;
    p0_warning_count: number;
    p1_warning_count: number;
    p2_warning_count: number;
  };
  checks: ModelOpsReadinessCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  warning_category_counts: Record<string, number>;
  warning_drilldown: ModelOpsReadinessWarningDrilldown[];
  recommended_actions: string[];
};

export type ModelOpsCheapFirstReleaseDecision = {
  status: string;
  release_decision: {
    status: string;
    label: string;
    current_default_action: string;
    default_change_policy: string;
  };
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    required_signal_count: number;
    attached_signal_count: number;
    passing_signal_count: number;
    warning_signal_count: number;
    blocking_signal_count: number;
    source_warning_id_count: number;
    source_blocking_id_count: number;
    current_cheap_first_default_allowed: boolean;
    default_change_allowed: boolean;
    default_promotion_blocked: boolean;
    maintainer_review_required: boolean;
    newapi_called: boolean;
    raw_payload_echoed: boolean;
  };
  checks: Array<{
    id: string;
    source_key: string;
    status: string;
    source_status: string;
    decision_effect: string;
    source_blocking_ids: string[];
    source_warning_ids: string[];
    source_summary: Record<string, number>;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  source_blocking_ids: string[];
  source_warning_ids: string[];
  promotion_policy: Record<string, string>;
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsDefaultChangeQueue = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    queue_item_count: number;
    change_request_count: number;
    ready_change_count: number;
    review_required_count: number;
    blocked_change_count: number;
    no_action_count: number;
    release_decision_status: string;
    gateway_probe_status: string;
    price_refresh_status: string;
    catalog_source_audit_status: string;
    configuration_written: boolean;
    gateway_called: boolean;
  };
  queue_items: Array<{
    id: string;
    task: string;
    env_var?: string | null;
    current_model: string;
    recommended_model: string;
    requires_change: boolean;
    requires_operator_review: boolean;
    queue_status: string;
    default_optimization_status: string;
    current_cost_tier?: string | null;
    recommended_cost_tier?: string | null;
    estimated_monthly_savings_usd?: number | null;
    reason_codes: string[];
    action: string;
  }>;
  blocking_item_ids: string[];
  review_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstPriorityQueue = {
  id: 'model-ops-cheap-first-priority-queue' | string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    priority_item_count: number;
    p0_count: number;
    p1_count: number;
    p2_count: number;
    p3_count: number;
    blocked_count: number;
    review_required_count: number;
    ready_count: number;
    monitor_only_count: number;
    change_request_count: number;
    estimated_monthly_savings_usd: number;
    release_gate_status: string;
    default_change_queue_status: string;
    coverage_gate_status: string;
    route_quality_status: string;
    price_refresh_status: string;
    catalog_source_audit_status: string;
    configuration_written: boolean;
    model_called: boolean;
    gateway_called: boolean;
    network_called: boolean;
    credentials_included: boolean;
  };
  priority_items: Array<{
    id: string;
    task: string;
    priority_rank: number;
    priority_score: number;
    priority_label: string;
    risk_level: string;
    work_status: string;
    release_gate_status: string;
    default_change_queue_status: string;
    coverage_status: string;
    default_optimization_status: string;
    quality_review_action: string;
    env_var?: string | null;
    current_model: string;
    recommended_model: string;
    cheap_start_model: string;
    current_cost_tier?: string | null;
    recommended_cost_tier?: string | null;
    requires_change: boolean;
    requires_operator_review: boolean;
    runtime_default_has_required_capabilities: boolean;
    runtime_default_over_budget: boolean;
    quality_score: number;
    quality_floor: number;
    estimated_monthly_savings_usd?: number | null;
    reason_codes: string[];
    next_action: string;
    validation_commands: string[];
    privacy_boundary: Record<string, boolean | string>;
  }>;
  blocking_item_ids: string[];
  review_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsGeminiDefaultChangeReviewRow = {
  id: string;
  task: string;
  env_var: string;
  current_model: string;
  current_canonical_model?: string | null;
  proposed_model: string;
  proposed_canonical_model?: string | null;
  recommended_model: string;
  review_status: string;
  release_action: string;
  current_cost_tier: string;
  proposed_cost_tier: string;
  max_cost_tier: string;
  proposed_model_known: boolean;
  proposed_model_status: string;
  proposed_model_family: string;
  required_capabilities: string[];
  missing_required_capabilities: string[];
  cheap_first_regression: boolean;
  premium_exception: boolean;
  reason_codes: string[];
  review_note: string;
};

export type ModelOpsGeminiDefaultChangeReview = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    proposal_count: number;
    ready_count: number;
    review_required_count: number;
    blocked_count: number;
    known_model_count: number;
    unknown_model_count: number;
    cheap_first_regression_count: number;
    premium_exception_count: number;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
  };
  proposal_rows: ModelOpsGeminiDefaultChangeReviewRow[];
  blocking_proposal_ids: string[];
  review_proposal_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsGeminiDefaultCostImpactRow = {
  id: string;
  task: string;
  env_var: string;
  current_model: string;
  proposed_model: string;
  profile: {
    task: string;
    display_name: string;
    monthly_units: number;
    prompt_tokens_per_unit: number;
    completion_tokens_per_unit: number;
    max_cost_tier: string;
    rationale: string;
  };
  current_cost_tier: string;
  proposed_cost_tier: string;
  current_unit_cost_usd?: number | null;
  proposed_unit_cost_usd?: number | null;
  current_monthly_cost_usd?: number | null;
  proposed_monthly_cost_usd?: number | null;
  monthly_delta_usd?: number | null;
  estimated_savings_delta_usd?: number | null;
  cost_regression: boolean;
  premium_exception: boolean;
  impact_status: string;
  release_action: string;
  reason_codes: string[];
};

export type ModelOpsGeminiDefaultCostImpact = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    proposal_count: number;
    priced_proposal_count: number;
    ready_count: number;
    review_required_count: number;
    blocked_count: number;
    cost_increase_count: number;
    cost_decrease_count: number;
    unknown_price_count: number;
    premium_exception_count: number;
    estimated_monthly_delta_usd: number;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
  };
  impact_rows: ModelOpsGeminiDefaultCostImpactRow[];
  blocking_impact_ids: string[];
  review_impact_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstCanaryPlan = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    queue_item_count: number;
    canary_step_count: number;
    canary_required_count: number;
    ready_step_count: number;
    review_required_step_count: number;
    blocked_step_count: number;
    monitor_only_step_count: number;
    rollback_trigger_count: number;
    route_guardrail_status: string;
    cost_guardrail_status: string;
    route_telemetry_ops_status: string;
    release_decision_status: string;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
  };
  rollout_policy: {
    batch_percentages: number[];
    minimum_observation_window_hours: number;
    holdout_required_until_final_review: boolean;
    operator_approval_required: boolean;
    validation_source: string;
  };
  success_thresholds: Record<string, number>;
  rollback_triggers: Array<{
    id: string;
    metric: string;
    threshold: number;
    action: string;
  }>;
  canary_steps: Array<{
    id: string;
    source_queue_item_id: string;
    task: string;
    env_var?: string | null;
    current_model: string;
    recommended_model: string;
    phase: string;
    step_status: string;
    batch_percentage: number;
    holdout_percentage: number;
    observation_window_hours: number;
    requires_configuration_change: boolean;
    requires_operator_review: boolean;
    reason_codes: string[];
    success_thresholds: Record<string, number>;
    rollback_trigger_ids: string[];
    action: string;
  }>;
  blocking_step_ids: string[];
  review_step_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstCanaryObservation = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    observation_count: number;
    matched_step_count: number;
    unmatched_step_count: number;
    passing_observation_count: number;
    warning_observation_count: number;
    failing_observation_count: number;
    rollback_trigger_breach_count: number;
    total_request_count: number;
    forbidden_payload_field_count: number;
    secret_like_value_count: number;
    source_plan_status: string;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    raw_payload_echoed: boolean;
  };
  thresholds: Record<string, number>;
  observation_rows: Array<{
    id: string;
    step_id: string;
    task: string;
    phase: string;
    status: string;
    source_step_found: boolean;
    request_count: number;
    failure_count: number;
    over_budget_count: number;
    premium_request_count: number;
    operator_review_count: number;
    failure_rate: number;
    over_budget_route_ratio: number;
    premium_request_ratio: number;
    operator_review_route_ratio: number;
    checks: Array<{
      id: string;
      status: string;
      value: number;
      threshold: number;
      reason: string;
    }>;
    reason_codes: string[];
    action: string;
  }>;
  blocking_observation_ids: string[];
  warning_observation_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
  promotion_decision?: ModelOpsCheapFirstCanaryPromotionDecision;
  approval_packet?: ModelOpsCheapFirstCanaryApprovalPacket;
  rollback_drill?: ModelOpsCheapFirstCanaryRollbackDrill;
  change_manifest?: ModelOpsCheapFirstCanaryChangeManifest;
};

export type ModelOpsCheapFirstCanaryPromotionDecision = {
  status: string;
  decision: {
    status: string;
    label: string;
    default_action: string;
    configuration_change_allowed: boolean;
    traffic_shift_allowed: boolean;
    requires_maintainer_approval: boolean;
  };
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    decision_item_count: number;
    advance_decision_count: number;
    hold_decision_count: number;
    rollback_decision_count: number;
    monitor_only_count: number;
    not_ready_count: number;
    source_plan_status: string;
    source_observation_status: string;
    observation_count: number;
    failing_observation_count: number;
    warning_observation_count: number;
    rollback_trigger_breach_count: number;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
  };
  promotion_items: Array<{
    id: string;
    source_step_id: string;
    task: string;
    phase: string;
    step_status: string;
    promotion_status: string;
    observation_statuses: string[];
    matched_observation_count: number;
    batch_percentage: number;
    holdout_percentage: number;
    reason_codes: string[];
    configuration_change_allowed: boolean;
    traffic_shift_allowed: boolean;
    action: string;
  }>;
  advance_item_ids: string[];
  hold_item_ids: string[];
  rollback_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstCanaryApprovalPacket = {
  status: string;
  approval_policy: {
    approval_required: boolean;
    approval_record_written: boolean;
    configuration_change_allowed: boolean;
    traffic_shift_allowed: boolean;
    requires_current_observation_review: boolean;
    requires_rollback_review_for_failed_steps: boolean;
  };
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    approval_item_count: number;
    ready_for_approval_count: number;
    blocked_approval_count: number;
    rollback_review_count: number;
    monitor_only_count: number;
    source_not_ready_count: number;
    required_signoff_count: number;
    approved_count: number;
    source_promotion_status: string;
    approval_record_written: boolean;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
  };
  approval_items: Array<{
    id: string;
    source_promotion_item_id: string;
    source_step_id: string;
    task: string;
    phase: string;
    promotion_status: string;
    approval_status: string;
    matched_observation_count: number;
    batch_percentage: number;
    holdout_percentage: number;
    required_signoffs: string[];
    pre_approval_checks: string[];
    blocking_reason_codes: string[];
    approval_record_written: boolean;
    configuration_change_allowed: boolean;
    traffic_shift_allowed: boolean;
    action: string;
  }>;
  ready_item_ids: string[];
  blocked_item_ids: string[];
  rollback_review_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstCanaryRollbackDrill = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    drill_item_count: number;
    ready_drill_count: number;
    blocked_drill_count: number;
    rollback_required_count: number;
    monitor_only_count: number;
    source_approval_status: string;
    source_promotion_status: string;
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    rollback_executed: boolean;
    drill_record_written: boolean;
  };
  rollback_drill_policy: {
    drill_required_before_approval: boolean;
    rollback_execution_allowed: boolean;
    configuration_change_allowed: boolean;
    traffic_shift_allowed: boolean;
    requires_trigger_review: boolean;
    requires_holdout_confirmation: boolean;
  };
  rollback_drill_items: Array<{
    id: string;
    source_approval_item_id: string;
    source_step_id: string;
    task: string;
    phase: string;
    approval_status: string;
    promotion_status: string;
    drill_status: string;
    trigger_review_status: string;
    rollback_trigger_ids: string[];
    reason_codes: string[];
    required_roles: string[];
    rehearsal_steps: string[];
    configuration_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    rollback_executed: boolean;
    drill_record_written: boolean;
    action: string;
  }>;
  ready_drill_item_ids: string[];
  blocked_drill_item_ids: string[];
  rollback_required_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstCanaryChangeManifest = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    manifest_item_count: number;
    ready_change_count: number;
    blocked_change_count: number;
    rollback_review_count: number;
    monitor_only_count: number;
    source_rollback_drill_status: string;
    source_approval_status: string;
    configuration_written: boolean;
    env_file_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    change_applied: boolean;
    manifest_record_written: boolean;
    secret_value_included: boolean;
  };
  change_manifest_policy: {
    external_execution_required: boolean;
    configuration_write_allowed: boolean;
    env_file_write_allowed: boolean;
    traffic_shift_allowed: boolean;
    requires_maintainer_approval: boolean;
    requires_rollback_drill_ready: boolean;
    includes_secret_values: boolean;
  };
  change_manifest_items: Array<{
    id: string;
    source_rollback_drill_item_id: string;
    source_approval_item_id: string;
    source_step_id: string;
    task: string;
    phase: string;
    approval_status: string;
    drill_status: string;
    manifest_status: string;
    env_var?: string | null;
    current_model: string;
    recommended_model: string;
    batch_percentage: number;
    holdout_percentage: number;
    external_change_set: {
      env_var?: string | null;
      from_model: string;
      to_model: string;
      batch_percentage: number;
      holdout_percentage: number;
      apply_mode: string;
      secret_value_included: boolean;
    };
    prerequisites: string[];
    operator_steps: string[];
    configuration_written: boolean;
    env_file_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    change_applied: boolean;
    manifest_record_written: boolean;
    action: string;
  }>;
  ready_change_item_ids: string[];
  blocked_change_item_ids: string[];
  rollback_review_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsCheapFirstMaintainerExecutionChecklist = {
  id: 'model-ops-cheap-first-maintainer-execution-checklist' | string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    execution_item_count: number;
    ready_for_external_change_count: number;
    review_required_count: number;
    blocked_count: number;
    rollback_review_count: number;
    monitor_only_count: number;
    priority_queue_status: string;
    release_decision_status: string;
    canary_plan_status: string;
    promotion_decision_status: string;
    approval_packet_status: string;
    rollback_drill_status: string;
    change_manifest_status: string;
    configuration_written: boolean;
    env_file_written: boolean;
    approval_record_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    traffic_shifted: boolean;
    raw_payload_echoed: boolean;
    secret_value_included: boolean;
  };
  execution_policy: {
    external_execution_required: boolean;
    configuration_write_allowed: boolean;
    env_file_write_allowed: boolean;
    approval_record_write_allowed: boolean;
    traffic_shift_allowed: boolean;
    gateway_call_allowed: boolean;
    requires_release_pass: boolean;
    requires_canary_evidence: boolean;
    requires_maintainer_approval: boolean;
    requires_rollback_drill_ready: boolean;
    requires_metadata_only_boundary: boolean;
  };
  execution_items: Array<{
    id: string;
    task: string;
    execution_rank: number;
    execution_status: string;
    priority_rank: number;
    priority_score: number;
    priority_label: string;
    priority_work_status: string;
    release_decision_status: string;
    canary_step_status: string;
    promotion_decision_status: string;
    approval_status: string;
    rollback_drill_status: string;
    manifest_status: string;
    env_var?: string | null;
    current_model: string;
    recommended_model: string;
    requires_change: boolean;
    external_change_allowed: boolean;
    configuration_written: boolean;
    env_file_written: boolean;
    approval_record_written: boolean;
    gateway_called: boolean;
    traffic_shifted: boolean;
    missing_evidence: string[];
    required_evidence: string[];
    reason_codes: string[];
    operator_action: string;
    validation_commands: string[];
  }>;
  ready_execution_item_ids: string[];
  blocked_execution_item_ids: string[];
  review_execution_item_ids: string[];
  rollback_review_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  claim_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelOpsPerformanceBudget = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    first_load_budget_ms: number;
    cache_hit_budget_ms: number;
    frontend_request_timeout_ms: number;
    frontend_total_timeout_ms: number;
    backend_cache_ttl_seconds: number;
    models_payload_cache_enabled: boolean;
    same_origin_fetch_first: boolean;
    fallback_after_timeout_disabled: boolean;
    duplicate_calibration_fetch_removed: boolean;
    frontend_abort_controller_required: boolean;
    slow_observation_failure_threshold: number;
    raw_payload_echoed: boolean;
    observation_count: number;
    slow_observation_count: number;
    blocking_check_count: number;
    warning_check_count: number;
  };
  observations: Array<{
    metric: string;
    duration_ms: number;
    budget_ms?: number | null;
    within_budget: boolean;
  }>;
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: {
    raw_payload_echoed: boolean;
    credentials_included: boolean;
    prompts_included: boolean;
    raw_legal_text_included: boolean;
    raw_model_output_included: boolean;
    urls_included: boolean;
    output_scope: string;
  };
  validation_commands: string[];
};

export type ModelRouteQualityBudget = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    task_count: number;
    cheap_start_task_count: number;
    premium_exception_task_count: number;
    runtime_default_gap_count: number;
    quality_gate_count: number;
    blocking_check_count: number;
    warning_check_count: number;
    raw_payload_echoed: boolean;
  };
  task_quality_budgets: Array<{
    task: string;
    display_name: string;
    recommended_model: string;
    runtime_default_model: string;
    cheap_start_model: string;
    recommended_model_cost_tier: string;
    runtime_default_cost_tier: string;
    max_cost_tier: string;
    candidate_count: number;
    quality_score: number;
    quality_floor: number;
    quality_gate_ids: string[];
    quality_gate_count: number;
    runtime_default_has_required_capabilities: boolean;
    runtime_default_over_budget: boolean;
    premium_exception_allowed: boolean;
    review_action: string;
  }>;
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: {
    raw_payload_echoed: boolean;
    credentials_included: boolean;
    prompts_included: boolean;
    raw_legal_text_included: boolean;
    raw_model_output_included: boolean;
    emails_included: boolean;
    output_scope: string;
  };
  validation_commands: string[];
};

export type ModelOpsCheapFirstEscalationBudgetCheck = {
  id: string;
  status: string;
  reason: string;
  value?: number;
  threshold?: number;
  warn_threshold?: number;
  fail_threshold?: number;
};

export type ModelOpsCheapFirstEscalationBudgetRow = {
  id: string;
  task: string;
  phase: string;
  status: string;
  request_count: number;
  primary_failure_count: number;
  verification_count: number;
  escalation_count: number;
  successful_after_escalation_count: number;
  premium_escalation_count: number;
  operator_review_count: number;
  primary_failure_rate: number;
  escalation_rate: number;
  premium_escalation_rate: number;
  escalation_success_rate: number;
  primary_cost_usd: number;
  verification_cost_usd: number;
  escalation_cost_usd: number;
  premium_cost_usd: number;
  cascade_cost_usd: number;
  wasted_escalation_cost_usd: number;
  wasted_escalation_cost_ratio: number;
  premium_review_coverage: boolean;
  checks: ModelOpsCheapFirstEscalationBudgetCheck[];
  reason_codes: string[];
  recommended_action: string;
};

export type ModelOpsCheapFirstEscalationBudget = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
    research_basis?: Array<{
      id: string;
      url: string;
      signal: string;
    }>;
  };
  thresholds: Record<string, number>;
  summary: {
    observation_count: number;
    default_observation_used: boolean;
    passing_observation_count: number;
    warning_observation_count: number;
    failing_observation_count: number;
    total_request_count: number;
    primary_failure_count: number;
    verification_count: number;
    escalation_count: number;
    successful_after_escalation_count: number;
    premium_escalation_count: number;
    operator_review_count: number;
    cascade_cost_usd: number;
    primary_cost_usd: number;
    verification_cost_usd: number;
    escalation_cost_usd: number;
    premium_cost_usd: number;
    wasted_escalation_cost_usd: number;
    wasted_escalation_cost_ratio: number;
    escalation_success_rate: number;
    blocking_check_count: number;
    warning_check_count: number;
    forbidden_payload_field_count: number;
    secret_like_value_count: number;
    model_called: boolean;
    gateway_called: boolean;
    network_called: boolean;
    configuration_written: boolean;
    raw_payload_echoed: boolean;
  };
  budget_rows: ModelOpsCheapFirstEscalationBudgetRow[];
  checks: ModelOpsCheapFirstEscalationBudgetCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  blocking_observation_ids: string[];
  warning_observation_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type ModelFailureUpgradeBudgetCheck = {
  id: string;
  status: string;
  reason: string;
  value?: number | null;
  warn_threshold?: number;
  fail_threshold?: number;
};

export type ModelFailureUpgradeBudgetPayloadShape = {
  required: string[];
  optional: string[];
  forbidden: string[];
  example: Record<string, unknown>;
};

export type ModelFailureUpgradeBudgetDecision = {
  decision: string;
  task: string;
  current_model: string;
  current_cost_tier: string;
  next_model: string;
  next_cost_tier: string;
  next_step?: Record<string, unknown> | null;
  policy_decision?: string | null;
  failure_signals: string[];
  requires_operator_review: boolean;
  quota_decision?: {
    status: string;
    allowed: boolean;
    effective_plan_type: string;
    remaining_before: { premium_escalations: number };
    remaining_after: { premium_escalations: number };
    over_limit_codes: string[];
  } | null;
  cost_delta: {
    current_cost_usd?: number | null;
    next_cost_usd?: number | null;
    incremental_cost_usd?: number | null;
  };
};

export type ModelFailureUpgradeBudget = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
    research_basis?: Array<{
      id: string;
      url: string;
      signal: string;
    }>;
  };
  payload_shape: ModelFailureUpgradeBudgetPayloadShape;
  summary: {
    default_payload_used: boolean;
    task: string;
    attempt_index: number;
    max_attempts: number;
    attempt_budget_remaining: number;
    failure_signal_count: number;
    operator_approved: boolean;
    current_model_known: boolean;
    next_model_known: boolean;
    current_cost_usd?: number | null;
    next_cost_usd?: number | null;
    incremental_cost_usd?: number | null;
    next_cost_tier?: string | null;
    premium_quota_allowed?: boolean | null;
    forbidden_payload_field_count: number;
    secret_like_value_count: number;
    model_called: boolean;
    gateway_called: boolean;
    network_called: boolean;
    configuration_written: boolean;
  };
  decision: ModelFailureUpgradeBudgetDecision;
  checks: ModelFailureUpgradeBudgetCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type ModelOpsLegalBenchmarkRiskBridgeRouteReview = {
  id: string;
  task_id: string;
  task: string;
  product_area: string;
  risk_level: string;
  priority: number;
  calibration_status: string;
  calibration_decision: string;
  cheap_first_allowed: boolean;
  balanced_precheck_required: boolean;
  premium_exception_required: boolean;
  cost_tier: string;
  research_source_ids: string[];
  user_need_ids: string[];
  coverage_statuses: string[];
  public_benchmark_statuses: string[];
  release_gate_links: string[];
  reason_codes: string[];
  next_action: string;
};

export type ModelOpsLegalBenchmarkRiskBridgeUserNeedReview = {
  need_id: string;
  title: string;
  priority_band: string;
  priority_score: number;
  coverage_status: string;
  public_benchmark_status: string;
  calibration_status: string;
  highest_risk_level: string;
  queue_row_ids: string[];
  task_ids: string[];
  research_source_ids: string[];
  cheap_first_allowed_count: number;
  premium_exception_count: number;
  next_action: string;
};

export type ModelOpsLegalBenchmarkRiskBridge = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    route_review_count: number;
    user_need_review_count: number;
    blocking_route_count: number;
    watch_route_count: number;
    premium_exception_route_count: number;
    benchmark_license_watch_count: number;
    cheap_first_allowed_route_count: number;
    balanced_precheck_route_count: number;
    default_change_queue_item_count: number;
    source_risk_queue_status: string;
    source_release_decision_status: string;
    newapi_called: boolean;
    network_called: boolean;
    dataset_downloaded: boolean;
    configuration_written: boolean;
    traffic_shifted: boolean;
    raw_payload_echoed: boolean;
  };
  route_reviews: ModelOpsLegalBenchmarkRiskBridgeRouteReview[];
  user_need_reviews: ModelOpsLegalBenchmarkRiskBridgeUserNeedReview[];
  bridge_policy: Record<string, boolean | string | number | null>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type ModelReasoningDecision = {
  task: string;
  model: string;
  requested_effort?: string | null;
  effective_effort?: string | null;
  gateway_parameter?: string | null;
  source: string;
  adjusted: boolean;
  supported_efforts: string[];
  cost_mode: string;
  reason: string;
};

export type ModelReasoningPolicy = {
  status: string;
  request_field: {
    name: string;
    values: string[];
    default: string;
  };
  policy_notes: string[];
  task_defaults: ModelReasoningDecision[];
};

export type ModelRequestPolicyDecision = {
  task: string;
  requested_temperature?: number | null;
  effective_temperature: number;
  requested_max_tokens?: number | null;
  effective_max_tokens: number;
  temperature_adjusted: boolean;
  max_tokens_adjusted: boolean;
  response_format_mode: string;
  cost_mode: string;
  reason: string;
};

export type ModelRequestPolicyTask = {
  task: string;
  default_temperature: number;
  max_temperature: number;
  default_max_tokens: number;
  max_max_tokens: number;
  rationale: string;
};

export type ModelRequestPolicy = {
  status: string;
  request_fields: Record<string, string>;
  policy_notes: string[];
  task_defaults: ModelRequestPolicyDecision[];
  task_policies: ModelRequestPolicyTask[];
};

export type ModelGatewayRequestCompatibilityRow = {
  id: string;
  task: string;
  model: string;
  canonical_model?: string | null;
  known_catalog_model: boolean;
  gemini_like: boolean;
  gateway_prefixed_model: boolean;
  cost_tier: string;
  max_default_cost_tier: string;
  cheap_first_task: boolean;
  compatibility_status: string;
  release_action: string;
  gateway_request_shape: {
    messages: string;
    response_format_mode: string;
    temperature: number;
    max_tokens: number;
    reasoning_effort?: string | null;
    request_body_returned: boolean;
    headers_returned: boolean;
  };
  request_policy: {
    temperature_adjusted: boolean;
    max_tokens_adjusted: boolean;
    cost_mode: string;
  };
  reasoning_policy: {
    effective_effort?: string | null;
    gateway_parameter?: string | null;
    cost_mode: string;
    adjusted: boolean;
  };
  reason_codes: string[];
  next_action: string;
};

export type ModelGatewayRequestCompatibilityGate = {
  id: string;
  title: string;
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    task_count: number;
    ready_task_count: number;
    review_task_count: number;
    blocked_task_count: number;
    cheap_first_task_count: number;
    cheap_first_ready_count: number;
    gateway_prefixed_model_count: number;
    unknown_model_count: number;
    reasoning_omitted_count: number;
    json_response_format_count: number;
    forbidden_payload_field_count: number;
    configuration_written: boolean;
    gateway_called: boolean;
    network_called: boolean;
    raw_payload_echoed: boolean;
    credentials_included: boolean;
  };
  task_rows: ModelGatewayRequestCompatibilityRow[];
  checks: Array<{ id: string; status: string; reason: string }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string | number | null>;
  claim_boundary: Record<string, boolean | string | number | null>;
  validation_commands: string[];
};

export type ModelRequestCostBound = {
  id: string;
  task: string;
  model: string;
  is_priced: boolean;
  cost_tier?: string | null;
  prompt_tokens_assumption: number;
  default_max_tokens: number;
  ceiling_max_tokens: number;
  default_request_cost_usd?: number | null;
  ceiling_request_cost_usd?: number | null;
  warn_default_cost_usd: number;
  fail_default_cost_usd: number;
  warn_ceiling_cost_usd: number;
  fail_ceiling_cost_usd: number;
  status: string;
  reason: string;
};

export type ModelRequestCostBounds = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    task_count: number;
    priced_task_count: number;
    default_cost_usd: number;
    ceiling_cost_usd: number;
    warning_count: number;
    blocking_count: number;
  };
  task_bounds: ModelRequestCostBound[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelCachePolicyRule = {
  id: string;
  task: string;
  cache_mode: string;
  ttl_seconds: number;
  expected_hit_rate: number;
  key_material: string[];
  privacy_boundary: string;
  rationale: string;
  enabled_by_default: boolean;
  status: string;
  deterministic_request_policy: boolean;
  request_temperature: number;
  forecast_monthly_cost_usd?: number | null;
  estimated_monthly_savings_usd?: number | null;
  reason: string;
};

export type ModelCachePolicy = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    rule_count: number;
    enabled_rule_count: number;
    estimated_monthly_savings_usd: number;
    warning_count: number;
    blocking_count: number;
  };
  rules: ModelCachePolicyRule[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelCallsiteAudit = {
  status: string;
  method: {
    type: string;
    scope: string;
    notes: string[];
  };
  summary: {
    callsite_count: number;
    explicit_task_count: number;
    missing_task_count: number;
    with_model_count: number;
    fail_count: number;
    warn_count: number;
  };
  callsites: Array<{
    file: string;
    line: number;
    function: string;
    has_task: boolean;
    has_model: boolean;
    status: string;
    reason: string;
  }>;
  recommended_actions: string[];
};

export type ModelRouteTelemetryBucket = {
  requests: number;
  successes: number;
  failures: number;
  auto_inferred: number;
  explicit_task: number;
  downgraded_to_recommended: number;
  over_budget_requested: number;
  operator_review_requested: number;
  allowed_over_budget: number;
  unknown_price_model: number;
  stream_requests: number;
  last_seen_at: number;
  models: Record<string, number>;
};

export type ModelRouteTelemetry = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    request_count: number;
    auto_inferred_ratio: number;
    downgrade_ratio: number;
    over_budget_request_ratio: number;
    failure_rate: number;
    operator_review_request_count: number;
    allowed_over_budget_count: number;
    unknown_price_model_count: number;
  };
  totals: ModelRouteTelemetryBucket;
  by_task: Record<string, ModelRouteTelemetryBucket>;
  by_inference_source: Record<string, ModelRouteTelemetryBucket>;
};

export type ModelRouteTelemetryRepository = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    stored_event_count: number;
    accepted_event_count: number;
    rejected_event_count: number;
    daily_bucket_count: number;
    raw_payload_storage_allowed: boolean;
    credentials_included: boolean;
    prompts_included: boolean;
    raw_legal_text_included: boolean;
    raw_model_output_included: boolean;
    storage_mode: string;
  };
  storage: {
    events_path: string;
    aggregates_path: string;
    retention: Record<string, unknown>;
  };
  accepted_events: Array<Record<string, unknown>>;
  rejected_events: Array<{
    event_index?: number | null;
    event_id?: string;
    status: string;
    reason_codes: string[];
  }>;
  daily_buckets: Array<{
    day: string;
    task: string;
    resolved_model: string;
    inference_source: string;
    routed_to_recommended_model: boolean;
    is_over_budget: boolean;
    requires_operator_review: boolean;
    success: boolean;
    request_count: number;
    success_count: number;
    failure_count: number;
    unpriced_model_count: number;
    reason_code_counts: Record<string, number>;
    estimated_cost_usd_sum: number;
  }>;
  totals: {
    request_count: number;
    success_count: number;
    failure_count: number;
    downgrade_count: number;
    over_budget_count: number;
    operator_review_count: number;
    unknown_model_count: number;
    unpriced_model_count: number;
    reason_code_counts: Record<string, number>;
    estimated_cost_usd_sum: number;
  };
  persistence_plan_status: string;
  recommended_actions: string[];
  privacy_boundary: {
    allowed_fields: string[];
    raw_payload_storage_allowed: boolean;
    duplicate_event_policy: string;
    forbidden_content: string[];
  };
  validation_commands: string[];
};

export type ModelRouteTelemetryOpsSummary = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  thresholds: Record<string, number>;
  summary: {
    stored_event_count: number;
    daily_bucket_count: number;
    request_count: number;
    success_count: number;
    failure_count: number;
    downgrade_count: number;
    over_budget_count: number;
    operator_review_count: number;
    premium_request_count: number;
    unknown_model_count: number;
    unpriced_model_count: number;
    estimated_cost_usd_sum: number;
    failure_rate: number;
    downgrade_ratio: number;
    over_budget_ratio: number;
    operator_review_ratio: number;
    premium_request_ratio: number;
    empty_repository: boolean;
    repository_status: string;
    raw_payload_storage_allowed: boolean;
    storage_mode: string;
  };
  daily_rows: Array<{
    day: string;
    request_count: number;
    success_count: number;
    failure_count: number;
    downgrade_count: number;
    over_budget_count: number;
    operator_review_count: number;
    premium_request_count: number;
    unpriced_model_count: number;
    estimated_cost_usd_sum: number;
    models: Record<string, number>;
    failure_rate: number;
    downgrade_ratio: number;
    over_budget_ratio: number;
    operator_review_ratio: number;
    premium_request_ratio: number;
  }>;
  checks: Array<{
    id: string;
    status: string;
    value: number;
    ratio?: number;
    warn_threshold?: number;
    fail_threshold?: number;
    reason: string;
  }>;
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
  release_guardrails: string[];
  privacy_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelRouteTelemetryTriageItem = {
  id: string;
  title: string;
  severity: string;
  priority: number;
  check_id: string;
  metric: string;
  value: number | string | boolean | null;
  threshold: number | string | boolean | null;
  reason: string;
  action: string;
  owner: string;
  release_gate_links: string[];
  evidence_paths: string[];
  validation_commands: string[];
};

export type ModelRouteTelemetryTriage = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    triage_item_count: number;
    blocking_item_count: number;
    warning_item_count: number;
    info_item_count: number;
    cheap_first_action_count: number;
    highest_priority: number;
    source_status: string;
    source_request_count: number;
    empty_repository: boolean;
  };
  triage_items: ModelRouteTelemetryTriageItem[];
  blocking_item_ids: string[];
  warning_item_ids: string[];
  recommended_actions: string[];
  privacy_boundary: Record<string, boolean | string>;
  release_guardrails: string[];
  validation_commands: string[];
};

export type ModelRouteTelemetryRemediationStep = {
  id: string;
  title: string;
  severity: string;
  priority: number;
  source_triage_item_id: string;
  source_check_id: string;
  task: string;
  env_var?: string | null;
  current_model?: string | null;
  recommended_model?: string | null;
  recommended_env_assignment?: string | null;
  requires_env_change: boolean;
  requires_operator_review: boolean;
  estimated_monthly_savings_usd?: number | null;
  reason: string;
  action: string;
  validation_commands: string[];
  release_gate_links: string[];
  evidence_paths: string[];
};

export type ModelRouteTelemetryRecommendedEnv = {
  env_var: string;
  task: string;
  current_value?: string | null;
  recommended_value?: string | null;
  requires_change: boolean;
  source_step_id: string;
  reason: string;
};

export type ModelRouteTelemetryRemediation = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    remediation_step_count: number;
    blocking_step_count: number;
    warning_step_count: number;
    env_change_count: number;
    manual_review_step_count: number;
    source_triage_status: string;
    source_triage_item_count: number;
    default_optimization_status: string;
    estimated_monthly_savings_usd: number;
    newapi_called: boolean;
    configuration_written: boolean;
  };
  remediation_steps: ModelRouteTelemetryRemediationStep[];
  blocking_step_ids: string[];
  warning_step_ids: string[];
  recommended_env: ModelRouteTelemetryRecommendedEnv[];
  recommended_actions: string[];
  release_guardrails: string[];
  privacy_boundary: Record<string, boolean | string>;
  validation_commands: string[];
};

export type ModelRouteGuardrailCheck = {
  id: string;
  status: string;
  value: number;
  ratio?: number;
  warn_threshold?: number;
  fail_threshold?: number;
  reason: string;
};

export type ModelRouteGuardrails = {
  status: string;
  thresholds: Record<string, number>;
  summary: {
    request_count: number;
    failure_rate: number;
    over_budget_route_ratio: number;
    downgrade_ratio: number;
    operator_review_route_ratio: number;
    unknown_price_model_count: number;
    allowed_over_budget_count: number;
  };
  checks: ModelRouteGuardrailCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelCapabilityCandidate = {
  model_id: string;
  status: string;
  cost_tier: string;
  latency_tier: string;
  context_window_tokens?: number | null;
  input_usd_per_million_tokens?: number | null;
  output_usd_per_million_tokens?: number | null;
  preferred_capability_hits: string[];
  missing_preferred_capabilities: string[];
  over_task_budget: boolean;
  fit_score: number;
};

export type ModelCapabilityTask = {
  task: string;
  requirement: {
    task: string;
    display_name: string;
    required_capabilities: string[];
    preferred_capabilities: string[];
    max_cost_tier: string;
    preferred_latency_tier: string;
    default_alias: string;
    reason: string;
  };
  recommended_model: string;
  runtime_default_model: string;
  runtime_default_is_recommended: boolean;
  candidate_count: number;
  candidates: ModelCapabilityCandidate[];
};

export type ModelCapabilityMatrix = {
  status: string;
  selection_policy: string[];
  source_notes: string[];
  tasks: ModelCapabilityTask[];
  coverage: {
    task_count: number;
    recommended_models: string[];
    premium_exception_tasks: string[];
  };
};

export type ModelEscalationStep = {
  order: number;
  mode: string;
  task: string;
  model_alias: string;
  resolved_model: string;
  trigger: string;
  requires_operator_review: boolean;
  stop_after_failure: boolean;
};

export type ModelEscalationPlan = {
  task: string;
  display_name: string;
  max_attempts: number;
  hard_stop_signals: string[];
  steps: ModelEscalationStep[];
  quality_signals: string[];
  rationale: string;
};

export type ModelEscalationPolicy = {
  status: string;
  research_basis: Array<{
    id: string;
    url: string;
    signal: string;
  }>;
  policy_notes: string[];
  plans: ModelEscalationPlan[];
  coverage: {
    plan_count: number;
    tasks: string[];
    max_attempts: number;
    premium_escalation_tasks: string[];
  };
};

export type ModelRoutingReplayCheck = {
  id: string;
  status: string;
  expected: string | boolean | null;
  actual: string | boolean | null;
  reason: string;
};

export type ModelRoutingReplayScenario = {
  id: string;
  status: string;
  scenario: {
    id: string;
    task: string;
    signals: string[];
    expected_decision: string;
    max_cost_tier: string;
    expected_operator_review: boolean;
    rationale: string;
  };
  actual: {
    decision?: string | null;
    resolved_model?: string | null;
    cost_tier: string;
    requires_operator_review: boolean;
    reasons: string[];
  };
  checks: ModelRoutingReplayCheck[];
  recommended_action: string;
};

export type ModelRoutingReplay = {
  status: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    scenario_count: number;
    passed_count: number;
    warning_count: number;
    failed_count: number;
    cheap_start_count: number;
    premium_operator_review_count: number;
    hard_stop_count: number;
  };
  scenarios: ModelRoutingReplayScenario[];
};

export type ModelFallbackChainStep = {
  order: number;
  role: string;
  trigger: string;
  model_alias?: string | null;
  resolved_model: string;
  cost_tier: string;
  latency_tier: string;
  model_status: string;
  requires_operator_review: boolean;
  source: string;
  note: string;
};

export type ModelFallbackChain = {
  task: string;
  display_name: string;
  status: string;
  budget_mode: string;
  max_cost_tier: string;
  runtime_default_model?: string | null;
  recommended_model?: string | null;
  source: string;
  hard_stop_signals: string[];
  steps: ModelFallbackChainStep[];
  checks: Array<{
    id: string;
    status: string;
    reason: string;
  }>;
  recommended_action: string;
};

export type ModelFallbackChains = {
  status: string;
  method: {
    strategy: string;
    notes: string[];
  };
  summary: {
    chain_count: number;
    pass_count: number;
    warn_count: number;
    fail_count: number;
    cheap_primary_count: number;
    operator_review_step_count: number;
    premium_exception_task_count: number;
  };
  chains: ModelFallbackChain[];
};

export type ModelCostForecastProfile = {
  task: string;
  initial_model: string;
  escalation_model: string;
  premium_baseline_model: string;
  initial_unit_cost_usd: number | null;
  escalation_unit_cost_usd: number | null;
  premium_baseline_unit_cost_usd: number | null;
  cheap_first_monthly_cost_usd: number | null;
  premium_baseline_monthly_cost_usd: number | null;
  estimated_savings_ratio: number | null;
  estimated_savings_usd: number | null;
  recommended_action: string;
  profile: {
    task: string;
    display_name: string;
    monthly_units: number;
    prompt_tokens_per_unit: number;
    completion_tokens_per_unit: number;
    expected_escalation_rate: number;
    baseline_model_alias: string;
    rationale: string;
  };
};

export type ModelCostForecast = {
  status: string;
  method: {
    unit: string;
    source_basis: string[];
    limitations: string[];
  };
  summary: {
    profile_count: number;
    priced_profile_count: number;
    cheap_first_monthly_cost_usd: number;
    premium_baseline_monthly_cost_usd: number;
    estimated_savings_ratio: number | null;
    estimated_savings_usd: number | null;
  };
  profiles: ModelCostForecastProfile[];
};

export type ModelCostGuardrailCheck = {
  id: string;
  status: string;
  value: number;
  ratio?: number;
  limit?: number;
  warn_threshold?: number;
  fail_threshold?: number;
  forecast_reference_usd?: number;
  reason: string;
};

export type ModelCostGuardrails = {
  status: string;
  thresholds: Record<string, number>;
  summary: {
    request_count: number;
    estimated_cost_usd: number;
    forecast_cheap_first_monthly_cost_usd: number;
    forecast_premium_baseline_monthly_cost_usd: number;
    forecast_savings_ratio: number | null;
    premium_request_ratio: number;
    failure_rate: number;
    unpriced_model_count: number;
  };
  checks: ModelCostGuardrailCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
};

export type ModelOpsResponse = {
  success: boolean;
  routing_aliases: RoutingAliases;
  model_ops_readiness?: ModelOpsReadiness;
  runtime_router?: ModelRuntimeRouter;
  model_configuration_audit?: ModelConfigurationAudit;
  default_template_audit?: ModelDefaultTemplateAudit;
  default_optimization?: ModelDefaultOptimization;
  gateway_compatibility?: ModelGatewayCompatibility;
  gemini_variant_matrix?: GeminiVariantMatrix;
  observed_gemini_model_intake_queue?: ModelOpsObservedGeminiModelIntakeQueue;
  gemini_newapi_alias_capability_coverage?: GeminiNewApiAliasCapabilityCoverage;
  gateway_health_plan?: ModelGatewayHealthPlan;
  gateway_probe_evaluation?: ModelGatewayProbeEvaluation;
  lifecycle_policy?: ModelLifecyclePolicy;
  reasoning_policy?: ModelReasoningPolicy;
  request_policy?: ModelRequestPolicy;
  gateway_request_compatibility_gate?: ModelGatewayRequestCompatibilityGate;
  request_cost_bounds?: ModelRequestCostBounds;
  cache_policy?: ModelCachePolicy;
  route_telemetry?: ModelRouteTelemetry;
  route_telemetry_repository?: ModelRouteTelemetryRepository;
  route_telemetry_ops_summary?: ModelRouteTelemetryOpsSummary;
  route_telemetry_triage?: ModelRouteTelemetryTriage;
  route_telemetry_remediation?: ModelRouteTelemetryRemediation;
  route_guardrails?: ModelRouteGuardrails;
  callsite_audit?: ModelCallsiteAudit;
  budget_policy: ModelBudgetPolicy;
  capability_matrix?: ModelCapabilityMatrix;
  escalation_policy?: ModelEscalationPolicy;
  fallback_chains?: ModelFallbackChains;
  routing_replay?: ModelRoutingReplay;
  cost_forecast?: ModelCostForecast;
  cost_guardrails?: ModelCostGuardrails;
  cheap_first_calibration?: ModelCheapFirstCalibration;
  price_refresh_monitor?: ModelPriceRefreshMonitor;
  catalog_source_audit?: ModelCatalogSourceAudit;
  catalog_candidate_patch_plan?: ModelCatalogCandidatePatchPlan;
  catalog_candidate_impact_replay?: ModelCatalogCandidateImpactReplay;
  gemini_cheap_first_coverage_gate?: ModelOpsGeminiCheapFirstCoverageGate;
  route_quality_budget?: ModelRouteQualityBudget;
  cheap_first_escalation_budget?: ModelOpsCheapFirstEscalationBudget;
  failure_upgrade_budget?: ModelFailureUpgradeBudget;
  legal_benchmark_risk_bridge?: ModelOpsLegalBenchmarkRiskBridge;
  model_ops_performance_budget?: ModelOpsPerformanceBudget;
  cheap_first_release_decision?: ModelOpsCheapFirstReleaseDecision;
  default_change_queue?: ModelOpsDefaultChangeQueue;
  cheap_first_priority_queue?: ModelOpsCheapFirstPriorityQueue;
  gemini_default_change_review?: ModelOpsGeminiDefaultChangeReview;
  gemini_default_cost_impact?: ModelOpsGeminiDefaultCostImpact;
  cheap_first_canary_plan?: ModelOpsCheapFirstCanaryPlan;
  cheap_first_canary_observation?: ModelOpsCheapFirstCanaryObservation;
  cheap_first_canary_promotion_decision?: ModelOpsCheapFirstCanaryPromotionDecision;
  cheap_first_canary_approval_packet?: ModelOpsCheapFirstCanaryApprovalPacket;
  cheap_first_canary_rollback_drill?: ModelOpsCheapFirstCanaryRollbackDrill;
  cheap_first_canary_change_manifest?: ModelOpsCheapFirstCanaryChangeManifest;
  cheap_first_maintainer_execution_checklist?: ModelOpsCheapFirstMaintainerExecutionChecklist;
  models: ModelCatalogItem[];
  usage: ModelUsageSummary;
};

type ApiRequest = {
  url: string;
  method: 'GET' | 'POST';
  data?: Record<string, unknown>;
};

function unwrapApiPayload(value: unknown): unknown {
  if (value && typeof value === 'object' && 'data' in value) {
    const data = (value as { data?: unknown }).data;
    if (data && typeof data === 'object' && 'data' in data) {
      return (data as { data?: unknown }).data;
    }
    return data ?? value;
  }
  return value;
}

function hasModelOpsPayload(value: unknown): boolean {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const payload = value as {
    models?: unknown;
    method?: unknown;
    payload_shape?: unknown;
    summary?: unknown;
    checks?: unknown;
    recommended_actions?: unknown;
    calibration_tasks?: unknown;
    calibration_rows?: unknown;
    model_rows?: unknown;
    family_rows?: unknown;
    validation_commands?: unknown;
    queue_items?: unknown;
    proposal_rows?: unknown;
    impact_rows?: unknown;
    candidate_patch_rows?: unknown;
    candidate_rows?: unknown;
    task_impact_rows?: unknown;
    budget_rows?: unknown;
    canary_steps?: unknown;
    observation_rows?: unknown;
    promotion_items?: unknown;
    approval_items?: unknown;
    rollback_drill_items?: unknown;
    change_manifest_items?: unknown;
    execution_items?: unknown;
    priority_items?: unknown;
    coverage_rows?: unknown;
    route_reviews?: unknown;
    user_need_reviews?: unknown;
    rows?: unknown;
    task_rows?: unknown;
    default_targets?: unknown;
    required?: unknown;
    optional?: unknown;
    forbidden?: unknown;
    example?: unknown;
  };
  return Boolean(
    Array.isArray(payload.models)
      || (Boolean(payload.method) && Boolean(payload.payload_shape))
      || (Array.isArray(payload.required) && Array.isArray(payload.optional) && Array.isArray(payload.forbidden))
      || (Boolean(payload.summary) && Array.isArray(payload.checks) && Array.isArray(payload.recommended_actions))
      || (Boolean(payload.summary) && Array.isArray(payload.calibration_tasks) && Array.isArray(payload.calibration_rows))
      || (Boolean(payload.summary) && Array.isArray(payload.model_rows) && Array.isArray(payload.family_rows))
      || (Boolean(payload.summary) && Array.isArray(payload.checks) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.queue_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.proposal_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.impact_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.candidate_patch_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.candidate_rows) && Array.isArray(payload.task_impact_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.budget_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.canary_steps) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.observation_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.promotion_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.approval_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.rollback_drill_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.change_manifest_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.execution_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.priority_items) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.coverage_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.route_reviews) && Array.isArray(payload.user_need_reviews) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.task_rows) && Array.isArray(payload.validation_commands))
      || (Boolean(payload.summary) && Array.isArray(payload.rows) && Array.isArray(payload.default_targets) && Array.isArray(payload.validation_commands)),
  );
}

function timeoutError(request: ApiRequest): Error {
  const error = new Error(`Model ops API request timed out after ${MODEL_OPS_TOTAL_TIMEOUT_MS}ms: ${request.url}`);
  error.name = 'ModelOpsTimeoutError';
  return error;
}

function isModelOpsTimeoutError(error: unknown): boolean {
  return error instanceof Error && error.name === 'ModelOpsTimeoutError';
}

async function withModelOpsTimeout<T>(promise: Promise<T>, request: ApiRequest): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => reject(timeoutError(request)), MODEL_OPS_TOTAL_TIMEOUT_MS);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

async function fetchModelOpsApi<T>(request: ApiRequest): Promise<T> {
  if (typeof globalThis.fetch !== 'function') {
    throw new Error('Model ops same-origin fetch is unavailable.');
  }
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : undefined;
  const timeoutId = controller
    ? setTimeout(() => controller.abort(), MODEL_OPS_TOTAL_TIMEOUT_MS)
    : undefined;
  try {
    const response = await globalThis.fetch(request.url, {
      method: request.method,
      credentials: 'include',
      headers: request.data ? { 'Content-Type': 'application/json' } : undefined,
      body: request.data ? JSON.stringify(request.data) : undefined,
      signal: controller?.signal,
    });
    if (!response.ok) {
      throw new Error(`Model ops API request failed with HTTP ${response.status}.`);
    }
    const payload = unwrapApiPayload(await response.json());
    if (hasModelOpsPayload(payload)) {
      return payload as T;
    }
    throw new Error('Model ops API response was empty.');
  } catch (err) {
    if (typeof DOMException !== 'undefined' && err instanceof DOMException && err.name === 'AbortError') {
      throw timeoutError(request);
    }
    throw err;
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

async function invokeModelOpsApi<T>(request: ApiRequest): Promise<T> {
  let fetchError: unknown = null;
  if (typeof globalThis.fetch === 'function') {
    try {
      return await fetchModelOpsApi<T>(request);
    } catch (err) {
      fetchError = err;
      if (isModelOpsTimeoutError(err)) {
        throw err;
      }
    }
  }

  let sdkError: unknown = null;
  try {
    const response = await withModelOpsTimeout(
      client.apiCall.invoke({
        url: request.url,
        method: request.method,
        data: request.data,
      }),
      request,
    );
    const payload = unwrapApiPayload(response);
    if (hasModelOpsPayload(payload)) {
      return payload as T;
    }
  } catch (err) {
    sdkError = err;
  }

  if (fetchError) {
    throw fetchError;
  }
  if (sdkError) {
    throw sdkError;
  }
  throw new Error('Model ops API response was empty.');
}

export async function getModelOps(): Promise<ModelOpsResponse> {
  return invokeModelOpsApi<ModelOpsResponse>({
    url: '/api/v1/aihub/models',
    method: 'GET',
  });
}

export async function getModelGatewayProbeTemplate(): Promise<ModelGatewayProbeTemplate> {
  return invokeModelOpsApi<ModelGatewayProbeTemplate>({
    url: '/api/v1/aihub/models/gateway-probe-template',
    method: 'GET',
  });
}

export async function evaluateModelGatewayProbe(payload: Record<string, unknown>): Promise<ModelGatewayProbeEvaluation> {
  return invokeModelOpsApi<ModelGatewayProbeEvaluation>({
    url: '/api/v1/aihub/models/gateway-probe-evaluation',
    method: 'POST',
    data: payload,
  });
}

export async function getCheapFirstCalibration(): Promise<ModelCheapFirstCalibration> {
  return invokeModelOpsApi<ModelCheapFirstCalibration>({
    url: '/api/v1/aihub/models/cheap-first-calibration',
    method: 'GET',
  });
}

export async function getGeminiVariantMatrix(): Promise<GeminiVariantMatrix> {
  return invokeModelOpsApi<GeminiVariantMatrix>({
    url: '/api/v1/aihub/models/gemini-variant-matrix',
    method: 'GET',
  });
}

export async function getModelOpsObservedGeminiModelIntakeQueue(): Promise<ModelOpsObservedGeminiModelIntakeQueue> {
  return invokeModelOpsApi<ModelOpsObservedGeminiModelIntakeQueue>({
    url: '/api/v1/aihub/models/observed-gemini-model-intake-queue',
    method: 'GET',
  });
}

export async function getGeminiNewApiAliasCapabilityCoverage(): Promise<GeminiNewApiAliasCapabilityCoverage> {
  return invokeModelOpsApi<GeminiNewApiAliasCapabilityCoverage>({
    url: '/api/v1/aihub/models/gemini-newapi-alias-capability-coverage',
    method: 'GET',
  });
}

export async function getGeminiCheapFirstCoverageGate(): Promise<ModelOpsGeminiCheapFirstCoverageGate> {
  return invokeModelOpsApi<ModelOpsGeminiCheapFirstCoverageGate>({
    url: '/api/v1/aihub/models/gemini-cheap-first-coverage-gate',
    method: 'GET',
  });
}

export async function getModelDefaultTemplateAudit(): Promise<ModelDefaultTemplateAudit> {
  return invokeModelOpsApi<ModelDefaultTemplateAudit>({
    url: '/api/v1/aihub/models/default-template-audit',
    method: 'GET',
  });
}

export async function getModelCatalogSourceAudit(): Promise<ModelCatalogSourceAudit> {
  return invokeModelOpsApi<ModelCatalogSourceAudit>({
    url: '/api/v1/aihub/models/catalog-source-audit',
    method: 'GET',
  });
}

export async function getModelCatalogCandidatePatchPlan(): Promise<ModelCatalogCandidatePatchPlan> {
  return invokeModelOpsApi<ModelCatalogCandidatePatchPlan>({
    url: '/api/v1/aihub/models/catalog-candidate-patch-plan',
    method: 'GET',
  });
}

export async function getModelCatalogCandidateImpactReplay(): Promise<ModelCatalogCandidateImpactReplay> {
  return invokeModelOpsApi<ModelCatalogCandidateImpactReplay>({
    url: '/api/v1/aihub/models/catalog-candidate-impact-replay',
    method: 'GET',
  });
}

export async function getModelGatewayRequestCompatibilityGate(): Promise<ModelGatewayRequestCompatibilityGate> {
  return invokeModelOpsApi<ModelGatewayRequestCompatibilityGate>({
    url: '/api/v1/aihub/models/gateway-request-compatibility-gate',
    method: 'GET',
  });
}

export async function evaluateModelGatewayRequestCompatibilityGate(
  payload: Record<string, unknown>,
): Promise<ModelGatewayRequestCompatibilityGate> {
  return invokeModelOpsApi<ModelGatewayRequestCompatibilityGate>({
    url: '/api/v1/aihub/models/gateway-request-compatibility-gate',
    method: 'POST',
    data: payload,
  });
}

export async function getModelOpsCheapFirstReleaseDecision(): Promise<ModelOpsCheapFirstReleaseDecision> {
  return invokeModelOpsApi<ModelOpsCheapFirstReleaseDecision>({
    url: '/api/v1/aihub/models/cheap-first-release-decision',
    method: 'GET',
  });
}

export async function getModelOpsDefaultChangeQueue(): Promise<ModelOpsDefaultChangeQueue> {
  return invokeModelOpsApi<ModelOpsDefaultChangeQueue>({
    url: '/api/v1/aihub/models/default-change-queue',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstPriorityQueue(): Promise<ModelOpsCheapFirstPriorityQueue> {
  return invokeModelOpsApi<ModelOpsCheapFirstPriorityQueue>({
    url: '/api/v1/aihub/models/cheap-first-priority-queue',
    method: 'GET',
  });
}

export async function getModelOpsGeminiDefaultChangeReview(): Promise<ModelOpsGeminiDefaultChangeReview> {
  return invokeModelOpsApi<ModelOpsGeminiDefaultChangeReview>({
    url: '/api/v1/aihub/models/gemini-default-change-review',
    method: 'GET',
  });
}

export async function evaluateModelOpsGeminiDefaultChangeReview(
  payload: Record<string, unknown>,
): Promise<ModelOpsGeminiDefaultChangeReview> {
  return invokeModelOpsApi<ModelOpsGeminiDefaultChangeReview>({
    url: '/api/v1/aihub/models/gemini-default-change-review',
    method: 'POST',
    data: payload,
  });
}

export async function getModelOpsGeminiDefaultCostImpact(): Promise<ModelOpsGeminiDefaultCostImpact> {
  return invokeModelOpsApi<ModelOpsGeminiDefaultCostImpact>({
    url: '/api/v1/aihub/models/gemini-default-cost-impact',
    method: 'GET',
  });
}

export async function evaluateModelOpsGeminiDefaultCostImpact(
  payload: Record<string, unknown>,
): Promise<ModelOpsGeminiDefaultCostImpact> {
  return invokeModelOpsApi<ModelOpsGeminiDefaultCostImpact>({
    url: '/api/v1/aihub/models/gemini-default-cost-impact',
    method: 'POST',
    data: payload,
  });
}

export async function getModelOpsCheapFirstCanaryPlan(): Promise<ModelOpsCheapFirstCanaryPlan> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryPlan>({
    url: '/api/v1/aihub/models/cheap-first-canary-plan',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstCanaryObservation(): Promise<ModelOpsCheapFirstCanaryObservation> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryObservation>({
    url: '/api/v1/aihub/models/cheap-first-canary-observation',
    method: 'GET',
  });
}

export async function evaluateModelOpsCheapFirstCanaryObservation(
  payload: Record<string, unknown>,
): Promise<ModelOpsCheapFirstCanaryObservation> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryObservation>({
    url: '/api/v1/aihub/models/cheap-first-canary-observation',
    method: 'POST',
    data: payload,
  });
}

export async function getModelOpsCheapFirstCanaryPromotionDecision(): Promise<ModelOpsCheapFirstCanaryPromotionDecision> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryPromotionDecision>({
    url: '/api/v1/aihub/models/cheap-first-canary-promotion-decision',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstCanaryApprovalPacket(): Promise<ModelOpsCheapFirstCanaryApprovalPacket> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryApprovalPacket>({
    url: '/api/v1/aihub/models/cheap-first-canary-approval-packet',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstCanaryRollbackDrill(): Promise<ModelOpsCheapFirstCanaryRollbackDrill> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryRollbackDrill>({
    url: '/api/v1/aihub/models/cheap-first-canary-rollback-drill',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstCanaryChangeManifest(): Promise<ModelOpsCheapFirstCanaryChangeManifest> {
  return invokeModelOpsApi<ModelOpsCheapFirstCanaryChangeManifest>({
    url: '/api/v1/aihub/models/cheap-first-canary-change-manifest',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstMaintainerExecutionChecklist(): Promise<ModelOpsCheapFirstMaintainerExecutionChecklist> {
  return invokeModelOpsApi<ModelOpsCheapFirstMaintainerExecutionChecklist>({
    url: '/api/v1/aihub/models/cheap-first-maintainer-execution-checklist',
    method: 'GET',
  });
}

export async function getModelOpsPerformanceBudget(): Promise<ModelOpsPerformanceBudget> {
  return invokeModelOpsApi<ModelOpsPerformanceBudget>({
    url: '/api/v1/aihub/models/performance-budget',
    method: 'GET',
  });
}

export async function evaluateModelOpsPerformanceBudget(payload: Record<string, unknown>): Promise<ModelOpsPerformanceBudget> {
  return invokeModelOpsApi<ModelOpsPerformanceBudget>({
    url: '/api/v1/aihub/models/performance-budget',
    method: 'POST',
    data: payload,
  });
}

export async function getModelRouteQualityBudget(): Promise<ModelRouteQualityBudget> {
  return invokeModelOpsApi<ModelRouteQualityBudget>({
    url: '/api/v1/aihub/models/route-quality-budget',
    method: 'GET',
  });
}

export async function getModelOpsCheapFirstEscalationBudget(): Promise<ModelOpsCheapFirstEscalationBudget> {
  return invokeModelOpsApi<ModelOpsCheapFirstEscalationBudget>({
    url: '/api/v1/aihub/models/cheap-first-escalation-budget',
    method: 'GET',
  });
}

export async function evaluateModelOpsCheapFirstEscalationBudget(
  payload: Record<string, unknown>,
): Promise<ModelOpsCheapFirstEscalationBudget> {
  return invokeModelOpsApi<ModelOpsCheapFirstEscalationBudget>({
    url: '/api/v1/aihub/models/cheap-first-escalation-budget',
    method: 'POST',
    data: payload,
  });
}

export async function getModelFailureUpgradeBudget(): Promise<ModelFailureUpgradeBudget> {
  return invokeModelOpsApi<ModelFailureUpgradeBudget>({
    url: '/api/v1/aihub/models/failure-upgrade-budget',
    method: 'GET',
  });
}

export async function getModelFailureUpgradeBudgetTemplate(): Promise<ModelFailureUpgradeBudgetPayloadShape> {
  return invokeModelOpsApi<ModelFailureUpgradeBudgetPayloadShape>({
    url: '/api/v1/aihub/models/failure-upgrade-budget-template',
    method: 'GET',
  });
}

export async function evaluateModelFailureUpgradeBudget(
  payload: Record<string, unknown>,
): Promise<ModelFailureUpgradeBudget> {
  return invokeModelOpsApi<ModelFailureUpgradeBudget>({
    url: '/api/v1/aihub/models/failure-upgrade-budget',
    method: 'POST',
    data: payload,
  });
}

export async function getModelOpsLegalBenchmarkRiskBridge(): Promise<ModelOpsLegalBenchmarkRiskBridge> {
  return invokeModelOpsApi<ModelOpsLegalBenchmarkRiskBridge>({
    url: '/api/v1/aihub/models/legal-benchmark-risk-bridge',
    method: 'GET',
  });
}

export async function evaluateGeminiVariantMatrix(payload: Record<string, unknown>): Promise<GeminiVariantMatrix> {
  return invokeModelOpsApi<GeminiVariantMatrix>({
    url: '/api/v1/aihub/models/gemini-variant-matrix',
    method: 'POST',
    data: payload,
  });
}

export async function evaluateModelOpsObservedGeminiModelIntakeQueue(
  payload: Record<string, unknown>,
): Promise<ModelOpsObservedGeminiModelIntakeQueue> {
  return invokeModelOpsApi<ModelOpsObservedGeminiModelIntakeQueue>({
    url: '/api/v1/aihub/models/observed-gemini-model-intake-queue',
    method: 'POST',
    data: payload,
  });
}

export async function evaluateGeminiNewApiAliasCapabilityCoverage(
  payload: Record<string, unknown>,
): Promise<GeminiNewApiAliasCapabilityCoverage> {
  return invokeModelOpsApi<GeminiNewApiAliasCapabilityCoverage>({
    url: '/api/v1/aihub/models/gemini-newapi-alias-capability-coverage',
    method: 'POST',
    data: payload,
  });
}

export async function evaluateCheapFirstCalibration(
  payload: Record<string, unknown>,
): Promise<ModelCheapFirstCalibration> {
  return invokeModelOpsApi<ModelCheapFirstCalibration>({
    url: '/api/v1/aihub/models/cheap-first-calibration',
    method: 'POST',
    data: payload,
  });
}
