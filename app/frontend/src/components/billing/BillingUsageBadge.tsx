import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Clock, Gauge } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { getBillingUsageSummary, type BillingUsageSummary } from '@/lib/billingUsageApi';
import { cn } from '@/lib/utils';

interface BillingUsageBadgeProps {
  className?: string;
  onNavigate?: () => void;
}

function formatPlan(summary: BillingUsageSummary | undefined) {
  const raw = summary?.effective_plan_type || summary?.plan_type || summary?.subscription_status || 'plan';
  return raw
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (value) => value.toUpperCase());
}

function getQuota(summary: BillingUsageSummary) {
  const limit = summary.report_quota_monthly ?? summary.limit ?? null;
  const used = summary.reports_used_month ?? summary.persisted_usage ?? summary.usage_snapshot?.used ?? 0;
  const remaining = summary.reports_remaining ?? summary.remaining ?? summary.usage_snapshot?.remaining ?? null;

  if (typeof limit === 'number') {
    const safeRemaining = typeof remaining === 'number' ? remaining : Math.max(limit - used, 0);
    return `${safeRemaining}/${limit}`;
  }

  if (typeof remaining === 'number') {
    return String(remaining);
  }

  return null;
}

export default function BillingUsageBadge({ className, onNavigate }: BillingUsageBadgeProps) {
  const { user, loading: authLoading } = useAuth();
  const { lang } = useI18n();
  const copy = lang === 'zh'
    ? {
        title: '权益',
        loading: '加载中',
        unavailable: '暂不可用',
        retry: '稍后重试',
        allowed: '可用',
        blocked: '受限',
        quota: '报告额度',
        open: '查看权益与价格',
      }
    : {
        title: 'Benefits',
        loading: 'Loading',
        unavailable: 'Unavailable',
        retry: 'Retry later',
        allowed: 'Allowed',
        blocked: 'Blocked',
        quota: 'Report quota',
        open: 'View plan and pricing',
      };

  const enabled = Boolean(user && !authLoading);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['billing-usage-summary', 'me'],
    queryFn: () => getBillingUsageSummary(),
    enabled,
    staleTime: 60_000,
    retry: 1,
  });

  if (!enabled) return null;

  if (isLoading) {
    return (
      <div
        className={cn(
          'inline-flex min-w-[132px] items-center gap-2 rounded-[6px] border border-stone-950/15 bg-white/50 px-2.5 py-1.5 text-xs text-stone-600',
          className
        )}
      >
        <Clock className="h-3.5 w-3.5 shrink-0" />
        <span className="font-semibold">{copy.title}</span>
        <span className="text-stone-500">{copy.loading}</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div
        className={cn(
          'inline-flex min-w-[132px] items-center gap-2 rounded-[6px] border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs text-amber-900',
          className
        )}
      >
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span className="font-semibold">{copy.title}</span>
        <span>{copy.unavailable}</span>
      </div>
    );
  }

  const allowed = data.can_create_report && data.decision_status !== 'blocked';
  const quota = getQuota(data);
  const statusText = allowed ? copy.allowed : copy.blocked;

  return (
    <Link
      to="/pricing"
      onClick={onNavigate}
      aria-label={copy.open}
      className={cn(
        'inline-flex min-w-[164px] max-w-[230px] items-center gap-2 rounded-[6px] border px-2.5 py-1.5 text-xs transition-colors',
        allowed
          ? 'border-emerald-200 bg-emerald-50/80 text-emerald-950 hover:bg-emerald-50'
          : 'border-red-200 bg-red-50/80 text-red-950 hover:bg-red-50',
        className
      )}
    >
      {allowed ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0" /> : <AlertTriangle className="h-3.5 w-3.5 shrink-0" />}
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          <Gauge className="h-3.5 w-3.5 shrink-0 text-stone-600" />
          <span className="truncate font-semibold text-stone-950">{formatPlan(data)}</span>
        </span>
        <span className="mt-0.5 block truncate text-[11px] text-stone-600">
          {quota ? `${copy.quota} ${quota}` : copy.retry}
        </span>
      </span>
      <Badge
        variant="outline"
        className={cn(
          'shrink-0 border-white/80 bg-white/70 px-1.5 py-0 text-[10px]',
          allowed ? 'text-emerald-800' : 'text-red-800'
        )}
      >
        {statusText}
      </Badge>
    </Link>
  );
}
