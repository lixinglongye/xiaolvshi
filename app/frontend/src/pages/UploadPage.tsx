import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Upload as UploadIcon, AlertTriangle, CheckCircle2, Clock3, FileCheck, Loader2, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import { client } from '@/lib/api';
import {
  getUploadedDocumentAnalysisStatus,
  startUploadedDocumentAnalysis,
  type AnalyzeUploadedDocumentStatusResponse,
  } from '@/lib/deepReviewApi';
import { createPlanSession, submitPlanAnswers, type PlanModeSession } from '@/lib/caseApi';
import { useI18n, DOC_TYPES, ROLE_TYPES, docTypeLabel, roleLabel } from '@/contexts/I18nContext';

type ReviewPhase = 'idle' | 'uploading' | 'creating' | 'queued' | 'extracting' | 'analyzing' | 'completed' | 'failed';
type PlanQuestion = PlanModeSession['questions'][number];
type PlanAnswerPayload = { question_id?: string; field: string; value: string };

function mergePlanAnswerPayloads(base: PlanAnswerPayload[], updates: PlanAnswerPayload[]) {
  const merged = [...base];
  updates.forEach((answer) => {
    const existingIndex = merged.findIndex((item) => (
      (answer.question_id && item.question_id === answer.question_id) || item.field === answer.field
    ));
    if (existingIndex >= 0) {
      merged[existingIndex] = answer;
    } else {
      merged.push(answer);
    }
  });
  return merged;
}

function planAnswersToFacts(answers: PlanAnswerPayload[]) {
  return answers
    .filter((answer) => answer.value.trim())
    .map((answer) => `${answer.field}：${answer.value.trim()}`);
}

const POLL_INTERVAL_MS = 3000;
const PAGE_WAIT_TIMEOUT_MS = 20 * 60 * 1000;

const reviewSteps: Array<{ phase: ReviewPhase; label: string }> = [
  { phase: 'uploading', label: '上传' },
  { phase: 'creating', label: '建档' },
  { phase: 'extracting', label: '解析/OCR' },
  { phase: 'analyzing', label: '法律审查' },
  { phase: 'completed', label: '报告' },
];

