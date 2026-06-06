import { useEffect, useMemo, useState } from 'react';
import AuthGuard from '@/components/AuthGuard';
import Layout from '@/components/Layout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertTriangle, ClipboardList, Gauge, Loader2, PlayCircle, RefreshCw, Route, Zap } from 'lucide-react';
import {
  evaluateCheapFirstCalibration,
  evaluateGeminiVariantMatrix,
  evaluateModelGatewayProbe,
  evaluateModelOpsCheapFirstCanaryObservation,
  evaluateModelOpsGeminiDefaultChangeReview,
  evaluateModelOpsGeminiDefaultCostImpact,
  evaluateModelOpsObservedGeminiModelIntakeQueue,
  evaluateModelOpsPerformanceBudget,
  getCheapFirstCalibration,
  getGeminiCheapFirstCoverageGate,
  getModelGatewayProbeTemplate,
  getModelOps,
  type ModelCatalogItem,
  type ModelCheapFirstCalibration,
  type GeminiVariantMatrix,
  type ModelOpsGeminiCheapFirstCoverageGate,
  type ModelGatewayHealthPlanRole,
  type ModelGatewayProbeEvaluation,
  type ModelOpsCheapFirstCanaryApprovalPacket,
  type ModelOpsCheapFirstCanaryChangeManifest,
  type ModelOpsCheapFirstCanaryObservation,
  type ModelOpsCheapFirstCanaryPromotionDecision,
  type ModelOpsCheapFirstCanaryRollbackDrill,
  type ModelOpsGeminiDefaultChangeReview,
  type ModelOpsGeminiDefaultCostImpact,
  type ModelOpsObservedGeminiModelIntakeQueue,
  type ModelOpsPerformanceBudget,
  type ModelOpsResponse,
} from '@/lib/modelOpsApi';

const costClass: Record<string, string> = {
  lowest: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  low: 'bg-lime-50 text-lime-800 border-lime-200',
  medium: 'bg-amber-50 text-amber-900 border-amber-200',
  premium: 'bg-red-50 text-red-800 border-red-200',
};

function formatNumber(value?: number) {
  return new Intl.NumberFormat('en-US').format(value ?? 0);
}

function formatUsd(value?: number | null) {
  if (value == null) return 'unpriced';
  return `$${value.toFixed(value < 0.01 ? 6 : 4)}`;
}

function roleText(model: ModelCatalogItem) {
  return model.configured_roles.length ? model.configured_roles.join(', ') : '-';
}

function pricingText(model: ModelCatalogItem) {
  const parts = [
    `in ${formatUsd(model.pricing.input_usd_per_million_tokens)}`,
    `out ${formatUsd(model.pricing.output_usd_per_million_tokens)}`,
  ];
  if (model.pricing.output_usd_per_image != null) {
    parts.push(`image ${formatUsd(model.pricing.output_usd_per_image)}`);
  }
  return parts.join(' / ');
}

function gatewayHealthProbeText(row: ModelGatewayHealthPlanRole) {
  if (row.billing_unit === 'image' && row.output_usd_per_image != null) {
    return `image ${formatUsd(row.output_usd_per_image)}`;
  }
  return formatUsd(row.estimated_probe_cost_usd);
}

function statusClass(status?: string) {
  return status === 'pass'
    || status === 'ready'
    || status === 'approval_ready'
    || status === 'drill_ready'
    || status === 'manifest_ready'
    || status === 'advance_next_batch'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
    : status === 'fail'
      || status === 'blocked'
      || status === 'approval_blocked'
      || status === 'drill_blocked'
      || status === 'manifest_blocked'
      || status === 'rollback_required'
      || status === 'rollback_drill_required'
      || status === 'rollback_review_required'
      ? 'border-red-200 bg-red-50 text-red-800'
      : status === 'not_run' || status === 'not_supplied' || status === 'monitor_only'
        ? 'border-stone-200 bg-white text-stone-700'
        : 'border-amber-200 bg-amber-50 text-amber-900';
}

function boundaryDisplayEntries(value?: Record<string, unknown>) {
  return Object.entries(value ?? {})
    .filter(([key]) => !/(raw|prompt|payload|credential|secret|api[_-]?key|authorization)/i.test(key))
    .slice(0, 4);
}

function defaultCheapFirstCalibrationPayload() {
  return {
    fixture_report: {
      observations: {
        'fixture-service-agreement-small': {
          route: 'review',
          output_text:
            'liability_cap missing_sla termination_cure_period confidentiality_carveout_gap risk_matrix missing_facts replacement_clause cost_route',
        },
        'fixture-lease-dispute-notice-small': {
          route: 'review',
          output_text:
            'deposit_amount repair_notice_dates missing_invoice missing_handover_checklist evidence_tasks pending_facts citations release_decision',
        },
        'fixture-low-text-pdf-page-small': {
          route: 'ocr',
          output_text:
            'low_text_page ocr_confidence_gap version_conflict appendix_reference extraction_quality ocr_pages low_text_pages route_reason',
        },
      },
      run_metadata: {
        'fixture-service-agreement-small': {
          phase: 'cheap_first',
          model: 'gemini-2.5-flash-lite',
          estimated_cost_usd: 0.00009,
        },
        'fixture-lease-dispute-notice-small': {
          phase: 'cheap_first',
          model: 'gemini-2.5-flash-lite',
          estimated_cost_usd: 0.0001,
        },
        'fixture-low-text-pdf-page-small': {
          phase: 'cheap_first',
          model: 'gemini-2.5-flash-lite',
          estimated_cost_usd: 0.00011,
        },
      },
    },
  };
}

function defaultGeminiVariantMatrixPayload() {
  return {
    models_response: {
      object: 'list',
      data: [
        { id: 'models/gemini-2.5-flash-lite', object: 'model' },
        { id: 'google/gemini-2.5-flash', object: 'model' },
        { id: 'models/gemini-3.1-pro', object: 'model' },
        { id: 'yibu/gemini-3.1-flash-image', object: 'model' },
        { id: 'google/gemini-3.2-flash-lite', object: 'model' },
      ],
    },
  };
}

function defaultObservedGeminiModelIntakePayload() {
  return {
    models_response: {
      object: 'list',
      data: [
        { id: 'models/gemini-2.5-flash-lite', object: 'model' },
        { id: 'google/gemini-3.5-flash', object: 'model' },
        { id: 'models/gemini-3.1-pro', object: 'model' },
        { id: 'yibu/gemini-3.1-flash-image', object: 'model' },
        { id: 'newapi/gemini-4.0-flash-lite-preview', object: 'model' },
        { id: 'gemini-3.1-pro-preview', object: 'model' },
      ],
    },
  };
}

function defaultGeminiDefaultChangeReviewPayload() {
  return {
    proposed_changes: [
      {
        task: 'agentic',
        env_var: 'APP_AI_AGENTIC_MODEL',
        current_model: 'gemini-3.1-flash-lite',
        proposed_model: 'gemini-3.1-flash-lite',
        review_note: 'current cheap-first agentic default',
      },
      {
        task: 'grounded-research',
        env_var: 'APP_AI_GROUNDED_RESEARCH_MODEL',
        current_model: 'gemini-3.1-flash-lite',
        proposed_model: 'gemini-3.1-pro-preview',
        review_note: 'maintainer metadata review only',
      },
    ],
  };
}

function defaultGeminiDefaultCostImpactPayload() {
  return {
    proposed_changes: [
      {
        task: 'agentic',
        env_var: 'APP_AI_AGENTIC_MODEL',
        current_model: 'gemini-3.1-flash-lite',
        proposed_model: 'gemini-3.1-flash-lite',
      },
      {
        task: 'grounded-research',
        env_var: 'APP_AI_GROUNDED_RESEARCH_MODEL',
        current_model: 'gemini-3.1-flash-lite',
        proposed_model: 'gemini-3.1-pro-preview',
      },
    ],
  };
}

function defaultPerformanceObservationPayload() {
  return {
    observations: [
      { metric: 'model-ops-first-load', duration_ms: 1800, budget_ms: 2500 },
      { metric: 'model-ops-cache-hit', duration_ms: 420, budget_ms: 750 },
    ],
  };
}

function defaultCanaryObservationPayload() {
  return {
    observations: [
      {
        step_id: 'monitor_existing_default-fast',
        task: 'fast',
        phase: 'monitor_existing_default',
        request_count: 25,
        failure_count: 0,
        over_budget_count: 0,
        premium_request_count: 0,
        unknown_price_model_count: 0,
        operator_review_count: 1,
      },
    ],
  };
}

function hasForbiddenCheapFirstPayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers|email)\b/i.test(
      value,
    )
  );
}

function hasForbiddenGeminiVariantPayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers|email)\b/i.test(
      value,
    )
  );
}

function hasForbiddenObservedGeminiModelIntakePayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers?|email|legal[_ -]?text|payload)\b/i.test(
      value,
    )
  );
}

function hasForbiddenPerformancePayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers|email|legal[_ -]?text)\b/i.test(
      value,
    )
  );
}

function hasForbiddenCanaryObservationPayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers?|email|legal[_ -]?text|client[_ -]?email)\b/i.test(
      value,
    )
  );
}

function hasForbiddenGeminiDefaultChangePayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers?|email|legal[_ -]?text|payload)\b/i.test(
      value,
    )
  );
}

function hasForbiddenGeminiDefaultCostPayloadText(value: string) {
  return (
    /\bsk-[A-Za-z0-9]{20,}\b/.test(value) ||
    /\b(api[_-]?key|authorization|password|secret|raw[_ -]?model[_ -]?output|raw[_ -]?prompt|prompt|headers?|email|legal[_ -]?text|payload)\b/i.test(
      value,
    )
  );
}

