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
  getFrontendUiRegressionGate,
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
  getLegalBenchmarkFixtureCrosswalk,
  getLegalDocumentBenchmarkCoverage,
  getLegalDocumentFactConsistencyBenchmark,
  getLegalAdoptionResearchBridge,
  getLegalBenchmarkResearchRegistry,
  getGeminiNewApiSelectorReplayEvidence,
  getLegalKnowledgeAudit,
  getModelOpsLegalFixtureCheapFirstBenchmarkGate,
  getModelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
  getLegalPublicBenchmarkLicenseGate,
  getLegalPublicBenchmarkSampler,
  getLegalRagAbstentionEscalationGate,
  getLegalRagAuthorityCitationGate,
  getLegalRagBenchmarkAlignment,
  getLegalRagHallucinationTriageGate,
  getLegalRagRetrievalDiagnosticsGate,
  getLegalResearchBacklog,
  getLegalReviewFixtureSmoke,
  getLegalReviewBenchmark,
  getLegalBenchmarkResearchRefresh,
  getModelRouteLegalBenchmarkRiskQueue,
  getLegalRagEvaluationPolicy,
  getLawyerReviewWorkflowPolicy,
  getMaintenanceContinuousSessionTimeline,
  getMaintenanceContinuousSessionReviewPacket,
  getMaintenanceEvidence,
  getMaintenanceGateSnapshot,
  getMaintenanceGitHistoryEvidence,
  getMaintenanceContinuousSessionRunMonitor,
  getMaintenanceValidationEventEvidence,
  getMatterAuditRetentionPolicy,
  getOcrImportReadinessPolicy,
  getFeedbackRoadmapCatalog,
  getGeminiNewApiModelAliasMatrixEvidence,
  getGeminiNewApiModelSelectorEvidence,
  getProductFeatureGapRadar,
  getReleaseReadiness,
  getUserNeedBenchmarkCoverage,
  getUserNeedGeminiRouteCoverage,
  getUserNeedImplementationPriorityQueue,
  getUserNeedsRadar,
  normalizeLegalFixtureResponse,
  postMaintenanceContinuousSessionRunMonitor,
  reviewContinuousUpdateLedger,
  reviewLegalFixtureLocalRun,
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
  type FrontendUiRegressionGate,
  type GeminiNewApiModelAliasMatrixEvidence,
  type GeminiNewApiModelSelectorEvidence,
  type GeminiNewApiSelectorReplayEvidence,
  type LawyerReviewWorkflowPolicy,
  type LegalDocumentExportReadiness,
  type LegalDocumentTemplateMatrix,
  type LegalFixtureEvidenceBundle,
  type LegalFixtureImprovementPlan,
  type LegalFixtureModelMatrix,
  type LegalFixturePromptPack,
  type LegalFixtureLocalRunPackage,
  type LegalFixtureLocalRunReview,
  type LegalFixtureResponseNormalizer,
  type LegalFixtureResultArchive,
  type LegalFixtureRunPlan,
  type LegalFixtureRunReport,
  type LegalAdoptionResearchBridge,
  type LegalBenchmarkFixtureCrosswalk,
  type LegalBenchmarkResearchRegistry,
  type LegalBenchmarkResearchRefresh,
  type LegalDocumentBenchmarkCoverage,
  type LegalDocumentFactConsistencyBenchmark,
  type LegalKnowledgeAudit,
  type LegalPublicBenchmarkLicenseGate,
  type LegalPublicBenchmarkSampler,
  type LegalRagAbstentionEscalationGate,
  type LegalRagAuthorityCitationGate,
  type LegalRagBenchmarkAlignment,
  type LegalRagHallucinationTriageGate,
  type LegalRagRetrievalDiagnosticsGate,
  type LegalResearchBacklog,
  type LegalReviewBenchmark,
  type LegalReviewFixtureSmoke,
  type LegalRagEvaluationPolicy,
  type MaintenanceContinuousSessionTimeline,
  type MaintenanceContinuousSessionRunMonitor,
  type MaintenanceContinuousSessionReviewPacket,
  type MaintenanceGateSnapshot,
  type MaintenanceGitHistoryEvidence,
  type MaintenanceValidationEventEvidence,
  type MaintenanceEvidenceProfile,
  type MaintenanceLanguage,
  type MatterAuditRetentionPolicy,
  type ModelOpsLegalFixtureCheapFirstBenchmarkGate,
  type ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
  type ModelRouteLegalBenchmarkRiskQueue,
  type OcrImportReadinessPolicy,
  type ProductFeatureGapRadar,
  type ReleaseReadinessResult,
  type ReleaseValidationCommand,
  type UserNeedBenchmarkCoverage,
  type UserNeedGeminiRouteCoverage,
  type UserNeedImplementationPriorityQueue,
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
  ready_for_review: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  complete: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  approved: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  covered: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  parsed: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  not_run: 'border-stone-200 bg-stone-50 text-stone-700',
  not_started: 'border-stone-200 bg-stone-50 text-stone-700',
  template: 'border-stone-200 bg-stone-50 text-stone-700',
  uploaded: 'border-stone-200 bg-stone-50 text-stone-700',
  preflight: 'border-sky-200 bg-sky-50 text-sky-800',
  collecting: 'border-sky-200 bg-sky-50 text-sky-800',
  running: 'border-sky-200 bg-sky-50 text-sky-800',
  warn: 'border-amber-200 bg-amber-50 text-amber-900',
  at_risk: 'border-amber-200 bg-amber-50 text-amber-900',
  needs_review: 'border-amber-200 bg-amber-50 text-amber-900',
  review_required: 'border-amber-200 bg-amber-50 text-amber-900',
  needs_attention: 'border-amber-200 bg-amber-50 text-amber-900',
  manual_review: 'border-amber-200 bg-amber-50 text-amber-900',
  cadence_reviewable: 'border-amber-200 bg-amber-50 text-amber-900',
  ocr_needed: 'border-amber-200 bg-amber-50 text-amber-900',
  review_recommended: 'border-amber-200 bg-amber-50 text-amber-900',
  pass_with_warnings: 'border-amber-200 bg-amber-50 text-amber-900',
  license_review_required: 'border-amber-200 bg-amber-50 text-amber-900',
  ready_with_gaps: 'border-amber-200 bg-amber-50 text-amber-900',
  ready_with_watchlist: 'border-amber-200 bg-amber-50 text-amber-900',
  partial: 'border-amber-200 bg-amber-50 text-amber-900',
  blocked: 'border-red-200 bg-red-50 text-red-800',
  gap: 'border-red-200 bg-red-50 text-red-800',
  missing: 'border-red-200 bg-red-50 text-red-800',
  ocr_failed: 'border-red-200 bg-red-50 text-red-800',
  sampling_ready: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  catalog_only: 'border-stone-200 bg-stone-50 text-stone-700',
  needs_escalation: 'border-red-200 bg-red-50 text-red-800',
  needs_improvement: 'border-red-200 bg-red-50 text-red-800',
  fail: 'border-red-200 bg-red-50 text-red-800',
  incomplete: 'border-red-200 bg-red-50 text-red-800',
  ready_with_blockers: 'border-red-200 bg-red-50 text-red-800',
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

function displayToken(value: string) {
  return value.replace(/_/g, ' ');
}

function shortHash(value?: string) {
  if (!value) return '-';
  return value.length > 12 ? value.slice(0, 12) : value;
}

function readinessStatus(value?: boolean) {
  return value ? 'ready' : 'blocked';
}

function boundaryValueIncluded(value: unknown) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value > 0;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, '_');
    if (!normalized || ['false', 'none', 'disabled', 'not_included', 'not_returned', 'metadata_only', 'no'].includes(normalized)) {
      return false;
    }
    return true;
  }
  return Boolean(value);
}

function boundaryFlag(boundary: Record<string, unknown> | undefined, keys: string[]) {
  if (!boundary) return false;
  return keys.some((key) => boundaryValueIncluded(boundary[key]));
}

function includedBoundaryLabel(value: unknown) {
  return boundaryValueIncluded(value) ? 'true / included' : 'false / not included';
}

function privacyBoundarySummary(boundary: MaintenanceGateSnapshot['gates'][number]['privacy_boundary']) {
  const outputScope = typeof boundary.output_scope === 'string' ? boundary.output_scope : 'metadata-only reviewer output';
  const flags = Object.entries(boundary)
    .filter(([key, value]) => key !== 'output_scope' && typeof value === 'boolean')
    .slice(0, 3)
    .map(([key, value]) => `${displayToken(key)}: ${String(value)}`);
  return [outputScope, ...flags];
}

function geminiNewApiPrivacyBoundarySummary(boundary: Record<string, unknown>) {
  const outputScope =
    typeof boundary.output_scope === 'string'
      ? boundary.output_scope
      : 'metadata-only model selector evidence; no NewAPI invocation claim';
  const flags = Object.entries(boundary)
    .filter(([key, value]) => key !== 'output_scope' && (typeof value === 'boolean' || typeof value === 'string'))
    .slice(0, 6)
    .map(([key, value]) => `${displayToken(key)}: ${formatInline(value)}`);
  return [outputScope, ...flags];
}

function blockerSummary(blocker: MaintenanceContinuousSessionTimeline['blockers'][number]) {
  if (typeof blocker === 'string') return blocker;
  return blocker.title ?? blocker.detail ?? blocker.required_action ?? blocker.code ?? blocker.id ?? 'review required';
}

function runMonitorBlockerSummary(blocker: MaintenanceContinuousSessionRunMonitor['blockers'][number]) {
  return blocker.detail || blocker.id || blocker.severity || 'review required';
}

function runMonitorActionSummary(action: MaintenanceContinuousSessionRunMonitor['next_actions'][number]) {
  return action.detail || action.id || 'record next checkpoint';
}

const validationEventTypes = ['test', 'credential_scan', 'push', 'review', 'legal_fixture'] as const;

function validationEventCount(data: MaintenanceValidationEventEvidence | null, eventType: string) {
  if (!data) return 0;
  const summary = data.summary;
  const fromGroupedCounts = summary.event_type_counts?.[eventType] ?? summary.counts?.[eventType];
  if (typeof fromGroupedCounts === 'number') return fromGroupedCounts;
  const directCount = summary[`${eventType}_count`];
  if (typeof directCount === 'number') return directCount;
  const normalizedCount = data.normalized_session_events.filter((event) => event.event_type === eventType).length;
  if (normalizedCount > 0) return normalizedCount;
  return data.event_reviews
    .filter((review) => review.event_type === eventType)
    .reduce((total, review) => total + (typeof review.count === 'number' ? review.count : 1), 0);
}

type LedgerBucket = 'completed_updates' | 'next_update_queue';
type LedgerEntryWithBucket = ContinuousUpdateLedgerEntry & { bucket: LedgerBucket };
type MaintenanceLoadFailure = {
  label: string;
  message: string;
};
type MaintenanceLoadTask = {
  label: string;
  run: () => Promise<unknown>;
  apply: (value: unknown) => void;
};

const MAINTENANCE_TASK_TIMEOUT_MS = 45000;

function maintenanceLoadFailureMessage(reason: unknown) {
  const status =
    (reason as { response?: { status?: number } })?.response?.status ??
    (reason as { status?: number })?.status ??
    null;
  if (status) return `HTTP ${status}`;
  if (reason instanceof Error && reason.message) return reason.message.slice(0, 180);
  return 'request failed';
}

