import { useState } from 'react';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ClipboardCheck, MessageSquare, Send, User as UserIcon } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { previewFeedbackCapturePlan, type FeedbackCapturePlan } from '@/lib/feedbackApi';
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
  const [feedbackCategory, setFeedbackCategory] = useState('general');
  const [feedbackContent, setFeedbackContent] = useState('');
  const [affectedArtifactId, setAffectedArtifactId] = useState('');
  const [accountContext, setAccountContext] = useState('');
  const [capturePlan, setCapturePlan] = useState<FeedbackCapturePlan | null>(null);
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [previewingFeedback, setPreviewingFeedback] = useState(false);
  const [submittedFeedback, setSubmittedFeedback] = useState<{
    id?: number;
    priority?: string;
    assignee?: string;
    status?: string;
  } | null>(null);

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

  const feedbackPayload = () => ({
    category: feedbackCategory,
    content: feedbackContent,
    ...(affectedArtifactId.trim() ? { affected_artifact_id: affectedArtifactId.trim() } : {}),
    ...(accountContext.trim() ? { account_context: accountContext.trim() } : {}),
  });

  const previewFeedback = async () => {
    if (!feedbackContent.trim()) return;
    setPreviewingFeedback(true);
    try {
      const plan = await previewFeedbackCapturePlan(feedbackPayload());
      setCapturePlan(plan);
      setSubmittedFeedback(null);
      toast.success('Feedback plan ready');
      return plan;
    } catch (e) {
      console.error(e);
      toast.error('Preview error');
      return null;
    } finally {
      setPreviewingFeedback(false);
    }
  };

  const submitFeedback = async () => {
    if (!feedbackContent.trim()) return;
    setFeedbackSubmitting(true);
    try {
      const plan = capturePlan ?? (await previewFeedback());
      const response = await client.entities.feedback_tickets.create({
        data: {
          category: feedbackCategory,
          content: feedbackContent,
          status: 'open',
          resolution_note: plan?.ticket_defaults.resolution_note,
        },
      });
      const ticket = (response?.data ?? response ?? {}) as {
        id?: number;
        priority?: string;
        assignee?: string;
        status?: string;
      };
      setSubmittedFeedback(ticket);
      setFeedbackContent('');
      setAffectedArtifactId('');
      setAccountContext('');
      toast.success('Feedback submitted');
    } catch (e) {
      console.error(e);
      toast.error('Submit error');
    } finally {
      setFeedbackSubmitting(false);
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
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-700" /> Product feedback
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Workflow</Label>
                <Select
                  value={feedbackCategory}
                  onValueChange={(value) => {
                    setFeedbackCategory(value);
                    setCapturePlan(null);
                    setSubmittedFeedback(null);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General feedback</SelectItem>
                    <SelectItem value="report_quality">Report quality</SelectItem>
                    <SelectItem value="upload_pipeline">Upload or OCR</SelectItem>
                    <SelectItem value="billing_access">Billing or access</SelectItem>
                    <SelectItem value="template_export">Template or export</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Related report/case/document ID</Label>
                <Input
                  value={affectedArtifactId}
                  onChange={(event) => {
                    setAffectedArtifactId(event.target.value);
                    setCapturePlan(null);
                  }}
                  placeholder="Optional"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Account or plan context</Label>
              <Input
                value={accountContext}
                onChange={(event) => {
                  setAccountContext(event.target.value);
                  setCapturePlan(null);
                }}
                placeholder="Optional"
              />
            </div>
            <div className="space-y-2">
              <Label>What happened?</Label>
              <Textarea
                rows={4}
                value={feedbackContent}
                onChange={(event) => {
                  setFeedbackContent(event.target.value);
                  setCapturePlan(null);
                  setSubmittedFeedback(null);
                }}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={previewFeedback}
                disabled={previewingFeedback || !feedbackContent.trim()}
              >
                <ClipboardCheck className="mr-2 h-4 w-4" />
                {previewingFeedback ? 'Checking...' : 'Preview triage'}
              </Button>
              <Button
                onClick={submitFeedback}
                disabled={feedbackSubmitting || !feedbackContent.trim()}
                className="bg-blue-700 hover:bg-blue-800 text-white"
              >
                <Send className="mr-2 h-4 w-4" />
                {feedbackSubmitting ? 'Sending...' : 'Send feedback'}
              </Button>
            </div>
            {capturePlan && (
              <div className="rounded-md border border-blue-100 bg-blue-50 p-4 text-sm text-slate-700">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{capturePlan.capture_summary.priority}</Badge>
                  <Badge variant="outline">{capturePlan.capture_summary.assignee}</Badge>
                  <Badge variant="outline">{capturePlan.status}</Badge>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="font-semibold text-slate-900">Roadmap need</div>
                    <div>{capturePlan.capture_summary.linked_need_id ?? 'unmapped'}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Release gates</div>
                    <div>{capturePlan.capture_summary.release_gate_links.join(', ') || 'none'}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Missing fields</div>
                    <div>{capturePlan.capture_summary.missing_required_fields.join(', ') || 'none'}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Privacy boundary</div>
                    <div>
                      raw feedback returned: {String(capturePlan.privacy_boundary.returns_raw_feedback_text)} · model
                      calls: {String(capturePlan.privacy_boundary.calls_ai_model)}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {submittedFeedback && (
              <div className="rounded-md border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-800">
                Submitted #{submittedFeedback.id ?? 'new'} · {submittedFeedback.priority ?? 'triaged'} ·{' '}
                {submittedFeedback.assignee ?? 'assigned'} · {submittedFeedback.status ?? 'open'}
              </div>
            )}
          </CardContent>
        </Card>

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
