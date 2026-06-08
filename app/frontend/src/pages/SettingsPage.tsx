import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertTriangle, ExternalLink, Route, ShieldCheck, User as UserIcon, Zap } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import {
  getModelGatewayRuntimeConfiguration,
  type ModelGatewayRuntimeConfiguration,
} from '@/lib/modelOpsApi';
import FeedbackCapturePanel from '@/components/feedback/FeedbackCapturePanel';
import { useI18n } from '@/contexts/I18nContext';

const PROVIDER_ENV_NAMES = [
  'APP_AI_BASE_URL',
  'APP_AI_KEY',
  'APP_AI_CHEAP_MODEL',
  'APP_AI_BALANCED_MODEL',
  'APP_AI_PREMIUM_MODEL',
  'APP_AI_AGENTIC_MODEL',
  'APP_AI_GROUNDED_RESEARCH_MODEL',
  'APP_AI_EMBEDDING_MODEL',
] as const;

function providerStatusClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes('blocked') || normalized.includes('fail') || normalized.includes('missing')) {
    return 'border-red-200 bg-red-50 text-red-700';
  }
  if (normalized.includes('warning') || normalized.includes('review') || normalized.includes('gap')) {
    return 'border-amber-200 bg-amber-50 text-amber-700';
  }
  if (normalized.includes('ready') || normalized.includes('pass')) {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
  return 'border-slate-200 bg-slate-50 text-slate-700';
}

