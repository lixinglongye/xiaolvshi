import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Trash2, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { useI18n, docTypeLabel } from '@/contexts/I18nContext';

interface DocItem {
  id: number;
  title: string;
  doc_type: string;
  status: string;
  created_at?: string;
}

export default function DocumentsPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t, lang } = useI18n();
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [filter, setFilter] = useState<string>('all');

  const load = useCallback(async () => {
    try {
      const query: Record<string, unknown> = {};
      if (filter !== 'all') query.status = filter;
      const r = await client.entities.documents.query({
        query,
        sort: '-created_at',
        limit: 100,
      });
      setDocs(r?.data?.items ?? []);
    } catch (e) {
      console.error(e);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const onDelete = async (id: number) => {
    if (!confirm(t('confirm_delete'))) return;
    try {
      await client.apiCall.invoke({
        url: '/api/v1/ai/documents/delete',
        method: 'POST',
        data: { document_id: id, reason: '' },
      });
      toast.success(t('deleted_success'));
      load();
    } catch (e) {
      console.error(e);
      toast.error('Delete error');
    }
  };

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14">
        <div className="flex items-end justify-between mb-8 flex-wrap gap-4 border-b border-stone-950/20 pb-6">
          <div>
            <div className="eyebrow mb-3">Document registry</div>
            <h1 className="text-4xl sm:text-6xl font-black leading-none text-stone-950">{t('documents_title')}</h1>
          </div>
          <div className="flex gap-3">
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-40 bg-[#fbfaf6] border-stone-950/25">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="processing">processing</SelectItem>
                <SelectItem value="completed">completed</SelectItem>
                <SelectItem value="failed">failed</SelectItem>
                <SelectItem value="deleted">deleted</SelectItem>
              </SelectContent>
            </Select>
            <Button asChild className="quiet-button">
              <Link to="/upload">{t('cta_upload')}</Link>
            </Button>
          </div>
        </div>

        <Card className="surface-card overflow-hidden">
          <CardHeader>
            <CardTitle className="text-xl">{t('documents_title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('title')}</TableHead>
                  <TableHead>{t('upload_doc_type')}</TableHead>
                  <TableHead>{t('status')}</TableHead>
                  <TableHead>{t('created_at')}</TableHead>
                  <TableHead className="text-right">{t('actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {docs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-slate-500 py-8">
                      {t('no_documents')}
                    </TableCell>
                  </TableRow>
                ) : (
                  docs.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell className="font-medium">{d.title}</TableCell>
                      <TableCell>{docTypeLabel(lang, d.doc_type)}</TableCell>
                      <TableCell>
                        <Badge variant={d.status === 'completed' ? 'default' : 'secondary'}>
                          {d.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">{d.created_at ?? ''}</TableCell>
                      <TableCell className="text-right space-x-2">
                        <Button asChild size="sm" variant="outline">
                          <Link to={`/review/${d.id}`}>
                            <Eye className="w-3 h-3 mr-1" /> {t('view')}
                          </Link>
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 hover:bg-red-50"
                          onClick={() => onDelete(d.id)}
                        >
                          <Trash2 className="w-3 h-3 mr-1" /> {t('delete')}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
