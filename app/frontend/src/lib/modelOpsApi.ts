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
  reasoning_policy?: ModelReasoningPolicy;
  request_policy?: ModelRequestPolicy;
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
