import { useEffect, useMemo, useState } from 'react';
import AuthGuard from '@/components/AuthGuard';
import Layout from '@/components/Layout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertTriangle, Gauge, Loader2, RefreshCw, Route, Zap } from 'lucide-react';
import { getModelOps, type ModelCatalogItem, type ModelOpsResponse } from '@/lib/modelOpsApi';

const costClass: Record<string, string> = {
  lowest: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  low: 'bg-lime-50 text-lime-800 border-lime-200',
  medium: 'bg-amber-50 text-amber-900 border-amber-200',
  premium: 'bg-red-50 text-red-800 border-red-200',
};

function formatNumber(value?: number) {
  return new Intl.NumberFormat('en-US').format(value ?? 0);
}

function formatUsd(value?: number | null) {
  if (value == null) return 'unpriced';
  return `$${value.toFixed(value < 0.01 ? 6 : 4)}`;
}

function roleText(model: ModelCatalogItem) {
  return model.configured_roles.length ? model.configured_roles.join(', ') : '-';
}

export default function ModelOpsPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const [data, setData] = useState<ModelOpsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setData(await getModelOps());
    } catch (err) {
      console.error(err);
      setError('Model telemetry failed to load.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const aliases = useMemo(() => Object.entries(data?.routing_aliases ?? {}), [data]);
  const usageRows = useMemo(() => Object.entries(data?.usage.models ?? {}), [data]);
  const runtimeRouterFields = useMemo(() => Object.entries(data?.runtime_router?.request_fields ?? {}), [data]);
  const runtimeDefaults = data?.runtime_router?.task_defaults ?? [];
  const configurationAuditRows = data?.model_configuration_audit?.checks ?? [];
  const taskInferenceRules = data?.runtime_router?.auto_task_inference?.rules ?? [];
  const reasoningRows = data?.reasoning_policy?.task_defaults ?? [];
  const requestPolicyRows = data?.request_policy?.task_defaults ?? [];
  const routeTelemetryRows = useMemo(() => Object.entries(data?.route_telemetry?.by_task ?? {}), [data]);
  const routeGuardrailRows = data?.route_guardrails?.checks ?? [];
  const callsiteRows = data?.callsite_audit?.callsites ?? [];
  const budgetRows = data?.budget_policy.task_decisions ?? [];
  const capabilityRows = data?.capability_matrix?.tasks ?? [];
  const escalationRows = data?.escalation_policy?.plans ?? [];
  const fallbackChainRows = data?.fallback_chains?.chains ?? [];
  const routingReplayRows = data?.routing_replay?.scenarios ?? [];
  const forecastRows = data?.cost_forecast?.profiles ?? [];
  const guardrailRows = data?.cost_guardrails?.checks ?? [];
  const totals = data?.usage.totals;

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-stone-950/15 pb-6">
          <div>
            <div className="eyebrow mb-3">Model Ops</div>
            <h1 className="text-4xl font-black leading-none text-stone-950 sm:text-6xl">AI Model Routing</h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600">
              Runtime routing, model catalog, and aggregate usage counters for cost-aware legal review.
            </p>
          </div>
          <Button variant="outline" className="soft-button" onClick={load} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </Button>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Route className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{aliases.length}</div>
              <div className="mt-1 text-sm text-stone-600">routing aliases</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Zap className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{data?.models.length ?? 0}</div>
              <div className="mt-1 text-sm text-stone-600">catalog models</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatNumber(totals?.requests)}</div>
              <div className="mt-1 text-sm text-stone-600">requests recorded</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatNumber(totals?.total_tokens)}</div>
              <div className="mt-1 text-sm text-stone-600">tokens recorded</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatUsd(totals?.estimated_cost_usd)}</div>
              <div className="mt-1 text-sm text-stone-600">estimated cost</div>
            </CardContent>
          </Card>
        </div>

        {data?.cost_guardrails && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cost guardrails</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.cost_guardrails.blocking_check_ids.length} blocking ·{' '}
                  {data.cost_guardrails.warning_check_ids.length} warning checks
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.cost_guardrails.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.cost_guardrails.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.cost_guardrails.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.cost_guardrails.summary.estimated_cost_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">actual estimate</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.cost_guardrails.summary.premium_request_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">premium ratio</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.cost_guardrails.summary.failure_rate * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">failure rate</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cost_guardrails.summary.unpriced_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unpriced models</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {guardrailRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{check.ratio != null ? `${Math.round(check.ratio * 100)}%` : check.value}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        <section className="mb-8">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-xl font-black text-stone-950">Routing aliases</h2>
            {data?.budget_policy && (
              <Badge variant="outline" className="bg-white">
                premium review {data.budget_policy.premium_requires_review ? 'on' : 'off'}
              </Badge>
            )}
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {aliases.map(([alias, model]) => (
              <div key={alias} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="font-mono text-sm font-semibold text-stone-950">{alias}</div>
                <div className="mt-2 break-words text-sm text-stone-600">{model}</div>
              </div>
            ))}
          </div>
        </section>

        {data?.model_configuration_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Configuration audit</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.model_configuration_audit.summary.role_count} roles /{' '}
                  {data.model_configuration_audit.summary.unknown_model_count} unknown models
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.model_configuration_audit.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.model_configuration_audit.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.model_configuration_audit.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Gaps</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {configurationAuditRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{check.label}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{check.env_var ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{check.model}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[check.cost_tier || ''] ?? 'bg-white'}>
                          {check.cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">max {check.max_cost_tier}</div>
                      </TableCell>
                      <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                        {check.missing_required_capabilities.length || check.missing_preferred_capabilities.length
                          ? [...check.missing_required_capabilities, ...check.missing_preferred_capabilities].join(', ')
                          : '-'}
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.runtime_router && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Runtime router</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {runtimeDefaults.length} task defaults / {taskInferenceRules.length} auto rules
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.runtime_router.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              {runtimeRouterFields.map(([field, note]) => (
                <div key={field} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="font-mono text-sm font-semibold text-stone-950">{field}</div>
                  <div className="mt-2 text-xs leading-5 text-stone-600">{note}</div>
                </div>
              ))}
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Default model</TableHead>
                    <TableHead>Budget</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runtimeDefaults.map((row) => (
                    <TableRow key={`runtime-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.resolved_model}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          max {row.max_cost_tier}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.budget_mode}</TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {data.runtime_router.auto_task_inference && (
              <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="font-semibold text-stone-950">Auto task inference</div>
                  <Badge variant="outline" className="bg-white">
                    default {data.runtime_router.auto_task_inference.default_task}
                  </Badge>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  {taskInferenceRules.map((rule) => (
                    <div key={rule} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 text-xs leading-5 text-stone-600">
                      {rule}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {data?.reasoning_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Reasoning policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {reasoningRows.length} task defaults / request default {data.reasoning_policy.request_field.default}
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.reasoning_policy.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Effort</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Supported</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reasoningRows.map((row) => (
                    <TableRow key={`reasoning-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.model}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.cost_mode === 'elevated-thinking'
                              ? 'border-amber-200 bg-amber-50 text-amber-900'
                              : row.cost_mode === 'thinking-disabled'
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                                : 'bg-white'
                          }
                        >
                          {row.effective_effort ?? 'omitted'}
                        </Badge>
                        {row.adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">adjusted</div>}
                      </TableCell>
                      <TableCell className="text-xs text-stone-600">{row.cost_mode}</TableCell>
                      <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                        {row.supported_efforts.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.request_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Request policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {requestPolicyRows.length} task defaults / temperature and token ceilings
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.request_policy.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Temperature</TableHead>
                    <TableHead>Max tokens</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requestPolicyRows.map((row) => (
                    <TableRow key={`request-policy-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{row.effective_temperature}</div>
                        {row.temperature_adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">clamped</div>}
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{formatNumber(row.effective_max_tokens)}</div>
                        {row.max_tokens_adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">clamped</div>}
                      </TableCell>
                      <TableCell>{row.response_format_mode}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={row.cost_mode === 'caller-expanded' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'bg-white'}>
                          {row.cost_mode}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry.summary.request_count} routed requests /{' '}
                  {Math.round(data.route_telemetry.summary.downgrade_ratio * 100)}% downgraded
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.route_telemetry.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_telemetry.summary.auto_inferred_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">auto inferred</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_telemetry.summary.over_budget_request_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">over budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry.summary.operator_review_request_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">review-gated</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry.summary.unknown_price_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown price</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Requests</TableHead>
                    <TableHead>Auto</TableHead>
                    <TableHead>Downgraded</TableHead>
                    <TableHead>Over budget</TableHead>
                    <TableHead>Failure</TableHead>
                    <TableHead>Models</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-stone-500">
                        No routed text calls recorded in this backend process.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryRows.map(([task, bucket]) => (
                      <TableRow key={task}>
                        <TableCell className="font-mono font-semibold text-stone-950">{task}</TableCell>
                        <TableCell>{formatNumber(bucket.requests)}</TableCell>
                        <TableCell>{formatNumber(bucket.auto_inferred)}</TableCell>
                        <TableCell>{formatNumber(bucket.downgraded_to_recommended)}</TableCell>
                        <TableCell>{formatNumber(bucket.over_budget_requested)}</TableCell>
                        <TableCell>{formatNumber(bucket.failures)}</TableCell>
                        <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                          {Object.entries(bucket.models).map(([model, count]) => `${model}:${count}`).join(', ')}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_guardrails && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route guardrails</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_guardrails.blocking_check_ids.length} blocking ·{' '}
                  {data.route_guardrails.warning_check_ids.length} warning checks
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.route_guardrails.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.route_guardrails.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.route_guardrails.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.failure_rate * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">route failures</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.over_budget_route_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">over budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.operator_review_route_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">review gated</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_guardrails.summary.unknown_price_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown price</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeGuardrailRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{check.ratio != null ? `${Math.round(check.ratio * 100)}%` : check.value}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.callsite_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Callsite audit</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.callsite_audit.summary.explicit_task_count} explicit /{' '}
                  {data.callsite_audit.summary.callsite_count} service calls
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.callsite_audit.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.callsite_audit.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.callsite_audit.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.missing_task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">missing tasks</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.with_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">explicit models</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.fail_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">failures</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Callsite</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {callsiteRows.map((row) => (
                    <TableRow key={`${row.file}:${row.line}`}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">
                          {row.file}:{row.line}
                        </div>
                        <div className="mt-1 text-xs text-stone-500">{row.function}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.has_task ? 'explicit' : 'missing'}</TableCell>
                      <TableCell>{row.has_model ? 'explicit' : '-'}</TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        <section className="mb-8">
          <h2 className="mb-3 text-xl font-black text-stone-950">Budget policy</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Resolved model</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Max</TableHead>
                  <TableHead>Operator review</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {budgetRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                    <TableCell>{row.budget_mode}</TableCell>
                    <TableCell className="font-mono text-xs">{row.resolved_model}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? ''}>
                        {row.cost_tier || 'unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell>{row.max_cost_tier}</TableCell>
                    <TableCell>{row.requires_operator_review ? 'required' : row.is_over_budget ? 'recommended' : '-'}</TableCell>
                    <TableCell className="max-w-[360px] text-xs text-stone-600">{row.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Capability matrix</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.capability_matrix?.coverage.task_count ?? 0} tasks ·{' '}
                {(data?.capability_matrix?.coverage.recommended_models ?? []).length} recommended models
              </div>
            </div>
            <Badge variant="outline" className="bg-white">
              {data?.capability_matrix?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Recommended</TableHead>
                  <TableHead>Runtime default</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Capabilities</TableHead>
                  <TableHead>Candidates</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {capabilityRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.requirement.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-stone-700">{row.recommended_model}</TableCell>
                    <TableCell>
                      <div className="font-mono text-xs text-stone-700">{row.runtime_default_model}</div>
                      <Badge
                        variant="outline"
                        className={
                          row.runtime_default_is_recommended
                            ? 'mt-1 border-emerald-200 bg-emerald-50 text-emerald-800'
                            : 'mt-1 border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {row.runtime_default_is_recommended ? 'aligned' : 'review'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[row.requirement.max_cost_tier] ?? 'bg-white'}>
                        max {row.requirement.max_cost_tier}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                      {row.requirement.required_capabilities.join(', ')}
                    </TableCell>
                    <TableCell className="text-stone-700">{row.candidate_count}</TableCell>
                    <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">{row.requirement.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Fallback chains</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.fallback_chains?.summary.chain_count ?? 0} chains /{' '}
                {data?.fallback_chains?.summary.operator_review_step_count ?? 0} operator-review steps
              </div>
            </div>
            <Badge
              variant="outline"
              className={
                data?.fallback_chains?.status === 'pass'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : data?.fallback_chains?.status === 'fail'
                    ? 'border-red-200 bg-red-50 text-red-800'
                    : 'border-amber-200 bg-amber-50 text-amber-900'
              }
            >
              {data?.fallback_chains?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="mb-3 grid gap-3 md:grid-cols-4">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.cheap_primary_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">cheap primaries</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.premium_exception_task_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">premium tasks</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.warn_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">warnings</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.fail_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">failures</div>
            </div>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Chain</TableHead>
                  <TableHead>Hard stops</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fallbackChainRows.map((chain) => (
                  <TableRow key={chain.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{chain.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{chain.task}</div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          chain.status === 'pass'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            : chain.status === 'fail'
                              ? 'border-red-200 bg-red-50 text-red-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {chain.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[chain.max_cost_tier] ?? 'bg-white'}>
                        max {chain.max_cost_tier}
                      </Badge>
                      <div className="mt-1 text-xs text-stone-500">{chain.budget_mode}</div>
                    </TableCell>
                    <TableCell className="max-w-[420px]">
                      <div className="space-y-1">
                        {chain.steps.map((step) => (
                          <div key={`${chain.task}-${step.order}`} className="rounded-[6px] border border-stone-950/10 bg-white px-2 py-1">
                            <div className="font-mono text-[11px] text-stone-950">
                              {step.order}. {step.role}: {step.resolved_model}
                            </div>
                            <div className="mt-1 flex flex-wrap gap-1">
                              <Badge variant="outline" className={costClass[step.cost_tier] ?? 'bg-white'}>
                                {step.cost_tier}
                              </Badge>
                              <Badge variant="outline" className="bg-white">
                                {step.latency_tier}
                              </Badge>
                              {step.requires_operator_review && (
                                <Badge variant="outline" className="border-red-200 bg-red-50 text-red-800">
                                  review
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {chain.hard_stop_signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                      {chain.recommended_action}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Routing replay</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.routing_replay?.summary.scenario_count ?? 0} scenarios /{' '}
                {data?.routing_replay?.summary.failed_count ?? 0} failures
              </div>
            </div>
            <Badge
              variant="outline"
              className={
                data?.routing_replay?.status === 'pass'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : data?.routing_replay?.status === 'fail'
                    ? 'border-red-200 bg-red-50 text-red-800'
                    : 'border-amber-200 bg-amber-50 text-amber-900'
              }
            >
              {data?.routing_replay?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="mb-3 grid gap-3 md:grid-cols-4">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.cheap_start_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">cheap starts</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.premium_operator_review_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">premium reviews</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.hard_stop_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">hard stops</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.passed_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">passed scenarios</div>
            </div>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scenario</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Task</TableHead>
                  <TableHead>Signals</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {routingReplayRows.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      <div className="font-mono text-xs font-semibold text-stone-950">{row.id}</div>
                      <div className="mt-1 max-w-[320px] text-xs leading-5 text-stone-600">
                        {row.scenario.rationale}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          row.status === 'pass'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            : row.status === 'fail'
                              ? 'border-red-200 bg-red-50 text-red-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {row.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-stone-700">{row.scenario.task}</TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {row.scenario.signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.actual.decision ?? '-'}</div>
                      <div className="mt-1 text-xs text-stone-500">expected {row.scenario.expected_decision}</div>
                    </TableCell>
                    <TableCell className="max-w-[240px]">
                      <div className="font-mono text-xs text-stone-700">{row.actual.resolved_model ?? 'no spend'}</div>
                      <Badge variant="outline" className={`mt-1 ${costClass[row.actual.cost_tier] ?? 'bg-white'}`}>
                        {row.actual.cost_tier}
                      </Badge>
                      {row.actual.requires_operator_review && (
                        <div className="mt-1 text-[11px] font-semibold text-red-700">operator review</div>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                      {row.recommended_action}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Escalation policy</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.escalation_policy?.coverage.plan_count ?? 0} plans · max{' '}
                {data?.escalation_policy?.coverage.max_attempts ?? 0} attempts
              </div>
            </div>
            <Badge variant="outline" className="bg-white">
              {data?.escalation_policy?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>Quality signals</TableHead>
                  <TableHead>Hard stops</TableHead>
                  <TableHead>Rationale</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {escalationRows.map((plan) => (
                  <TableRow key={plan.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{plan.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{plan.task}</div>
                    </TableCell>
                    <TableCell className="max-w-[320px]">
                      <div className="space-y-1">
                        {plan.steps.map((step) => (
                          <div key={`${plan.task}-${step.order}`} className="rounded-[6px] border border-stone-950/10 bg-white px-2 py-1">
                            <div className="font-mono text-[11px] text-stone-950">
                              {step.order}. {step.mode}: {step.resolved_model}
                            </div>
                            {step.requires_operator_review && (
                              <div className="mt-1 text-[11px] font-semibold text-red-700">operator review</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                      {plan.quality_signals.join(', ')}
                    </TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {plan.hard_stop_signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">{plan.rationale}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Cost forecast</h2>
              <div className="mt-1 text-sm text-stone-600">
                cheap-first {formatUsd(data?.cost_forecast?.summary.cheap_first_monthly_cost_usd)} / premium baseline{' '}
                {formatUsd(data?.cost_forecast?.summary.premium_baseline_monthly_cost_usd)}
              </div>
            </div>
            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
              saves {Math.round((data?.cost_forecast?.summary.estimated_savings_ratio ?? 0) * 100)}%
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Profile</TableHead>
                  <TableHead>Models</TableHead>
                  <TableHead>Monthly volume</TableHead>
                  <TableHead>Cheap-first</TableHead>
                  <TableHead>Premium baseline</TableHead>
                  <TableHead>Savings</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {forecastRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.profile.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                    </TableCell>
                    <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                      start {row.initial_model}
                      <br />
                      up {row.escalation_model}
                    </TableCell>
                    <TableCell className="text-xs leading-5 text-stone-600">
                      {formatNumber(row.profile.monthly_units)} units
                      <br />
                      {Math.round(row.profile.expected_escalation_rate * 100)}% escalation
                    </TableCell>
                    <TableCell>{formatUsd(row.cheap_first_monthly_cost_usd)}</TableCell>
                    <TableCell>{formatUsd(row.premium_baseline_monthly_cost_usd)}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                        {Math.round((row.estimated_savings_ratio ?? 0) * 100)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">{row.recommended_action}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="mb-3 text-xl font-black text-stone-950">Model catalog</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Context</TableHead>
                  <TableHead>Token price</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Best for</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data?.models ?? []).map((model) => (
                  <TableRow key={model.id}>
                    <TableCell className="font-mono font-semibold text-stone-950">{model.id}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[model.cost_tier] ?? ''}>
                        {model.cost_tier}
                      </Badge>
                    </TableCell>
                    <TableCell>{model.latency_tier}</TableCell>
                    <TableCell>{model.status}</TableCell>
                    <TableCell>{model.context_window_tokens ? formatNumber(model.context_window_tokens) : '-'}</TableCell>
                    <TableCell className="text-xs text-stone-600">
                      in {formatUsd(model.pricing.input_usd_per_million_tokens)} / out{' '}
                      {formatUsd(model.pricing.output_usd_per_million_tokens)}
                    </TableCell>
                    <TableCell>{roleText(model)}</TableCell>
                    <TableCell className="max-w-[320px] text-stone-600">{model.best_for.join(', ')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-black text-stone-950">Usage counters</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Requests</TableHead>
                  <TableHead>Success</TableHead>
                  <TableHead>Failure</TableHead>
                  <TableHead>Total tokens</TableHead>
                  <TableHead>Est. cost</TableHead>
                  <TableHead>Avg latency</TableHead>
                  <TableHead>Tasks</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usageRows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-8 text-center text-stone-500">
                      No model calls recorded in this backend process.
                    </TableCell>
                  </TableRow>
                ) : (
                  usageRows.map(([model, usage]) => (
                    <TableRow key={model}>
                      <TableCell className="font-mono font-semibold text-stone-950">{model}</TableCell>
                      <TableCell>{formatNumber(usage.requests)}</TableCell>
                      <TableCell>{formatNumber(usage.successes)}</TableCell>
                      <TableCell>{formatNumber(usage.failures)}</TableCell>
                      <TableCell>{formatNumber(usage.total_tokens)}</TableCell>
                      <TableCell>{formatUsd(usage.estimated_cost_usd)}</TableCell>
                      <TableCell>{usage.avg_latency_ms}ms</TableCell>
                      <TableCell className="max-w-[320px] text-stone-600">
                        {Object.entries(usage.tasks).map(([task, count]) => `${task}:${count}`).join(', ')}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </section>
      </div>
    </Layout>
  );
}
