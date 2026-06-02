import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, FileText, Upload, PenLine, Users, CheckCircle2 } from 'lucide-react';
import { client } from '@/lib/api';
import { useI18n, docTypeLabel } from '@/contexts/I18nContext';

interface DocItem {
  id: number;
  title: string;
  doc_type: string;
  status: string;
  created_at?: string;
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardInner />
    </AuthGuard>
  );
}

function DashboardInner() {
  const { t, lang } = useI18n();
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [draftCount, setDraftCount] = useState(0);
  const [reviewedCount, setReviewedCount] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const resp = await client.entities.documents.query({ sort: '-created_at', limit: 5 });
        setDocs(resp?.data?.items ?? []);
        const allResp = await client.entities.documents.query({ limit: 200 });
        const list: DocItem[] = allResp?.data?.items ?? [];
        setTotalCount(list.length);
        setReviewedCount(list.filter((d) => d.status === 'completed').length);
        const draftResp = await client.entities.generated_documents.query({ limit: 200 });
        setDraftCount(draftResp?.data?.items?.length ?? 0);
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <div className="eyebrow mb-3">Workspace</div>
            <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-950">{t('nav_dashboard')}</h1>
          </div>
          <Button asChild className="quiet-button rounded-full">
            <Link to="/upload">
              <Upload className="w-4 h-4" />
              {t('cta_upload')}
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card className="surface-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-slate-500">{t('summary_total_docs')}</CardTitle>
              <FileText className="w-5 h-5 text-slate-700" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold tracking-tight">{totalCount}</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-slate-500">{t('summary_completed')}</CardTitle>
              <CheckCircle2 className="w-5 h-5 text-emerald-700" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold tracking-tight">{reviewedCount}</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-slate-500">{t('summary_drafts')}</CardTitle>
              <PenLine className="w-5 h-5 text-emerald-700" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold tracking-tight">{draftCount}</div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6 surface-panel">
          <CardHeader>
            <CardTitle className="text-xl tracking-tight">{t('quick_actions')}</CardTitle>
          </CardHeader>
          <CardContent className="grid sm:grid-cols-3 gap-3">
            <Button asChild className="quiet-button rounded-full justify-between">
              <Link to="/upload">
                <span className="inline-flex items-center gap-2"><Upload className="w-4 h-4" /> {t('cta_upload')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" className="soft-button rounded-full justify-between">
              <Link to="/generate">
                <span className="inline-flex items-center gap-2"><PenLine className="w-4 h-4" /> {t('nav_generate')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" className="soft-button rounded-full justify-between">
              <Link to="/team">
                <span className="inline-flex items-center gap-2"><Users className="w-4 h-4" /> {t('nav_team')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="surface-card">
          <CardHeader>
            <CardTitle className="text-xl tracking-tight">{t('recent_documents')}</CardTitle>
          </CardHeader>
          <CardContent>
            {docs.length === 0 ? (
              <p className="text-slate-500 text-sm">{t('no_documents')}</p>
            ) : (
              <ul className="space-y-2">
                {docs.map((d) => (
                  <li key={d.id}>
                    <Link
                      to={`/review/${d.id}`}
                      className="interactive-button group flex items-center justify-between gap-4 rounded-[16px] border border-stone-950/12 bg-[#fbfaf6] px-4 py-3 transition-[background,border-color,transform] hover:-translate-y-0.5 hover:border-stone-950/22 hover:bg-[#f2ede3] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-950/25"
                    >
                      <div className="min-w-0">
                        <div className="truncate font-semibold text-slate-950 group-hover:text-stone-950">
                          {d.title || `#${d.id}`}
                        </div>
                        <div className="mt-1 truncate text-xs text-slate-500">
                          {docTypeLabel(lang, d.doc_type)} · {d.created_at ?? ''}
                        </div>
                      </div>
                      <Badge variant={d.status === 'completed' ? 'default' : 'secondary'} className={`shrink-0 ${d.status === 'completed' ? 'bg-slate-950 text-white' : ''}`}>
                        {d.status}
                      </Badge>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
