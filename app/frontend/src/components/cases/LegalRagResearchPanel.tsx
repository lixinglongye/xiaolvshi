import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AlertTriangle, BookOpen, Copy, Database, Gauge, Loader2, RefreshCw, Search, ShieldCheck, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  buildLegalRagRetrievalPlan,
  evaluateLegalRag,
  type LegalRagEvaluation,
  type LegalRagEvaluationResponse,
  type LegalRagRetrievalPlan,
  type LegalRagRetrievalPlanRequest,
  type LegalRagSourceMetadata,
} from '@/lib/legalRagApi';
import { cn } from '@/lib/utils';

export type LegalRagResearchSafeMetadata = {
  schema_version: 'legal-rag-research-safe-metadata-v1';
  selected_source_ids: string[];
  selected_source_count: number;
  plan_status: string;
  evaluation_status: string;
  blocked: boolean;
  freshness_statuses: string[];
  coverage_counts: Record<string, number>;
  reason_codes: string[];
  metric_scores: Record<string, number>;
  unsupported_claim_count: number;
  pii_finding_count: number;
  evaluated_at: string;
  privacy_boundary: {
    raw_legal_text_included: false;
    user_claims_included: false;
    pii_included: false;
  };
};

export type LegalRagResearchEvaluationResult = {
  plan: LegalRagRetrievalPlan;
  evaluation: LegalRagEvaluation;
  unsupportedClaimCount: number;
  piiFindingCount: number;
  selectedSourceIds: string[];
  safeMetadata: LegalRagResearchSafeMetadata;
};

export type LegalRagResearchPanelProps = {
  caseId?: number | string;
  caseRefHash?: string;
  defaultJurisdiction?: string;
  defaultDocumentType?: string;
  defaultUseCase?: string;
  defaultSourceIds?: string[];
  className?: string;
  onEvaluated?: (result: LegalRagResearchEvaluationResult) => void;
};

type EvaluationBundle = {
  plan: LegalRagRetrievalPlan;
  evaluation: LegalRagEvaluation;
  unsupportedClaimCount: number;
  piiFindingCount: number;
  evaluationInput: Record<string, unknown>;
};

type LegalRagEvaluationBundleResponse = {
  retrieval_plan: Pick<
    LegalRagRetrievalPlan,
    'status' | 'blocked' | 'reason_codes' | 'selected_source_ids' | 'coverage_counts'
  >;
  evaluation_input: Record<string, unknown>;
  evaluation: LegalRagEvaluation;
};

type ResearchResultOrigin = 'fresh' | 'cache';

type CachedLegalRagSummary = {
  selected_source_ids: string[];
  status: {
    plan: string;
    evaluation: string;
    blocked: boolean;
    freshness_statuses: string[];
  };
  coverage_counts: Record<string, number>;
  metric_scores: Record<string, number>;
  reason_codes: string[];
  timestamp: string;
};

const LEGAL_RAG_CACHE_PREFIX = 'xiaolvshi:legal-rag:metadata-summary:v1:';

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function parseSourceIds(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function statusClass(status?: string, blocked?: boolean) {
  if (blocked || status === 'blocked' || status === 'fail') return 'border-red-200 bg-red-50 text-red-700';
  if (status === 'ready' || status === 'pass') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (status === 'ready_with_warnings' || status === 'warn') return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-slate-200 bg-slate-50 text-slate-600';
}

function formatScore(score?: number) {
  if (typeof score !== 'number' || Number.isNaN(score)) return '暂无';
  return score <= 1 ? `${Math.round(score * 100)}%` : String(score);
}

function hasEvaluationBundle(value: LegalRagEvaluationResponse): value is LegalRagEvaluationBundleResponse {
  return Boolean(value && typeof value === 'object' && 'evaluation' in value);
}

function countFromInput(input: Record<string, unknown>, key: string) {
  const value = input[key];
  return typeof value === 'number' ? value : 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function stringArray(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function numberRecord(value: unknown) {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, number] => (
      typeof entry[1] === 'number' && Number.isFinite(entry[1])
    )),
  );
}

function uniqueStrings(values: string[]) {
  return [...new Set(values.filter(Boolean))];
}

function cacheKeyForCase(caseContext: string) {
  return caseContext ? `${LEGAL_RAG_CACHE_PREFIX}${caseContext}` : null;
}

