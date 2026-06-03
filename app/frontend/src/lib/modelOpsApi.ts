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
  budget_policy: ModelBudgetPolicy;
  capability_matrix?: ModelCapabilityMatrix;
  escalation_policy?: ModelEscalationPolicy;
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
