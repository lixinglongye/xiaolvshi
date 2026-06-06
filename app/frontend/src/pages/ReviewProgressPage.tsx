import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Clock3, Loader2, ShieldAlert, Lock } from 'lucide-react';
import { toast } from 'sonner';
import LoadingSpinner from '@/components/LoadingSpinner';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import { client } from '@/lib/api';
import { useI18n } from '@/contexts/I18nContext';
import {
  getLatestReportByDocument,
  getUploadedDocumentAnalysisStatus,
  type AnalyzeUploadedDocumentStatusResponse,
  type DeepReviewReportSummary,
} from '@/lib/deepReviewApi';
import { getProductBySku } from '@/lib/productCatalog';

interface DocItem {
  id: number;
  title: string;
  doc_type: string;
  status: string;
}
export default function ReviewProgressPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t, lang } = useI18n();
  const [doc, setDoc] = useState<DocItem | null>(null);
  const [review, setReview] = useState<DeepReviewReportSummary | null>(null);
  const [statusInfo, setStatusInfo] = useState<AnalyzeUploadedDocumentStatusResponse | null>(null);
  const [tries, setTries] = useState(0);
  const [unlocking, setUnlocking] = useState(false);
  const [unlockPrice, setUnlockPrice] = useState('');

  useEffect(() => {
    let stop = false;
    const fetchOnce = async () => {
      try {
        const docResp = await client.entities.documents.get({ id: id as string });
        if (stop) return;
        setDoc(docResp?.data ?? null);

        const status = await getUploadedDocumentAnalysisStatus(Number(id));
        if (stop) return;
        setStatusInfo(status);
        if (status.status === 'completed') {
          const latest = await getLatestReportByDocument(Number(id));
          if (!stop && latest) setReview(latest);
        } else {
          setTries((n) => n + 1);
        }
      } catch (e) {
        console.error(e);
        try {
          const latest = await getLatestReportByDocument(Number(id));
          if (!stop && latest) {
            setReview(latest);
          } else {
            setTries((n) => n + 1);
          }
        } catch {
          setTries((n) => n + 1);
        }
      }
    };
    fetchOnce();
    const timer = setInterval(() => {
      if (stop || review) return;
      fetchOnce();
    }, 2500);
    return () => {
      stop = true;
      clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, review]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const item = await getProductBySku(lang, 'report_unlock');
        if (!cancelled) setUnlockPrice(item?.display_price ?? '');
      } catch {
        if (!cancelled) setUnlockPrice('');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lang]);

  const unlock = async () => {
    if (!review) return;
    setUnlocking(true);
    try {
      const resp = await client.apiCall.invoke({
        url: '/api/v1/payment/create_payment_session',
        method: 'POST',
        data: { sku: 'report_unlock', related_review_id: review.report_id },
      });
      const url = resp?.data?.url;
      if (url) {
        if (client.utils?.openUrl) {
          client.utils.openUrl(url);
        } else {
          window.location.href = url;
        }
      } else {
        throw new Error('Missing checkout URL');
      }
    } catch (e) {
      console.error(e);
      toast.info(t('unlock_processing'));
      await client.apiCall.invoke({
        url: '/api/v1/entitlements/demo-activate',
        method: 'POST',
        data: { sku: 'report_unlock', related_review_id: review.report_id },
      });
      toast.success(t('unlock_success'));
      navigate(`/payment-success?demo=true&sku=report_unlock&review_id=${review.report_id}`);
    } finally {
      setUnlocking(false);
    }
  };

  const riskBg =
    review?.risk_level === 'high' || review?.risk_level === '高' || review?.risk_level === '重大'
      ? 'bg-red-50 border-red-200'
      : review?.risk_level === 'medium' || review?.risk_level === '中'
      ? 'bg-amber-50 border-amber-200'
      : 'bg-green-50 border-green-200';

  const topRisks = (review?.top_risks ?? []).map((risk) => {
    if (typeof risk === 'string') return { title: risk, severity: review?.risk_level ?? 'medium' };
    return { title: risk.title ?? '', severity: risk.severity ?? review?.risk_level ?? 'medium' };
  });

  const riskLabel = review?.risk_level === '高' || review?.risk_level === '重大'
    ? 'high'
    : review?.risk_level === '低'
    ? 'low'
    : review?.risk_level === '中'
    ? 'medium'
    : review?.risk_level || 'medium';
  const riskBadgeClass = riskLabel === 'high'
    ? 'bg-red-600'
    : riskLabel === 'medium'
    ? 'bg-amber-600'
    : 'bg-green-600';

  if (!doc) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  if (!review) {
    const progressPercent = statusInfo?.progress?.percent ?? Math.min(95, tries * 18);
    const stageName = statusInfo?.progress?.stage_name || (lang === 'zh' ? '正在准备审查' : 'Preparing review');
    const stageDetail = statusInfo?.progress?.detail || (lang === 'zh' ? '页面会自动刷新当前步骤。' : 'This page refreshes the current step automatically.');
    const preview = statusInfo?.pipeline_preview ?? statusInfo?.progress?.completed_stages ?? [];
    const ocrReadiness = statusInfo?.ocr_readiness || statusInfo?.extraction?.ocr_readiness;
    const stageLabels = lang === 'zh'
      ? ['上传', '解析/OCR', '风险识别', '法律依据', '报告']
      : ['Upload', 'OCR', 'Issue spotting', 'Authorities', 'Report'];
    const stageThresholds = [20, 40, 72, 84, 100];
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-lg font-semibold text-slate-950">
                  <Loader2 className="w-5 h-5 animate-spin text-emerald-800" />
                  {stageName}
                </div>
                <p className="mt-1 text-sm text-slate-600">{stageDetail}</p>
                <p className="mt-2 text-xs text-slate-500">{doc.title}</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Clock3 className="w-4 h-4" />
                {statusInfo?.status || 'processing'}
              </div>
            </div>

            <Progress value={progressPercent} className="mt-6 h-2 bg-slate-100" />

            <div className="mt-6 grid grid-cols-5 gap-2">
              {stageLabels.map((label, index) => {
                const done = progressPercent >= stageThresholds[index];
                const active = !done && progressPercent >= (stageThresholds[index - 1] ?? 0);
                return (
                  <div key={label} className="min-w-0 text-center">
                    <div
                      className={[
                        'mx-auto mb-2 flex h-9 w-9 items-center justify-center rounded-full border',
                        done
                          ? 'border-emerald-700 bg-emerald-700 text-white'
                          : active
                            ? 'border-emerald-700 bg-emerald-50 text-emerald-800'
                            : 'border-slate-200 bg-slate-50 text-slate-400',
                      ].join(' ')}
                    >
                      {done ? <CheckCircle2 className="w-4 h-4" /> : <span className="text-xs">{index + 1}</span>}
                    </div>
                    <div className="truncate text-xs text-slate-500">{label}</div>
                  </div>
                );
              })}
            </div>

            {preview.length ? (
              <div className="mt-6 grid gap-2 sm:grid-cols-2">
                {preview.slice(-6).map((stage) => (
                  <div key={`${stage.stage_id}-${stage.stage_name}`} className="rounded-xl bg-slate-50 px-3 py-2 text-xs">
                    <div className="font-medium text-slate-900">{stage.stage_name}</div>
                    <div className="mt-1 text-slate-500">{stage.status || (lang === 'zh' ? '已完成' : 'completed')}</div>
                  </div>
                ))}
              </div>
            ) : null}

            {statusInfo?.extraction?.warnings?.length ? (
              <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                {statusInfo.extraction.warnings.join('；')}
              </div>
            ) : null}

            {ocrReadiness ? (
              <div className="mt-5 rounded-xl border border-indigo-100 bg-indigo-50 p-3 text-xs text-indigo-950">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="font-semibold">{lang === 'zh' ? 'OCR 导入状态' : 'OCR readiness'}</div>
                  <Badge
                    variant="outline"
                    className={
                      ocrReadiness.status === 'parsed'
                        ? 'border-emerald-200 bg-white text-emerald-800'
                        : ocrReadiness.status === 'blocked' || ocrReadiness.status === 'ocr_failed'
                          ? 'border-red-200 bg-white text-red-800'
                          : ocrReadiness.status === 'manual_review'
                            ? 'border-amber-200 bg-white text-amber-900'
                            : 'border-indigo-200 bg-white text-indigo-900'
                    }
                  >
                    {ocrReadiness.status || 'uploaded'}
                  </Badge>
                </div>
                <div className="grid gap-2 sm:grid-cols-3">
                  <div>{lang === 'zh' ? '需 OCR' : 'OCR required'}: {ocrReadiness.summary?.ocr_required ? 'yes' : 'no'}</div>
                  <div>{lang === 'zh' ? '低文本页' : 'Low text'}: {ocrReadiness.summary?.low_text_page_count ?? 0}</div>
                  <div>{lang === 'zh' ? '尝试次数' : 'Attempts'}: {ocrReadiness.summary?.ocr_attempt_count ?? 0}</div>
                </div>
                {ocrReadiness.blocking_conditions?.[0] ? (
                  <div className="mt-2 leading-5 text-red-800">{ocrReadiness.blocking_conditions[0].title}</div>
                ) : ocrReadiness.manual_review_conditions?.[0] ? (
                  <div className="mt-2 leading-5 text-amber-900">{ocrReadiness.manual_review_conditions[0].title}</div>
                ) : ocrReadiness.recommended_next_actions?.[0] ? (
                  <div className="mt-2 leading-5 text-indigo-900">{ocrReadiness.recommended_next_actions[0]}</div>
                ) : null}
              </div>
            ) : null}

            <div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
              {lang === 'zh'
                ? '深度审查会依次完成文书识别、条款定位、风险识别、法律依据校验和报告组装。长合同、扫描件或模型排队时会更久。'
                : 'Deep review runs document intake, clause mapping, issue spotting, citation validation, and report assembly. Long or scanned documents can take longer.'}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{doc.title}</h1>
            <p className="text-slate-500 text-sm mt-1">{doc.doc_type}</p>
          </div>
          <Button asChild className="bg-blue-700 hover:bg-blue-800 text-white">
            <Link to={`/deep-report/${review.report_id}`}>{t('view_full_report')}</Link>
          </Button>
        </div>

        <Card className={`border-2 ${riskBg}`}>
          <CardContent className="py-8 flex items-center gap-8 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <Badge
                className={`text-base px-3 py-1 ${riskBadgeClass} text-white`}
              >
                <ShieldAlert className="w-4 h-4 mr-1" />
                {t(`risk_level_${riskLabel}`)}
              </Badge>
              <p className="mt-3 text-slate-700">{review.executive_summary}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('top_risks')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topRisks.map((r, i) => (
              <div key={i} className="flex items-center gap-3 p-3 border rounded-lg bg-slate-50">
                <Badge
                  className={
                    r.severity === 'high'
                    || r.severity === '高'
                    || r.severity === '重大'
                      ? 'bg-red-600 text-white'
                      : r.severity === 'medium' || r.severity === '中'
                      ? 'bg-amber-600 text-white'
                      : 'bg-green-600 text-white'
                  }
                >
                  {r.severity}
                </Badge>
                <span className="flex-1">{r.title}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {!review.is_paid && (
          <Card className="border-2 border-blue-300 bg-blue-50">
            <CardContent className="py-6 flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <Lock className="w-6 h-6 text-blue-700" />
                  <div>
                    <div className="font-semibold text-slate-900">{t('unlock_full')}</div>
                  <div className="text-sm text-slate-600">
                    {unlockPrice ? `${unlockPrice} — ` : ''}修改建议 / 谈判话术 / 法律依据
                  </div>
                </div>
              </div>
              <Button
                disabled={unlocking}
                onClick={unlock}
                className="bg-blue-700 hover:bg-blue-800 text-white"
              >
                {unlocking ? '...' : t('unlock_now')}
              </Button>
            </CardContent>
          </Card>
        )}

        <DisclaimerBanner />
      </div>
    </Layout>
  );
}
