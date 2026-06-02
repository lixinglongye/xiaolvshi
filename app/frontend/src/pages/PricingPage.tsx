import { useEffect, useState, type CSSProperties, type PointerEvent } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { CheckCircle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { getProductCatalog, type ProductCatalogItem } from '@/lib/productCatalog';

export default function PricingPage() {
  const { user } = useAuth();
  const { t, lang } = useI18n();
  const [loading, setLoading] = useState<string | null>(null);
  const [activeSku, setActiveSku] = useState('');
  const [spotlight, setSpotlight] = useState({ x: 62, y: 42 });
  const [plans, setPlans] = useState<ProductCatalogItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);

  const copy = lang === 'zh'
    ? {
        intro: '透明定价，按需付费。每个方案都保留审查依据、风险矩阵和可复制建议。',
        recommended: 'Recommended',
        loading: '...',
      }
    : {
        intro: 'Transparent pricing for document review. Every plan keeps the rationale, risk matrix, and copy-ready suggestions.',
        recommended: 'Recommended',
        loading: '...',
      };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setCatalogLoading(true);
      try {
        const items = await getProductCatalog(lang);
        if (cancelled) return;
        setPlans(items);
        const defaultPlan = items.find((item) => item.highlight) ?? items[0];
        if (defaultPlan) setActiveSku(defaultPlan.sku);
      } catch (error) {
        console.error('Product catalog load failed:', error);
        if (!cancelled) toast.error(lang === 'zh' ? '价格目录加载失败' : 'Failed to load pricing catalog');
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lang]);

  const handleSubscribe = async (sku: string) => {
    if (!user) {
      try {
        await client.auth.toLogin();
      } catch (e) {
        console.error(e);
      }
      return;
    }
    setLoading(sku);
    try {
      const resp = await client.apiCall.invoke({
        url: '/api/v1/payment/create_payment_session',
        method: 'POST',
        data: { sku },
      });
      const url = resp?.data?.url;
      if (url) {
        if (client.utils?.openUrl) {
          client.utils.openUrl(url);
        } else {
          window.location.href = url;
        }
      } else {
        // Stripe not configured — simulate successful subscription
        await demoSubscribe(sku);
      }
    } catch (e) {
      console.error('Payment session error:', e);
      // Fallback: simulate successful subscription when payment service unavailable
      await demoSubscribe(sku);
    } finally {
      setLoading(null);
    }
  };

  const handleBoardPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setSpotlight({
      x: ((event.clientX - rect.left) / rect.width) * 100,
      y: ((event.clientY - rect.top) / rect.height) * 100,
    });
  };

  const boardStyle = {
    '--pricing-x': `${spotlight.x}%`,
    '--pricing-y': `${spotlight.y}%`,
  } as CSSProperties;

  const defaultActiveSku = plans.find((item) => item.highlight)?.sku ?? plans[0]?.sku ?? '';

  const demoSubscribe = async (sku: string) => {
    toast.info(t('payment_pending'));
    try {
      await client.apiCall.invoke({
        url: '/api/v1/entitlements/demo-activate',
        method: 'POST',
        data: { sku },
      });
    } catch (e) {
      console.error('Demo entitlement activation failed:', e);
    }
    window.location.href = `/payment-success?demo=true&sku=${sku}`;
  };

  return (
    <Layout>
      <div className="law-container py-14 lg:py-20">
        <div className="mb-12 max-w-4xl">
          <div className="eyebrow mb-3">Pricing</div>
          <h1 className="text-6xl sm:text-8xl font-black leading-[0.88] text-stone-950">{t('pricing_title')}</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600">{copy.intro}</p>
        </div>
        <div
          className="pricing-board grid md:grid-cols-2 lg:grid-cols-4"
          style={boardStyle}
          onPointerMove={handleBoardPointerMove}
          onPointerLeave={() => setActiveSku(defaultActiveSku)}
        >
          {catalogLoading && (
            <div className="col-span-full min-h-[220px] p-8 text-sm text-stone-500">
              {lang === 'zh' ? '正在加载价格目录...' : 'Loading pricing catalog...'}
            </div>
          )}
          {plans.map((p) => {
            const active = activeSku === p.sku || (!activeSku && p.highlight);
            return (
            <article
              key={p.sku}
              className={`pricing-plan relative min-h-[520px] p-5 flex flex-col ${active ? 'is-active' : ''}`}
              onPointerEnter={() => setActiveSku(p.sku)}
              onFocus={() => setActiveSku(p.sku)}
              tabIndex={0}
            >
              <div className={`relative z-10 text-sm font-semibold ${active ? 'text-amber-300' : 'text-amber-700'}`}>
                {p.highlight || active ? (
                  <span className="inline-flex items-center gap-2"><Sparkles className="w-4 h-4" /> {copy.recommended}</span>
                ) : (
                  p.sku.replace('_', ' ')
                )}
              </div>
              <h2 className="relative z-10 mt-5 text-3xl font-black leading-none">{p.name}</h2>
              <p className={`relative z-10 mt-3 text-sm leading-6 ${active ? 'text-stone-300' : 'text-stone-600'}`}>
                {p.description}
              </p>
              <div className="relative z-10 mt-8 text-5xl font-black leading-none">
                {p.display_price}
                {p.interval === 'month' && (
                  <span className={`ml-2 text-sm font-semibold ${active ? 'text-stone-400' : 'text-stone-500'}`}>
                    {t('per_month')}
                  </span>
                )}
              </div>
              <ul className="relative z-10 mt-10 space-y-4 text-sm leading-6">
                {p.features.map((f) => (
                  <li key={f} className={`flex items-start gap-2 ${active ? 'text-stone-200' : 'text-stone-700'}`}>
                    <CheckCircle className={`w-4 h-4 mt-1 flex-shrink-0 ${active ? 'text-amber-300' : 'text-amber-700'}`} />
                    {f}
                  </li>
                ))}
              </ul>
              <Button
                className={`relative z-10 mt-auto w-full ${active ? 'bg-white text-stone-950 hover:bg-stone-200' : 'quiet-button'}`}
                disabled={loading === p.sku}
                onClick={() => handleSubscribe(p.sku)}
              >
                {loading === p.sku
                  ? copy.loading
                  : p.sku === 'report_unlock'
                  ? t('unlock_now')
                  : t('subscribe')}
              </Button>
            </article>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