const phaseOrder: ReviewPhase[] = ['idle', 'uploading', 'creating', 'queued', 'extracting', 'analyzing', 'completed', 'failed'];

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function formatElapsed(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${String(rest).padStart(2, '0')}`;
}

function mapStatusToPhase(status: string): ReviewPhase {
  if (status === 'queued') return 'queued';
  if (status === 'extracting') return 'extracting';
  if (status === 'analyzing') return 'analyzing';
  if (status === 'completed') return 'completed';
  if (status === 'failed') return 'failed';
  return 'queued';
}

function progressForPhase(phase: ReviewPhase, elapsedSeconds: number) {
  if (phase === 'uploading') return 8;
  if (phase === 'creating') return 18;
  if (phase === 'queued') return 28;
  if (phase === 'extracting') return Math.min(54, 32 + elapsedSeconds * 0.45);
  if (phase === 'analyzing') return Math.min(92, 56 + elapsedSeconds * 0.12);
  if (phase === 'completed') return 100;
  if (phase === 'failed') return 100;
  return 0;
}

export default function UploadPage() {
  return (
    <AuthGuard>
      <UploadInner />
    </AuthGuard>
  );
}

function UploadInner() {
  const navigate = useNavigate();
  const { t, lang } = useI18n();

  const [agreeTerms, setAgreeTerms] = useState(false);
  const [agreePrivacy, setAgreePrivacy] = useState(false);
  const [agreeDisc, setAgreeDisc] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>('lease');
  const [role, setRole] = useState<string>('party_a');
  const [title, setTitle] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [reviewPhase, setReviewPhase] = useState<ReviewPhase>('idle');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [activeDocumentId, setActiveDocumentId] = useState<number | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanModeSession | null>(null);
  const [planKey, setPlanKey] = useState('');
  const [planAnswers, setPlanAnswers] = useState<Record<string, string>>({});
  const [savedPlanAnswers, setSavedPlanAnswers] = useState<PlanAnswerPayload[]>([]);
  const [planUpdateMessage, setPlanUpdateMessage] = useState('');
  const [planPanelCollapsed, setPlanPanelCollapsed] = useState(false);
  const [planSubmitting, setPlanSubmitting] = useState(false);
  const [assumptionAccepted, setAssumptionAccepted] = useState(false);
  const [liveStatus, setLiveStatus] = useState<AnalyzeUploadedDocumentStatusResponse | null>(null);

  const ready = agreeTerms && agreePrivacy && agreeDisc && file && title.trim();
  const progress = progressForPhase(reviewPhase, elapsedSeconds);
  const copy = lang === 'zh'
    ? {
        intro: '上传 PDF、DOCX 或 TXT，系统会先解析正文和 OCR，再按文书类型生成专业审查报告。',
        filePrompt: '选择或拖入文书文件',
        fileHelp: 'PDF / DOCX / TXT · OCR 可处理扫描件',
        selected: '已选择',
        titlePlaceholder: '例如：张三与李四 房屋租赁合同',
        planCompleteness: '完整',
        needsConfirm: '需确认缺口',
        canReview: '可审查',
        processing: '处理中',
        makePlan: '生成审查计划',
        updatePlan: '保存并开始审查',
        updatingPlan: '正在进入下一步',
        answerPlaceholder: '在这里补充你的真实情况，系统会重新生成审查计划。',
        planSaved: '补充信息已保存，系统已重新评估审查计划。',
        planCollapsedTitle: '审查计划已确认',
        planCollapsedDetail: '系统会按已补充信息继续审查；剩余缺口将作为待补事实写入报告。',
        editPlan: '展开修改',
        savedAnswer: '已保存',
        needsMoreDetail: '仍需补充',
        planBlocked: '请先回答 Plan Mode 问题，或勾选“按当前假设审查”。',
        assumptionConfirm: '我确认暂不补充，按当前假设审查',
        startWithAssumptions: '按当前假设开始审查',
        startWithSavedPlan: '按已补充信息开始审查',
        elapsed: '已用时',
        longReviewNote: '深度审查会比普通摘要慢很多。短合同通常 1-3 分钟，扫描件或 20 页以上 PDF 可能需要更久；完成后会自动跳转到报告页。',
        documentId: '文档编号',
        unfinished: '审查未完成',
        coverageTitle: '本次审查会覆盖',
        coverage: ['文书类型专项策略', '长文档切分与关键条款定位', 'OCR 低文本页补识别', '法律依据与实务清单校验', '可复制修改条款和证据建议'],
        phaseLabels: {
          idle: { title: '等待提交', detail: '请选择文书并确认协议。' },
          uploading: { title: '正在上传文件', detail: '文件正在保存到本地/对象存储。' },
          creating: { title: '正在建立文档记录', detail: '系统正在保存文书基础信息。' },
          queued: { title: '后台审查已启动', detail: '任务已进入队列，页面会自动轮询结果。' },
          extracting: { title: '正在解析正文和 OCR', detail: 'PDF 文本层优先，扫描页会触发 OCR 识别。' },
          analyzing: { title: '正在深度法律审查', detail: '模型正在生成风险矩阵、法律依据和修改条款。' },
          completed: { title: '报告已生成', detail: '正在打开深度审查报告。' },
          failed: { title: '审查失败', detail: '请查看错误信息后重试。' },
        },
        reviewSteps: ['上传', '建档', '解析/OCR', '法律审查', '报告'],
      }
    : {
        intro: 'Upload a PDF, DOCX, or TXT file. The system extracts text and OCR first, then generates a professional review by document type.',
        filePrompt: 'Choose or drop a legal document',
        fileHelp: 'PDF / DOCX / TXT · OCR can handle scanned pages',
        selected: 'selected',
        titlePlaceholder: 'Example: Smith v. Acme lease agreement',
        planCompleteness: 'complete',
        needsConfirm: 'Needs confirmation',
        canReview: 'Ready to review',
        processing: 'Processing',
        makePlan: 'Create review plan',
        updatePlan: 'Save and start review',
        updatingPlan: 'Moving to next step',
        answerPlaceholder: 'Add the real facts here. The system will rebuild the review plan.',
        planSaved: 'Plan answers were saved and the review plan was reassessed.',
        planCollapsedTitle: 'Review plan confirmed',
        planCollapsedDetail: 'The review will continue with the saved facts; remaining gaps will be included as pending facts.',
        editPlan: 'Edit plan',
        savedAnswer: 'Saved',
        needsMoreDetail: 'Needs more detail',
        planBlocked: 'Answer the Plan Mode questions first, or explicitly confirm reviewing with assumptions.',
        assumptionConfirm: 'I confirm reviewing with current assumptions',
        startWithAssumptions: 'Start review with current assumptions',
        startWithSavedPlan: 'Start review with saved facts',
        elapsed: 'Elapsed',
        longReviewNote: 'Deep review takes longer than a quick summary. Short contracts usually take 1-3 minutes; scanned files or PDFs over 20 pages may take longer. The page opens the report automatically when ready.',
        documentId: 'Document ID',
        unfinished: 'Review not completed',
        coverageTitle: 'This review covers',
        coverage: ['Document-type review strategy', 'Long-document splitting and key clause location', 'OCR fallback for low-text pages', 'Legal basis and practice checklist validation', 'Copy-ready revisions and evidence suggestions'],
        phaseLabels: {
          idle: { title: 'Waiting to submit', detail: 'Choose a document and confirm the agreements.' },
          uploading: { title: 'Uploading file', detail: 'The file is being saved to storage.' },
          creating: { title: 'Creating document record', detail: 'The system is saving document metadata.' },
          queued: { title: 'Background review started', detail: 'The task is queued and this page will poll for results.' },
          extracting: { title: 'Extracting text and OCR', detail: 'Text layers are used first; scanned pages trigger OCR.' },
          analyzing: { title: 'Running deep legal review', detail: 'The model is generating risks, legal basis, and revised clauses.' },
          completed: { title: 'Report generated', detail: 'Opening the deep review report.' },
          failed: { title: 'Review failed', detail: 'Check the error details and try again.' },
        },
        reviewSteps: ['Upload', 'Record', 'OCR', 'Review', 'Report'],
      };
  const currentPlanKey = () => JSON.stringify({ name: file?.name || '', size: file?.size || 0, docType, role, title, lang });
  const currentPhase = copy.phaseLabels[reviewPhase];
  const planNeedsInput = Boolean(plan && planKey === currentPlanKey() && (plan.missing_required.length || plan.conflicts.length));
  const hasSavedPlanInput = savedPlanAnswers.length > 0;
  const progressDetail = liveStatus?.progress?.detail || currentPhase.detail;
  const progressStageName = liveStatus?.progress?.stage_name || currentPhase.title;
  const liveProgressValue = liveStatus?.progress?.percent;
  const extractionQuality = liveStatus?.extraction?.extraction_quality;
  const preflightProgress = liveStatus?.progress?.preflight_status
      ? {
          status: liveStatus.progress.preflight_status,
          strategy: liveStatus.progress.preflight_strategy_id,
          task: liveStatus.progress.recommended_task,
          model: liveStatus.progress.recommended_model,
          privacyRisk: liveStatus.progress.privacy_risk_level,
          privacyCount: liveStatus.progress.privacy_finding_count,
        }
      : null;

  useEffect(() => {
    if (!submitting) return undefined;
    const timer = window.setInterval(() => {
      setElapsedSeconds((value) => value + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [submitting]);

  useEffect(() => {
    setAssumptionAccepted(false);
    setPlanAnswers({});
    setSavedPlanAnswers([]);
    setPlanUpdateMessage('');
    setPlanPanelCollapsed(false);
    setLiveStatus(null);
  }, [file, docType, role, title, lang]);

  const waitForAnalysisCompletion = async (documentId: number): Promise<AnalyzeUploadedDocumentStatusResponse> => {
    const startedAt = Date.now();
    let lastWarning = '';

    while (Date.now() - startedAt < PAGE_WAIT_TIMEOUT_MS) {
      const status = await getUploadedDocumentAnalysisStatus(documentId);
      if (!status.success) {
        throw new Error(status.error || '审查状态查询失败');
      }

      setLiveStatus(status);
      const nextPhase = mapStatusToPhase(status.status);
      setReviewPhase(nextPhase);

      const warnings = status.extraction?.warnings || [];
      if (warnings.length && warnings[0] !== lastWarning) {
        lastWarning = warnings[0];
        toast.warning(warnings[0], { duration: 6000 });
      }

      if (status.status === 'completed' && status.report_id) {
        return status;
      }

      if (status.status === 'failed') {
        throw new Error(status.error || '深度审查失败');
      }

      await sleep(POLL_INTERVAL_MS);
    }

    throw new Error('审查仍在后台运行，当前页面等待已超过 20 分钟。请稍后在文档列表或报告页刷新查看。');
  };

  const createReviewPlan = async () => {
    const key = currentPlanKey();
    const session = await createPlanSession({
      task_type: 'contract_review',
      document_type: docTypeLabel('zh', docType),
      user_input: [
        `文书标题：${title}`,
        `文书类型：${docTypeLabel('zh', docType)}`,
        `审查立场：${roleLabel('zh', role)}`,
        file ? `文件名：${file.name}` : '',
      ].filter(Boolean).join('\n'),
      context: {
        user_role: roleLabel('zh', role),
        contract_type: docTypeLabel('zh', docType),
        transaction_background: title,
      },
    });
    setPlan(session);
    setPlanKey(key);
    setSavedPlanAnswers([]);
    setPlanUpdateMessage('');
    setPlanPanelCollapsed(false);
    return session;
  };

  const savedPlanAnswerMap = savedPlanAnswers.reduce<Record<string, string>>((acc, answer) => {
    if (answer.question_id) acc[answer.question_id] = answer.value;
    acc[answer.field] = answer.value;
    return acc;
  }, {});

  const answerForQuestion = (question: PlanQuestion) => (
    planAnswers[question.question_id]
    ?? planAnswers[question.field]
    ?? savedPlanAnswerMap[question.question_id]
    ?? savedPlanAnswerMap[question.field]
    ?? ''
  );

  const questionHasSavedAnswer = (question: PlanQuestion) => {
    const value = answerForQuestion(question).trim();
    return Boolean(value && (savedPlanAnswerMap[question.question_id] === value || savedPlanAnswerMap[question.field] === value));
  };

  const setQuestionAnswer = (question: PlanQuestion, value: string) => {
    setPlanAnswers((prev) => ({
      ...prev,
      [question.question_id]: value,
      [question.field]: value,
    }));
  };

  const collectPlanAnswers = () => {
    if (!plan) return [];
    return plan.questions
      .map((question) => ({
        question_id: question.question_id,
        field: question.field,
        value: answerForQuestion(question).trim(),
      }))
      .filter((answer) => (
        answer.value
        && savedPlanAnswerMap[answer.question_id] !== answer.value
        && savedPlanAnswerMap[answer.field] !== answer.value
      ));
  };
  const unsavedPlanItems = collectPlanAnswers().length;

  const savePlanAnswers = async (providedAnswers?: PlanAnswerPayload[]) => {
    if (!plan) return null;
    const answers = providedAnswers ?? collectPlanAnswers();
    if (!answers.length) {
      toast.warning(copy.planBlocked);
      return null;
    }
    setPlanSubmitting(true);
    try {
      const updated = await submitPlanAnswers(plan.session_id, answers);
      const mergedAnswers = mergePlanAnswerPayloads(savedPlanAnswers, answers);
      setPlan(updated);
      setPlanKey(currentPlanKey());
      setAssumptionAccepted(false);
      setPlanAnswers((prev) => {
        const next = { ...prev };
        answers.forEach((answer) => {
          if (answer.question_id) next[answer.question_id] = answer.value;
          next[answer.field] = answer.value;
        });
        return next;
      });
      setSavedPlanAnswers(mergedAnswers);
      setPlanUpdateMessage(copy.planSaved);
      setPlanPanelCollapsed(true);
      toast.success(lang === 'zh' ? '审查计划已更新' : 'Review plan updated');
      return { session: updated, savedAnswers: mergedAnswers };
    } finally {
      setPlanSubmitting(false);
    }
  };

  const handleSubmit = async () => {
    if (!file || !ready) return;
    setSubmitting(true);
    setReviewPhase('uploading');
    setElapsedSeconds(0);
    setActiveDocumentId(null);
    setAnalysisError(null);
    setLiveStatus(null);
    try {
      let activePlan = plan;
      let planFactsForReview = savedPlanAnswers;
      if (!activePlan || planKey !== currentPlanKey()) {
        activePlan = await createReviewPlan();
        if (activePlan.missing_required.length || activePlan.conflicts.length) {
          toast.warning(lang === 'zh' ? '合同审查 Plan Mode 已生成，请先补充缺口。' : 'Review Plan Mode is ready. Please fill the gaps first.');
          setReviewPhase('idle');
          return;
        }
      } else if (activePlan.missing_required.length || activePlan.conflicts.length) {
        const answersToSave = collectPlanAnswers();
        if (answersToSave.length) {
          const updatedPlan = await savePlanAnswers(answersToSave);
          if (updatedPlan) {
            activePlan = updatedPlan.session;
            planFactsForReview = updatedPlan.savedAnswers;
          }
        }
        if (activePlan && (activePlan.missing_required.length || activePlan.conflicts.length) && !assumptionAccepted && !planFactsForReview.length) {
          toast.warning(copy.planBlocked);
          setReviewPhase('idle');
          return;
        }
      }
      const upload = await client.storage.upload({ bucket_name: 'law-radar-docs', file });
      const uploadResult = upload as { data?: { object_key?: string }; object_key?: string } | null | undefined;
      const objectKey = uploadResult?.data?.object_key ?? uploadResult?.object_key ?? '';
      setReviewPhase('creating');
      const created = await client.entities.documents.create({
        data: {
          title,
          doc_type: docType,
          user_role: role,
          file_key: objectKey,
          file_name: file.name,
          file_size: file.size,
          mime_type: file.type || 'application/octet-stream',
          status: 'processing',
          language: lang,
        },
      });
      const docId = created?.data?.id;
      if (!docId) {
        toast.error('Upload failed');
        return;
      }
      setActiveDocumentId(Number(docId));
      setReviewPhase('queued');
      toast.info(lang === 'zh' ? '后台深度审查已启动，页面会自动刷新进度。' : 'Background deep review started. This page will refresh progress automatically.');
      const residualPlanGaps = activePlan.missing_required || [];
      const planKnownFacts = [
        ...planAnswersToFacts(planFactsForReview),
        ...(activePlan.assumptions_if_generate_now || []).map((item) => `系统假设：${item}`),
      ];
      const started = await startUploadedDocumentAnalysis({
        document_id: Number(docId),
        document_type: docTypeLabel('zh', docType),
        user_role: roleLabel('zh', role),
        review_goal: residualPlanGaps.length
          ? `Plan Mode 已补充信息审查；剩余缺口：${residualPlanGaps.join('、')}`
          : '签署前审查',
        jurisdiction: '中国大陆',
        known_facts: planKnownFacts,
        enable_ocr: true,
      });
      if (!started.success) {
        const message = started.error || '深度审查启动失败';
        setAnalysisError(message);
        toast.error(message);
        return;
      }
      const analysis = await waitForAnalysisCompletion(Number(docId));
      if (!analysis.report_id) {
        throw new Error('报告生成成功但缺少 report_id');
      }
      setReviewPhase('completed');
      toast.success(lang === 'zh' ? '深度审查报告已生成' : 'Deep review report generated');
      navigate(`/deep-report/${analysis.report_id}`);
    } catch (e) {
      console.error(e);
      const detail =
        (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ||
        (e as Error)?.message ||
        'Upload error';
      setReviewPhase('failed');
      setAnalysisError(detail);
      toast.error(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-10 lg:py-14">
        <div className="grid lg:grid-cols-[1fr_390px] gap-6 items-start">
          <div className="space-y-6">
            <div>
              <div className="eyebrow mb-3">Deep review</div>
              <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-950 mb-3">{t('upload_title')}</h1>
              <p className="max-w-2xl text-slate-600 leading-7">{copy.intro}</p>
            </div>

            <Alert className="border-amber-200 bg-amber-50/80 text-amber-950">
              <AlertTriangle className="h-4 w-4 text-amber-700" />
              <AlertTitle>Privacy</AlertTitle>
              <AlertDescription className="text-sm text-amber-900">
                {t('sensitive_warning')}
              </AlertDescription>
            </Alert>

            <Card className="surface-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl tracking-tight">
                  <UploadIcon className="w-5 h-5 text-emerald-800" /> {t('upload_choose')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <label className="block rounded-lg border border-dashed border-slate-300 bg-[#fbfbf8] p-5 hover:border-slate-400 transition-colors cursor-pointer">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                      <UploadIcon className="w-5 h-5 text-slate-700" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-slate-950">{file ? file.name : copy.filePrompt}</div>
                      <div className="text-xs text-slate-500 mt-1">{copy.fileHelp}</div>
                      {file && (
                        <p className="text-xs text-emerald-800 mt-2">
                          {(file.size / 1024).toFixed(1)} KB {copy.selected}
                        </p>
                      )}
                    </div>
                  </div>
                  <Input
                    type="file"
                    accept=".docx,.pdf,.txt"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    disabled={submitting}
                    className="hidden"
                  />
                </label>

                <div>
                  <Label>{t('upload_doc_title')}</Label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={submitting}
                    className="mt-1 bg-white"
                    placeholder={copy.titlePlaceholder}
                  />
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <Label>{t('upload_doc_type')}</Label>
                    <Select value={docType} onValueChange={setDocType} disabled={submitting}>
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
                    <Select value={role} onValueChange={setRole} disabled={submitting}>
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

                {plan && planKey === currentPlanKey() && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-slate-950">Plan Mode</span>
                      <Badge variant="outline">{Math.round(plan.completeness_score * 100)}% {copy.planCompleteness}</Badge>
                      {plan.missing_required.length ? <Badge className="bg-amber-100 text-amber-900">{copy.needsConfirm}</Badge> : <Badge className="bg-emerald-50 text-emerald-800">{copy.canReview}</Badge>}
                    </div>
                    {planPanelCollapsed ? (
                      <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs leading-5 text-emerald-950">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-2">
                            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-800" />
                            <div>
                              <div className="font-semibold">{copy.planCollapsedTitle}</div>
                              <div className="mt-1 text-emerald-800">
                                {copy.planCollapsedDetail}
                                {savedPlanAnswers.length ? ` ${lang === 'zh' ? '已保存' : 'Saved'} ${savedPlanAnswers.length} ${lang === 'zh' ? '项。' : 'answer(s).'}` : ''}
                              </div>
                            </div>
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            disabled={submitting || planSubmitting}
                            className="h-7 shrink-0 rounded-full bg-white px-3 text-xs"
                            onClick={() => setPlanPanelCollapsed(false)}
                          >
                            {copy.editPlan}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="text-xs leading-5 text-slate-600">{plan.understanding}</p>
                        {planUpdateMessage ? (
                          <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs leading-5 text-emerald-900">
                            {planUpdateMessage}
                          </div>
                        ) : null}
                        {plan.conflicts.length ? (
                          <div className="rounded-xl border border-red-100 bg-red-50 p-3 text-xs text-red-900">
                            {plan.conflicts.map((conflict, index) => (
                              <div key={`${conflict.field || 'conflict'}-${index}`}>
                                {conflict.field ? `${conflict.field}：` : ''}{conflict.message}
                              </div>
                            ))}
                          </div>
                        ) : null}
                        {plan.questions.length ? (
                          <div className="space-y-3">
                            {plan.questions.slice(0, 6).map((question) => (
                              <div key={question.question_id} className="rounded-xl bg-slate-50 p-3 text-xs">
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <div className="font-medium text-slate-900">{question.question}</div>
                                    <div className="mt-1 text-slate-500">{question.why_needed}</div>
                                  </div>
                                  <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
                                    {questionHasSavedAnswer(question) ? (
                                      <Badge className="bg-emerald-50 text-emerald-800">{copy.savedAnswer}</Badge>
                                    ) : null}
                                    <Badge variant="outline">
                                      {question.priority === 'required' ? (lang === 'zh' ? '必填' : 'Required') : (lang === 'zh' ? '可选' : 'Optional')}
                                    </Badge>
                                  </div>
                                </div>
                                {question.options?.length ? (
                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {question.options.map((option) => {
                                      const selected = answerForQuestion(question) === option;
                                      return (
                                        <button
                                          key={option}
                                          type="button"
                                          disabled={submitting || planSubmitting}
                                          onClick={() => setQuestionAnswer(question, option)}
                                          className={[
                                            'rounded-full border px-3 py-1.5 text-xs transition-all',
                                            selected
                                              ? 'border-slate-950 bg-slate-950 text-white'
                                              : 'border-slate-200 bg-white text-slate-700 hover:border-slate-400',
                                          ].join(' ')}
                                        >
                                          {option}
                                        </button>
                                      );
                                    })}
                                  </div>
                                ) : (
                                  <Textarea
                                    value={answerForQuestion(question)}
                                    onChange={(event) => setQuestionAnswer(question, event.target.value)}
                                    disabled={submitting || planSubmitting}
                                    placeholder={copy.answerPlaceholder}
                                    className="mt-3 min-h-[76px] resize-y bg-white text-sm"
                                  />
                                )}
                                {questionHasSavedAnswer(question) ? (
                                  <div className="mt-2 text-[11px] leading-4 text-slate-500">{copy.needsMoreDetail}</div>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : null}
                        {plan.assumptions_if_generate_now.length ? (
                          <label className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-950">
                            <Checkbox
                              checked={assumptionAccepted}
                              onCheckedChange={(value) => setAssumptionAccepted(Boolean(value))}
                              disabled={submitting || planSubmitting}
                              className="mt-0.5"
                            />
                            <span>
                              {copy.assumptionConfirm}
                              <span className="mt-1 block text-amber-800">
                                {plan.assumptions_if_generate_now.slice(0, 2).join('；')}
                              </span>
                            </span>
                          </label>
                        ) : null}
                        {plan.questions.length ? (
                          <Button
                            type="button"
                            variant="outline"
                            className="w-full rounded-full"
                            disabled={submitting || planSubmitting || !unsavedPlanItems}
                            onClick={handleSubmit}
                          >
                            {planSubmitting || submitting ? <><Loader2 className="w-4 h-4 animate-spin" />{copy.updatingPlan}</> : copy.updatePlan}
                          </Button>
                        ) : null}
                      </>
                    )}
                  </div>
                )}

                <div className="space-y-2 rounded-lg border border-slate-200 bg-[#fbfbf8] p-4">
                  {[{
                    checked: agreeTerms,
                    set: setAgreeTerms,
                    label: t('agree_terms'),
                  }, {
                    checked: agreePrivacy,
                    set: setAgreePrivacy,
                    label: t('agree_privacy'),
                  }, {
                    checked: agreeDisc,
                    set: setAgreeDisc,
                    label: t('agree_disclaimer'),
                  }].map((item) => (
                    <label key={item.label} className="flex items-start gap-2 text-sm cursor-pointer text-slate-700">
                      <Checkbox
                        checked={item.checked}
                        onCheckedChange={(v) => item.set(Boolean(v))}
                        disabled={submitting}
                        className="mt-0.5"
                      />
                      <span>{item.label}</span>
                    </label>
                  ))}
                </div>

                <Button
                  className="w-full quiet-button rounded-full"
                  disabled={!ready || submitting || planSubmitting || (planNeedsInput && !unsavedPlanItems && !assumptionAccepted && !hasSavedPlanInput)}
                  onClick={handleSubmit}
                >
                  {submitting
                    ? <><Loader2 className="w-4 h-4 animate-spin" />{copy.processing}</>
                    : !plan || planKey !== currentPlanKey()
                      ? copy.makePlan
                      : planNeedsInput && unsavedPlanItems
                        ? (lang === 'zh' ? '保存补充信息并开始审查' : 'Save answers and start review')
                        : planNeedsInput && hasSavedPlanInput
                          ? copy.startWithSavedPlan
                        : planNeedsInput && assumptionAccepted
                          ? copy.startWithAssumptions
                          : planNeedsInput
                            ? copy.planBlocked
                            : t('upload_submit')}
                </Button>

                {(submitting || reviewPhase === 'failed') && (
                  <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                          {reviewPhase === 'completed' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                          ) : reviewPhase === 'failed' ? (
                            <AlertTriangle className="w-4 h-4 text-red-700" />
                          ) : (
                            <Loader2 className="w-4 h-4 animate-spin text-emerald-800" />
                          )}
                          {progressStageName}
                        </div>
                        <p className="mt-1 text-xs text-slate-500">{progressDetail}</p>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-slate-500">
                        <Clock3 className="w-3.5 h-3.5" />
                        {copy.elapsed} {formatElapsed(elapsedSeconds)}
                      </div>
                    </div>

                    <Progress value={typeof liveProgressValue === 'number' ? liveProgressValue : progress} className="h-2 bg-slate-100" />

                    {preflightProgress && (
                      <div className="grid gap-2 rounded-lg border border-emerald-100 bg-emerald-50/70 p-3 text-xs text-emerald-950 sm:grid-cols-5">
                        <div>
                          <div className="text-[11px] font-semibold uppercase text-emerald-700">
                            {lang === 'zh' ? '规则预检' : 'Preflight'}
                          </div>
                          <Badge className="mt-1 bg-white text-emerald-800" variant="outline">
                            {preflightProgress.status}
                          </Badge>
                        </div>
                        <div>
                          <div className="text-[11px] font-semibold uppercase text-emerald-700">
                            {lang === 'zh' ? '策略' : 'Strategy'}
                          </div>
                          <div className="mt-1 break-words font-mono text-[11px]">{preflightProgress.strategy || '-'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] font-semibold uppercase text-emerald-700">
                            {lang === 'zh' ? '任务路由' : 'Task route'}
                          </div>
                          <div className="mt-1 break-words font-mono text-[11px]">{preflightProgress.task || '-'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] font-semibold uppercase text-emerald-700">
                            {lang === 'zh' ? '推荐模型' : 'Model'}
                          </div>
                          <div className="mt-1 break-words font-mono text-[11px]">{preflightProgress.model || '-'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] font-semibold uppercase text-emerald-700">
                            {lang === 'zh' ? '隐私风险' : 'Privacy'}
                          </div>
                          <div className="mt-1 break-words font-mono text-[11px]">
                            {preflightProgress.privacyRisk || 'none'} · {preflightProgress.privacyCount ?? 0}
                          </div>
                        </div>
                      </div>
                    )}

                    {extractionQuality && (
                      <div className="rounded-lg border border-sky-100 bg-sky-50/70 p-3 text-xs text-sky-950">
                        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                          <div className="font-semibold">
                            {lang === 'zh' ? '解析质量审计' : 'Extraction quality'}
                          </div>
                          <Badge
                            variant="outline"
                            className={
                              extractionQuality.status === 'pass'
                                ? 'border-emerald-200 bg-white text-emerald-800'
                                : extractionQuality.status === 'fail'
                                  ? 'border-red-200 bg-white text-red-800'
                                  : 'border-amber-200 bg-white text-amber-900'
                            }
                          >
                            {extractionQuality.status || 'unknown'} / {extractionQuality.score ?? 0}
                          </Badge>
                        </div>
                        <div className="grid gap-2 sm:grid-cols-3">
                          <div>{lang === 'zh' ? '字符/页' : 'Chars/page'}: {extractionQuality.chars_per_page ?? '-'}</div>
                          <div>{lang === 'zh' ? '低文本页' : 'Low-text pages'}: {extractionQuality.low_text_page_count ?? 0}</div>
                          <div>{lang === 'zh' ? 'OCR 页' : 'OCR pages'}: {extractionQuality.ocr_page_count ?? 0}</div>
                        </div>
                        {extractionQuality.recommended_actions?.length ? (
                          <div className="mt-2 leading-5 text-sky-900">
                            {extractionQuality.recommended_actions[0]}
                          </div>
                        ) : null}
                      </div>
                    )}

                    {liveStatus?.pipeline_preview?.length ? (
                      <div className="grid sm:grid-cols-2 gap-2">
                        {liveStatus.pipeline_preview.slice(-4).map((stage) => (
                          <div key={`${stage.stage_id}-${stage.stage_name}`} className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
                            <span className="font-medium text-slate-900">{stage.stage_name}</span>
                            <span className="ml-2 text-slate-400">{stage.status}</span>
                          </div>
                        ))}
                      </div>
                    ) : null}

                    <div className="grid grid-cols-5 gap-2">
                      {reviewSteps.map((step, index) => {
                        const currentIndex = phaseOrder.indexOf(reviewPhase);
                        const stepIndex = phaseOrder.indexOf(step.phase);
                        const done = reviewPhase !== 'failed' && (currentIndex > stepIndex || reviewPhase === 'completed');
                        const active = reviewPhase === step.phase || (reviewPhase === 'queued' && step.phase === 'extracting');
                        return (
                          <div key={step.phase} className="min-w-0">
                            <div
                              className={[
                                'mx-auto mb-1 h-7 w-7 rounded-full border flex items-center justify-center',
                                done
                                  ? 'border-emerald-700 bg-emerald-700 text-white'
                                  : active
                                    ? 'border-emerald-700 bg-emerald-50 text-emerald-800'
                                    : 'border-slate-200 bg-slate-50 text-slate-400',
                              ].join(' ')}
                            >
                              {done ? <CheckCircle2 className="w-4 h-4" /> : <span className="text-xs">{index + 1}</span>}
                            </div>
                            <div className="truncate text-center text-[11px] text-slate-500">{copy.reviewSteps[index]}</div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="rounded-md bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-600">
                      {copy.longReviewNote}
                      {activeDocumentId ? <span> {copy.documentId}: {activeDocumentId}</span> : null}
                    </div>

                    {analysisError && (
                      <Alert className="border-red-200 bg-red-50 text-red-950">
                        <AlertTriangle className="h-4 w-4 text-red-700" />
                        <AlertTitle>{copy.unfinished}</AlertTitle>
                        <AlertDescription className="text-sm text-red-900">{analysisError}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-4 lg:sticky lg:top-24">
            <Card className="surface-panel">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-800" />
                  {copy.coverageTitle}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-700">
                {copy.coverage.map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-800 shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
            <DisclaimerBanner />
          </aside>
        </div>
      </div>
    </Layout>
  );
}
