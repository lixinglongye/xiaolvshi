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
import { AlertTriangle, Clipboard, ExternalLink, FileCheck, Loader2, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  getMaintenanceEvidence,
  type MaintenanceEvidenceProfile,
  type MaintenanceLanguage,
} from '@/lib/maintenanceApi';

const categoryClass: Record<string, string> = {
  model_ops: 'bg-sky-50 text-sky-800 border-sky-200',
  quality: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  review_ops: 'bg-amber-50 text-amber-900 border-amber-200',
  release_management: 'bg-red-50 text-red-800 border-red-200',
  product: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  maintenance: 'bg-stone-50 text-stone-800 border-stone-200',
};

function roleLabel(role?: string) {
  return role ? role.replace(/_/g, ' ') : '-';
}

export default function MaintenanceEvidencePage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const [language, setLanguage] = useState<MaintenanceLanguage>('en');
  const [data, setData] = useState<MaintenanceEvidenceProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const load = async (nextLanguage = language) => {
    setLoading(true);
    setError('');
    try {
      setData(await getMaintenanceEvidence(nextLanguage));
    } catch (err) {
      console.error(err);
      setError('Maintenance evidence failed to load.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(language);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  const controls = data?.release_management.release_readiness_controls ?? [];
  const totalEvidencePaths = useMemo(
    () => (data?.signals ?? []).reduce((total, signal) => total + signal.evidence_paths.length, 0),
    [data],
  );

  const copyAnswer = async () => {
    if (!data?.form_answer) return;
    await navigator.clipboard.writeText(data.form_answer);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-stone-950/15 pb-6">
          <div>
            <div className="eyebrow mb-3">Maintenance</div>
            <h1 className="text-4xl font-black leading-none text-stone-950 sm:text-6xl">OSS Evidence</h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600">
              {data?.active_maintenance_summary ?? 'Reviewable maintenance signals for support applications.'}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-[8px] border border-stone-950/20 bg-[#fbfaf6] p-1">
              {(['en', 'zh'] as MaintenanceLanguage[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`h-9 min-w-12 rounded-[6px] px-3 text-sm font-semibold ${
                    language === item ? 'bg-stone-950 text-white' : 'text-stone-600 hover:text-stone-950'
                  }`}
                  onClick={() => setLanguage(item)}
                >
                  {item.toUpperCase()}
                </button>
              ))}
            </div>
            <Button variant="outline" className="soft-button" onClick={() => load()} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{data?.evidence_score ?? 0}</div>
              <div className="mt-1 text-sm text-stone-600">evidence score</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <FileCheck className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{data?.signals.length ?? 0}</div>
              <div className="mt-1 text-sm text-stone-600">maintenance signals</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <FileCheck className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{totalEvidencePaths}</div>
              <div className="mt-1 text-sm text-stone-600">evidence files</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{controls.length}</div>
              <div className="mt-1 text-sm text-stone-600">release controls</div>
            </CardContent>
          </Card>
        </div>

        {data && (
          <>
            <section className="mb-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Application answer</h2>
                    <div className="mt-1 text-sm text-stone-600">{roleLabel(data.maintainer_role)}</div>
                  </div>
                  <Button variant="outline" className="soft-button" onClick={copyAnswer}>
                    <Clipboard className="h-4 w-4" />
                    {copied ? 'Copied' : 'Copy'}
                  </Button>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4 text-sm leading-7 text-stone-700">
                  {data.form_answer}
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                <h2 className="mb-4 text-xl font-black text-stone-950">Project</h2>
                <div className="space-y-3 text-sm">
                  <div>
                    <div className="text-xs font-semibold uppercase text-stone-500">Name</div>
                    <div className="mt-1 font-semibold text-stone-950">{data.project.display_name}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase text-stone-500">Domain</div>
                    <div className="mt-1 text-stone-700">{data.project.domain}</div>
                  </div>
                  <a
                    href={data.project.repository_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-stone-950 hover:underline"
                  >
                    Repository
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="mb-3 text-xl font-black text-stone-950">Maintenance signals</h2>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead>Signal</TableHead>
                      <TableHead>Responsibility</TableHead>
                      <TableHead>Cadence</TableHead>
                      <TableHead>Evidence</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.signals.map((signal) => (
                      <TableRow key={signal.id}>
                        <TableCell>
                          <Badge variant="outline" className={categoryClass[signal.category] ?? categoryClass.maintenance}>
                            {signal.category.replace(/_/g, ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="font-semibold text-stone-950">{signal.title}</div>
                          <div className="mt-1 max-w-[420px] text-xs leading-5 text-stone-600">{signal.description}</div>
                        </TableCell>
                        <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                          {signal.responsibility}
                        </TableCell>
                        <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">{signal.cadence}</TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            {signal.evidence_paths.map((path) => (
                              <div key={path} className="break-all font-mono text-[11px] text-stone-600">
                                {path}
                              </div>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                <h2 className="mb-4 text-xl font-black text-stone-950">Release management</h2>
                <div className="mb-4 text-sm text-stone-600">{data.release_management.client_delivery_policy}</div>
                <div className="flex flex-wrap gap-2">
                  {controls.map((control) => (
                    <Badge key={control} variant="outline" className="bg-white">
                      {control}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                <h2 className="mb-4 text-xl font-black text-stone-950">Application guardrails</h2>
                <ul className="space-y-2 text-sm leading-6 text-stone-700">
                  {data.application_guardrails.map((guardrail) => (
                    <li key={guardrail} className="flex gap-2">
                      <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                      <span>{guardrail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          </>
        )}
      </div>
    </Layout>
  );
}
