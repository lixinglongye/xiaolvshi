import { useState } from 'react';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Copy, Download, FileText, Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import { client } from '@/lib/api';
import { createPlanSession, generatePlanDraft, type PlanModeSession } from '@/lib/caseApi';
import {
  useI18n,
  DOC_TYPES,
  ROLE_TYPES,
  docTypeLabel,
  roleLabel,
  LEGAL_DRAFT_TYPES,
} from '@/contexts/I18nContext';

export default function GeneratePage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t, lang } = useI18n();
  const [docType, setDocType] = useState('lease');
  const [role, setRole] = useState('party_a');
  const [title, setTitle] = useState('');
  const [partyA, setPartyA] = useState('');
  const [partyB, setPartyB] = useState('');
  const [subject, setSubject] = useState('');
  const [amount, setAmount] = useState('');
  const [period, setPeriod] = useState('');
  const [facts, setFacts] = useState('');
  const [claims, setClaims] = useState('');
  const [content, setContent] = useState('');
  const [draftLabel, setDraftLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanModeSession | null>(null);
  const [planKey, setPlanKey] = useState('');

  const isLegal = LEGAL_DRAFT_TYPES.includes(docType);
  const uiCopy = lang === 'zh'
    ? {
        conditions: '生成条件',
        titlePlaceholder: '例如：解除通知函',
        partyA: '甲方 / Party A',
        partyB: '乙方 / Party B',
        subject: '标的 / Subject',
        amount: '金额 / Amount',
        period: '期限 / Period',
        facts: '事实 / Facts',
        factsPlaceholder: '写清楚发生了什么、有哪些证据、对方目前的状态。',
        claims: '请求 / Claims',
        claimsPlaceholder: '写清楚你希望文书达到的结果。',
        processing: '处理中',
        checkPlan: '生成计划 / 检查缺口',
        draftWithAssumptions: '按现有信息生成带假设草稿',
        completeness: '完整',
        needMore: '需补充',
        canGenerate: '可生成',
        followups: '追问清单',
        noBlockers: '暂无阻断问题。',
        emptyTitle: '文书草稿会显示在这里',
        emptyBody: '补充事实和请求后生成，输出会带结构、关键条款、待补信息和质量提示。',
        planGapToast: 'Plan Mode 已发现关键缺口，请先确认或生成带假设草稿。',
        planReadyToast: '生成计划已就绪，请再次确认生成。',
        planDraftFailed: 'Plan Mode 草稿生成失败',
        planDraftLabel: 'Plan Mode 假设草稿',
        planDraftToast: '已按现有信息生成草稿，缺失字段已显著标注。',
        planFailed: 'Plan Mode 失败',
      }
    : {
        conditions: 'Draft conditions',
        titlePlaceholder: 'Example: termination notice',
        partyA: 'Party A / Plaintiff',
        partyB: 'Party B / Defendant',
        subject: 'Subject',
        amount: 'Amount',
        period: 'Period',
        facts: 'Facts',
        factsPlaceholder: 'Describe what happened, available evidence, and the other party’s current status.',
        claims: 'Claims',
        claimsPlaceholder: 'Describe what outcome you want the document to achieve.',
        processing: 'Processing',
        checkPlan: 'Create plan / check gaps',
        draftWithAssumptions: 'Generate an assumption-marked draft',
        completeness: 'complete',
        needMore: 'Needs more info',
        canGenerate: 'Ready to generate',
        followups: 'Follow-up questions',
        noBlockers: 'No blocking questions.',
        emptyTitle: 'The draft will appear here',
        emptyBody: 'Add facts and claims to generate a structured draft with key clauses, missing information, and quality notes.',
        planGapToast: 'Plan Mode found key gaps. Confirm them or generate an assumption-marked draft.',
        planReadyToast: 'Generation plan is ready. Confirm again to generate.',
        planDraftFailed: 'Plan Mode draft generation failed',
        planDraftLabel: 'Plan Mode assumption draft',
        planDraftToast: 'Draft generated with current information; missing fields are clearly marked.',
        planFailed: 'Plan Mode failed',
      };

  const currentPlanKey = () => JSON.stringify({ docType, role, title, partyA, partyB, subject, amount, period, facts, claims, lang });

  const buildPlanInput = () => [
    title ? `标题：${title}` : '',
    `文书类型：${docTypeLabel('zh', docType)}`,
    `用户立场：${roleLabel('zh', role)}`,
    partyA ? `甲方/原告候选：${partyA}` : '',
    partyB ? `乙方/被告候选：${partyB}` : '',
    subject ? `标的：${subject}` : '',
    amount ? `金额：${amount}` : '',
    period ? `期限：${period}` : '',
    facts ? `事实：${facts}` : '',
    claims ? `请求：${claims}` : '',
  ].filter(Boolean).join('\n');

  const createPlan = async () => {
    const key = currentPlanKey();
    const session = await createPlanSession({
      task_type: docType === 'lawsuit' || docTypeLabel('zh', docType).includes('起诉') ? 'generate_civil_complaint' : 'generate_legal_document',
      user_input: buildPlanInput(),
      document_type: docTypeLabel('zh', docType),
      context: {
        plaintiff: partyA,
        defendant: partyB,
        claims,
        key_facts: facts,
        amount_calculation: amount,
      },
    });
    setPlan(session);
    setPlanKey(key);
    return session;
  };

  const generateFinalDocument = async () => {
    setLoading(true);
    try {
      const resp = await client.apiCall.invoke({
        url: '/api/v1/deep-review/generate-document',
        method: 'POST',
        data: {
          doc_type: docTypeLabel('zh', docType),
          user_role: roleLabel('zh', role),
          title,
          input_data: {
            party_a: partyA,
            party_b: partyB,
            subject,
            amount,
            period,
            facts,
            claims,
          },
          language: lang,
        },
      });
      if (!resp?.data?.success) {
        throw new Error(resp?.data?.error || 'Generate error');
      }
      const document = resp?.data?.document;
      setContent(document?.content ?? '');
      setDraftLabel(document?.document_meta?.title ?? document?.document_meta?.doc_type ?? '');
      const warnings = document?.quality_audit?.warnings ?? [];
      if (warnings.length > 0) {
        toast.warning(warnings[0]);
      } else {
        toast.success('Generated');
      }
    } catch (e) {
      console.error(e);
      toast.error('Generate error');
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    setLoading(true);
    try {
      const key = currentPlanKey();
      let activePlan = plan;
      if (!activePlan || planKey !== key) {
        activePlan = await createPlan();
        if (activePlan.missing_required.length > 0 || activePlan.conflicts.length > 0) {
          toast.warning(uiCopy.planGapToast);
          return;
        }
        toast.success(uiCopy.planReadyToast);
        return;
      }
      if (activePlan.missing_required.length > 0 || activePlan.conflicts.length > 0) {
        const draft = await generatePlanDraft(activePlan.session_id);
        if (!draft.success) throw new Error(uiCopy.planDraftFailed);
        setContent(draft.draft.content);
        setDraftLabel(uiCopy.planDraftLabel);
        toast.warning(uiCopy.planDraftToast);
        return;
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : uiCopy.planFailed);
      return;
    } finally {
      setLoading(false);
    }
    await generateFinalDocument();
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Copied');
    } catch {
      toast.error('Copy failed');
    }
  };

  const download = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title || docType}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Layout hideFooter>
      <div className="max-w-7xl mx-auto px-4 py-8 lg:py-10">
        <div className="mb-6">
          <div className="eyebrow mb-3">Drafting workspace</div>
          <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-950">{t('generate_title')}</h1>
        </div>

        <div className="grid lg:grid-cols-[430px_1fr] gap-6 items-start">
          <Card className="surface-card lg:sticky lg:top-24">
            <CardHeader>
              <CardTitle className="text-xl tracking-tight flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-emerald-800" />
                {uiCopy.conditions}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid sm:grid-cols-2 lg:grid-cols-1 gap-4">
                <div>
                  <Label>{t('upload_doc_type')}</Label>
                  <Select value={docType} onValueChange={setDocType}>
                    <SelectTrigger className="mt-1 bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DOC_TYPES.map((d) => (
                        <SelectItem key={d} value={d}>
                          {docTypeLabel(lang, d)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>{t('upload_role')}</Label>
                  <Select value={role} onValueChange={setRole}>
                    <SelectTrigger className="mt-1 bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLE_TYPES.map((r) => (
                        <SelectItem key={r} value={r}>
                          {roleLabel(lang, r)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label>{t('upload_doc_title')}</Label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 bg-white" placeholder={uiCopy.titlePlaceholder} />
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <Label>{uiCopy.partyA}</Label>
                  <Input value={partyA} onChange={(e) => setPartyA(e.target.value)} className="mt-1 bg-white" />
                </div>
                <div>
                  <Label>{uiCopy.partyB}</Label>
                  <Input value={partyB} onChange={(e) => setPartyB(e.target.value)} className="mt-1 bg-white" />
                </div>
                <div>
                  <Label>{uiCopy.subject}</Label>
                  <Input value={subject} onChange={(e) => setSubject(e.target.value)} className="mt-1 bg-white" />
                </div>
                <div>
                  <Label>{uiCopy.amount}</Label>
                  <Input value={amount} onChange={(e) => setAmount(e.target.value)} className="mt-1 bg-white" />
                </div>
                <div className="sm:col-span-2">
                  <Label>{uiCopy.period}</Label>
                  <Input value={period} onChange={(e) => setPeriod(e.target.value)} className="mt-1 bg-white" />
                </div>
              </div>
              <div>
                <Label>{uiCopy.facts}</Label>
                <Textarea rows={4} value={facts} onChange={(e) => setFacts(e.target.value)} className="mt-1 bg-white" placeholder={uiCopy.factsPlaceholder} />
              </div>
              <div>
                <Label>{uiCopy.claims}</Label>
                <Textarea rows={3} value={claims} onChange={(e) => setClaims(e.target.value)} className="mt-1 bg-white" placeholder={uiCopy.claimsPlaceholder} />
              </div>
              <Button onClick={submit} disabled={loading} className="w-full quiet-button rounded-full">
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" />{uiCopy.processing}</>
                ) : !plan || planKey !== currentPlanKey() ? (
                  uiCopy.checkPlan
                ) : plan.missing_required.length > 0 || plan.conflicts.length > 0 ? (
                  uiCopy.draftWithAssumptions
                ) : (
                  t('generate_submit')
                )}
              </Button>
            </CardContent>
          </Card>

          <div className="space-y-4">
            {plan && planKey === currentPlanKey() && (
              <Card className="surface-card">
                <CardHeader className="border-b border-slate-200/80">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Sparkles className="w-4 h-4 text-emerald-800" />
                    Plan Mode
                    <Badge variant="outline">{Math.round(plan.completeness_score * 100)}% {uiCopy.completeness}</Badge>
                    {plan.missing_required.length ? <Badge className="bg-amber-100 text-amber-900">{uiCopy.needMore}</Badge> : <Badge className="bg-emerald-50 text-emerald-800">{uiCopy.canGenerate}</Badge>}
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 p-4 md:grid-cols-3">
                  <div className="md:col-span-2">
                    <p className="text-sm leading-6 text-slate-700">{plan.understanding}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(plan.generation_plan.structure || []).map((item) => <Badge key={item} variant="secondary">{item}</Badge>)}
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="font-medium text-slate-950">{uiCopy.followups}</div>
                    {plan.questions.length ? plan.questions.slice(0, 6).map((q) => (
                      <div key={q.question_id} className="rounded-md border border-slate-200 bg-white p-2">
                        <div className="font-medium text-slate-800">{q.question}</div>
                        <div className="mt-1 text-xs text-slate-500">{q.why_needed}</div>
                      </div>
                    )) : <div className="text-slate-500">{uiCopy.noBlockers}</div>}
                  </div>
                </CardContent>
              </Card>
            )}
            <Card className="surface-card min-h-[620px]">
              <CardHeader className="flex flex-row items-center justify-between gap-3 border-b border-slate-200/80">
                <CardTitle className="flex items-center gap-2 text-xl tracking-tight">
                  <FileText className="w-5 h-5 text-emerald-800" />
                  {title || docTypeLabel(lang, docType)}
                  {isLegal && <Badge className="bg-amber-100 text-amber-900 border border-amber-200">{draftLabel || t('draft_label')}</Badge>}
                </CardTitle>
                {content && (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="soft-button rounded-full" onClick={copy}>
                      <Copy className="w-4 h-4" /> {t('copy')}
                    </Button>
                    <Button size="sm" variant="outline" className="soft-button rounded-full" onClick={download}>
                      <Download className="w-4 h-4" /> {t('download_txt')}
                    </Button>
                  </div>
                )}
              </CardHeader>
              <CardContent className="p-0">
                {content ? (
                  <pre className="whitespace-pre-wrap text-sm bg-white p-6 font-sans leading-7 text-slate-800">
                    {content}
                  </pre>
                ) : (
                  <div className="min-h-[520px] flex items-center justify-center px-6 text-center">
                    <div className="max-w-sm">
                      <div className="w-12 h-12 rounded-lg bg-emerald-50 mx-auto mb-4 flex items-center justify-center">
                        <FileText className="w-6 h-6 text-emerald-800" />
                      </div>
                      <div className="font-medium text-slate-950 mb-2">{uiCopy.emptyTitle}</div>
                      <p className="text-sm leading-6 text-slate-500">{uiCopy.emptyBody}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
            <DisclaimerBanner />
          </div>
        </div>
      </div>
    </Layout>
  );
}