function runMaintenanceLoadTask(task: MaintenanceLoadTask) {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(
      () => reject(new Error(`request timed out after ${MAINTENANCE_TASK_TIMEOUT_MS / 1000}s`)),
      MAINTENANCE_TASK_TIMEOUT_MS,
    );
  });

  return Promise.race([task.run(), timeout]).finally(() => {
    if (timeoutId) clearTimeout(timeoutId);
  });
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
  const [releaseReadiness, setReleaseReadiness] = useState<ReleaseReadinessResult | null>(null);
  const [validationCommands, setValidationCommands] = useState<ReleaseValidationCommand[]>([]);
  const [legalAudit, setLegalAudit] = useState<LegalKnowledgeAudit | null>(null);
  const [ragPolicy, setRagPolicy] = useState<LegalRagEvaluationPolicy | null>(null);
  const [legalRagAuthorityCitationGate, setLegalRagAuthorityCitationGate] =
    useState<LegalRagAuthorityCitationGate | null>(null);
  const [legalRagHallucinationTriageGate, setLegalRagHallucinationTriageGate] =
    useState<LegalRagHallucinationTriageGate | null>(null);
  const [legalRagAbstentionEscalationGate, setLegalRagAbstentionEscalationGate] =
    useState<LegalRagAbstentionEscalationGate | null>(null);
  const [legalRagRetrievalDiagnosticsGate, setLegalRagRetrievalDiagnosticsGate] =
    useState<LegalRagRetrievalDiagnosticsGate | null>(null);
  const [legalRagBenchmarkAlignment, setLegalRagBenchmarkAlignment] =
    useState<LegalRagBenchmarkAlignment | null>(null);
  const [maintenanceGateSnapshot, setMaintenanceGateSnapshot] = useState<MaintenanceGateSnapshot | null>(null);
  const [userNeeds, setUserNeeds] = useState<UserNeedsRadar | null>(null);
  const [userNeedBenchmarkCoverage, setUserNeedBenchmarkCoverage] = useState<UserNeedBenchmarkCoverage | null>(null);
  const [userNeedGeminiRouteCoverage, setUserNeedGeminiRouteCoverage] =
    useState<UserNeedGeminiRouteCoverage | null>(null);
  const [userNeedImplementationQueue, setUserNeedImplementationQueue] =
    useState<UserNeedImplementationPriorityQueue | null>(null);
  const [frontendUiRegressionGate, setFrontendUiRegressionGate] = useState<FrontendUiRegressionGate | null>(null);
  const [productFeatureGaps, setProductFeatureGaps] = useState<ProductFeatureGapRadar | null>(null);
  const [feedbackRoadmap, setFeedbackRoadmap] = useState<FeedbackRoadmapCatalog | null>(null);
  const [continuousLedger, setContinuousLedger] = useState<ContinuousUpdateLedger | null>(null);
  const [continuousSessionTimeline, setContinuousSessionTimeline] =
    useState<MaintenanceContinuousSessionTimeline | null>(null);
  const [continuousSessionRunMonitor, setContinuousSessionRunMonitor] =
    useState<MaintenanceContinuousSessionRunMonitor | null>(null);
  const [continuousSessionReviewPacket, setContinuousSessionReviewPacket] =
    useState<MaintenanceContinuousSessionReviewPacket | null>(null);
  const [gitHistoryEvidence, setGitHistoryEvidence] = useState<MaintenanceGitHistoryEvidence | null>(null);
  const [validationEventEvidence, setValidationEventEvidence] =
    useState<MaintenanceValidationEventEvidence | null>(null);
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
  const [adoptionResearchBridge, setAdoptionResearchBridge] = useState<LegalAdoptionResearchBridge | null>(null);
  const [benchmarkResearchRegistry, setBenchmarkResearchRegistry] =
    useState<LegalBenchmarkResearchRegistry | null>(null);
  const [legalBenchmarkResearchRefresh, setLegalBenchmarkResearchRefresh] =
    useState<LegalBenchmarkResearchRefresh | null>(null);
  const [modelRouteLegalBenchmarkRiskQueue, setModelRouteLegalBenchmarkRiskQueue] =
    useState<ModelRouteLegalBenchmarkRiskQueue | null>(null);
  const [modelOpsLegalFixtureCheapFirstBenchmarkGate, setModelOpsLegalFixtureCheapFirstBenchmarkGate] =
    useState<ModelOpsLegalFixtureCheapFirstBenchmarkGate | null>(null);
  const [
    modelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
    setModelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
  ] = useState<ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket | null>(null);
  const [publicBenchmarkSampler, setPublicBenchmarkSampler] = useState<LegalPublicBenchmarkSampler | null>(null);
  const [publicBenchmarkLicenseGate, setPublicBenchmarkLicenseGate] =
    useState<LegalPublicBenchmarkLicenseGate | null>(null);
  const [benchmarkFixtureCrosswalk, setBenchmarkFixtureCrosswalk] =
    useState<LegalBenchmarkFixtureCrosswalk | null>(null);
  const [fixtureEvidenceBundle, setFixtureEvidenceBundle] = useState<LegalFixtureEvidenceBundle | null>(null);
  const [fixtureModelMatrix, setFixtureModelMatrix] = useState<LegalFixtureModelMatrix | null>(null);
  const [geminiNewApiModelSelector, setGeminiNewApiModelSelector] =
    useState<GeminiNewApiModelSelectorEvidence | null>(null);
  const [geminiNewApiModelAliasMatrix, setGeminiNewApiModelAliasMatrix] =
    useState<GeminiNewApiModelAliasMatrixEvidence | null>(null);
  const [geminiNewApiSelectorReplay, setGeminiNewApiSelectorReplay] =
    useState<GeminiNewApiSelectorReplayEvidence | null>(null);
  const [fixturePromptPack, setFixturePromptPack] = useState<LegalFixturePromptPack | null>(null);
  const [fixtureLocalRunPackage, setFixtureLocalRunPackage] = useState<LegalFixtureLocalRunPackage | null>(null);
  const [legalDocumentBenchmarkCoverage, setLegalDocumentBenchmarkCoverage] =
    useState<LegalDocumentBenchmarkCoverage | null>(null);
  const [legalDocumentFactConsistencyBenchmark, setLegalDocumentFactConsistencyBenchmark] =
    useState<LegalDocumentFactConsistencyBenchmark | null>(null);
  const [fixtureResponseNormalizer, setFixtureResponseNormalizer] = useState<LegalFixtureResponseNormalizer | null>(null);
  const [fixtureLocalRunReview, setFixtureLocalRunReview] = useState<LegalFixtureLocalRunReview | null>(null);
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
  const [loadFailures, setLoadFailures] = useState<MaintenanceLoadFailure[]>([]);
  const [copied, setCopied] = useState(false);

  const load = async (nextLanguage = language) => {
    setLoading(true);
    setError('');
    setLoadFailures([]);
    try {
      const tasks: MaintenanceLoadTask[] = [
        {
          label: 'OSS evidence',
          run: () => getMaintenanceEvidence(nextLanguage),
          apply: (value) => setData(value as MaintenanceEvidenceProfile),
        },
        {
          label: 'Release readiness',
          run: getReleaseReadiness,
          apply: (value) => {
            const readiness = value as { data: ReleaseReadinessResult; validation_commands: ReleaseValidationCommand[] };
            setReleaseReadiness(readiness.data);
            setValidationCommands(readiness.validation_commands);
          },
        },
        { label: 'User needs radar', run: getUserNeedsRadar, apply: (value) => setUserNeeds(value as UserNeedsRadar) },
        {
          label: 'User need benchmark coverage',
          run: getUserNeedBenchmarkCoverage,
          apply: (value) => setUserNeedBenchmarkCoverage(value as UserNeedBenchmarkCoverage),
        },
        {
          label: 'User need Gemini route coverage',
          run: getUserNeedGeminiRouteCoverage,
          apply: (value) => setUserNeedGeminiRouteCoverage(value as UserNeedGeminiRouteCoverage),
        },
        {
          label: 'User need implementation priority queue',
          run: getUserNeedImplementationPriorityQueue,
          apply: (value) => setUserNeedImplementationQueue(value as UserNeedImplementationPriorityQueue),
        },
        {
          label: 'Frontend UI regression gate',
          run: getFrontendUiRegressionGate,
          apply: (value) => setFrontendUiRegressionGate(value as FrontendUiRegressionGate),
        },
        {
          label: 'Product feature gap radar',
          run: getProductFeatureGapRadar,
          apply: (value) => setProductFeatureGaps(value as ProductFeatureGapRadar),
        },
        {
          label: 'Feedback roadmap',
          run: getFeedbackRoadmapCatalog,
          apply: (value) => setFeedbackRoadmap(value as FeedbackRoadmapCatalog),
        },
        {
          label: 'Continuous update ledger',
          run: getContinuousUpdateLedger,
          apply: (value) => setContinuousLedger(value as ContinuousUpdateLedger),
        },
        {
          label: 'Continuous session timeline',
          run: getMaintenanceContinuousSessionTimeline,
          apply: (value) => setContinuousSessionTimeline(value as MaintenanceContinuousSessionTimeline),
        },
        {
          label: 'Continuous session run monitor',
          run: getMaintenanceContinuousSessionRunMonitor,
          apply: (value) => setContinuousSessionRunMonitor(value as MaintenanceContinuousSessionRunMonitor),
        },
        {
          label: 'Continuous session review packet',
          run: getMaintenanceContinuousSessionReviewPacket,
          apply: (value) => setContinuousSessionReviewPacket(value as MaintenanceContinuousSessionReviewPacket),
        },
        {
          label: 'Git history evidence',
          run: getMaintenanceGitHistoryEvidence,
          apply: (value) => setGitHistoryEvidence(value as MaintenanceGitHistoryEvidence),
        },
        {
          label: 'Validation event evidence',
          run: getMaintenanceValidationEventEvidence,
          apply: (value) => setValidationEventEvidence(value as MaintenanceValidationEventEvidence),
        },
        {
          label: 'Case intake completeness',
          run: getCaseIntakeCompleteness,
          apply: (value) => setCaseIntakeCompleteness(value as CaseIntakeCompleteness),
        },
        {
          label: 'Case team access policy',
          run: getCaseTeamAccessPolicy,
          apply: (value) => setCaseTeamAccessPolicy(value as CaseTeamAccessPolicy),
        },
        {
          label: 'Client delivery risk checklist',
          run: getClientDeliveryRiskChecklist,
          apply: (value) => setClientDeliveryRiskChecklist(value as ClientDeliveryRiskChecklist),
        },
        {
          label: 'Legal document template matrix',
          run: getLegalDocumentTemplateMatrix,
          apply: (value) => setLegalDocumentTemplateMatrix(value as LegalDocumentTemplateMatrix),
        },
        {
          label: 'Legal document export readiness',
          run: getLegalDocumentExportReadiness,
          apply: (value) => setLegalDocumentExportReadiness(value as LegalDocumentExportReadiness),
        },
        {
          label: 'OCR import readiness policy',
          run: getOcrImportReadinessPolicy,
          apply: (value) => setOcrImportReadinessPolicy(value as OcrImportReadinessPolicy),
        },
        {
          label: 'Case timeline deadline risk',
          run: getCaseTimelineDeadlineRisk,
          apply: (value) => setCaseTimelineDeadlineRisk(value as CaseTimelineDeadlineRisk),
        },
        {
          label: 'Matter audit retention policy',
          run: getMatterAuditRetentionPolicy,
          apply: (value) => setMatterAuditRetentionPolicy(value as MatterAuditRetentionPolicy),
        },
        {
          label: 'Lawyer review workflow policy',
          run: getLawyerReviewWorkflowPolicy,
          apply: (value) => setLawyerReviewWorkflowPolicy(value as LawyerReviewWorkflowPolicy),
        },
        {
          label: 'Evidence exhibit package policy',
          run: getEvidenceExhibitPackagePolicy,
          apply: (value) => setEvidenceExhibitPackagePolicy(value as EvidenceExhibitPackagePolicy),
        },
        {
          label: 'Case task notification policy',
          run: getCaseTaskNotificationPolicy,
          apply: (value) => setCaseTaskNotificationPolicy(value as CaseTaskNotificationPolicy),
        },
        {
          label: 'Case workbench payload',
          run: getCaseWorkbenchPayload,
          apply: (value) => setCaseWorkbenchPayload(value as CaseWorkbenchPayload),
        },
        {
          label: 'Legal review benchmark',
          run: getLegalReviewBenchmark,
          apply: (value) => setBenchmark(value as LegalReviewBenchmark),
        },
        {
          label: 'Legal document benchmark coverage',
          run: getLegalDocumentBenchmarkCoverage,
          apply: (value) => setLegalDocumentBenchmarkCoverage(value as LegalDocumentBenchmarkCoverage),
        },
        {
          label: 'Legal document fact consistency benchmark',
          run: getLegalDocumentFactConsistencyBenchmark,
          apply: (value) => setLegalDocumentFactConsistencyBenchmark(value as LegalDocumentFactConsistencyBenchmark),
        },
        {
          label: 'Legal research backlog',
          run: getLegalResearchBacklog,
          apply: (value) => setResearchBacklog(value as LegalResearchBacklog),
        },
        {
          label: 'Legal adoption research bridge',
          run: getLegalAdoptionResearchBridge,
          apply: (value) => setAdoptionResearchBridge(value as LegalAdoptionResearchBridge),
        },
        {
          label: 'Legal benchmark research registry',
          run: getLegalBenchmarkResearchRegistry,
          apply: (value) => setBenchmarkResearchRegistry(value as LegalBenchmarkResearchRegistry),
        },
        {
          label: 'Legal benchmark research refresh',
          run: getLegalBenchmarkResearchRefresh,
          apply: (value) => setLegalBenchmarkResearchRefresh(value as LegalBenchmarkResearchRefresh),
        },
        {
          label: 'Model route legal benchmark risk queue',
          run: getModelRouteLegalBenchmarkRiskQueue,
          apply: (value) => setModelRouteLegalBenchmarkRiskQueue(value as ModelRouteLegalBenchmarkRiskQueue),
        },
        {
          label: 'ModelOps legal fixture cheap-first benchmark gate',
          run: getModelOpsLegalFixtureCheapFirstBenchmarkGate,
          apply: (value) => setModelOpsLegalFixtureCheapFirstBenchmarkGate(value as ModelOpsLegalFixtureCheapFirstBenchmarkGate),
        },
        {
          label: 'ModelOps legal fixture cheap-first default promotion packet',
          run: getModelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
          apply: (value) =>
            setModelOpsLegalFixtureCheapFirstDefaultPromotionPacket(
              value as ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket,
            ),
        },
        {
          label: 'Legal public benchmark sampler',
          run: getLegalPublicBenchmarkSampler,
          apply: (value) => setPublicBenchmarkSampler(value as LegalPublicBenchmarkSampler),
        },
        {
          label: 'Legal public benchmark license gate',
          run: getLegalPublicBenchmarkLicenseGate,
          apply: (value) => setPublicBenchmarkLicenseGate(value as LegalPublicBenchmarkLicenseGate),
        },
        {
          label: 'Legal benchmark fixture crosswalk',
          run: getLegalBenchmarkFixtureCrosswalk,
          apply: (value) => setBenchmarkFixtureCrosswalk(value as LegalBenchmarkFixtureCrosswalk),
        },
        {
          label: 'Legal fixture evidence bundle',
          run: getLegalFixtureEvidenceBundle,
          apply: (value) => setFixtureEvidenceBundle(value as LegalFixtureEvidenceBundle),
        },
        {
          label: 'Legal fixture model matrix',
          run: getLegalFixtureModelMatrix,
          apply: (value) => setFixtureModelMatrix(value as LegalFixtureModelMatrix),
        },
        {
          label: 'Gemini/NewAPI model selector',
          run: getGeminiNewApiModelSelectorEvidence,
          apply: (value) => setGeminiNewApiModelSelector(value as GeminiNewApiModelSelectorEvidence),
        },
        {
          label: 'Gemini/NewAPI model alias matrix',
          run: getGeminiNewApiModelAliasMatrixEvidence,
          apply: (value) => setGeminiNewApiModelAliasMatrix(value as GeminiNewApiModelAliasMatrixEvidence),
        },
        {
          label: 'Gemini/NewAPI selector replay',
          run: getGeminiNewApiSelectorReplayEvidence,
          apply: (value) => setGeminiNewApiSelectorReplay(value as GeminiNewApiSelectorReplayEvidence),
        },
        {
          label: 'Legal fixture prompt pack',
          run: getLegalFixturePromptPack,
          apply: (value) => setFixturePromptPack(value as LegalFixturePromptPack),
        },
        {
          label: 'Legal fixture local run package',
          run: getLegalFixtureLocalRunPackage,
          apply: (value) => setFixtureLocalRunPackage(value as LegalFixtureLocalRunPackage),
        },
        {
          label: 'Legal fixture run plan',
          run: getLegalFixtureRunPlan,
          apply: (value) => setFixtureRunPlan(value as LegalFixtureRunPlan),
        },
        {
          label: 'Legal fixture run report',
          run: getLegalFixtureRunReport,
          apply: (value) => setFixtureRunReport(value as LegalFixtureRunReport),
        },
        {
          label: 'Legal fixture result archive',
          run: getLegalFixtureResultArchive,
          apply: (value) => setFixtureResultArchive(value as LegalFixtureResultArchive),
        },
        {
          label: 'Legal review fixture smoke',
          run: getLegalReviewFixtureSmoke,
          apply: (value) => setFixtureSmoke(value as LegalReviewFixtureSmoke),
        },
        {
          label: 'Legal fixture improvement plan',
          run: getLegalFixtureImprovementPlan,
          apply: (value) => setFixtureImprovement(value as LegalFixtureImprovementPlan),
        },
        {
          label: 'Legal knowledge audit',
          run: getLegalKnowledgeAudit,
          apply: (value) => setLegalAudit(value as LegalKnowledgeAudit),
        },
        {
          label: 'Legal RAG evaluation policy',
          run: getLegalRagEvaluationPolicy,
          apply: (value) => setRagPolicy(value as LegalRagEvaluationPolicy),
        },
        {
          label: 'Legal RAG authority citation gate',
          run: getLegalRagAuthorityCitationGate,
          apply: (value) => setLegalRagAuthorityCitationGate(value as LegalRagAuthorityCitationGate),
        },
        {
          label: 'Legal RAG retrieval diagnostics gate',
          run: getLegalRagRetrievalDiagnosticsGate,
          apply: (value) => setLegalRagRetrievalDiagnosticsGate(value as LegalRagRetrievalDiagnosticsGate),
        },
        {
          label: 'Legal RAG benchmark alignment',
          run: getLegalRagBenchmarkAlignment,
          apply: (value) => setLegalRagBenchmarkAlignment(value as LegalRagBenchmarkAlignment),
        },
        {
          label: 'Legal RAG hallucination triage gate',
          run: getLegalRagHallucinationTriageGate,
          apply: (value) => setLegalRagHallucinationTriageGate(value as LegalRagHallucinationTriageGate),
        },
        {
          label: 'Legal RAG abstention escalation gate',
          run: getLegalRagAbstentionEscalationGate,
          apply: (value) => setLegalRagAbstentionEscalationGate(value as LegalRagAbstentionEscalationGate),
        },
        {
          label: 'Maintenance gate snapshot',
          run: getMaintenanceGateSnapshot,
          apply: (value) => setMaintenanceGateSnapshot(value as MaintenanceGateSnapshot),
        },
      ];

      const failures: MaintenanceLoadFailure[] = [];
      await Promise.all(
        tasks.map(async (task) => {
          try {
            task.apply(await runMaintenanceLoadTask(task));
          } catch (reason) {
            console.error(`Maintenance evidence failed: ${task.label}`, reason);
            const failure = { label: task.label, message: maintenanceLoadFailureMessage(reason) };
            failures.push(failure);
            setLoadFailures((current) => [...current, failure]);
          }
        }),
      );
      setLoadFailures(failures);
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
  const timelineVerifiedHours =
    continuousSessionTimeline?.summary.verified_hours ??
    continuousSessionTimeline?.summary.verified_continuous_hours ??
    0;
  const timelineRemainingHours =
    continuousSessionTimeline?.summary.remaining_hours ??
    continuousSessionTimeline?.summary.continuous_hours_remaining ??
    0;
  const timelineLedgerCount =
    continuousSessionTimeline?.summary.ledger_count ??
    continuousSessionTimeline?.summary.completed_medium_large_update_count ??
    ledgerEntries.length;
  const timelineEventCount =
    continuousSessionTimeline?.summary.event_count ?? continuousSessionTimeline?.timeline_events.length ?? 0;
  const gitHistoryCommitCount = gitHistoryEvidence?.summary.commit_count ?? gitHistoryEvidence?.commit_events.length ?? 0;
  const gitHistoryLongestWindowHours =
    gitHistoryEvidence?.summary.longest_window_hours ??
    gitHistoryEvidence?.longest_window.verified_hours ??
    gitHistoryEvidence?.longest_window.duration_hours ??
    '-';
  const gitHistoryMaxGapHours =
    gitHistoryEvidence?.summary.max_observed_gap_hours ??
    gitHistoryEvidence?.summary.max_gap_hours ??
    gitHistoryEvidence?.longest_window.max_observed_gap_hours ??
    gitHistoryEvidence?.longest_window.max_gap_hours ??
    gitHistoryEvidence?.gap_analysis.reduce((maxGap, gap) => Math.max(maxGap, gap.gap_hours ?? 0), 0) ??
    '-';
  const gitHistoryStart =
    gitHistoryEvidence?.summary.start_timestamp ?? gitHistoryEvidence?.longest_window.start_timestamp ?? '-';
  const gitHistoryEnd =
    gitHistoryEvidence?.summary.end_timestamp ?? gitHistoryEvidence?.longest_window.end_timestamp ?? '-';
  const gitHistoryCompletionClaimState =
    gitHistoryEvidence?.summary.ready_for_goal_claim === true ||
    gitHistoryEvidence?.summary.completion_claim_ready === true
      ? 'ready'
      : 'blocked';
  const validationNormalizedEventCount =
    validationEventEvidence?.summary.normalized_event_count ??
    validationEventEvidence?.summary.normalized_session_event_count ??
    validationEventEvidence?.normalized_session_events.length ??
    0;
  const legalFixtureDocumentSummary = modelOpsLegalFixtureCheapFirstBenchmarkGate?.document_benchmark_summary;
  const legalFixtureDocumentRows = modelOpsLegalFixtureCheapFirstBenchmarkGate?.document_benchmark_rows ?? [];
  const legalFixtureFactConsistencySummary =
    modelOpsLegalFixtureCheapFirstBenchmarkGate?.fact_consistency_summary;
  const legalFixtureFactConsistencyRows =
    modelOpsLegalFixtureCheapFirstBenchmarkGate?.fact_consistency_rows ?? [];
  const legalFixtureDocumentAttentionRows = legalFixtureDocumentRows
    .filter((row) => row.default_change_blocker || row.gate_status !== 'pass')
    .slice(0, 3);
  const legalFixtureFactConsistencyAttentionRows = legalFixtureFactConsistencyRows
    .filter((row) => row.default_change_blocker || row.gate_status !== 'pass')
    .slice(0, 3);
  const hasLegalFixtureDocumentBenchmark =
    Boolean(legalFixtureDocumentSummary) ||
    (modelOpsLegalFixtureCheapFirstBenchmarkGate?.summary.document_benchmark_case_count ?? 0) > 0;
  const hasLegalFixtureFactConsistency =
    Boolean(legalFixtureFactConsistencySummary) ||
    (modelOpsLegalFixtureCheapFirstBenchmarkGate?.summary.fact_consistency_case_count ?? 0) > 0;
  const legalFixtureDefaultPromotionRows =
    modelOpsLegalFixtureCheapFirstDefaultPromotionPacket?.promotion_items ?? [];
  const legalFixtureDefaultPromotionAttentionRows = (
    legalFixtureDefaultPromotionRows.some((row) => row.promotion_status !== 'ready_for_maintainer_review')
      ? legalFixtureDefaultPromotionRows.filter((row) => row.promotion_status !== 'ready_for_maintainer_review')
      : legalFixtureDefaultPromotionRows
  ).slice(0, 3);
  const reviewPacketReadinessFlags = continuousSessionReviewPacket
    ? [
        { label: 'updates', value: continuousSessionReviewPacket.summary.update_count_ready },
        { label: 'timeline', value: continuousSessionReviewPacket.summary.timeline_completion_ready },
        { label: 'git', value: continuousSessionReviewPacket.summary.git_cadence_ready },
        { label: 'validation', value: continuousSessionReviewPacket.summary.validation_events_ready },
      ]
    : [];
  const lowResourceFixtureReviewSummary =
    continuousSessionReviewPacket?.source_summaries?.low_resource_fixture_review ?? null;
  const lowResourceFixtureReviewStatus =
    continuousSessionReviewPacket?.summary.low_resource_fixture_review_status ??
    lowResourceFixtureReviewSummary?.status ??
    'not_supplied';
  const lowResourceFixtureReviewObserved =
    continuousSessionReviewPacket?.summary.low_resource_fixture_review_observed_count ??
    lowResourceFixtureReviewSummary?.observed_fixture_count ??
    0;
  const lowResourceFixtureReviewNotRun =
    continuousSessionReviewPacket?.summary.low_resource_fixture_review_not_run_count ??
    lowResourceFixtureReviewSummary?.not_run_fixture_count ??
    0;
  const lowResourceFixtureReviewRedacted =
    continuousSessionReviewPacket?.summary.low_resource_fixture_review_redacted_count ??
    lowResourceFixtureReviewSummary?.redacted_response_count ??
    0;
  const runMonitorReadyEvidenceCount =
    continuousSessionRunMonitor?.summary.required_evidence_ready_count ??
    continuousSessionRunMonitor?.required_evidence.filter((item) => item.status === 'ready').length ??
    0;
  const runMonitorRequiredEvidenceCount =
    continuousSessionRunMonitor?.summary.required_evidence_count ??
    continuousSessionRunMonitor?.required_evidence.length ??
    0;
  const runMonitorCurrentGapHours = continuousSessionRunMonitor?.summary.current_gap_hours;
  const runMonitorMaxGapHours =
    continuousSessionRunMonitor?.summary.max_allowed_gap_hours ??
    continuousSessionRunMonitor?.checkpoint_policy.max_allowed_gap_hours ??
    '-';
  const runMonitorNextCheckpointDueAt = continuousSessionRunMonitor?.summary.next_checkpoint_due_at ?? null;
  const runMonitorNextCheckpointDueIn = continuousSessionRunMonitor?.summary.next_checkpoint_due_in_hours;
  const runMonitorLowResourceFixtureEvidence =
    continuousSessionRunMonitor?.low_resource_fixture_evidence ?? null;
  const runMonitorLowResourceFixtureSummary =
    continuousSessionRunMonitor?.source_summaries.low_resource_fixture_evidence ?? null;
  const runMonitorLowResourceFixtureStatus =
    continuousSessionRunMonitor?.summary.low_resource_fixture_evidence_status ??
    runMonitorLowResourceFixtureEvidence?.status ??
    runMonitorLowResourceFixtureSummary?.status ??
    'not_supplied';
  const runMonitorLowResourceFixtureObserved =
    continuousSessionRunMonitor?.summary.low_resource_fixture_evidence_observed_count ??
    runMonitorLowResourceFixtureEvidence?.summary.observed_fixture_count ??
    runMonitorLowResourceFixtureSummary?.observed_fixture_count ??
    0;
  const runMonitorLowResourceFixtureArchived =
    continuousSessionRunMonitor?.summary.low_resource_fixture_evidence_archived_count ??
    runMonitorLowResourceFixtureEvidence?.summary.archived_fixture_count ??
    runMonitorLowResourceFixtureSummary?.archived_fixture_count ??
    0;
  const runMonitorLowResourceFixtureBlocking =
    continuousSessionRunMonitor?.summary.low_resource_fixture_evidence_blocking_count ??
    runMonitorLowResourceFixtureEvidence?.summary.blocking_check_count ??
    runMonitorLowResourceFixtureSummary?.blocking_check_count ??
    0;

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
      const [normalized, review] = await Promise.all([
        normalizeLegalFixtureResponse(payload),
        reviewLegalFixtureLocalRun(payload),
      ]);
      setFixtureResponseNormalizer(normalized);
      setFixtureLocalRunReview(review);
      const fixtureReviewPayload = { low_resource_fixture_review: payload };
      const [ledgerWithFixtureEvidence, runMonitorWithFixtureEvidence] = await Promise.all([
        reviewContinuousUpdateLedger(fixtureReviewPayload),
        postMaintenanceContinuousSessionRunMonitor(fixtureReviewPayload),
      ]);
      setContinuousLedger(ledgerWithFixtureEvidence);
      setContinuousSessionRunMonitor(runMonitorWithFixtureEvidence);
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
      setFixtureLocalRunReview(null);
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

        {loadFailures.length > 0 && (
          <div className="mb-6 rounded-[8px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="h-4 w-4" />
              Partial maintenance evidence loaded
            </div>
            <div className="mt-1 text-xs leading-5 text-amber-900/80">
              {loadFailures.length} endpoint{loadFailures.length === 1 ? '' : 's'} failed. Available evidence remains
              visible so a single 500 or 404 does not hide the rest of the page.
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {loadFailures.map((failure) => (
                <Badge key={`${failure.label}-${failure.message}`} variant="outline" className="border-amber-200 bg-white">
                  {failure.label}: {failure.message}
                </Badge>
              ))}
            </div>
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

        {maintenanceGateSnapshot && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">100+ maintenance gates</h2>
                <div className="mt-1 text-sm text-stone-600">
                  metadata-only / no raw legal text / no benchmark or payment claims
                </div>
              </div>
              <Badge
                variant="outline"
                className={statusClass[maintenanceGateSnapshot.status] ?? statusClass.review_required}
              >
                {displayToken(maintenanceGateSnapshot.status)}
              </Badge>
            </div>

            <div className="overflow-hidden rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <div className="grid gap-3 border-b border-stone-950/10 p-4 sm:grid-cols-2 lg:grid-cols-5">
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {maintenanceGateSnapshot.summary.gate_count}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">new endpoints</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {maintenanceGateSnapshot.summary.ready_count}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">ready</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {maintenanceGateSnapshot.summary.blocked_count}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">blocked</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {maintenanceGateSnapshot.summary.reason_code_count}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">reason codes</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {maintenanceGateSnapshot.summary.metadata_only_count}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">metadata-only</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 border-b border-stone-950/10 px-4 py-3">
                {maintenanceGateSnapshot.labels.map((label) => (
                  <Badge key={label} variant="outline" className="bg-white">
                    {label}
                  </Badge>
                ))}
                <Badge variant="outline" className="border-red-200 bg-red-50 text-red-800">
                  unsupported claim reasons: {maintenanceGateSnapshot.summary.unsupported_claim_reason_count}
                </Badge>
                <Badge variant="outline" className="bg-white">
                  raw boundary violations: {maintenanceGateSnapshot.summary.raw_boundary_violation_count}
                </Badge>
              </div>

              <div className="divide-y divide-stone-950/10">
                {maintenanceGateSnapshot.gates.map((gate) => (
                  <div
                    key={gate.id}
                    className="grid gap-3 px-4 py-3 lg:grid-cols-[1.1fr_1fr_1.1fr_1.35fr]"
                  >
                    <div>
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className={statusClass[gate.status] ?? statusClass.not_run}>
                          {displayToken(gate.status)}
                        </Badge>
                        <span className="font-semibold text-stone-950">{gate.label}</span>
                      </div>
                      <div className="break-all font-mono text-[11px] text-stone-500">
                        {gate.method} {gate.endpoint}
                      </div>
                    </div>

                    <div className="flex flex-wrap content-start gap-2">
                      {gate.counts.map((count) => (
                        <Badge key={count.label} variant="outline" className="bg-white">
                          {count.label}: {formatInline(count.value)}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex flex-wrap content-start gap-2">
                      {gate.reason_codes.length > 0 ? (
                        <>
                          {gate.reason_codes.slice(0, 4).map((code) => (
                            <Badge key={code} variant="outline" className="bg-white">
                              {displayToken(code)}
                            </Badge>
                          ))}
                          {gate.reason_codes.length > 4 && (
                            <Badge variant="outline" className="bg-white">
                              +{gate.reason_codes.length - 4}
                            </Badge>
                          )}
                        </>
                      ) : (
                        <Badge variant="outline" className="bg-white">
                          no reason codes
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      {privacyBoundarySummary(gate.privacy_boundary)
                        .slice(0, 4)
                        .map((item) => (
                          <div key={item} className="break-words">
                            {item}
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {continuousSessionTimeline && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">24h evidence timeline</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Reviewer view of observed session evidence; 24h completion is not claimed here.
                </div>
              </div>
              <Badge
                variant="outline"
                className={statusClass[continuousSessionTimeline.status] ?? statusClass.in_progress}
              >
                {displayToken(continuousSessionTimeline.status)}
              </Badge>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(timelineVerifiedHours)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">verified hours</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(timelineRemainingHours)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">remaining hours</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(timelineLedgerCount)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">ledger count</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(timelineEventCount)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">event count</div>
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Blockers</h3>
                  {continuousSessionTimeline.blockers.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {continuousSessionTimeline.blockers.slice(0, 6).map((blocker, index) => (
                        <Badge key={`${blockerSummary(blocker)}-${index}`} variant="outline" className="bg-[#fbfaf6]">
                          {blockerSummary(blocker)}
                        </Badge>
                      ))}
                      {continuousSessionTimeline.blockers.length > 6 && (
                        <Badge variant="outline" className="bg-[#fbfaf6]">
                          +{continuousSessionTimeline.blockers.length - 6}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-stone-600">No blockers reported by the timeline endpoint.</div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {privacyBoundarySummary(continuousSessionTimeline.privacy_boundary)
                      .slice(0, 4)
                      .map((item) => (
                        <div key={item} className="break-words">
                          {item}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {continuousSessionRunMonitor && (
          <section className="mb-8">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-black text-stone-950">Continuous session run monitor</h2>
                  <div className="mt-1 text-sm text-stone-600">
                    Active-run checkpoint monitor; metadata-only status, readiness, blockers, and next actions.
                  </div>
                </div>
                <Badge
                  variant="outline"
                  className={statusClass[continuousSessionRunMonitor.status] ?? statusClass.in_progress}
                >
                  {displayToken(continuousSessionRunMonitor.status)}
                </Badge>
              </div>

              <div className="mb-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <div>
                  <div className="text-xl font-black text-stone-950">
                    {formatInline(continuousSessionRunMonitor.summary.elapsed_hours_since_start)} /{' '}
                    {formatInline(continuousSessionRunMonitor.summary.continuous_hours_remaining)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">elapsed / remaining hours</div>
                </div>
                <div>
                  <div className="text-xl font-black text-stone-950">
                    {formatInline(continuousSessionRunMonitor.summary.verified_continuous_hours)} /{' '}
                    {formatInline(continuousSessionRunMonitor.summary.target_continuous_hours)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">verified / target hours</div>
                </div>
                <div>
                  <div className="text-xl font-black text-stone-950">
                    {formatInline(runMonitorCurrentGapHours)} / {formatInline(runMonitorMaxGapHours)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">current / max gap hours</div>
                </div>
                <div>
                  <div className="break-all text-sm font-semibold text-stone-950">
                    {runMonitorNextCheckpointDueAt ?? 'not scheduled'}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">
                    next checkpoint
                    {typeof runMonitorNextCheckpointDueIn === 'number'
                      ? ` / ${runMonitorNextCheckpointDueIn}h`
                      : ''}
                  </div>
                </div>
                <div>
                  <div className="text-xl font-black text-stone-950">
                    {runMonitorReadyEvidenceCount}/{runMonitorRequiredEvidenceCount}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">required evidence ready</div>
                </div>
              </div>

              <div className="mb-3 flex flex-wrap gap-2">
                {continuousSessionRunMonitor.required_evidence.map((item) => (
                  <Badge
                    key={item.event_type}
                    variant="outline"
                    className={statusClass[item.status] ?? statusClass.review_required}
                  >
                    {displayToken(item.event_type)} {displayToken(item.status)}
                  </Badge>
                ))}
              </div>

              <div className="mb-3 rounded-[8px] border border-stone-950/10 bg-white p-3">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-xs font-black uppercase text-stone-500">Run monitor fixture evidence</h3>
                  <Badge
                    variant="outline"
                    className={statusClass[runMonitorLowResourceFixtureStatus] ?? statusClass.review_recommended}
                  >
                    {displayToken(runMonitorLowResourceFixtureStatus)}
                  </Badge>
                </div>
                <div className="grid gap-2 sm:grid-cols-4">
                  <div>
                    <div className="text-lg font-black text-stone-950">{runMonitorLowResourceFixtureObserved}</div>
                    <div className="text-xs font-semibold uppercase text-stone-500">observed fixtures</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-stone-950">{runMonitorLowResourceFixtureArchived}</div>
                    <div className="text-xs font-semibold uppercase text-stone-500">archived fixtures</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-stone-950">{runMonitorLowResourceFixtureBlocking}</div>
                    <div className="text-xs font-semibold uppercase text-stone-500">blocking checks</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-stone-950">
                      {readinessStatus(
                        continuousSessionRunMonitor.summary.low_resource_fixture_evidence_release_ready === true ||
                          runMonitorLowResourceFixtureEvidence?.summary.release_ready === true,
                      )}
                    </div>
                    <div className="text-xs font-semibold uppercase text-stone-500">release-ready evidence</div>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-stone-600">
                  <span>updates count mutated: false</span>
                  <span>completion ready mutated: false</span>
                  <span>raw gateway responses included: false</span>
                  <span>archive summaries only: true</span>
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-3">
                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Top blockers</h3>
                  {continuousSessionRunMonitor.blockers.length > 0 ? (
                    <div className="space-y-2">
                      {continuousSessionRunMonitor.blockers.slice(0, 3).map((blocker, index) => (
                        <div key={`${blocker.id}-${index}`} className="text-xs leading-5 text-stone-600">
                          <div className="mb-1 flex flex-wrap items-center gap-2">
                            <Badge
                              variant="outline"
                              className={blocker.severity === 'hard' ? statusClass.blocked : statusClass.review_required}
                            >
                              {displayToken(blocker.severity ?? 'review')}
                            </Badge>
                            <span className="font-mono text-[11px] font-semibold text-stone-950">
                              {blocker.id || 'blocker'}
                            </span>
                          </div>
                          <div>{runMonitorBlockerSummary(blocker)}</div>
                        </div>
                      ))}
                      {continuousSessionRunMonitor.blockers.length > 3 && (
                        <Badge variant="outline" className="bg-[#fbfaf6]">
                          +{continuousSessionRunMonitor.blockers.length - 3}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-stone-600">No active monitor blockers reported.</div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Top actions</h3>
                  <div className="space-y-2">
                    {continuousSessionRunMonitor.next_actions.slice(0, 3).map((action) => (
                      <div key={action.id} className="text-xs leading-5 text-stone-600">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className={priorityClass[action.priority ?? 'medium'] ?? priorityClass.medium}>
                            {displayToken(action.priority ?? 'medium')}
                          </Badge>
                          <span className="font-mono text-[11px] font-semibold text-stone-950">{action.id}</span>
                        </div>
                        <div>{runMonitorActionSummary(action)}</div>
                      </div>
                    ))}
                    {continuousSessionRunMonitor.next_actions.length === 0 && (
                      <div className="text-sm text-stone-600">No monitor actions reported.</div>
                    )}
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {privacyBoundarySummary(continuousSessionRunMonitor.privacy_boundary)
                      .slice(0, 4)
                      .map((item) => (
                        <div key={item} className="break-words">
                          {item}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {continuousSessionReviewPacket && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Continuous session review packet</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Metadata-only packet; excludes raw legal text, raw logs, raw model outputs, credentials, and emails.
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant="outline"
                  className={statusClass[continuousSessionReviewPacket.status] ?? statusClass.review_required}
                >
                  {displayToken(continuousSessionReviewPacket.status)}
                </Badge>
                <Badge variant="outline" className="bg-white font-mono">
                  {shortHash(continuousSessionReviewPacket.summary.packet_hash)}
                </Badge>
              </div>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
                {reviewPacketReadinessFlags.map((flag) => (
                  <div key={flag.label}>
                    <Badge
                      variant="outline"
                      className={statusClass[readinessStatus(flag.value)] ?? statusClass.warn}
                    >
                      {flag.label} {readinessStatus(flag.value)}
                    </Badge>
                  </div>
                ))}
                <div>
                  <Badge
                    variant="outline"
                    className={
                      statusClass[readinessStatus(continuousSessionReviewPacket.summary.packet_ready_for_support_claim)] ??
                      statusClass.warn
                    }
                  >
                    support claim {readinessStatus(continuousSessionReviewPacket.summary.packet_ready_for_support_claim)}
                  </Badge>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {formatInline(
                      continuousSessionReviewPacket.summary.blocker_count ??
                        continuousSessionReviewPacket.blockers.length,
                    )}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">blockers</div>
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr]">
                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Blockers</h3>
                  {continuousSessionReviewPacket.blockers.length > 0 ? (
                    <div className="space-y-2">
                      {continuousSessionReviewPacket.blockers.slice(0, 4).map((blocker) => (
                        <div key={blocker.id} className="text-xs leading-5 text-stone-600">
                          <div className="font-mono text-[11px] font-semibold text-stone-950">{blocker.id}</div>
                          <div>{blocker.detail ?? blocker.severity ?? 'review required'}</div>
                        </div>
                      ))}
                      {continuousSessionReviewPacket.blockers.length > 4 && (
                        <Badge variant="outline" className="bg-[#fbfaf6]">
                          +{continuousSessionReviewPacket.blockers.length - 4}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-stone-600">No packet blockers reported.</div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Low-resource fixture review</h3>
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <Badge
                      variant="outline"
                      className={statusClass[lowResourceFixtureReviewStatus] ?? statusClass.review_recommended}
                    >
                      {displayToken(lowResourceFixtureReviewStatus)}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        statusClass[
                          readinessStatus(
                            continuousSessionReviewPacket.summary.low_resource_fixture_review_blocked === false,
                          )
                        ] ?? statusClass.warn
                      }
                    >
                      fixture packet boundary
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <div className="text-lg font-black text-stone-950">{lowResourceFixtureReviewObserved}</div>
                      <div className="font-semibold uppercase text-stone-500">observed</div>
                    </div>
                    <div>
                      <div className="text-lg font-black text-stone-950">{lowResourceFixtureReviewNotRun}</div>
                      <div className="font-semibold uppercase text-stone-500">not run</div>
                    </div>
                    <div>
                      <div className="text-lg font-black text-stone-950">{lowResourceFixtureReviewRedacted}</div>
                      <div className="font-semibold uppercase text-stone-500">redacted</div>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1 text-xs leading-5 text-stone-600">
                    <div>raw fixture payload echoed: false</div>
                    <div>raw gateway responses included: false</div>
                    <div>raw model outputs included: false</div>
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {privacyBoundarySummary(continuousSessionReviewPacket.privacy_boundary)
                      .slice(0, 4)
                      .map((item) => (
                        <div key={item} className="break-words">
                          {item}
                        </div>
                      ))}
                    <div>raw model outputs included: false</div>
                    <div>credentials and emails included: false</div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {validationEventEvidence && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Validation event evidence</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Metadata-only validation evidence; raw logs and raw legal text are not included. No 24h completion
                  claim is made here.
                </div>
              </div>
              <Badge
                variant="outline"
                className={statusClass[validationEventEvidence.status] ?? statusClass.review_required}
              >
                {displayToken(validationEventEvidence.status)}
              </Badge>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
                {validationEventTypes.map((eventType) => (
                  <div key={eventType}>
                    <div className="text-2xl font-black text-stone-950">
                      {validationEventCount(validationEventEvidence, eventType)}
                    </div>
                    <div className="text-xs font-semibold uppercase text-stone-500">{displayToken(eventType)}</div>
                  </div>
                ))}
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {formatInline(validationNormalizedEventCount)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">normalized events</div>
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Missing types</h3>
                  {validationEventEvidence.missing_event_types.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {validationEventEvidence.missing_event_types.map((eventType) => (
                        <Badge key={eventType} variant="outline" className="bg-[#fbfaf6]">
                          {displayToken(eventType)}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-stone-600">No missing validation event types reported.</div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {privacyBoundarySummary(validationEventEvidence.privacy_boundary)
                      .slice(0, 4)
                      .map((item) => (
                        <div key={item} className="break-words">
                          {item}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {gitHistoryEvidence && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Git history evidence</h2>
                <div className="mt-1 text-sm text-stone-600">
                  Reviewer view of git commit cadence evidence; no 24h completion claim is made here.
                </div>
              </div>
              <Badge variant="outline" className={statusClass[gitHistoryEvidence.status] ?? statusClass.in_progress}>
                {displayToken(gitHistoryEvidence.status)}
              </Badge>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(gitHistoryCommitCount)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">commit count</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">
                    {formatInline(gitHistoryLongestWindowHours)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">longest window hours</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-stone-950">{formatInline(gitHistoryMaxGapHours)}</div>
                  <div className="text-xs font-semibold uppercase text-stone-500">max gap hours</div>
                </div>
                <div className="sm:col-span-2 lg:col-span-1">
                  <div className="break-all font-mono text-xs font-semibold leading-5 text-stone-950">
                    {formatInline(gitHistoryStart)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">start</div>
                </div>
                <div className="sm:col-span-2 lg:col-span-1">
                  <div className="break-all font-mono text-xs font-semibold leading-5 text-stone-950">
                    {formatInline(gitHistoryEnd)}
                  </div>
                  <div className="text-xs font-semibold uppercase text-stone-500">end</div>
                </div>
                <div>
                  <Badge
                    variant="outline"
                    className={statusClass[gitHistoryCompletionClaimState] ?? statusClass.warn}
                  >
                    completion claim {gitHistoryCompletionClaimState}
                  </Badge>
                </div>
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Recent commit events</h3>
                  {gitHistoryEvidence.commit_events.length > 0 ? (
                    <div className="space-y-2">
                      {gitHistoryEvidence.commit_events.slice(0, 3).map((event) => (
                        <div key={event.commit_hash} className="text-xs leading-5 text-stone-600">
                          <div className="font-semibold text-stone-950">{event.title ?? event.subject ?? 'commit metadata'}</div>
                          <div className="font-mono text-[11px] text-stone-500">
                            {event.commit_hash} / {event.timestamp ?? event.committed_at ?? '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-stone-600">No commit events returned by the evidence endpoint.</div>
                  )}
                </div>

                <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                  <h3 className="mb-2 text-xs font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {privacyBoundarySummary(gitHistoryEvidence.privacy_boundary)
                      .slice(0, 4)
                      .map((item) => (
                        <div key={item} className="break-words">
                          {item}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

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
                  <div className="break-all font-mono text-[11px] text-stone-500">
                    {continuousLedger.low_resource_test_policy.ledger_review_endpoint ??
                      '/api/v1/maintenance/continuous-update-ledger'}
                  </div>
                  <div className="break-all font-mono text-[11px] text-stone-500">
                    {continuousLedger.low_resource_test_policy.run_monitor_review_endpoint ??
                      '/api/v1/maintenance/continuous-session-run-monitor'}
                  </div>
                </div>

                <div className="mt-4 border-t border-stone-950/10 pt-4">
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <h4 className="text-xs font-black uppercase text-stone-500">Ledger fixture evidence</h4>
                    <Badge
                      variant="outline"
                      className={
                        statusClass[continuousLedger.low_resource_fixture_evidence.status] ??
                        statusClass.review_recommended
                      }
                    >
                      {displayToken(continuousLedger.low_resource_fixture_evidence.status)}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-lg font-black text-stone-950">
                        {continuousLedger.low_resource_fixture_evidence.summary.observed_fixture_count}
                      </div>
                      <div className="font-semibold uppercase text-stone-500">observed</div>
                    </div>
                    <div>
                      <div className="text-lg font-black text-stone-950">
                        {continuousLedger.low_resource_fixture_evidence.summary.archived_fixture_count}
                      </div>
                      <div className="font-semibold uppercase text-stone-500">archived</div>
                    </div>
                    <div>
                      <div className="text-lg font-black text-stone-950">
                        {continuousLedger.low_resource_fixture_evidence.summary.dropped_raw_field_count}
                      </div>
                      <div className="font-semibold uppercase text-stone-500">raw fields dropped</div>
                    </div>
                    <div>
                      <div className="text-lg font-black text-stone-950">
                        {continuousLedger.low_resource_fixture_evidence.summary.blocking_check_count}
                      </div>
                      <div className="font-semibold uppercase text-stone-500">blocking checks</div>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1 text-xs leading-5 text-stone-600">
                    <div>
                      review: {displayToken(continuousLedger.low_resource_fixture_evidence.summary.review_status)}
                    </div>
                    <div>
                      archive: {displayToken(continuousLedger.low_resource_fixture_evidence.summary.archive_status)}
                    </div>
                    <div>updates count mutated: false</div>
                    <div>raw gateway responses included: false</div>
                    <div>archive summaries only: true</div>
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
                                  {entry.evidence_paths.slice(0, 2).map((path, index) => (
                                    <div key={`${entry.id}-${path}-${index}`} className="break-all font-mono text-[11px]">
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

            {frontendUiRegressionGate && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Frontend UI regression gate</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {frontendUiRegressionGate.summary.ready_command_gate_count}/
                      {frontendUiRegressionGate.summary.required_command_gate_count} command gates ready /{' '}
                      {frontendUiRegressionGate.summary.missing_page_automation_count} automation gaps
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[frontendUiRegressionGate.status] ?? statusClass.warn}
                  >
                    {displayToken(frontendUiRegressionGate.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  {[
                    { label: 'pages', value: frontendUiRegressionGate.summary.page_count },
                    { label: 'command gates', value: frontendUiRegressionGate.summary.command_gate_count },
                    { label: 'protected panels', value: frontendUiRegressionGate.summary.protected_panel_count },
                    { label: 'missing automation', value: frontendUiRegressionGate.summary.missing_page_automation_count },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Gate</TableHead>
                          <TableHead>Ready</TableHead>
                          <TableHead>Command</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {frontendUiRegressionGate.command_gates.map((gate) => (
                          <TableRow key={gate.id}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{displayToken(gate.id)}</div>
                              <div className="mt-1 max-w-[340px] text-xs leading-5 text-stone-600">{gate.purpose}</div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={statusClass[readinessStatus(gate.ready)] ?? statusClass.warn}
                              >
                                {gate.ready ? 'ready' : 'missing'}
                              </Badge>
                              {gate.gap_reason && (
                                <div className="mt-2 font-mono text-[11px] text-stone-500">{gate.gap_reason}</div>
                              )}
                            </TableCell>
                            <TableCell className="font-mono text-xs text-stone-600">{gate.command}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Page</TableHead>
                          <TableHead>Protected panels</TableHead>
                          <TableHead>Missing automation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {frontendUiRegressionGate.page_rows.map((row) => (
                          <TableRow key={row.route}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{row.route}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_path}</div>
                              <Badge
                                variant="outline"
                                className={statusClass[row.status] ?? statusClass.warn}
                              >
                                {displayToken(row.status)}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                              {row.protected_panels.join(', ')}
                            </TableCell>
                            <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                              {row.missing_automation.join(', ') || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Failure modes</h3>
                    <div className="grid gap-3 md:grid-cols-3">
                      {frontendUiRegressionGate.failure_modes.map((mode) => (
                        <div key={mode.id} className="rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3">
                          <div className="font-semibold text-stone-950">{displayToken(mode.id)}</div>
                          <div className="mt-1 text-xs text-stone-500">{mode.page}</div>
                          <div className="mt-2 text-xs leading-5 text-stone-600">{mode.regression_target}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>source code returned: {String(frontendUiRegressionGate.privacy_boundary.returns_source_code)}</div>
                      <div>browser storage returned: {String(frontendUiRegressionGate.privacy_boundary.returns_raw_browser_storage)}</div>
                      <div>raw model output returned: {String(frontendUiRegressionGate.privacy_boundary.returns_raw_model_output)}</div>
                      <div>credentials returned: {String(frontendUiRegressionGate.privacy_boundary.returns_credentials)}</div>
                    </div>
                    <h3 className="mb-2 mt-4 text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {frontendUiRegressionGate.recommended_actions.map((action) => (
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

            {userNeedBenchmarkCoverage && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">User need benchmark coverage</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {userNeedBenchmarkCoverage.summary.covered_need_count} covered /{' '}
                      {userNeedBenchmarkCoverage.summary.partial_need_count} partial /{' '}
                      {userNeedBenchmarkCoverage.summary.gap_need_count} gaps
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[userNeedBenchmarkCoverage.status] ?? statusClass.warn}
                  >
                    {displayToken(userNeedBenchmarkCoverage.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-9">
                  {[
                    { label: 'high-priority gaps', value: userNeedBenchmarkCoverage.summary.high_priority_gap_count },
                    { label: 'covered needs', value: userNeedBenchmarkCoverage.summary.covered_need_count },
                    { label: 'synthetic fixtures', value: userNeedBenchmarkCoverage.summary.synthetic_fixture_count },
                    { label: 'benchmark cases', value: userNeedBenchmarkCoverage.summary.benchmark_case_count },
                    { label: 'backlog items', value: userNeedBenchmarkCoverage.summary.research_backlog_item_count },
                    { label: 'public sources', value: userNeedBenchmarkCoverage.summary.public_benchmark_source_count },
                    {
                      label: 'public review needs',
                      value: userNeedBenchmarkCoverage.summary.public_benchmark_license_review_required_need_count,
                    },
                    {
                      label: 'calibrated needs',
                      value: userNeedBenchmarkCoverage.summary.cheap_first_calibration_mapped_need_count,
                    },
                    {
                      label: 'calibration attention',
                      value: userNeedBenchmarkCoverage.summary.cheap_first_calibration_attention_need_count,
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Need</TableHead>
                          <TableHead>Coverage</TableHead>
                          <TableHead>Benchmark links</TableHead>
                          <TableHead>Public benchmark</TableHead>
                          <TableHead>Calibration</TableHead>
                          <TableHead>Gap / next action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {userNeedBenchmarkCoverage.coverage_rows.slice(0, 8).map((row) => (
                          <TableRow key={row.need_id}>
                            <TableCell className="max-w-[340px]">
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.need_id}</div>
                              <div className="mt-2 text-xs text-stone-600">{displayToken(row.category)}</div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={statusClass[row.coverage_status] ?? statusClass.warn}
                              >
                                {displayToken(row.coverage_status)}
                              </Badge>
                              <div className="mt-2">
                                <Badge
                                  variant="outline"
                                  className={priorityClass[row.priority_band] ?? priorityClass.medium}
                                >
                                  {row.priority_band} / {row.priority_score}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                              <div>cases: {row.linked_benchmark_case_ids.join(', ') || '-'}</div>
                              <div>fixtures: {row.linked_fixture_ids.join(', ') || '-'}</div>
                              <div>docs: {row.linked_document_fixture_ids.join(', ') || '-'}</div>
                              <div>backlog: {row.linked_backlog_item_ids.join(', ') || '-'}</div>
                            </TableCell>
                            <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                              <Badge
                                variant="outline"
                                className={statusClass[row.public_benchmark_status] ?? statusClass.warn}
                              >
                                {displayToken(row.public_benchmark_status)}
                              </Badge>
                              <div className="mt-2">sources: {row.linked_public_source_ids.join(', ') || '-'}</div>
                              <div>batches: {row.linked_public_sampling_batch_ids.join(', ') || '-'}</div>
                              <div className="font-mono text-[11px] text-stone-500">
                                states:{' '}
                                {Object.entries(row.public_sampling_states)
                                  .map(([sourceId, state]) => `${sourceId}:${displayToken(state)}`)
                                  .join(', ') || '-'}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                              <Badge
                                variant="outline"
                                className={statusClass[row.calibration_status] ?? statusClass.warn}
                              >
                                {displayToken(row.calibration_status)}
                              </Badge>
                              <div className="mt-2">tasks: {row.linked_calibration_task_ids.join(', ') || '-'}</div>
                              <div>gates: {row.linked_calibration_release_gates.join(', ') || '-'}</div>
                              <div className="font-mono text-[11px] text-stone-500">
                                decisions:{' '}
                                {Object.entries(row.calibration_decisions)
                                  .map(([taskId, decision]) => `${taskId}:${displayToken(decision)}`)
                                  .join(', ') || '-'}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                              <div className="font-mono text-[11px] text-stone-500">
                                {row.gap_reasons.join(', ') || 'metadata_coverage_present'}
                              </div>
                              <div className="mt-2">{row.next_actions[0] || '-'}</div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Coverage boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>local only: {String(userNeedBenchmarkCoverage.summary.local_run_only)}</div>
                      <div>model calls: {userNeedBenchmarkCoverage.summary.model_calls}</div>
                      <div>network: {userNeedBenchmarkCoverage.summary.network_access}</div>
                      <div>public sampler: {userNeedBenchmarkCoverage.summary.public_sampler_endpoint}</div>
                      <div>public sampler network: {userNeedBenchmarkCoverage.summary.public_sampler_network_access}</div>
                      <div>cheap-first calibration: {userNeedBenchmarkCoverage.summary.cheap_first_calibration_status}</div>
                      <div>
                        calibration newapi called:{' '}
                        {String(userNeedBenchmarkCoverage.source_summaries.cheap_first_calibration.newapi_called)}
                      </div>
                      <div>source: {userNeedBenchmarkCoverage.privacy_boundary.source}</div>
                      <div>
                        public benchmark text:{' '}
                        {String(userNeedBenchmarkCoverage.privacy_boundary.returns_public_benchmark_text)}
                      </div>
                      <div>
                        calibration payloads: {String(userNeedBenchmarkCoverage.privacy_boundary.returns_calibration_payloads)}
                      </div>
                      <div>raw output: {String(userNeedBenchmarkCoverage.privacy_boundary.returns_raw_model_output)}</div>
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">High-priority gaps</h3>
                    <div className="flex flex-wrap gap-2">
                      {userNeedBenchmarkCoverage.high_priority_gap_need_ids.length === 0 ? (
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                          none
                        </Badge>
                      ) : (
                        userNeedBenchmarkCoverage.high_priority_gap_need_ids.map((needId) => (
                          <Badge key={needId} variant="outline" className="bg-red-50 font-mono text-[11px] text-red-800">
                            {needId}
                          </Badge>
                        ))
                      )}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Public benchmark review gaps</h3>
                    <div className="flex flex-wrap gap-2">
                      {userNeedBenchmarkCoverage.public_benchmark_gap_need_ids.length === 0 ? (
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                          none
                        </Badge>
                      ) : (
                        userNeedBenchmarkCoverage.public_benchmark_gap_need_ids.map((needId) => (
                          <Badge key={needId} variant="outline" className="bg-amber-50 font-mono text-[11px] text-amber-900">
                            {needId}
                          </Badge>
                        ))
                      )}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Calibration attention gaps</h3>
                    <div className="flex flex-wrap gap-2">
                      {userNeedBenchmarkCoverage.calibration_attention_need_ids.length === 0 ? (
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                          none
                        </Badge>
                      ) : (
                        userNeedBenchmarkCoverage.calibration_attention_need_ids.map((needId) => (
                          <Badge key={needId} variant="outline" className="bg-red-50 font-mono text-[11px] text-red-800">
                            {needId}
                          </Badge>
                        ))
                      )}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {userNeedBenchmarkCoverage.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {userNeedBenchmarkCoverage.validation_commands.map((command) => (
                      <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3 font-mono text-[11px] text-stone-600">
                        {command}
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {userNeedGeminiRouteCoverage && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">User need Gemini route coverage</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {userNeedGeminiRouteCoverage.summary.high_priority_route_protected_count} high-priority route protected /{' '}
                      {userNeedGeminiRouteCoverage.summary.review_required_need_count} reviews /{' '}
                      {userNeedGeminiRouteCoverage.summary.blocked_need_count} blocked
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[userNeedGeminiRouteCoverage.status] ?? statusClass.warn}
                  >
                    {displayToken(userNeedGeminiRouteCoverage.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-9">
                  {[
                    { label: 'needs', value: userNeedGeminiRouteCoverage.summary.need_count },
                    { label: 'high priority', value: userNeedGeminiRouteCoverage.summary.high_priority_need_count },
                    {
                      label: 'route protected',
                      value: userNeedGeminiRouteCoverage.summary.high_priority_route_protected_count,
                    },
                    { label: 'cheap-first needs', value: userNeedGeminiRouteCoverage.summary.cheap_first_route_need_count },
                    { label: 'balanced needs', value: userNeedGeminiRouteCoverage.summary.balanced_route_need_count },
                    { label: 'premium needs', value: userNeedGeminiRouteCoverage.summary.premium_exception_need_count },
                    { label: 'route tasks', value: userNeedGeminiRouteCoverage.summary.route_task_count },
                    { label: 'official sources', value: userNeedGeminiRouteCoverage.summary.official_source_count },
                    { label: 'raw text returned', value: String(userNeedGeminiRouteCoverage.summary.raw_text_returned) },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Need</TableHead>
                          <TableHead>Route coverage</TableHead>
                          <TableHead>Gemini routes</TableHead>
                          <TableHead>Models / costs</TableHead>
                          <TableHead>Evidence state</TableHead>
                          <TableHead>Next action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {userNeedGeminiRouteCoverage.coverage_rows.slice(0, 8).map((row) => (
                          <TableRow key={row.id}>
                            <TableCell className="max-w-[320px]">
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.need_id}</div>
                              <div className="mt-2 text-xs text-stone-600">{displayToken(row.category)}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <Badge
                                variant="outline"
                                className={statusClass[row.route_coverage_status] ?? statusClass.warn}
                              >
                                {displayToken(row.route_coverage_status)}
                              </Badge>
                              <div className="mt-2">
                                <Badge
                                  variant="outline"
                                  className={priorityClass[row.priority_band] ?? priorityClass.medium}
                                >
                                  {row.priority_band} / {row.priority_score}
                                </Badge>
                              </div>
                              <div className="mt-2">source: {displayToken(row.route_task_source)}</div>
                              <div>HF ready: {String(row.high_frequency_route_ready)}</div>
                              <div>default without review: {String(row.default_allowed_without_review)}</div>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <div>tasks: {row.linked_route_tasks.join(', ') || '-'}</div>
                              <div>modes: {row.route_modes.map(displayToken).join(', ') || '-'}</div>
                              <div>cheap-first: {row.cheap_first_route_count}</div>
                              <div>balanced: {row.balanced_route_count}</div>
                              <div>premium exception: {row.premium_exception_route_count}</div>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <div>models: {row.linked_default_models.join(', ') || '-'}</div>
                              <div>costs: {row.cost_tiers.map(displayToken).join(', ') || '-'}</div>
                              <div>calibration tasks: {row.linked_calibration_task_ids.join(', ') || '-'}</div>
                              <div className="font-mono text-[11px] text-stone-500">
                                decisions:{' '}
                                {Object.entries(row.calibration_decisions)
                                  .map(([taskId, decision]) => `${taskId}:${displayToken(decision)}`)
                                  .join(', ') || '-'}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                              <div>benchmark: {displayToken(row.benchmark_coverage_status)}</div>
                              <div>public: {displayToken(row.public_benchmark_status)}</div>
                              <div>calibration: {displayToken(row.calibration_status)}</div>
                              <div className="mt-2 font-mono text-[11px] text-stone-500">
                                blocked: {row.blocked_reason_codes.join(', ') || 'none'}
                              </div>
                              <div className="font-mono text-[11px] text-stone-500">
                                review: {row.review_reason_codes.join(', ') || 'none'}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[380px] text-xs leading-5 text-stone-600">
                              {row.next_actions[0] || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Route coverage boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>coverage endpoint: {userNeedGeminiRouteCoverage.source_boundaries.coverage_endpoint}</div>
                      <div>
                        route preflight endpoint: {userNeedGeminiRouteCoverage.source_boundaries.route_preflight_endpoint}
                      </div>
                      <div>
                        public sample import:{' '}
                        {String(userNeedGeminiRouteCoverage.source_boundaries.imports_public_benchmark_samples)}
                      </div>
                      <div>changes defaults: {String(userNeedGeminiRouteCoverage.source_boundaries.changes_default_routes)}</div>
                      <div>model calls: {userNeedGeminiRouteCoverage.summary.model_calls}</div>
                      <div>network: {userNeedGeminiRouteCoverage.summary.network_access}</div>
                      <div>configuration written: {String(userNeedGeminiRouteCoverage.summary.configuration_written)}</div>
                      <div>
                        claims_default_route_changed:{' '}
                        {String(userNeedGeminiRouteCoverage.claim_boundary.claims_default_route_changed)}
                      </div>
                      <div>
                        claims_public_benchmark_scores:{' '}
                        {String(userNeedGeminiRouteCoverage.claim_boundary.claims_public_benchmark_scores)}
                      </div>
                      <div>
                        claims_live_gateway_execution:{' '}
                        {String(userNeedGeminiRouteCoverage.claim_boundary.claims_live_gateway_execution)}
                      </div>
                      <div>metadata only: {String(userNeedGeminiRouteCoverage.privacy_boundary.metadata_only)}</div>
                      <div>route payloads: {String(userNeedGeminiRouteCoverage.privacy_boundary.returns_route_payloads)}</div>
                      <div>prompts: {String(userNeedGeminiRouteCoverage.privacy_boundary.returns_prompts)}</div>
                      <div>credentials: {String(userNeedGeminiRouteCoverage.privacy_boundary.returns_credentials)}</div>
                      <div>emails: {String(userNeedGeminiRouteCoverage.privacy_boundary.returns_emails)}</div>
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Official source refresh</h3>
                    <div className="space-y-2">
                      {userNeedGeminiRouteCoverage.source_boundaries.official_source_urls.map((url) => (
                        <a
                          key={url}
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-2 break-all rounded-[8px] border border-stone-950/10 bg-white p-2 text-xs text-stone-700 hover:bg-stone-50"
                        >
                          <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                          <span>{url}</span>
                        </a>
                      ))}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Review ids</h3>
                    <div className="space-y-3">
                      <div>
                        <div className="mb-1 text-xs font-semibold uppercase text-stone-500">Blocked</div>
                        <div className="flex flex-wrap gap-2">
                          {userNeedGeminiRouteCoverage.blocked_need_ids.length === 0 ? (
                            <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                              none
                            </Badge>
                          ) : (
                            userNeedGeminiRouteCoverage.blocked_need_ids.map((needId) => (
                              <Badge key={needId} variant="outline" className="bg-red-50 font-mono text-[11px] text-red-800">
                                {needId}
                              </Badge>
                            ))
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="mb-1 text-xs font-semibold uppercase text-stone-500">Review</div>
                        <div className="flex flex-wrap gap-2">
                          {userNeedGeminiRouteCoverage.review_need_ids.slice(0, 8).map((needId) => (
                            <Badge key={needId} variant="outline" className="bg-amber-50 font-mono text-[11px] text-amber-900">
                              {needId}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {userNeedGeminiRouteCoverage.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {userNeedGeminiRouteCoverage.validation_commands.map((command) => (
                      <div
                        key={command}
                        className="break-all rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3 font-mono text-[11px] text-stone-600"
                      >
                        {command}
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {userNeedImplementationQueue && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {userNeedImplementationQueue.summary.queue_item_count} items /{' '}
                      {userNeedImplementationQueue.summary.review_required_action_count} reviews /{' '}
                      {userNeedImplementationQueue.summary.blocked_action_count} blocked
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[userNeedImplementationQueue.status] ?? statusClass.warn}
                  >
                    {displayToken(userNeedImplementationQueue.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
                  {[
                    { label: 'blocked', value: userNeedImplementationQueue.summary.blocked_action_count },
                    { label: 'review required', value: userNeedImplementationQueue.summary.review_required_action_count },
                    { label: 'ready', value: userNeedImplementationQueue.summary.ready_action_count },
                    { label: 'high priority', value: userNeedImplementationQueue.summary.high_priority_item_count },
                    {
                      label: 'public review',
                      value: userNeedImplementationQueue.summary.public_benchmark_review_item_count,
                    },
                    {
                      label: 'calibration attention',
                      value: userNeedImplementationQueue.summary.calibration_attention_item_count,
                    },
                    {
                      label: 'source gaps',
                      value: userNeedImplementationQueue.summary.source_high_priority_gap_count,
                    },
                    {
                      label: 'raw text returned',
                      value: String(userNeedImplementationQueue.summary.raw_text_returned),
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Need</TableHead>
                          <TableHead>Priority</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Tracks</TableHead>
                          <TableHead>Links</TableHead>
                          <TableHead>Next action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {userNeedImplementationQueue.queue_items.slice(0, 8).map((item) => (
                          <TableRow key={item.id}>
                            <TableCell className="max-w-[320px]">
                              <div className="font-semibold text-stone-950">{item.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{item.need_id}</div>
                              <div className="mt-2 text-xs text-stone-600">{displayToken(item.category)}</div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={priorityClass[item.priority_band] ?? priorityClass.medium}
                              >
                                {item.priority_band} / {item.queue_priority_score}
                              </Badge>
                              <div className="mt-2 text-[11px] text-stone-500">
                                need score {item.user_need_priority_score}
                              </div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <Badge
                                variant="outline"
                                className={statusClass[item.action_status] ?? statusClass.warn}
                              >
                                {displayToken(item.action_status)}
                              </Badge>
                              <div className="mt-2">coverage: {displayToken(item.coverage_status)}</div>
                              <div>public: {displayToken(item.public_benchmark_status)}</div>
                              <div>calibration: {displayToken(item.calibration_status)}</div>
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              <div>{item.implementation_tracks.join(', ') || '-'}</div>
                              <div className="mt-2 font-mono text-[11px] text-stone-500">
                                blockers: {item.blocker_codes.join(', ') || 'none'}
                              </div>
                              <div className="font-mono text-[11px] text-stone-500">
                                review: {item.review_reason_codes.join(', ') || 'none'}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <div>cases: {item.linked_benchmark_case_ids.join(', ') || '-'}</div>
                              <div>fixtures: {item.linked_fixture_ids.join(', ') || '-'}</div>
                              <div>public: {item.linked_public_source_ids.join(', ') || '-'}</div>
                              <div>calibration: {item.linked_calibration_task_ids.join(', ') || '-'}</div>
                              <div>backlog: {item.linked_backlog_item_ids.join(', ') || '-'}</div>
                            </TableCell>
                            <TableCell className="max-w-[380px] text-xs leading-5 text-stone-600">
                              {item.next_actions[0] || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Queue boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>coverage endpoint: {userNeedImplementationQueue.source_boundary.coverage_endpoint}</div>
                      <div>public sampler: {userNeedImplementationQueue.source_boundary.public_sampler_endpoint}</div>
                      <div>
                        imports public samples:{' '}
                        {String(userNeedImplementationQueue.source_boundary.imports_public_benchmark_samples)}
                      </div>
                      <div>uses raw legal text: {String(userNeedImplementationQueue.source_boundary.uses_raw_legal_text)}</div>
                      <div>uses model outputs: {String(userNeedImplementationQueue.source_boundary.uses_model_outputs)}</div>
                      <div>uses credentials: {String(userNeedImplementationQueue.source_boundary.uses_credentials)}</div>
                      <div>model calls: {userNeedImplementationQueue.summary.model_calls}</div>
                      <div>network: {userNeedImplementationQueue.summary.network_access}</div>
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Blocked needs</h3>
                    <div className="flex flex-wrap gap-2">
                      {userNeedImplementationQueue.blocked_need_ids.length === 0 ? (
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                          none
                        </Badge>
                      ) : (
                        userNeedImplementationQueue.blocked_need_ids.map((needId) => (
                          <Badge key={needId} variant="outline" className="bg-red-50 font-mono text-[11px] text-red-800">
                            {needId}
                          </Badge>
                        ))
                      )}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Review needs</h3>
                    <div className="flex flex-wrap gap-2">
                      {userNeedImplementationQueue.review_need_ids.slice(0, 8).map((needId) => (
                        <Badge key={needId} variant="outline" className="bg-amber-50 font-mono text-[11px] text-amber-900">
                          {needId}
                        </Badge>
                      ))}
                    </div>

                    <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Next actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {userNeedImplementationQueue.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {userNeedImplementationQueue.validation_commands.map((command) => (
                      <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3 font-mono text-[11px] text-stone-600">
                        {command}
                      </div>
                    ))}
                  </div>
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

            {adoptionResearchBridge && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Adoption research bridge</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {adoptionResearchBridge.summary.action_count} actions /{' '}
                      {adoptionResearchBridge.summary.source_count} sources /{' '}
                      {adoptionResearchBridge.summary.cheap_first_action_count} cheap-first
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[adoptionResearchBridge.status] ?? statusClass.ready}>
                    {adoptionResearchBridge.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {adoptionResearchBridge.summary.high_priority_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">high priority</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {adoptionResearchBridge.summary.governance_action_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">governance actions</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {adoptionResearchBridge.summary.research_digest_signal_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">digest signals</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {adoptionResearchBridge.summary.unmapped_need_ids.length +
                        adoptionResearchBridge.summary.unmapped_gap_ids.length}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">unmapped refs</div>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[0.95fr_1.05fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Implementation queue</h3>
                    <div className="space-y-3">
                      {adoptionResearchBridge.implementation_queue.map((item) => (
                        <div key={item.action_id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="bg-stone-950 text-white">
                              {item.priority_score}
                            </Badge>
                            <span className="font-mono text-xs text-stone-500">{item.action_id}</span>
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
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Research and adoption sources</h3>
                    <div className="space-y-3">
                      {adoptionResearchBridge.method.input_sources.map((source) => (
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
                          <div className="mt-2 text-xs leading-5 text-stone-500">{source.local_interpretation}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Action</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Research</TableHead>
                        <TableHead>Needs and gaps</TableHead>
                        <TableHead>Validation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {adoptionResearchBridge.actions.map((action) => (
                        <TableRow key={action.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{action.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{action.id}</div>
                            <div className="mt-2 flex flex-wrap gap-1">
                              <Badge
                                variant="outline"
                                className={categoryClass[action.product_area] ?? categoryClass.user_research}
                              >
                                {action.product_area.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={priorityClass[action.priority_band] ?? priorityClass.medium}
                            >
                              {action.priority_band} / {action.priority_score}
                            </Badge>
                            <div className="mt-2 text-[11px] leading-5 text-stone-500">
                              low cost {action.low_cost_fit} / effort {action.effort}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                            {action.source_ids.join(', ')}
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            <div>{action.user_need_ids.join(', ')}</div>
                            <div className="mt-2 text-stone-500">{action.product_gap_ids.join(', ')}</div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            <div className="mb-2 flex flex-wrap gap-1">
                              {action.release_gate_links.map((gate) => (
                                <Badge key={gate} variant="outline" className="bg-white font-mono text-[11px]">
                                  {gate}
                                </Badge>
                              ))}
                            </div>
                            <div>{action.validation_commands[0] || '-'}</div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Survey intake</h3>
                    <div className="space-y-3">
                      {adoptionResearchBridge.survey_intake_questions.map((question) => (
                        <div key={question.id} className="rounded-[8px] border border-stone-950/15 bg-white p-3">
                          <div className="font-mono text-[11px] text-stone-500">{question.id}</div>
                          <div className="mt-1 text-sm font-semibold text-stone-950">{question.prompt}</div>
                          <div className="mt-1 text-xs leading-5 text-stone-600">{question.privacy_rule}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Release guardrails</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {adoptionResearchBridge.release_guardrails.map((guardrail) => (
                        <li key={guardrail} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{guardrail}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 text-xs leading-5 text-stone-500">
                      {adoptionResearchBridge.privacy_note}
                    </div>
                  </div>
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

            {legalBenchmarkResearchRefresh && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal benchmark research refresh</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only refresh for legal benchmark research sources / no benchmark score claims.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[legalBenchmarkResearchRefresh.status] ?? statusClass.review_required}
                  >
                    {displayToken(legalBenchmarkResearchRefresh.status)}
                  </Badge>
                </div>

                <div className="mb-3 rounded-[8px] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                  This reviewer panel is metadata-only: source names, review freshness, user-need mappings, and local
                  validation commands are reviewable. It makes no benchmark score claims, no external benchmark run
                  claims, and no dataset download claims.
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-5">
                  {[
                    {
                      label: 'research sources',
                      value:
                        legalBenchmarkResearchRefresh.summary.source_count ??
                        (legalBenchmarkResearchRefresh.research_sources ?? []).length,
                    },
                    {
                      label: 'refresh rows',
                      value:
                        legalBenchmarkResearchRefresh.summary.refresh_row_count ??
                        (legalBenchmarkResearchRefresh.refresh_rows ?? []).length,
                    },
                    {
                      label: 'user need rows',
                      value:
                        legalBenchmarkResearchRefresh.summary.user_need_row_count ??
                        (legalBenchmarkResearchRefresh.user_need_rows ?? []).length,
                    },
                    {
                      label: 'cheap-first signals',
                      value: legalBenchmarkResearchRefresh.summary.cheap_first_signal_count ?? 0,
                    },
                    {
                      label: 'local commands',
                      value:
                        legalBenchmarkResearchRefresh.summary.local_validation_command_count ??
                        (legalBenchmarkResearchRefresh.validation_commands ?? []).length,
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Refresh target</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Metadata fields</TableHead>
                          <TableHead>User needs</TableHead>
                          <TableHead>cheap-first/local validation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(legalBenchmarkResearchRefresh.refresh_rows ?? []).slice(0, 6).map((row, index) => {
                          const rowKey = row.id ?? row.source_id ?? row.source_name ?? row.title ?? `refresh-${index}`;
                          const reviewedFields =
                            row.refreshed_metadata_fields ??
                            row.fields_reviewed ??
                            row.changed_fields ??
                            row.stale_fields ??
                            [row.product_area, row.local_validation_target].filter(Boolean) ??
                            [];
                          const refreshStatus =
                            row.refresh_status ??
                            (row.dataset_download_required || row.public_score_claimed ? 'review_required' : 'ready');
                          return (
                            <TableRow key={rowKey}>
                              <TableCell>
                                <div className="font-semibold text-stone-950">
                                  {row.source_name ?? row.title ?? row.source_id ?? row.id ?? '-'}
                                </div>
                                <div className="mt-1 font-mono text-[11px] text-stone-500">
                                  {row.source_id ?? row.id ?? '-'}
                                </div>
                                <div className="mt-2 text-xs leading-5 text-stone-600">
                                  {row.benchmark_signal ?? row.recommended_action ?? '-'}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge
                                  variant="outline"
                                  className={statusClass[refreshStatus] ?? statusClass.warn}
                                >
                                  {displayToken(refreshStatus)}
                                </Badge>
                                <div className="mt-2 text-[11px] leading-5 text-stone-500">
                                  metadata only: {String(row.metadata_only ?? true)}
                                </div>
                                <div className="text-[11px] leading-5 text-stone-500">
                                  benchmark score claimed:{' '}
                                  {String(row.benchmark_score_claimed ?? row.public_score_claimed ?? false)}
                                </div>
                              </TableCell>
                              <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                                <div>{reviewedFields.join(', ') || '-'}</div>
                                <div className="mt-1 font-mono text-[11px] text-stone-500">
                                  evidence: {(row.local_evidence_paths ?? []).slice(0, 2).join(', ') || 'metadata only'}
                                </div>
                              </TableCell>
                              <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                                {(row.user_need_ids ?? []).join(', ') || '-'}
                              </TableCell>
                              <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                                <div>
                                  {row.cheap_first_local_validation ??
                                    row.cheap_first_policy ??
                                    row.validation_command ??
                                    row.validation_commands?.[0] ??
                                    '-'}
                                </div>
                                <div className="mt-1 text-stone-500">
                                  dataset download {String(row.dataset_download_required ?? false)} / model call{' '}
                                  {String(row.model_call_required ?? false)}
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">
                      Metadata-only/no benchmark score claims boundary
                    </h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        metadata-only refresh:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.metadata_only ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.metadata_only ??
                            true,
                        )}
                      </div>
                      <div>
                        raw benchmark text:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.privacy_boundary?.returns_raw_benchmark_text ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.returns_public_benchmark_text ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.returns_dataset_samples ??
                            false,
                        )}
                      </div>
                      <div>
                        raw model output:{' '}
                        {String(legalBenchmarkResearchRefresh.privacy_boundary?.returns_raw_model_output ?? false)}
                      </div>
                      <div>
                        external dataset download:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.dataset_downloaded ??
                          legalBenchmarkResearchRefresh.summary.external_dataset_downloads ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.external_dataset_downloads ??
                            legalBenchmarkResearchRefresh.claim_boundary?.external_dataset_download_claimed ??
                            false,
                        )}
                      </div>
                      <div>
                        benchmark score claims:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.public_benchmark_score_claimed ??
                          legalBenchmarkResearchRefresh.summary.benchmark_score_claims ??
                            legalBenchmarkResearchRefresh.claim_boundary?.public_benchmark_scores_claimed ??
                            legalBenchmarkResearchRefresh.claim_boundary?.benchmark_score_claims ??
                            false,
                        )}
                      </div>
                      <div>
                        external benchmark run claimed:{' '}
                        {String(legalBenchmarkResearchRefresh.claim_boundary?.external_benchmark_run_claimed ?? false)}
                      </div>
                      <div>
                        cheap-first local validation:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.cheap_first_local_validation_status ??
                            'local metadata checks first',
                        )}
                      </div>
                      <div>
                        network:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.network_called ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.network_called ??
                            legalBenchmarkResearchRefresh.summary.network_access ??
                            'local_only',
                        )}
                      </div>
                      <div>
                        model calls:{' '}
                        {String(
                          legalBenchmarkResearchRefresh.summary.model_called ??
                            legalBenchmarkResearchRefresh.privacy_boundary?.model_called ??
                            legalBenchmarkResearchRefresh.summary.model_calls ??
                            'none',
                        )}
                      </div>
                      <div>source: {String(legalBenchmarkResearchRefresh.privacy_boundary?.source ?? 'metadata only')}</div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {(legalBenchmarkResearchRefresh.recommended_actions ?? []).slice(0, 4).map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1fr_1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Research sources</h3>
                    <div className="space-y-3">
                      {(legalBenchmarkResearchRefresh.research_sources ?? []).slice(0, 5).map((source, index) => {
                        const sourceTitle = source.title ?? source.public_name ?? source.source_id ?? source.id ?? '-';
                        const sourceUrl = source.url ?? source.public_link ?? '#';
                        return (
                          <div
                            key={source.id ?? source.source_id ?? sourceTitle ?? `source-${index}`}
                            className="rounded-[8px] border border-stone-950/15 bg-white p-3"
                          >
                            <div className="mb-2 flex flex-wrap items-center gap-2">
                              <a
                                href={sourceUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-sm font-semibold text-stone-950 hover:underline"
                              >
                                {sourceTitle}
                                <ExternalLink className="h-3.5 w-3.5" />
                              </a>
                              <Badge variant="outline" className="bg-white">
                                {displayToken(source.source_type ?? 'public_metadata')}
                              </Badge>
                              <Badge
                                variant="outline"
                                className={statusClass[source.refresh_status ?? source.metadata_status ?? 'review_required'] ?? statusClass.warn}
                              >
                                {displayToken(source.refresh_status ?? source.metadata_status ?? 'review_required')}
                              </Badge>
                            </div>
                            <div className="text-xs leading-5 text-stone-600">
                              license {displayToken(source.license_status ?? 'review_required')} / cheap-first{' '}
                              {displayToken(source.cheap_first_fit ?? 'local_metadata_only')}
                            </div>
                            <div className="mt-1 text-xs leading-5 text-stone-500">
                              {source.local_validation ??
                                source.local_interpretation ??
                                source.import_policy ??
                                source.notes?.[0] ??
                                'Review metadata locally before any network sampling.'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">User need refresh mapping</h3>
                    <div className="space-y-3">
                      {(legalBenchmarkResearchRefresh.user_need_rows ?? []).slice(0, 5).map((row, index) => {
                        const coverageStatus = row.coverage_status ?? row.local_coverage_status ?? 'review_required';
                        const sourceIds = row.linked_source_ids ?? row.source_ids ?? [];
                        const refreshRowIds = row.linked_refresh_row_ids ?? row.refresh_row_ids ?? [];
                        return (
                          <div
                            key={row.need_id ?? row.title ?? `need-${index}`}
                            className="rounded-[8px] border border-stone-950/15 bg-white p-3"
                          >
                            <div className="mb-2 flex flex-wrap items-center gap-2">
                              <Badge
                                variant="outline"
                                className={statusClass[coverageStatus] ?? statusClass.warn}
                              >
                                {displayToken(coverageStatus)}
                              </Badge>
                              {row.priority_band && (
                                <Badge
                                  variant="outline"
                                  className={priorityClass[row.priority_band] ?? priorityClass.medium}
                                >
                                  {row.priority_band}
                                  {row.priority_score !== undefined ? ` / ${row.priority_score}` : ''}
                                </Badge>
                              )}
                              {row.cheap_first_relevant && (
                                <Badge variant="outline" className="bg-white">
                                  cheap-first relevant
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm font-semibold text-stone-950">{row.title ?? row.need_id ?? '-'}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.need_id ?? '-'}</div>
                            <div className="mt-2 text-xs leading-5 text-stone-600">
                              sources: {sourceIds.join(', ') || '-'}
                            </div>
                            <div className="text-xs leading-5 text-stone-600">
                              refresh rows: {refreshRowIds.join(', ') || '-'}
                            </div>
                            <div className="text-xs leading-5 text-stone-600">
                              public {displayToken(row.public_benchmark_status ?? 'not_mapped')} / calibration{' '}
                              {displayToken(row.calibration_status ?? 'not_mapped')}
                            </div>
                            <div className="mt-1 text-xs leading-5 text-stone-500">
                              {row.cheap_first_local_validation ??
                                row.next_action ??
                                row.next_actions?.[0] ??
                                'Keep validation cheap-first and local.'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {(legalBenchmarkResearchRefresh.validation_commands ?? []).map((command) => (
                      <div
                        key={command}
                        className="break-all rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3 font-mono text-[11px] text-stone-600"
                      >
                        {command}
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {modelOpsLegalFixtureCheapFirstBenchmarkGate && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">
                      Legal fixture cheap-first benchmark gate
                    </h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Small legal-document fixture gate for cheap Gemini default evidence before routing changes.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      statusClass[modelOpsLegalFixtureCheapFirstBenchmarkGate.status] ?? statusClass.review_required
                    }
                  >
                    {displayToken(modelOpsLegalFixtureCheapFirstBenchmarkGate.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 lg:grid-cols-6">
                  {[
                    {
                      label: 'selected fixtures',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.selected_fixture_count,
                    },
                    {
                      label: 'evaluated',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.evaluated_fixture_count,
                    },
                    {
                      label: 'evidence allowed',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.default_evidence_allowed_count,
                    },
                    {
                      label: 'blocked',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.blocked_count,
                    },
                    {
                      label: 'document cases',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_case_count,
                    },
                    {
                      label: 'document score',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_score,
                    },
                    {
                      label: 'coverage gaps',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_coverage_missing_type_count,
                    },
                    {
                      label: 'max parallel',
                      value: modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.max_parallel_requests,
                    },
                    {
                      label: 'cheap cost',
                      value: formatUsd(modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.estimated_cheap_first_cost_usd),
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.3fr_0.7fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fixture</TableHead>
                          <TableHead>Gate</TableHead>
                          <TableHead>Cheap-first</TableHead>
                          <TableHead>Evidence signals</TableHead>
                          <TableHead>Release action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {modelOpsLegalFixtureCheapFirstBenchmarkGate.gate_rows.map((row) => (
                          <TableRow key={row.id}>
                            <TableCell className="max-w-[280px]">
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.fixture_id}</div>
                              <div className="mt-2 text-xs text-stone-600">
                                {displayToken(row.matter_type)} / {displayToken(row.task)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={statusClass[row.gate_status] ?? statusClass.warn}>
                                {displayToken(row.gate_status)}
                              </Badge>
                              <div className="mt-2 text-xs leading-5 text-stone-600">
                                run {displayToken(row.run_report_status)} / matrix {displayToken(row.model_matrix_status)}
                              </div>
                              <div className="text-xs leading-5 text-stone-500">
                                default evidence: {String(row.default_change_evidence_allowed)}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                              <div className="font-mono text-[11px] text-stone-950">{row.cheap_first_model ?? '-'}</div>
                              <div>tier {row.cheap_first_cost_tier ?? '-'}</div>
                              <div>known {String(row.cheap_first_known_model)}</div>
                              <div>premium escalation {String(row.premium_escalation_candidate)}</div>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              expected signals {row.expected_signal_count} / tasks {row.expected_task_count}
                              <br />
                              matched {row.matched_signal_count} / missing signals {row.missing_signal_count} / missing tasks{' '}
                              {row.missing_task_count}
                              <br />
                              sources {row.public_source_ids.join(', ') || '-'}
                            </TableCell>
                            <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                              <div>{row.release_action}</div>
                              <div className="mt-2 font-mono text-[11px] text-stone-500">
                                {row.reason_codes.join(', ') || 'fixture-gate-ready'}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        raw fixture text:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.privacy_boundary.returns_raw_fixture_text ?? false)}
                      </div>
                      <div>
                        raw model output:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.privacy_boundary.returns_raw_model_output ?? false)}
                      </div>
                      <div>
                        gateway payloads:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.privacy_boundary.returns_gateway_payloads ?? false)}
                      </div>
                      <div>
                        credentials:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.privacy_boundary.returns_credentials ?? false)}
                      </div>
                      <div>
                        NewAPI called:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.privacy_boundary.newapi_called ?? false)}
                      </div>
                      <div>
                        automatic default change:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.claim_boundary.automatic_default_change_claimed ??
                            false,
                        )}
                      </div>
                      <div>
                        public benchmark scores:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.claim_boundary.public_benchmark_scores_claimed ??
                            false,
                        )}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Routing policy</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>strategy: {displayToken(modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy.default_strategy)}</div>
                      <div>
                        cheap models:{' '}
                        {modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy.cheap_first_models.join(', ') || '-'}
                      </div>
                      <div>
                        config write allowed:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy.configuration_write_allowed)}
                      </div>
                      <div>
                        document benchmark required:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy
                            .document_benchmark_required_for_default_change,
                        )}
                      </div>
                      <div>
                        fact consistency required:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy
                            .fact_consistency_required_for_default_change,
                        )}
                      </div>
                      <div>
                        default change evidence:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.default_change_evidence_allowed)}
                      </div>
                      <div>
                        traffic shift allowed:{' '}
                        {String(modelOpsLegalFixtureCheapFirstBenchmarkGate.routing_policy.traffic_shift_allowed)}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Validation</h3>
                    <div className="grid gap-2">
                      {modelOpsLegalFixtureCheapFirstBenchmarkGate.validation_commands.slice(0, 2).map((command) => (
                        <div
                          key={command}
                          className="break-all rounded-[8px] border border-stone-950/10 bg-white p-3 font-mono text-[11px] text-stone-600"
                        >
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {hasLegalFixtureDocumentBenchmark && (
                  <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-black uppercase text-stone-500">Document benchmark gate</h3>
                        <div className="mt-1 text-xs leading-5 text-stone-600">
                          score{' '}
                          {legalFixtureDocumentSummary?.score ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_score}{' '}
                          / cases{' '}
                          {legalFixtureDocumentSummary?.case_count ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_case_count}{' '}
                          / coverage{' '}
                          {legalFixtureDocumentSummary?.covered_document_type_count ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_coverage_covered_type_count}
                          /
                          {legalFixtureDocumentSummary?.target_document_type_count ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_coverage_target_type_count}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          statusClass[
                            legalFixtureDocumentSummary?.status ??
                              modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_status ??
                              'not_run'
                          ] ?? statusClass.review_required
                        }
                      >
                        {displayToken(
                          legalFixtureDocumentSummary?.status ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_status ??
                            'not_run',
                        )}
                      </Badge>
                    </div>

                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="text-xs leading-5 text-stone-600">
                        passed{' '}
                        {legalFixtureDocumentSummary?.passed_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_passed_case_count}{' '}
                        / warn{' '}
                        {legalFixtureDocumentSummary?.warning_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_warning_case_count}{' '}
                        / failed{' '}
                        {legalFixtureDocumentSummary?.failed_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_failed_case_count}
                        <br />
                        not run{' '}
                        {legalFixtureDocumentSummary?.not_run_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_not_run_case_count}{' '}
                        / blocking{' '}
                        {legalFixtureDocumentSummary?.blocking_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_blocking_case_count}{' '}
                        / review{' '}
                        {legalFixtureDocumentSummary?.review_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_benchmark_review_case_count}
                      </div>
                      <div className="text-xs leading-5 text-stone-600">
                        coverage{' '}
                        {displayToken(
                          legalFixtureDocumentSummary?.coverage_status ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_coverage_status,
                        )}
                        <br />
                        missing document types{' '}
                        {legalFixtureDocumentSummary?.missing_document_type_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.document_coverage_missing_type_count}
                        <br />
                        max local fixtures{' '}
                        {legalFixtureDocumentSummary?.max_local_fixtures_per_run ?? '-'}
                      </div>
                      <div className="text-xs leading-5 text-stone-600">
                        model calls {legalFixtureDocumentSummary?.model_calls ?? 'not_required'}
                        <br />
                        network {legalFixtureDocumentSummary?.network_access ?? 'disabled'}
                        <br />
                        raw document snippets{' '}
                        {String(
                          legalFixtureDocumentSummary?.raw_document_snippets_returned ?? false,
                        )}{' '}
                        / raw candidate text{' '}
                        {String(
                          legalFixtureDocumentSummary?.raw_candidate_text_returned ?? false,
                        )}
                      </div>
                    </div>

                    <div className="mt-3 grid gap-2 md:grid-cols-3">
                      {legalFixtureDocumentAttentionRows
                        .map((row) => (
                          <div key={row.id} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <div className="truncate text-sm font-semibold text-stone-950">{row.title}</div>
                                <div className="font-mono text-[11px] text-stone-500">{row.case_id}</div>
                              </div>
                              <Badge variant="outline" className={statusClass[row.gate_status] ?? statusClass.warn}>
                                {displayToken(row.gate_status)}
                              </Badge>
                            </div>
                            <div className="mt-2 text-xs leading-5 text-stone-600">
                              {displayToken(row.document_type)} / score {row.score}
                              <br />
                              missing: sections {row.missing_section_count}, citations {row.missing_citation_count},
                              risk {row.missing_risk_label_count}
                              <br />
                              PII findings {row.pii_finding_count} / hard block {String(row.hard_pii_block)}
                            </div>
                            <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                              {(row.reason_codes ?? []).join(', ') || 'document-benchmark-ready'}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {hasLegalFixtureFactConsistency && (
                  <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-black uppercase text-stone-500">Fact consistency gate</h3>
                        <div className="mt-1 text-xs leading-5 text-stone-600">
                          score{' '}
                          {legalFixtureFactConsistencySummary?.score ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_score ??
                            0}{' '}
                          / cases{' '}
                          {legalFixtureFactConsistencySummary?.case_count ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_case_count ??
                            0}{' '}
                          / amount mismatches{' '}
                          {legalFixtureFactConsistencySummary?.amount_mismatch_count ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_amount_mismatch_count ??
                            0}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          statusClass[
                            legalFixtureFactConsistencySummary?.status ??
                              modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_status ??
                              'not_run'
                          ] ?? statusClass.review_required
                        }
                      >
                        {displayToken(
                          legalFixtureFactConsistencySummary?.status ??
                            modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_status ??
                            'not_run',
                        )}
                      </Badge>
                    </div>

                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="text-xs leading-5 text-stone-600">
                        passed{' '}
                        {legalFixtureFactConsistencySummary?.passed_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_passed_case_count ??
                          0}{' '}
                        / warn{' '}
                        {legalFixtureFactConsistencySummary?.warning_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_warning_case_count ??
                          0}{' '}
                        / failed{' '}
                        {legalFixtureFactConsistencySummary?.failed_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_failed_case_count ??
                          0}
                        <br />
                        not run{' '}
                        {legalFixtureFactConsistencySummary?.not_run_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_not_run_case_count ??
                          0}{' '}
                        / blocking{' '}
                        {legalFixtureFactConsistencySummary?.blocking_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_blocking_case_count ??
                          0}{' '}
                        / review{' '}
                        {legalFixtureFactConsistencySummary?.review_case_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_review_case_count ??
                          0}
                      </div>
                      <div className="text-xs leading-5 text-stone-600">
                        deadline mismatches{' '}
                        {legalFixtureFactConsistencySummary?.deadline_mismatch_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_deadline_mismatch_count ??
                          0}
                        <br />
                        contradictions{' '}
                        {legalFixtureFactConsistencySummary?.contradiction_count ??
                          modelOpsLegalFixtureCheapFirstBenchmarkGate.summary.fact_consistency_contradiction_count ??
                          0}
                        <br />
                        raw input fields {legalFixtureFactConsistencySummary?.raw_input_field_count ?? 0}
                      </div>
                      <div className="text-xs leading-5 text-stone-600">
                        model calls {legalFixtureFactConsistencySummary?.model_calls ?? 'not_required'}
                        <br />
                        network {legalFixtureFactConsistencySummary?.network_access ?? 'disabled'}
                        <br />
                        raw document text{' '}
                        {String(legalFixtureFactConsistencySummary?.raw_document_text_returned ?? false)} / raw
                        candidate text {String(legalFixtureFactConsistencySummary?.raw_candidate_text_returned ?? false)}
                      </div>
                    </div>

                    <div className="mt-3 grid gap-2 md:grid-cols-3">
                      {legalFixtureFactConsistencyAttentionRows.map((row) => (
                        <div key={row.id} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <div className="truncate text-sm font-semibold text-stone-950">{row.title}</div>
                              <div className="font-mono text-[11px] text-stone-500">{row.case_id}</div>
                            </div>
                            <Badge variant="outline" className={statusClass[row.gate_status] ?? statusClass.warn}>
                              {displayToken(row.gate_status)}
                            </Badge>
                          </div>
                          <div className="mt-2 text-xs leading-5 text-stone-600">
                            score {row.score} / amounts {row.mismatched_amount_count} / deadlines{' '}
                            {row.mismatched_deadline_count}
                            <br />
                            facts missing {row.missing_fact_count} / contradictions {row.contradiction_count}
                          </div>
                          <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                            {(row.reason_codes ?? []).join(', ') || 'fact-consistency-ready'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {modelOpsLegalFixtureCheapFirstDefaultPromotionPacket && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">
                      Legal fixture cheap-first default promotion packet
                    </h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Maintainer-only packet for cheap-first legal fixture default review, without configuration writes or gateway calls.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      statusClass[modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.status] ??
                      statusClass.review_required
                    }
                  >
                    {displayToken(modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 lg:grid-cols-6">
                  {[
                    {
                      label: 'promotion items',
                      value: modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary.promotion_item_count,
                    },
                    {
                      label: 'ready review',
                      value: modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary.ready_for_review_count,
                    },
                    {
                      label: 'blocked',
                      value: modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary.blocked_count,
                    },
                    {
                      label: 'source gate',
                      value: displayToken(modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary.source_gate_status),
                    },
                    {
                      label: 'document status',
                      value: displayToken(
                        modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary.document_benchmark_status,
                      ),
                    },
                    {
                      label: 'coverage gaps',
                      value:
                        modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.summary
                          .document_coverage_missing_type_count,
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fixture</TableHead>
                          <TableHead>Promotion</TableHead>
                          <TableHead>Proposed default</TableHead>
                          <TableHead>Review evidence</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {legalFixtureDefaultPromotionAttentionRows.map((row) => (
                          <TableRow key={row.id}>
                            <TableCell className="max-w-[260px]">
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.fixture_id}</div>
                              <div className="mt-2 text-xs text-stone-600">
                                {displayToken(row.matter_type)} / {displayToken(row.task)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={statusClass[row.promotion_status] ?? statusClass.review_required}
                              >
                                {displayToken(row.promotion_status)}
                              </Badge>
                              <div className="mt-2 text-xs leading-5 text-stone-600">
                                gate {displayToken(row.gate_status)} / document{' '}
                                {displayToken(row.document_benchmark_status)}
                              </div>
                              <div className="text-xs leading-5 text-stone-500">
                                coverage {displayToken(row.document_coverage_status)}
                              </div>
                            </TableCell>
                            <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                              <div className="font-mono text-[11px] text-stone-950">
                                {row.proposed_default_model ?? '-'}
                              </div>
                              <div>tier {row.proposed_cost_tier ?? '-'}</div>
                              <div>default evidence {String(row.default_change_evidence_allowed ?? false)}</div>
                              <div>premium escalation {String(row.premium_escalation_candidate ?? false)}</div>
                            </TableCell>
                            <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                              <div>{row.action}</div>
                              <div className="mt-2">signoffs {(row.required_signoffs ?? []).join(', ') || '-'}</div>
                              <div className="mt-2 font-mono text-[11px] text-stone-500">
                                {(row.reason_codes ?? []).join(', ') || 'promotion-packet-ready'}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Decision boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        default_change_allowed_by_packet:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.decision
                            .default_change_allowed_by_packet ?? false,
                        )}
                      </div>
                      <div>
                        configuration_write_allowed:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.decision
                            .configuration_change_allowed ?? false,
                        )}
                      </div>
                      <div>
                        gateway_call_allowed:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.decision.gateway_call_allowed ?? false,
                        )}
                      </div>
                      <div>
                        traffic_shift_allowed:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.decision.traffic_shift_allowed ?? false,
                        )}
                      </div>
                      <div>
                        automatic default change:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.claim_boundary
                            .automatic_default_change_claimed ?? false,
                        )}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        metadata only:{' '}
                        {String(modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary.metadata_only)}
                      </div>
                      <div>
                        raw fixture text:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary
                            .returns_raw_fixture_text ?? false,
                        )}
                      </div>
                      <div>
                        raw document snippets:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary
                            .returns_document_snippets ?? false,
                        )}
                      </div>
                      <div>
                        raw candidate text:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary.returns_candidate_text ??
                            false,
                        )}
                      </div>
                      <div>
                        credentials:{' '}
                        {String(
                          modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary.returns_credentials ??
                            false,
                        )}
                      </div>
                      <div>
                        NewAPI called:{' '}
                        {String(modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.privacy_boundary.newapi_called)}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Checklist</h3>
                    <div className="grid gap-2">
                      {modelOpsLegalFixtureCheapFirstDefaultPromotionPacket.evidence_checklist.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between gap-3 rounded-[8px] border border-stone-950/10 bg-white px-3 py-2 text-xs"
                        >
                          <span className="font-semibold text-stone-700">{displayToken(item.id)}</span>
                          <Badge variant="outline" className={statusClass[item.status] ?? statusClass.review_required}>
                            {displayToken(item.status)}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {modelRouteLegalBenchmarkRiskQueue && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">
                      Model route legal benchmark risk queue
                    </h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Compact cheap-first/legal benchmark/user-need risk queue for reviewer routing decisions.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[modelRouteLegalBenchmarkRiskQueue.status] ?? statusClass.review_required}
                  >
                    {displayToken(modelRouteLegalBenchmarkRiskQueue.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-5">
                  {[
                    {
                      label: 'queue rows',
                      value:
                        modelRouteLegalBenchmarkRiskQueue.summary.queue_row_count ??
                        modelRouteLegalBenchmarkRiskQueue.queue_rows.length,
                    },
                    {
                      label: 'high risk',
                      value:
                        modelRouteLegalBenchmarkRiskQueue.summary.watch_count ??
                        modelRouteLegalBenchmarkRiskQueue.summary.high_risk_count ??
                        0,
                    },
                    {
                      label: 'cheap-first allowed',
                      value:
                        modelRouteLegalBenchmarkRiskQueue.summary.cheap_first_allowed_count ??
                        modelRouteLegalBenchmarkRiskQueue.summary.cheap_first_risk_count ??
                        0,
                    },
                    {
                      label: 'premium exceptions',
                      value:
                        modelRouteLegalBenchmarkRiskQueue.summary.premium_exception_count ??
                        modelRouteLegalBenchmarkRiskQueue.summary.legal_benchmark_gap_count ??
                        0,
                    },
                    {
                      label: 'license watches',
                      value:
                        modelRouteLegalBenchmarkRiskQueue.summary.benchmark_license_watch_count ??
                        modelRouteLegalBenchmarkRiskQueue.summary.user_need_gap_count ??
                        0,
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Route</TableHead>
                          <TableHead>Risk</TableHead>
                          <TableHead>Legal benchmark</TableHead>
                          <TableHead>User needs</TableHead>
                          <TableHead>Reviewer action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {modelRouteLegalBenchmarkRiskQueue.queue_rows.slice(0, 6).map((row, index) => {
                          const rowKey = row.id ?? row.route_id ?? row.route ?? row.route_name ?? `risk-row-${index}`;
                          const routeLabel =
                            row.task ??
                            row.task_id ??
                            row.route_name ??
                            row.route ??
                            row.route_id ??
                            row.canonical_model ??
                            row.selected_model ??
                            row.model ??
                            row.model_id ??
                            '-';
                          const riskStatus = row.risk_status ?? row.status ?? row.risk_level ?? 'review_required';
                          const cheapFirstStatus =
                            row.cheap_first_status ??
                            row.cheap_first_decision ??
                            row.cheap_first_gate ??
                            row.calibration_decision ??
                            'review_required';
                          const benchmarkStatus =
                            row.legal_benchmark_status ??
                            row.benchmark_status ??
                            row.public_benchmark_statuses?.[0] ??
                            'review_required';
                          const userNeedStatus =
                            row.user_need_status ??
                            row.coverage_status ??
                            row.coverage_statuses?.[0] ??
                            'review_required';
                          const benchmarkIds =
                            row.research_source_ids ??
                            row.legal_benchmark_case_ids ??
                            row.benchmark_case_ids ??
                            row.linked_benchmark_case_ids ??
                            [];
                          const userNeedIds = row.user_need_ids ?? row.linked_user_need_ids ?? [];
                          const reasons = row.reason_codes ?? row.gap_reasons ?? row.risk_reasons ?? [];
                          const actions =
                            row.next_actions ??
                            (row.next_action ? [row.next_action] : row.recommended_action ? [row.recommended_action] : []);
                          const commands =
                            row.validation_commands ?? (row.validation_command ? [row.validation_command] : []);
                          return (
                            <TableRow key={rowKey}>
                              <TableCell className="max-w-[280px]">
                                <div className="font-semibold text-stone-950">{routeLabel}</div>
                                <div className="mt-1 font-mono text-[11px] text-stone-500">
                                  {row.task_id ?? row.route_id ?? row.id ?? '-'}
                                </div>
                                <div className="mt-2 text-xs text-stone-600">
                                  {displayToken(row.task_family ?? row.product_area ?? 'model_route')}
                                </div>
                                <div className="mt-1 text-xs text-stone-500">
                                  model {formatInline(row.canonical_model ?? row.selected_model ?? row.cost_tier ?? '-')}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className={statusClass[riskStatus] ?? statusClass.warn}>
                                  {displayToken(riskStatus)}
                                </Badge>
                                <div className="mt-2 text-xs leading-5 text-stone-600">
                                  cheap-first {displayToken(cheapFirstStatus)}
                                  {row.priority !== undefined ? ` / priority ${row.priority}` : ''}
                                </div>
                                <div className="text-xs leading-5 text-stone-500">
                                  premium exception {String(row.premium_exception_required ?? false)}
                                </div>
                              </TableCell>
                              <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                                <Badge
                                  variant="outline"
                                  className={statusClass[benchmarkStatus] ?? statusClass.review_required}
                                >
                                  {displayToken(benchmarkStatus)}
                                </Badge>
                                <div className="mt-2 font-mono text-[11px] text-stone-500">
                                  {benchmarkIds.join(', ') || '-'}
                                </div>
                              </TableCell>
                              <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                                <Badge
                                  variant="outline"
                                  className={statusClass[userNeedStatus] ?? statusClass.review_required}
                                >
                                  {displayToken(userNeedStatus)}
                                </Badge>
                                <div className="mt-2 font-mono text-[11px] text-stone-500">
                                  {userNeedIds.join(', ') || '-'}
                                </div>
                              </TableCell>
                              <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                                <div>{actions[0] ?? reasons[0] ?? 'Review route against legal benchmark coverage.'}</div>
                                <div className="mt-2 font-mono text-[11px] text-stone-500">
                                  {commands[0] ?? 'metadata-only validation'}
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Routing policy</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        cheap-first default:{' '}
                        {formatInline(
                          modelRouteLegalBenchmarkRiskQueue.routing_policy.cheap_first_default ??
                            modelRouteLegalBenchmarkRiskQueue.routing_policy.default_route ??
                            modelRouteLegalBenchmarkRiskQueue.routing_policy.cheap_model_start ??
                            'review_required',
                        )}
                      </div>
                      <div>
                        default strategy:{' '}
                        {formatInline(modelRouteLegalBenchmarkRiskQueue.routing_policy.default_strategy ?? 'cheap_first')}
                      </div>
                      <div>
                        legal benchmark gate:{' '}
                        {formatInline(
                          modelRouteLegalBenchmarkRiskQueue.routing_policy.legal_benchmark_gate ??
                            modelRouteLegalBenchmarkRiskQueue.summary.benchmark_license_watch_count ??
                            'metadata_required',
                        )}
                      </div>
                      <div>
                        user-need gate:{' '}
                        {formatInline(
                          modelRouteLegalBenchmarkRiskQueue.routing_policy.user_need_gate ??
                            modelRouteLegalBenchmarkRiskQueue.summary.user_need_gap_count ??
                            'coverage_required',
                        )}
                      </div>
                      <div>
                        local validation first:{' '}
                        {String(modelRouteLegalBenchmarkRiskQueue.routing_policy.local_validation_first ?? true)}
                      </div>
                      <div>
                        network:{' '}
                        {formatInline(
                          modelRouteLegalBenchmarkRiskQueue.summary.network_access ??
                            modelRouteLegalBenchmarkRiskQueue.summary.network_called ??
                            modelRouteLegalBenchmarkRiskQueue.privacy_boundary.network_called ??
                            modelRouteLegalBenchmarkRiskQueue.privacy_boundary.network_access ??
                            'local_only',
                        )}
                      </div>
                      <div>
                        model calls:{' '}
                        {formatInline(
                          modelRouteLegalBenchmarkRiskQueue.summary.model_calls ??
                            modelRouteLegalBenchmarkRiskQueue.summary.newapi_called ??
                            modelRouteLegalBenchmarkRiskQueue.privacy_boundary.newapi_called ??
                            modelRouteLegalBenchmarkRiskQueue.privacy_boundary.model_calls ??
                            'none',
                        )}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Claim boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>
                        automatic routing change claimed:{' '}
                        {String(
                          modelRouteLegalBenchmarkRiskQueue.claim_boundary.automatic_routing_change_claimed ??
                            modelRouteLegalBenchmarkRiskQueue.claim_boundary.cheap_first_default_change_claimed ??
                            modelRouteLegalBenchmarkRiskQueue.claim_boundary.default_model_changed ??
                            false,
                        )}
                      </div>
                      <div>
                        public benchmark scores claimed:{' '}
                        {String(
                          modelRouteLegalBenchmarkRiskQueue.claim_boundary.public_benchmark_scores_claimed ??
                            modelRouteLegalBenchmarkRiskQueue.claim_boundary.benchmark_score_claims ??
                            false,
                        )}
                      </div>
                      <div>
                        legal advice claimed:{' '}
                        {String(modelRouteLegalBenchmarkRiskQueue.claim_boundary.legal_advice_claimed ?? false)}
                      </div>
                      <div>
                        raw model output returned:{' '}
                        {String(modelRouteLegalBenchmarkRiskQueue.privacy_boundary.returns_raw_model_output ?? false)}
                      </div>
                      <div>
                        routing payloads returned:{' '}
                        {String(
                          modelRouteLegalBenchmarkRiskQueue.privacy_boundary.returns_routing_payloads ??
                            modelRouteLegalBenchmarkRiskQueue.privacy_boundary.returns_gateway_payloads ??
                            false,
                        )}
                      </div>
                      <div>
                        gateway calls allowed:{' '}
                        {String(modelRouteLegalBenchmarkRiskQueue.routing_policy.gateway_call_allowed ?? false)}
                      </div>
                    </div>

                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {modelRouteLegalBenchmarkRiskQueue.recommended_actions.slice(0, 3).map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-3 grid gap-3 lg:grid-cols-[1fr_1fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">User-need risk mapping</h3>
                    <div className="grid gap-3 md:grid-cols-2">
                      {modelRouteLegalBenchmarkRiskQueue.user_need_rows.slice(0, 4).map((row, index) => {
                        const rowKey = row.need_id ?? row.title ?? `route-need-${index}`;
                        const routeIds = row.task_ids ?? row.linked_route_ids ?? row.route_ids ?? [];
                        const queueRowIds = row.queue_row_ids ?? row.linked_queue_row_ids ?? [];
                        const coverageStatus =
                          row.highest_risk_level ??
                          row.user_need_status ??
                          row.coverage_status ??
                          row.legal_benchmark_status ??
                          'review_required';
                        return (
                          <div key={rowKey} className="rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3">
                            <div className="mb-2 flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className={statusClass[coverageStatus] ?? statusClass.warn}>
                                {displayToken(coverageStatus)}
                              </Badge>
                              {row.priority_band && (
                                <Badge
                                  variant="outline"
                                  className={priorityClass[row.priority_band] ?? priorityClass.medium}
                                >
                                  {row.priority_band}
                                  {row.priority_score !== undefined ? ` / ${row.priority_score}` : ''}
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm font-semibold text-stone-950">{row.title ?? row.need_id ?? '-'}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.need_id ?? '-'}</div>
                            <div className="mt-2 text-xs leading-5 text-stone-600">
                              routes: {routeIds.join(', ') || '-'}
                            </div>
                            <div className="text-xs leading-5 text-stone-600">
                              queue rows: {queueRowIds.join(', ') || '-'}
                            </div>
                            <div className="text-xs leading-5 text-stone-600">
                              sources: {(row.research_source_ids ?? []).join(', ') || '-'} / premium{' '}
                              {row.premium_exception_count ?? 0}
                            </div>
                            <div className="mt-1 text-xs leading-5 text-stone-500">
                              {row.next_action ?? row.next_actions?.[0] ?? row.gap_reasons?.[0] ?? 'Keep user need mapped.'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="grid gap-2 md:grid-cols-2">
                      {modelRouteLegalBenchmarkRiskQueue.validation_commands.slice(0, 4).map((command) => (
                        <div
                          key={command}
                          className="break-all rounded-[8px] border border-stone-950/10 bg-[#fbfaf6] p-3 font-mono text-[11px] text-stone-600"
                        >
                          {command}
                        </div>
                      ))}
                    </div>
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

            {legalDocumentBenchmarkCoverage && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal document benchmark coverage</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {legalDocumentBenchmarkCoverage.summary.covered_document_type_count}/
                      {legalDocumentBenchmarkCoverage.summary.target_document_type_count} document types covered /{' '}
                      {legalDocumentBenchmarkCoverage.summary.missing_document_type_count} gaps
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[legalDocumentBenchmarkCoverage.status] ?? statusClass.warn}
                  >
                    {legalDocumentBenchmarkCoverage.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  {[
                    { label: 'fixture cases', value: legalDocumentBenchmarkCoverage.summary.case_count },
                    { label: 'sections', value: legalDocumentBenchmarkCoverage.summary.section_label_count },
                    { label: 'citations', value: legalDocumentBenchmarkCoverage.summary.citation_label_count },
                    { label: 'risk labels', value: legalDocumentBenchmarkCoverage.summary.risk_label_count },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.15fr_0.85fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fixture</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Coverage axes</TableHead>
                          <TableHead>Run fit</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {legalDocumentBenchmarkCoverage.case_rows.map((row) => (
                          <TableRow key={row.case_id}>
                            <TableCell className="max-w-[340px]">
                              <div className="font-semibold text-stone-950">{row.title}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.case_id}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <Badge variant="outline" className="bg-white font-mono text-[11px]">
                                {row.document_type}
                              </Badge>
                              <div className="mt-2">{row.matter_type}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>{row.required_section_count} sections</div>
                              <div>{row.expected_citation_count} citations</div>
                              <div>{row.expected_risk_label_count} risk labels</div>
                              <div>{row.banned_pii_category_count} PII bans</div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                                {row.local_run_fit.replace(/_/g, ' ')}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Missing document types</h3>
                    <div className="mb-4 flex flex-wrap gap-2">
                      {legalDocumentBenchmarkCoverage.missing_document_types.length === 0 ? (
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-800">
                          all targets covered
                        </Badge>
                      ) : (
                        legalDocumentBenchmarkCoverage.missing_document_types.map((documentType) => (
                          <Badge key={documentType} variant="outline" className="bg-amber-50 text-amber-900">
                            {documentType.replace(/_/g, ' ')}
                          </Badge>
                        ))
                      )}
                    </div>
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      <div>model calls: {String(legalDocumentBenchmarkCoverage.privacy_boundary.model_calls)}</div>
                      <div>
                        raw model output:{' '}
                        {String(legalDocumentBenchmarkCoverage.privacy_boundary.returns_raw_model_output)}
                      </div>
                      <div>snippets: {String(legalDocumentBenchmarkCoverage.privacy_boundary.returns_snippets)}</div>
                      <div>network: {legalDocumentBenchmarkCoverage.summary.network_access}</div>
                    </div>
                    <div className="mt-3 text-xs leading-5 text-stone-500">
                      {legalDocumentBenchmarkCoverage.privacy_note}
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Next fixture</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Reason</TableHead>
                        <TableHead>Fixture shape</TableHead>
                        <TableHead>Validation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {legalDocumentBenchmarkCoverage.next_fixture_queue.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="font-mono text-xs font-semibold text-stone-950">
                            {item.document_type}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={priorityClass[item.priority] ?? priorityClass.medium}>
                              {item.priority}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">{item.reason}</TableCell>
                          <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                            {item.recommended_fixture_shape}
                          </TableCell>
                          <TableCell className="break-all font-mono text-[11px] text-stone-500">
                            {item.validation_target}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-white p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Coverage actions</h3>
                  <ul className="space-y-2 text-sm leading-6 text-stone-700">
                    {legalDocumentBenchmarkCoverage.recommended_actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>
            )}

            {legalDocumentFactConsistencyBenchmark && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">
                      Legal document fact consistency benchmark
                    </h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {legalDocumentFactConsistencyBenchmark.summary.case_count} cases /{' '}
                      {legalDocumentFactConsistencyBenchmark.summary.check_count} checks / tolerance{' '}
                      {legalDocumentFactConsistencyBenchmark.summary.amount_tolerance}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[legalDocumentFactConsistencyBenchmark.status] ?? statusClass.ready}
                  >
                    {legalDocumentFactConsistencyBenchmark.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  {[
                    { label: 'fact cases', value: legalDocumentFactConsistencyBenchmark.summary.case_count },
                    { label: 'checks', value: legalDocumentFactConsistencyBenchmark.summary.check_count },
                    { label: 'max cases', value: legalDocumentFactConsistencyBenchmark.summary.max_cases },
                    { label: 'tolerance', value: legalDocumentFactConsistencyBenchmark.summary.amount_tolerance },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-sm text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Case</TableHead>
                        <TableHead>Document</TableHead>
                        <TableHead>Structured expectations</TableHead>
                        <TableHead>Contradictions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {legalDocumentFactConsistencyBenchmark.benchmark_cases.map((row) => (
                        <TableRow key={row.id}>
                          <TableCell className="max-w-[320px]">
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.id}</div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <Badge variant="outline" className="bg-white font-mono text-[11px]">
                              {row.document_type}
                            </Badge>
                            <div className="mt-2">{row.matter_type}</div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>{row.amount_expectations.length} amount_expectations</div>
                            <div>{row.deadline_expectations.length} deadline_expectations</div>
                            <div>{row.required_fact_ids.length} required_fact_ids</div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>{row.contradiction_pairs.length} contradiction_pairs</div>
                            <div className="mt-1 text-stone-500">
                              {row.contradiction_pairs.slice(0, 2).map((item) => item.id).join(', ') || 'none'}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[1.15fr_0.85fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Check</TableHead>
                          <TableHead>Target</TableHead>
                          <TableHead>Weight</TableHead>
                          <TableHead>Local rule</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {legalDocumentFactConsistencyBenchmark.checks.map((check) => (
                          <TableRow key={check.id}>
                            <TableCell>
                              <div className="font-mono text-xs font-semibold text-stone-950">{check.id}</div>
                              {check.hard_fail && (
                                <Badge variant="outline" className="mt-2 bg-red-50 text-red-800">
                                  hard fail
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="font-mono text-xs text-stone-600">{check.target}</TableCell>
                            <TableCell>{check.weight}</TableCell>
                            <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">
                              {check.local_check}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="grid gap-2 text-xs leading-5 text-stone-600">
                      <div>model calls: {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.model_calls)}</div>
                      <div>network called: {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.network_called)}</div>
                      <div>
                        external datasets:{' '}
                        {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.external_dataset_downloads)}
                      </div>
                      <div>
                        returns_raw_document_text:{' '}
                        {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.returns_raw_document_text)}
                      </div>
                      <div>
                        generated text:{' '}
                        {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.returns_generated_text)}
                      </div>
                      <div>
                        credentials: {String(legalDocumentFactConsistencyBenchmark.privacy_boundary.returns_credentials)}
                      </div>
                    </div>
                    <h3 className="mb-2 mt-4 text-sm font-black uppercase text-stone-500">Validation</h3>
                    <div className="space-y-2">
                      {legalDocumentFactConsistencyBenchmark.validation_commands.map((command) => (
                        <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
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
                            <div className="mt-2 font-semibold text-stone-950">Document fixtures</div>
                            <div className="break-words font-mono text-[11px]">
                              {(source.document_fixture_ids ?? []).join(', ') || 'metadata only'}
                            </div>
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

            {publicBenchmarkLicenseGate && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Public benchmark license gate</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      {publicBenchmarkLicenseGate.summary.source_count} sources /{' '}
                      {publicBenchmarkLicenseGate.summary.license_review_required_source_count} need review /{' '}
                      {publicBenchmarkLicenseGate.summary.release_claim_blocked_source_count} claim-blocked
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[publicBenchmarkLicenseGate.status] ?? statusClass.warn}>
                    {displayToken(publicBenchmarkLicenseGate.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkLicenseGate.summary.approved_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">approved sources</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkLicenseGate.summary.license_review_required_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">license review</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkLicenseGate.summary.linked_user_need_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">linked user needs</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {publicBenchmarkLicenseGate.summary.linked_route_task_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">route tasks</div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Review</TableHead>
                        <TableHead>Mappings</TableHead>
                        <TableHead>Checks</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {publicBenchmarkLicenseGate.source_rows.map((source) => (
                        <TableRow key={source.id}>
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
                            <div className="mt-2 text-xs text-stone-600">{displayToken(source.resource_profile)}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[source.review_state] ?? statusClass.warn}>
                              {displayToken(source.review_state)}
                            </Badge>
                            <div className="mt-2 font-mono text-[11px] text-stone-500">{source.decision}</div>
                            <div className="mt-2 text-xs text-stone-600">max {source.max_samples} samples</div>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            <div className="font-semibold text-stone-950">User needs</div>
                            <div className="break-words font-mono text-[11px]">
                              {source.linked_user_need_ids.join(', ') || 'metadata only'}
                            </div>
                            <div className="mt-2 font-semibold text-stone-950">Route tasks</div>
                            <div className="break-words font-mono text-[11px]">
                              {source.linked_route_task_ids.join(', ') || 'metadata only'}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            <div className="flex flex-wrap gap-1">
                              {source.required_checks.map((check) => (
                                <Badge
                                  key={`${source.id}-${check.id}`}
                                  variant="outline"
                                  className={statusClass[check.status] ?? statusClass.warn}
                                >
                                  {displayToken(check.id)}
                                </Badge>
                              ))}
                            </div>
                            <div className="mt-2 font-mono text-[11px] text-stone-500">{source.license_gate}</div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {source.next_action}
                            <div className="mt-2">
                              public score claim: {String(source.public_score_claim_allowed)} / dataset download:{' '}
                              {String(source.dataset_download_allowed)}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">User need review</h3>
                    <div className="space-y-3">
                      {publicBenchmarkLicenseGate.user_need_rows.slice(0, 5).map((row) => (
                        <div key={row.need_id} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={priorityClass[row.priority_band] ?? priorityClass.medium}>
                              {displayToken(row.priority_band)}
                            </Badge>
                            <span className="font-mono text-[11px] text-stone-500">{row.need_id}</span>
                          </div>
                          <div className="font-semibold text-stone-950">{row.title}</div>
                          <div className="mt-2 text-xs leading-5 text-stone-600">{row.next_action}</div>
                          <div className="mt-2 break-words font-mono text-[11px] text-stone-500">
                            blocked: {row.blocked_source_ids.join(', ') || 'none'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>public benchmark scores claimed: {String(publicBenchmarkLicenseGate.claim_boundary.public_benchmark_scores_claimed)}</div>
                      <div>external dataset execution claimed: {String(publicBenchmarkLicenseGate.claim_boundary.external_dataset_execution_claimed)}</div>
                      <div>public benchmark text returned: {String(publicBenchmarkLicenseGate.privacy_boundary.returns_public_benchmark_text)}</div>
                      <div>datasets downloaded: {String(publicBenchmarkLicenseGate.privacy_boundary.dataset_downloaded)}</div>
                      <div>model calls: {String(publicBenchmarkLicenseGate.privacy_boundary.model_called)}</div>
                      <div>gateway calls: {String(publicBenchmarkLicenseGate.privacy_boundary.gateway_called)}</div>
                      <div>credentials returned: {String(publicBenchmarkLicenseGate.privacy_boundary.returns_credentials)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {publicBenchmarkLicenseGate.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <h3 className="mb-2 mt-4 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {publicBenchmarkLicenseGate.validation_commands.slice(0, 3).map((command) => (
                        <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {benchmarkFixtureCrosswalk && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Public benchmark source to local benchmark case, fixture, document fixture, and small corpus metadata path
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[benchmarkFixtureCrosswalk.status] ?? statusClass.ready}>
                    {displayToken(benchmarkFixtureCrosswalk.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-5">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkFixtureCrosswalk.summary.source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">sources</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkFixtureCrosswalk.summary.source_with_local_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">fixture mapped</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkFixtureCrosswalk.summary.source_with_document_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">document fixture mapped</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkFixtureCrosswalk.summary.source_with_small_corpus_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">small corpus mapped</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {benchmarkFixtureCrosswalk.summary.gap_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">mapping gaps</div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Coverage</TableHead>
                        <TableHead>Benchmark cases</TableHead>
                        <TableHead>Local fixtures</TableHead>
                        <TableHead>Document/corpus path</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {benchmarkFixtureCrosswalk.source_rows.map((row) => (
                        <TableRow key={row.source_id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_id}</div>
                            <div className="mt-2 flex flex-wrap gap-1">
                              <Badge variant="outline" className={priorityClass[row.priority] ?? priorityClass.low}>
                                {displayToken(row.priority)}
                              </Badge>
                              <Badge variant="outline" className={statusClass[row.sampling_state] ?? statusClass.warn}>
                                {displayToken(row.sampling_state)}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[row.coverage_status] ?? statusClass.review_required}>
                              {displayToken(row.coverage_status)}
                            </Badge>
                            <div className="mt-2 text-xs leading-5 text-stone-600">
                              {row.resource_profile.replace(/_/g, ' ')}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                            <div className="break-words font-mono text-[11px]">
                              {row.benchmark_case_ids.join(', ') || 'not mapped'}
                            </div>
                            <div className="mt-2 flex flex-wrap gap-1">
                              {row.validation_targets.slice(0, 4).map((target) => (
                                <Badge key={`${row.source_id}-${target}`} variant="outline" className="bg-white text-[11px]">
                                  {displayToken(target)}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                            <div className="font-semibold text-stone-950">fixture-*</div>
                            <div className="break-words font-mono text-[11px]">
                              {row.local_fixture_ids.join(', ') || 'not mapped'}
                            </div>
                            <div className="mt-2 font-semibold text-stone-950">license gate</div>
                            <div className="break-words font-mono text-[11px]">{row.license_gate}</div>
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            <div className="font-semibold text-stone-950">ldoc-*</div>
                            <div className="break-words font-mono text-[11px]">
                              {row.document_fixture_ids.join(', ') || 'not mapped'}
                            </div>
                            <div className="mt-2 font-semibold text-stone-950">small-corpus-*</div>
                            <div className="break-words font-mono text-[11px]">
                              {row.small_corpus_item_ids.join(', ') || 'not mapped'}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Gap queue</h3>
                    <div className="space-y-3">
                      {benchmarkFixtureCrosswalk.gap_queue.slice(0, 5).map((gap) => (
                        <div key={gap.source_id} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={priorityClass[gap.priority] ?? priorityClass.medium}>
                              {displayToken(gap.priority)}
                            </Badge>
                            <span className="font-mono text-[11px] text-stone-500">{gap.source_id}</span>
                          </div>
                          <div className="text-xs leading-5 text-stone-600">{gap.recommended_action}</div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {gap.gap_reasons.map((reason) => (
                              <Badge key={`${gap.source_id}-${reason}`} variant="outline" className="bg-[#fbfaf6] text-[11px]">
                                {displayToken(reason)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                      {benchmarkFixtureCrosswalk.gap_queue.length === 0 && (
                        <div className="text-sm text-stone-600">All public sources have a local metadata path.</div>
                      )}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>public benchmark scores claimed: {String(benchmarkFixtureCrosswalk.summary.public_benchmark_score_claimed)}</div>
                      <div>public benchmark text returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_public_benchmark_text)}</div>
                      <div>fixture snippets returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_local_fixture_snippets)}</div>
                      <div>small corpus excerpts returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_small_corpus_excerpts)}</div>
                      <div>generated text returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_generated_text)}</div>
                      <div>raw model output returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_raw_model_output)}</div>
                      <div>credentials returned: {String(benchmarkFixtureCrosswalk.privacy_boundary.returns_credentials)}</div>
                      <div>datasets downloaded: {String(benchmarkFixtureCrosswalk.privacy_boundary.downloads_datasets)}</div>
                      <div>model calls: {String(benchmarkFixtureCrosswalk.privacy_boundary.model_calls)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {benchmarkFixtureCrosswalk.recommended_actions.map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <h3 className="mb-2 mt-4 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {benchmarkFixtureCrosswalk.validation_commands.slice(0, 3).map((command) => (
                        <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
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

            {geminiNewApiModelSelector && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only selector evidence; excludes credentials, prompts, raw legal text, and raw model outputs.
                      This panel does not claim an actual NewAPI call was made.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[geminiNewApiModelSelector.status] ?? statusClass.review_recommended}
                  >
                    {geminiNewApiModelSelector.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-5">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {geminiNewApiModelSelector.summary.task_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">tasks</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {geminiNewApiModelSelector.summary.cheap_first_ready_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first ready</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {geminiNewApiModelSelector.summary.premium_exception_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">premium exceptions</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {geminiNewApiModelSelector.summary.catalog_review_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">catalog reviews</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {geminiNewApiModelSelector.summary.unknown_model_count ?? 0}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">unknown models</div>
                  </div>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.35fr_0.65fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Task</TableHead>
                          <TableHead>Selected model</TableHead>
                          <TableHead>Cost tier</TableHead>
                          <TableHead>Decision</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {geminiNewApiModelSelector.task_recommendations.slice(0, 6).map((item) => (
                          <TableRow key={`${item.task}-${item.selected_model}`}>
                            <TableCell className="max-w-[260px]">
                              <div className="font-semibold text-stone-950">{item.task}</div>
                              {item.escalation_chain && item.escalation_chain.length > 0 && (
                                <div className="mt-1 text-xs leading-5 text-stone-600">
                                  escalate: {item.escalation_chain.slice(0, 3).join(' -> ')}
                                </div>
                              )}
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              <div className="font-mono font-semibold text-stone-950">{item.selected_model}</div>
                              <div className="font-mono text-[11px]">{item.canonical_model ?? '-'}</div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="bg-white">
                                {item.cost_tier ?? 'unknown'}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              <div>{item.decision ?? item.route_mode ?? '-'}</div>
                              {item.route_mode && item.decision && (
                                <div className="mt-1 font-mono text-[11px] text-stone-500">{item.route_mode}</div>
                              )}
                              {item.warnings && item.warnings.length > 0 && (
                                <div className="mt-1 text-amber-800">{item.warnings.slice(0, 2).join('; ')}</div>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="space-y-3">
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Observed model review</h3>
                      <div className="space-y-3">
                        {geminiNewApiModelSelector.observed_model_reviews.slice(0, 4).map((review) => (
                          <div key={`${review.raw_model}-${review.status}`} className="text-xs leading-5 text-stone-600">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono font-semibold text-stone-950">{review.raw_model}</span>
                              <Badge variant="outline" className={statusClass[review.status] ?? statusClass.not_run}>
                                {review.status.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <div className="mt-1 font-mono text-[11px]">{review.canonical_model ?? '-'}</div>
                            {review.action && <div className="mt-1">{review.action}</div>}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Default ladders</h3>
                      <div className="space-y-3">
                        {geminiNewApiModelSelector.cheap_first_ladders.slice(0, 3).map((ladder) => (
                          <div key={ladder.task_group} className="text-xs leading-5 text-stone-600">
                            <div className="font-mono font-semibold text-stone-950">{ladder.task_group}</div>
                            <div className="mt-2 space-y-2">
                              {(ladder.ladder ?? []).slice(0, 3).map((item) => (
                                <div key={`${ladder.task_group}-${item.order}-${item.model}`} className="rounded-[8px] border border-stone-950/10 bg-white p-2">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="font-mono font-semibold text-stone-950">{item.model}</span>
                                    <Badge
                                      variant="outline"
                                      className={item.review_required ? statusClass.review_required : statusClass.ready}
                                    >
                                      {item.candidate_stage ?? (item.review_required ? 'review only' : 'default eligible')}
                                    </Badge>
                                  </div>
                                  <div className="mt-1 text-stone-600">
                                    {item.cost_tier} / {item.pricing_status ?? 'unknown'} / {item.role ?? 'candidate'}
                                  </div>
                                  {item.promotion_blockers && item.promotion_blockers.length > 0 && (
                                    <div className="mt-1 font-mono text-[11px] text-amber-800">
                                      {item.promotion_blockers.slice(0, 3).join(', ')}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                      <ul className="space-y-2 text-xs leading-5 text-stone-600">
                        {geminiNewApiPrivacyBoundarySummary(geminiNewApiModelSelector.privacy_boundary).map((item) => (
                          <li key={item} className="flex gap-2">
                            <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {geminiNewApiModelAliasMatrix && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model alias matrix</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only alias evidence for OpenAI-compatible Gemini gateway model names. It excludes
                      credentials, prompts, complete legal text, gateway payload bodies, and model outputs.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[geminiNewApiModelAliasMatrix.status] ?? statusClass.review_recommended}
                  >
                    {geminiNewApiModelAliasMatrix.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-6">
                  {[
                    { label: 'aliases', value: geminiNewApiModelAliasMatrix.summary.alias_row_count ?? 0 },
                    { label: 'catalog models', value: geminiNewApiModelAliasMatrix.summary.catalog_model_count ?? 0 },
                    { label: 'known aliases', value: geminiNewApiModelAliasMatrix.summary.known_alias_count ?? 0 },
                    {
                      label: 'cheap-first',
                      value: geminiNewApiModelAliasMatrix.summary.high_frequency_default_allowed_count ?? 0,
                    },
                    { label: 'catalog review', value: geminiNewApiModelAliasMatrix.summary.catalog_review_count ?? 0 },
                    {
                      label: 'rejected',
                      value:
                        geminiNewApiModelAliasMatrix.summary.rejected_model_count ??
                        geminiNewApiModelAliasMatrix.summary.rejected_sensitive_count ??
                        0,
                    },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-3">
                      <div className="text-xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-xs text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.5fr_0.5fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Alias</TableHead>
                          <TableHead>Canonical</TableHead>
                          <TableHead>Shape</TableHead>
                          <TableHead>Default class</TableHead>
                          <TableHead>Boundary</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(geminiNewApiModelAliasMatrix.alias_rows ?? []).slice(0, 8).map((row, index) => {
                          const rowKey = `${row.id}-${row.alias_model}-${row.alias_status}-${index}`;
                          return (
                            <TableRow key={rowKey}>
                              <TableCell className="max-w-[260px]">
                                <div className="font-mono text-xs font-semibold text-stone-950">{row.alias_model}</div>
                                <div className="mt-1 text-[11px] text-stone-500">{row.source}</div>
                              </TableCell>
                              <TableCell className="max-w-[220px]">
                                <div className="font-mono text-xs text-stone-700">{row.canonical_model ?? '-'}</div>
                                <Badge variant="outline" className="mt-2 bg-white">
                                  {row.cost_tier ?? 'unknown'}
                                </Badge>
                              </TableCell>
                              <TableCell className="max-w-[210px]">
                                <div className="font-mono text-xs text-stone-700">{row.alias_shape}</div>
                                <Badge
                                  variant="outline"
                                  className={statusClass[row.alias_status] ?? statusClass.review_recommended}
                                >
                                  {row.alias_status.replace(/_/g, ' ')}
                                </Badge>
                              </TableCell>
                              <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                                <div className="font-mono font-semibold text-stone-950">{row.default_class}</div>
                                {(row.reason_codes ?? []).slice(0, 3).map((reason, reasonIndex) => (
                                  <div key={`${rowKey}-${reason}-${reasonIndex}`} className="mt-1">
                                    {reason}
                                  </div>
                                ))}
                              </TableCell>
                              <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                                <div className="flex flex-wrap gap-2">
                                  <Badge variant="outline" className={row.high_frequency_default_allowed ? statusClass.ready : statusClass.warn}>
                                    high frequency {row.high_frequency_default_allowed ? 'allowed' : 'blocked'}
                                  </Badge>
                                  <Badge variant="outline" className={row.premium_exception ? statusClass.warn : statusClass.ready}>
                                    {row.premium_exception ? 'review required' : 'cheap-first ok'}
                                  </Badge>
                                </div>
                                {row.recommended_action && <div className="mt-2">{row.recommended_action}</div>}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="space-y-3">
                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Accepted shapes</h3>
                      <div className="mb-3 grid grid-cols-2 gap-2 text-xs leading-5 text-stone-600">
                        <div className="rounded-[6px] border border-stone-950/10 bg-white p-2">
                          <div className="font-mono text-stone-950">
                            {geminiNewApiModelAliasMatrix.summary.rejected_sensitive_count ?? 0}
                          </div>
                          <div>sensitive</div>
                        </div>
                        <div className="rounded-[6px] border border-stone-950/10 bg-white p-2">
                          <div className="font-mono text-stone-950">
                            {geminiNewApiModelAliasMatrix.summary.rejected_invalid_count ?? 0}
                          </div>
                          <div>invalid format</div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {(geminiNewApiModelAliasMatrix.accepted_alias_shapes ?? []).slice(0, 6).map((shape) => (
                          <div key={shape} className="font-mono text-xs leading-5 text-stone-700">
                            {shape}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Alias privacy boundary</h3>
                      <ul className="space-y-2 text-xs leading-5 text-stone-600">
                        {geminiNewApiPrivacyBoundarySummary(geminiNewApiModelAliasMatrix.privacy_boundary).map((item) => (
                          <li key={item} className="flex gap-2">
                            <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {geminiNewApiSelectorReplay && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Gemini/NewAPI selector replay</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only replay evidence; does not call NewAPI and excludes credentials, prompts, raw legal
                      text, and raw model outputs.
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[geminiNewApiSelectorReplay.status] ?? statusClass.review_recommended}
                  >
                    {geminiNewApiSelectorReplay.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-7">
                  {[
                    { label: 'scenarios', value: geminiNewApiSelectorReplay.summary.scenario_count ?? 0 },
                    { label: 'pass', value: geminiNewApiSelectorReplay.summary.pass_count ?? 0 },
                    { label: 'warn', value: geminiNewApiSelectorReplay.summary.warn_count ?? 0 },
                    { label: 'fail', value: geminiNewApiSelectorReplay.summary.fail_count ?? 0 },
                    { label: 'cheap-first', value: geminiNewApiSelectorReplay.summary.cheap_first_pass_count ?? 0 },
                    { label: 'premium', value: geminiNewApiSelectorReplay.summary.premium_exception_count ?? 0 },
                    { label: 'catalog-review', value: geminiNewApiSelectorReplay.summary.catalog_review_count ?? 0 },
                  ].map((metric) => (
                    <div key={metric.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-3">
                      <div className="text-xl font-black text-stone-950">{metric.value}</div>
                      <div className="mt-1 text-xs text-stone-600">{metric.label}</div>
                    </div>
                  ))}
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.45fr_0.55fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Replay</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Selected model</TableHead>
                          <TableHead>Decision</TableHead>
                          <TableHead>Cost tier</TableHead>
                          <TableHead>Recommended action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {geminiNewApiSelectorReplay.replay_results.slice(0, 7).map((result) => (
                          <TableRow key={result.id}>
                            <TableCell className="max-w-[240px]">
                              <div className="font-mono text-xs font-semibold text-stone-950">{result.id}</div>
                              {result.actual?.route_mode && (
                                <div className="mt-1 font-mono text-[11px] text-stone-500">
                                  {result.actual.route_mode}
                                </div>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={statusClass[result.status] ?? statusClass.not_run}>
                                {result.status.replace(/_/g, ' ')}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                              <div className="font-mono font-semibold text-stone-950">
                                {result.actual?.selected_model ?? '-'}
                              </div>
                              <div className="font-mono text-[11px]">{result.actual?.canonical_model ?? '-'}</div>
                            </TableCell>
                            <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                              {result.actual?.decision ?? '-'}
                              {result.actual?.warnings && result.actual.warnings.length > 0 && (
                                <div className="mt-1 text-amber-800">{result.actual.warnings.slice(0, 2).join('; ')}</div>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="bg-white">
                                {result.actual?.cost_tier ?? 'unknown'}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                              {result.recommended_action ?? '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <ul className="space-y-2 text-xs leading-5 text-stone-600">
                      {geminiNewApiPrivacyBoundarySummary(geminiNewApiSelectorReplay.privacy_boundary).map((item) => (
                        <li key={item} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs leading-5 text-stone-600">
                      Replay validation uses selector metadata only. NewAPI is not invoked; credentials, prompts, raw
                      legal text, and raw model outputs stay outside this evidence payload.
                    </div>
                  </div>
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
                  {fixtureLocalRunReview && (
                    <div className="mt-3 rounded-[8px] border border-stone-950/10 bg-white p-3">
                      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <h4 className="text-xs font-black uppercase text-stone-500">Local run review status</h4>
                          <div className="mt-1 text-xs leading-5 text-stone-600">
                            Safe summary only; raw gateway responses, prompts, headers, and model outputs are not rendered.
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge
                            variant="outline"
                            className={statusClass[fixtureLocalRunReview.status] ?? statusClass.review_recommended}
                          >
                            {displayToken(fixtureLocalRunReview.status)}
                          </Badge>
                          <Badge variant="outline" className="bg-[#fbfaf6]">
                            {displayToken(fixtureLocalRunReview.release_decision)}
                          </Badge>
                        </div>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
                        <div>
                          <div className="text-lg font-black text-stone-950">
                            {fixtureLocalRunReview.summary.normalized_observation_count}
                          </div>
                          <div className="text-[11px] font-semibold uppercase text-stone-500">observations</div>
                        </div>
                        <div>
                          <div className="text-lg font-black text-stone-950">
                            {fixtureLocalRunReview.summary.not_run_fixture_count}
                          </div>
                          <div className="text-[11px] font-semibold uppercase text-stone-500">not run</div>
                        </div>
                        <div>
                          <div className="text-lg font-black text-stone-950">
                            {fixtureLocalRunReview.summary.redacted_response_count}
                          </div>
                          <div className="text-[11px] font-semibold uppercase text-stone-500">redacted</div>
                        </div>
                        <div>
                          <div className="text-lg font-black text-stone-950">
                            {fixtureLocalRunReview.summary.blocking_check_count}
                          </div>
                          <div className="text-[11px] font-semibold uppercase text-stone-500">blocking checks</div>
                        </div>
                        <div>
                          <div className="text-lg font-black text-stone-950">
                            {fixtureLocalRunReview.summary.warning_check_count}
                          </div>
                          <div className="text-[11px] font-semibold uppercase text-stone-500">warnings</div>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase text-stone-500">evidence bundle status</div>
                          <div className="mt-1 font-mono text-xs text-stone-700">
                            {fixtureLocalRunReview.summary.evidence_bundle_status}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
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

            {legalRagAuthorityCitationGate && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal RAG authority citation gate</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only authority and citation quality review for retrieved legal sources
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[legalRagAuthorityCitationGate.status] ?? statusClass.review_required}
                  >
                    {displayToken(legalRagAuthorityCitationGate.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                  {[
                    {
                      label: 'source tiers',
                      value:
                        legalRagAuthorityCitationGate.summary.source_tier_count ??
                        Object.keys(legalRagAuthorityCitationGate.source_tiers ?? {}).length,
                    },
                    {
                      label: 'authority reviewed',
                      value:
                        legalRagAuthorityCitationGate.summary.authority_review_count ??
                        (legalRagAuthorityCitationGate.source_rows ?? []).length,
                    },
                    {
                      label: 'jurisdictions',
                      value:
                        legalRagAuthorityCitationGate.summary.jurisdiction_count ??
                        Object.keys(legalRagAuthorityCitationGate.jurisdiction_counts ?? {}).length,
                    },
                    {
                      label: 'freshness gaps',
                      value:
                        legalRagAuthorityCitationGate.summary.freshness_gap_count ??
                        legalRagAuthorityCitationGate.summary.stale_source_count ??
                        0,
                    },
                    {
                      label: 'citation mismatches',
                      value:
                        legalRagAuthorityCitationGate.summary.citation_mismatch_count ??
                        (legalRagAuthorityCitationGate.citation_mismatch_rows ?? []).length,
                    },
                    {
                      label: 'retrieval gaps',
                      value:
                        legalRagAuthorityCitationGate.summary.retrieval_gap_count ??
                        (legalRagAuthorityCitationGate.retrieval_gap_rows ?? []).length,
                    },
                  ].map((item) => (
                    <div key={item.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{formatInline(item.value)}</div>
                      <div className="mt-1 text-sm text-stone-600">{item.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Tier / authority</TableHead>
                        <TableHead>Jurisdiction / freshness</TableHead>
                        <TableHead>Citation mismatch</TableHead>
                        <TableHead>Retrieval gap</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(legalRagAuthorityCitationGate.source_rows ?? []).slice(0, 8).map((row, index) => {
                        const rowId = row.id ?? row.source_id ?? `authority-row-${index}`;
                        const sourceTitle = row.title ?? row.source_title ?? row.source_id ?? row.id ?? 'source metadata';
                        const tier = row.source_tier ?? row.tier ?? '-';
                        const authority = row.authority ?? row.authority_level ?? '-';
                        const freshness = row.freshness_status ?? row.freshness ?? '-';
                        const citationMismatch = row.citation_mismatch_count ?? row.citation_mismatches ?? 0;
                        const retrievalGap = row.retrieval_gap_count ?? row.retrieval_gaps ?? 0;
                        return (
                          <TableRow key={rowId}>
                            <TableCell>
                              <div className="font-semibold text-stone-950">{sourceTitle}</div>
                              <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_id ?? row.id ?? '-'}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>tier: {formatInline(tier)}</div>
                              <div>authority: {formatInline(authority)}</div>
                            </TableCell>
                            <TableCell className="text-xs leading-5 text-stone-600">
                              <div>jurisdiction: {formatInline(row.jurisdiction ?? row.jurisdiction_status ?? '-')}</div>
                              <div>freshness: {formatInline(freshness)}</div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={citationMismatch > 0 ? statusClass.review_required : statusClass.ready}
                              >
                                {citationMismatch}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={retrievalGap > 0 ? statusClass.review_required : statusClass.ready}>
                                {retrievalGap}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={statusClass[row.status ?? 'ready'] ?? statusClass.not_run}>
                                {displayToken(row.status ?? 'ready')}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Claim boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>legal advice claimed: {String(legalRagAuthorityCitationGate.claim_boundary.legal_advice_claimed ?? false)}</div>
                      <div>
                        unsupported claims allowed:{' '}
                        {String(legalRagAuthorityCitationGate.claim_boundary.unsupported_claims_allowed ?? false)}
                      </div>
                      <div>
                        citation without source allowed:{' '}
                        {String(legalRagAuthorityCitationGate.claim_boundary.citation_without_source_allowed ?? false)}
                      </div>
                      <div>
                        jurisdiction mismatch allowed:{' '}
                        {String(legalRagAuthorityCitationGate.claim_boundary.jurisdiction_mismatch_allowed ?? false)}
                      </div>
                      <div>freshness gap allowed: {String(legalRagAuthorityCitationGate.claim_boundary.freshness_gap_allowed ?? false)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>metadata-only: {String(legalRagAuthorityCitationGate.privacy_boundary.metadata_only ?? true)}</div>
                      <div>
                        raw legal text:{' '}
                        {String(
                          legalRagAuthorityCitationGate.privacy_boundary.returns_raw_legal_text ??
                            legalRagAuthorityCitationGate.privacy_boundary.returns_raw_source_text ??
                            false,
                        )}
                      </div>
                      <div>
                        prompt returned:{' '}
                        {String(
                          legalRagAuthorityCitationGate.privacy_boundary.returns_prompts ??
                            legalRagAuthorityCitationGate.privacy_boundary.returns_prompt ??
                            false,
                        )}
                      </div>
                      <div>
                        model output:{' '}
                        {String(
                          legalRagAuthorityCitationGate.privacy_boundary.returns_raw_model_output ??
                            legalRagAuthorityCitationGate.privacy_boundary.returns_model_output ??
                            false,
                        )}
                      </div>
                      <div>
                        credentials:{' '}
                        {String(
                          legalRagAuthorityCitationGate.privacy_boundary.returns_credentials ??
                            legalRagAuthorityCitationGate.privacy_boundary.returns_secrets ??
                            false,
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {(legalRagAuthorityCitationGate.recommended_actions ?? []).slice(0, 5).map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {(legalRagAuthorityCitationGate.validation_commands ?? []).slice(0, 4).map((command) => (
                        <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {legalRagRetrievalDiagnosticsGate &&
              (() => {
                const gate = legalRagRetrievalDiagnosticsGate;
                const rows = gate.diagnostic_rows ?? [];
                const summary = gate.summary ?? {};
                const linkage = gate.linkage ?? {};
                const linkedGateSummary = gate.linked_gate_summary ?? {};
                const gateStatuses = linkage.gate_statuses ?? {};
                const cheapFirstDecision = (action: unknown) => {
                  if (typeof action === 'string') return action;
                  if (action && typeof action === 'object') {
                    const record = action as Record<string, unknown>;
                    return String(record.decision ?? record.task ?? '-');
                  }
                  return '-';
                };
                const cheapFirstModelAlias = (action: unknown) => {
                  if (action && typeof action === 'object') {
                    const record = action as Record<string, unknown>;
                    return String(record.recommended_model_alias ?? '-');
                  }
                  return '-';
                };
                const cheapFirstStartsCheap = (action: unknown) =>
                  action && typeof action === 'object' ? Boolean((action as Record<string, unknown>).starts_cheap) : false;
                const linkedGates = [
                  {
                    id: 'legal-rag-index-binding',
                    status: String(
                      gateStatuses['legal-rag-index-binding'] ??
                        linkage.legal_rag_index_binding_status ??
                        linkedGateSummary.legal_rag_index_binding ??
                        'metadata_only',
                    ),
                  },
                  {
                    id: 'legal-rag-authority-citation-gate',
                    status: String(
                      gateStatuses['legal-rag-authority-citation-gate'] ??
                        linkage.legal_rag_authority_citation_gate_status ??
                        linkedGateSummary.authority_gate_id ??
                        legalRagAuthorityCitationGate?.status ??
                        'not_run',
                    ),
                  },
                  {
                    id: 'legal-rag-abstention-escalation-gate',
                    status: String(
                      gateStatuses['legal-rag-abstention-escalation-gate'] ??
                        linkage.legal_rag_abstention_escalation_gate_status ??
                        linkedGateSummary.abstention_gate_id ??
                        legalRagAbstentionEscalationGate?.status ??
                        'not_run',
                    ),
                  },
                ];
                const rowStatusCount = (keys: string[]) =>
                  rows.filter((row) =>
                    keys.some((key) =>
                      [
                        row.retrieval_status,
                        row.source_coverage_status,
                        row.top_k_depth_status,
                        row.jurisdiction_status,
                        row.freshness_status,
                        row.release_action,
                      ]
                        .map((value) => String(value ?? '').toLowerCase())
                        .some((value) => value.includes(key)),
                    ),
                  ).length;
                const jurisdictionFreshnessGaps =
                  Number(summary.jurisdiction_freshness_gap_count ?? NaN) ||
                  Number(summary.jurisdiction_gap_count ?? 0) + Number(summary.freshness_gap_count ?? 0) ||
                  rows.filter((row) =>
                    [row.jurisdiction_status, row.freshness_status]
                      .map((value) => String(value ?? '').toLowerCase())
                      .some((value) => value.includes('gap') || value.includes('stale') || value.includes('mismatch')),
                  ).length;
                const summaryCounts = [
                  { label: 'diagnostic rows', value: summary.diagnostic_row_count ?? rows.length },
                  { label: 'ready rows', value: summary.ready_row_count ?? rowStatusCount(['ready', 'pass']) },
                  { label: 'review rows', value: summary.review_row_count ?? rowStatusCount(['review', 'warn']) },
                  { label: 'blocked rows', value: summary.blocked_row_count ?? rowStatusCount(['block', 'fail']) },
                  {
                    label: 'authority coverage',
                    value: summary.authority_coverage ?? summary.authority_coverage_count ?? summary.authority_coverage_status ?? '-',
                  },
                  {
                    label: 'retrieval depth gaps',
                    value:
                      summary.retrieval_depth_gap_count ??
                      summary.retrieval_depth_gaps ??
                      rows.filter((row) => String(row.top_k_depth_status ?? '').toLowerCase().includes('gap')).length,
                  },
                  { label: 'jurisdiction/freshness gaps', value: jurisdictionFreshnessGaps },
                  {
                    label: 'cheap-first retry count',
                    value:
                      summary.cheap_first_retry_count ??
                      summary.cheap_first_retry_rows ??
                      rows.filter((row) => ['verify', 'escalate'].includes(cheapFirstDecision(row.cheap_first_action).toLowerCase()))
                        .length,
                  },
                ];
                const privacy = gate.privacy_boundary ?? {};
                const claim = gate.claim_boundary ?? {};
                const boundaryRows = [
                  {
                    label: 'model',
                    value: boundaryFlag(privacy, ['model_called', 'model_calls']) || boundaryFlag(claim, ['model_claimed']),
                  },
                  {
                    label: 'gateway',
                    value: boundaryFlag(privacy, ['gateway_called']) || boundaryFlag(claim, ['gateway_claimed']),
                  },
                  {
                    label: 'network',
                    value: boundaryFlag(privacy, ['network_called', 'network_access']) || boundaryFlag(claim, ['network_claimed']),
                  },
                  {
                    label: 'raw query',
                    value:
                      boundaryFlag(privacy, [['returns', 'raw', 'query'].join('_'), 'returns_query_text']) ||
                      boundaryFlag(claim, [['raw', 'query', 'included'].join('_')]),
                  },
                  {
                    label: 'raw context',
                    value:
                      boundaryFlag(privacy, [['returns', 'raw', 'context'].join('_'), 'returns_context_text']) ||
                      boundaryFlag(claim, [['raw', 'context', 'included'].join('_')]),
                  },
                  {
                    label: 'raw legal text',
                    value:
                      boundaryFlag(privacy, [['returns', 'raw', 'legal', 'text'].join('_'), 'returns_legal_text']) ||
                      boundaryFlag(claim, [['raw', 'legal', 'text', 'included'].join('_')]),
                  },
                  {
                    label: 'prompts',
                    value: boundaryFlag(privacy, ['returns_prompts']) || boundaryFlag(claim, ['prompts_included']),
                  },
                  {
                    label: 'model output',
                    value:
                      boundaryFlag(privacy, ['returns_model_output', ['returns', 'raw', 'model', 'output'].join('_')]) ||
                      boundaryFlag(claim, ['model_output_included']),
                  },
                  {
                    label: 'credentials',
                    value:
                      boundaryFlag(privacy, ['returns_credentials', 'credentials_included']) ||
                      boundaryFlag(claim, ['credentials_included']),
                  },
                ];

                return (
                  <section className="mb-8">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h2 className="text-xl font-black text-stone-950">Legal RAG retrieval diagnostics gate</h2>
                        <div className="mt-1 text-sm text-stone-600">
                          Metadata-only retrieval depth, source coverage, jurisdiction, freshness, and cheap-first retry diagnostics
                        </div>
                      </div>
                      <Badge variant="outline" className={statusClass[gate.status] ?? statusClass.review_required}>
                        {displayToken(gate.status)}
                      </Badge>
                    </div>

                    <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
                      {summaryCounts.map((item) => (
                        <div key={item.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                          <div className="text-2xl font-black text-stone-950">{formatInline(item.value)}</div>
                          <div className="mt-1 text-sm text-stone-600">{item.label}</div>
                        </div>
                      ))}
                    </div>

                    <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Query intent</TableHead>
                            <TableHead>Retrieval status</TableHead>
                            <TableHead>Source coverage status</TableHead>
                            <TableHead>Top-k depth status</TableHead>
                            <TableHead>Jurisdiction / freshness status</TableHead>
                            <TableHead>Cheap-first action / release action</TableHead>
                            <TableHead>Linked gate ids</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {rows.slice(0, 8).map((row, index) => {
                            const rowId = row.id ?? row.diagnostic_id ?? `${gate.id}-row-${index}`;
                            return (
                              <TableRow key={rowId}>
                                <TableCell>
                                  <div className="font-semibold text-stone-950">{displayToken(row.query_intent ?? 'unclassified')}</div>
                                  <div className="mt-1 font-mono text-[11px] text-stone-500">{row.diagnostic_id ?? row.id ?? '-'}</div>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className={statusClass[row.retrieval_status] ?? statusClass.not_run}>
                                    {displayToken(row.retrieval_status)}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className={statusClass[row.source_coverage_status] ?? statusClass.not_run}>
                                    {displayToken(row.source_coverage_status)}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className={statusClass[row.top_k_depth_status] ?? statusClass.not_run}>
                                    {displayToken(row.top_k_depth_status)}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-xs leading-5 text-stone-600">
                                  <div>jurisdiction status: {displayToken(row.jurisdiction_status)}</div>
                                  <div>freshness status: {displayToken(row.freshness_status)}</div>
                                </TableCell>
                                <TableCell className="text-xs leading-5 text-stone-600">
                                  <div>cheap-first action: {displayToken(cheapFirstDecision(row.cheap_first_action))}</div>
                                  <div>starts cheap: {cheapFirstStartsCheap(row.cheap_first_action) ? 'true' : 'false'}</div>
                                  <div>model alias: {displayToken(cheapFirstModelAlias(row.cheap_first_action))}</div>
                                  <div>release action: {displayToken(row.release_action)}</div>
                                </TableCell>
                                <TableCell>
                                  <div className="flex max-w-[260px] flex-wrap gap-1.5">
                                    {(row.linked_gate_ids ?? []).length ? (
                                      row.linked_gate_ids.map((gateId) => (
                                        <Badge key={`${rowId}-${gateId}`} variant="outline" className="bg-white">
                                          {gateId}
                                        </Badge>
                                      ))
                                    ) : (
                                      <span className="text-xs text-stone-500">-</span>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>

                    <div className="grid gap-3 lg:grid-cols-4">
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Linkage</h3>
                        <div className="flex flex-wrap gap-2">
                          {linkedGates.map((linkedGate) => (
                            <Badge
                              key={linkedGate.id}
                              variant="outline"
                              className={statusClass[linkedGate.status] ?? statusClass.not_run}
                            >
                              {linkedGate.id}: {displayToken(linkedGate.status)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                        <div className="space-y-2 text-xs leading-5 text-stone-600">
                          {boundaryRows.map((item) => (
                            <div key={item.label}>
                              {item.label}: {includedBoundaryLabel(item.value)}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                        <ul className="space-y-2 text-sm leading-6 text-stone-700">
                          {(gate.recommended_actions ?? []).slice(0, 5).map((action) => (
                            <li key={action} className="flex gap-2">
                              <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                        <div className="space-y-2">
                          {(legalRagRetrievalDiagnosticsGate.validation_commands ?? []).slice(0, 4).map((command) => (
                            <div
                              key={command}
                              className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600"
                            >
                              {command}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>
                );
              })()}

            {legalRagBenchmarkAlignment && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal RAG benchmark alignment scorecard</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Public benchmark signals mapped to local retrieval diagnostics, abstention, fixture crosswalk, and cheap-first boundaries
                    </div>
                  </div>
                  <Badge variant="outline" className={statusClass[legalRagBenchmarkAlignment.status] ?? statusClass.review_required}>
                    {displayToken(legalRagBenchmarkAlignment.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
                  {[
                    { label: 'dimensions', value: legalRagBenchmarkAlignment.summary.dimension_count },
                    { label: 'aligned', value: legalRagBenchmarkAlignment.summary.aligned_count },
                    { label: 'review', value: legalRagBenchmarkAlignment.summary.review_count },
                    { label: 'gaps', value: legalRagBenchmarkAlignment.summary.gap_count },
                    { label: 'blocked claims', value: legalRagBenchmarkAlignment.summary.blocked_claim_count },
                    { label: 'retrieval blockers', value: legalRagBenchmarkAlignment.summary.retrieval_blocked_row_count },
                    { label: 'abstention blockers', value: legalRagBenchmarkAlignment.summary.abstention_blocker_count },
                    { label: 'crosswalk gaps', value: legalRagBenchmarkAlignment.summary.fixture_crosswalk_gap_count },
                  ].map((item) => (
                    <div key={item.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{formatInline(item.value)}</div>
                      <div className="mt-1 text-sm text-stone-600">{item.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Dimension</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Coverage</TableHead>
                        <TableHead>Benchmark signals</TableHead>
                        <TableHead>Release action</TableHead>
                        <TableHead>Cheap-first</TableHead>
                        <TableHead>Gap reasons</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(legalRagBenchmarkAlignment.alignment_rows ?? []).slice(0, 8).map((row) => (
                        <TableRow key={row.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.id}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[row.alignment_status] ?? statusClass.review_required}>
                              {displayToken(row.alignment_status)}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>{row.coverage_score}%</div>
                            <div>missing targets: {(row.missing_validation_targets ?? []).length}</div>
                            <div>missing fixtures: {(row.missing_local_fixture_ids ?? []).length}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[260px] flex-wrap gap-1.5">
                              {(row.benchmark_signal_ids ?? []).map((sourceId) => (
                                <Badge key={`${row.id}-${sourceId}`} variant="outline" className="bg-white">
                                  {sourceId}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass[row.release_action] ?? statusClass.not_run}>
                              {displayToken(row.release_action)}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>starts cheap: {String(row.starts_cheap)}</div>
                            <div>premium exception: {String(row.premium_exception_allowed)}</div>
                            <div className="mt-1 max-w-[260px] text-stone-500">{row.cheap_first_policy}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[300px] flex-wrap gap-1.5">
                              {(row.gap_reasons ?? []).length ? (
                                row.gap_reasons.map((reason) => (
                                  <Badge key={`${row.id}-${reason}`} variant="outline" className={statusClass.warn}>
                                    {displayToken(reason)}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-xs text-stone-500">-</span>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Research basis</h3>
                    <div className="space-y-2">
                      {(legalRagBenchmarkAlignment.research_basis ?? []).slice(0, 4).map((source) => (
                        <div key={source.id} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                          <div className="font-mono text-[11px] text-stone-500">{source.id}</div>
                          <div className="mt-1 text-sm leading-5 text-stone-700">{source.signal}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Linked gates</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      {Object.entries(legalRagBenchmarkAlignment.linked_gate_summary ?? {}).slice(0, 8).map(([key, value]) => (
                        <div key={key}>
                          {displayToken(key)}: {formatInline(value)}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>legal advice claimed: {String(legalRagBenchmarkAlignment.claim_boundary.legal_advice_claimed)}</div>
                      <div>public benchmark score claimed: {String(legalRagBenchmarkAlignment.claim_boundary.public_benchmark_score_claimed)}</div>
                      <div>leaderboard claimed: {String(legalRagBenchmarkAlignment.claim_boundary.leaderboard_claimed)}</div>
                      <div>public benchmark text: {String(legalRagBenchmarkAlignment.privacy_boundary.returns_public_benchmark_text)}</div>
                      <div>raw query: {String(legalRagBenchmarkAlignment.privacy_boundary.returns_raw_query)}</div>
                      <div>raw context: {String(legalRagBenchmarkAlignment.privacy_boundary.returns_retrieved_context)}</div>
                      <div>credentials: {String(legalRagBenchmarkAlignment.privacy_boundary.returns_credentials)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {(legalRagBenchmarkAlignment.validation_commands ?? []).slice(0, 4).map((command) => (
                        <div
                          key={command}
                          className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600"
                        >
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {legalRagHallucinationTriageGate && (
              <section className="mb-8">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-black text-stone-950">Legal RAG hallucination triage gate</h2>
                    <div className="mt-1 text-sm text-stone-600">
                      Metadata-only fixture taxonomy, blocker status, and release actions for Legal RAG hallucination risks
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={statusClass[legalRagHallucinationTriageGate.status] ?? statusClass.review_required}
                  >
                    {displayToken(legalRagHallucinationTriageGate.status)}
                  </Badge>
                </div>

                <div className="mb-3 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                  {[
                    { label: 'fixture cases', value: legalRagHallucinationTriageGate.summary.fixture_case_count },
                    { label: 'taxonomy labels', value: legalRagHallucinationTriageGate.summary.taxonomy_count },
                    { label: 'triage rows', value: legalRagHallucinationTriageGate.summary.triage_row_count },
                    { label: 'blocking rows', value: legalRagHallucinationTriageGate.summary.blocker_row_count },
                    { label: 'citation mismatches', value: legalRagHallucinationTriageGate.summary.citation_mismatch_count },
                    { label: 'retrieval gaps', value: legalRagHallucinationTriageGate.summary.retrieval_gap_count },
                  ].map((item) => (
                    <div key={item.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                      <div className="text-2xl font-black text-stone-950">{formatInline(item.value)}</div>
                      <div className="mt-1 text-sm text-stone-600">{item.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mb-3 grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Fixture/failure taxonomy counts</h3>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {Object.entries(legalRagHallucinationTriageGate.failure_label_counts ?? {}).map(([label, count]) => (
                        <div key={label} className="flex items-center justify-between gap-3 rounded-[8px] border border-stone-950/10 bg-white px-3 py-2 text-sm">
                          <span className="font-mono text-xs text-stone-700">{displayToken(label)}</span>
                          <Badge variant="outline" className="bg-[#fbfaf6]">
                            {count}
                          </Badge>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {['missing_citation', 'stale_regulation', 'jurisdiction_mismatch', 'unsupported_conclusion', 'hallucinated_article', 'conflicting_facts'].map((label) => (
                        <Badge key={label} variant="outline" className="bg-white">
                          {displayToken(label)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Severity/block status</h3>
                    <div className="grid gap-2 sm:grid-cols-3">
                      {Object.entries(legalRagHallucinationTriageGate.severity_counts ?? {}).map(([severity, count]) => (
                        <div key={severity} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                          <Badge variant="outline" className={priorityClass[severity] ?? statusClass.not_run}>
                            {displayToken(severity)}
                          </Badge>
                          <div className="mt-2 text-xl font-black text-stone-950">{count}</div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Badge variant="outline" className={statusClass[legalRagHallucinationTriageGate.summary.authority_gate_status] ?? statusClass.not_run}>
                        authority gate: {displayToken(legalRagHallucinationTriageGate.summary.authority_gate_status)}
                      </Badge>
                      <Badge variant="outline" className={legalRagHallucinationTriageGate.summary.blocker_row_count > 0 ? statusClass.blocked : statusClass.ready}>
                        release blockers: {legalRagHallucinationTriageGate.summary.blocker_row_count}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fixture</TableHead>
                        <TableHead>Failure taxonomy</TableHead>
                        <TableHead>Severity / block</TableHead>
                        <TableHead>Release action</TableHead>
                        <TableHead>Evidence signals</TableHead>
                        <TableHead>Recommended actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(legalRagHallucinationTriageGate.triage_rows ?? []).map((row) => (
                        <TableRow key={row.case_id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.case_id}</div>
                          </TableCell>
                          <TableCell>
                            <div className="flex max-w-[260px] flex-wrap gap-1.5">
                              {row.failure_labels.map((label) => (
                                <Badge key={`${row.case_id}-${label}`} variant="outline" className="bg-white">
                                  {displayToken(label)}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <Badge variant="outline" className={priorityClass[row.severity] ?? statusClass.not_run}>
                              {displayToken(row.severity)}
                            </Badge>
                            <div className="mt-2">blocks release: {String(row.block_release)}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={row.block_release ? statusClass.blocked : statusClass.review_required}>
                              {displayToken(row.release_action)}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            {(row.evidence_signals ?? []).slice(0, 4).map((signal) => (
                              <div key={`${row.case_id}-${signal}`}>{displayToken(signal)}</div>
                            ))}
                          </TableCell>
                          <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                            {(row.reviewer_actions ?? []).slice(0, 3).map((action) => (
                              <div key={`${row.case_id}-${action}`}>{action}</div>
                            ))}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Claim boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>hallucination-free claimed: {String(legalRagHallucinationTriageGate.claim_boundary.hallucination_free_claimed)}</div>
                      <div>legal answer accuracy claimed: {String(legalRagHallucinationTriageGate.claim_boundary.legal_answer_accuracy_claimed)}</div>
                      <div>public benchmark score claimed: {String(legalRagHallucinationTriageGate.claim_boundary.public_benchmark_score_claimed)}</div>
                      <div>live gateway quality claimed: {String(legalRagHallucinationTriageGate.claim_boundary.live_gateway_quality_claimed)}</div>
                      <div>automatic client delivery claimed: {String(legalRagHallucinationTriageGate.claim_boundary.automatic_client_delivery_claimed)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="space-y-2 text-xs leading-5 text-stone-600">
                      <div>metadata-only: {String(legalRagHallucinationTriageGate.privacy_boundary.metadata_only)}</div>
                      <div>user question returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_user_question)}</div>
                      <div>retrieved context returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_retrieved_context)}</div>
                      <div>unsafe answer returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_unsafe_answer)}</div>
                      <div>legal text returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_raw_legal_text)}</div>
                      <div>prompt content returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_prompts)}</div>
                      <div>model output content returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_model_outputs)}</div>
                      <div>credential material returned: {String(legalRagHallucinationTriageGate.privacy_boundary.returns_credentials)}</div>
                    </div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                    <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                    <ul className="space-y-2 text-sm leading-6 text-stone-700">
                      {(legalRagHallucinationTriageGate.recommended_actions ?? []).map((action) => (
                        <li key={action} className="flex gap-2">
                          <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                    <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {(legalRagHallucinationTriageGate.validation_commands ?? []).slice(0, 4).map((command) => (
                        <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {legalRagAbstentionEscalationGate &&
              (() => {
                const gate = legalRagAbstentionEscalationGate;
                const rows = gate.decision_rows ?? [];
                const summary = gate.summary ?? {};
                const decisionCounts = { ...(summary.decision_counts ?? {}), ...(gate.decision_counts ?? {}) };
                const evidenceCounts = {
                  ...(summary.evidence_sufficiency_counts ?? {}),
                  ...(gate.evidence_sufficiency_counts ?? {}),
                };
                const modeOf = (row: (typeof rows)[number]) =>
                  String(row.answer_mode ?? row.decision_mode ?? row.mode ?? row.decision ?? 'unclassified');
                const modeCount = (mode: string) =>
                  Number(
                    decisionCounts[mode] ??
                      summary[`${mode}_count`] ??
                      rows.filter((row) => modeOf(row) === mode).length,
                  );
                const privacy = gate.privacy_boundary ?? {};
                const claim = gate.claim_boundary ?? {};
                const summaryCounts = [
                  { label: 'decision row count', value: summary.decision_row_count ?? summary.row_count ?? rows.length },
                  { label: 'abstain', value: modeCount('abstain') },
                  { label: 'lawyer review', value: modeCount('lawyer_review') },
                  { label: 'premium exception', value: modeCount('premium_exception') },
                  { label: 'cheap-first', value: summary.cheap_first_count ?? summary.cheap_first_route_count ?? 0 },
                  { label: 'blockers', value: summary.blocker_count ?? 0 },
                  { label: 'evidence sufficient', value: summary.evidence_sufficient_count ?? evidenceCounts.sufficient ?? 0 },
                  {
                    label: 'evidence gaps',
                    value: summary.evidence_gap_count ?? summary.evidence_insufficient_count ?? evidenceCounts.insufficient ?? 0,
                  },
                ];

                return (
                  <section className="mb-8">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h2 className="text-xl font-black text-stone-950">Legal RAG abstention escalation gate</h2>
                        <div className="mt-1 text-sm text-stone-600">
                          Metadata-only decision routing, abstention, lawyer review, and premium exception boundary checks
                        </div>
                      </div>
                      <Badge variant="outline" className={statusClass[gate.status] ?? statusClass.review_required}>
                        {displayToken(gate.status)}
                      </Badge>
                    </div>

                    <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
                      {summaryCounts.map((item) => (
                        <div key={item.label} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                          <div className="text-2xl font-black text-stone-950">{formatInline(item.value)}</div>
                          <div className="mt-1 text-sm text-stone-600">{item.label}</div>
                        </div>
                      ))}
                    </div>

                    <div className="grid gap-3 lg:grid-cols-4">
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Decision rows</h3>
                        <div className="space-y-2">
                          {['answer', 'answer_with_warning', 'abstain', 'ask_clarification', 'lawyer_review', 'premium_exception'].map((mode) => (
                            <div key={mode} className="flex items-center justify-between gap-3 rounded-[8px] border border-stone-950/10 bg-white px-3 py-2 text-sm">
                              <span className="font-mono text-xs text-stone-700">{mode}</span>
                              <Badge variant="outline" className="bg-[#fbfaf6]">
                                {modeCount(mode)}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Linkage and routing</h3>
                        <div className="flex flex-wrap gap-2">
                          <Badge
                            variant="outline"
                            className={statusClass[String(summary.authority_citation_gate_status ?? summary.authority_gate_status ?? legalRagAuthorityCitationGate?.status ?? 'not_run')] ?? statusClass.not_run}
                          >
                            authority citation gate: {displayToken(String(summary.authority_citation_gate_status ?? summary.authority_gate_status ?? legalRagAuthorityCitationGate?.status ?? 'not_run'))}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={statusClass[String(summary.hallucination_triage_gate_status ?? summary.hallucination_gate_status ?? legalRagHallucinationTriageGate?.status ?? 'not_run')] ?? statusClass.not_run}
                          >
                            hallucination triage gate: {displayToken(String(summary.hallucination_triage_gate_status ?? summary.hallucination_gate_status ?? legalRagHallucinationTriageGate?.status ?? 'not_run'))}
                          </Badge>
                        </div>
                        <div className="mt-4 space-y-2 text-xs leading-5 text-stone-600">
                          <div>cheap-first route: {String(gate.routing_policy?.cheap_first_route ?? 'metadata-only')}</div>
                          <div>premium exception boundary: {String(gate.routing_policy?.premium_exception_boundary ?? 'lawyer review required')}</div>
                          <div>premium exception allowed: {String(gate.routing_policy?.premium_exception_allowed ?? false)}</div>
                        </div>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Claim/privacy boundary</h3>
                        <div className="space-y-2 text-xs leading-5 text-stone-600">
                          <div>legal advice claimed: {claim.legal_advice_claimed ? 'true / included' : 'false / not included'}</div>
                          <div>accuracy claimed: {claim.legal_answer_accuracy_claimed ? 'true / included' : 'false / not included'}</div>
                          <div>automatic escalation claimed: {claim.automatic_escalation_claimed ? 'true / included' : 'false / not included'}</div>
                          <div>model called: {privacy.model_called ? 'true / included' : 'false / not included'}</div>
                          <div>gateway called: {privacy.gateway_called ? 'true / included' : 'false / not included'}</div>
                          <div>network called: {privacy.network_called ? 'true / included' : 'false / not included'}</div>
                          <div>raw fixture returned: {privacy.returns_raw_fixture || privacy.returns_raw_fixture_payload ? 'true / included' : 'false / not included'}</div>
                          <div>retrieved context returned: {privacy.returns_retrieved_context ? 'true / included' : 'false / not included'}</div>
                          <div>raw legal text returned: {privacy.returns_raw_legal_text ? 'true / included' : 'false / not included'}</div>
                          <div>raw model output returned: {privacy.returns_raw_model_output ? 'true / included' : 'false / not included'}</div>
                          <div>raw gateway payload returned: {privacy.returns_gateway_payload ? 'true / included' : 'false / not included'}</div>
                        </div>
                      </div>
                      <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-5">
                        <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Recommended actions</h3>
                        <ul className="space-y-2 text-sm leading-6 text-stone-700">
                          {(gate.recommended_actions ?? []).slice(0, 5).map((action) => (
                            <li key={action} className="flex gap-2">
                              <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                        <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                        <div className="space-y-2">
                          {(gate.validation_commands ?? []).slice(0, 4).map((command) => (
                            <div
                              key={command}
                              className="break-all rounded-[8px] border border-stone-950/10 bg-white p-2 font-mono text-[11px] text-stone-600"
                            >
                              {command}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>
                );
              })()}

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
                            {signal.evidence_paths.map((path, index) => (
                              <div key={`${signal.id}-${path}-${index}`} className="break-all font-mono text-[11px] text-stone-600">
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
