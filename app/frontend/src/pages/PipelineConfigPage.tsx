import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileSearch,
  FileText,
  Loader2,
  Package,
  RefreshCw,
  Scale,
  Scissors,
  Settings,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import { getLatestPipelineTrace, type PipelineTraceResponse, type PipelineTraceStage } from '@/lib/deepReviewApi';
import { useI18n } from '@/contexts/I18nContext';

export default function PipelineConfigPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

const stageIcons: Record<string, ReactNode> = {
  'stage-1': <FileSearch className="w-5 h-5" />,
  'stage-1b': <Settings className="w-5 h-5" />,
  'stage-2': <Scissors className="w-5 h-5" />,
  'stage-2b': <AlertTriangle className="w-5 h-5" />,
  'stage-3': <AlertTriangle className="w-5 h-5" />,
  'stage-4': <BookOpen className="w-5 h-5" />,
  'stage-5': <ShieldCheck className="w-5 h-5" />,
  'stage-6': <Scale className="w-5 h-5" />,
  'stage-7': <FileText className="w-5 h-5" />,
  'stage-8': <Package className="w-5 h-5" />,
};

const stageCopy: Record<string, { zh: string; en: string }> = {
  'stage-1': { zh: '识别文书基础信息、合同类型、审查立场和关键事实。', en: 'Identifies document basics, type, user role, and key facts.' },
  'stage-1b': { zh: '选择审查策略并补齐专业审查框架。', en: 'Selects the review strategy and professional framework.' },
  'stage-2': { zh: '切分条款结构，为逐条风险分析建立索引。', en: 'Maps clause structure and builds indexes for clause-level review.' },
  'stage-2b': { zh: '用确定性规则预扫描高风险和缺失信息。', en: 'Runs deterministic pre-scan rules for risks and missing facts.' },
  'stage-3': { zh: '识别风险、缺失条款和需要律师复核的问题。', en: 'Spots risks, missing clauses, and lawyer-review triggers.' },
  'stage-4': { zh: '检索法律依据与案例候选。', en: 'Retrieves legal authority and case candidates.' },
  'stage-5': { zh: '校验引用状态、效力层级和适用理由。', en: 'Validates citations, authority level, and relevance.' },
  'stage-6': { zh: '模拟资深律师复核并调整风险排序。', en: 'Performs senior-lawyer style review and risk calibration.' },
  'stage-7': { zh: '生成替代条款、谈判话术和证据建议。', en: 'Drafts replacement clauses, negotiation scripts, and evidence suggestions.' },
  'stage-8': { zh: '组装完整报告并写入报告表。', en: 'Assembles the final report and persists it.' },
};

