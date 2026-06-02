import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { client } from '@/lib/api';
import { useI18n } from '@/contexts/I18nContext';
import { getProductCatalog } from '@/lib/productCatalog';

export default function PaymentSuccessPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t, lang } = useI18n();
  const [params] = useSearchParams();
  const sessionId = params.get('session_id');
  const isDemo = params.get('demo') === 'true';
  const sku = params.get('sku');
  const reviewIdParam = params.get('review_id');
  const parsedReviewId = reviewIdParam ? Number(reviewIdParam) : NaN;
  const [status, setStatus] = useState<'pending' | 'paid' | 'cancelled' | 'error'>('pending');
  const [reviewId, setReviewId] = useState<number | null>(Number.isFinite(parsedReviewId) ? parsedReviewId : null);
  const [skuLabel, setSkuLabel] = useState('');

  useEffect(() => {
    if (!sku) return;
    let cancelled = false;
    (async () => {
      try {
        const items = await getProductCatalog(lang);
        const item = items.find((candidate) => candidate.sku === sku);
        if (!cancelled) setSkuLabel(item?.name ?? sku);
      } catch {
        if (!cancelled) setSkuLabel(sku);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sku, lang]);

  useEffect(() => {
    // Demo mode: immediately show success
    if (isDemo) {
      setStatus('paid');
      return;
    }

    if (!sessionId) {
      setStatus('error');
      return;
    }
    (async () => {
      try {
        const r = await client.apiCall.invoke({
          url: '/api/v1/payment/verify_payment',
          method: 'POST',
          data: { session_id: sessionId },
        });
        const data = r?.data ?? {};
        setStatus(data.status === 'paid' ? 'paid' : data.status === 'cancelled' ? 'cancelled' : 'pending');
        if (data.related_review_id) setReviewId(data.related_review_id);
      } catch (e) {
        console.error(e);
        setStatus('error');
      }
    })();
  }, [sessionId, isDemo]);

  return (
    <Layout>
      <div className="flex items-center justify-center min-h-[60vh] p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            {status === 'paid' ? (
              <CheckCircle className="w-14 h-14 text-green-600 mx-auto mb-2" />
            ) : status === 'pending' ? (
              <Loader2 className="w-14 h-14 text-blue-600 mx-auto mb-2 animate-spin" />
            ) : (
              <XCircle className="w-14 h-14 text-red-600 mx-auto mb-2" />
            )}
            <CardTitle>
              {status === 'paid'
                ? t('payment_success')
                : status === 'pending'
                ? t('payment_pending')
                : t('payment_failed')}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-3">
            {status === 'paid' && skuLabel && (
              <p className="text-slate-600 text-sm">
                {lang === 'zh' ? '已成功订阅：' : 'Subscribed: '}
                <span className="font-semibold text-slate-900">{skuLabel}</span>
              </p>
            )}
            {isDemo && status === 'paid' && (
              <p className="text-xs text-slate-400">
                {lang === 'zh' ? '（演示模式 — Stripe 未配置）' : '(Demo mode — Stripe not configured)'}
              </p>
            )}
            {reviewId && status === 'paid' && (
              <Button asChild className="w-full bg-blue-700 hover:bg-blue-800 text-white">
                <Link to={`/deep-report/${reviewId}`}>{t('view_full_report')}</Link>
              </Button>
            )}
            <Button asChild variant="outline" className="w-full">
              <Link to="/dashboard">{t('back_to_dashboard')}</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
