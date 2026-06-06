import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, ClipboardCheck, Loader2, RefreshCw, Send, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  applyCaseWorkbenchStateEvent,
  getCaseWorkbenchState,
  listCaseWorkbenchStateEvents,
  type CaseWorkbenchApplyEventResponse,
  type CaseWorkbenchSectionState,
  type CaseWorkbenchStateEvent,
  type CaseWorkbenchStateEventRecord,
  type CaseWorkbenchStatePayload,
} from '@/lib/workbenchRuntimeApi';
import { cn } from '@/lib/utils';

type TaskStatus = 'open' | 'in_progress' | 'blocked' | 'completed';
type TaskPriority = 'low' | 'normal' | 'high';

export type CaseWorkbenchRuntimePanelProps = {
  caseId: number | string;
  caseRefHash?: string;
  workspaceId?: string;
  actorRefHash?: string;
  defaultTaskRefHash?: string;
  className?: string;
  onStateChanged?: (payload: CaseWorkbenchStatePayload, receipt: CaseWorkbenchApplyEventResponse) => void;
};

const STATE_SCHEMA_VERSION = 'case-workbench-state-v1';
const POLICY_VERSION = 'case-workbench-persistence-v1';
const RUNTIME_SOURCE = 'case_workbench_runtime_panel';

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

function safeToken(value: unknown, fallback = 'ref') {
  const token = String(value ?? '')
    .trim()
    .replace(/[^A-Za-z0-9:_-]/g, '_')
    .replace(/_+/g, '_')
    .slice(0, 96);
  return token || fallback;
}

function shortToken(value: unknown) {
  return safeToken(value, 'case').slice(0, 36);
}

function randomSuffix() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 10);
  }
  return Math.random().toString(36).slice(2, 12);
}

function formatDate(value?: string | null) {
  if (!value) return '鏆傛棤璁板綍';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN');
}

function summaryCount(section: CaseWorkbenchSectionState | undefined, key: string) {
  const value = section?.summary?.[key];
  return typeof value === 'number' ? value : 0;
}

function statusBadgeClass(status?: string) {
  if (status === 'ready' || status === 'pass' || status === 'completed') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
  if (status === 'blocked' || status === 'fail') {
    return 'border-red-200 bg-red-50 text-red-700';
  }
  if (status === 'empty') return 'border-slate-200 bg-slate-50 text-slate-600';
  return 'border-amber-200 bg-amber-50 text-amber-700';
}

function buildTaskEvent(params: {
  runtimeCaseId: string;
  workspaceId?: string;
  actorRefHash?: string;
  previousStateVersion: number;
  taskRefHash: string;
  status: TaskStatus;
  priority: TaskPriority;
  reviewRequired: boolean;
}): CaseWorkbenchStateEvent {
  const now = new Date().toISOString();
  const stateVersion = Math.max(1, params.previousStateVersion + 1);
  const safeCase = safeToken(params.runtimeCaseId, 'case_ref_hash');
  const safeTask = safeToken(params.taskRefHash, `task_hash_${shortToken(params.runtimeCaseId)}`);
  const nonce = randomSuffix();
  const activeCount = params.status === 'completed' ? 0 : 1;

  return {
    event_id: `cwp_event_ui_${safeCase}_${stateVersion}_${nonce}`,
    event_type: 'case_workbench_state_event',
    timestamp: now,
    idempotency_key: `cwp:v1:${safeCase}:tasks:${stateVersion}:ui_${nonce}`,
    case_ref_hash: params.runtimeCaseId,
    matter_ref_hash: params.workspaceId,
    actor_ref_hash: params.actorRefHash || 'actor_hash_current_user',
    section: 'tasks',
    operation: 'upsert_snapshot',
    state_version: stateVersion,
    previous_state_version: params.previousStateVersion,
    schema_version: STATE_SCHEMA_VERSION,
    source_component: RUNTIME_SOURCE,
    payload_kind: 'metadata_snapshot',
    item_count: 1,
    changed_item_refs: [safeTask],
    changed_field_names: [
      'task_ref_hash',
      'task_type',
      'status',
      'priority',
      'owner_role',
      'review_required',
      'updated_at',
    ],
    state_delta: {
      schema_version: STATE_SCHEMA_VERSION,
      section: 'tasks',
      state_version: stateVersion,
      item_count: 1,
      updated_at: now,
      updated_by_role: 'lawyer',
      source_component: RUNTIME_SOURCE,
      policy_version: POLICY_VERSION,
      summary: {
        task_count: 1,
        active_count: activeCount,
        completed_count: params.status === 'completed' ? 1 : 0,
        review_required_count: params.reviewRequired ? 1 : 0,
      },
      task_states: [
        {
          task_ref_hash: safeTask,
          task_type: 'lawyer_review',
          status: params.status,
          priority: params.priority,
          owner_role: 'lawyer',
          due_date_status: 'none',
          escalation_status: params.status === 'blocked' ? 'watch' : 'none',
          blocker_codes: params.status === 'blocked' ? ['manual_review_blocked'] : [],
          dependency_refs: [],
          review_required: params.reviewRequired,
          updated_at: now,
        },
      ],
    },
    retention_bucket: 'active_case_workbench',
    policy_version: POLICY_VERSION,
    review_required: params.reviewRequired,
    validation_status: 'pass',
    created_at: now,
  };
}