function readCachedSummary(cacheKey: string | null): CachedLegalRagSummary | null {
  if (!cacheKey || typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(cacheKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!isRecord(parsed)) return null;
    const status = isRecord(parsed.status) ? parsed.status : {};
    const timestamp = typeof parsed.timestamp === 'string' ? parsed.timestamp : '';
    if (!timestamp) return null;
    return {
      selected_source_ids: stringArray(parsed.selected_source_ids),
      status: {
        plan: typeof status.plan === 'string' ? status.plan : 'unknown',
        evaluation: typeof status.evaluation === 'string' ? status.evaluation : 'unknown',
        blocked: typeof status.blocked === 'boolean' ? status.blocked : false,
        freshness_statuses: stringArray(status.freshness_statuses),
      },
      coverage_counts: numberRecord(parsed.coverage_counts),
      metric_scores: numberRecord(parsed.metric_scores),
      reason_codes: stringArray(parsed.reason_codes),
      timestamp,
    };
  } catch {
    return null;
  }
}

function writeCachedSummary(cacheKey: string | null, summary: CachedLegalRagSummary) {
  if (!cacheKey || typeof window === 'undefined') return;
  window.localStorage.setItem(cacheKey, JSON.stringify(summary));
}

function clearCachedSummary(cacheKey: string | null) {
  if (!cacheKey || typeof window === 'undefined') return;
  window.localStorage.removeItem(cacheKey);
}

function buildCachedSummary(plan: LegalRagRetrievalPlan, evaluation: LegalRagEvaluation): CachedLegalRagSummary {
  return {
    selected_source_ids: [...(plan.selected_source_ids || [])],
    status: {
      plan: plan.status || 'unknown',
      evaluation: evaluation.status || 'unknown',
      blocked: Boolean(plan.blocked),
      freshness_statuses: uniqueStrings((plan.selected_sources || []).map((source) => source.freshness_status)),
    },
    coverage_counts: { ...(plan.coverage_counts || {}) },
    metric_scores: { ...(evaluation.metric_scores || {}) },
    reason_codes: [...(plan.reason_codes || [])],
    timestamp: new Date().toISOString(),
  };
}

function buildSafeMetadata(
  summary: CachedLegalRagSummary,
  unsupportedClaimCount: number,
  piiFindingCount: number,
): LegalRagResearchSafeMetadata {
  return {
    schema_version: 'legal-rag-research-safe-metadata-v1',
    selected_source_ids: [...summary.selected_source_ids],
    selected_source_count: summary.selected_source_ids.length,
    plan_status: summary.status.plan,
    evaluation_status: summary.status.evaluation,
    blocked: summary.status.blocked,
    freshness_statuses: [...summary.status.freshness_statuses],
    coverage_counts: { ...summary.coverage_counts },
    reason_codes: [...summary.reason_codes],
    metric_scores: { ...summary.metric_scores },
    unsupported_claim_count: unsupportedClaimCount,
    pii_finding_count: piiFindingCount,
    evaluated_at: summary.timestamp,
    privacy_boundary: {
      raw_legal_text_included: false,
      user_claims_included: false,
      pii_included: false,
    },
  };
}

function coverageValue(summary: CachedLegalRagSummary | null, key: string) {
  return summary?.coverage_counts?.[key] || 0;
}

function selectedSourceCount(summary: CachedLegalRagSummary | null) {
  return coverageValue(summary, 'selected_source_count') || summary?.selected_source_ids.length || 0;
}

function formatSummaryTimestamp(value?: string) {
  if (!value) return 'unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatCoverageForCopy(coverage: Record<string, number>) {
  const keys = [
    'candidate_source_count',
    'selected_source_count',
    'requested_source_count',
    'blocked_source_count',
    'stale_source_count',
    'missing_requested_source_count',
    'unusable_requested_source_count',
  ];
  const pairs = keys
    .filter((key) => typeof coverage[key] === 'number')
    .map((key) => `${key}=${coverage[key]}`);
  return pairs.length ? pairs.join('; ') : 'none';
}

function formatMetricScoresForCopy(metricScores: Record<string, number>) {
  const pairs = Object.entries(metricScores).map(([key, value]) => `${key}=${formatScore(value)}`);
  return pairs.length ? pairs.join('; ') : 'none';
}

