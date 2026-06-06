import { useState } from 'react';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { User as UserIcon } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import FeedbackCapturePanel from '@/components/feedback/FeedbackCapturePanel';
import { useI18n } from '@/contexts/I18nContext';

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