function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[12px] border border-dashed border-stone-950/20 bg-[#efebe1]/70 p-5 text-center text-sm text-stone-500">
      {children}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="text-2xl font-black text-stone-950">{value}</div>
      <div className="mt-1 text-xs text-stone-500">{label}</div>
    </div>
  );
}

export function CaseWorkbenchRuntimePanel({
  caseId,
  caseRefHash,
  workspaceId,
  actorRefHash,
  defaultTaskRefHash,
  className,
  onStateChanged,
}: CaseWorkbenchRuntimePanelProps) {
  const runtimeCaseId = useMemo(() => caseRefHash?.trim() || String(caseId), [caseId, caseRefHash]);
  const [state, setState] = useState<CaseWorkbenchStatePayload | null>(null);
  const [events, setEvents] = useState<CaseWorkbenchStateEventRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<TaskStatus>('in_progress');
  const [priority, setPriority] = useState<TaskPriority>('normal');
  const [reviewRequired, setReviewRequired] = useState(true);
  const [taskRefHash, setTaskRefHash] = useState(defaultTaskRefHash || '');

  const taskSection = state?.sections?.tasks;
  const riskRefreshPlan = state?.risk_refresh_plan;
  const riskRefreshRows = riskRefreshPlan?.section_refresh_rows?.filter((row) => row.refresh_required) ?? [];
  const riskTriggerRows =
    riskRefreshPlan?.event_trigger_rows?.filter(
      (row) => row.requires_risk_state_refresh || row.requires_evidence_graph_refresh,
    ) ?? [];
  const latestEvents = useMemo(() => [...events].reverse().slice(0, 5), [events]);
  const resolvedTaskRefHash = taskRefHash.trim() || `task_hash_ui_${shortToken(runtimeCaseId)}`;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextState, nextEvents] = await Promise.all([
        getCaseWorkbenchState(runtimeCaseId, { workspace_id: workspaceId }),
        listCaseWorkbenchStateEvents(runtimeCaseId, { section: 'tasks', limit: 5 }),
      ]);
      setState(nextState);
      setEvents(nextEvents.events || []);
    } catch (err) {
      setError(errorMessage(err, 'Failed to load workbench runtime state.'));
    } finally {
      setLoading(false);
    }
  }, [runtimeCaseId, workspaceId]);

  useEffect(() => {
    load();
  }, [load]);

  async function submitTaskEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const workbenchEvent = buildTaskEvent({
        runtimeCaseId,
        workspaceId,
        actorRefHash,
        previousStateVersion: Number(taskSection?.state_version || 0),
        taskRefHash: resolvedTaskRefHash,
        status,
        priority,
        reviewRequired,
      });
      const receipt = await applyCaseWorkbenchStateEvent(runtimeCaseId, workbenchEvent);
      if (receipt.payload) setState(receipt.payload);
      const nextEvents = await listCaseWorkbenchStateEvents(runtimeCaseId, { section: 'tasks', limit: 5 });
      setEvents(nextEvents.events || []);
      if (receipt.payload) onStateChanged?.(receipt.payload, receipt);
      toast.success(receipt.status === 'idempotent_replay' ? 'Runtime event already applied' : 'Runtime state updated');
    } catch (err) {
      const message = errorMessage(err, 'Failed to submit runtime state event.');
      setError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className={cn('surface-card', className)}>
      <CardHeader className="flex-row items-start justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <ClipboardCheck className="h-4 w-4" />
            Workbench runtime state
          </CardTitle>
          <p className="mt-1 text-xs text-slate-500">
            Syncs section state, counts, and reference hashes only. It does not store case narrative or party names.
          </p>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={load} disabled={loading || submitting}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert className="border-red-200 bg-red-50 text-red-950">
            <AlertTriangle className="h-4 w-4 text-red-700" />
            <AlertTitle>Action incomplete</AlertTitle>
            <AlertDescription className="text-sm text-red-900">{error}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading workbench runtime state
          </div>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-4">
              <Metric label="Overall status" value={state?.status || 'empty'} />
              <Metric label="Populated sections" value={`${state?.populated_section_count || 0}/${state?.section_count || 0}`} />
              <Metric label="Task version" value={taskSection?.state_version || 0} />
              <Metric label="Active tasks" value={summaryCount(taskSection, 'active_count')} />
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={statusBadgeClass(taskSection?.status)}>
                  tasks: {taskSection?.status || 'empty'}
                </Badge>
                <Badge variant="outline" className={statusBadgeClass(taskSection?.validation_status || undefined)}>
                  validation: {taskSection?.validation_status || 'pending'}
                </Badge>
                <span className="text-xs text-slate-500">Updated: {formatDate(taskSection?.updated_at)}</span>
              </div>
              {taskSection?.state_version ? (
                <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                  <span>task_count: {summaryCount(taskSection, 'task_count')}</span>
                  <span>completed_count: {summaryCount(taskSection, 'completed_count')}</span>
                  <span>review_required_count: {summaryCount(taskSection, 'review_required_count')}</span>
                </div>
              ) : (
                <EmptyState>No tasks section state yet. Submit a lightweight review task event first.</EmptyState>
              )}
            </div>

            {riskRefreshPlan && (
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
                    <AlertTriangle className="h-4 w-4 text-amber-700" />
                    Risk refresh plan
                  </div>
                  <Badge variant="outline" className={statusBadgeClass(riskRefreshPlan.status)}>
                    {riskRefreshPlan.status}
                  </Badge>
                </div>
                <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-4">
                  <span>refresh_required: {riskRefreshPlan.summary.refresh_required_count}</span>
                  <span>blocking_sections: {riskRefreshPlan.summary.blocking_section_count}</span>
                  <span>risk_events: {riskRefreshPlan.summary.risk_affecting_event_count}</span>
                  <span>graph_events: {riskRefreshPlan.summary.evidence_graph_affecting_event_count}</span>
                </div>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Sections requiring refresh
                    </div>
                    {riskRefreshRows.length ? (
                      <div className="mt-2 space-y-2">
                        {riskRefreshRows.slice(0, 4).map((row) => (
                          <div key={row.section} className="rounded-md bg-white p-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="secondary">{row.section}</Badge>
                              <span className="text-xs text-slate-500">v{row.state_version}</span>
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              targets: {row.refresh_targets.join(', ') || 'watch'}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              reasons: {row.reason_codes.slice(0, 3).join(', ') || 'none'}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState>No section refresh required.</EmptyState>
                    )}
                  </div>
                  <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Event delta triggers
                    </div>
                    {riskTriggerRows.length ? (
                      <div className="mt-2 space-y-2">
                        {riskTriggerRows.slice(0, 4).map((row) => (
                          <div key={row.event_id} className="rounded-md bg-white p-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="secondary">{row.section}</Badge>
                              <span className="font-mono text-xs text-slate-500">{row.event_id}</span>
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              fields: {row.changed_field_names.slice(0, 4).join(', ') || 'metadata'}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              raw_event_payload_returned: {String(row.raw_event_payload_returned)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState>No risk-affecting event deltas.</EmptyState>
                    )}
                  </div>
                </div>
                <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                  <span>raw_text_returned: {String(riskRefreshPlan.summary.raw_text_returned)}</span>
                  <span>event_payloads_returned: {String(riskRefreshPlan.summary.event_payloads_returned)}</span>
                  <span>risk_state_written: {String(riskRefreshPlan.summary.risk_state_written)}</span>
                </div>
              </div>
            )}
          </>
        )}

        <form onSubmit={submitTaskEvent} className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
            <ShieldCheck className="h-4 w-4 text-emerald-700" />
            Submit lightweight task state event
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="task-ref-hash">Task reference hash</Label>
              <Input
                id="task-ref-hash"
                value={taskRefHash}
                onChange={(event) => setTaskRefHash(event.target.value)}
                placeholder={`task_hash_ui_${shortToken(runtimeCaseId)}`}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select value={status} onValueChange={(value) => setStatus(value as TaskStatus)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">open</SelectItem>
                  <SelectItem value="in_progress">in_progress</SelectItem>
                  <SelectItem value="blocked">blocked</SelectItem>
                  <SelectItem value="completed">completed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Priority</Label>
              <Select value={priority} onValueChange={(value) => setPriority(value as TaskPriority)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">low</SelectItem>
                  <SelectItem value="normal">normal</SelectItem>
                  <SelectItem value="high">high</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <Checkbox checked={reviewRequired} onCheckedChange={(checked) => setReviewRequired(checked === true)} />
              Requires lawyer review
            </label>
            <Button type="submit" size="sm" disabled={loading || submitting}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {submitting ? 'Submitting' : 'Submit state event'}
            </Button>
          </div>
        </form>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
            <CheckCircle2 className="h-4 w-4 text-emerald-700" />
            Recent events
          </div>
          {latestEvents.length ? (
            <div className="space-y-2">
              {latestEvents.map((item) => (
                <div key={item.event_id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">{item.section}</Badge>
                    <span className="font-medium text-slate-800">{item.operation}</span>
                    <Badge variant="outline">v{item.state_version}</Badge>
                    <Badge variant="outline" className={statusBadgeClass(item.validation_status || undefined)}>
                      {item.validation_status || 'pending'}
                    </Badge>
                  </div>
                  <div className="mt-1 truncate font-mono text-xs text-slate-500">{item.event_id}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatDate(item.created_at)}</div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState>No tasks section events.</EmptyState>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default CaseWorkbenchRuntimePanel;