function buildCopyContext(summary: CachedLegalRagSummary, origin: ResearchResultOrigin | null, caseContext: string) {
  return [
    'Legal RAG metadata context',
    caseContext ? `case_ref: ${caseContext}` : null,
    `origin: ${origin === 'cache' ? 'cache' : 'current_run'}`,
    `timestamp: ${summary.timestamp}`,
    `selected_source_ids: ${summary.selected_source_ids.length ? summary.selected_source_ids.join(', ') : 'none'}`,
    `status: plan=${summary.status.plan}; evaluation=${summary.status.evaluation}; blocked=${summary.status.blocked}`,
    `freshness_statuses: ${summary.status.freshness_statuses.length ? summary.status.freshness_statuses.join(', ') : 'none'}`,
    `coverage: ${formatCoverageForCopy(summary.coverage_counts)}`,
    `reason_codes: ${summary.reason_codes.length ? summary.reason_codes.join(', ') : 'none'}`,
    `metric_scores: ${formatMetricScoresForCopy(summary.metric_scores)}`,
    'raw_text: excluded',
    'pii: excluded',
  ].filter(Boolean).join('\n');
}

async function copyText(text: string) {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  if (typeof document === 'undefined') throw new Error('Clipboard is unavailable');
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', 'true');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  textarea.remove();
}

function buildRequest(params: {
  jurisdiction: string;
  documentType: string;
  useCase: string;
  effectiveOn: string;
  sourceIds: string[];
}): LegalRagRetrievalPlanRequest {
  const request: LegalRagRetrievalPlanRequest = {
    jurisdiction: params.jurisdiction || undefined,
    document_type: params.documentType || undefined,
    effective_on: params.effectiveOn || undefined,
    use_case: params.useCase || undefined,
  };
  if (params.sourceIds.length) request.source_ids = params.sourceIds;
  return request;
}

function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[12px] border border-dashed border-stone-950/20 bg-[#efebe1]/70 p-5 text-center text-sm text-stone-500">
      {children}
    </div>
  );
}