function formatDuration(ms?: number) {
  if (!ms) return '0ms';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function statusConfig(status: string, lang: string) {
  if (status === 'completed') {
    return {
      icon: <CheckCircle2 className="w-4 h-4" />,
      className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      label: lang === 'zh' ? '完成' : 'Completed',
    };
  }
  if (status === 'error' || status === 'failed') {
    return {
      icon: <AlertCircle className="w-4 h-4" />,
      className: 'bg-red-50 text-red-800 border-red-200',
      label: lang === 'zh' ? '错误' : 'Error',
    };
  }
  return {
    icon: <Loader2 className="w-4 h-4 animate-spin" />,
    className: 'bg-blue-50 text-blue-800 border-blue-200',
    label: lang === 'zh' ? '运行中' : 'Running',
  };
}

function StageCard({ stage, index, lang }: { stage: PipelineTraceStage; index: number; lang: string }) {
  const cfg = statusConfig(stage.status, lang);
  const description = stageCopy[stage.stage_id]?.[lang === 'zh' ? 'zh' : 'en'];
  return (
    <Card className="surface-card overflow-hidden">
      <CardContent className="p-0">
        <div className="grid md:grid-cols-[72px_1fr]">
          <div className="flex md:flex-col items-center justify-between gap-3 border-b md:border-b-0 md:border-r border-stone-950/10 bg-[#f6f1e8] p-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-[14px] border border-stone-950/15 bg-white text-stone-900">
              {stageIcons[stage.stage_id] || <Settings className="w-5 h-5" />}
            </div>
            <span className="font-mono text-xs text-stone-500">#{index + 1}</span>
          </div>
          <div className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-stone-500">{stage.stage_id}</div>
                <h3 className="mt-1 text-lg font-black text-stone-950">{stage.stage_name}</h3>
              </div>
              <Badge variant="outline" className={`gap-1.5 ${cfg.className}`}>
                {cfg.icon}
                {cfg.label}
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">{description}</p>
            <div className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
              <div className="rounded-[14px] border border-stone-950/10 bg-white px-3 py-2">
                <span className="text-stone-500">{lang === 'zh' ? '模型' : 'Model'}: </span>
                <span className="font-semibold text-stone-900">{stage.model || '-'}</span>
              </div>
              <div className="rounded-[14px] border border-stone-950/10 bg-white px-3 py-2">
                <span className="text-stone-500">{lang === 'zh' ? '耗时' : 'Duration'}: </span>
                <span className="font-semibold text-stone-900">{formatDuration(stage.duration_ms)}</span>
              </div>
              <div className="rounded-[14px] border border-stone-950/10 bg-white px-3 py-2">
                <span className="text-stone-500">{lang === 'zh' ? '状态' : 'Status'}: </span>
                <span className="font-semibold text-stone-900">{stage.status}</span>
              </div>
            </div>
            {stage.error && (
              <div className="mt-4 rounded-[14px] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {stage.error}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Inner() {
  const { lang } = useI18n();
  const [data, setData] = useState<PipelineTraceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const copy = lang === 'zh'
    ? {
        eyebrow: 'AI Pipeline',
        title: '真实审查流水线',
        subtitle: '这里显示最近一次报告持久化的 pipeline trace，不再使用静态 mock。',
        refresh: '刷新',
        upload: '上传文书',
        progress: '流水线进度',
        completed: '阶段完成',
        totalDuration: '总耗时',
        empty: '还没有可展示的审查流水线记录。',
      }
    : {
        eyebrow: 'AI Pipeline',
        title: 'Live Review Pipeline',
        subtitle: 'This page shows the latest persisted pipeline trace instead of static mock data.',
        refresh: 'Refresh',
        upload: 'Upload',
        progress: 'Pipeline progress',
        completed: 'stages completed',
        totalDuration: 'Total duration',
        empty: 'No review pipeline trace is available yet.',
      };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getLatestPipelineTrace());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const stages = data?.trace ?? [];
  const completedCount = useMemo(() => stages.filter((stage) => stage.status === 'completed').length, [stages]);
  const progress = stages.length ? Math.round((completedCount / stages.length) * 100) : 0;

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-stone-950/15 pb-6">
          <div className="max-w-3xl">
            <div className="eyebrow mb-3">{copy.eyebrow}</div>
            <h1 className="text-4xl font-black leading-none text-stone-950 sm:text-6xl">{copy.title}</h1>
            <p className="mt-4 text-base leading-7 text-stone-600">{copy.subtitle}</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="soft-button" onClick={load} disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              {copy.refresh}
            </Button>
            <Button asChild className="quiet-button">
              <Link to="/upload">
                <Upload className="w-4 h-4" />
                {copy.upload}
              </Link>
            </Button>
          </div>
        </div>

        <Card className="surface-card mb-6">
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between gap-4">
              <span className="text-sm font-semibold text-stone-800">{copy.progress}</span>
              <span className="text-sm text-stone-500">
                {completedCount}/{stages.length} {copy.completed}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-stone-500">
              <span>{copy.totalDuration}: {formatDuration(data?.total_duration_ms)}</span>
              <span>{data?.report_id ? `Report #${data.report_id}` : '-'}</span>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-stone-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            {copy.refresh}
          </div>
        ) : stages.length === 0 ? (
          <Card className="surface-card">
            <CardContent className="flex flex-col items-center justify-center gap-4 py-14 text-center">
              <p className="text-sm text-stone-600">{copy.empty}</p>
              <Button asChild className="quiet-button">
                <Link to="/upload">
                  <Upload className="w-4 h-4" />
                  {copy.upload}
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {stages.map((stage, index) => (
              <div key={`${stage.stage_id}-${index}`}>
                <StageCard stage={stage} index={index} lang={lang} />
                {index < stages.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowRight className="h-4 w-4 rotate-90 text-stone-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
