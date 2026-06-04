import { useEffect, useMemo, useState } from 'react';
import AuthGuard from '@/components/AuthGuard';
import Layout from '@/components/Layout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertTriangle, Clipboard, ExternalLink, FileCheck, Loader2, RefreshCw, ShieldCheck, Target } from 'lucide-react';
import {
  getCaseIntakeCompleteness,
  getCaseTaskNotificationPolicy,
  getCaseTimelineDeadlineRisk,
  getCaseTeamAccessPolicy,
  getCaseWorkbenchPayload,
  getClientDeliveryRiskChecklist,
  getContinuousUpdateLedger,
  getEvidenceExhibitPackagePolicy,
  getLegalFixtureImprovementPlan,
  getLegalFixtureEvidenceBundle,
  getLegalFixtureModelMatrix,
  getLegalDocumentExportReadiness,
  getLegalDocumentTemplateMatrix,
  getLegalFixturePromptPack,
  getLegalFixtureLocalRunPackage,
  getLegalFixtureResponseNormalizerTemplate,
  getLegalFixtureResultArchive,
  getLegalFixtureRunPlan,
  getLegalFixtureRunReport,
  getLegalBenchmarkResearchRegistry,
  getLegalKnowledgeAudit,
  getLegalPublicBenchmarkSampler,
  getLegalResearchBacklog,
  getLegalReviewFixtureSmoke,
  getLegalReviewBenchmark,
  getLegalRagEvaluationPolicy,
  getLawyerReviewWorkflowPolicy,
  getMaintenanceEvidence,
  getMatterAuditRetentionPolicy,
  getOcrImportReadinessPolicy,
  getFeedbackRoadmapCatalog,
  getProductFeatureGapRadar,
  getReleaseReadiness,
  getUserNeedsRadar,
  normalizeLegalFixtureResponse,
  type CaseIntakeCompleteness,
  type CaseTaskNotificationPolicy,
  type CaseTimelineDeadlineRisk,
  type CaseTeamAccessPolicy,
  type CaseWorkbenchPayload,
  type ClientDeliveryRiskChecklist,
  type ContinuousUpdateLedger,
  type ContinuousUpdateLedgerEntry,
  type EvidenceExhibitPackagePolicy,
  type FeedbackRoadmapCatalog,
  type LawyerReviewWorkflowPolicy,
  type LegalDocumentExportReadiness,
  type LegalDocumentTemplateMatrix,
  type LegalFixtureEvidenceBundle,
  type LegalFixtureImprovementPlan,
  type LegalFixtureModelMatrix,
  type LegalFixturePromptPack,
  type LegalFixtureLocalRunPackage,
  type LegalFixtureResponseNormalizer,
  type LegalFixtureResultArchive,
  type LegalFixtureRunPlan,
  type LegalFixtureRunReport,
  type LegalBenchmarkResearchRegistry,
  type LegalKnowledgeAudit,
  type LegalPublicBenchmarkSampler,
  type LegalResearchBacklog,
  type LegalReviewBenchmark,
  type LegalReviewFixtureSmoke,
  type LegalRagEvaluationPolicy,
  type MaintenanceEvidenceProfile,
  type MaintenanceLanguage,
  type MatterAuditRetentionPolicy,
  type OcrImportReadinessPolicy,
  type ProductFeatureGapRadar,
  type ReleaseReadinessResult,
  type ReleaseValidationCommand,
  type UserNeedsRadar,
} from '@/lib/maintenanceApi';

const categoryClass: Record<string, string> = {
  benchmark: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  frontend_ui: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  model_ops: 'bg-sky-50 text-sky-800 border-sky-200',
  quality: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  review_ops: 'bg-amber-50 text-amber-900 border-amber-200',
  release_management: 'bg-red-50 text-red-800 border-red-200',
  release_evidence: 'bg-violet-50 text-violet-800 border-violet-200',
  product: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  safety: 'bg-red-50 text-red-800 border-red-200',
  user_research: 'bg-teal-50 text-teal-800 border-teal-200',
  maintenance: 'bg-stone-50 text-stone-800 border-stone-200',
};

const priorityClass: Record<string, string> = {
  critical: 'border-red-300 bg-red-100 text-red-900',
  high: 'border-red-200 bg-red-50 text-red-800',
  medium: 'border-amber-200 bg-amber-50 text-amber-900',
  info: 'border-sky-200 bg-sky-50 text-sky-800',
  low: 'border-stone-200 bg-stone-50 text-stone-700',
};

const statusClass: Record<string, string> = {
  pass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  ready: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  complete: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  parsed: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  not_run: 'border-stone-200 bg-stone-50 text-stone-700',
  template: 'border-stone-200 bg-stone-50 text-stone-700',
  uploaded: 'border-stone-200 bg-stone-50 text-stone-700',
  preflight: 'border-sky-200 bg-sky-50 text-sky-800',
  warn: 'border-amber-200 bg-amber-50 text-amber-900',
  needs_review: 'border-amber-200 bg-amber-50 text-amber-900',
  needs_attention: 'border-amber-200 bg-amber-50 text-amber-900',
  manual_review: 'border-amber-200 bg-amber-50 text-amber-900',
  ocr_needed: 'border-amber-200 bg-amber-50 text-amber-900',
  review_recommended: 'border-amber-200 bg-amber-50 text-amber-900',
  license_review_required: 'border-amber-200 bg-amber-50 text-amber-900',
  blocked: 'border-red-200 bg-red-50 text-red-800',
  missing: 'border-red-200 bg-red-50 text-red-800',
  ocr_failed: 'border-red-200 bg-red-50 text-red-800',
  sampling_ready: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  catalog_only: 'border-stone-200 bg-stone-50 text-stone-700',
  needs_escalation: 'border-red-200 bg-red-50 text-red-800',
  needs_improvement: 'border-red-200 bg-red-50 text-red-800',
  fail: 'border-red-200 bg-red-50 text-red-800',
  incomplete: 'border-red-200 bg-red-50 text-red-800',
  in_progress: 'border-sky-200 bg-sky-50 text-sky-800',
  planned: 'border-stone-200 bg-stone-50 text-stone-700',
  shipped: 'border-emerald-200 bg-emerald-50 text-emerald-800',
};

function roleLabel(role?: string) {
  return role ? role.replace(/_/g, ' ') : '-';
}

function formatUsd(value?: number | null) {
  if (value === null || value === undefined) return '-';
  if (value < 0.0001) return `$${value.toFixed(8)}`;
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

function formatInline(value: unknown) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}