function SourceMetadataCard({ source }: { source: LegalRagSourceMetadata }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{source.source_type}</Badge>
        <Badge variant="outline">{source.jurisdiction}</Badge>
        <Badge variant="outline" className={statusClass(source.freshness_status)}>
          {source.freshness_status}
        </Badge>
      </div>
      <h4 className="mt-2 font-medium text-slate-900">{source.title || source.source_title || source.source_id}</h4>
      <div className="mt-2 grid gap-1 text-xs text-slate-600 sm:grid-cols-2">
        <span>source_id: {source.source_id}</span>
        <span>effective: {source.effective_date}</span>
        <span>verified: {source.last_verified_at}</span>
        <span>authority: {source.authority_level || 'unspecified'}</span>
      </div>
      <p className="mt-2 text-xs text-slate-500">{source.citation}</p>
      {source.retrieval_locator && (
        <p className="mt-1 truncate font-mono text-xs text-slate-500">{source.retrieval_locator}</p>
      )}
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

export function LegalRagResearchPanel({
  caseId,
  caseRefHash,
  defaultJurisdiction = 'CN-National',
  defaultDocumentType = 'statute',
  defaultUseCase = 'contract_review',
  defaultSourceIds = [],
  className,
  onEvaluated,
}: LegalRagResearchPanelProps) {
  const [jurisdiction, setJurisdiction] = useState(defaultJurisdiction);
  const [documentType, setDocumentType] = useState(defaultDocumentType);
  const [useCase, setUseCase] = useState(defaultUseCase);
  const [effectiveOn, setEffectiveOn] = useState(today());
  const [sourceIdsText, setSourceIdsText] = useState(defaultSourceIds.join(', '));
  const [bundle, setBundle] = useState<EvaluationBundle | null>(null);
  const [freshSummary, setFreshSummary] = useState<CachedLegalRagSummary | null>(null);
  const [cachedSummary, setCachedSummary] = useState<CachedLegalRagSummary | null>(null);
  const [resultOrigin, setResultOrigin] = useState<ResearchResultOrigin | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sourceIds = useMemo(() => parseSourceIds(sourceIdsText), [sourceIdsText]);
  const caseContext = caseRefHash || (caseId !== undefined ? String(caseId) : '');
  const cacheKey = useMemo(() => cacheKeyForCase(caseContext), [caseContext]);

  useEffect(() => {
    const restoredSummary = readCachedSummary(cacheKey);
    setBundle(null);
    setFreshSummary(null);
    setCachedSummary(restoredSummary);
    setResultOrigin(restoredSummary ? 'cache' : null);
  }, [cacheKey]);

  async function runMetadataOnlyResearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const filters = buildRequest({ jurisdiction, documentType, useCase, effectiveOn, sourceIds });
      const plan = await buildLegalRagRetrievalPlan(filters);
      const selectedSourceIds = plan.selected_source_ids || [];
      const response = await evaluateLegalRag({
        filters,
        retrieved_source_ids: selectedSourceIds,
        answer_citation_source_ids: selectedSourceIds,
        verified_claim_count: selectedSourceIds.length,
        total_claim_count: selectedSourceIds.length,
        unsupported_claims: [],
        pii_findings: [],
      });

      const evaluation = hasEvaluationBundle(response) ? response.evaluation : response;
      const evaluationInput = hasEvaluationBundle(response) ? response.evaluation_input : {};
      const nextBundle = {
        plan,
        evaluation,
        unsupportedClaimCount: countFromInput(evaluationInput, 'unsupported_claim_count'),
        piiFindingCount: countFromInput(evaluationInput, 'pii_finding_count'),
        evaluationInput,
      };
      const nextSummary = buildCachedSummary(plan, evaluation);
      writeCachedSummary(cacheKey, nextSummary);
      setBundle(nextBundle);
      setFreshSummary(nextSummary);
      setCachedSummary(nextSummary);
      setResultOrigin('fresh');
      const safeMetadata = buildSafeMetadata(
        nextSummary,
        nextBundle.unsupportedClaimCount,
        nextBundle.piiFindingCount,
      );
      onEvaluated?.({
        plan: nextBundle.plan,
        evaluation: nextBundle.evaluation,
        unsupportedClaimCount: nextBundle.unsupportedClaimCount,
        piiFindingCount: nextBundle.piiFindingCount,
        selectedSourceIds: [...nextSummary.selected_source_ids],
        safeMetadata,
      });
      toast.success(plan.blocked ? '检索计划已返回阻塞原因' : '法律 RAG 元数据评估完成');
    } catch (err) {
      const message = errorMessage(err, '法律 RAG 元数据评估失败');
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  async function copyResearchContext() {
    const summary = resultOrigin === 'fresh' ? freshSummary : cachedSummary;
    if (!summary) return;
    try {
      await copyText(buildCopyContext(summary, resultOrigin, caseContext));
      toast.success('Research context copied');
    } catch (err) {
      const message = errorMessage(err, 'Copy failed');
      setError(message);
      toast.error(message);
    }
  }

  function clearCaseCache() {
    clearCachedSummary(cacheKey);
    setCachedSummary(null);
    if (resultOrigin === 'cache') {
      setResultOrigin(null);
    }
    toast.success('Legal RAG cache cleared');
  }

  const plan = bundle?.plan;
  const evaluation = bundle?.evaluation;
  const activeSummary = resultOrigin === 'fresh' ? freshSummary : cachedSummary;
  const activeCoverage = activeSummary?.coverage_counts;
  const activeMetricScores = activeSummary?.metric_scores || {};
  const activeReasonCodes = activeSummary?.reason_codes || [];
  const activeOriginLabel = resultOrigin === 'cache' ? 'cache' : 'current run';

  return (
    <Card className={cn('surface-card', className)}>
      <CardHeader className="flex-row items-start justify-between gap-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <BookOpen className="h-4 w-4" />
            法律 RAG 研究
          </CardTitle>
          <p className="mt-1 text-xs text-slate-500">
            只提交筛选条件、来源 ID 和评估计数；结果区不展示法规全文、用户主张原文或 PII。
          </p>
        </div>
        {caseContext && (
          <Badge variant="outline" className="max-w-[180px] truncate font-mono">
            {caseContext}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert className="border-red-200 bg-red-50 text-red-950">
            <AlertTriangle className="h-4 w-4 text-red-700" />
            <AlertTitle>研究请求未完成</AlertTitle>
            <AlertDescription className="text-sm text-red-900">{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={runMetadataOnlyResearch} className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="rag-jurisdiction">辖区</Label>
              <Input id="rag-jurisdiction" value={jurisdiction} onChange={(event) => setJurisdiction(event.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>来源类型</Label>
              <Select value={documentType} onValueChange={setDocumentType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="statute">statute</SelectItem>
                  <SelectItem value="judicial_interpretation">judicial_interpretation</SelectItem>
                  <SelectItem value="template">template</SelectItem>
                  <SelectItem value="case">case</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rag-use-case">用途</Label>
              <Input id="rag-use-case" value={useCase} onChange={(event) => setUseCase(event.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rag-effective-on">生效日</Label>
              <Input id="rag-effective-on" type="date" value={effectiveOn} onChange={(event) => setEffectiveOn(event.target.value)} />
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-[1fr_auto]">
            <div className="space-y-1.5">
              <Label htmlFor="rag-source-ids">指定来源 ID</Label>
              <Input
                id="rag-source-ids"
                value={sourceIdsText}
                onChange={(event) => setSourceIdsText(event.target.value)}
                placeholder="可选，多个 source_id 用英文逗号分隔"
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" disabled={loading} className="w-full md:w-auto">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                {loading ? '评估中' : '运行元数据评估'}
              </Button>
            </div>
          </div>
        </form>

        {loading && (
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在构建检索计划并执行 metadata-only 评估
          </div>
        )}

        {!loading && !activeSummary && (
          <EmptyState>暂无评估结果。先提交一次 metadata-only 检索/评估请求。</EmptyState>
        )}

        {activeSummary && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
                <Badge variant="outline" className={resultOrigin === 'cache' ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}>
                  origin: {activeOriginLabel}
                </Badge>
                <span>saved_at: {formatSummaryTimestamp(activeSummary.timestamp)}</span>
                <Badge variant="outline" className={cachedSummary ? 'border-slate-200 bg-slate-50 text-slate-600' : 'border-amber-200 bg-amber-50 text-amber-700'}>
                  {cachedSummary ? 'cache available' : 'cache cleared'}
                </Badge>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" variant="outline" onClick={copyResearchContext}>
                  <Copy className="h-4 w-4" />
                  Copy context
                </Button>
                {cachedSummary && (
                  <Button type="button" size="sm" variant="outline" onClick={clearCaseCache}>
                    <Trash2 className="h-4 w-4" />
                    Clear cache
                  </Button>
                )}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-4">
              <Metric label="readiness" value={activeSummary.status.plan || 'unknown'} />
              <Metric label="selected_sources" value={selectedSourceCount(activeSummary)} />
              <Metric label="stale_sources" value={coverageValue(activeSummary, 'stale_source_count')} />
              <Metric label="missing_requested" value={coverageValue(activeSummary, 'missing_requested_source_count')} />
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={statusClass(activeSummary.status.plan, activeSummary.status.blocked)}>
                  plan: {activeSummary.status.plan}
                </Badge>
                <Badge variant="outline" className={statusClass(activeSummary.status.evaluation)}>
                  evaluation: {activeSummary.status.evaluation || 'pending'}
                </Badge>
                <Badge variant="outline">
                  score: {evaluation ? formatScore(evaluation.score) : 'not cached'}
                </Badge>
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                <span>blocked_sources: {activeCoverage?.blocked_source_count || 0}</span>
                <span>stale_sources: {activeCoverage?.stale_source_count || 0}</span>
                <span>missing_requested: {activeCoverage?.missing_requested_source_count || 0}</span>
              </div>
              {!!activeReasonCodes.length && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {activeReasonCodes.map((code) => (
                    <Badge key={code} variant="outline" className={statusClass(activeSummary.status.plan, activeSummary.status.blocked)}>
                      {code}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-800">
                <Gauge className="h-4 w-4" />
                指标
              </div>
              {Object.keys(activeMetricScores).length ? (
                <div className="grid gap-2 md:grid-cols-3">
                  {Object.entries(activeMetricScores).map(([key, value]) => (
                    <div key={key} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                      <div className="font-medium text-slate-800">{key}</div>
                      <div className="mt-1 text-xs text-slate-500">{formatScore(value)}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState>暂无指标明细。</EmptyState>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
                <Database className="h-4 w-4" />
                来源 metadata
              </div>
              {plan?.selected_sources?.length ? (
                <div className="grid gap-3 lg:grid-cols-2">
                  {plan.selected_sources.map((source) => (
                    <SourceMetadataCard key={`${source.source_id}-${source.index_entry_id}`} source={source} />
                  ))}
                </div>
              ) : activeSummary.selected_source_ids.length ? (
                <div className="grid gap-2 md:grid-cols-2">
                  {activeSummary.selected_source_ids.map((sourceId) => (
                    <div key={sourceId} className="rounded-lg border border-slate-200 bg-white p-3 font-mono text-xs text-slate-700">
                      {sourceId}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState>当前筛选条件没有可用来源 metadata。</EmptyState>
              )}
            </div>

            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
              <div className="flex items-center gap-2 font-medium">
                <ShieldCheck className="h-4 w-4" />
                安全摘要
              </div>
              <p className="mt-1 text-xs">
                本次请求和缓存只使用安全 metadata 摘要；复制内容不包含法规全文、用户主张原文或 PII 明细。
              </p>
            </div>
          </div>
        )}

        {bundle?.evaluation?.recommended_actions?.length ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-amber-900">
              <RefreshCw className="h-4 w-4" />
              建议动作
            </div>
            <ul className="list-inside list-disc space-y-1 text-sm text-amber-900">
              {bundle.evaluation.recommended_actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default LegalRagResearchPanel;
