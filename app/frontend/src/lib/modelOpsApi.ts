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

export type ModelOpsResponse = {
  success: boolean;
  routing_aliases: RoutingAliases;
  budget_policy: ModelBudgetPolicy;
  capability_matrix?: ModelCapabilityMatrix;
  escalation_policy?: ModelEscalationPolicy;
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
