import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { ClipboardCheck, MessageSquare, Send } from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { previewFeedbackCapturePlan, type FeedbackCapturePlan } from '@/lib/feedbackApi';

type SubmittedFeedback = {
  id?: number;
  priority?: string;
  assignee?: string;
  status?: string;
};

type FeedbackCapturePanelProps = {
  title?: string;
  description?: string;
  defaultCategory?: string;
  defaultAffectedArtifactId?: string;
  lockCategory?: boolean;
  compact?: boolean;
};

const workflowOptions = [
  { value: 'general', label: 'General feedback' },
  { value: 'report_quality', label: 'Report quality' },
  { value: 'upload_pipeline', label: 'Upload or OCR' },
  { value: 'billing_access', label: 'Billing or access' },
  { value: 'template_export', label: 'Template or export' },
];

export default function FeedbackCapturePanel({
  title = 'Product feedback',
  description,
  defaultCategory = 'general',
  defaultAffectedArtifactId = '',
  lockCategory = false,
  compact = false,
}: FeedbackCapturePanelProps) {
  const [feedbackCategory, setFeedbackCategory] = useState(defaultCategory);
  const [feedbackContent, setFeedbackContent] = useState('');
  const [affectedArtifactId, setAffectedArtifactId] = useState(defaultAffectedArtifactId);
  const [accountContext, setAccountContext] = useState('');
  const [capturePlan, setCapturePlan] = useState<FeedbackCapturePlan | null>(null);
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [previewingFeedback, setPreviewingFeedback] = useState(false);
  const [submittedFeedback, setSubmittedFeedback] = useState<SubmittedFeedback | null>(null);

  useEffect(() => {
    setFeedbackCategory(defaultCategory);
    setCapturePlan(null);
    setSubmittedFeedback(null);
  }, [defaultCategory]);

  useEffect(() => {
    setAffectedArtifactId(defaultAffectedArtifactId);
    setCapturePlan(null);
    setSubmittedFeedback(null);
  }, [defaultAffectedArtifactId]);

  const clearPreview = () => {
    setCapturePlan(null);
    setSubmittedFeedback(null);
  };

  const feedbackPayload = () => ({
    category: feedbackCategory,
    content: feedbackContent,
    ...(affectedArtifactId.trim() ? { affected_artifact_id: affectedArtifactId.trim() } : {}),
    ...(accountContext.trim() ? { account_context: accountContext.trim() } : {}),
  });

  const previewFeedback = async () => {
    if (!feedbackContent.trim()) return null;
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
          resolution_note: plan?.ticket_defaults?.resolution_note,
        },
      });
      const ticket = (response?.data ?? response ?? {}) as SubmittedFeedback;
      setSubmittedFeedback(ticket);
      setFeedbackContent('');
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
    <Card className={compact ? 'border-blue-100 bg-blue-50/40' : undefined}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-700" /> {title}
        </CardTitle>
        {description && <p className="text-sm text-slate-600">{description}</p>}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Workflow</Label>
            {lockCategory ? (
              <div className="flex h-10 items-center rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700">
                {workflowOptions.find((option) => option.value === feedbackCategory)?.label ?? feedbackCategory}
              </div>
            ) : (
              <Select
                value={feedbackCategory}
                onValueChange={(value) => {
                  setFeedbackCategory(value);
                  clearPreview();
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {workflowOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
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
            rows={compact ? 3 : 4}
            value={feedbackContent}
            onChange={(event) => {
              setFeedbackContent(event.target.value);
              clearPreview();
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
  );
}