export default function SettingsPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t, lang, setLang } = useI18n();
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [providerStatus, setProviderStatus] = useState<ModelGatewayRuntimeConfiguration | null>(null);
  const [providerLoading, setProviderLoading] = useState(true);
  const [providerError, setProviderError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadProviderStatus = async () => {
      setProviderLoading(true);
      setProviderError(null);
      try {
        const payload = await getModelGatewayRuntimeConfiguration();
        if (mounted) {
          setProviderStatus(payload);
        }
      } catch (error) {
        console.error(error);
        if (mounted) {
          setProviderError('Provider status is unavailable');
          setProviderStatus(null);
        }
      } finally {
        if (mounted) {
          setProviderLoading(false);
        }
      }
    };

    void loadProviderStatus();

    return () => {
      mounted = false;
    };
  }, []);

  const providerRoleRows = providerStatus?.role_rows ?? [];
  const highFrequencyProviderRows = providerRoleRows.filter((row) => row.high_frequency_role).slice(0, 4);
  const visibleProviderRows =
    highFrequencyProviderRows.length > 0 ? highFrequencyProviderRows : providerRoleRows.slice(0, 4);
  const visibleProviderActions = providerStatus?.recommended_actions.slice(0, 3) ?? [];

  const submitDeletion = async () => {
    if (!reason.trim()) return;
    setSubmitting(true);
    try {
      await client.entities.feedback_tickets.create({
        data: { category: 'data_deletion', content: reason, status: 'open' },
      });
      toast.success('Submitted');
      setReason('');
    } catch (e) {
      console.error(e);
      toast.error('Submit error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        <h1 className="text-3xl font-bold text-slate-900">{t('settings_title')}</h1>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="w-5 h-5 text-blue-700" /> Account
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">已登录账户 / Logged in account</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('language')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={lang} onValueChange={(v) => setLang(v as 'zh' | 'en')}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="zh">中文</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-blue-700" /> AI model provider
                </CardTitle>
                <p className="mt-1 text-sm text-slate-600">
                  Gemini cheap-first routing is read-only here. Configuration is managed through deployment secrets.
                </p>
              </div>
              {providerStatus ? (
                <Badge variant="outline" className={providerStatusClass(providerStatus.status)}>
                  {providerStatus.status}
                </Badge>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {providerLoading ? (
              <div className="rounded-[8px] border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                Loading provider status...
              </div>
            ) : providerError ? (
              <div className="flex items-start gap-3 rounded-[8px] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <div>{providerError}. Open ModelOps for the full runtime configuration packet.</div>
              </div>
            ) : providerStatus ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[8px] border border-slate-200 bg-slate-50 p-4">
                    <div className="text-sm font-semibold text-slate-950">
                      {providerStatus.summary.base_url_configured ? 'configured' : 'missing'}
                    </div>
                    <div className="mt-1 text-xs text-slate-600">
                      normalized base URL via {providerStatus.runtime_env.base_url_env}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-slate-200 bg-slate-50 p-4">
                    <div className="text-sm font-semibold text-slate-950">
                      {providerStatus.summary.api_key_configured ? 'configured' : 'missing'}
                    </div>
                    <div className="mt-1 text-xs text-slate-600">
                      credential presence via {providerStatus.runtime_env.api_key_env}
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-[8px] border border-slate-200 p-3">
                    <div className="text-lg font-bold text-slate-950">
                      {providerStatus.summary.cheap_first_ready_count}
                    </div>
                    <div className="text-xs text-slate-600">cheap-first ready roles</div>
                  </div>
                  <div className="rounded-[8px] border border-slate-200 p-3">
                    <div className="text-lg font-bold text-slate-950">
                      {String(providerStatus.summary.base_url_configured)}
                    </div>
                    <div className="text-xs text-slate-600">base URL configured</div>
                  </div>
                  <div className="rounded-[8px] border border-slate-200 p-3">
                    <div className="text-lg font-bold text-slate-950">
                      {String(providerStatus.summary.credentials_included)}
                    </div>
                    <div className="text-xs text-slate-600">credentials included</div>
                  </div>
                  <div className="rounded-[8px] border border-slate-200 p-3">
                    <div className="text-lg font-bold text-slate-950">
                      {String(providerStatus.summary.configuration_written)}
                    </div>
                    <div className="text-xs text-slate-600">configuration written</div>
                  </div>
                </div>

                <div className="rounded-[8px] border border-slate-200">
                  <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
                    <Route className="h-4 w-4 text-blue-700" />
                    High-frequency route defaults
                  </div>
                  <div className="divide-y divide-slate-200">
                    {visibleProviderRows.map((row) => (
                      <div key={`${row.role}-${row.env_name}`} className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[1fr_1.2fr]">
                        <div>
                          <div className="font-semibold text-slate-950">{row.role}</div>
                          <div className="font-mono text-xs text-slate-500">{row.env_name}</div>
                        </div>
                        <div>
                          <div className="font-mono text-xs text-slate-950">{row.configured_model}</div>
                          <div className="mt-1 flex flex-wrap gap-2">
                            <Badge variant="outline" className="border-slate-200 bg-white text-slate-700">
                              {row.cost_tier}
                            </Badge>
                            <Badge variant="outline" className={providerStatusClass(row.runtime_action)}>
                              {row.runtime_action}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-[1fr_0.9fr]">
                  <div className="rounded-[8px] border border-slate-200 p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <ShieldCheck className="h-4 w-4 text-blue-700" />
                      Safe runtime env names
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {PROVIDER_ENV_NAMES.map((name) => (
                        <div key={name} className="font-mono text-xs text-slate-600">
                          {name}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-slate-200 p-4">
                    <div className="mb-2 text-sm font-semibold text-slate-900">Recommended actions</div>
                    <div className="space-y-2 text-xs leading-5 text-slate-600">
                      {visibleProviderActions.length > 0 ? (
                        visibleProviderActions.map((action) => <div key={action}>{action}</div>)
                      ) : (
                        <div>No provider action is currently recommended.</div>
                      )}
                    </div>
                  </div>
                </div>

                <Button asChild variant="outline" className="w-full justify-center sm:w-auto">
                  <Link to="/model-ops">
                    Open ModelOps evidence
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                </Button>
              </>
            ) : null}
          </CardContent>
        </Card>

        <FeedbackCapturePanel />

        <Card>
          <CardHeader>
            <CardTitle>{t('data_deletion_request')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Label>{t('data_deletion_reason')}</Label>
            <Textarea rows={4} value={reason} onChange={(e) => setReason(e.target.value)} />
            <Button
              onClick={submitDeletion}
              disabled={submitting}
              className="bg-blue-700 hover:bg-blue-800 text-white"
            >
              {submitting ? '...' : t('submit')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
