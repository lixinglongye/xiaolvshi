import { useMemo, useState, type ReactNode } from 'react';
import { AlertTriangle, BookOpen, Database, Gauge, Loader2, RefreshCw, Search, ShieldCheck } from 'lucide-react';
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

export type LegalRagResearchPanelProps = {
  caseId?: number | string;
  caseRefHash?: string;
  defaultJurisdiction?: string;
  defaultDocumentType?: string;
  defaultUseCase?: string;
  defaultSourceIds?: string[];
  className?: string;
  onEvaluated?: (result: {
    plan: LegalRagRetrievalPlan;
    evaluation: LegalRagEvaluation;
    unsupportedClaimCount: number;
    piiFindingCount: number;
  }) => void;
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sourceIds = useMemo(() => parseSourceIds(sourceIdsText), [sourceIdsText]);
  const caseContext = caseRefHash || (caseId !== undefined ? String(caseId) : '');

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
      setBundle(nextBundle);
      onEvaluated?.({
        plan: nextBundle.plan,
        evaluation: nextBundle.evaluation,
        unsupportedClaimCount: nextBundle.unsupportedClaimCount,
        piiFindingCount: nextBundle.piiFindingCount,
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

  const plan = bundle?.plan;
  const evaluation = bundle?.evaluation;
  const coverage = plan?.coverage_counts;

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

        {!loading && !bundle && (
          <EmptyState>暂无评估结果。先提交一次 metadata-only 检索/评估请求。</EmptyState>
        )}

        {bundle && (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              <Metric label="readiness" value={plan?.status || 'unknown'} />
              <Metric label="selected_sources" value={coverage?.selected_source_count || 0} />
              <Metric label="unsupported_claims" value={bundle.unsupportedClaimCount} />
              <Metric label="pii_findings" value={bundle.piiFindingCount} />
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={statusClass(plan?.status, plan?.blocked)}>
                  plan: {plan?.status}
                </Badge>
                <Badge variant="outline" className={statusClass(evaluation?.status)}>
                  evaluation: {evaluation?.status || 'pending'}
                </Badge>
                <Badge variant="outline">
                  score: {formatScore(evaluation?.score)}
                </Badge>
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                <span>blocked_sources: {coverage?.blocked_source_count || 0}</span>
                <span>stale_sources: {coverage?.stale_source_count || 0}</span>
                <span>missing_requested: {coverage?.missing_requested_source_count || 0}</span>
              </div>
              {!!plan?.reason_codes?.length && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {plan.reason_codes.map((code) => (
                    <Badge key={code} variant="outline" className={statusClass(plan.status, plan.blocked)}>
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
              {evaluation?.metric_scores && Object.keys(evaluation.metric_scores).length ? (
                <div className="grid gap-2 md:grid-cols-3">
                  {Object.entries(evaluation.metric_scores).map(([key, value]) => (
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
                本次请求未提交 unsupported claim 明文或 PII 明细，仅提交计数和来源 ID。返回结果也只渲染安全 metadata 字段。
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