type LedgerBucket = 'completed_updates' | 'next_update_queue';
type LedgerEntryWithBucket = ContinuousUpdateLedgerEntry & { bucket: LedgerBucket };

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
  const [releaseReadiness, setReleaseReadiness] = useState<ReleaseReadinessResult | null>(null);
  const [validationCommands, setValidationCommands] = useState<ReleaseValidationCommand[]>([]);
  const [legalAudit, setLegalAudit] = useState<LegalKnowledgeAudit | null>(null);
  const [ragPolicy, setRagPolicy] = useState<LegalRagEvaluationPolicy | null>(null);
  const [userNeeds, setUserNeeds] = useState<UserNeedsRadar | null>(null);
  const [productFeatureGaps, setProductFeatureGaps] = useState<ProductFeatureGapRadar | null>(null);
  const [feedbackRoadmap, setFeedbackRoadmap] = useState<FeedbackRoadmapCatalog | null>(null);
  const [continuousLedger, setContinuousLedger] = useState<ContinuousUpdateLedger | null>(null);
  const [caseIntakeCompleteness, setCaseIntakeCompleteness] = useState<CaseIntakeCompleteness | null>(null);
  const [caseTeamAccessPolicy, setCaseTeamAccessPolicy] = useState<CaseTeamAccessPolicy | null>(null);
  const [clientDeliveryRiskChecklist, setClientDeliveryRiskChecklist] = useState<ClientDeliveryRiskChecklist | null>(null);
  const [legalDocumentTemplateMatrix, setLegalDocumentTemplateMatrix] = useState<LegalDocumentTemplateMatrix | null>(null);
  const [legalDocumentExportReadiness, setLegalDocumentExportReadiness] =
    useState<LegalDocumentExportReadiness | null>(null);
  const [ocrImportReadinessPolicy, setOcrImportReadinessPolicy] = useState<OcrImportReadinessPolicy | null>(null);
  const [caseTimelineDeadlineRisk, setCaseTimelineDeadlineRisk] = useState<CaseTimelineDeadlineRisk | null>(null);
  const [matterAuditRetentionPolicy, setMatterAuditRetentionPolicy] = useState<MatterAuditRetentionPolicy | null>(null);
  const [lawyerReviewWorkflowPolicy, setLawyerReviewWorkflowPolicy] =
    useState<LawyerReviewWorkflowPolicy | null>(null);
  const [evidenceExhibitPackagePolicy, setEvidenceExhibitPackagePolicy] =
    useState<EvidenceExhibitPackagePolicy | null>(null);
  const [caseTaskNotificationPolicy, setCaseTaskNotificationPolicy] =
    useState<CaseTaskNotificationPolicy | null>(null);
  const [caseWorkbenchPayload, setCaseWorkbenchPayload] = useState<CaseWorkbenchPayload | null>(null);
  const [benchmark, setBenchmark] = useState<LegalReviewBenchmark | null>(null);
  const [researchBacklog, setResearchBacklog] = useState<LegalResearchBacklog | null>(null);
  const [benchmarkResearchRegistry, setBenchmarkResearchRegistry] =
    useState<LegalBenchmarkResearchRegistry | null>(null);
  const [publicBenchmarkSampler, setPublicBenchmarkSampler] = useState<LegalPublicBenchmarkSampler | null>(null);
  const [fixtureEvidenceBundle, setFixtureEvidenceBundle] = useState<LegalFixtureEvidenceBundle | null>(null);
  const [fixtureModelMatrix, setFixtureModelMatrix] = useState<LegalFixtureModelMatrix | null>(null);
  const [fixturePromptPack, setFixturePromptPack] = useState<LegalFixturePromptPack | null>(null);
  const [fixtureLocalRunPackage, setFixtureLocalRunPackage] = useState<LegalFixtureLocalRunPackage | null>(null);
  const [fixtureResponseNormalizer, setFixtureResponseNormalizer] = useState<LegalFixtureResponseNormalizer | null>(null);
  const [normalizerPayloadText, setNormalizerPayloadText] = useState('');
  const [normalizerError, setNormalizerError] = useState('');
  const [normalizerLoading, setNormalizerLoading] = useState(false);
  const [normalizerTemplateLoading, setNormalizerTemplateLoading] = useState(false);
  const [ledgerCategoryFilter, setLedgerCategoryFilter] = useState('all');
  const [ledgerStatusFilter, setLedgerStatusFilter] = useState('all');
  const [ledgerSearch, setLedgerSearch] = useState('');
  const [fixtureReviewFixtureId, setFixtureReviewFixtureId] = useState('');
  const [fixtureReviewModel, setFixtureReviewModel] = useState('');
  const [fixtureReviewRoute, setFixtureReviewRoute] = useState('');
  const [fixtureReviewHttpStatus, setFixtureReviewHttpStatus] = useState('200');
  const [fixtureReviewPayloadText, setFixtureReviewPayloadText] = useState('');
  const [fixtureReviewError, setFixtureReviewError] = useState('');
  const [fixtureReviewLoading, setFixtureReviewLoading] = useState(false);
  const [fixtureRunPlan, setFixtureRunPlan] = useState<LegalFixtureRunPlan | null>(null);
  const [fixtureRunReport, setFixtureRunReport] = useState<LegalFixtureRunReport | null>(null);
  const [fixtureResultArchive, setFixtureResultArchive] = useState<LegalFixtureResultArchive | null>(null);
  const [fixtureSmoke, setFixtureSmoke] = useState<LegalReviewFixtureSmoke | null>(null);
  const [fixtureImprovement, setFixtureImprovement] = useState<LegalFixtureImprovementPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const load = async (nextLanguage = language) => {
    setLoading(true);
    setError('');
    try {
      const [
        evidence,
        readiness,
        needsRadar,
        productFeatureGapData,
        feedbackMap,
        continuousLedgerData,
        caseIntakeCompletenessData,
        caseTeamAccessPolicyData,
        clientDeliveryRiskChecklistData,
        legalDocumentTemplateMatrixData,
        legalDocumentExportReadinessData,
        ocrImportReadinessPolicyData,
        caseTimelineDeadlineRiskData,
        matterAuditRetentionPolicyData,
        lawyerReviewWorkflowPolicyData,
        evidenceExhibitPackagePolicyData,
        caseTaskNotificationPolicyData,
        caseWorkbenchPayloadData,
        benchmarkData,
        researchBacklogData,
        benchmarkResearchRegistryData,
        publicBenchmarkSamplerData,
        fixtureEvidenceBundleData,
        fixtureModelMatrixData,
        fixturePromptPackData,
        fixtureLocalRunPackageData,
        fixtureRunPlanData,
        fixtureRunReportData,
        fixtureResultArchiveData,
        fixtureSmokeData,
        fixtureImprovementData,
        legalKnowledge,
        ragEvaluation,
      ] = await Promise.all([
        getMaintenanceEvidence(nextLanguage),
        getReleaseReadiness(),
        getUserNeedsRadar(),
        getProductFeatureGapRadar(),
        getFeedbackRoadmapCatalog(),
        getContinuousUpdateLedger(),
        getCaseIntakeCompleteness(),
        getCaseTeamAccessPolicy(),
        getClientDeliveryRiskChecklist(),
        getLegalDocumentTemplateMatrix(),
        getLegalDocumentExportReadiness(),
        getOcrImportReadinessPolicy(),
        getCaseTimelineDeadlineRisk(),
        getMatterAuditRetentionPolicy(),
        getLawyerReviewWorkflowPolicy(),
        getEvidenceExhibitPackagePolicy(),
        getCaseTaskNotificationPolicy(),
        getCaseWorkbenchPayload(),
        getLegalReviewBenchmark(),
        getLegalResearchBacklog(),
        getLegalBenchmarkResearchRegistry(),
        getLegalPublicBenchmarkSampler(),
        getLegalFixtureEvidenceBundle(),
        getLegalFixtureModelMatrix(),
        getLegalFixturePromptPack(),
        getLegalFixtureLocalRunPackage(),
        getLegalFixtureRunPlan(),
        getLegalFixtureRunReport(),
        getLegalFixtureResultArchive(),
        getLegalReviewFixtureSmoke(),
        getLegalFixtureImprovementPlan(),
        getLegalKnowledgeAudit(),
        getLegalRagEvaluationPolicy(),
      ]);
      setData(evidence);
      setReleaseReadiness(readiness.data);
      setValidationCommands(readiness.validation_commands);
      setUserNeeds(needsRadar);
      setProductFeatureGaps(productFeatureGapData);
      setFeedbackRoadmap(feedbackMap);
      setContinuousLedger(continuousLedgerData);
      setCaseIntakeCompleteness(caseIntakeCompletenessData);
      setCaseTeamAccessPolicy(caseTeamAccessPolicyData);
      setClientDeliveryRiskChecklist(clientDeliveryRiskChecklistData);
      setLegalDocumentTemplateMatrix(legalDocumentTemplateMatrixData);
      setLegalDocumentExportReadiness(legalDocumentExportReadinessData);
      setOcrImportReadinessPolicy(ocrImportReadinessPolicyData);
      setCaseTimelineDeadlineRisk(caseTimelineDeadlineRiskData);
      setMatterAuditRetentionPolicy(matterAuditRetentionPolicyData);
      setLawyerReviewWorkflowPolicy(lawyerReviewWorkflowPolicyData);
      setEvidenceExhibitPackagePolicy(evidenceExhibitPackagePolicyData);
      setCaseTaskNotificationPolicy(caseTaskNotificationPolicyData);
      setCaseWorkbenchPayload(caseWorkbenchPayloadData);
      setBenchmark(benchmarkData);
      setResearchBacklog(researchBacklogData);
      setBenchmarkResearchRegistry(benchmarkResearchRegistryData);
      setPublicBenchmarkSampler(publicBenchmarkSamplerData);
      setFixtureEvidenceBundle(fixtureEvidenceBundleData);
      setFixtureModelMatrix(fixtureModelMatrixData);
      setFixturePromptPack(fixturePromptPackData);
      setFixtureLocalRunPackage(fixtureLocalRunPackageData);
      setFixtureRunPlan(fixtureRunPlanData);
      setFixtureRunReport(fixtureRunReportData);
      setFixtureResultArchive(fixtureResultArchiveData);
      setFixtureSmoke(fixtureSmokeData);
      setFixtureImprovement(fixtureImprovementData);
      setLegalAudit(legalKnowledge);
      setRagPolicy(ragEvaluation);
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

  useEffect(() => {
    const firstRequest = fixtureLocalRunPackage?.request_files[0];
    if (!firstRequest) return;
    if (fixtureReviewFixtureId && fixtureLocalRunPackage.request_files.some((item) => item.fixture_id === fixtureReviewFixtureId)) {
      return;
    }
    setFixtureReviewFixtureId(firstRequest.fixture_id);
    setFixtureReviewModel(firstRequest.model);
  }, [fixtureLocalRunPackage, fixtureReviewFixtureId]);

  const controls = data?.release_management.release_readiness_controls ?? [];
  const blockingCount = releaseReadiness?.blocking_check_ids.length ?? 0;
  const totalEvidencePaths = useMemo(
    () => (data?.signals ?? []).reduce((total, signal) => total + signal.evidence_paths.length, 0),
    [data],
  );
  const ledgerCompletionPercent = useMemo(() => {
    if (!continuousLedger) return 0;
    const target = continuousLedger.goal.target_medium_large_update_count || 1;
    return Math.min(100, Math.round((continuousLedger.summary.completed_medium_large_update_count / target) * 100));
  }, [continuousLedger]);
  const ledgerEntries = useMemo<LedgerEntryWithBucket[]>(() => {
    if (!continuousLedger) return [];
    return [
      ...continuousLedger.completed_updates.map((entry) => ({ ...entry, bucket: 'completed_updates' as const })),
      ...continuousLedger.next_update_queue.map((entry) => ({ ...entry, bucket: 'next_update_queue' as const })),
    ];
  }, [continuousLedger]);
  const ledgerCategoryOptions = useMemo(
    () => Array.from(new Set(ledgerEntries.map((entry) => entry.category))).sort(),
    [ledgerEntries],
  );
  const ledgerStatusOptions = useMemo(
    () => Array.from(new Set(ledgerEntries.map((entry) => entry.status))).sort(),
    [ledgerEntries],
  );
  const filteredLedgerEntries = useMemo(() => {
    const query = ledgerSearch.trim().toLowerCase();
    return ledgerEntries.filter((entry) => {
      const matchesCategory = ledgerCategoryFilter === 'all' || entry.category === ledgerCategoryFilter;
      const matchesStatus = ledgerStatusFilter === 'all' || entry.status === ledgerStatusFilter;
      const searchableText = [
        entry.id,
        entry.title,
        entry.category,
        entry.status,
        entry.size,
        entry.impact,
        entry.commit_hint ?? '',
        ...entry.evidence_paths,
        ...entry.release_gate_links,
        ...entry.user_need_ids,
      ]
        .join(' ')
        .toLowerCase();
      return matchesCategory && matchesStatus && (!query || searchableText.includes(query));
    });
  }, [ledgerCategoryFilter, ledgerEntries, ledgerSearch, ledgerStatusFilter]);
  const filteredCompletedLedgerCount = filteredLedgerEntries.filter((entry) => entry.bucket === 'completed_updates').length;
  const filteredQueuedLedgerCount = filteredLedgerEntries.filter((entry) => entry.bucket === 'next_update_queue').length;

  const copyAnswer = async () => {
    if (!data?.form_answer) return;
    await navigator.clipboard.writeText(data.form_answer);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const loadNormalizerTemplate = async () => {
    setNormalizerTemplateLoading(true);
    setNormalizerError('');
    try {
      const template = await getLegalFixtureResponseNormalizerTemplate();
      setNormalizerPayloadText(JSON.stringify(template.payload_shape, null, 2));
    } catch (err) {
      console.error(err);
      setNormalizerError('Response normalizer template failed to load.');
    } finally {
      setNormalizerTemplateLoading(false);
    }
  };

  const selectFixtureReviewFixture = (fixtureId: string) => {
    setFixtureReviewFixtureId(fixtureId);
    const request = fixtureLocalRunPackage?.request_files.find((item) => item.fixture_id === fixtureId);
    if (request) {
      setFixtureReviewModel(request.model);
    }
  };

  const normalizeFixtureReviewPayload = async () => {
    setFixtureReviewLoading(true);
    setFixtureReviewError('');
    setNormalizerError('');
    try {
      const fixtureId = fixtureReviewFixtureId.trim();
      if (!fixtureId) {
        setFixtureReviewError('Select a fixture before review.');
        return;
      }
      if (!fixtureReviewPayloadText.trim()) {
        setFixtureReviewError('Paste a local gateway response JSON object first.');
        return;
      }
      const parsed = JSON.parse(fixtureReviewPayloadText) as unknown;
      if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
        setFixtureReviewError('Local review payload must be a JSON object.');
        return;
      }
      let httpStatus: number | undefined;
      if (fixtureReviewHttpStatus.trim()) {
        const statusValue = Number(fixtureReviewHttpStatus);
        if (!Number.isInteger(statusValue) || statusValue < 100 || statusValue > 599) {
          setFixtureReviewError('HTTP status must be a number from 100 to 599.');
          return;
        }
        httpStatus = statusValue;
      }
      const parsedObject = parsed as Record<string, unknown>;
      const payload =
        'responses' in parsedObject
          ? parsedObject
          : {
              responses: {
                [fixtureId]: {
                  gateway_response: parsedObject,
                  ...(fixtureReviewModel.trim() ? { model: fixtureReviewModel.trim() } : {}),
                  ...(fixtureReviewRoute.trim() ? { route: fixtureReviewRoute.trim() } : {}),
                  ...(httpStatus ? { http_status: httpStatus } : {}),
                },
              },
            };
      setNormalizerPayloadText(JSON.stringify(payload, null, 2));
      setFixtureResponseNormalizer(await normalizeLegalFixtureResponse(payload));
    } catch (err) {
      console.error(err);
      setFixtureReviewError(err instanceof SyntaxError ? 'Local review payload is not valid JSON.' : 'Local fixture review failed.');
    } finally {
      setFixtureReviewLoading(false);
    }
  };

  const normalizeFixtureResponse = async () => {
    setNormalizerLoading(true);
    setNormalizerError('');
    try {
      const payload = normalizerPayloadText.trim() ? JSON.parse(normalizerPayloadText) : {};
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setNormalizerError('Normalizer payload must be a JSON object.');
        return;
      }
      setFixtureResponseNormalizer(await normalizeLegalFixtureResponse(payload as Record<string, unknown>));
    } catch (err) {
      console.error(err);
      setNormalizerError(err instanceof SyntaxError ? 'Normalizer payload is not valid JSON.' : 'Response normalization failed.');
    } finally {
      setNormalizerLoading(false);
    }
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
                <Target className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{userNeeds?.summary.high_priority_count ?? 0}</div>
              <div className="mt-1 text-sm text-stone-600">high-priority needs</div>
            </CardContent>
          </Card>
        </div>

        {(caseIntakeCompleteness ||
          caseTeamAccessPolicy ||
          clientDeliveryRiskChecklist ||
          legalDocumentTemplateMatrix ||
          legalDocumentExportReadiness ||
          ocrImportReadinessPolicy ||
          caseTimelineDeadlineRisk ||
          matterAuditRetentionPolicy ||
          lawyerReviewWorkflowPolicy ||
          evidenceExhibitPackagePolicy ||
          caseTaskNotificationPolicy) && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Case workflow gates</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Intake, team access, delivery, document, OCR, deadline, review, evidence, task, and audit readiness.
                </div>
              </div>
              <Badge variant="outline" className="bg-white">
                11 maintenance endpoints
              </Badge>
            </div>

            <div className="grid gap-3 xl:grid-cols-4 md:grid-cols-2">
              {caseIntakeCompleteness && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Intake completeness</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">case-intake-completeness</div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[caseIntakeCompleteness.status] ?? statusClass.not_run}
                    >
                      {caseIntakeCompleteness.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseIntakeCompleteness.summary.requirement_count}
                      </div>
                      <div className="text-[11px] text-stone-500">requirements</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseIntakeCompleteness.summary.blocking_requirement_count}
                      </div>
                      <div className="text-[11px] text-stone-500">blocking</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseIntakeCompleteness.summary.complete_requirement_count}
                      </div>
                      <div className="text-[11px] text-stone-500">complete</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {caseIntakeCompleteness.blocking_items.slice(0, 3).map((item) => (
                      <div key={item.id} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.title}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">
                          missing: {item.missing_fields.join(', ') || '-'}
                        </div>
                      </div>
                    ))}
                    {caseIntakeCompleteness.blocking_items.length === 0 &&
                      caseIntakeCompleteness.requirements.slice(0, 3).map((item) => (
                        <div key={item.id} className="flex items-center justify-between gap-2 text-xs">
                          <span className="truncate text-stone-700">{item.title}</span>
                          <Badge variant="outline" className={statusClass[item.status] ?? statusClass.not_run}>
                            {item.status}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {caseTeamAccessPolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Team access policy</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{caseTeamAccessPolicy.policy_id}</div>
                    </div>
                    <Badge variant="outline" className={statusClass[caseTeamAccessPolicy.status] ?? statusClass.ready}>
                      {caseTeamAccessPolicy.status}
                    </Badge>
                  </div>
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge variant="outline" className="bg-white">
                      roles: {caseTeamAccessPolicy.summary.role_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      sensitive ops: {caseTeamAccessPolicy.summary.sensitive_operation_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      {caseTeamAccessPolicy.summary.default_posture.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {caseTeamAccessPolicy.role_matrix.slice(0, 5).map((role) => (
                      <div key={role.role} className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-stone-950">{role.role.replace(/_/g, ' ')}</span>
                          <span className="font-mono text-[11px] text-stone-500">
                            {role.default_scope.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">
                          deny: {role.denied_actions.slice(0, 2).join(', ') || '-'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {clientDeliveryRiskChecklist && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Client delivery risk</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        client-delivery-risk-checklist
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[clientDeliveryRiskChecklist.status] ?? statusClass.ready}
                    >
                      {clientDeliveryRiskChecklist.status}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {clientDeliveryRiskChecklist.checklist_items.length}
                      </div>
                      <div className="text-[11px] text-stone-500">checks</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {clientDeliveryRiskChecklist.blocking_items.length}
                      </div>
                      <div className="text-[11px] text-stone-500">blockers</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {clientDeliveryRiskChecklist.client_disclosures.length}
                      </div>
                      <div className="text-[11px] text-stone-500">client notices</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {clientDeliveryRiskChecklist.blocking_items.slice(0, 3).map((item) => (
                      <div key={item.id} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className="border-red-200 bg-red-50 text-red-800">
                            {item.severity}
                          </Badge>
                          <span className="text-xs font-semibold text-stone-950">{item.title}</span>
                        </div>
                        <div className="text-[11px] leading-4 text-stone-500">{item.owner.replace(/_/g, ' ')}</div>
                      </div>
                    ))}
                    <div className="text-[11px] leading-4 text-stone-500">
                      Delivery default: {clientDeliveryRiskChecklist.delivery_allowed_by_default ? 'allowed' : 'blocked'}
                    </div>
                  </div>
                </div>
              )}

              {legalDocumentTemplateMatrix && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Document templates</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        legal-document-template-matrix
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[legalDocumentTemplateMatrix.status] ?? statusClass.ready}
                    >
                      {legalDocumentTemplateMatrix.status}
                    </Badge>
                  </div>
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge variant="outline" className="bg-white">
                      types: {legalDocumentTemplateMatrix.summary.document_type_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      blockers: {legalDocumentTemplateMatrix.summary.blocking_condition_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      exports: {legalDocumentTemplateMatrix.summary.export_format_count}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {legalDocumentTemplateMatrix.document_types.slice(0, 4).map((row) => (
                      <div key={row.id} className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{row.document_type}</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                          <Badge variant="outline" className="bg-white font-mono text-[10px]">
                            fields {row.required_fields.length}
                          </Badge>
                          <Badge variant="outline" className="bg-white font-mono text-[10px]">
                            blockers {row.pre_generation_blockers.length}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={
                              row.review_gate.critical
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-stone-200 bg-stone-50 text-stone-700'
                            }
                          >
                            review gate
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {legalDocumentExportReadiness && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Export readiness</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        legal-document-export-readiness
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[legalDocumentExportReadiness.status] ?? statusClass.not_run}
                    >
                      {legalDocumentExportReadiness.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {legalDocumentExportReadiness.summary.gate_count}
                      </div>
                      <div className="text-[11px] text-stone-500">gates</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {legalDocumentExportReadiness.summary.blocking_gate_count}
                      </div>
                      <div className="text-[11px] text-stone-500">blocking</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {legalDocumentExportReadiness.summary.supported_export_formats.length}
                      </div>
                      <div className="text-[11px] text-stone-500">formats</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {legalDocumentExportReadiness.blocking_items.slice(0, 3).map((item) => (
                      <div key={item.id} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.title}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">
                          observed: {formatInline(item.observed_value)}
                        </div>
                      </div>
                    ))}
                    {legalDocumentExportReadiness.blocking_items.length === 0 && (
                      <div className="text-[11px] leading-4 text-stone-500">
                        Format gate: {legalDocumentExportReadiness.format_gate.status}; supported:{' '}
                        {legalDocumentExportReadiness.summary.supported_export_formats.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {ocrImportReadinessPolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">OCR import</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {ocrImportReadinessPolicy.policy_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[ocrImportReadinessPolicy.status] ?? statusClass.not_run}
                    >
                      {ocrImportReadinessPolicy.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge variant="outline" className="bg-white">
                      states: {ocrImportReadinessPolicy.status_enumeration.length}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      scanned: {ocrImportReadinessPolicy.summary.scanned_page_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      low text: {ocrImportReadinessPolicy.summary.low_text_page_count}
                    </Badge>
                    <Badge variant="outline" className="bg-white">
                      attempts: {ocrImportReadinessPolicy.summary.ocr_attempt_count}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {[...ocrImportReadinessPolicy.blocking_conditions, ...ocrImportReadinessPolicy.manual_review_conditions]
                      .slice(0, 3)
                      .map((item) => (
                        <div key={item.id} className="rounded-[8px] border border-amber-100 bg-white p-2">
                          <div className="text-xs font-semibold text-stone-950">{item.title}</div>
                          <div className="mt-1 text-[11px] leading-4 text-stone-500">{item.reviewer_action}</div>
                        </div>
                      ))}
                    {ocrImportReadinessPolicy.blocking_conditions.length +
                      ocrImportReadinessPolicy.manual_review_conditions.length ===
                      0 &&
                      ocrImportReadinessPolicy.status_enumeration.slice(0, 3).map((item) => (
                        <div key={item.status} className="flex items-center justify-between gap-2 text-xs">
                          <span className="truncate text-stone-700">{item.meaning}</span>
                          <Badge variant="outline" className={statusClass[item.status] ?? statusClass.not_run}>
                            {item.status.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {caseTimelineDeadlineRisk && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Deadline risk</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {caseTimelineDeadlineRisk.assessment_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[caseTimelineDeadlineRisk.status] ?? statusClass.not_run}
                    >
                      {caseTimelineDeadlineRisk.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTimelineDeadlineRisk.event_type_standards.length}
                      </div>
                      <div className="text-[11px] text-stone-500">event types</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTimelineDeadlineRisk.summary.blocking_urgent_count}
                      </div>
                      <div className="text-[11px] text-stone-500">urgent</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTimelineDeadlineRisk.summary.missing_fact_count}
                      </div>
                      <div className="text-[11px] text-stone-500">missing facts</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {caseTimelineDeadlineRisk.blocking_urgent_items.slice(0, 3).map((item) => (
                      <div key={`${item.event_id}-${item.event_type}`} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.event_type.replace(/_/g, ' ')}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">{item.reason}</div>
                      </div>
                    ))}
                    {caseTimelineDeadlineRisk.blocking_urgent_items.length === 0 &&
                      caseTimelineDeadlineRisk.deadline_rules_metadata.slice(0, 3).map((rule) => (
                        <div key={rule.rule_id} className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                          <div className="text-xs font-semibold text-stone-950">{rule.rule_id.replace(/_/g, ' ')}</div>
                          <div className="mt-1 text-[11px] leading-4 text-stone-500">{rule.trigger}</div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {matterAuditRetentionPolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Audit retention</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {matterAuditRetentionPolicy.policy_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[matterAuditRetentionPolicy.status] ?? statusClass.not_run}
                    >
                      {matterAuditRetentionPolicy.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {matterAuditRetentionPolicy.summary.event_type_count}
                      </div>
                      <div className="text-[11px] text-stone-500">event types</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {matterAuditRetentionPolicy.summary.blocking_issue_count}
                      </div>
                      <div className="text-[11px] text-stone-500">blockers</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {matterAuditRetentionPolicy.summary.retention_bucket_count}
                      </div>
                      <div className="text-[11px] text-stone-500">buckets</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {matterAuditRetentionPolicy.blocking_items.slice(0, 3).map((item) => (
                      <div key={item.event_type} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">
                          {item.event_type.replace(/_/g, ' ')}
                        </div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">
                          missing: {item.missing_fields.join(', ') || '-'}; forbidden:{' '}
                          {item.forbidden_fields_present.join(', ') || '-'}
                        </div>
                      </div>
                    ))}
                    {matterAuditRetentionPolicy.blocking_items.length === 0 &&
                      matterAuditRetentionPolicy.event_policies.slice(0, 3).map((item) => (
                        <div key={item.event_type} className="flex items-center justify-between gap-2 text-xs">
                          <span className="truncate text-stone-700">{item.event_type.replace(/_/g, ' ')}</span>
                          <Badge variant="outline" className={statusClass[item.status] ?? statusClass.not_run}>
                            {item.retention_bucket.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {lawyerReviewWorkflowPolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Lawyer review</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {lawyerReviewWorkflowPolicy.policy_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[lawyerReviewWorkflowPolicy.status] ?? statusClass.ready}
                    >
                      {lawyerReviewWorkflowPolicy.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {lawyerReviewWorkflowPolicy.summary.state_count}
                      </div>
                      <div className="text-[11px] text-stone-500">states</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {lawyerReviewWorkflowPolicy.summary.transition_count}
                      </div>
                      <div className="text-[11px] text-stone-500">flows</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {lawyerReviewWorkflowPolicy.summary.blocking_condition_count}
                      </div>
                      <div className="text-[11px] text-stone-500">blockers</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {lawyerReviewWorkflowPolicy.blocking_conditions.slice(0, 3).map((item) => (
                      <div key={item.code} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.code.replace(/_/g, ' ')}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">{item.message}</div>
                      </div>
                    ))}
                    {lawyerReviewWorkflowPolicy.blocking_conditions.length === 0 &&
                      lawyerReviewWorkflowPolicy.allowed_state_transitions.slice(0, 3).map((item) => (
                        <div
                          key={`${item.from_status}-${item.to_status}`}
                          className="rounded-[8px] border border-stone-950/10 bg-white p-2"
                        >
                          <div className="text-xs font-semibold text-stone-950">
                            {item.from_status.replace(/_/g, ' ')} {'->'} {item.to_status.replace(/_/g, ' ')}
                          </div>
                          <div className="mt-1 text-[11px] leading-4 text-stone-500">
                            roles: {item.allowed_roles.map(roleLabel).join(', ')}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {evidenceExhibitPackagePolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Evidence package</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {evidenceExhibitPackagePolicy.policy_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[evidenceExhibitPackagePolicy.status] ?? statusClass.not_run}
                    >
                      {evidenceExhibitPackagePolicy.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {evidenceExhibitPackagePolicy.summary.exhibit_count}
                      </div>
                      <div className="text-[11px] text-stone-500">exhibits</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {evidenceExhibitPackagePolicy.summary.blocking_issue_count}
                      </div>
                      <div className="text-[11px] text-stone-500">blockers</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {evidenceExhibitPackagePolicy.summary.export_manifest_field_count}
                      </div>
                      <div className="text-[11px] text-stone-500">manifest</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {evidenceExhibitPackagePolicy.blocking_issues.slice(0, 3).map((item) => (
                      <div key={item.id} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.exhibit_ref}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">{item.message}</div>
                      </div>
                    ))}
                    {evidenceExhibitPackagePolicy.blocking_issues.length === 0 &&
                      evidenceExhibitPackagePolicy.package_checks.slice(0, 3).map((item) => (
                        <div key={item.id} className="flex items-center justify-between gap-2 text-xs">
                          <span className="truncate text-stone-700">{item.label}</span>
                          <Badge variant="outline" className={statusClass[item.status] ?? statusClass.not_run}>
                            {item.status.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {caseTaskNotificationPolicy && (
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Task notifications</h3>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">
                        {caseTaskNotificationPolicy.policy_id}
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={statusClass[caseTaskNotificationPolicy.status] ?? statusClass.ready}
                    >
                      {caseTaskNotificationPolicy.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="mb-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTaskNotificationPolicy.summary.active_task_count}
                      </div>
                      <div className="text-[11px] text-stone-500">active</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTaskNotificationPolicy.summary.blocking_urgent_count}
                      </div>
                      <div className="text-[11px] text-stone-500">urgent</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                      <div className="text-lg font-black text-stone-950">
                        {caseTaskNotificationPolicy.summary.notification_count}
                      </div>
                      <div className="text-[11px] text-stone-500">queued</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {caseTaskNotificationPolicy.blocking_urgent_tasks.slice(0, 3).map((item) => (
                      <div key={`${item.case_id}-${item.task_id}`} className="rounded-[8px] border border-red-100 bg-white p-2">
                        <div className="text-xs font-semibold text-stone-950">{item.task_id}</div>
                        <div className="mt-1 text-[11px] leading-4 text-stone-500">
                          {item.priority}; triggers: {item.triggers.join(', ') || '-'}
                        </div>
                      </div>
                    ))}
                    {caseTaskNotificationPolicy.blocking_urgent_tasks.length === 0 &&
                      caseTaskNotificationPolicy.trigger_rules.slice(0, 3).map((item) => (
                        <div key={item.rule_id} className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate text-xs font-semibold text-stone-950">
                              {item.rule_id.replace(/-/g, ' ')}
                            </span>
                            <Badge variant="outline" className={priorityClass[item.severity] ?? priorityClass.medium}>
                              {item.severity}
                            </Badge>
                          </div>
                          <div className="mt-1 text-[11px] leading-4 text-stone-500">{item.trigger}</div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {caseWorkbenchPayload && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Case workbench payload</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Frontend-ready template payload for the case workbench dashboard, sections, blockers, and actions.
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge
                  variant="outline"
                  className={statusClass[caseWorkbenchPayload.dashboard.status] ?? statusClass.not_run}
                >
                  dashboard: {caseWorkbenchPayload.dashboard.status.replace(/_/g, ' ')}
                </Badge>
                <Badge variant="outline" className="bg-white font-mono text-[11px]">
                  {caseWorkbenchPayload.payload_id}
                </Badge>
              </div>
            </div>

            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase text-stone-500">Dashboard status</div>
                <div className="mt-2 text-2xl font-black text-stone-950">
                  {caseWorkbenchPayload.dashboard.status.replace(/_/g, ' ')}
                </div>
                <div className="mt-1 text-xs leading-5 text-stone-500">
                  {caseWorkbenchPayload.dashboard.deterministic ? 'deterministic local template' : 'dynamic payload'}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase text-stone-500">Sections</div>
                <div className="mt-2 text-2xl font-black text-stone-950">
                  {caseWorkbenchPayload.dashboard.evaluated_section_count}/
                  {caseWorkbenchPayload.dashboard.section_count}
                </div>
                <div className="mt-1 text-xs leading-5 text-stone-500">evaluated sections</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase text-stone-500">Blockers</div>
                <div className="mt-2 text-2xl font-black text-stone-950">
                  {caseWorkbenchPayload.dashboard.blocker_count}
                </div>
                <div className="mt-1 text-xs leading-5 text-stone-500">
                  {caseWorkbenchPayload.dashboard.primary_blocker?.title ?? 'no blocking items'}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase text-stone-500">Next actions</div>
                <div className="mt-2 text-2xl font-black text-stone-950">
                  {caseWorkbenchPayload.dashboard.next_action_count}
                </div>
                <div className="mt-1 text-xs leading-5 text-stone-500">
                  {caseWorkbenchPayload.dashboard.critical_action_count} critical
                </div>
              </div>
            </div>

            <div className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <div className="flex flex-wrap items-center justify-between gap-2 p-4 pb-2">
                  <h3 className="text-sm font-black uppercase text-stone-500">Sections</h3>
                  <div className="text-xs text-stone-500">
                    {caseWorkbenchPayload.case_ref} / {caseWorkbenchPayload.matter_ref}
                  </div>
                </div>
                <div className="max-h-[360px] overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Section</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Metrics</TableHead>
                        <TableHead>Preview</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {caseWorkbenchPayload.sections.map((section) => (
                        <TableRow key={section.id}>
                          <TableCell className="max-w-[240px]">
                            <div className="font-semibold text-stone-950">{section.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{section.id}</div>
                            <div className="mt-1 text-[11px] text-stone-500">{section.source}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-2">
                              <Badge variant="outline" className={statusClass[section.status] ?? statusClass.not_run}>
                                {section.status.replace(/_/g, ' ')}
                              </Badge>
                              <Badge variant="outline" className="bg-white">
                                {section.input_state.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <div className="mt-2 text-[11px] text-stone-500">severity: {section.severity}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px]">
                            <div className="flex flex-wrap gap-1">
                              {section.metrics.map((metric) => (
                                <Badge key={metric.id} variant="outline" className="bg-white text-[11px]">
                                  {metric.label}: {formatInline(metric.value)}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {section.empty_state?.message ??
                              (section.preview_items.length
                                ? `${section.preview_items.length} preview items`
                                : 'No preview items')}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              <div className="grid gap-3">
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <h3 className="text-sm font-black uppercase text-stone-500">Blockers</h3>
                    <Badge variant="outline" className="bg-white">
                      {caseWorkbenchPayload.blockers.length}
                    </Badge>
                  </div>
                  {caseWorkbenchPayload.blockers.length === 0 ? (
                    <div className="border-t border-stone-950/10 pt-3 text-sm text-stone-600">
                      No blockers in the current template payload.
                    </div>
                  ) : (
                    <div className="divide-y divide-stone-950/10">
                      {caseWorkbenchPayload.blockers.slice(0, 4).map((blocker) => (
                        <div key={blocker.id} className="py-3 first:pt-1 last:pb-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={statusClass.blocked}>
                              {blocker.severity}
                            </Badge>
                            <span className="text-xs font-semibold text-stone-950">{blocker.title}</span>
                          </div>
                          <div className="mt-1 text-xs leading-5 text-stone-600">{blocker.reason}</div>
                          <div className="mt-1 text-[11px] leading-5 text-stone-500">
                            {blocker.source_section.replace(/_/g, ' ')}: {blocker.required_action}
                          </div>
                        </div>
                      ))}
                      {caseWorkbenchPayload.blockers.length > 4 && (
                        <div className="pt-3 text-xs text-stone-500">
                          +{caseWorkbenchPayload.blockers.length - 4} more blockers
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <h3 className="text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <Badge variant="outline" className="bg-white">
                      {caseWorkbenchPayload.next_actions.length}
                    </Badge>
                  </div>
                  <div className="divide-y divide-stone-950/10">
                    {caseWorkbenchPayload.next_actions.slice(0, 6).map((action) => (
                      <div key={action.id} className="py-3 first:pt-1 last:pb-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className={priorityClass[action.priority] ?? priorityClass.low}>
                            {action.priority}
                          </Badge>
                          <span className="font-mono text-[11px] text-stone-500">
                            {action.source_section.replace(/_/g, ' ')} / {action.owner.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <div className="mt-1 text-xs leading-5 text-stone-700">{action.action}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {continuousLedger && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Continuous update ledger</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Progress evidence for 24h maintenance and 100+ medium/large update tracking.
                </div>
              </div>
              <Badge variant="outline" className={statusClass[continuousLedger.status] ?? statusClass.in_progress}>
                {continuousLedger.status.replace(/_/g, ' ')}
              </Badge>
            </div>

            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {continuousLedger.summary.completed_medium_large_update_count}/
                  {continuousLedger.goal.target_medium_large_update_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">medium/large updates</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {continuousLedger.summary.remaining_medium_large_update_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">updates remaining</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{continuousLedger.summary.planned_update_count}</div>
                <div className="mt-1 text-sm text-stone-600">planned updates</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {continuousLedger.summary.continuous_hours_verified}/
                  {continuousLedger.goal.target_continuous_hours}
                </div>
                <div className="mt-1 text-sm text-stone-600">hours verified</div>
              </div>
            </div>

            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-4">
                <div className="mb-2 flex items-center justify-between gap-3 text-xs font-semibold uppercase text-stone-500">
                  <span>100 update progress</span>
                  <span>{ledgerCompletionPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-stone-200">
                  <div className="h-full bg-stone-950" style={{ width: `${ledgerCompletionPercent}%` }} />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(continuousLedger.summary.category_counts).map(([category, count]) => (
                  <Badge key={category} variant="outline" className={categoryClass[category] ?? categoryClass.maintenance}>
                    {category.replace(/_/g, ' ')}: {count}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="mb-3 flex flex-wrap items-end gap-2 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-3">
              <label className="min-w-[220px] flex-1">
                <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Search</div>
                <Input
                  value={ledgerSearch}
                  onChange={(event) => setLedgerSearch(event.target.value)}
                  className="h-9 rounded-[8px] bg-white text-sm"
                  placeholder="Title, impact, evidence, gate"
                />
              </label>
              <label className="w-full sm:w-[190px]">
                <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Category</div>
                <Select value={ledgerCategoryFilter} onValueChange={setLedgerCategoryFilter}>
                  <SelectTrigger className="h-9 rounded-[8px] bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All categories</SelectItem>
                    {ledgerCategoryOptions.map((category) => (
                      <SelectItem key={category} value={category}>
                        {category.replace(/_/g, ' ')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </label>
              <label className="w-full sm:w-[170px]">
                <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Status</div>
                <Select value={ledgerStatusFilter} onValueChange={setLedgerStatusFilter}>
                  <SelectTrigger className="h-9 rounded-[8px] bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statuses</SelectItem>
                    {ledgerStatusOptions.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status.replace(/_/g, ' ')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </label>
              <Button
                type="button"
                variant="outline"
                className="soft-button h-9"
                disabled={ledgerCategoryFilter === 'all' && ledgerStatusFilter === 'all' && !ledgerSearch}
                onClick={() => {
                  setLedgerCategoryFilter('all');
                  setLedgerStatusFilter('all');
                  setLedgerSearch('');
                }}
              >
                <RefreshCw className="h-4 w-4" />
                Reset
              </Button>
              <div className="ml-auto text-xs leading-5 text-stone-500">
                {filteredLedgerEntries.length}/{ledgerEntries.length} entries / completed {filteredCompletedLedgerCount} / queue{' '}
                {filteredQueuedLedgerCount}
              </div>
            </div>

            <div className="grid gap-3 lg:grid-cols-[0.72fr_1.28fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Low-resource test policy</h3>
                <div className="space-y-2 text-sm text-stone-700">
                  <div className="flex items-center justify-between gap-3">
                    <span>Fixture limit</span>
                    <Badge variant="outline" className="bg-white">
                      {continuousLedger.low_resource_test_policy.default_fixture_limit}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span>Max parallel requests</span>
                    <Badge variant="outline" className="bg-white">
                      {continuousLedger.low_resource_test_policy.max_parallel_requests}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span>Network</span>
                    <Badge variant="outline" className="bg-white">
                      {continuousLedger.low_resource_test_policy.network_access.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="break-all font-mono text-[11px] text-stone-500">
                    {continuousLedger.low_resource_test_policy.recommended_endpoint}
                  </div>
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <div className="flex flex-wrap items-center justify-between gap-2 p-4 pb-2">
                  <h3 className="text-sm font-black uppercase text-stone-500">Update entries</h3>
                  <div className="text-xs text-stone-500">completed_updates + next_update_queue</div>
                </div>
                <div className="max-h-[560px] overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Bucket</TableHead>
                        <TableHead>Update</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Evidence</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredLedgerEntries.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="py-6 text-center text-stone-500">
                            No updates match the current filters.
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredLedgerEntries.map((entry) => (
                          <TableRow key={`${entry.bucket}-${entry.id}`}>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={entry.bucket === 'completed_updates' ? statusClass.shipped : statusClass.planned}
                              >
                                {entry.bucket === 'completed_updates' ? 'completed' : 'queue'}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[420px]">
                              <div className="font-semibold text-stone-950">{entry.title}</div>
                              <div className="mt-1 text-xs leading-5 text-stone-600">{entry.impact}</div>
                              {entry.commit_hint && (
                                <div className="mt-1 font-mono text-[11px] text-stone-500">{entry.commit_hint}</div>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={categoryClass[entry.category] ?? categoryClass.maintenance}>
                                {entry.category.replace(/_/g, ' ')}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-2">
                                <Badge variant="outline" className={statusClass[entry.status] ?? statusClass.planned}>
                                  {entry.status.replace(/_/g, ' ')}
                                </Badge>
                                <Badge variant="outline" className="bg-white">
                                  {entry.size}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                              {entry.evidence_paths.length === 0 ? (
                                '-'
                              ) : (
                                <div className="space-y-1">
                                  {entry.evidence_paths.slice(0, 2).map((path) => (
                                    <div key={path} className="break-all font-mono text-[11px]">
                                      {path}
                                    </div>
                                  ))}
                                  {entry.evidence_paths.length > 2 && (
                                    <div className="text-[11px] text-stone-500">
                                      +{entry.evidence_paths.length - 2} more evidence paths
                                    </div>
                                  )}
                                </div>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          </section>
        )}

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

            {releaseReadiness && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Release readiness</h2>
                    <div className="mt-1 text-sm text-stone-600">{releaseReadiness.summary}</div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      releaseReadiness.release_allowed
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                        : releaseReadiness.failed_check_ids.length
                          ? 'border-red-200 bg-red-50 text-red-800'
                          : 'border-amber-200 bg-amber-50 text-amber-900'
                    }
                  >
                    {releaseReadiness.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {releaseReadiness.passed_or_waived_required_count}/{releaseReadiness.required_check_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">required checks passed</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{blockingCount}</div>
                    <div className="mt-1 text-sm text-stone-600">blocking checks</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{validationCommands.length}</div>
                    <div className="mt-1 text-sm text-stone-600">validation commands</div>
                  </div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Check</TableHead>
                        <TableHead>Owner</TableHead>
                        <TableHead>State</TableHead>
                        <TableHead>Required</TableHead>
                        <TableHead>Command</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {releaseReadiness.checks.map((check) => (
                        <TableRow key={check.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{check.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{check.id}</div>
                          </TableCell>
                          <TableCell className="font-mono text-xs">{check.owner}</TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                check.validation_state === 'pass' || check.validation_state === 'waived'
                                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                                  : check.validation_state === 'fail'
                                    ? 'border-red-200 bg-red-50 text-red-800'
                                    : 'border-stone-200 bg-stone-50 text-stone-700'
                              }
                            >
                              {check.validation_state.replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>{check.required ? 'yes' : 'no'}</TableCell>
                          <TableCell className="max-w-[420px] font-mono text-[11px] text-stone-600">
                            {check.validation_command || check.manual_note || '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </section>
            )}

            {userNeeds && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">User needs radar</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {userNeeds.summary.need_count} needs · {userNeeds.summary.high_priority_count} high priority ·{' '}
                      {userNeeds.method.input_sources.length} sources
                    </div>
                  </div>
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                    {userNeeds.status}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-3">
                  {userNeeds.roadmap.map((phase) => (
                    <div key={phase.phase} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-xs font-semibold uppercase text-stone-500">{phase.phase}</div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {phase.focus_need_ids.map((id) => (
                          <Badge key={id} variant="outline" className="bg-white font-mono text-[11px]">
                            {id}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-xs font-semibold uppercase text-stone-500">Scoring</div>
                    <div className="mt-2 text-sm leading-6 text-stone-700">{userNeeds.method.scoring}</div>
                  </div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Need</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Users</TableHead>
                        <TableHead>Release gates</TableHead>
                        <TableHead>Next action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {userNeeds.needs.slice(0, 7).map((need) => (
                        <TableRow key={need.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{need.title}</div>
                            <div className="mt-1 max-w-[440px] text-xs leading-5 text-stone-600">{need.pain_point}</div>
                            <div className="mt-2 font-mono text-[11px] text-stone-500">{need.id}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={priorityClass[need.priority_band] ?? priorityClass.low}>
                              {need.priority_band} · {need.priority_score}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                            {need.user_segments.join(', ')}
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[260px] flex-wrap gap-1">
                              {need.release_gate_links.map((gate) => (
                                <Badge key={gate} variant="outline" className="bg-white font-mono text-[11px]">
                                  {gate}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {need.next_actions[0] || '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </section>
            )}

            {productFeatureGaps && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Product feature gap radar</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {productFeatureGaps.summary.feature_gap_count} gaps /{' '}
                      {productFeatureGaps.summary.high_priority_count} high priority /{' '}
                      {productFeatureGaps.summary.module_count} modules
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge
                      variant="outline"
                      className={statusClass[productFeatureGaps.status] ?? statusClass.incomplete}
                    >
                      {productFeatureGaps.status.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" className="border-red-200 bg-red-50 text-red-800">
                      public feature claim:{' '}
                      {productFeatureGaps.summary.ready_for_public_feature_claim ? 'ready' : 'blocked'}
                    </Badge>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-red-200 bg-red-50 p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-red-800">Incomplete status</h3>
                    <div className="text-sm leading-6 text-red-900">
                      This register is incomplete product planning evidence. It means these modules still require shipped
                      implementation evidence before the product can claim full legal workflow coverage.
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {productFeatureGaps.summary.top_gap_ids.map((id) => (
                        <Badge key={id} variant="outline" className="border-red-200 bg-white font-mono text-[11px]">
                          {id}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Delivery phases</h3>
                    <div className="grid gap-3 md:grid-cols-3">
                      {productFeatureGaps.delivery_phases.map((phase) => (
                        <div key={phase.id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                          <div className="font-semibold text-stone-950">{phase.title}</div>
                          <div className="mt-1 text-xs leading-5 text-stone-600">{phase.objective}</div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {phase.gap_ids.slice(0, 5).map((gapId) => (
                              <Badge key={gapId} variant="outline" className="bg-white font-mono text-[10px]">
                                {gapId}
                              </Badge>
                            ))}
                          </div>
                          <div className="mt-2 text-[11px] leading-5 text-stone-500">
                            Exit: {phase.exit_criteria[0] || '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Gap</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Current state</TableHead>
                        <TableHead>Target capability</TableHead>
                        <TableHead>Next actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {productFeatureGaps.feature_gaps.slice(0, 6).map((gap) => (
                        <TableRow key={gap.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{gap.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{gap.id}</div>
                            <div className="mt-2 text-xs text-stone-600">{gap.module.replace(/_/g, ' ')}</div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={priorityClass[gap.priority_band] ?? priorityClass.medium}
                            >
                              {gap.priority_band} / {gap.priority_score}
                            </Badge>
                            <div className="mt-2 text-[11px] leading-5 text-stone-500">
                              state: {gap.completion_state}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {gap.current_state}
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {gap.target_capability}
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            <ul className="space-y-1">
                              {gap.next_actions.map((action) => (
                                <li key={action} className="flex gap-2">
                                  <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                                  <span>{action}</span>
                                </li>
                              ))}
                            </ul>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Completion policy</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {productFeatureGaps.summary.completion_policy.map((policy) => (
                      <li key={policy} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{policy}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 text-xs leading-5 text-stone-500">{productFeatureGaps.privacy_note}</div>
                </div>
              </section>
            )}

            {researchBacklog && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal research backlog</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {researchBacklog.summary.backlog_item_count} items / {researchBacklog.summary.source_count} sources /{' '}
                      {researchBacklog.summary.workstream_count} workstreams
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[researchBacklog.status] ?? statusClass.ready}>
                    {researchBacklog.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {researchBacklog.summary.high_priority_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">high-priority items</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {researchBacklog.summary.cheap_first_item_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first items</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {researchBacklog.summary.local_run_item_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">local-run fit</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {researchBacklog.next_iteration_queue.length}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">queued updates</div>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Next iteration queue</h3>
                    <div className="space-y-3">
                      {researchBacklog.next_iteration_queue.map((item) => (
                        <div key={item.item_id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="bg-stone-950 text-white">
                              {item.priority_score}
                            </Badge>
                            <span className="font-mono text-xs text-stone-500">{item.item_id}</span>
                          </div>
                          <div className="text-sm font-semibold text-stone-950">{item.title}</div>
                          <div className="mt-1 text-xs leading-5 text-stone-600">{item.first_action}</div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {item.release_gate_links.map((gate) => (
                              <Badge key={gate} variant="outline" className="bg-white font-mono text-[11px]">
                                {gate}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Research sources</h3>
                    <div className="space-y-3">
                      {researchBacklog.method.input_sources.map((source) => (
                        <div key={source.id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-sm font-semibold text-stone-950 hover:underline"
                            >
                              {source.title}
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                            <Badge variant="outline" className="bg-white">
                              {source.source_type.replace(/_/g, ' ')}
                            </Badge>
                          </div>
                          <div className="text-xs leading-5 text-stone-600">{source.signal}</div>
                          <div className="mt-2 text-xs leading-5 text-stone-500">{source.project_application}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Research</TableHead>
                        <TableHead>Needs</TableHead>
                        <TableHead>Release gates</TableHead>
                        <TableHead>Next action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {researchBacklog.backlog.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{item.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{item.id}</div>
                            <div className="mt-2 text-xs text-stone-600">{item.workstream.replace(/_/g, ' ')}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={priorityClass[item.priority_band] ?? priorityClass.low}>
                              {item.priority_band} / {item.priority_score}
                            </Badge>
                            <div className="mt-2 text-[11px] leading-5 text-stone-500">
                              cost {item.cost_sensitivity} / local {item.local_run_fit}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                            {item.source_ids.join(', ')}
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            {item.user_need_ids.join(', ')}
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[280px] flex-wrap gap-1">
                              {item.release_gate_links.map((gate) => (
                                <Badge key={gate} variant="outline" className="bg-white font-mono text-[11px]">
                                  {gate}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {item.next_actions[0] || '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Maintenance actions</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {researchBacklog.maintenance_actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 text-xs leading-5 text-stone-500">{researchBacklog.privacy_note}</div>
                </div>
              </section>
            )}

            {benchmarkResearchRegistry && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal benchmark research registry</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only/source registry for {benchmarkResearchRegistry.summary.source_names.join(', ')} / no
                      benchmark downloads, runs, scores, or leaderboard claims.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[benchmarkResearchRegistry.status] ?? statusClass.ready}
                  >
                    {benchmarkResearchRegistry.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 rounded-[8px] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                  This entry exposes public benchmark metadata and local planning mappings only. It is evidence for
                  low-resource synthetic test design, not evidence that external LegalBench, LexGLUE, or COLIEE datasets
                  were downloaded, executed, scored, or used for product benchmark claims.
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkResearchRegistry.summary.source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">registry sources</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkResearchRegistry.summary.low_resource_action_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">low-resource actions</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-sm font-black uppercase text-stone-500">Dataset downloads</div>
                    <div className="mt-2 text-sm font-semibold text-stone-950">
                      {benchmarkResearchRegistry.low_resource_strategy.dataset_downloads.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {
                        benchmarkResearchRegistry.low_resource_strategy.fixture_cap
                          .max_fixtures_per_source_without_review
                      }
                    </div>
                    <div className="mt-1 text-sm text-stone-600">max fixtures/source without review</div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Public source</TableHead>
                        <TableHead>Local mapping</TableHead>
                        <TableHead>Low-resource action</TableHead>
                        <TableHead>Guardrails</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {benchmarkResearchRegistry.sources.map((source) => (
                        <TableRow key={source.public_name}>
                          <TableCell>
                            <a
                              className="inline-flex items-center gap-1 font-semibold text-stone-950 hover:underline"
                              href={source.public_link}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {source.public_name}
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                            <div className="mt-2 space-y-1 text-xs leading-5 text-stone-600">
                              {source.experience_takeaways.slice(0, 2).map((takeaway) => (
                                <div key={takeaway} className="flex gap-2">
                                  <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                                  <span>{takeaway}</span>
                                </div>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {Object.entries(source.project_mapping).map(([key, value]) => (
                              <div key={key}>
                                <span className="font-semibold text-stone-950">{key.replace(/_/g, ' ')}:</span>{' '}
                                {formatInline(value)}
                              </div>
                            ))}
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {source.low_resource_action}
                          </TableCell>
                          <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                            {source.forbidden_claims.slice(0, 2).map((claim) => (
                              <div key={claim} className="mb-1 flex gap-2">
                                <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-red-600" />
                                <span>{claim}</span>
                              </div>
                            ))}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Low-resource strategy</h3>
                    <div className="mb-3 flex flex-wrap gap-2">
                      <Badge variant="outline" className="bg-white">
                        {benchmarkResearchRegistry.low_resource_strategy.default_mode.replace(/_/g, ' ')}
                      </Badge>
                      <Badge variant="outline" className="bg-white">
                        network {benchmarkResearchRegistry.low_resource_strategy.network_access.replace(/_/g, ' ')}
                      </Badge>
                      <Badge variant="outline" className="bg-white">
                        sensitive data {benchmarkResearchRegistry.low_resource_strategy.sensitive_data.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {benchmarkResearchRegistry.low_resource_strategy.actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Allowed claims</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {benchmarkResearchRegistry.allowed_claims.map((claim) => (
                        <li key={claim} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-700" />
                          <span>{claim}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 text-xs leading-5 text-stone-500">{benchmarkResearchRegistry.privacy_note}</div>
                  </div>
                </div>
              </section>
            )}

            {feedbackRoadmap && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Feedback roadmap</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {feedbackRoadmap.rule_count} rules · {feedbackRoadmap.mapped_need_count}/
                      {feedbackRoadmap.coverage.radar_need_count} mapped needs
                    </div>
                  </div>
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                    {feedbackRoadmap.status}
                  </Badge>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rule</TableHead>
                        <TableHead>Need</TableHead>
                        <TableHead>Triage rules</TableHead>
                        <TableHead>Labels</TableHead>
                        <TableHead>Reason</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {feedbackRoadmap.rules.map((rule) => (
                        <TableRow key={rule.id}>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold text-stone-950">{rule.id}</div>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-stone-700">{rule.need_id}</TableCell>
                          <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                            {rule.triage_rule_ids.join(', ')}
                          </TableCell>
                          <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                            {rule.labels.join(', ')}
                          </TableCell>
                          <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{rule.reason}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                {feedbackRoadmap.coverage.unmapped_need_ids.length > 0 && (
                  <div className="mt-3 rounded-[8px] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                    Unmapped needs: {feedbackRoadmap.coverage.unmapped_need_ids.join(', ')}
                  </div>
                )}
              </section>
            )}

            {benchmark && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal review benchmark</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {benchmark.case_count} cases · {Object.keys(benchmark.suite.task_family_counts).length} task families ·{' '}
                      {Object.keys(benchmark.suite.required_metric_counts).length} metrics
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      benchmark.status === 'pass'
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                        : benchmark.status === 'fail'
                          ? 'border-red-200 bg-red-50 text-red-800'
                          : 'border-stone-200 bg-stone-50 text-stone-700'
                    }
                  >
                    {benchmark.status} · {benchmark.score}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{benchmark.passed_case_count}</div>
                    <div className="mt-1 text-sm text-stone-600">passed</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{benchmark.warning_case_count}</div>
                    <div className="mt-1 text-sm text-stone-600">warnings</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{benchmark.failed_case_count}</div>
                    <div className="mt-1 text-sm text-stone-600">failed</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{benchmark.not_run_case_count}</div>
                    <div className="mt-1 text-sm text-stone-600">not run</div>
                  </div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Case</TableHead>
                        <TableHead>Family</TableHead>
                        <TableHead>Route</TableHead>
                        <TableHead>Metrics</TableHead>
                        <TableHead>Gates</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {benchmark.suite.cases.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{item.title}</div>
                            <div className="mt-1 max-w-[420px] text-xs leading-5 text-stone-600">{item.scenario}</div>
                            <div className="mt-2 font-mono text-[11px] text-stone-500">{item.id}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="bg-white">
                              {item.task_family.replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-stone-600">{item.expected_route}</TableCell>
                          <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                            {item.required_metrics.join(', ')}
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[260px] flex-wrap gap-1">
                              {item.release_gate_links.map((gate) => (
                                <Badge key={gate} variant="outline" className="bg-white font-mono text-[11px]">
                                  {gate}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                {benchmark.recommended_actions.length > 0 && (
                  <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-white p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Benchmark actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {benchmark.recommended_actions.slice(0, 4).map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}

            {publicBenchmarkSampler && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Public benchmark sampler</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {publicBenchmarkSampler.summary.source_count} sources / max{' '}
                      {publicBenchmarkSampler.summary.max_samples_per_source} samples each /{' '}
                      {publicBenchmarkSampler.resource_policy.network_access.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[publicBenchmarkSampler.status] ?? statusClass.ready}>
                    {publicBenchmarkSampler.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkSampler.summary.sampling_ready_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">sampling ready</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkSampler.summary.license_review_required_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">license review</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkSampler.summary.catalog_only_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">catalog only</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkSampler.summary.local_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">local fixtures</div>
                  </div>
                </div>
                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Sampling state</TableHead>
                        <TableHead>Local mapping</TableHead>
                        <TableHead>Strategy</TableHead>
                        <TableHead>Gate</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {publicBenchmarkSampler.source_plans.map((source) => (
                        <TableRow key={source.source_id}>
                          <TableCell>
                            <a
                              className="inline-flex items-center gap-1 font-semibold text-stone-950 hover:underline"
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {source.title}
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{source.source_id}</div>
                            <div className="mt-2 text-xs text-stone-600">{source.resource_profile.replace(/_/g, ' ')}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[source.sampling_state] ?? statusClass.warn}>
                              {source.sampling_state.replace(/_/g, ' ')}
                            </Badge>
                            <div className="mt-2 text-xs text-stone-600">max {source.max_samples} samples</div>
                          </TableCell>
                          <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                            <div className="font-semibold text-stone-950">Fixtures</div>
                            <div className="break-words font-mono text-[11px]">{source.local_fixture_ids.join(', ')}</div>
                            <div className="mt-2 font-semibold text-stone-950">Cases</div>
                            <div className="break-words font-mono text-[11px]">{source.benchmark_case_ids.join(', ')}</div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {source.sample_strategy}
                            <div className="mt-2 font-mono text-[11px] text-stone-500">
                              {source.download_policy.replace(/_/g, ' ')}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            <div className="font-mono text-[11px] text-stone-950">{source.license_gate}</div>
                            <div className="mt-2">{source.recommended_action}</div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Sampler actions</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {publicBenchmarkSampler.recommended_actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 text-xs leading-5 text-stone-500">{publicBenchmarkSampler.privacy_note}</div>
                </div>
              </section>
            )}

            {fixtureEvidenceBundle && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture evidence bundle</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureEvidenceBundle.summary.component_count} components /{' '}
                      {fixtureEvidenceBundle.summary.release_decision.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[fixtureEvidenceBundle.status] ?? statusClass.warn}>
                    {fixtureEvidenceBundle.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureEvidenceBundle.summary.observed_fixture_count}/
                      {fixtureEvidenceBundle.summary.fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">observed fixtures</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureEvidenceBundle.summary.cheap_first_candidate_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first candidates</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureEvidenceBundle.summary.blocking_component_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">blocking components</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixtureEvidenceBundle.summary.estimated_cheap_first_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first estimate</div>
                  </div>
                </div>
                <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Component</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Endpoint</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fixtureEvidenceBundle.components.map((component) => (
                          <TableRow key={component.id}>
                            <TableCell className="font-mono text-xs text-stone-700">{component.id}</TableCell>
                            <TableCell>
                              <Badge variant="outline" className={statusClass[component.status] ?? statusClass.warn}>
                                {component.status.replace(/_/g, ' ')}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[320px] break-all font-mono text-[11px] text-stone-500">
                              {component.endpoint}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Release claims</h3>
                    <div className="space-y-4 text-sm leading-6 text-stone-700">
                      <div>
                        <div className="mb-1 font-semibold text-stone-950">Can claim</div>
                        <ul className="space-y-1">
                          {fixtureEvidenceBundle.release_claims.can_claim.map((claim) => (
                            <li key={claim} className="flex gap-2">
                              <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-700" />
                              <span>{claim}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="mb-1 font-semibold text-stone-950">After run</div>
                        <ul className="space-y-1">
                          {fixtureEvidenceBundle.release_claims.claim_after_run.map((claim) => (
                            <li key={claim} className="flex gap-2">
                              <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-amber-600" />
                              <span>{claim}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Bundle actions</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {fixtureEvidenceBundle.recommended_actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 text-xs leading-5 text-stone-500">{fixtureEvidenceBundle.privacy_note}</div>
                </div>
              </section>
            )}

            {fixtureModelMatrix && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture model matrix</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureModelMatrix.summary.fixture_count} fixtures /{' '}
                      {fixtureModelMatrix.summary.cheap_first_candidate_count} cheap-first candidates /{' '}
                      {fixtureModelMatrix.summary.operator_review_candidate_count} operator-review candidates
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[fixtureModelMatrix.status] ?? statusClass.warn}>
                    {fixtureModelMatrix.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixtureModelMatrix.summary.pass_count}</div>
                    <div className="mt-1 text-sm text-stone-600">passing ladders</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureModelMatrix.summary.premium_candidate_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">premium candidates</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureModelMatrix.summary.unknown_candidate_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">unknown candidates</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureModelMatrix.summary.warning_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">warnings</div>
                  </div>
                </div>
                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fixture</TableHead>
                        <TableHead>Budget</TableHead>
                        <TableHead>Cheap-first</TableHead>
                        <TableHead>Escalation candidates</TableHead>
                        <TableHead>Checks</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fixtureModelMatrix.fixtures.map((row) => {
                        const cheap = row.candidate_ladder.find((item) => item.role === 'cheap_first');
                        const escalation = row.candidate_ladder.filter((item) => item.role !== 'cheap_first').slice(0, 3);
                        return (
                          <TableRow key={row.fixture_id}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.fixture_id}</div>
                              <div className="mt-2 text-xs text-stone-600">route {row.smoke_route}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>{row.budget_mode}</div>
                              <div>max {row.max_cost_tier}</div>
                              <div className="font-mono text-[11px]">{row.runtime_default_model ?? '-'}</div>
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              <div className="font-mono font-semibold text-stone-950">{cheap?.model ?? '-'}</div>
                              <div>
                                {cheap?.cost_tier ?? '-'} / {cheap?.latency_tier ?? '-'}
                              </div>
                              <div>{cheap?.known_model ? 'catalog priced' : 'gateway price unknown'}</div>
                            </TableCell>
                            <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                              {escalation.map((candidate) => (
                                <div key={`${row.fixture_id}-${candidate.role}-${candidate.model}`} className="mb-1">
                                  <span className="font-mono text-[11px] text-stone-950">{candidate.model}</span>{' '}
                                  <span>
                                    {candidate.role.replace(/_/g, ' ')} / {candidate.cost_tier}
                                    {candidate.requires_operator_review ? ' / review' : ''}
                                  </span>
                                </div>
                              ))}
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <Badge variant="outline" className={statusClass[row.status] ?? statusClass.warn}>
                                {row.status}
                              </Badge>
                              <div className="mt-2">{row.recommended_action}</div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Matrix actions</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {fixtureModelMatrix.recommended_actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 text-xs leading-5 text-stone-500">{fixtureModelMatrix.privacy_note}</div>
                </div>
              </section>
            )}

            {fixturePromptPack && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture prompt pack</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixturePromptPack.summary.fixture_count} prompts / cheap trial{' '}
                      {fixturePromptPack.summary.cheap_trial_model}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[fixturePromptPack.status] ?? statusClass.review_recommended}
                  >
                    {fixturePromptPack.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixturePromptPack.summary.priced_prompt_count}</div>
                    <div className="mt-1 text-sm text-stone-600">priced prompts</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixturePromptPack.summary.estimated_total_request_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">estimated total</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixturePromptPack.summary.unknown_model_count}</div>
                    <div className="mt-1 text-sm text-stone-600">unknown models</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixturePromptPack.prompts.length}</div>
                    <div className="mt-1 text-sm text-stone-600">prompt rows</div>
                  </div>
                </div>
                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fixture</TableHead>
                        <TableHead>Model plan</TableHead>
                        <TableHead>Cost / params</TableHead>
                        <TableHead>Schema / follow-up</TableHead>
                        <TableHead>Prompt preview</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fixturePromptPack.prompts.map((prompt) => (
                        <TableRow key={prompt.fixture_id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{prompt.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{prompt.fixture_id}</div>
                            <div className="mt-2 text-xs text-stone-600">{prompt.matter_type}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            <div className="font-mono font-semibold text-stone-950">{prompt.recommended_model}</div>
                            <div className="mt-1">
                              task {prompt.recommended_task} / route {prompt.expected_route}
                            </div>
                            <div className="mt-1">
                              tier {prompt.recommended_model_cost_tier ?? 'gateway'} / cheap {prompt.cheap_trial_model}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div className="font-mono text-stone-950">{formatUsd(prompt.estimated_request_cost_usd)}</div>
                            <div>{prompt.prompt_tokens_estimate} prompt tokens</div>
                            <div>{prompt.completion_tokens_budget} max tokens</div>
                            <div>temp {prompt.request_parameters.temperature}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            <div>{prompt.output_schema.required.join(', ')}</div>
                            <div className="mt-2 space-y-1">
                              {prompt.follow_up_endpoints.map((endpoint) => (
                                <div key={endpoint} className="break-all font-mono text-[11px] text-stone-500">
                                  {endpoint}
                                </div>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                            {prompt.user_prompt.slice(0, 260)}
                            {prompt.user_prompt.length > 260 ? '...' : ''}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Method</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixturePromptPack.method.notes.map((note) => (
                        <li key={note} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixturePromptPack.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 text-xs leading-5 text-stone-500">{fixturePromptPack.privacy_note}</div>
                  </div>
                </div>
              </section>
            )}

            {fixtureRunPlan && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture run plan</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureRunPlan.summary.batch_count} batches / max parallel{' '}
                      {fixtureRunPlan.summary.max_parallel_requests}
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[fixtureRunPlan.status] ?? statusClass.warn}>
                    {fixtureRunPlan.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureRunPlan.summary.cheap_first_step_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first steps</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureRunPlan.summary.escalation_step_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">conditional escalations</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixtureRunPlan.summary.estimated_min_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap run estimate</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixtureRunPlan.summary.estimated_max_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">worst-case estimate</div>
                  </div>
                </div>
                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Batch</TableHead>
                        <TableHead>Model</TableHead>
                        <TableHead>Fixtures</TableHead>
                        <TableHead>Cost</TableHead>
                        <TableHead>Run order</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fixtureRunPlan.batches.map((batch) => (
                        <TableRow key={batch.batch_id}>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold text-stone-950">{batch.batch_id}</div>
                            <div className="mt-1 text-xs text-stone-600">{batch.phase.replace(/_/g, ' ')}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            <div className="font-mono font-semibold text-stone-950">{batch.model}</div>
                            <div className="mt-1">
                              task {batch.task} / tier {batch.model_cost_tier ?? 'gateway'}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            {batch.fixture_ids.join(', ')}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-stone-700">
                            {formatUsd(batch.estimated_batch_cost_usd)}
                          </TableCell>
                          <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                            {batch.run_after} / parallel {batch.max_parallel_requests}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Step</TableHead>
                          <TableHead>Request budget</TableHead>
                          <TableHead>Condition</TableHead>
                          <TableHead>Targets</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fixtureRunPlan.steps.slice(0, 8).map((step) => (
                          <TableRow key={step.step_id}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{step.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{step.step_id}</div>
                              <div className="mt-1 text-xs text-stone-600">{step.model}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>{step.prompt_tokens_estimate} prompt tokens</div>
                              <div>{step.completion_tokens_budget} max tokens</div>
                              <div className="font-mono text-stone-950">
                                {formatUsd(step.estimated_request_cost_usd)}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              {step.run_condition}
                            </TableCell>
                            <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                              <div className="break-all font-mono text-[11px]">{step.observation_target}</div>
                              <div className="break-all font-mono text-[11px]">{step.improvement_target}</div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Run policy</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixtureRunPlan.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 text-xs leading-5 text-stone-500">{fixtureRunPlan.privacy_note}</div>
                  </div>
                </div>
              </section>
            )}

            {fixtureLocalRunPackage && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture local run package</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureLocalRunPackage.summary.request_file_count} request files / max parallel{' '}
                      {fixtureLocalRunPackage.summary.max_parallel_requests}
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[fixtureLocalRunPackage.status] ?? statusClass.warn}>
                    {fixtureLocalRunPackage.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureLocalRunPackage.summary.selected_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">selected fixtures</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureLocalRunPackage.summary.request_file_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">request files</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixtureLocalRunPackage.summary.estimated_cheap_first_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first estimate</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureLocalRunPackage.summary.follow_up_endpoint_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">follow-up endpoints</div>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Request file</TableHead>
                          <TableHead>Model</TableHead>
                          <TableHead>Budget</TableHead>
                          <TableHead>Capture</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fixtureLocalRunPackage.request_files.map((request) => (
                          <TableRow key={request.file_name}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{request.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{request.file_name}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{request.fixture_id}</div>
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              <div className="font-mono font-semibold text-stone-950">{request.model}</div>
                              <div>
                                {request.phase.replace(/_/g, ' ')} / {request.model_cost_tier ?? 'gateway'}
                              </div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>{request.prompt_tokens_estimate} prompt tokens</div>
                              <div>{request.completion_tokens_budget} max tokens</div>
                              <div>body max {formatInline(request.body.max_tokens)}</div>
                              <div className="font-mono text-stone-950">
                                {formatUsd(request.estimated_request_cost_usd)}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <div className="font-mono text-[11px]">{request.response_capture.gateway_json_path}</div>
                              <div className="mt-1 break-all font-mono text-[11px]">
                                {request.response_capture.normalized_observation_path}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Environment</h3>
                    <div className="mb-3 flex flex-wrap gap-2">
                      {fixtureLocalRunPackage.environment.required_env.map((item) => (
                        <Badge key={item} variant="outline" className="bg-white font-mono">
                          {item}
                        </Badge>
                      ))}
                    </div>
                    <div className="mb-3 text-xs leading-5 text-stone-600">
                      {fixtureLocalRunPackage.environment.base_url_rule}
                    </div>
                    <div className="text-xs leading-5 text-stone-600">
                      {fixtureLocalRunPackage.environment.secret_policy}
                    </div>
                    <div className="mt-4 border-t border-stone-950/10 pt-3 text-xs leading-5 text-stone-500">
                      {fixtureLocalRunPackage.privacy_note}
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-black uppercase text-stone-500">Local run review paste</h3>
                      <div className="mt-1 text-xs leading-5 text-stone-500">
                        Paste one local gateway response and review it with the existing normalizer.
                      </div>
                    </div>
                    <Button
                      type="button"
                      className="law-button h-9"
                      onClick={normalizeFixtureReviewPayload}
                      disabled={fixtureReviewLoading}
                    >
                      {fixtureReviewLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Target className="h-4 w-4" />}
                      Review
                    </Button>
                  </div>
                  {fixtureReviewError && (
                    <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                      <AlertTriangle className="h-4 w-4" />
                      {fixtureReviewError}
                    </div>
                  )}
                  <div className="mb-3 grid gap-2 md:grid-cols-[1.4fr_1fr_0.8fr_0.8fr]">
                    <label>
                      <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Fixture</div>
                      <Select
                        value={fixtureReviewFixtureId || 'no_fixture'}
                        onValueChange={selectFixtureReviewFixture}
                        disabled={fixtureLocalRunPackage.request_files.length === 0}
                      >
                        <SelectTrigger className="h-9 rounded-[8px] bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {fixtureLocalRunPackage.request_files.length === 0 ? (
                            <SelectItem value="no_fixture" disabled>
                              No fixture
                            </SelectItem>
                          ) : (
                            fixtureLocalRunPackage.request_files.map((request) => (
                              <SelectItem key={request.fixture_id} value={request.fixture_id}>
                                {request.fixture_id}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </label>
                    <label>
                      <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Model</div>
                      <Input
                        value={fixtureReviewModel}
                        onChange={(event) => setFixtureReviewModel(event.target.value)}
                        className="h-9 rounded-[8px] bg-white text-sm"
                        placeholder="model"
                      />
                    </label>
                    <label>
                      <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">Route</div>
                      <Input
                        value={fixtureReviewRoute}
                        onChange={(event) => setFixtureReviewRoute(event.target.value)}
                        className="h-9 rounded-[8px] bg-white text-sm"
                        placeholder="fast"
                      />
                    </label>
                    <label>
                      <div className="mb-1 text-[11px] font-semibold uppercase text-stone-500">HTTP</div>
                      <Input
                        value={fixtureReviewHttpStatus}
                        onChange={(event) => setFixtureReviewHttpStatus(event.target.value)}
                        className="h-9 rounded-[8px] bg-white text-sm"
                        inputMode="numeric"
                        placeholder="200"
                      />
                    </label>
                  </div>
                  <Textarea
                    value={fixtureReviewPayloadText}
                    onChange={(event) => setFixtureReviewPayloadText(event.target.value)}
                    className="min-h-[118px] resize-y rounded-[8px] bg-white font-mono text-xs leading-5"
                    spellCheck={false}
                    placeholder='{"choices":[{"message":{"content":"{\"fixture_id\":\"fixture-service-agreement-small\",\"route\":\"fast\"}"}}]}'
                  />
                  <div className="mt-2 text-xs leading-5 text-stone-500">
                    Full normalizer payloads with a top-level responses object are accepted as pasted JSON.
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Step</TableHead>
                        <TableHead>PowerShell</TableHead>
                        <TableHead>Next action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fixtureLocalRunPackage.run_steps.map((step) => (
                        <TableRow key={step.step_id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{step.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{step.step_id}</div>
                            <div className="mt-1 text-xs text-stone-600">parallel {step.max_parallel_requests}</div>
                          </TableCell>
                          <TableCell className="max-w-[560px] font-mono text-[11px] leading-5 text-stone-600">
                            {step.command_templates.powershell}
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {step.next_local_action}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Follow-up endpoints</h3>
                    <div className="space-y-2">
                      {fixtureLocalRunPackage.follow_up_endpoints.map((endpoint) => (
                        <div key={endpoint} className="break-all font-mono text-xs text-stone-700">
                          {endpoint}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Package actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixtureLocalRunPackage.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}

            <section className="mb-8">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-stone-950">Legal fixture response normalizer</h2>
                  <div className="mt-1 text-sm text-stone-600">
                    {fixtureResponseNormalizer
                      ? `${fixtureResponseNormalizer.summary.normalized_observation_count} observations / ${fixtureResponseNormalizer.summary.redacted_response_count} redacted`
                      : 'convert local gateway responses into fixture-smoke and run-report payloads'}
                  </div>
                </div>
                <Badge variant="outline" className={statusClass[fixtureResponseNormalizer?.status ?? 'not_run'] ?? statusClass.warn}>
                  {(fixtureResponseNormalizer?.status ?? 'not_run').replace(/_/g, ' ')}
                </Badge>
              </div>

              {normalizerError && (
                <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  <AlertTriangle className="h-4 w-4" />
                  {normalizerError}
                </div>
              )}

              <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="font-semibold text-stone-950">Gateway response payload</div>
                      <div className="mt-1 text-xs text-stone-500">Paste local response JSON only; omit headers, keys, prompts, and client files.</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        className="soft-button"
                        onClick={loadNormalizerTemplate}
                        disabled={normalizerTemplateLoading}
                      >
                        {normalizerTemplateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clipboard className="h-4 w-4" />}
                        Template
                      </Button>
                      <Button type="button" className="law-button" onClick={normalizeFixtureResponse} disabled={normalizerLoading}>
                        {normalizerLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Target className="h-4 w-4" />}
                        Normalize
                      </Button>
                    </div>
                  </div>
                  <Textarea
                    value={normalizerPayloadText}
                    onChange={(event) => setNormalizerPayloadText(event.target.value)}
                    className="min-h-[280px] resize-y rounded-[8px] bg-white font-mono text-xs leading-5"
                    spellCheck={false}
                    placeholder='{"responses":{"fixture-service-agreement-small":{"route":"fast","model":"gemini-2.5-flash-lite","http_status":200,"gateway_response":{"choices":[{"message":{"content":"{\"fixture_id\":\"fixture-service-agreement-small\",\"route\":\"fast\"}"}}]}}}}'
                  />
                  <div className="mt-3 text-xs leading-5 text-stone-500">
                    {fixtureResponseNormalizer?.privacy_note ??
                      'The backend extracts message content, redacts secret-like values, and returns only normalized fixture payloads.'}
                  </div>
                </div>

                <div className="grid gap-3">
                  <div className="grid gap-3 sm:grid-cols-4">
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">
                        {fixtureResponseNormalizer?.summary.response_count ?? 0}
                      </div>
                      <div className="mt-1 text-sm text-stone-600">responses</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">
                        {fixtureResponseNormalizer?.summary.normalized_observation_count ?? 0}
                      </div>
                      <div className="mt-1 text-sm text-stone-600">observations</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">
                        {fixtureResponseNormalizer?.summary.parsed_json_content_count ?? 0}
                      </div>
                      <div className="mt-1 text-sm text-stone-600">JSON parsed</div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">
                        {fixtureResponseNormalizer?.summary.warning_check_count ?? 0}
                      </div>
                      <div className="mt-1 text-sm text-stone-600">warnings</div>
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fixture</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Model</TableHead>
                          <TableHead>Route</TableHead>
                          <TableHead>Content</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(fixtureResponseNormalizer?.response_summaries ?? []).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={5} className="py-6 text-center text-stone-500">
                              Load a template or paste a local gateway response to normalize.
                            </TableCell>
                          </TableRow>
                        ) : (
                          fixtureResponseNormalizer?.response_summaries.map((row) => (
                            <TableRow key={row.fixture_id}>
                              <TableCell>
                                <div className="font-mono text-xs font-semibold text-stone-950">{row.fixture_id}</div>
                                <div className="mt-1 text-[11px] text-stone-500">
                                  {row.known_fixture ? 'known fixture' : 'unknown fixture'}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className={statusClass[row.status] ?? statusClass.warn}>
                                  {row.status.replace(/_/g, ' ')}
                                </Badge>
                              </TableCell>
                              <TableCell className="max-w-[220px] font-mono text-xs text-stone-600">{row.model || '-'}</TableCell>
                              <TableCell className="font-mono text-xs text-stone-600">{row.route || '-'}</TableCell>
                              <TableCell className="text-xs leading-5 text-stone-600">
                                <div>{row.content_length} chars</div>
                                <div>{row.json_content_parsed ? 'JSON parsed' : 'plain text'}</div>
                                {row.redacted && <div className="font-semibold text-amber-700">redacted</div>}
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </div>

              {fixtureResponseNormalizer && (
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Next payloads</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>
                        <span className="font-semibold text-stone-950">fixture-smoke:</span>{' '}
                        <span className="font-mono">run_report_payload.observations</span>
                      </div>
                      <div>
                        <span className="font-semibold text-stone-950">run-report:</span>{' '}
                        <span className="font-mono">run_report_payload</span>
                      </div>
                      <div>
                        <span className="font-semibold text-stone-950">metadata rows:</span>{' '}
                        {Object.keys(fixtureResponseNormalizer.run_report_payload.run_metadata).length}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Normalizer actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixtureResponseNormalizer.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </section>

            {fixtureRunReport && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture run report</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureRunReport.summary.observed_fixture_count}/{fixtureRunReport.summary.fixture_count} observed /{' '}
                      {fixtureRunReport.release_decision.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[fixtureRunReport.status] ?? statusClass.warn}>
                    {fixtureRunReport.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureRunReport.summary.passed_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">passed fixtures</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureRunReport.summary.escalation_required_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">escalation required</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {formatUsd(fixtureRunReport.summary.observed_cost_usd)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">observed cost</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureRunReport.summary.high_priority_improvement_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">high-priority actions</div>
                  </div>
                </div>
                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fixture</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Model decision</TableHead>
                        <TableHead>Coverage gaps</TableHead>
                        <TableHead>Next step</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fixtureRunReport.fixture_reports.map((row) => (
                        <TableRow key={row.fixture_id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.fixture_id}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[row.smoke_status] ?? statusClass.not_run}>
                              {row.smoke_status.replace(/_/g, ' ')} / {row.score}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            <div className="font-mono font-semibold text-stone-950">
                              {row.observed_model ?? row.cheap_first_model ?? '-'}
                            </div>
                            <div className="mt-1">phase {row.observed_phase ?? '-'}</div>
                            <div className="mt-1">escalate {row.escalation_model ?? 'none'}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            <div>{row.missing_signal_count} missing signals</div>
                            <div>{row.missing_task_count} missing tasks</div>
                            <div>{row.high_priority_action_count} high-priority actions</div>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            {row.recommended_next_step.replace(/_/g, ' ')}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Evidence template</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div className="break-all font-mono">{fixtureRunReport.run_evidence_template.source_endpoint}</div>
                      <div className="font-mono">{fixtureRunReport.run_evidence_template.validation_command}</div>
                      <div>
                        cheap {formatUsd(fixtureRunReport.run_evidence_template.expected_cheap_first_cost_usd)} / worst{' '}
                        {formatUsd(fixtureRunReport.run_evidence_template.expected_worst_case_cost_usd)}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Report actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixtureRunReport.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 text-xs leading-5 text-stone-500">{fixtureRunReport.privacy_note}</div>
                  </div>
                </div>
              </section>
            )}

            {fixtureResultArchive && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture result archive</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureResultArchive.summary.archived_fixture_count} archived fixtures /{' '}
                      {fixtureResultArchive.summary.request_metadata_count} request metadata rows
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className={statusClass[fixtureResultArchive.status] ?? statusClass.warn}>
                      {fixtureResultArchive.status.replace(/_/g, ' ')}
                    </Badge>
                    <Badge variant="outline" className="border-stone-200 bg-white text-stone-700">
                      {fixtureResultArchive.summary.release_decision.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureResultArchive.summary.archived_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">archived fixtures</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureResultArchive.summary.request_metadata_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">request metadata</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureResultArchive.summary.dropped_raw_field_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">dropped raw fields</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="break-words text-xl font-black text-stone-950">
                      {fixtureResultArchive.summary.release_decision.replace(/_/g, ' ')}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">release decision</div>
                  </div>
                </div>

                <div className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Archive policy</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div className="break-all font-mono">{fixtureResultArchive.archive_record.source_endpoint}</div>
                      <div>
                        {fixtureResultArchive.summary.observed_fixture_count}/
                        {fixtureResultArchive.summary.fixture_count} observed fixtures
                      </div>
                      <div>
                        Evidence bundle: {fixtureResultArchive.summary.evidence_bundle_status.replace(/_/g, ' ')}
                      </div>
                      <div className="text-stone-500">{fixtureResultArchive.privacy_note}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Archive actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {fixtureResultArchive.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}

            {(fixtureSmoke || fixtureImprovement) && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal fixture smoke tests</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {fixtureSmoke?.fixture_count ?? 0} local fixtures 路 {fixtureImprovement?.summary.action_count ?? 0}{' '}
                      improvement actions
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {fixtureSmoke && (
                      <Badge variant="outline" className={statusClass[fixtureSmoke.status] ?? statusClass.not_run}>
                        smoke {fixtureSmoke.status.replace(/_/g, ' ')} 路 {fixtureSmoke.score}
                      </Badge>
                    )}
                    {fixtureImprovement && (
                      <Badge
                        variant="outline"
                        className={statusClass[fixtureImprovement.status] ?? statusClass.review_recommended}
                      >
                        plan {fixtureImprovement.status.replace(/_/g, ' ')}
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixtureSmoke?.passed_fixture_count ?? 0}</div>
                    <div className="mt-1 text-sm text-stone-600">fixture passes</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">{fixtureSmoke?.not_run_fixture_count ?? 0}</div>
                    <div className="mt-1 text-sm text-stone-600">not run</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureImprovement?.summary.high_priority_action_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">high-priority actions</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {fixtureImprovement?.summary.affected_fixture_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">affected fixtures</div>
                  </div>
                </div>

                {fixtureSmoke && (
                  <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fixture</TableHead>
                          <TableHead>Expected route</TableHead>
                          <TableHead>Expected signals</TableHead>
                          <TableHead>Expected outputs</TableHead>
                          <TableHead>Smoke result</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fixtureSmoke.template.fixtures.map((fixture) => {
                          const result = fixtureSmoke.fixture_results.find((item) => item.fixture_id === fixture.id);
                          return (
                            <TableRow key={fixture.id}>
                              <TableCell>
                                <div className="font-semibold text-stone-950">{fixture.title}</div>
                                <div className="mt-1 max-w-[360px] text-xs leading-5 text-stone-600">
                                  {fixture.input_excerpt}
                                </div>
                                <div className="mt-2 font-mono text-[11px] text-stone-500">{fixture.id}</div>
                              </TableCell>
                              <TableCell className="font-mono text-xs text-stone-600">
                                {fixture.expected_routes.join(', ') || '-'}
                              </TableCell>
                              <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                                {fixture.expected_signals.join(', ')}
                              </TableCell>
                              <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                                {fixture.expected_tasks.join(', ')}
                              </TableCell>
                              <TableCell>
                                <Badge
                                  variant="outline"
                                  className={statusClass[result?.status ?? 'not_run'] ?? statusClass.not_run}
                                >
                                  {(result?.status ?? 'not_run').replace(/_/g, ' ')} 路 {result?.score ?? 0}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {fixtureImprovement && (
                  <div className="grid gap-3 lg:grid-cols-[0.75fr_1.25fr]">
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Planner</h3>
                      <div className="space-y-3 text-sm text-stone-700">
                        <div>
                          <div className="text-xs font-semibold uppercase text-stone-500">Formula</div>
                          <div className="mt-1 leading-6">{fixtureSmoke?.template.method.score_formula ?? '-'}</div>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase text-stone-500">Resource policy</div>
                          <div className="mt-1 leading-6">{fixtureSmoke?.template.method.local_resource_policy ?? '-'}</div>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase text-stone-500">Privacy</div>
                          <div className="mt-1 leading-6">{fixtureImprovement.privacy_note}</div>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Prompt / schema actions</h3>
                      {fixtureImprovement.actions.length > 0 ? (
                        <div className="space-y-3">
                          {fixtureImprovement.actions.slice(0, 6).map((action) => (
                            <div key={action.id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                <Badge variant="outline" className={priorityClass[action.priority] ?? priorityClass.medium}>
                                  {action.priority}
                                </Badge>
                                <span className="font-mono text-xs text-stone-500">{action.schema_target}</span>
                              </div>
                              <div className="text-sm font-semibold text-stone-950">{action.report_section}</div>
                              <div className="mt-1 text-xs leading-5 text-stone-600">{action.prompt_clause}</div>
                              <div className="mt-2 text-[11px] leading-5 text-stone-500">{action.validation_hint}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <ul className="space-y-2 text-sm leading-6 text-stone-700">
                          {fixtureImprovement.recommended_actions.map((action) => (
                            <li key={action} className="flex gap-2">
                              <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                )}
              </section>
            )}

            {legalAudit && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal knowledge audit</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Generated {legalAudit.generated_at || '-'} · {legalAudit.record_count} records ·{' '}
                      {Math.round(legalAudit.reviewable_ratio * 100)}% verified
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      legalAudit.status === 'pass'
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                        : legalAudit.status === 'fail'
                          ? 'border-red-200 bg-red-50 text-red-800'
                          : 'border-amber-200 bg-amber-50 text-amber-900'
                    }
                  >
                    {legalAudit.status.toUpperCase()} / {legalAudit.score}
                  </Badge>
                </div>
                <div className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-xs font-semibold uppercase text-stone-500">Age</div>
                        <div className="mt-1 font-semibold text-stone-950">
                          {legalAudit.age_days ?? '-'} / {legalAudit.max_age_days} days
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase text-stone-500">Verified</div>
                        <div className="mt-1 font-semibold text-stone-950">
                          {legalAudit.verified_count}/{legalAudit.record_count}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase text-stone-500">Duplicates</div>
                        <div className="mt-1 font-semibold text-stone-950">{legalAudit.duplicate_source_ids.length}</div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase text-stone-500">Missing fields</div>
                        <div className="mt-1 font-semibold text-stone-950">{legalAudit.missing_required_fields.length}</div>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {legalAudit.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    {legalAudit.missing_critical_topics.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {legalAudit.missing_critical_topics.map((topic) => (
                          <Badge key={topic} variant="outline" className="bg-white">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </section>
            )}

            {ragPolicy && (
              <section className="mb-8">
                <div className="mb-3">
                  <h2 className="text-xl font-black text-stone-950">Legal RAG evaluation</h2>
                  <div className="mt-1 text-sm text-stone-600">
                    {ragPolicy.required_metrics.length} metrics · {ragPolicy.blocking_conditions.length} blockers
                  </div>
                </div>
                <div className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Metric weights</h3>
                    <div className="space-y-2">
                      {Object.entries(ragPolicy.metric_weights).map(([metric, weight]) => (
                        <div key={metric} className="flex items-center justify-between gap-3 text-sm">
                          <span className="font-mono text-xs text-stone-700">{metric.replace(/_/g, ' ')}</span>
                          <Badge variant="outline" className="bg-white">
                            {weight}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Blocking conditions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {ragPolicy.blocking_conditions.map((condition) => (
                        <li key={condition} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{condition}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {Object.entries(ragPolicy.status_thresholds).map(([status, threshold]) => (
                        <Badge key={status} variant="outline" className="bg-white">
                          {status}: {threshold}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

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