export default function ModelOpsPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const [data, setData] = useState<ModelOpsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [probePayloadText, setProbePayloadText] = useState('');
  const [probeEvaluation, setProbeEvaluation] = useState<ModelGatewayProbeEvaluation | null>(null);
  const [probeLoading, setProbeLoading] = useState(false);
  const [probeTemplateLoading, setProbeTemplateLoading] = useState(false);
  const [probeError, setProbeError] = useState('');
  const [cheapFirstCalibration, setCheapFirstCalibration] = useState<ModelCheapFirstCalibration | null>(null);
  const [cheapFirstPayloadText, setCheapFirstPayloadText] = useState('');
  const [cheapFirstEvaluateLoading, setCheapFirstEvaluateLoading] = useState(false);
  const [cheapFirstError, setCheapFirstError] = useState('');
  const [geminiVariantMatrix, setGeminiVariantMatrix] = useState<GeminiVariantMatrix | null>(null);
  const [geminiVariantPayloadText, setGeminiVariantPayloadText] = useState('');
  const [geminiVariantEvaluateLoading, setGeminiVariantEvaluateLoading] = useState(false);
  const [geminiVariantError, setGeminiVariantError] = useState('');
  const [observedGeminiModelIntakeQueue, setObservedGeminiModelIntakeQueue] =
    useState<ModelOpsObservedGeminiModelIntakeQueue | null>(null);
  const [observedGeminiModelIntakePayloadText, setObservedGeminiModelIntakePayloadText] = useState('');
  const [observedGeminiModelIntakeLoading, setObservedGeminiModelIntakeLoading] = useState(false);
  const [observedGeminiModelIntakeError, setObservedGeminiModelIntakeError] = useState('');
  const [geminiCheapFirstCoverageGate, setGeminiCheapFirstCoverageGate] =
    useState<ModelOpsGeminiCheapFirstCoverageGate | null>(null);
  const [geminiCheapFirstCoverageGateError, setGeminiCheapFirstCoverageGateError] = useState('');
  const [performanceBudget, setPerformanceBudget] = useState<ModelOpsPerformanceBudget | null>(null);
  const [performancePayloadText, setPerformancePayloadText] = useState('');
  const [performanceEvaluateLoading, setPerformanceEvaluateLoading] = useState(false);
  const [performanceError, setPerformanceError] = useState('');
  const [geminiDefaultChangeReview, setGeminiDefaultChangeReview] = useState<ModelOpsGeminiDefaultChangeReview | null>(null);
  const [geminiDefaultChangePayloadText, setGeminiDefaultChangePayloadText] = useState('');
  const [geminiDefaultChangeLoading, setGeminiDefaultChangeLoading] = useState(false);
  const [geminiDefaultChangeError, setGeminiDefaultChangeError] = useState('');
  const [geminiDefaultCostImpact, setGeminiDefaultCostImpact] = useState<ModelOpsGeminiDefaultCostImpact | null>(null);
  const [geminiDefaultCostPayloadText, setGeminiDefaultCostPayloadText] = useState('');
  const [geminiDefaultCostLoading, setGeminiDefaultCostLoading] = useState(false);
  const [geminiDefaultCostError, setGeminiDefaultCostError] = useState('');
  const [canaryObservation, setCanaryObservation] = useState<ModelOpsCheapFirstCanaryObservation | null>(null);
  const [canaryPromotionDecision, setCanaryPromotionDecision] = useState<ModelOpsCheapFirstCanaryPromotionDecision | null>(null);
  const [canaryApprovalPacket, setCanaryApprovalPacket] = useState<ModelOpsCheapFirstCanaryApprovalPacket | null>(null);
  const [canaryRollbackDrill, setCanaryRollbackDrill] = useState<ModelOpsCheapFirstCanaryRollbackDrill | null>(null);
  const [canaryChangeManifest, setCanaryChangeManifest] = useState<ModelOpsCheapFirstCanaryChangeManifest | null>(null);
  const [canaryObservationPayloadText, setCanaryObservationPayloadText] = useState('');
  const [canaryObservationLoading, setCanaryObservationLoading] = useState(false);
  const [canaryObservationError, setCanaryObservationError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    setCheapFirstError('');
    setCheapFirstCalibration(null);
    setGeminiVariantError('');
    setGeminiVariantMatrix(null);
    setObservedGeminiModelIntakeError('');
    setObservedGeminiModelIntakeQueue(null);
    setGeminiCheapFirstCoverageGateError('');
    setGeminiCheapFirstCoverageGate(null);
    setPerformanceError('');
    setPerformanceBudget(null);
    setGeminiDefaultChangeError('');
    setGeminiDefaultChangeReview(null);
    setGeminiDefaultCostError('');
    setGeminiDefaultCostImpact(null);
    setCanaryObservationError('');
    setCanaryObservation(null);
    setCanaryPromotionDecision(null);
    setCanaryApprovalPacket(null);
    setCanaryRollbackDrill(null);
    setCanaryChangeManifest(null);
    try {
      const [modelOpsResult, geminiCheapFirstCoverageGateResult] = await Promise.allSettled([
        getModelOps(),
        getGeminiCheapFirstCoverageGate(),
      ]);
      if (modelOpsResult.status === 'rejected') {
        console.error(modelOpsResult.reason);
        setError('Model telemetry failed to load.');
        setData(null);
      } else {
        setData(modelOpsResult.value);
        setProbeEvaluation(null);
        setPerformanceBudget(null);
        setCanaryObservation(null);
        setCanaryPromotionDecision(null);
        setCanaryApprovalPacket(null);
        setCanaryRollbackDrill(null);
        setCanaryChangeManifest(null);
        setGeminiDefaultChangeReview(modelOpsResult.value.gemini_default_change_review ?? null);
        setGeminiDefaultCostImpact(modelOpsResult.value.gemini_default_cost_impact ?? null);
        setGeminiVariantMatrix(modelOpsResult.value.gemini_variant_matrix ?? null);
        setObservedGeminiModelIntakeQueue(modelOpsResult.value.observed_gemini_model_intake_queue ?? null);
        if (geminiCheapFirstCoverageGateResult.status === 'fulfilled') {
          setGeminiCheapFirstCoverageGate(geminiCheapFirstCoverageGateResult.value);
        } else {
          console.error(geminiCheapFirstCoverageGateResult.reason);
          setGeminiCheapFirstCoverageGate(modelOpsResult.value.gemini_cheap_first_coverage_gate ?? null);
          if (!modelOpsResult.value.gemini_cheap_first_coverage_gate) {
            setGeminiCheapFirstCoverageGateError('Gemini cheap-first coverage gate failed to load.');
          }
        }
        if (modelOpsResult.value.cheap_first_calibration) {
          setCheapFirstCalibration(modelOpsResult.value.cheap_first_calibration);
        } else {
          try {
            setCheapFirstCalibration(await getCheapFirstCalibration());
          } catch (calibrationError) {
            console.error(calibrationError);
            setCheapFirstError('Cheap-first calibration failed to load.');
          }
        }
      }
      if (modelOpsResult.status === 'rejected' && geminiCheapFirstCoverageGateResult.status === 'fulfilled') {
        setGeminiCheapFirstCoverageGate(geminiCheapFirstCoverageGateResult.value);
      }
      if (modelOpsResult.status === 'rejected' && geminiCheapFirstCoverageGateResult.status === 'rejected') {
        console.error(geminiCheapFirstCoverageGateResult.reason);
        setGeminiCheapFirstCoverageGateError('Gemini cheap-first coverage gate failed to load.');
      }
    } catch (err) {
      console.error(err);
      setError('Model telemetry failed to load.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const loadProbeTemplate = async () => {
    setProbeTemplateLoading(true);
    setProbeError('');
    try {
      const template = await getModelGatewayProbeTemplate();
      setProbePayloadText(JSON.stringify(template.payload_shape, null, 2));
    } catch (err) {
      console.error(err);
      setProbeError('Gateway probe template failed to load.');
    } finally {
      setProbeTemplateLoading(false);
    }
  };

  const evaluateProbePayload = async () => {
    setProbeLoading(true);
    setProbeError('');
    try {
      const payload = probePayloadText.trim() ? JSON.parse(probePayloadText) : {};
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setProbeError('Probe payload must be a JSON object.');
        return;
      }
      const evaluation = await evaluateModelGatewayProbe(payload as Record<string, unknown>);
      setProbeEvaluation(evaluation);
      await load();
    } catch (err) {
      console.error(err);
      setProbeError(err instanceof SyntaxError ? 'Probe payload is not valid JSON.' : 'Gateway probe evaluation failed.');
    } finally {
      setProbeLoading(false);
    }
  };

  const loadCheapFirstTemplate = () => {
    setCheapFirstError('');
    setCheapFirstPayloadText(JSON.stringify(defaultCheapFirstCalibrationPayload(), null, 2));
  };

  const evaluateCheapFirstPayload = async () => {
    setCheapFirstEvaluateLoading(true);
    setCheapFirstError('');
    try {
      const text = cheapFirstPayloadText.trim();
      if (!text) {
        setCheapFirstError('Calibration payload is empty.');
        return;
      }
      if (hasForbiddenCheapFirstPayloadText(text)) {
        setCheapFirstError('Calibration payload must not include secrets, headers, prompts, emails, passwords, or raw model output.');
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setCheapFirstError('Calibration payload must be a JSON object.');
        return;
      }
      setCheapFirstCalibration(await evaluateCheapFirstCalibration(payload as Record<string, unknown>));
    } catch (err) {
      console.error(err);
      setCheapFirstError(err instanceof SyntaxError ? 'Calibration payload is not valid JSON.' : 'Cheap-first calibration evaluation failed.');
    } finally {
      setCheapFirstEvaluateLoading(false);
    }
  };

  const loadGeminiVariantTemplate = () => {
    setGeminiVariantError('');
    setGeminiVariantPayloadText(JSON.stringify(defaultGeminiVariantMatrixPayload(), null, 2));
  };

  const evaluateGeminiVariantPayload = async () => {
    setGeminiVariantEvaluateLoading(true);
    setGeminiVariantError('');
    try {
      const text = geminiVariantPayloadText.trim();
      if (!text) {
        setGeminiVariantError('Observed model payload is empty.');
        return;
      }
      if (hasForbiddenGeminiVariantPayloadText(text)) {
        setGeminiVariantError('Observed model payload must not include secrets, headers, prompts, emails, passwords, or raw model output.');
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setGeminiVariantError('Observed model payload must be a JSON object.');
        return;
      }
      setGeminiVariantMatrix(await evaluateGeminiVariantMatrix(payload as Record<string, unknown>));
    } catch (err) {
      console.error(err);
      setGeminiVariantError(err instanceof SyntaxError ? 'Observed model payload is not valid JSON.' : 'Gemini variant review failed.');
    } finally {
      setGeminiVariantEvaluateLoading(false);
    }
  };

  const loadObservedGeminiModelIntakeTemplate = () => {
    setObservedGeminiModelIntakeError('');
    setObservedGeminiModelIntakePayloadText(JSON.stringify(defaultObservedGeminiModelIntakePayload(), null, 2));
  };

  const evaluateObservedGeminiModelIntakePayload = async () => {
    setObservedGeminiModelIntakeLoading(true);
    setObservedGeminiModelIntakeError('');
    try {
      const text = observedGeminiModelIntakePayloadText.trim();
      if (!text) {
        setObservedGeminiModelIntakeError('Observed Gemini intake payload is empty.');
        return;
      }
      if (hasForbiddenObservedGeminiModelIntakePayloadText(text)) {
        setObservedGeminiModelIntakeError(
          'Observed Gemini intake payload must not include keys, headers, prompts, raw payloads, emails, raw output, or legal text.',
        );
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setObservedGeminiModelIntakeError('Observed Gemini intake payload must be a JSON object.');
        return;
      }
      setObservedGeminiModelIntakeQueue(
        await evaluateModelOpsObservedGeminiModelIntakeQueue(payload as Record<string, unknown>),
      );
    } catch (err) {
      console.error(err);
      setObservedGeminiModelIntakeError(
        err instanceof SyntaxError
          ? 'Observed Gemini intake payload is not valid JSON.'
          : 'Observed Gemini model intake review failed.',
      );
    } finally {
      setObservedGeminiModelIntakeLoading(false);
    }
  };

  const loadPerformanceTemplate = () => {
    setPerformancePayloadText(JSON.stringify(defaultPerformanceObservationPayload(), null, 2));
    setPerformanceError('');
  };

  const evaluatePerformancePayload = async () => {
    setPerformanceEvaluateLoading(true);
    setPerformanceError('');
    try {
      if (hasForbiddenPerformancePayloadText(performancePayloadText)) {
        setPerformanceError('Performance payload must not include keys, headers, prompts, emails, raw output, or legal text.');
        return;
      }
      const payload = performancePayloadText.trim() ? JSON.parse(performancePayloadText) : {};
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setPerformanceError('Performance payload must be a JSON object.');
        return;
      }
      const result = await evaluateModelOpsPerformanceBudget(payload as Record<string, unknown>);
      setPerformanceBudget(result);
    } catch (err) {
      console.error(err);
      setPerformanceError('Performance observations failed to evaluate.');
    } finally {
      setPerformanceEvaluateLoading(false);
    }
  };

  const loadGeminiDefaultChangeTemplate = () => {
    setGeminiDefaultChangePayloadText(JSON.stringify(defaultGeminiDefaultChangeReviewPayload(), null, 2));
    setGeminiDefaultChangeError('');
  };

  const evaluateGeminiDefaultChangePayload = async () => {
    setGeminiDefaultChangeLoading(true);
    setGeminiDefaultChangeError('');
    try {
      const text = geminiDefaultChangePayloadText.trim();
      if (!text) {
        setGeminiDefaultChangeError('Default change proposal payload is empty.');
        return;
      }
      if (hasForbiddenGeminiDefaultChangePayloadText(text)) {
        setGeminiDefaultChangeError('Default change proposal must not include keys, headers, prompts, raw payloads, emails, raw output, or legal text.');
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setGeminiDefaultChangeError('Default change proposal must be a JSON object.');
        return;
      }
      setGeminiDefaultChangeReview(await evaluateModelOpsGeminiDefaultChangeReview(payload as Record<string, unknown>));
    } catch (err) {
      console.error(err);
      setGeminiDefaultChangeError(
        err instanceof SyntaxError ? 'Default change proposal is not valid JSON.' : 'Gemini default change review failed.',
      );
    } finally {
      setGeminiDefaultChangeLoading(false);
    }
  };

  const loadGeminiDefaultCostTemplate = () => {
    setGeminiDefaultCostPayloadText(JSON.stringify(defaultGeminiDefaultCostImpactPayload(), null, 2));
    setGeminiDefaultCostError('');
  };

  const evaluateGeminiDefaultCostPayload = async () => {
    setGeminiDefaultCostLoading(true);
    setGeminiDefaultCostError('');
    try {
      const text = geminiDefaultCostPayloadText.trim();
      if (!text) {
        setGeminiDefaultCostError('Default cost impact payload is empty.');
        return;
      }
      if (hasForbiddenGeminiDefaultCostPayloadText(text)) {
        setGeminiDefaultCostError('Default cost impact payload must not include keys, headers, prompts, raw payloads, emails, raw output, or legal text.');
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setGeminiDefaultCostError('Default cost impact payload must be a JSON object.');
        return;
      }
      setGeminiDefaultCostImpact(await evaluateModelOpsGeminiDefaultCostImpact(payload as Record<string, unknown>));
    } catch (err) {
      console.error(err);
      setGeminiDefaultCostError(
        err instanceof SyntaxError ? 'Default cost impact payload is not valid JSON.' : 'Gemini default cost impact failed.',
      );
    } finally {
      setGeminiDefaultCostLoading(false);
    }
  };

  const loadCanaryObservationTemplate = () => {
    setCanaryObservationPayloadText(JSON.stringify(defaultCanaryObservationPayload(), null, 2));
    setCanaryObservationError('');
  };

  const evaluateCanaryObservationPayload = async () => {
    setCanaryObservationLoading(true);
    setCanaryObservationError('');
    try {
      const text = canaryObservationPayloadText.trim();
      if (!text) {
        setCanaryObservationError('Canary observation payload is empty.');
        return;
      }
      if (hasForbiddenCanaryObservationPayloadText(text)) {
        setCanaryObservationError('Canary observation payload must not include keys, headers, prompts, emails, raw output, or legal text.');
        return;
      }
      const payload = JSON.parse(text);
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
        setCanaryObservationError('Canary observation payload must be a JSON object.');
        return;
      }
      const result = await evaluateModelOpsCheapFirstCanaryObservation(payload as Record<string, unknown>);
      setCanaryObservation(result);
      setCanaryPromotionDecision(result.promotion_decision ?? null);
      setCanaryApprovalPacket(result.approval_packet ?? null);
      setCanaryRollbackDrill(result.rollback_drill ?? null);
      setCanaryChangeManifest(result.change_manifest ?? null);
    } catch (err) {
      console.error(err);
      setCanaryObservationError(
        err instanceof SyntaxError ? 'Canary observation payload is not valid JSON.' : 'Canary observation review failed.',
      );
    } finally {
      setCanaryObservationLoading(false);
    }
  };

  const aliases = useMemo(() => Object.entries(data?.routing_aliases ?? {}), [data]);
  const usageRows = useMemo(() => Object.entries(data?.usage.models ?? {}), [data]);
  const readinessRows = data?.model_ops_readiness?.checks ?? [];
  const cheapFirstDecisionChecks = data?.cheap_first_release_decision?.checks ?? [];
  const defaultChangeQueueRows = data?.default_change_queue?.queue_items ?? [];
  const activeGeminiDefaultChangeReview = geminiDefaultChangeReview ?? data?.gemini_default_change_review ?? null;
  const geminiDefaultChangeRows = activeGeminiDefaultChangeReview?.proposal_rows ?? [];
  const activeGeminiDefaultCostImpact = geminiDefaultCostImpact ?? data?.gemini_default_cost_impact ?? null;
  const geminiDefaultCostRows = activeGeminiDefaultCostImpact?.impact_rows ?? [];
  const cheapFirstCanarySteps = data?.cheap_first_canary_plan?.canary_steps ?? [];
  const cheapFirstCanaryTriggers = data?.cheap_first_canary_plan?.rollback_triggers ?? [];
  const activeCanaryObservation = canaryObservation ?? data?.cheap_first_canary_observation ?? null;
  const canaryObservationRows = activeCanaryObservation?.observation_rows ?? [];
  const activeCanaryPromotionDecision =
    canaryPromotionDecision
    ?? activeCanaryObservation?.promotion_decision
    ?? data?.cheap_first_canary_promotion_decision
    ?? null;
  const canaryPromotionRows = activeCanaryPromotionDecision?.promotion_items ?? [];
  const activeCanaryApprovalPacket =
    canaryApprovalPacket
    ?? activeCanaryObservation?.approval_packet
    ?? data?.cheap_first_canary_approval_packet
    ?? null;
  const canaryApprovalRows = activeCanaryApprovalPacket?.approval_items ?? [];
  const activeCanaryRollbackDrill =
    canaryRollbackDrill
    ?? activeCanaryObservation?.rollback_drill
    ?? data?.cheap_first_canary_rollback_drill
    ?? null;
  const canaryRollbackDrillRows = activeCanaryRollbackDrill?.rollback_drill_items ?? [];
  const activeCanaryChangeManifest =
    canaryChangeManifest
    ?? activeCanaryObservation?.change_manifest
    ?? data?.cheap_first_canary_change_manifest
    ?? null;
  const canaryChangeManifestRows = activeCanaryChangeManifest?.change_manifest_items ?? [];
  const activePerformanceBudget = performanceBudget ?? data?.model_ops_performance_budget ?? null;
  const modelOpsPerformanceRows = activePerformanceBudget?.checks ?? [];
  const routeQualityRows = data?.route_quality_budget?.task_quality_budgets ?? [];
  const runtimeRouterFields = useMemo(() => Object.entries(data?.runtime_router?.request_fields ?? {}), [data]);
  const runtimeDefaults = data?.runtime_router?.task_defaults ?? [];
  const configurationAuditRows = data?.model_configuration_audit?.checks ?? [];
  const defaultTemplateRows = data?.default_template_audit?.rows ?? [];
  const defaultOptimizationRows = data?.default_optimization?.recommendations ?? [];
  const gatewayCompatibilityRows = data?.gateway_compatibility?.configured_roles ?? [];
  const gatewayExampleRows = data?.gateway_compatibility?.gateway_examples ?? [];
  const activeGeminiVariantMatrix = geminiVariantMatrix ?? data?.gemini_variant_matrix ?? null;
  const geminiVariantRows = activeGeminiVariantMatrix?.model_rows ?? [];
  const geminiVariantFamilyRows = activeGeminiVariantMatrix?.family_rows ?? [];
  const geminiVariantObservedRows = activeGeminiVariantMatrix?.observed_model_reviews ?? [];
  const geminiVariantExtraction = activeGeminiVariantMatrix?.source_summaries?.observed_model_extraction;
  const activeObservedGeminiModelIntakeQueue =
    observedGeminiModelIntakeQueue ?? data?.observed_gemini_model_intake_queue ?? null;
  const observedGeminiModelIntakeRows = activeObservedGeminiModelIntakeQueue?.queue_items ?? [];
  const activeGeminiCheapFirstCoverageGate =
    geminiCheapFirstCoverageGate ?? data?.gemini_cheap_first_coverage_gate ?? null;
  const geminiCheapFirstCoverageRows = activeGeminiCheapFirstCoverageGate?.coverage_rows ?? [];
  const geminiCheapFirstCoverageClaimBoundaryEntries = boundaryDisplayEntries(
    activeGeminiCheapFirstCoverageGate?.claim_boundary,
  );
  const catalogSourceRows = data?.catalog_source_audit?.catalog_rows ?? [];
  const catalogSourceChecks = data?.catalog_source_audit?.checks ?? [];
  const catalogSourceDefaultRows = data?.catalog_source_audit?.high_frequency_defaults ?? [];
  const catalogCandidatePatchPlan = data?.catalog_candidate_patch_plan ?? null;
  const catalogCandidatePatchRows = catalogCandidatePatchPlan?.candidate_patch_rows ?? [];
  const catalogCandidatePatchChecks = catalogCandidatePatchPlan?.checks ?? [];
  const catalogCandidateClaimBoundaryEntries = boundaryDisplayEntries(catalogCandidatePatchPlan?.claim_boundary);
  const gatewayHealthRows = data?.gateway_health_plan?.role_models ?? [];
  const gatewayHealthContracts = data?.gateway_health_plan?.dry_run_contracts ?? [];
  const activeProbeEvaluation = probeEvaluation ?? data?.gateway_probe_evaluation ?? null;
  const probeEnvRows = activeProbeEvaluation?.recommended_env ?? [];
  const probeCheckRows = activeProbeEvaluation?.checks ?? [];
  const probeModelRows = activeProbeEvaluation?.model_rows ?? [];
  const activeCheapFirstCalibration = cheapFirstCalibration ?? data?.cheap_first_calibration ?? null;
  const cheapFirstRows = activeCheapFirstCalibration?.calibration_rows ?? [];
  const cheapFirstResearchRows = activeCheapFirstCalibration?.external_research_mappings ?? [];
  const priceRefreshChecks = data?.price_refresh_monitor?.checks ?? [];
  const priceRefreshSignals = data?.price_refresh_monitor?.drift_signals ?? [];
  const lifecycleRows = data?.lifecycle_policy?.configured_roles ?? [];
  const taskInferenceRules = data?.runtime_router?.auto_task_inference?.rules ?? [];
  const reasoningRows = data?.reasoning_policy?.task_defaults ?? [];
  const requestPolicyRows = data?.request_policy?.task_defaults ?? [];
  const requestCostBoundRows = data?.request_cost_bounds?.task_bounds ?? [];
  const cachePolicyRows = data?.cache_policy?.rules ?? [];
  const routeTelemetryRows = useMemo(() => Object.entries(data?.route_telemetry?.by_task ?? {}), [data]);
  const routeTelemetryRepositoryRows = data?.route_telemetry_repository?.daily_buckets ?? [];
  const routeTelemetryOpsRows = data?.route_telemetry_ops_summary?.daily_rows ?? [];
  const routeTelemetryTriageRows = data?.route_telemetry_triage?.triage_items ?? [];
  const routeTelemetryRemediationRows = data?.route_telemetry_remediation?.remediation_steps ?? [];
  const routeTelemetryRemediationEnvRows = data?.route_telemetry_remediation?.recommended_env ?? [];
  const routeGuardrailRows = data?.route_guardrails?.checks ?? [];
  const callsiteRows = data?.callsite_audit?.callsites ?? [];
  const budgetRows = data?.budget_policy.task_decisions ?? [];
  const capabilityRows = data?.capability_matrix?.tasks ?? [];
  const escalationRows = data?.escalation_policy?.plans ?? [];
  const fallbackChainRows = data?.fallback_chains?.chains ?? [];
  const routingReplayRows = data?.routing_replay?.scenarios ?? [];
  const forecastRows = data?.cost_forecast?.profiles ?? [];
  const guardrailRows = data?.cost_guardrails?.checks ?? [];
  const totals = data?.usage.totals;

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-stone-950/15 pb-6">
          <div>
            <div className="eyebrow mb-3">Model Ops</div>
            <h1 className="text-4xl font-black leading-none text-stone-950 sm:text-6xl">AI Model Routing</h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600">
              Runtime routing, model catalog, and aggregate usage counters for cost-aware legal review.
            </p>
          </div>
          <Button variant="outline" className="soft-button" onClick={load} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </Button>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Route className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{aliases.length}</div>
              <div className="mt-1 text-sm text-stone-600">routing aliases</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Zap className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{data?.models.length ?? 0}</div>
              <div className="mt-1 text-sm text-stone-600">catalog models</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatNumber(totals?.requests)}</div>
              <div className="mt-1 text-sm text-stone-600">requests recorded</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatNumber(totals?.total_tokens)}</div>
              <div className="mt-1 text-sm text-stone-600">tokens recorded</div>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] bg-stone-950 text-white">
                <Gauge className="h-5 w-5" />
              </div>
              <div className="text-3xl font-black text-stone-950">{formatUsd(totals?.estimated_cost_usd)}</div>
              <div className="mt-1 text-sm text-stone-600">estimated cost</div>
            </CardContent>
          </Card>
        </div>

        {data?.model_ops_readiness && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Model ops readiness</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.model_ops_readiness.summary.required_component_count} required /{' '}
                  {data.model_ops_readiness.summary.optional_component_count} optional /{' '}
                  {data.model_ops_readiness.summary.blocking_count} blocking /{' '}
                  {data.model_ops_readiness.summary.warning_count} warning
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.model_ops_readiness.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.model_ops_readiness.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.model_ops_readiness.release_recommendation.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.model_ops_readiness.summary.pass_count}</div>
                <div className="mt-1 text-sm text-stone-600">passing</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.model_ops_readiness.summary.required_warning_count}</div>
                <div className="mt-1 text-sm text-stone-600">required warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.model_ops_readiness.summary.optional_review_count}</div>
                <div className="mt-1 text-sm text-stone-600">optional review</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.model_ops_readiness.summary.required_failure_count}</div>
                <div className="mt-1 text-sm text-stone-600">required failures</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.model_ops_readiness.blocking_check_ids.length}</div>
                <div className="mt-1 text-sm text-stone-600">blocking ids</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Component</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {readinessRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{check.label}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{check.source_key}</div>
                        <div className="mt-1 text-[11px] text-stone-500">
                          {check.required ? 'required gate' : 'optional evidence'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{check.category}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.cheap_first_release_decision && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.cheap_first_release_decision.release_decision.label} /{' '}
                  {data.cheap_first_release_decision.summary.attached_signal_count} of{' '}
                  {data.cheap_first_release_decision.summary.required_signal_count} signals attached
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.cheap_first_release_decision.status)}>
                {data.cheap_first_release_decision.release_decision.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_release_decision.summary.passing_signal_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">passing signals</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_release_decision.summary.warning_signal_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">review signals</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_release_decision.summary.blocking_signal_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking signals</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_release_decision.summary.current_cheap_first_default_allowed ? 'yes' : 'no'}
                </div>
                <div className="mt-1 text-sm text-stone-600">current default allowed</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_release_decision.summary.default_change_allowed ? 'yes' : 'review'}
                </div>
                <div className="mt-1 text-sm text-stone-600">default change allowed</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.cheap_first_release_decision.summary.raw_payload_echoed)}
                </div>
                <div className="mt-1 text-sm text-stone-600">raw payload echoed</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-3">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Promotion policy</div>
                <div className="mt-2 text-sm leading-6 text-stone-700">
                  {data.cheap_first_release_decision.promotion_policy.default_change_policy}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-500">
                  default_promotion_blocked: {String(data.cheap_first_release_decision.summary.default_promotion_blocked)} /{' '}
                  maintainer_review_required: {String(data.cheap_first_release_decision.summary.maintainer_review_required)}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Privacy boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  gateway called: {String(data.cheap_first_release_decision.privacy_boundary.network_called)} / NewAPI called:{' '}
                  {String(data.cheap_first_release_decision.summary.newapi_called)} / raw model output:{' '}
                  {String(data.cheap_first_release_decision.privacy_boundary.raw_model_output_included)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {data.cheap_first_release_decision.recommended_actions.slice(0, 2).join(' ')}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Claim boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  public benchmark scores:{' '}
                  {String(data.cheap_first_release_decision.claim_boundary.public_benchmark_scores_included)} / 24h
                  complete:{' '}
                  {String(data.cheap_first_release_decision.claim_boundary.twenty_four_hour_completion_claimed)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  live gateway:{' '}
                  {String(data.cheap_first_release_decision.claim_boundary.live_gateway_execution_claimed)} / external
                  adoption:{' '}
                  {String(data.cheap_first_release_decision.claim_boundary.external_adoption_included)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Signal</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Decision effect</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cheapFirstDecisionChecks.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{check.id}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{check.source_key}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(check.status)}>
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{check.decision_effect}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.default_change_queue && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Default change queue</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.default_change_queue.summary.change_request_count} changes /{' '}
                  {data.default_change_queue.summary.review_required_count} reviews /{' '}
                  {data.default_change_queue.summary.blocked_change_count} blocked
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.default_change_queue.status)}>
                {data.default_change_queue.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_change_queue.summary.queue_item_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">queue items</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_change_queue.summary.ready_change_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">ready changes</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_change_queue.summary.review_required_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">review required</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_change_queue.summary.blocked_change_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocked changes</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.default_change_queue.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.default_change_queue.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-sm font-black uppercase text-stone-500">Queue boundary</div>
              <div className="mt-2 text-xs leading-5 text-stone-600">
                automatic default change:{' '}
                {String(data.default_change_queue.claim_boundary.automatic_default_change_claimed)} / public benchmark
                scores: {String(data.default_change_queue.claim_boundary.public_benchmark_scores_included)} / raw model
                output: {String(data.default_change_queue.privacy_boundary.raw_model_output_included)}
              </div>
              <div className="mt-2 text-xs leading-5 text-stone-600">
                {data.default_change_queue.recommended_actions.slice(0, 2).join(' ')}
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Models</TableHead>
                    <TableHead>Review</TableHead>
                    <TableHead>Reason codes</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {defaultChangeQueueRows.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{item.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{item.env_var ?? 'explicit'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(item.queue_status)}>
                          {item.queue_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        current {item.current_model || '-'}
                        <br />
                        recommended {item.recommended_model || '-'}
                      </TableCell>
                      <TableCell>
                        {item.requires_change ? 'change' : 'no change'}
                        <div className="mt-1 text-[11px] text-stone-500">
                          operator review: {String(item.requires_operator_review)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {item.reason_codes.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {item.action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeGeminiDefaultChangeReview && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini default change review</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeGeminiDefaultChangeReview.summary.proposal_count} proposals /{' '}
                  {activeGeminiDefaultChangeReview.summary.review_required_count} reviews /{' '}
                  {activeGeminiDefaultChangeReview.summary.blocked_count} blocked
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeGeminiDefaultChangeReview.status)}>
                {activeGeminiDefaultChangeReview.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultChangeReview.summary.ready_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">ready proposals</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultChangeReview.summary.cheap_first_regression_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first regressions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultChangeReview.summary.premium_exception_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">premium exceptions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeGeminiDefaultChangeReview.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeGeminiDefaultChangeReview.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeGeminiDefaultChangeReview.summary.raw_payload_echoed)}
                </div>
                <div className="mt-1 text-sm text-stone-600">raw payload echoed</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-stone-950">Sanitized default proposal evaluator</div>
                    <div className="mt-1 text-xs leading-5 text-stone-600">
                      Reviews proposed Gemini defaults before .env/template edits; no gateway call and no configuration write.
                    </div>
                  </div>
                  <Button type="button" variant="outline" size="sm" onClick={loadGeminiDefaultChangeTemplate}>
                    <ClipboardList className="mr-2 h-4 w-4" /> Template
                  </Button>
                </div>
                <Textarea
                  value={geminiDefaultChangePayloadText}
                  onChange={(event) => setGeminiDefaultChangePayloadText(event.target.value)}
                  placeholder='{"proposed_changes":[{"task":"agentic","env_var":"APP_AI_AGENTIC_MODEL","current_model":"gemini-3.1-flash-lite","proposed_model":"gemini-3.1-flash-lite"}]}'
                  className="min-h-[180px] border-stone-950/15 bg-white font-mono text-xs"
                />
                {geminiDefaultChangeError && (
                  <div className="mt-2 rounded-[6px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                    {geminiDefaultChangeError}
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={evaluateGeminiDefaultChangePayload}
                    disabled={geminiDefaultChangeLoading}
                  >
                    {geminiDefaultChangeLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-2 h-4 w-4" />}
                    Evaluate proposal
                  </Button>
                  <div className="text-xs text-stone-600">
                    blocked fields: prompt, payload, key, authorization, email, legal text, raw output
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Review boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  automatic default change:{' '}
                  {String(activeGeminiDefaultChangeReview.claim_boundary.automatic_default_change_claimed)} / live gateway:{' '}
                  {String(activeGeminiDefaultChangeReview.claim_boundary.live_gateway_execution_claimed)} / production quality:{' '}
                  {String(activeGeminiDefaultChangeReview.claim_boundary.production_quality_claimed)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {activeGeminiDefaultChangeReview.recommended_actions.slice(0, 2).join(' ')}
                </div>
                <div className="mt-3 grid gap-2">
                  {activeGeminiDefaultChangeReview.validation_commands.slice(0, 2).map((command) => (
                    <div key={command} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 font-mono text-xs leading-5 text-stone-600">
                      {command}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Models</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Capabilities</TableHead>
                    <TableHead>Reason codes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {geminiDefaultChangeRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.env_var}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.review_status)}>
                          {row.review_status}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.release_action}</div>
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        current {row.current_model || '-'}
                        <br />
                        proposed {row.proposed_model || '-'}
                        <br />
                        recommended {row.recommended_model || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.proposed_cost_tier] ?? 'bg-white'}>
                          {row.proposed_cost_tier}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          max {row.max_cost_tier} / premium: {String(row.premium_exception)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.missing_required_capabilities.length
                          ? `missing ${row.missing_required_capabilities.join(', ')}`
                          : row.required_capabilities.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                        {row.reason_codes.join(', ') || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeGeminiDefaultCostImpact && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini default cost impact</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeGeminiDefaultCostImpact.summary.proposal_count} proposals /{' '}
                  {activeGeminiDefaultCostImpact.summary.review_required_count} reviews /{' '}
                  {activeGeminiDefaultCostImpact.summary.blocked_count} blocked
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeGeminiDefaultCostImpact.status)}>
                {activeGeminiDefaultCostImpact.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(activeGeminiDefaultCostImpact.summary.estimated_monthly_delta_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">monthly delta</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultCostImpact.summary.cost_increase_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cost increases</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultCostImpact.summary.cost_decrease_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cost decreases</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiDefaultCostImpact.summary.unknown_price_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown prices</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeGeminiDefaultCostImpact.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeGeminiDefaultCostImpact.summary.raw_payload_echoed)}
                </div>
                <div className="mt-1 text-sm text-stone-600">raw payload echoed</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-stone-950">Sanitized cost impact evaluator</div>
                    <div className="mt-1 text-xs leading-5 text-stone-600">
                      Estimates default-change monthly cost before promotion; no gateway call and no configuration write.
                    </div>
                  </div>
                  <Button type="button" variant="outline" size="sm" onClick={loadGeminiDefaultCostTemplate}>
                    <ClipboardList className="mr-2 h-4 w-4" /> Template
                  </Button>
                </div>
                <Textarea
                  value={geminiDefaultCostPayloadText}
                  onChange={(event) => setGeminiDefaultCostPayloadText(event.target.value)}
                  placeholder='{"proposed_changes":[{"task":"grounded-research","env_var":"APP_AI_GROUNDED_RESEARCH_MODEL","current_model":"gemini-3.1-flash-lite","proposed_model":"gemini-3.1-pro-preview"}]}'
                  className="min-h-[180px] border-stone-950/15 bg-white font-mono text-xs"
                />
                {geminiDefaultCostError && (
                  <div className="mt-2 rounded-[6px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                    {geminiDefaultCostError}
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={evaluateGeminiDefaultCostPayload}
                    disabled={geminiDefaultCostLoading}
                  >
                    {geminiDefaultCostLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-2 h-4 w-4" />}
                    Evaluate cost impact
                  </Button>
                  <div className="text-xs text-stone-600">
                    blocked fields: prompt, payload, key, authorization, email, legal text, raw output
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Cost boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  billing_accuracy_claimed:{' '}
                  {String(activeGeminiDefaultCostImpact.claim_boundary.billing_accuracy_claimed)} / production savings:{' '}
                  {String(activeGeminiDefaultCostImpact.claim_boundary.production_savings_claimed)} / network:{' '}
                  {String(activeGeminiDefaultCostImpact.privacy_boundary.network_called)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {activeGeminiDefaultCostImpact.recommended_actions.slice(0, 2).join(' ')}
                </div>
                <div className="mt-3 grid gap-2">
                  {activeGeminiDefaultCostImpact.validation_commands.slice(0, 2).map((command) => (
                    <div key={command} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 font-mono text-xs leading-5 text-stone-600">
                      {command}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Models</TableHead>
                    <TableHead>Unit cost</TableHead>
                    <TableHead>monthly delta</TableHead>
                    <TableHead>Reason codes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {geminiDefaultCostRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.env_var}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.impact_status)}>
                          {row.impact_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.release_action}</div>
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        current {row.current_model || '-'}
                        <br />
                        proposed {row.proposed_model || '-'}
                        <br />
                        units {formatNumber(row.profile.monthly_units)}
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        current {formatUsd(row.current_unit_cost_usd)}
                        <br />
                        proposed {formatUsd(row.proposed_unit_cost_usd)}
                        <br />
                        tier {row.current_cost_tier} -&gt; {row.proposed_cost_tier}
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        monthly delta {formatUsd(row.monthly_delta_usd)}
                        <br />
                        estimated savings delta {formatUsd(row.estimated_savings_delta_usd)}
                        <br />
                        premium: {String(row.premium_exception)}
                      </TableCell>
                      <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                        {row.reason_codes.join(', ') || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.cheap_first_canary_plan && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary plan</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.cheap_first_canary_plan.summary.canary_required_count} queued canaries /{' '}
                  {data.cheap_first_canary_plan.summary.review_required_step_count} review steps /{' '}
                  {data.cheap_first_canary_plan.summary.blocked_step_count} blocked
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.cheap_first_canary_plan.status)}>
                {data.cheap_first_canary_plan.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_canary_plan.summary.canary_step_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">canary steps</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_canary_plan.rollout_policy.batch_percentages.join('% / ')}%
                </div>
                <div className="mt-1 text-sm text-stone-600">batch plan</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cheap_first_canary_plan.summary.rollback_trigger_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">rollback triggers</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.cheap_first_canary_plan.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.cheap_first_canary_plan.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(data.cheap_first_canary_plan.summary.traffic_shifted)}
                </div>
                <div className="mt-1 text-sm text-stone-600">traffic shifted</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-2">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Rollout policy</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  observation window: {data.cheap_first_canary_plan.rollout_policy.minimum_observation_window_hours}h /
                  holdout required: {String(data.cheap_first_canary_plan.rollout_policy.holdout_required_until_final_review)} /
                  operator approval: {String(data.cheap_first_canary_plan.rollout_policy.operator_approval_required)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {data.cheap_first_canary_plan.recommended_actions.slice(0, 2).join(' ')}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Rollback triggers</div>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {cheapFirstCanaryTriggers.map((trigger) => (
                    <div key={trigger.id} className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                      <div className="font-mono text-[11px] text-stone-500">{trigger.metric}</div>
                      <div className="text-sm font-black text-stone-950">{trigger.threshold}</div>
                      <div className="mt-1 text-xs leading-5 text-stone-600">{trigger.action}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Phase</TableHead>
                    <TableHead>Batch</TableHead>
                    <TableHead>Models</TableHead>
                    <TableHead>Rollback</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cheapFirstCanarySteps.map((step) => (
                    <TableRow key={step.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{step.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{step.env_var ?? 'explicit'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(step.step_status)}>
                          {step.step_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{step.phase}</div>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        batch {step.batch_percentage}% / holdout {step.holdout_percentage}%
                        <div className="mt-1 text-[11px] text-stone-500">
                          observe {step.observation_window_hours}h / config change:{' '}
                          {String(step.requires_configuration_change)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        current {step.current_model || '-'}
                        <br />
                        recommended {step.recommended_model || '-'}
                      </TableCell>
                      <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                        {step.rollback_trigger_ids.join(', ')}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {step.action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3 text-xs leading-5 text-stone-500">
              production traffic shifted:{' '}
              {String(data.cheap_first_canary_plan.claim_boundary.production_traffic_shifted)} / automatic canary rollout:{' '}
              {String(data.cheap_first_canary_plan.claim_boundary.automatic_canary_rollout_claimed)} / raw model output:{' '}
              {String(data.cheap_first_canary_plan.privacy_boundary.raw_model_output_included)}
            </div>
          </section>
        )}

        {activeCanaryObservation && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary observation review</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCanaryObservation.summary.observation_count} observations /{' '}
                  {activeCanaryObservation.summary.failing_observation_count} failing /{' '}
                  {activeCanaryObservation.summary.warning_observation_count} review
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCanaryObservation.status)}>
                {activeCanaryObservation.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryObservation.summary.total_request_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">observed requests</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeCanaryObservation.summary.matched_step_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">matched steps</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeCanaryObservation.summary.forbidden_payload_field_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocked payload fields</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryObservation.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryObservation.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryObservation.summary.traffic_shifted)}
                </div>
                <div className="mt-1 text-sm text-stone-600">traffic shifted</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-black uppercase text-stone-500">Canary observations</h3>
                    <div className="mt-1 text-xs text-stone-600">Aggregate counts only; no headers, keys, prompts, raw output, or legal text.</div>
                  </div>
                  <Button variant="outline" className="soft-button" onClick={loadCanaryObservationTemplate}>
                    <ClipboardList className="h-4 w-4" />
                    Template
                  </Button>
                </div>
                <Textarea
                  value={canaryObservationPayloadText}
                  onChange={(event) => setCanaryObservationPayloadText(event.target.value)}
                  className="min-h-[180px] font-mono text-xs"
                  placeholder='{"observations":[{"step_id":"monitor_existing_default-fast","request_count":25}]}'
                />
                {canaryObservationError && (
                  <div className="mt-2 text-xs font-semibold text-red-700">{canaryObservationError}</div>
                )}
                <Button
                  className="mt-3 soft-button"
                  onClick={evaluateCanaryObservationPayload}
                  disabled={canaryObservationLoading}
                >
                  {canaryObservationLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                  Evaluate canary observations
                </Button>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Thresholds</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {Object.entries(activeCanaryObservation.thresholds).map(([key, value]) => (
                    <div key={key} className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                      <div className="font-mono text-[11px] text-stone-500">{key}</div>
                      <div className="text-sm font-black text-stone-950">{value}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  {activeCanaryObservation.recommended_actions.slice(0, 2).join(' ')}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-500">
                  production traffic shifted:{' '}
                  {String(activeCanaryObservation.claim_boundary.production_traffic_shifted)} / automatic rollout:{' '}
                  {String(activeCanaryObservation.claim_boundary.automatic_canary_rollout_claimed)} / raw payload echoed:{' '}
                  {String(activeCanaryObservation.summary.raw_payload_echoed)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Step</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>Rates</TableHead>
                    <TableHead>Reason codes</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {canaryObservationRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.step_id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.status)}>
                          {row.status}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">mapped: {String(row.source_step_found)}</div>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        requests {formatNumber(row.request_count)}
                        <br />
                        failures {formatNumber(row.failure_count)} / review {formatNumber(row.operator_review_count)}
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        fail {Math.round(row.failure_rate * 100)}% / over budget{' '}
                        {Math.round(row.over_budget_route_ratio * 100)}%
                        <br />
                        premium {Math.round(row.premium_request_ratio * 100)}% / review{' '}
                        {Math.round(row.operator_review_route_ratio * 100)}%
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.reason_codes.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {row.action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeCanaryPromotionDecision && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary promotion decision</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCanaryPromotionDecision.summary.advance_decision_count} advance /{' '}
                  {activeCanaryPromotionDecision.summary.hold_decision_count} hold /{' '}
                  {activeCanaryPromotionDecision.summary.rollback_decision_count} rollback
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCanaryPromotionDecision.status)}>
                {activeCanaryPromotionDecision.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryPromotionDecision.summary.decision_item_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">promotion items</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryPromotionDecision.summary.monitor_only_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">monitor only</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryPromotionDecision.summary.not_ready_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">not ready</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryPromotionDecision.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryPromotionDecision.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryPromotionDecision.summary.traffic_shifted)}
                </div>
                <div className="mt-1 text-sm text-stone-600">traffic shifted</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Decision policy</div>
                <div className="mt-3 text-lg font-black text-stone-950">{activeCanaryPromotionDecision.decision.label}</div>
                <div className="mt-2 font-mono text-xs text-stone-600">
                  default_action: {activeCanaryPromotionDecision.decision.default_action}
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">configuration_change_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryPromotionDecision.decision.configuration_change_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">traffic_shift_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryPromotionDecision.decision.traffic_shift_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">maintainer review</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryPromotionDecision.decision.requires_maintainer_approval)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Promotion summary</div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  source plan: {activeCanaryPromotionDecision.summary.source_plan_status} / source observation:{' '}
                  {activeCanaryPromotionDecision.summary.source_observation_status} / observations:{' '}
                  {formatNumber(activeCanaryPromotionDecision.summary.observation_count)}
                </div>
                <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                  statuses: advance_next_batch / hold_for_review / rollback_required
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  {activeCanaryPromotionDecision.recommended_actions.slice(0, 3).join(' ')}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-500">
                  production traffic shifted:{' '}
                  {String(activeCanaryPromotionDecision.claim_boundary.production_traffic_shifted)} / automatic rollout:{' '}
                  {String(activeCanaryPromotionDecision.claim_boundary.automatic_canary_rollout_claimed)} / public benchmark scores:{' '}
                  {String(activeCanaryPromotionDecision.claim_boundary.public_benchmark_scores_included)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Decision</TableHead>
                    <TableHead>Batch</TableHead>
                    <TableHead>Observations</TableHead>
                    <TableHead>Reason codes</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {canaryPromotionRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_step_id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.promotion_status)}>
                          {row.promotion_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">step: {row.step_status.replace(/_/g, ' ')}</div>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        batch {row.batch_percentage}% / holdout {row.holdout_percentage}%
                        <br />
                        phase {row.phase}
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        {formatNumber(row.matched_observation_count)} matched
                        <br />
                        {row.observation_statuses.join(', ') || 'none'}
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.reason_codes.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {row.action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeCanaryApprovalPacket && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary approval packet</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCanaryApprovalPacket.summary.ready_for_approval_count} ready /{' '}
                  {activeCanaryApprovalPacket.summary.blocked_approval_count} blocked /{' '}
                  {activeCanaryApprovalPacket.summary.rollback_review_count} rollback review
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCanaryApprovalPacket.status)}>
                {activeCanaryApprovalPacket.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryApprovalPacket.summary.approval_item_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">approval items</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryApprovalPacket.summary.required_signoff_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">required signoffs</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryApprovalPacket.summary.approved_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">approved count</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryApprovalPacket.summary.approval_record_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">approval record written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryApprovalPacket.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryApprovalPacket.summary.traffic_shifted)}
                </div>
                <div className="mt-1 text-sm text-stone-600">traffic shifted</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Approval policy</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">approval_required</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryApprovalPacket.approval_policy.approval_required)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">approval_record_written</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryApprovalPacket.approval_policy.approval_record_written)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">configuration_change_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryApprovalPacket.approval_policy.configuration_change_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">traffic_shift_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryApprovalPacket.approval_policy.traffic_shift_allowed)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Approval summary</div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  source promotion: {activeCanaryApprovalPacket.summary.source_promotion_status} / monitor:{' '}
                  {activeCanaryApprovalPacket.summary.monitor_only_count} / source not ready:{' '}
                  {activeCanaryApprovalPacket.summary.source_not_ready_count}
                </div>
                <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                  statuses: approval_ready / approval_blocked / rollback_review_required
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  {activeCanaryApprovalPacket.recommended_actions.slice(0, 3).join(' ')}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-500">
                  maintainer approval claimed:{' '}
                  {String(activeCanaryApprovalPacket.claim_boundary.maintainer_approval_claimed)} / approver identity:{' '}
                  {String(activeCanaryApprovalPacket.privacy_boundary.approver_identity_included)} / automatic rollout:{' '}
                  {String(activeCanaryApprovalPacket.claim_boundary.automatic_canary_rollout_claimed)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Approval</TableHead>
                    <TableHead>Signoffs</TableHead>
                    <TableHead>Checks</TableHead>
                    <TableHead>Blocking reasons</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {canaryApprovalRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_step_id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.approval_status)}>
                          {row.approval_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          promotion: {row.promotion_status.replace(/_/g, ' ')}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                        {row.required_signoffs.join(', ') || 'none'}
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        {row.pre_approval_checks.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.blocking_reason_codes.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {row.action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeCanaryRollbackDrill && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary rollback drill</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCanaryRollbackDrill.summary.ready_drill_count} ready /{' '}
                  {activeCanaryRollbackDrill.summary.blocked_drill_count} blocked /{' '}
                  {activeCanaryRollbackDrill.summary.rollback_required_count} rollback required
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCanaryRollbackDrill.status)}>
                {activeCanaryRollbackDrill.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryRollbackDrill.summary.drill_item_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">drill items</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryRollbackDrill.summary.monitor_only_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">monitor only</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryRollbackDrill.summary.drill_record_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">drill record written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryRollbackDrill.summary.rollback_executed)}
                </div>
                <div className="mt-1 text-sm text-stone-600">rollback executed</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryRollbackDrill.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryRollbackDrill.summary.traffic_shifted)}
                </div>
                <div className="mt-1 text-sm text-stone-600">traffic shifted</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">rollback_drill_policy</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">rollback_execution_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.rollback_execution_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">configuration_change_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.configuration_change_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">traffic_shift_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.traffic_shift_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">requires_trigger_review</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.requires_trigger_review)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">requires_holdout_confirmation</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.requires_holdout_confirmation)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">drill_required_before_approval</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryRollbackDrill.rollback_drill_policy.drill_required_before_approval)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Rollback drill boundary</div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  source approval: {activeCanaryRollbackDrill.summary.source_approval_status} / source promotion:{' '}
                  {activeCanaryRollbackDrill.summary.source_promotion_status}
                </div>
                <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                  statuses: drill_ready / drill_blocked / rollback_drill_required
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  {activeCanaryRollbackDrill.recommended_actions.slice(0, 3).join(' ')}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-500">
                  rollback executed: {String(activeCanaryRollbackDrill.claim_boundary.rollback_executed)} / network called:{' '}
                  {String(activeCanaryRollbackDrill.privacy_boundary.network_called)} / drill record written:{' '}
                  {String(activeCanaryRollbackDrill.privacy_boundary.drill_record_written)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Drill</TableHead>
                    <TableHead>Triggers</TableHead>
                    <TableHead>Roles</TableHead>
                    <TableHead>Rehearsal steps</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {canaryRollbackDrillRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_step_id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.drill_status)}>
                          {row.drill_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          trigger_review_status: {row.trigger_review_status.replace(/_/g, ' ')}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                        {row.rollback_trigger_ids.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                        {row.required_roles.join(', ') || 'none'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {row.rehearsal_steps.slice(0, 3).join(' ')}
                      </TableCell>
                      <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">
                        <div>{row.action}</div>
                        <div className="mt-2 font-mono text-[11px] text-stone-500">
                          rollback_executed:{String(row.rollback_executed)} / traffic_shifted:{String(row.traffic_shifted)}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeCanaryChangeManifest && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first canary change manifest</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCanaryChangeManifest.summary.ready_change_count} ready /{' '}
                  {activeCanaryChangeManifest.summary.blocked_change_count} blocked /{' '}
                  {activeCanaryChangeManifest.summary.rollback_review_count} rollback review
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCanaryChangeManifest.status)}>
                {activeCanaryChangeManifest.status.replace(/_/g, ' ')}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryChangeManifest.summary.manifest_item_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">change_manifest_items</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activeCanaryChangeManifest.summary.rollback_review_count)}
                </div>
                <div className="mt-1 text-sm text-stone-600">rollback review</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryChangeManifest.summary.change_applied)}
                </div>
                <div className="mt-1 text-sm text-stone-600">change_applied</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryChangeManifest.summary.env_file_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">env_file_written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryChangeManifest.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway_called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeCanaryChangeManifest.summary.secret_value_included)}
                </div>
                <div className="mt-1 text-sm text-stone-600">secret_value_included</div>
              </div>
            </div>
            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">change_manifest_policy</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">external_execution_required</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.external_execution_required)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">configuration_write_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.configuration_write_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">env_file_write_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.env_file_write_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">traffic_shift_allowed</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.traffic_shift_allowed)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">requires_maintainer_approval</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.requires_maintainer_approval)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">requires_rollback_drill_ready</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.requires_rollback_drill_ready)}
                    </div>
                  </div>
                  <div className="rounded-[6px] border border-stone-950/10 bg-white p-3">
                    <div className="font-mono text-[11px] text-stone-500">includes_secret_values</div>
                    <div className="text-sm font-black text-stone-950">
                      {String(activeCanaryChangeManifest.change_manifest_policy.includes_secret_values)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Manifest boundary</div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  source rollback drill: {activeCanaryChangeManifest.summary.source_rollback_drill_status} / source
                  approval: {activeCanaryChangeManifest.summary.source_approval_status ?? 'not supplied'}
                </div>
                <div className="mt-2 font-mono text-[11px] leading-5 text-stone-500">
                  statuses: manifest_ready / manifest_blocked / rollback_review_required
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-600">
                  {activeCanaryChangeManifest.recommended_actions.slice(0, 3).join(' ')}
                </div>
                <div className="mt-3 text-xs leading-5 text-stone-500">
                  change_applied: {String(activeCanaryChangeManifest.summary.change_applied)} / secret_value_included:{' '}
                  {String(activeCanaryChangeManifest.summary.secret_value_included)} / manifest_record_written:{' '}
                  {String(activeCanaryChangeManifest.summary.manifest_record_written)}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Manifest</TableHead>
                    <TableHead>Change set</TableHead>
                    <TableHead>Prerequisites</TableHead>
                    <TableHead>Operator steps</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {canaryChangeManifestRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_step_id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.manifest_status)}>
                          {row.manifest_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          drill_status: {row.drill_status.replace(/_/g, ' ')}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        <div className="font-mono text-[11px] text-stone-700">{row.env_var ?? 'explicit model request'}</div>
                        <div className="mt-1">
                          from {row.external_change_set.from_model || '-'}
                          <br />
                          to {row.external_change_set.to_model || '-'}
                          <br />
                          apply_mode {row.external_change_set.apply_mode}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.prerequisites.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                        {row.operator_steps.slice(0, 3).join(' ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        <div>{row.action}</div>
                        <div className="mt-2 font-mono text-[11px] text-stone-500">
                          change_applied:{String(row.change_applied)} / secret_value_included:
                          {String(row.external_change_set.secret_value_included)}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activePerformanceBudget && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">ModelOps load guard</h2>
                <div className="mt-1 text-sm text-stone-600">
                  timeout {formatNumber(activePerformanceBudget.summary.frontend_total_timeout_ms)}ms / cache{' '}
                  {activePerformanceBudget.summary.backend_cache_ttl_seconds}s / fetch first{' '}
                  {activePerformanceBudget.summary.same_origin_fetch_first ? 'on' : 'off'} /{' '}
                  {activePerformanceBudget.summary.slow_observation_count} slow observations
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activePerformanceBudget.status)}>
                {activePerformanceBudget.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activePerformanceBudget.summary.first_load_budget_ms)}ms
                </div>
                <div className="mt-1 text-sm text-stone-600">first load budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatNumber(activePerformanceBudget.summary.cache_hit_budget_ms)}ms
                </div>
                <div className="mt-1 text-sm text-stone-600">cache-hit budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activePerformanceBudget.summary.models_payload_cache_enabled ? 'on' : 'off'}
                </div>
                <div className="mt-1 text-sm text-stone-600">backend cache</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activePerformanceBudget.summary.same_origin_fetch_first ? 'on' : 'off'}
                </div>
                <div className="mt-1 text-sm text-stone-600">same-origin fetch first</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activePerformanceBudget.summary.fallback_after_timeout_disabled ? 'off' : 'review'}
                </div>
                <div className="mt-1 text-sm text-stone-600">timeout fallback</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activePerformanceBudget.summary.duplicate_calibration_fetch_removed ? 'removed' : 'review'}
                </div>
                <div className="mt-1 text-sm text-stone-600">duplicate calibration fetch</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modelOpsPerformanceRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-mono text-xs text-stone-700">{row.id}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.status)}>
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[620px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3 text-xs leading-5 text-stone-500">
              raw payload echoed: {String(activePerformanceBudget.privacy_boundary.raw_payload_echoed)} / raw model output:{' '}
              {String(activePerformanceBudget.privacy_boundary.raw_model_output_included)}
            </div>
            <div className="mt-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-black uppercase text-stone-500">Performance observations</h3>
                    <div className="mt-1 text-xs text-stone-600">Numeric timing rows only; no headers, keys, prompts, or legal text.</div>
                  </div>
                  <Button variant="outline" className="soft-button" onClick={loadPerformanceTemplate}>
                    <ClipboardList className="h-4 w-4" />
                    Template
                  </Button>
                </div>
                {performanceError && (
                  <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                    <AlertTriangle className="h-4 w-4" />
                    {performanceError}
                  </div>
                )}
                <Textarea
                  value={performancePayloadText}
                  onChange={(event) => setPerformancePayloadText(event.target.value)}
                  placeholder='{"observations":[{"metric":"model-ops-first-load","duration_ms":1800,"budget_ms":2500}]}'
                  className="min-h-[130px] font-mono text-xs"
                />
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    className="law-button"
                    onClick={evaluatePerformancePayload}
                    disabled={performanceEvaluateLoading}
                  >
                    {performanceEvaluateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                    Evaluate observations
                  </Button>
                  <Button
                    variant="outline"
                    className="soft-button"
                    onClick={() => {
                      setPerformancePayloadText('');
                      setPerformanceError('');
                      setPerformanceBudget(null);
                    }}
                  >
                    Reset
                  </Button>
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Observation review</h3>
                <div className="mb-3 grid grid-cols-3 gap-2">
                  <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                    <div className="text-xl font-black text-stone-950">{activePerformanceBudget.summary.observation_count}</div>
                    <div className="mt-1 text-[11px] text-stone-500">observations</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                    <div className="text-xl font-black text-stone-950">{activePerformanceBudget.summary.slow_observation_count}</div>
                    <div className="mt-1 text-[11px] text-stone-500">slow</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                    <div className="text-xl font-black text-stone-950">
                      {activePerformanceBudget.summary.slow_observation_failure_threshold}
                    </div>
                    <div className="mt-1 text-[11px] text-stone-500">fail threshold</div>
                  </div>
                </div>
                <div className="space-y-2">
                  {activePerformanceBudget.observations.map((row) => (
                    <div key={`${row.metric}-${row.duration_ms}`} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-mono text-xs text-stone-950">{row.metric}</div>
                        <Badge variant="outline" className={row.within_budget ? statusClass('pass') : statusClass('warn')}>
                          {row.within_budget ? 'within budget' : 'slow'}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-stone-600">
                        {formatNumber(row.duration_ms)}ms / budget {formatNumber(row.budget_ms ?? 0)}ms
                      </div>
                    </div>
                  ))}
                  {activePerformanceBudget.observations.length === 0 && (
                    <div className="rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs text-stone-600">
                      Submit a sanitized observation payload to review first-load and cache-hit timings.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {data?.route_quality_budget && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first quality budget</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_quality_budget.summary.cheap_start_task_count} cheap-start tasks /{' '}
                  {data.route_quality_budget.summary.quality_gate_count} quality gates /{' '}
                  {data.route_quality_budget.summary.runtime_default_gap_count} default gaps
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.route_quality_budget.status)}>
                {data.route_quality_budget.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_quality_budget.summary.task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">task budgets</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_quality_budget.summary.premium_exception_task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">premium exceptions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_quality_budget.summary.warning_check_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">quality warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_quality_budget.summary.blocking_check_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">quality blockers</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Cheap start</TableHead>
                    <TableHead>Runtime default</TableHead>
                    <TableHead>Quality gates</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeQualityRows.map((row) => (
                    <TableRow key={row.task}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.display_name}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{row.cheap_start_model}</div>
                        <div className="mt-1 text-[11px] text-stone-500">max {row.max_cost_tier}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{row.runtime_default_model}</div>
                        <div className="mt-1 text-[11px] text-stone-500">
                          {row.runtime_default_has_required_capabilities ? 'capable' : 'capability review'} /{' '}
                          {row.runtime_default_cost_tier}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-semibold text-stone-950">
                          {row.quality_score}/{row.quality_floor}
                        </div>
                        <div className="mt-1 max-w-[260px] text-[11px] leading-4 text-stone-500">
                          {row.quality_gate_ids.join(', ')}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                        {row.review_action.replace(/_/g, ' ')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3 text-xs leading-5 text-stone-500">
              raw payload echoed: {String(data.route_quality_budget.privacy_boundary.raw_payload_echoed)} / raw model output:{' '}
              {String(data.route_quality_budget.privacy_boundary.raw_model_output_included)}
            </div>
          </section>
        )}

        {data?.default_optimization && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Default optimization</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.default_optimization.summary.aligned_count} aligned /{' '}
                  {data.default_optimization.summary.change_count} changes / saves{' '}
                  {formatUsd(data.default_optimization.summary.estimated_monthly_savings_usd)}
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.default_optimization.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.default_optimization.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.default_optimization.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_optimization.summary.task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">task defaults</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_optimization.summary.change_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">env changes</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.default_optimization.summary.manual_review_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">manual-review defaults</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.default_optimization.summary.estimated_monthly_savings_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">estimated monthly savings</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Default</TableHead>
                    <TableHead>Recommendation</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {defaultOptimizationRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.display_name}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        <span className="font-mono">{row.current_model}</span>
                        <br />
                        {row.env_var ?? row.source}
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        <span className="font-mono">{row.recommended_model}</span>
                        <br />
                        {row.requires_change ? 'update default' : row.source}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.recommended_cost_tier || ''] ?? 'bg-white'}>
                          {row.recommended_cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          save {formatUsd(row.estimated_monthly_savings_usd)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.gateway_compatibility && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gateway compatibility</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.gateway_compatibility.summary.known_configured_count} known /{' '}
                  {data.gateway_compatibility.summary.prefixed_configured_count} prefixed /{' '}
                  {data.gateway_compatibility.summary.unknown_gemini_count} unknown Gemini
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.gateway_compatibility.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.gateway_compatibility.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.gateway_compatibility.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_compatibility.summary.configured_role_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">configured roles</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_compatibility.summary.example_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">prefix examples</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_compatibility.summary.warning_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_compatibility.summary.blocking_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking checks</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Configured model</TableHead>
                    <TableHead>Canonical</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gatewayCompatibilityRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.label}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.env_var}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[260px] font-mono text-xs text-stone-700">{row.model}</TableCell>
                      <TableCell className="max-w-[240px] font-mono text-xs text-stone-700">
                        {row.canonical_model ?? '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          {row.cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">max {row.max_cost_tier}</div>
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Gateway example</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Canonical</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gatewayExampleRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-mono text-xs text-stone-700">{row.model}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.canonical_model ?? '-'}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeObservedGeminiModelIntakeQueue && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Observed Gemini model intake queue</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeObservedGeminiModelIntakeQueue.summary.observed_model_count} observed /{' '}
                  {activeObservedGeminiModelIntakeQueue.summary.ready_count} ready /{' '}
                  {activeObservedGeminiModelIntakeQueue.summary.review_required_count} reviews /{' '}
                  {activeObservedGeminiModelIntakeQueue.summary.blocked_count} blocked
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeObservedGeminiModelIntakeQueue.status)}>
                {activeObservedGeminiModelIntakeQueue.status.replace(/_/g, ' ')}
              </Badge>
            </div>

            <div className="mb-3 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeObservedGeminiModelIntakeQueue.summary.cheap_first_candidate_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first candidates</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeObservedGeminiModelIntakeQueue.summary.unknown_gemini_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown Gemini ids</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeObservedGeminiModelIntakeQueue.summary.external_non_gemini_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">external non-Gemini</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeObservedGeminiModelIntakeQueue.summary.gateway_called)}
                </div>
                <div className="mt-1 text-sm text-stone-600">gateway called</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeObservedGeminiModelIntakeQueue.summary.configuration_written)}
                </div>
                <div className="mt-1 text-sm text-stone-600">configuration written</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {String(activeObservedGeminiModelIntakeQueue.summary.raw_payload_echoed)}
                </div>
                <div className="mt-1 text-sm text-stone-600">raw payload echoed</div>
              </div>
            </div>

            <div className="mb-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-stone-950">Sanitized observed model evaluator</div>
                    <div className="mt-1 text-xs leading-5 text-stone-600">
                      Converts gateway model ids into an intake queue before any default model promotion.
                    </div>
                  </div>
                  <Button type="button" variant="outline" size="sm" onClick={loadObservedGeminiModelIntakeTemplate}>
                    <ClipboardList className="mr-2 h-4 w-4" /> Template
                  </Button>
                </div>
                <Textarea
                  value={observedGeminiModelIntakePayloadText}
                  onChange={(event) => setObservedGeminiModelIntakePayloadText(event.target.value)}
                  placeholder='{"models_response":{"data":[{"id":"models/gemini-2.5-flash-lite"},{"id":"yibu/gemini-3.1-flash-image"},{"id":"newapi/gemini-4.0-flash-lite-preview"}]}}'
                  className="min-h-[160px] border-stone-950/15 bg-white font-mono text-xs"
                />
                {observedGeminiModelIntakeError && (
                  <div className="mt-2 rounded-[6px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                    {observedGeminiModelIntakeError}
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={evaluateObservedGeminiModelIntakePayload}
                    disabled={observedGeminiModelIntakeLoading}
                  >
                    {observedGeminiModelIntakeLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-2 h-4 w-4" />}
                    Evaluate intake queue
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setObservedGeminiModelIntakePayloadText('');
                      setObservedGeminiModelIntakeError('');
                      setObservedGeminiModelIntakeQueue(data?.observed_gemini_model_intake_queue ?? null);
                    }}
                  >
                    Reset
                  </Button>
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-sm font-black uppercase text-stone-500">Intake boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  automatic_default_change_claimed:{' '}
                  {String(activeObservedGeminiModelIntakeQueue.claim_boundary.automatic_default_change_claimed)} / network:{' '}
                  {String(activeObservedGeminiModelIntakeQueue.privacy_boundary.network_called)} / raw output:{' '}
                  {String(activeObservedGeminiModelIntakeQueue.privacy_boundary.raw_model_output_included)}
                </div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {activeObservedGeminiModelIntakeQueue.recommended_actions.slice(0, 2).join(' ')}
                </div>
                <div className="mt-3 grid gap-2">
                  {activeObservedGeminiModelIntakeQueue.validation_commands.slice(0, 2).map((command) => (
                    <div key={command} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 font-mono text-xs leading-5 text-stone-600">
                      {command}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Observed model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Release action</TableHead>
                    <TableHead>Reason codes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {observedGeminiModelIntakeRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">{row.raw_model}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.canonical_model ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.intake_status)}>
                          {row.intake_status.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.intake_action}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier] ?? 'bg-white'}>
                          {row.cost_tier}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">
                          cheap_first_default_candidate: {String(row.cheap_first_default_candidate)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.release_action}
                        <br />
                        tasks {row.allowed_default_tasks.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                        {row.reason_codes.join(', ') || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {activeGeminiVariantMatrix && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini variant matrix</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeGeminiVariantMatrix.summary.catalog_model_count} variants /{' '}
                  {activeGeminiVariantMatrix.summary.high_frequency_default_allowed_count} high-frequency defaults /{' '}
                  {activeGeminiVariantMatrix.summary.catalog_review_count} catalog reviews
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeGeminiVariantMatrix.status)}>
                {activeGeminiVariantMatrix.status.replace(/_/g, ' ')}
              </Badge>
            </div>

            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="font-mono text-sm font-black text-stone-950">
                  {activeGeminiVariantMatrix.summary.cheap_first_default_model}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first default</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiVariantMatrix.summary.explicit_only_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">explicit / escalation models</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiVariantMatrix.summary.preview_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">preview variants</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiVariantMatrix.summary.unpriced_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unpriced variants</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {activeGeminiVariantMatrix.warning_check_ids.length}
                </div>
                <div className="mt-1 text-sm text-stone-600">warning checks</div>
              </div>
            </div>

            <div className="mb-3 grid gap-3 lg:grid-cols-[1fr_1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Family</TableHead>
                      <TableHead>Models</TableHead>
                      <TableHead>Default posture</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {geminiVariantFamilyRows.map((row) => (
                      <TableRow key={row.family}>
                        <TableCell>
                          <div className="font-semibold text-stone-950">{row.family}</div>
                          <div className="mt-1 font-mono text-[11px] text-stone-500">
                            {row.catalog_patterns.join(', ')}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-2xl font-black text-stone-950">{row.catalog_model_count}</div>
                          <div className="mt-1 text-xs leading-5 text-stone-600">{row.catalog_models.join(', ') || '-'}</div>
                        </TableCell>
                        <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">
                          <Badge
                            variant="outline"
                            className={row.high_frequency_default_allowed ? statusClass('pass') : statusClass('warn')}
                          >
                            {row.high_frequency_default_allowed ? 'high-frequency allowed' : 'explicit or escalation'}
                          </Badge>
                          <div className="mt-2">{row.default_use}</div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Prefix compatibility</h3>
                <div className="space-y-2 text-xs leading-5 text-stone-600">
                  {activeGeminiVariantMatrix.prefix_compatibility.accepted_prefix_examples.map((item) => (
                    <div key={item.example} className="rounded-[8px] border border-stone-950/10 bg-white p-3">
                      <div className="font-mono text-stone-950">{item.example}</div>
                      <div>{item.normalization}</div>
                    </div>
                  ))}
                </div>
                <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Boundary</h3>
                <div className="space-y-1 text-xs leading-5 text-stone-600">
                  <div>gateway called: {String(activeGeminiVariantMatrix.privacy_boundary.gateway_called)}</div>
                  <div>raw payload echoed: {String(activeGeminiVariantMatrix.privacy_boundary.raw_payload_echoed)}</div>
                  <div>raw model output: {String(activeGeminiVariantMatrix.privacy_boundary.raw_model_output_included)}</div>
                </div>
              </div>
            </div>

            <div className="mb-3 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-black uppercase text-stone-500">Observed model review</h3>
                    <div className="mt-1 text-xs text-stone-600">
                      {activeGeminiVariantMatrix.summary.observed_model_count} observed /{' '}
                      {activeGeminiVariantMatrix.summary.catalog_review_count} catalog review
                    </div>
                  </div>
                  <Button variant="outline" className="soft-button" onClick={loadGeminiVariantTemplate}>
                    <ClipboardList className="h-4 w-4" />
                    Template
                  </Button>
                </div>
                {geminiVariantError && (
                  <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
                    <AlertTriangle className="h-4 w-4" />
                    {geminiVariantError}
                  </div>
                )}
                {geminiVariantExtraction && (
                  <div className="mb-3 rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs leading-5 text-stone-600">
                    <div>
                      source fields:{' '}
                      <span className="font-mono text-stone-950">
                        {geminiVariantExtraction.source_fields.join(', ') || '-'}
                      </span>
                    </div>
                    <div>
                      candidates: {geminiVariantExtraction.candidate_count} / accepted:{' '}
                      {geminiVariantExtraction.accepted_model_count} / dropped:{' '}
                      {geminiVariantExtraction.dropped_model_count}
                    </div>
                    <div>raw payload echoed: {String(geminiVariantExtraction.raw_payload_echoed)}</div>
                  </div>
                )}
                <Textarea
                  value={geminiVariantPayloadText}
                  onChange={(event) => setGeminiVariantPayloadText(event.target.value)}
                  placeholder='{"models_response":{"data":[{"id":"models/gemini-2.5-flash-lite"},{"id":"google/gemini-3.2-flash-lite"}]}}'
                  className="min-h-[150px] font-mono text-xs"
                />
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    className="law-button"
                    onClick={evaluateGeminiVariantPayload}
                    disabled={geminiVariantEvaluateLoading}
                  >
                    {geminiVariantEvaluateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                    Review models
                  </Button>
                  <Button
                    variant="outline"
                    className="soft-button"
                    onClick={() => {
                      setGeminiVariantPayloadText('');
                      setGeminiVariantError('');
                      setGeminiVariantMatrix(data?.gemini_variant_matrix ?? null);
                    }}
                  >
                    Reset
                  </Button>
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Review actions</h3>
                <ul className="space-y-2 text-sm leading-6 text-stone-700">
                  {activeGeminiVariantMatrix.recommended_actions.map((action) => (
                    <li key={action} className="flex gap-2">
                      <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-stone-950" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
                <h3 className="mb-3 mt-5 text-sm font-black uppercase text-stone-500">Validation</h3>
                <div className="space-y-2">
                  {activeGeminiVariantMatrix.validation_commands.slice(0, 3).map((command) => (
                    <div key={command} className="break-all rounded-[8px] border border-stone-950/10 bg-white p-3 font-mono text-[11px] text-stone-600">
                      {command}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Route role</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Request shapes</TableHead>
                    <TableHead>Review note</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {geminiVariantRows.map((row) => (
                    <TableRow key={row.model_id}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">{row.model_id}</div>
                        <div className="mt-1 text-xs text-stone-600">{row.family}</div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {row.configured_roles.map((role) => (
                            <Badge key={role} variant="outline" className="bg-white font-mono text-[10px] text-stone-700">
                              {role}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.route_role === 'cheap_first_default'
                              ? statusClass('pass')
                              : row.route_role === 'premium_exception'
                                ? statusClass('fail')
                                : statusClass('warn')
                          }
                        >
                          {row.route_role.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-2 text-[11px] text-stone-500">
                          high-frequency: {String(row.high_frequency_default_allowed)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier] ?? 'bg-white'}>
                          {row.cost_tier}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.pricing_status}</div>
                      </TableCell>
                      <TableCell className="max-w-[320px] font-mono text-[11px] leading-5 text-stone-600">
                        {row.supported_request_shapes.join(', ')}
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                        {row.review_note}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {geminiVariantObservedRows.length > 0 && (
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Observed model</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Canonical</TableHead>
                      <TableHead>Warnings</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {geminiVariantObservedRows.map((row) => (
                      <TableRow key={row.raw_model}>
                        <TableCell className="font-mono text-xs text-stone-700">{row.raw_model}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={row.status === 'catalog_known' ? statusClass('pass') : statusClass('warn')}
                          >
                            {row.status.replace(/_/g, ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-stone-700">{row.canonical_model ?? '-'}</TableCell>
                        <TableCell className="max-w-[480px] text-xs leading-5 text-stone-600">
                          {row.warnings.join(', ') || row.action}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>
        )}

        {(activeGeminiCheapFirstCoverageGate || geminiCheapFirstCoverageGateError) && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeGeminiCheapFirstCoverageGate
                    ? `${activeGeminiCheapFirstCoverageGate.summary.coverage_row_count} coverage rows / ${activeGeminiCheapFirstCoverageGate.summary.ready_row_count} ready / ${activeGeminiCheapFirstCoverageGate.summary.review_row_count} review / ${activeGeminiCheapFirstCoverageGate.summary.blocked_row_count} blocked`
                    : 'metadata-only Gemini cheap-first coverage review'}
                </div>
                <div className="mt-1 font-mono text-[11px] text-stone-500">
                  {activeGeminiCheapFirstCoverageGate?.id ?? 'modelops-gemini-cheap-first-coverage-gate'}
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeGeminiCheapFirstCoverageGate?.status)}>
                {activeGeminiCheapFirstCoverageGate?.status.replace(/_/g, ' ') ?? 'not loaded'}
              </Badge>
            </div>

            {geminiCheapFirstCoverageGateError && (
              <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <AlertTriangle className="h-4 w-4" />
                {geminiCheapFirstCoverageGateError}
              </div>
            )}

            {activeGeminiCheapFirstCoverageGate && (
              <>
                <div className="mb-3 grid gap-3 md:grid-cols-4 xl:grid-cols-7">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.coverage_row_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">coverage rows</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.ready_row_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">ready rows</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.review_row_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">review rows</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.blocked_row_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">blocked rows</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.cheap_first_ready_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">cheap-first ready</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.premium_exception_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">premium exceptions</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.unknown_model_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">unknown models</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.non_gemini_default_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">non-Gemini defaults</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.missing_price_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">missing price</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeGeminiCheapFirstCoverageGate.summary.missing_reasoning_policy_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">missing reasoning</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {String(activeGeminiCheapFirstCoverageGate.summary.model_called)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">model called</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {String(activeGeminiCheapFirstCoverageGate.summary.gateway_called)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">gateway called</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {String(activeGeminiCheapFirstCoverageGate.summary.network_called)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">network called</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {String(activeGeminiCheapFirstCoverageGate.summary.credentials_included)}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">credentials included</div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Task</TableHead>
                        <TableHead>Coverage</TableHead>
                        <TableHead>Models</TableHead>
                        <TableHead>Cheap-first</TableHead>
                        <TableHead>Catalog</TableHead>
                        <TableHead>Policy</TableHead>
                        <TableHead>Reasons</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {geminiCheapFirstCoverageRows.map((row) => (
                        <TableRow key={`${row.task}-${row.runtime_default_model}-${row.recommended_model}`}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.task}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.release_action}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass(row.coverage_status)}>
                              {row.coverage_status.replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            <div>runtime {row.runtime_default_model || '-'}</div>
                            <div className="mt-1">recommended {row.recommended_model || '-'}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={row.cheap_first_aligned ? statusClass('pass') : statusClass('warn')}>
                              {row.cheap_first_aligned ? 'aligned' : 'review'}
                            </Badge>
                            {row.premium_exception && (
                              <div className="mt-2">
                                <Badge variant="outline" className={statusClass('fail')}>
                                  premium exception
                                </Badge>
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div className="font-mono text-stone-950">{row.model_family}</div>
                            <Badge variant="outline" className={`mt-1 ${costClass[row.cost_tier] ?? 'bg-white'}`}>
                              {row.cost_tier}
                            </Badge>
                            <div className="mt-1">{row.lifecycle_status}</div>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>price_status: {row.price_status}</div>
                            <div>reasoning_policy_status: {row.reasoning_policy_status}</div>
                            <div>gateway_compatibility_status: {row.gateway_compatibility_status}</div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            <div>{row.reason_codes.join(', ') || '-'}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">
                              linked_gate_ids: {row.linked_gate_ids.join(', ') || '-'}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                    <div className="text-xs leading-5 text-stone-600">
                      Metadata only; no prompt text, request bodies, secrets, or model/gateway calls are included.
                    </div>
                    <div className="mt-2 text-xs leading-5 text-stone-600">
                      model_called: {String(activeGeminiCheapFirstCoverageGate.summary.model_called)} / gateway_called:{' '}
                      {String(activeGeminiCheapFirstCoverageGate.summary.gateway_called)} / network_called:{' '}
                      {String(activeGeminiCheapFirstCoverageGate.summary.network_called)} / credentials_included:{' '}
                      {String(activeGeminiCheapFirstCoverageGate.summary.credentials_included)}
                    </div>
                    <div className="mt-2 text-xs leading-5 text-stone-500">
                      scope: {String(activeGeminiCheapFirstCoverageGate.privacy_boundary.output_scope ?? 'metadata-only summary')}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Claim boundary</h3>
                    <div className="space-y-1 text-xs leading-5 text-stone-600">
                      {geminiCheapFirstCoverageClaimBoundaryEntries.length > 0 ? (
                        geminiCheapFirstCoverageClaimBoundaryEntries.map(([key, value]) => (
                          <div key={key}>
                            {key}: {value == null ? '-' : String(value)}
                          </div>
                        ))
                      ) : (
                        <div>No public benchmark, automatic routing, or live execution claims are made by this metadata panel.</div>
                      )}
                    </div>
                    <div className="mt-3 text-xs leading-5 text-stone-600">
                      {activeGeminiCheapFirstCoverageGate.recommended_actions.slice(0, 2).join(' ')}
                    </div>
                  </div>

                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                    <div className="space-y-2">
                      {activeGeminiCheapFirstCoverageGate.validation_commands.slice(0, 3).map((command) => (
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
              </>
            )}
          </section>
        )}

        {data?.catalog_source_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini catalog source audit</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.catalog_source_audit.summary.official_source_url_count} official source URLs /{' '}
                  {data.catalog_source_audit.summary.priced_model_count} priced models /{' '}
                  {data.catalog_source_audit.summary.high_frequency_aligned_count} cheap-first defaults aligned
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.catalog_source_audit.status)}>
                {data.catalog_source_audit.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.catalog_source_audit.summary.catalog_model_count}</div>
                <div className="mt-1 text-sm text-stone-600">catalog rows</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.catalog_source_audit.summary.source_reference_count}</div>
                <div className="mt-1 text-sm text-stone-600">source references</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.catalog_source_audit.summary.missing_pricing_count}</div>
                <div className="mt-1 text-sm text-stone-600">pricing watch rows</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.catalog_source_audit.summary.preview_model_count}</div>
                <div className="mt-1 text-sm text-stone-600">preview rows</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.catalog_source_audit.summary.warning_check_count}</div>
                <div className="mt-1 text-sm text-stone-600">warning checks</div>
              </div>
            </div>

            <div className="mb-3 grid gap-3 lg:grid-cols-[0.85fr_1.15fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Official source review</h3>
                <div className="space-y-2">
                  {data.catalog_source_audit.source_references.map((source) => (
                    <a
                      key={source.id}
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs leading-5 text-stone-600 hover:border-stone-950/30"
                    >
                      <div className="font-semibold text-stone-950">{source.title}</div>
                      <div className="font-mono text-[11px] text-stone-500">{source.url}</div>
                      <div className="mt-1">{source.review_purpose}</div>
                    </a>
                  ))}
                </div>
                <h3 className="mb-2 mt-5 text-sm font-black uppercase text-stone-500">Cheap-first defaults</h3>
                <div className="space-y-2">
                  {catalogSourceDefaultRows.map((row) => (
                    <div key={row.task} className="rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs leading-5 text-stone-600">
                      <div className="font-semibold text-stone-950">{row.task}</div>
                      <div className="font-mono text-[11px] text-stone-500">{row.default_model}</div>
                      <div>canonical: {row.canonical_model ?? '-'}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 text-xs leading-5 text-stone-500">
                  network called: {String(data.catalog_source_audit.privacy_boundary.network_called)} / raw payload echoed:{' '}
                  {String(data.catalog_source_audit.privacy_boundary.raw_payload_echoed)}
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Check</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {catalogSourceChecks.map((check) => (
                      <TableRow key={check.id}>
                        <TableCell className="font-mono text-xs text-stone-700">{check.id}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={statusClass(check.status)}>
                            {check.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Pricing</TableHead>
                    <TableHead>Default posture</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {catalogSourceRows.map((row) => (
                    <TableRow key={row.model_id}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">{row.model_id}</div>
                        <div className="mt-1 text-xs text-stone-600">
                          {row.catalog_status} / {row.cost_tier} / {row.latency_tier}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={row.official_source_url ? statusClass('pass') : statusClass('fail')}>
                          {row.official_source_url ? 'official source' : 'review source'}
                        </Badge>
                        <div className="mt-1 max-w-[280px] break-all font-mono text-[11px] text-stone-500">{row.source_url}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={row.pricing_status === 'missing' ? statusClass('warn') : statusClass('pass')}>
                          {row.pricing_status.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                        <div>{row.review_note}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">
                          roles: {row.configured_roles.join(', ') || '-'}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {catalogCandidatePatchPlan && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Model catalog candidate patch plan</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {catalogCandidatePatchPlan.summary.candidate_patch_count} candidate patches /{' '}
                  {catalogCandidatePatchPlan.summary.existing_catalog_review_count} known catalog reviews /{' '}
                  {catalogCandidatePatchPlan.summary.external_ignore_count} external ids ignored
                </div>
              </div>
              <Badge variant="outline" className={statusClass(catalogCandidatePatchPlan.status)}>
                {catalogCandidatePatchPlan.status.replace(/_/g, ' ')}
              </Badge>
            </div>

            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {catalogCandidatePatchPlan.summary.candidate_patch_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">candidate patches</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{catalogCandidatePatchPlan.summary.add_count}</div>
                <div className="mt-1 text-sm text-stone-600">adds</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {catalogCandidatePatchPlan.summary.review_required_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">review required</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{catalogCandidatePatchPlan.summary.blocked_count}</div>
                <div className="mt-1 text-sm text-stone-600">blocked</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {catalogCandidatePatchPlan.summary.pricing_watch_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">pricing watch</div>
              </div>
            </div>

            <div className="mb-3 grid gap-3 lg:grid-cols-[1.3fr_0.7fr]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Patch action</TableHead>
                      <TableHead>Cost / pricing</TableHead>
                      <TableHead>Default posture</TableHead>
                      <TableHead>Release action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {catalogCandidatePatchRows.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell className="max-w-[260px]">
                          <div className="font-mono text-xs font-semibold text-stone-950">
                            {row.proposed_catalog_id ?? row.model_id ?? row.observed_model}
                          </div>
                          <div className="mt-1 font-mono text-[11px] text-stone-500">{row.observed_model}</div>
                        </TableCell>
                        <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                          <div className="font-mono font-semibold text-stone-950">{row.patch_action}</div>
                          <div className="mt-1">{row.catalog_status ?? row.row_type}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={costClass[row.cost_tier ?? ''] ?? 'bg-white'}>
                            {row.cost_tier ?? 'unknown'}
                          </Badge>
                          <div className="mt-2 text-xs text-stone-600">
                            {row.latency_tier ?? 'unknown'} / {row.pricing_status ?? 'unknown'}
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                          <Badge
                            variant="outline"
                            className={
                              row.default_allowed_for_high_frequency ? statusClass('pass') : statusClass('warn')
                            }
                          >
                            default_allowed_for_high_frequency:{' '}
                            {String(Boolean(row.default_allowed_for_high_frequency))}
                          </Badge>
                          <div className="mt-2">{row.cheap_first_candidate_status ?? row.default_promotion_state}</div>
                        </TableCell>
                        <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                          <div className="font-mono text-[11px] text-stone-500">{row.release_action ?? '-'}</div>
                          <div className="mt-1">{row.recommended_action ?? row.reason ?? '-'}</div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {catalogCandidatePatchRows.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-sm text-stone-600">
                          No new catalog candidate rows are required for the current sanitized model metadata.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>

              <div className="space-y-3">
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-3 text-sm font-black uppercase text-stone-500">Candidate checks</h3>
                  <div className="space-y-2">
                    {catalogCandidatePatchChecks.map((check) => (
                      <div key={check.id} className="rounded-[8px] border border-stone-950/10 bg-white p-3 text-xs leading-5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono font-semibold text-stone-950">{check.id}</span>
                          <Badge variant="outline" className={statusClass(check.status)}>
                            {check.status}
                          </Badge>
                        </div>
                        <div className="mt-1 text-stone-600">{check.reason}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Privacy boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {boundaryDisplayEntries(catalogCandidatePatchPlan.privacy_boundary).map(([key, value]) => (
                      <div key={key}>
                        {key}: {String(value)}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Claim boundary</h3>
                  <div className="space-y-1 text-xs leading-5 text-stone-600">
                    {catalogCandidateClaimBoundaryEntries.length > 0 ? (
                      catalogCandidateClaimBoundaryEntries.map(([key, value]) => (
                        <div key={key}>
                          {key}: {String(value)}
                        </div>
                      ))
                    ) : (
                      <div>No automatic catalog edit, default change, live execution, pricing accuracy, or quality claims.</div>
                    )}
                  </div>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Validation commands</h3>
                  <div className="space-y-2">
                    {catalogCandidatePatchPlan.validation_commands.slice(0, 3).map((command) => (
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
            </div>
          </section>
        )}

        {data?.gateway_health_plan && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gateway health plan</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.gateway_health_plan.summary.base_url_configured ? 'base URL ready' : 'base URL missing'} /{' '}
                  {data.gateway_health_plan.summary.api_key_configured ? 'key configured' : 'key missing'} /{' '}
                  {data.gateway_health_plan.summary.cheap_first_low_cost_count} cheap-first roles
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.gateway_health_plan.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.gateway_health_plan.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.gateway_health_plan.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-5">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="truncate font-mono text-sm font-black text-stone-950">
                  {data.gateway_health_plan.gateway_config.base_url_display}
                </div>
                <div className="mt-1 text-sm text-stone-600">base URL</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_health_plan.summary.unknown_role_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown models</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_health_plan.summary.known_media_role_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">media roles</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.gateway_health_plan.summary.warning_check_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.gateway_health_plan.summary.estimated_probe_cost_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap probe estimate</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Probe</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gatewayHealthRows.map((row) => (
                    <TableRow key={row.role}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.role}</div>
                        <div className="mt-1 text-[11px] text-stone-500">
                          {row.cheap_first_aligned ? 'cheap-first' : 'review cost'}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                        <div className="font-mono text-stone-950">{row.model}</div>
                        <div className="font-mono text-[11px]">{row.canonical_model ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          {row.cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.model_status}</div>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-600">
                        <div>{gatewayHealthProbeText(row)}</div>
                        <div className="mt-1 text-[11px] text-stone-500">{row.probe_type}</div>
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Probe</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Expected</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gatewayHealthContracts.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-semibold text-stone-950">{row.id}</TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.method}</TableCell>
                      <TableCell className="max-w-[320px] font-mono text-xs text-stone-700">{row.url}</TableCell>
                      <TableCell className="max-w-[480px] text-xs leading-5 text-stone-600">
                        {row.expected_success}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Gateway probe evaluation</h2>
              <div className="mt-1 text-sm text-stone-600">
                {activeProbeEvaluation
                  ? `${activeProbeEvaluation.summary.observed_model_count} observed / ${activeProbeEvaluation.summary.probed_cheap_candidate_count} cheap probes / ${activeProbeEvaluation.summary.probed_image_candidate_count} image probes`
                  : 'sanitized model list, tiny chat probe, and image smoke review'}
                {activeProbeEvaluation?.stored_at && (
                  <span className="ml-2 font-mono text-[11px] text-stone-500">{activeProbeEvaluation.stored_at}</span>
                )}
              </div>
            </div>
            <Badge variant="outline" className={statusClass(activeProbeEvaluation?.status)}>
              {activeProbeEvaluation?.status ?? 'not evaluated'}
            </Badge>
          </div>

          {probeError && (
            <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              <AlertTriangle className="h-4 w-4" />
              {probeError}
            </div>
          )}

          <div className="mb-3 grid gap-3 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-semibold text-stone-950">Probe payload</div>
                  <div className="mt-1 text-xs text-stone-500">JSON object only; no headers, keys, prompts, or raw output.</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="soft-button"
                    onClick={loadProbeTemplate}
                    disabled={probeTemplateLoading}
                  >
                    {probeTemplateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ClipboardList className="h-4 w-4" />}
                    Template
                  </Button>
                  <Button
                    type="button"
                    className="law-button"
                    onClick={evaluateProbePayload}
                    disabled={probeLoading}
                  >
                    {probeLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                    Evaluate
                  </Button>
                </div>
              </div>
              <Textarea
                value={probePayloadText}
                onChange={(event) => setProbePayloadText(event.target.value)}
                className="min-h-[260px] resize-y rounded-[8px] bg-white font-mono text-xs leading-5"
                spellCheck={false}
                placeholder='{"models_response":{"data":[{"id":"gemini-2.5-flash-lite"},{"id":"gemini-2.5-flash-image"}]},"chat_probe_results":{"gemini-2.5-flash-lite":{"status":"pass","http_status":200,"json_ok":true,"latency_ms":1200}},"image_probe_results":{"gemini-2.5-flash-image":{"status":"pass","http_status":200,"image_count":1,"latency_ms":2400}}}'
              />
              <div className="mt-3 text-xs leading-5 text-stone-500">
                {activeProbeEvaluation?.privacy_note ?? 'The backend evaluates sanitized IDs, HTTP status, latency, JSON booleans, and image counts only.'}
              </div>
            </div>

            <div className="grid gap-3">
              <div className="grid gap-3 sm:grid-cols-4">
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="text-2xl font-black text-stone-950">
                    {activeProbeEvaluation?.summary.cheap_candidate_count ?? 0}
                  </div>
                  <div className="mt-1 text-sm text-stone-600">cheap candidates</div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="text-2xl font-black text-stone-950">
                    {activeProbeEvaluation?.summary.probed_image_candidate_count ?? 0}
                  </div>
                  <div className="mt-1 text-sm text-stone-600">image probes</div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="text-2xl font-black text-stone-950">
                    {activeProbeEvaluation?.summary.recommended_change_count ?? 0}
                  </div>
                  <div className="mt-1 text-sm text-stone-600">env changes</div>
                </div>
                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="text-2xl font-black text-stone-950">
                    {activeProbeEvaluation?.summary.forbidden_payload_field_count ?? 0}
                  </div>
                  <div className="mt-1 text-sm text-stone-600">blocked fields</div>
                </div>
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Env</TableHead>
                      <TableHead>Recommendation</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {probeEnvRows.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="py-6 text-center text-stone-500">
                          Evaluate sanitized probe results to generate default model recommendations.
                        </TableCell>
                      </TableRow>
                    ) : (
                      probeEnvRows.map((row) => (
                        <TableRow key={row.env_var}>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold text-stone-950">{row.env_var}</div>
                            <div className="mt-1 text-[11px] text-stone-500">{row.task}</div>
                          </TableCell>
                          <TableCell className="max-w-[300px] text-xs leading-5 text-stone-600">
                            <div className="font-mono text-stone-950">{row.recommended_value}</div>
                            <div className="font-mono text-[11px]">current {row.current_value}</div>
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            <Badge
                              variant="outline"
                              className={
                                row.requires_change
                                  ? 'border-amber-200 bg-amber-50 text-amber-900'
                                  : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              }
                            >
                              {row.requires_change ? 'review change' : 'aligned'}
                            </Badge>
                            <div className="mt-1">{row.reason}</div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </div>

          {probeCheckRows.length > 0 && (
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {probeCheckRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(check.status)}>
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[640px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {probeModelRows.length > 0 && (
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Catalog</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Probe</TableHead>
                    <TableHead>Latency</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {probeModelRows.map((row) => (
                    <TableRow key={row.model}>
                      <TableCell className="max-w-[280px]">
                        <div className="font-mono text-xs font-semibold text-stone-950">{row.model}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.canonical_model ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.is_known_model
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.is_known_model ? row.model_status : 'unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          {row.cost_tier ?? 'unpriced'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.chat_probe_status)}>
                          {row.chat_probe_status}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">HTTP {row.http_status ?? '-'}</div>
                        {row.image_probe_status !== 'not_supplied' && (
                          <div className="mt-2">
                            <Badge variant="outline" className={statusClass(row.image_probe_status)}>
                              image {row.image_probe_status}
                            </Badge>
                            <div className="mt-1 text-[11px] text-stone-500">
                              {row.image_count ?? 0} img / HTTP {row.image_http_status ?? '-'}
                            </div>
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-600">
                        <div>{row.latency_ms == null ? '-' : `${formatNumber(row.latency_ms)}ms`}</div>
                        {row.image_latency_ms != null && (
                          <div className="mt-1 text-[11px] text-stone-500">image {formatNumber(row.image_latency_ms)}ms</div>
                        )}
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>

        {(activeCheapFirstCalibration || cheapFirstError) && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cheap-first calibration</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {activeCheapFirstCalibration
                    ? `${activeCheapFirstCalibration.summary.cheap_first_retained_count} cheap defaults / ${activeCheapFirstCalibration.summary.balanced_precheck_count} balanced prechecks / ${activeCheapFirstCalibration.summary.premium_exception_count} premium exception`
                    : 'metadata-only Gemini/NewAPI calibration'}
                </div>
              </div>
              <Badge variant="outline" className={statusClass(activeCheapFirstCalibration?.status)}>
                {activeCheapFirstCalibration?.status ?? 'not loaded'}
              </Badge>
            </div>

            {cheapFirstError && (
              <div className="mb-3 flex items-center gap-2 rounded-[8px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <AlertTriangle className="h-4 w-4" />
                {cheapFirstError}
              </div>
            )}

            <div className="mb-3 grid gap-3 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-stone-950">Calibration payload</div>
                    <div className="mt-1 text-xs text-stone-500">
                      Synthetic fixture labels and run metadata only; no prompts, headers, raw output, or credentials.
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button type="button" variant="outline" className="soft-button" onClick={loadCheapFirstTemplate}>
                      <ClipboardList className="h-4 w-4" />
                      Template
                    </Button>
                    <Button
                      type="button"
                      className="law-button"
                      onClick={evaluateCheapFirstPayload}
                      disabled={cheapFirstEvaluateLoading}
                    >
                      {cheapFirstEvaluateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                      Evaluate
                    </Button>
                  </div>
                </div>
                <Textarea
                  value={cheapFirstPayloadText}
                  onChange={(event) => setCheapFirstPayloadText(event.target.value)}
                  className="min-h-[220px] resize-y rounded-[8px] bg-white font-mono text-xs leading-5"
                  spellCheck={false}
                  placeholder='{"fixture_report":{"observations":{"fixture-service-agreement-small":{"route":"review","output_text":"liability_cap risk_matrix cost_route"}}}}'
                />
              </div>

              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-3 font-semibold text-stone-950">Evaluation guardrails</div>
                <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-2">
                  <div>
                    <div className="mb-1 text-xs font-black uppercase text-stone-500">Accepted</div>
                    <div>Fixture ids, task labels, route labels, model ids, cost estimates, and synthetic signal labels.</div>
                  </div>
                  <div>
                    <div className="mb-1 text-xs font-black uppercase text-stone-500">Blocked</div>
                    <div>Secrets, headers, emails, prompts, raw legal text, gateway responses, and raw model output.</div>
                  </div>
                  <div>
                    <div className="mb-1 text-xs font-black uppercase text-stone-500">Effect</div>
                    <div>Updates this page result only; it does not write config or call NewAPI/Gemini.</div>
                  </div>
                  <div>
                    <div className="mb-1 text-xs font-black uppercase text-stone-500">Review</div>
                    <div>Use failing rows to hold defaults or keep premium exceptions operator-reviewed.</div>
                  </div>
                </div>
              </div>
            </div>

            {activeCheapFirstCalibration && (
              <>
                <div className="mb-3 grid gap-3 md:grid-cols-4">
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.pass_count}/{activeCheapFirstCalibration.summary.task_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">passing tasks</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {Math.round((activeCheapFirstCalibration.summary.estimated_savings_ratio ?? 0) * 100)}%
                    </div>
                    <div className="mt-1 text-sm text-stone-600">forecast savings</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.observed_fixture_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">observed fixtures</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.newapi_called ? 'live' : 'local'}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">gateway mode</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.external_research_source_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">research sources</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.research_mapped_task_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">mapped tasks</div>
                  </div>
                  <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                    <div className="text-2xl font-black text-stone-950">
                      {activeCheapFirstCalibration.summary.forbidden_payload_field_count}
                    </div>
                    <div className="mt-1 text-sm text-stone-600">blocked payload fields</div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                    <div>
                      <div className="mb-1 font-semibold text-stone-950">Next action</div>
                      <div>{activeCheapFirstCalibration.recommended_actions[0]}</div>
                    </div>
                    <div>
                      <div className="mb-1 font-semibold text-stone-950">Privacy boundary</div>
                      <div>
                        NewAPI called: {activeCheapFirstCalibration.summary.newapi_called ? 'yes' : 'no'} / raw payload echoed:{' '}
                        {activeCheapFirstCalibration.summary.raw_payload_echoed ? 'yes' : 'no'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Task</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Decision</TableHead>
                        <TableHead>Model</TableHead>
                        <TableHead>Fixture</TableHead>
                        <TableHead>Release gates</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cheapFirstRows.map((row) => (
                        <TableRow key={row.id}>
                          <TableCell>
                            <div className="font-semibold text-stone-950">{row.product_area.replace(/_/g, ' ')}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={statusClass(row.status)}>
                              {row.status}
                            </Badge>
                            <div className="mt-1 text-[11px] text-stone-500">{row.reason_codes.join(', ')}</div>
                          </TableCell>
                          <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                            <div className="font-semibold text-stone-950">{row.calibration_decision.replace(/_/g, ' ')}</div>
                            <div>{row.decision?.replace(/_/g, ' ') ?? '-'}</div>
                          </TableCell>
                          <TableCell className="max-w-[260px]">
                            <div className="font-mono text-xs text-stone-700">{row.selected_model ?? '-'}</div>
                            <Badge variant="outline" className={costClass[row.cost_tier] ?? 'mt-1 bg-white'}>
                              {row.cost_tier}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs leading-5 text-stone-600">
                            <div>{row.fixture_score}/{row.quality_floor}</div>
                            <div className="mt-1 text-[11px] text-stone-500">{row.fixture_ids.length || 'metadata only'}</div>
                          </TableCell>
                          <TableCell className="max-w-[280px] text-xs leading-5 text-stone-600">
                            {row.release_gate_links.join(', ')}
                            <div className="mt-1 text-[11px] text-stone-500">
                              research: {row.research_source_ids.join(', ') || 'unmapped'}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-[380px] text-xs leading-5 text-stone-600">{row.next_action}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Research source</TableHead>
                        <TableHead>Calibration tasks</TableHead>
                        <TableHead>Local fixtures</TableHead>
                        <TableHead>Policy impact</TableHead>
                        <TableHead>Import policy</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cheapFirstResearchRows.map((row) => (
                        <TableRow key={row.source_id}>
                          <TableCell className="max-w-[260px]">
                            <div className="font-semibold text-stone-950">{row.title}</div>
                            <div className="mt-1 font-mono text-[11px] text-stone-500">{row.source_id}</div>
                            <a
                              href={row.url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1 block break-all text-[11px] text-blue-700 hover:underline"
                            >
                              {row.url}
                            </a>
                          </TableCell>
                          <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                            {row.calibration_task_ids.join(', ')}
                            <div className="mt-1 text-[11px] text-stone-500">{row.task_signal}</div>
                          </TableCell>
                          <TableCell className="max-w-[220px] font-mono text-xs text-stone-700">
                            {row.local_fixture_ids.join(', ') || 'metadata only'}
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {row.policy_impact}
                          </TableCell>
                          <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                            {row.import_policy}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </>
            )}
          </section>
        )}

        {data?.price_refresh_monitor && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Price refresh monitor</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.price_refresh_monitor.summary.refresh_needed_count} refresh signals /{' '}
                  {data.price_refresh_monitor.summary.missing_price_metadata_count} missing prices /{' '}
                  {data.price_refresh_monitor.summary.observed_model_count} observed models
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.price_refresh_monitor.status)}>
                {data.price_refresh_monitor.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.price_refresh_monitor.summary.blocking_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.price_refresh_monitor.summary.warning_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.price_refresh_monitor.summary.drift_signal_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">drift signals</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="break-words text-lg font-black text-stone-950">
                  {data.price_refresh_monitor.summary.high_frequency_tasks.join(', ')}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first tasks</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="break-words text-lg font-black text-stone-950">
                  {data.price_refresh_monitor.summary.media_tasks.join(', ') || '-'}
                </div>
                <div className="mt-1 text-sm text-stone-600">media tasks</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Summary</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {priceRefreshChecks.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(check.status)}>
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {Object.entries(check.summary)
                          .map(([key, value]) => `${key}: ${String(value)}`)
                          .join(', ')}
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                        {check.recommended_action}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Signal</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {priceRefreshSignals.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center text-stone-500">
                        No Gemini/NewAPI price refresh drift found in local metadata.
                      </TableCell>
                    </TableRow>
                  ) : (
                    priceRefreshSignals.slice(0, 12).map((signal) => (
                      <TableRow key={signal.id}>
                        <TableCell>
                          <div className="font-mono text-xs font-semibold text-stone-950">{signal.signal_type}</div>
                          <div className="mt-1 font-mono text-[11px] text-stone-500">{signal.id}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={statusClass(signal.severity)}>
                            {signal.severity}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-[260px] font-mono text-xs text-stone-700">
                          {signal.model ?? '-'}
                        </TableCell>
                        <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                          {signal.reason}
                        </TableCell>
                        <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                          {signal.recommended_action}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.lifecycle_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Gemini lifecycle policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.lifecycle_policy.summary.stable_catalog_count} stable /{' '}
                  {data.lifecycle_policy.summary.preview_catalog_count} preview /{' '}
                  {data.lifecycle_policy.summary.default_allowed_count} defaults allowed
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.lifecycle_policy.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.lifecycle_policy.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.lifecycle_policy.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.lifecycle_policy.summary.latest_alias_default_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">latest aliases</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.lifecycle_policy.summary.deprecated_default_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">deprecated defaults</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.lifecycle_policy.summary.unknown_default_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown defaults</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.lifecycle_policy.summary.cheap_first_aligned_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first aligned</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Lifecycle</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Budget</TableHead>
                    <TableHead>Default</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lifecycleRows.map((row) => (
                    <TableRow key={`${row.role}-${row.task}`}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{row.role}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.lifecycle_state === 'stable'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.lifecycle_state === 'deprecated'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.lifecycle_state.replace(/_/g, ' ')}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">{row.model_status}</div>
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        <div className="font-mono text-stone-950">{row.model}</div>
                        <div className="font-mono text-[11px]">{row.canonical_model ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          {row.cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">max {row.max_cost_tier}</div>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        <div>{row.default_allowed ? 'allowed' : 'review required'}</div>
                        <div>{row.cheap_first_aligned ? 'cheap-first' : 'cost drift'}</div>
                      </TableCell>
                      <TableCell className="max-w-[480px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <h3 className="mb-2 text-sm font-black uppercase text-stone-500">Alias policy</h3>
              <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-2">
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Canonical prefixes</div>
                  <div className="font-mono text-xs">{data.lifecycle_policy.alias_policy.canonical_prefixes.join(', ')}</div>
                </div>
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Default examples</div>
                  <div className="font-mono text-xs">{data.lifecycle_policy.alias_policy.stable_default_examples.join(', ')}</div>
                </div>
                <div>{data.lifecycle_policy.alias_policy.pass_through}</div>
                <div>{data.lifecycle_policy.alias_policy.latest_alias_default_policy}</div>
              </div>
            </div>
          </section>
        )}

        {data?.cost_guardrails && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cost guardrails</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.cost_guardrails.blocking_check_ids.length} blocking ·{' '}
                  {data.cost_guardrails.warning_check_ids.length} warning checks
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.cost_guardrails.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.cost_guardrails.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.cost_guardrails.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.cost_guardrails.summary.estimated_cost_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">actual estimate</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.cost_guardrails.summary.premium_request_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">premium ratio</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.cost_guardrails.summary.failure_rate * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">failure rate</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.cost_guardrails.summary.unpriced_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unpriced models</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {guardrailRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{check.ratio != null ? `${Math.round(check.ratio * 100)}%` : check.value}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        <section className="mb-8">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-xl font-black text-stone-950">Routing aliases</h2>
            {data?.budget_policy && (
              <Badge variant="outline" className="bg-white">
                premium review {data.budget_policy.premium_requires_review ? 'on' : 'off'}
              </Badge>
            )}
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {aliases.map(([alias, model]) => (
              <div key={alias} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="font-mono text-sm font-semibold text-stone-950">{alias}</div>
                <div className="mt-2 break-words text-sm text-stone-600">{model}</div>
              </div>
            ))}
          </div>
        </section>

        {data?.model_configuration_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Configuration audit</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.model_configuration_audit.summary.role_count} roles /{' '}
                  {data.model_configuration_audit.summary.unknown_model_count} unknown models
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.model_configuration_audit.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.model_configuration_audit.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.model_configuration_audit.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Gaps</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {configurationAuditRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell>
                        <div className="font-semibold text-stone-950">{check.label}</div>
                        <div className="mt-1 font-mono text-[11px] text-stone-500">{check.env_var ?? '-'}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{check.model}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[check.cost_tier || ''] ?? 'bg-white'}>
                          {check.cost_tier ?? 'unknown'}
                        </Badge>
                        <div className="mt-1 text-[11px] text-stone-500">max {check.max_cost_tier}</div>
                      </TableCell>
                      <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                        {check.missing_required_capabilities.length || check.missing_preferred_capabilities.length
                          ? [...check.missing_required_capabilities, ...check.missing_preferred_capabilities].join(', ')
                          : '-'}
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.default_template_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Default template alignment</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.default_template_audit.summary.default_count} defaults /{' '}
                  {data.default_template_audit.summary.source_count} checked-in templates /{' '}
                  {data.default_template_audit.summary.drift_count} drift items
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.default_template_audit.status)}>
                {data.default_template_audit.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.08em] text-stone-500">Gemini cheap-first visibility</div>
                <div className="mt-2 text-sm font-semibold text-stone-950">
                  APP_AI_AGENTIC_MODEL / APP_AI_GROUNDED_RESEARCH_MODEL
                </div>
                <div className="mt-1 text-xs leading-5 text-stone-600">
                  visible: {String(data.default_template_audit.summary.agentic_grounded_defaults_visible)}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.08em] text-stone-500">Routing aliases covered</div>
                <div className="mt-2 font-mono text-sm font-semibold text-stone-950">auto-agentic / auto-grounded-research</div>
                <div className="mt-1 text-xs leading-5 text-stone-600">
                  {data.default_template_audit.summary.aligned_count} aligned,{' '}
                  {data.default_template_audit.summary.missing_value_count} missing,{' '}
                  {data.default_template_audit.summary.mismatched_value_count} mismatched
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.08em] text-stone-500">Privacy boundary</div>
                <div className="mt-2 text-xs leading-5 text-stone-600">
                  {boundaryDisplayEntries(data.default_template_audit.privacy_boundary)
                    .map(([key, value]) => `${key}: ${String(value)}`)
                    .join(' / ')}
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Env var</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Expected</TableHead>
                    <TableHead>Templates</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {defaultTemplateRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">{row.env_var}</div>
                        <div className="mt-1 text-[11px] text-stone-500">{row.required_for}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusClass(row.status)}>
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.expected_default}</TableCell>
                      <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                        {Object.entries(row.source_values)
                          .map(([source, value]) => `${source}: ${value ?? 'missing'}`)
                          .join(' / ')}
                      </TableCell>
                      <TableCell className="max-w-[460px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-2 font-semibold text-stone-950">Checked sources</div>
                <div className="grid gap-2">
                  {data.default_template_audit.source_files.map((source) => (
                    <div key={source.id} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 text-xs leading-5 text-stone-600">
                      <span className="font-mono font-semibold text-stone-950">{source.id}</span>: {source.path}
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-2 font-semibold text-stone-950">Validation commands</div>
                <div className="grid gap-2">
                  {data.default_template_audit.validation_commands.map((command) => (
                    <div key={command} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 font-mono text-xs leading-5 text-stone-600">
                      {command}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {data?.runtime_router && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Runtime router</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {runtimeDefaults.length} task defaults / {taskInferenceRules.length} auto rules
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.runtime_router.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              {runtimeRouterFields.map(([field, note]) => (
                <div key={field} className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                  <div className="font-mono text-sm font-semibold text-stone-950">{field}</div>
                  <div className="mt-2 text-xs leading-5 text-stone-600">{note}</div>
                </div>
              ))}
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Default model</TableHead>
                    <TableHead>Budget</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runtimeDefaults.map((row) => (
                    <TableRow key={`runtime-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.resolved_model}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'bg-white'}>
                          max {row.max_cost_tier}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.budget_mode}</TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {data.runtime_router.auto_task_inference && (
              <div className="mt-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="font-semibold text-stone-950">Auto task inference</div>
                  <Badge variant="outline" className="bg-white">
                    default {data.runtime_router.auto_task_inference.default_task}
                  </Badge>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  {taskInferenceRules.map((rule) => (
                    <div key={rule} className="rounded-[6px] border border-stone-950/10 bg-white px-3 py-2 text-xs leading-5 text-stone-600">
                      {rule}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {data?.reasoning_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Reasoning policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {reasoningRows.length} task defaults / request default {data.reasoning_policy.request_field.default}
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.reasoning_policy.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Effort</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Supported</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reasoningRows.map((row) => (
                    <TableRow key={`reasoning-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell className="font-mono text-xs text-stone-700">{row.model}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.cost_mode === 'elevated-thinking'
                              ? 'border-amber-200 bg-amber-50 text-amber-900'
                              : row.cost_mode === 'thinking-disabled'
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                                : 'bg-white'
                          }
                        >
                          {row.effective_effort ?? 'omitted'}
                        </Badge>
                        {row.adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">adjusted</div>}
                      </TableCell>
                      <TableCell className="text-xs text-stone-600">{row.cost_mode}</TableCell>
                      <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                        {row.supported_efforts.join(', ') || '-'}
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.request_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Request policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {requestPolicyRows.length} task defaults / temperature and token ceilings
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.request_policy.status}
              </Badge>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Temperature</TableHead>
                    <TableHead>Max tokens</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requestPolicyRows.map((row) => (
                    <TableRow key={`request-policy-${row.task}`}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{row.effective_temperature}</div>
                        {row.temperature_adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">clamped</div>}
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{formatNumber(row.effective_max_tokens)}</div>
                        {row.max_tokens_adjusted && <div className="mt-1 text-[11px] font-semibold text-amber-700">clamped</div>}
                      </TableCell>
                      <TableCell>{row.response_format_mode}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={row.cost_mode === 'caller-expanded' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'bg-white'}>
                          {row.cost_mode}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[440px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.request_cost_bounds && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Request cost bounds</h2>
                <div className="mt-1 text-sm text-stone-600">
                  default {formatUsd(data.request_cost_bounds.summary.default_cost_usd)} / ceiling{' '}
                  {formatUsd(data.request_cost_bounds.summary.ceiling_cost_usd)}
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.request_cost_bounds.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.request_cost_bounds.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.request_cost_bounds.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.request_cost_bounds.summary.task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">tracked tasks</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.request_cost_bounds.summary.priced_task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">priced tasks</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.request_cost_bounds.summary.warning_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.request_cost_bounds.summary.blocking_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking checks</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Tokens</TableHead>
                    <TableHead>Default cost</TableHead>
                    <TableHead>Ceiling cost</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requestCostBoundRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-[240px] font-mono text-xs text-stone-700">{row.model}</div>
                        <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? 'mt-1 bg-white'}>
                          {row.cost_tier ?? 'unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        prompt {formatNumber(row.prompt_tokens_assumption)}
                        <br />
                        default {formatNumber(row.default_max_tokens)}
                        <br />
                        ceiling {formatNumber(row.ceiling_max_tokens)}
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{formatUsd(row.default_request_cost_usd)}</div>
                        <div className="mt-1 text-[11px] text-stone-500">fail {formatUsd(row.fail_default_cost_usd)}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">{formatUsd(row.ceiling_request_cost_usd)}</div>
                        <div className="mt-1 text-[11px] text-stone-500">fail {formatUsd(row.fail_ceiling_cost_usd)}</div>
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.cache_policy && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Cache policy</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.cache_policy.summary.enabled_rule_count} enabled / saves{' '}
                  {formatUsd(data.cache_policy.summary.estimated_monthly_savings_usd)}
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.cache_policy.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.cache_policy.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.cache_policy.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.cache_policy.summary.rule_count}</div>
                <div className="mt-1 text-sm text-stone-600">rules</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.cache_policy.summary.enabled_rule_count}</div>
                <div className="mt-1 text-sm text-stone-600">enabled</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.cache_policy.summary.warning_count}</div>
                <div className="mt-1 text-sm text-stone-600">warnings</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">{data.cache_policy.summary.blocking_count}</div>
                <div className="mt-1 text-sm text-stone-600">blocking checks</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>TTL / hit rate</TableHead>
                    <TableHead>Key material</TableHead>
                    <TableHead>Savings</TableHead>
                    <TableHead>Boundary</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cachePolicyRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="font-mono font-semibold text-stone-950">{row.task}</div>
                        <div className="mt-1 text-[11px] text-stone-500">
                          {row.enabled_by_default ? 'enabled' : 'disabled'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[220px] font-mono text-xs text-stone-700">{row.cache_mode}</TableCell>
                      <TableCell className="text-xs leading-5 text-stone-600">
                        {row.ttl_seconds ? `${Math.round(row.ttl_seconds / 3600)}h` : 'off'}
                        <br />
                        {Math.round(row.expected_hit_rate * 100)}% expected hit
                        <br />
                        temp {row.request_temperature}
                      </TableCell>
                      <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                        {row.key_material.join(', ')}
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-xs text-stone-700">
                          {formatUsd(row.estimated_monthly_savings_usd)}
                        </div>
                        <div className="mt-1 text-[11px] text-stone-500">
                          base {formatUsd(row.forecast_monthly_cost_usd)}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">
                        {row.privacy_boundary}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry.summary.request_count} routed requests /{' '}
                  {Math.round(data.route_telemetry.summary.downgrade_ratio * 100)}% downgraded
                </div>
              </div>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {data.route_telemetry.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_telemetry.summary.auto_inferred_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">auto inferred</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_telemetry.summary.over_budget_request_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">over budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry.summary.operator_review_request_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">review-gated</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry.summary.unknown_price_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown price</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Requests</TableHead>
                    <TableHead>Auto</TableHead>
                    <TableHead>Downgraded</TableHead>
                    <TableHead>Over budget</TableHead>
                    <TableHead>Failure</TableHead>
                    <TableHead>Models</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-stone-500">
                        No routed text calls recorded in this backend process.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryRows.map(([task, bucket]) => (
                      <TableRow key={task}>
                        <TableCell className="font-mono font-semibold text-stone-950">{task}</TableCell>
                        <TableCell>{formatNumber(bucket.requests)}</TableCell>
                        <TableCell>{formatNumber(bucket.auto_inferred)}</TableCell>
                        <TableCell>{formatNumber(bucket.downgraded_to_recommended)}</TableCell>
                        <TableCell>{formatNumber(bucket.over_budget_requested)}</TableCell>
                        <TableCell>{formatNumber(bucket.failures)}</TableCell>
                        <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">
                          {Object.entries(bucket.models).map(([model, count]) => `${model}:${count}`).join(', ')}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry_repository && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry repository</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry_repository.summary.stored_event_count} stored events /{' '}
                  {data.route_telemetry_repository.summary.daily_bucket_count} daily buckets
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.route_telemetry_repository.status)}>
                {data.route_telemetry_repository.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_repository.totals.request_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">persisted requests</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_repository.totals.downgrade_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap downgrades</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_repository.summary.rejected_event_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">rejected latest</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_repository.summary.raw_payload_storage_allowed ? 'on' : 'off'}
                </div>
                <div className="mt-1 text-sm text-stone-600">raw payload storage</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Storage mode</div>
                  <div className="font-mono text-xs">{data.route_telemetry_repository.summary.storage_mode}</div>
                </div>
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Next action</div>
                  <div>{data.route_telemetry_repository.recommended_actions[0]}</div>
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Day</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Requests</TableHead>
                    <TableHead>Success</TableHead>
                    <TableHead>Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryRepositoryRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-stone-500">
                        No persisted route telemetry events yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryRepositoryRows.map((row) => (
                      <TableRow key={`${row.day}-${row.task}-${row.resolved_model}-${row.inference_source}`}>
                        <TableCell className="font-mono text-xs font-semibold text-stone-950">{row.day}</TableCell>
                        <TableCell className="font-mono text-xs text-stone-700">{row.task}</TableCell>
                        <TableCell className="max-w-[260px] font-mono text-xs text-stone-700">{row.resolved_model}</TableCell>
                        <TableCell className="text-xs leading-5 text-stone-600">
                          {row.inference_source}
                          <br />
                          {row.routed_to_recommended_model ? 'cheap-first downgrade' : 'direct'}
                          <br />
                          {row.requires_operator_review ? 'review gated' : 'no review gate'}
                        </TableCell>
                        <TableCell>{formatNumber(row.request_count)}</TableCell>
                        <TableCell>
                          {formatNumber(row.success_count)}/{formatNumber(row.failure_count)}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-stone-700">
                          {formatUsd(row.estimated_cost_usd_sum)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry_ops_summary && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry ops summary</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry_ops_summary.summary.request_count} persisted requests /{' '}
                  {Math.round(data.route_telemetry_ops_summary.summary.failure_rate * 100)}% failure /{' '}
                  {Math.round(data.route_telemetry_ops_summary.summary.premium_request_ratio * 100)}% premium
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.route_telemetry_ops_summary.status)}>
                {data.route_telemetry_ops_summary.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_ops_summary.summary.downgrade_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">cheap-first downgrades</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_telemetry_ops_summary.summary.over_budget_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">over-budget pressure</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_ops_summary.summary.unknown_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown models</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.route_telemetry_ops_summary.summary.estimated_cost_usd_sum)}
                </div>
                <div className="mt-1 text-sm text-stone-600">persisted cost sum</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Next action</div>
                  <div>{data.route_telemetry_ops_summary.recommended_actions[0]}</div>
                </div>
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Privacy boundary</div>
                  <div>
                    raw payload storage {data.route_telemetry_ops_summary.summary.raw_payload_storage_allowed ? 'on' : 'off'} /{' '}
                    source {data.route_telemetry_ops_summary.privacy_boundary.source}
                  </div>
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Day</TableHead>
                    <TableHead>Requests</TableHead>
                    <TableHead>Failure</TableHead>
                    <TableHead>Downgrade</TableHead>
                    <TableHead>Over budget</TableHead>
                    <TableHead>Premium</TableHead>
                    <TableHead>Models</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryOpsRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-stone-500">
                        No persisted route telemetry events yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryOpsRows.map((row) => (
                      <TableRow key={`route-ops-${row.day}`}>
                        <TableCell className="font-mono text-xs font-semibold text-stone-950">{row.day}</TableCell>
                        <TableCell>{formatNumber(row.request_count)}</TableCell>
                        <TableCell>{Math.round(row.failure_rate * 100)}%</TableCell>
                        <TableCell>{Math.round(row.downgrade_ratio * 100)}%</TableCell>
                        <TableCell>{Math.round(row.over_budget_ratio * 100)}%</TableCell>
                        <TableCell>{Math.round(row.premium_request_ratio * 100)}%</TableCell>
                        <TableCell className="max-w-[380px] text-xs leading-5 text-stone-600">
                          {Object.entries(row.models).map(([model, count]) => `${model}:${count}`).join(', ')}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry_triage && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry triage queue</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry_triage.summary.triage_item_count} actions /{' '}
                  {data.route_telemetry_triage.summary.blocking_item_count} blocking /{' '}
                  {data.route_telemetry_triage.summary.cheap_first_action_count} cheap-first
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.route_telemetry_triage.status)}>
                {data.route_telemetry_triage.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_triage.summary.blocking_item_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking actions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_triage.summary.warning_item_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">warning actions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_triage.summary.highest_priority}
                </div>
                <div className="mt-1 text-sm text-stone-600">highest priority</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_triage.summary.source_request_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">source requests</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Top action</div>
                  <div>{data.route_telemetry_triage.recommended_actions[0]}</div>
                </div>
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Privacy boundary</div>
                  <div>
                    source {data.route_telemetry_triage.privacy_boundary.source} / raw payload storage{' '}
                    {data.route_telemetry_triage.privacy_boundary.raw_payload_storage_allowed ? 'on' : 'off'}
                  </div>
                </div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Priority</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Metric</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryTriageRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-stone-500">
                        No route telemetry triage actions.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryTriageRows.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-mono text-xs font-semibold text-stone-950">
                          {item.priority}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={statusClass(item.severity)}>
                            {item.severity}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-[360px] text-sm leading-5 text-stone-800">
                          <div className="font-semibold text-stone-950">{item.title}</div>
                          <div className="mt-1 break-words">{item.action}</div>
                        </TableCell>
                        <TableCell className="font-mono text-xs leading-5 text-stone-700">
                          <div>{item.metric}</div>
                          <div>
                            {String(item.value)} / {String(item.threshold)}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-stone-700">{item.owner}</TableCell>
                        <TableCell className="max-w-[420px] break-words text-xs leading-5 text-stone-600">
                          {item.reason}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_telemetry_remediation && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route telemetry remediation plan</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_telemetry_remediation.summary.remediation_step_count} steps /{' '}
                  {data.route_telemetry_remediation.summary.env_change_count} env changes /{' '}
                  {data.route_telemetry_remediation.summary.manual_review_step_count} manual review
                </div>
              </div>
              <Badge variant="outline" className={statusClass(data.route_telemetry_remediation.status)}>
                {data.route_telemetry_remediation.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_remediation.summary.blocking_step_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">blocking steps</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_remediation.summary.env_change_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">env suggestions</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_telemetry_remediation.summary.manual_review_step_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">manual review</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {formatUsd(data.route_telemetry_remediation.summary.estimated_monthly_savings_usd)}
                </div>
                <div className="mt-1 text-sm text-stone-600">estimated savings</div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="grid gap-3 text-sm leading-6 text-stone-700 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Top remediation</div>
                  <div>
                    {data.route_telemetry_remediation.recommended_actions[0] ??
                      'No remediation steps are blocking cheap-first Gemini/NewAPI routing.'}
                  </div>
                </div>
                <div>
                  <div className="mb-1 font-semibold text-stone-950">Execution boundary</div>
                  <div>
                    config written {data.route_telemetry_remediation.summary.configuration_written ? 'yes' : 'no'} / NewAPI
                    called {data.route_telemetry_remediation.summary.newapi_called ? 'yes' : 'no'} / source{' '}
                    {data.route_telemetry_remediation.privacy_boundary.source}
                  </div>
                </div>
              </div>
            </div>
            <div className="mb-3 rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Env</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Current</TableHead>
                    <TableHead>Recommended</TableHead>
                    <TableHead>Change</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryRemediationEnvRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-stone-500">
                        No env suggestions from route telemetry remediation.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryRemediationEnvRows.map((row) => (
                      <TableRow key={`${row.env_var}-${row.task}`}>
                        <TableCell className="font-mono text-xs font-semibold text-stone-950">{row.env_var}</TableCell>
                        <TableCell>{row.task}</TableCell>
                        <TableCell className="max-w-[220px] break-words font-mono text-xs text-stone-700">
                          {row.current_value ?? 'manual'}
                        </TableCell>
                        <TableCell className="max-w-[220px] break-words font-mono text-xs text-stone-700">
                          {row.recommended_value ?? 'manual'}
                        </TableCell>
                        <TableCell>{row.requires_change ? 'review change' : 'keep'}</TableCell>
                        <TableCell className="max-w-[420px] break-words text-xs leading-5 text-stone-600">
                          {row.reason}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Priority</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Recommendation</TableHead>
                    <TableHead>Review</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeTelemetryRemediationRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-stone-500">
                        No remediation steps.
                      </TableCell>
                    </TableRow>
                  ) : (
                    routeTelemetryRemediationRows.map((step) => (
                      <TableRow key={step.id}>
                        <TableCell className="font-mono text-xs font-semibold text-stone-950">
                          {step.priority}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={statusClass(step.severity)}>
                            {step.severity}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-stone-700">{step.task}</TableCell>
                        <TableCell className="max-w-[360px] text-sm leading-5 text-stone-800">
                          <div className="font-semibold text-stone-950">{step.title}</div>
                          <div className="mt-1 break-words">{step.action}</div>
                          {step.recommended_env_assignment && (
                            <div className="mt-1 break-words font-mono text-xs text-stone-600">
                              {step.recommended_env_assignment}
                            </div>
                          )}
                        </TableCell>
                        <TableCell>{step.requires_operator_review ? 'manual' : 'standard'}</TableCell>
                        <TableCell className="max-w-[420px] break-words text-xs leading-5 text-stone-600">
                          {step.reason}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.route_guardrails && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Route guardrails</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.route_guardrails.blocking_check_ids.length} blocking ·{' '}
                  {data.route_guardrails.warning_check_ids.length} warning checks
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.route_guardrails.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.route_guardrails.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.route_guardrails.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-4">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.failure_rate * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">route failures</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.over_budget_route_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">over budget</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {Math.round(data.route_guardrails.summary.operator_review_route_ratio * 100)}%
                </div>
                <div className="mt-1 text-sm text-stone-600">review gated</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.route_guardrails.summary.unknown_price_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">unknown price</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Check</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {routeGuardrailRows.map((check) => (
                    <TableRow key={check.id}>
                      <TableCell className="font-mono text-xs font-semibold text-stone-950">{check.id}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            check.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : check.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {check.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{check.ratio != null ? `${Math.round(check.ratio * 100)}%` : check.value}</TableCell>
                      <TableCell className="max-w-[520px] text-xs leading-5 text-stone-600">{check.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {data?.callsite_audit && (
          <section className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-stone-950">Callsite audit</h2>
                <div className="mt-1 text-sm text-stone-600">
                  {data.callsite_audit.summary.explicit_task_count} explicit /{' '}
                  {data.callsite_audit.summary.callsite_count} service calls
                </div>
              </div>
              <Badge
                variant="outline"
                className={
                  data.callsite_audit.status === 'pass'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : data.callsite_audit.status === 'fail'
                      ? 'border-red-200 bg-red-50 text-red-800'
                      : 'border-amber-200 bg-amber-50 text-amber-900'
                }
              >
                {data.callsite_audit.status}
              </Badge>
            </div>
            <div className="mb-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.missing_task_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">missing tasks</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.with_model_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">explicit models</div>
              </div>
              <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
                <div className="text-2xl font-black text-stone-950">
                  {data.callsite_audit.summary.fail_count}
                </div>
                <div className="mt-1 text-sm text-stone-600">failures</div>
              </div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Callsite</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {callsiteRows.map((row) => (
                    <TableRow key={`${row.file}:${row.line}`}>
                      <TableCell>
                        <div className="font-mono text-xs font-semibold text-stone-950">
                          {row.file}:{row.line}
                        </div>
                        <div className="mt-1 text-xs text-stone-500">{row.function}</div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            row.status === 'pass'
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                              : row.status === 'fail'
                                ? 'border-red-200 bg-red-50 text-red-800'
                                : 'border-amber-200 bg-amber-50 text-amber-900'
                          }
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{row.has_task ? 'explicit' : 'missing'}</TableCell>
                      <TableCell>{row.has_model ? 'explicit' : '-'}</TableCell>
                      <TableCell className="max-w-[420px] text-xs leading-5 text-stone-600">{row.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        <section className="mb-8">
          <h2 className="mb-3 text-xl font-black text-stone-950">Budget policy</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Resolved model</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Max</TableHead>
                  <TableHead>Operator review</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {budgetRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell className="font-mono font-semibold text-stone-950">{row.task}</TableCell>
                    <TableCell>{row.budget_mode}</TableCell>
                    <TableCell className="font-mono text-xs">{row.resolved_model}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[row.cost_tier || ''] ?? ''}>
                        {row.cost_tier || 'unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell>{row.max_cost_tier}</TableCell>
                    <TableCell>{row.requires_operator_review ? 'required' : row.is_over_budget ? 'recommended' : '-'}</TableCell>
                    <TableCell className="max-w-[360px] text-xs text-stone-600">{row.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Capability matrix</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.capability_matrix?.coverage.task_count ?? 0} tasks ·{' '}
                {(data?.capability_matrix?.coverage.recommended_models ?? []).length} recommended models
              </div>
            </div>
            <Badge variant="outline" className="bg-white">
              {data?.capability_matrix?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Recommended</TableHead>
                  <TableHead>Runtime default</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Capabilities</TableHead>
                  <TableHead>Candidates</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {capabilityRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.requirement.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-stone-700">{row.recommended_model}</TableCell>
                    <TableCell>
                      <div className="font-mono text-xs text-stone-700">{row.runtime_default_model}</div>
                      <Badge
                        variant="outline"
                        className={
                          row.runtime_default_is_recommended
                            ? 'mt-1 border-emerald-200 bg-emerald-50 text-emerald-800'
                            : 'mt-1 border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {row.runtime_default_is_recommended ? 'aligned' : 'review'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[row.requirement.max_cost_tier] ?? 'bg-white'}>
                        max {row.requirement.max_cost_tier}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[240px] text-xs leading-5 text-stone-600">
                      {row.requirement.required_capabilities.join(', ')}
                    </TableCell>
                    <TableCell className="text-stone-700">{row.candidate_count}</TableCell>
                    <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">{row.requirement.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Fallback chains</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.fallback_chains?.summary.chain_count ?? 0} chains /{' '}
                {data?.fallback_chains?.summary.operator_review_step_count ?? 0} operator-review steps
              </div>
            </div>
            <Badge
              variant="outline"
              className={
                data?.fallback_chains?.status === 'pass'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : data?.fallback_chains?.status === 'fail'
                    ? 'border-red-200 bg-red-50 text-red-800'
                    : 'border-amber-200 bg-amber-50 text-amber-900'
              }
            >
              {data?.fallback_chains?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="mb-3 grid gap-3 md:grid-cols-4">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.cheap_primary_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">cheap primaries</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.premium_exception_task_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">premium tasks</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.warn_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">warnings</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.fallback_chains?.summary.fail_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">failures</div>
            </div>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Chain</TableHead>
                  <TableHead>Hard stops</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fallbackChainRows.map((chain) => (
                  <TableRow key={chain.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{chain.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{chain.task}</div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          chain.status === 'pass'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            : chain.status === 'fail'
                              ? 'border-red-200 bg-red-50 text-red-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {chain.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[chain.max_cost_tier] ?? 'bg-white'}>
                        max {chain.max_cost_tier}
                      </Badge>
                      <div className="mt-1 text-xs text-stone-500">{chain.budget_mode}</div>
                    </TableCell>
                    <TableCell className="max-w-[420px]">
                      <div className="space-y-1">
                        {chain.steps.map((step) => (
                          <div key={`${chain.task}-${step.order}`} className="rounded-[6px] border border-stone-950/10 bg-white px-2 py-1">
                            <div className="font-mono text-[11px] text-stone-950">
                              {step.order}. {step.role}: {step.resolved_model}
                            </div>
                            <div className="mt-1 flex flex-wrap gap-1">
                              <Badge variant="outline" className={costClass[step.cost_tier] ?? 'bg-white'}>
                                {step.cost_tier}
                              </Badge>
                              <Badge variant="outline" className="bg-white">
                                {step.latency_tier}
                              </Badge>
                              {step.requires_operator_review && (
                                <Badge variant="outline" className="border-red-200 bg-red-50 text-red-800">
                                  review
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {chain.hard_stop_signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                      {chain.recommended_action}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Routing replay</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.routing_replay?.summary.scenario_count ?? 0} scenarios /{' '}
                {data?.routing_replay?.summary.failed_count ?? 0} failures
              </div>
            </div>
            <Badge
              variant="outline"
              className={
                data?.routing_replay?.status === 'pass'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : data?.routing_replay?.status === 'fail'
                    ? 'border-red-200 bg-red-50 text-red-800'
                    : 'border-amber-200 bg-amber-50 text-amber-900'
              }
            >
              {data?.routing_replay?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="mb-3 grid gap-3 md:grid-cols-4">
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.cheap_start_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">cheap starts</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.premium_operator_review_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">premium reviews</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.hard_stop_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">hard stops</div>
            </div>
            <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6] p-4">
              <div className="text-2xl font-black text-stone-950">
                {data?.routing_replay?.summary.passed_count ?? 0}
              </div>
              <div className="mt-1 text-sm text-stone-600">passed scenarios</div>
            </div>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scenario</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Task</TableHead>
                  <TableHead>Signals</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {routingReplayRows.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      <div className="font-mono text-xs font-semibold text-stone-950">{row.id}</div>
                      <div className="mt-1 max-w-[320px] text-xs leading-5 text-stone-600">
                        {row.scenario.rationale}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          row.status === 'pass'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            : row.status === 'fail'
                              ? 'border-red-200 bg-red-50 text-red-800'
                              : 'border-amber-200 bg-amber-50 text-amber-900'
                        }
                      >
                        {row.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-stone-700">{row.scenario.task}</TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {row.scenario.signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.actual.decision ?? '-'}</div>
                      <div className="mt-1 text-xs text-stone-500">expected {row.scenario.expected_decision}</div>
                    </TableCell>
                    <TableCell className="max-w-[240px]">
                      <div className="font-mono text-xs text-stone-700">{row.actual.resolved_model ?? 'no spend'}</div>
                      <Badge variant="outline" className={`mt-1 ${costClass[row.actual.cost_tier] ?? 'bg-white'}`}>
                        {row.actual.cost_tier}
                      </Badge>
                      {row.actual.requires_operator_review && (
                        <div className="mt-1 text-[11px] font-semibold text-red-700">operator review</div>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[320px] text-xs leading-5 text-stone-600">
                      {row.recommended_action}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Escalation policy</h2>
              <div className="mt-1 text-sm text-stone-600">
                {data?.escalation_policy?.coverage.plan_count ?? 0} plans · max{' '}
                {data?.escalation_policy?.coverage.max_attempts ?? 0} attempts
              </div>
            </div>
            <Badge variant="outline" className="bg-white">
              {data?.escalation_policy?.status ?? 'not loaded'}
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Task</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>Quality signals</TableHead>
                  <TableHead>Hard stops</TableHead>
                  <TableHead>Rationale</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {escalationRows.map((plan) => (
                  <TableRow key={plan.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{plan.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{plan.task}</div>
                    </TableCell>
                    <TableCell className="max-w-[320px]">
                      <div className="space-y-1">
                        {plan.steps.map((step) => (
                          <div key={`${plan.task}-${step.order}`} className="rounded-[6px] border border-stone-950/10 bg-white px-2 py-1">
                            <div className="font-mono text-[11px] text-stone-950">
                              {step.order}. {step.mode}: {step.resolved_model}
                            </div>
                            {step.requires_operator_review && (
                              <div className="mt-1 text-[11px] font-semibold text-red-700">operator review</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                      {plan.quality_signals.join(', ')}
                    </TableCell>
                    <TableCell className="max-w-[220px] text-xs leading-5 text-stone-600">
                      {plan.hard_stop_signals.join(', ') || '-'}
                    </TableCell>
                    <TableCell className="max-w-[360px] text-xs leading-5 text-stone-600">{plan.rationale}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-stone-950">Cost forecast</h2>
              <div className="mt-1 text-sm text-stone-600">
                cheap-first {formatUsd(data?.cost_forecast?.summary.cheap_first_monthly_cost_usd)} / premium baseline{' '}
                {formatUsd(data?.cost_forecast?.summary.premium_baseline_monthly_cost_usd)}
              </div>
            </div>
            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
              saves {Math.round((data?.cost_forecast?.summary.estimated_savings_ratio ?? 0) * 100)}%
            </Badge>
          </div>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Profile</TableHead>
                  <TableHead>Models</TableHead>
                  <TableHead>Monthly volume</TableHead>
                  <TableHead>Cheap-first</TableHead>
                  <TableHead>Premium baseline</TableHead>
                  <TableHead>Savings</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {forecastRows.map((row) => (
                  <TableRow key={row.task}>
                    <TableCell>
                      <div className="font-semibold text-stone-950">{row.profile.display_name}</div>
                      <div className="mt-1 font-mono text-[11px] text-stone-500">{row.task}</div>
                    </TableCell>
                    <TableCell className="max-w-[260px] text-xs leading-5 text-stone-600">
                      start {row.initial_model}
                      <br />
                      up {row.escalation_model}
                    </TableCell>
                    <TableCell className="text-xs leading-5 text-stone-600">
                      {formatNumber(row.profile.monthly_units)} units
                      <br />
                      {Math.round(row.profile.expected_escalation_rate * 100)}% escalation
                    </TableCell>
                    <TableCell>{formatUsd(row.cheap_first_monthly_cost_usd)}</TableCell>
                    <TableCell>{formatUsd(row.premium_baseline_monthly_cost_usd)}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800">
                        {Math.round((row.estimated_savings_ratio ?? 0) * 100)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[340px] text-xs leading-5 text-stone-600">{row.recommended_action}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="mb-3 text-xl font-black text-stone-950">Model catalog</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Context</TableHead>
                  <TableHead>Token price</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Best for</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data?.models ?? []).map((model) => (
                  <TableRow key={model.id}>
                    <TableCell className="font-mono font-semibold text-stone-950">{model.id}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={costClass[model.cost_tier] ?? ''}>
                        {model.cost_tier}
                      </Badge>
                    </TableCell>
                    <TableCell>{model.latency_tier}</TableCell>
                    <TableCell>{model.status}</TableCell>
                    <TableCell>{model.context_window_tokens ? formatNumber(model.context_window_tokens) : '-'}</TableCell>
                    <TableCell className="text-xs text-stone-600">
                      {pricingText(model)}
                    </TableCell>
                    <TableCell>{roleText(model)}</TableCell>
                    <TableCell className="max-w-[320px] text-stone-600">{model.best_for.join(', ')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-black text-stone-950">Usage counters</h2>
          <div className="rounded-[8px] border border-stone-950/15 bg-[#fbfaf6]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Requests</TableHead>
                  <TableHead>Success</TableHead>
                  <TableHead>Failure</TableHead>
                  <TableHead>Total tokens</TableHead>
                  <TableHead>Est. cost</TableHead>
                  <TableHead>Avg latency</TableHead>
                  <TableHead>Tasks</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usageRows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-8 text-center text-stone-500">
                      No model calls recorded in this backend process.
                    </TableCell>
                  </TableRow>
                ) : (
                  usageRows.map(([model, usage]) => (
                    <TableRow key={model}>
                      <TableCell className="font-mono font-semibold text-stone-950">{model}</TableCell>
                      <TableCell>{formatNumber(usage.requests)}</TableCell>
                      <TableCell>{formatNumber(usage.successes)}</TableCell>
                      <TableCell>{formatNumber(usage.failures)}</TableCell>
                      <TableCell>{formatNumber(usage.total_tokens)}</TableCell>
                      <TableCell>{formatUsd(usage.estimated_cost_usd)}</TableCell>
                      <TableCell>{usage.avg_latency_ms}ms</TableCell>
                      <TableCell className="max-w-[320px] text-stone-600">
                        {Object.entries(usage.tasks).map(([task, count]) => `${task}:${count}`).join(', ')}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </section>
      </div>
    </Layout>
  );
}
