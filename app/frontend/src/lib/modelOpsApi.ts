import { client } from '@/lib/api';

export type RoutingAliases = Record<string, string>;

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

export type ModelGatewayHealthPlanRole = {
  role: string;
  model: string;
  canonical_model?: string | null;
  is_known_model: boolean;
  cost_tier?: string | null;
  model_status: string;
  cheap_first_aligned: boolean;
  estimated_probe_cost_usd?: number | null;
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
    cheap_candidate_count: number;
    probed_cheap_candidate_count: number;
    recommended_change_count: number;
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
    http_status?: number | null;
    json_ok?: boolean | null;
    latency_ms?: number | null;
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
  source_summaries: Record<string, Record<string, unknown>>;
  recommended_actions: string[];
  release_guardrails: string[];
  privacy_boundary: Record<string, boolean | string>;
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

export type ModelOpsReadiness = {
  status: string;
  release_recommendation: string;
  method: {
    type: string;
    notes: string[];
  };
  summary: {
    component_count: number;
    pass_count: number;
    warn_count: number;
    fail_count: number;
    blocking_count: number;
    warning_count: number;
  };
  checks: ModelOpsReadinessCheck[];
  blocking_check_ids: string[];
  warning_check_ids: string[];
  recommended_actions: string[];
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
  default_optimization?: ModelDefaultOptimization;
  gateway_compatibility?: ModelGatewayCompatibility;
  gateway_health_plan?: ModelGatewayHealthPlan;
  lifecycle_policy?: ModelLifecyclePolicy;
  reasoning_policy?: ModelReasoningPolicy;
  request_policy?: ModelRequestPolicy;
  request_cost_bounds?: ModelRequestCostBounds;
  cache_policy?: ModelCachePolicy;
  route_telemetry?: ModelRouteTelemetry;
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
  models: ModelCatalogItem[];
  usage: ModelUsageSummary;
};

export async function getModelOps(): Promise<ModelOpsResponse> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/aihub/models',
    method: 'GET',
  });
  return (resp?.data ?? resp) as ModelOpsResponse;
}

export async function getModelGatewayProbeTemplate(): Promise<ModelGatewayProbeTemplate> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/aihub/models/gateway-probe-template',
    method: 'GET',
  });
  return (resp?.data?.data ?? resp?.data ?? resp) as ModelGatewayProbeTemplate;
}

export async function evaluateModelGatewayProbe(payload: Record<string, unknown>): Promise<ModelGatewayProbeEvaluation> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/aihub/models/gateway-probe-evaluation',
    method: 'POST',
    data: payload,
  });
  return (resp?.data?.data ?? resp?.data ?? resp) as ModelGatewayProbeEvaluation;
}

export async function getCheapFirstCalibration(): Promise<ModelCheapFirstCalibration> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/aihub/models/cheap-first-calibration',
    method: 'GET',
  });
  return (resp?.data?.data ?? resp?.data ?? resp) as ModelCheapFirstCalibration;
}

export async function evaluateCheapFirstCalibration(
  payload: Record<string, unknown>,
): Promise<ModelCheapFirstCalibration> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/aihub/models/cheap-first-calibration',
    method: 'POST',
    data: payload,
  });
  return (resp?.data?.data ?? resp?.data ?? resp) as ModelCheapFirstCalibration;
}
