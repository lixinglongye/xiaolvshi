import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const files = {
  packageJson: 'package.json',
  maintenancePage: 'src/pages/MaintenanceEvidencePage.tsx',
  modelOpsPage: 'src/pages/ModelOpsPage.tsx',
  maintenanceApi: 'src/lib/maintenanceApi.ts',
  modelOpsApi: 'src/lib/modelOpsApi.ts',
};

function read(relativePath) {
  return readFileSync(resolve(root, relativePath), 'utf8');
}

function assertIncludes(source, needle, label) {
  if (!source.includes(needle)) {
    throw new Error(`${label}: expected to find "${needle}"`);
  }
}

function assertNotMatches(source, pattern, label) {
  if (pattern.test(source)) {
    throw new Error(`${label}: forbidden pattern ${pattern} matched`);
  }
}

function assertBefore(source, firstNeedle, secondNeedle, label) {
  const firstIndex = source.indexOf(firstNeedle);
  const secondIndex = source.indexOf(secondNeedle);
  if (firstIndex === -1 || secondIndex === -1 || firstIndex >= secondIndex) {
    throw new Error(`${label}: expected "${firstNeedle}" before "${secondNeedle}"`);
  }
}

const packageJson = JSON.parse(read(files.packageJson));
const maintenancePage = read(files.maintenancePage);
const modelOpsPage = read(files.modelOpsPage);
const maintenanceApi = read(files.maintenanceApi);
const modelOpsApi = read(files.modelOpsApi);
const relevantSources = [
  maintenancePage,
  modelOpsPage,
  maintenanceApi,
  modelOpsApi,
].join('\n');

const requiredScripts = ['lint', 'typecheck', 'build', 'ui:regression'];
for (const script of requiredScripts) {
  if (!packageJson.scripts?.[script]) {
    throw new Error(`package scripts: missing ${script}`);
  }
}

const checks = [
  () => assertIncludes(maintenancePage, 'runMaintenanceLoadTask', 'maintenance partial-load resilience'),
  () => assertIncludes(maintenancePage, 'MAINTENANCE_TASK_TIMEOUT_MS', 'maintenance request timeout guard'),
  () => assertIncludes(maintenancePage, 'task.apply(await runMaintenanceLoadTask(task))', 'maintenance incremental render'),
  () => assertIncludes(maintenancePage, 'Partial maintenance evidence loaded', 'maintenance partial-load banner'),
  () => assertIncludes(maintenancePage, 'Frontend UI regression gate', 'maintenance UI gate panel'),
  () => assertIncludes(maintenancePage, 'Low-resource fixture review', 'maintenance review packet fixture panel'),
  () => assertIncludes(maintenancePage, 'raw fixture payload echoed: false', 'maintenance fixture privacy boundary'),
  () => assertIncludes(maintenancePage, 'Local run review status', 'maintenance local run review status panel'),
  () => assertIncludes(maintenancePage, 'evidence bundle status', 'maintenance local run review evidence status'),
  () => assertIncludes(maintenancePage, 'blocking checks', 'maintenance local run review blocker count'),
  () => assertIncludes(maintenancePage, 'Ledger fixture evidence', 'maintenance ledger fixture evidence panel'),
  () => assertIncludes(maintenancePage, 'archive summaries only: true', 'maintenance ledger fixture archive-only boundary'),
  () => assertIncludes(maintenancePage, 'updates count mutated: false', 'maintenance ledger fixture non-mutating summary'),
  () => assertIncludes(maintenancePage, 'Run monitor fixture evidence', 'maintenance run monitor fixture evidence panel'),
  () => assertIncludes(maintenancePage, 'postMaintenanceContinuousSessionRunMonitor', 'maintenance run monitor fixture review API binding'),
  () => assertIncludes(maintenancePage, 'completion ready mutated: false', 'maintenance run monitor fixture non-completion boundary'),
  () => assertIncludes(maintenancePage, 'User need benchmark coverage', 'user need benchmark coverage panel'),
  () => assertIncludes(maintenancePage, 'Public benchmark review gaps', 'user need benchmark public review gap panel'),
  () => assertIncludes(maintenancePage, 'public sampler network', 'user need benchmark public sampler boundary'),
  () => assertIncludes(maintenancePage, 'public_benchmark_status', 'user need benchmark public status binding'),
  () => assertIncludes(maintenancePage, 'Calibration attention gaps', 'user need benchmark calibration attention panel'),
  () => assertIncludes(maintenancePage, 'cheap-first calibration', 'user need benchmark calibration summary'),
  () => assertIncludes(maintenancePage, 'linked_calibration_task_ids', 'user need benchmark calibration task binding'),
  () => assertIncludes(maintenancePage, 'Legal document benchmark coverage', 'legal document benchmark coverage panel'),
  () => assertIncludes(maintenancePage, 'returns_raw_model_output', 'maintenance privacy boundary'),
  () => assertIncludes(maintenanceApi, 'linked_public_source_ids', 'user need benchmark public source type'),
  () => assertIncludes(maintenanceApi, 'returns_public_benchmark_text', 'user need benchmark public text boundary type'),
  () => assertIncludes(maintenanceApi, 'public_sampler_network_access', 'user need benchmark public sampler summary type'),
  () => assertIncludes(maintenanceApi, 'linked_calibration_task_ids', 'user need benchmark calibration task type'),
  () => assertIncludes(maintenanceApi, 'returns_calibration_payloads', 'user need benchmark calibration payload boundary type'),
  () => assertIncludes(maintenanceApi, 'cheap_first_calibration_mapped_need_count', 'user need benchmark calibration summary type'),
  () => assertIncludes(maintenanceApi, 'low_resource_fixture_review_status', 'maintenance review packet fixture status type'),
  () => assertIncludes(maintenanceApi, 'raw_gateway_response_included', 'maintenance fixture raw gateway boundary type'),
  () => assertIncludes(maintenanceApi, 'reviewLegalFixtureLocalRun', 'maintenance local run review API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/local-run-review', 'maintenance local run review endpoint'),
  () => assertIncludes(maintenanceApi, 'reviewContinuousUpdateLedger', 'maintenance continuous ledger review API binding'),
  () => assertIncludes(maintenanceApi, 'low_resource_fixture_evidence', 'maintenance continuous ledger fixture evidence type'),
  () => assertIncludes(maintenanceApi, 'MaintenanceLowResourceFixtureEvidence', 'maintenance shared fixture evidence type'),
  () => assertIncludes(maintenanceApi, 'low_resource_fixture_evidence_status', 'maintenance run monitor fixture evidence status type'),
  () => assertIncludes(maintenanceApi, 'getFrontendUiRegressionGate', 'frontend UI gate API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/frontend-ui-regression-gate', 'frontend UI gate endpoint'),
  () => assertIncludes(modelOpsPage, 'Promise.allSettled', 'model-ops partial-load resilience'),
  () => assertIncludes(modelOpsPage, 'ModelOps load guard', 'model-ops performance budget panel'),
  () => assertIncludes(modelOpsPage, 'Performance observations', 'model-ops performance observation review form'),
  () => assertIncludes(modelOpsPage, 'Evaluate observations', 'model-ops performance observation submit button'),
  () => assertIncludes(modelOpsPage, 'fallback_after_timeout_disabled', 'model-ops timeout fallback summary binding'),
  () => assertIncludes(modelOpsPage, 'same-origin fetch first', 'model-ops same-origin fetch budget card'),
  () => assertIncludes(modelOpsPage, 'duplicate calibration fetch', 'model-ops duplicate calibration fetch summary'),
  () => assertIncludes(modelOpsPage, 'Cheap-first quality budget', 'model-ops route quality budget panel'),
  () => assertIncludes(modelOpsPage, 'routeQualityRows', 'model-ops route quality row binding'),
  () => assertIncludes(modelOpsPage, 'quality gates', 'model-ops route quality gate copy'),
  () => assertIncludes(modelOpsPage, 'modelOpsPerformanceRows', 'model-ops performance check row binding'),
  () => assertIncludes(modelOpsPage, 'Route telemetry', 'model-ops route telemetry panel'),
  () => assertIncludes(modelOpsPage, 'cheap-first', 'model-ops cheap-first copy'),
  () => assertIncludes(modelOpsPage, 'Gemini variant matrix', 'model-ops Gemini variant matrix panel'),
  () => assertIncludes(modelOpsPage, 'Gemini catalog source audit', 'model-ops Gemini catalog source audit panel'),
  () => assertIncludes(modelOpsPage, 'Cheap-first release decision', 'model-ops cheap-first release decision panel'),
  () => assertIncludes(modelOpsPage, 'cheapFirstDecisionChecks', 'model-ops cheap-first decision row binding'),
  () => assertIncludes(modelOpsPage, 'Default change queue', 'model-ops default change queue panel'),
  () => assertIncludes(modelOpsPage, 'defaultChangeQueueRows', 'model-ops default change queue row binding'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops default change queue write boundary'),
  () => assertIncludes(modelOpsPage, 'automatic_default_change_claimed', 'model-ops default change queue auto-change non-claim'),
  () => assertIncludes(modelOpsPage, 'Cheap-first canary plan', 'model-ops cheap-first canary plan panel'),
  () => assertIncludes(modelOpsPage, 'cheapFirstCanarySteps', 'model-ops cheap-first canary step binding'),
  () => assertIncludes(modelOpsPage, 'rollback_trigger_ids', 'model-ops cheap-first canary rollback binding'),
  () => assertIncludes(modelOpsPage, 'automatic_canary_rollout_claimed', 'model-ops cheap-first canary non-claim'),
  () => assertIncludes(modelOpsPage, 'traffic_shifted', 'model-ops cheap-first canary traffic boundary'),
  () => assertIncludes(modelOpsPage, 'Cheap-first canary observation review', 'model-ops canary observation panel'),
  () => assertIncludes(modelOpsPage, 'canaryObservationRows', 'model-ops canary observation row binding'),
  () => assertIncludes(modelOpsPage, 'Evaluate canary observations', 'model-ops canary observation submit button'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenCanaryObservationPayloadText', 'model-ops canary observation payload guard'),
  () => assertIncludes(modelOpsPage, 'raw payload echoed', 'model-ops canary observation raw-payload boundary'),
  () => assertIncludes(modelOpsPage, 'Cheap-first canary promotion decision', 'model-ops canary promotion decision panel'),
  () => assertIncludes(modelOpsPage, 'canaryPromotionRows', 'model-ops canary promotion row binding'),
  () => assertIncludes(modelOpsPage, 'promotion_items', 'model-ops canary promotion item binding'),
  () => assertIncludes(modelOpsPage, 'advance_next_batch', 'model-ops canary promotion advance status'),
  () => assertIncludes(modelOpsPage, 'rollback_required', 'model-ops canary promotion rollback status'),
  () => assertIncludes(modelOpsPage, 'configuration_change_allowed', 'model-ops canary promotion config boundary'),
  () => assertIncludes(modelOpsPage, 'traffic_shift_allowed', 'model-ops canary promotion traffic boundary'),
  () => assertIncludes(modelOpsPage, 'Cheap-first canary approval packet', 'model-ops canary approval packet panel'),
  () => assertIncludes(modelOpsPage, 'canaryApprovalRows', 'model-ops canary approval row binding'),
  () => assertIncludes(modelOpsPage, 'approval_items', 'model-ops canary approval item binding'),
  () => assertIncludes(modelOpsPage, 'approval_required', 'model-ops canary approval required boundary'),
  () => assertIncludes(modelOpsPage, 'approval_record_written', 'model-ops canary approval no-record boundary'),
  () => assertIncludes(modelOpsPage, 'approver_identity_included', 'model-ops canary approval privacy boundary'),
  () => assertIncludes(modelOpsPage, 'rollback_review_required', 'model-ops canary approval rollback status'),
  () => assertIncludes(modelOpsPage, 'default_promotion_blocked', 'model-ops cheap-first default promotion boundary'),
  () => assertIncludes(modelOpsPage, 'maintainer_review_required', 'model-ops cheap-first maintainer review boundary'),
  () => assertIncludes(modelOpsPage, 'current_cheap_first_default_allowed', 'model-ops cheap-first current default decision'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed', 'model-ops cheap-first default change decision'),
  () => assertIncludes(modelOpsPage, 'Claim boundary', 'model-ops cheap-first claim boundary panel'),
  () => assertIncludes(modelOpsPage, 'public benchmark scores', 'model-ops cheap-first public benchmark non-claim'),
  () => assertIncludes(modelOpsPage, 'twenty_four_hour_completion_claimed', 'model-ops cheap-first 24h non-claim'),
  () => assertIncludes(modelOpsPage, 'raw model output', 'model-ops cheap-first raw-output privacy boundary'),
  () => assertIncludes(modelOpsPage, 'Official source review', 'model-ops Gemini catalog official source review'),
  () => assertIncludes(modelOpsPage, 'catalogSourceRows', 'model-ops Gemini catalog source row binding'),
  () => assertIncludes(modelOpsPage, 'catalog_source_audit', 'model-ops Gemini catalog source audit response binding'),
  () => assertIncludes(modelOpsPage, 'Prefix compatibility', 'model-ops Gemini prefix compatibility panel'),
  () => assertIncludes(modelOpsPage, 'Observed model review', 'model-ops Gemini observed model review form'),
  () => assertIncludes(modelOpsPage, 'models_response', 'model-ops Gemini model-list response template'),
  () => assertIncludes(modelOpsPage, 'source fields:', 'model-ops Gemini model-list extraction summary'),
  () => assertIncludes(modelOpsPage, 'evaluateGeminiVariantPayload', 'model-ops Gemini variant review submit handler'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenGeminiVariantPayloadText', 'model-ops Gemini variant payload guard'),
  () => assertIncludes(modelOpsPage, 'gateway called: {String(activeGeminiVariantMatrix.privacy_boundary.gateway_called)}', 'model-ops Gemini variant privacy boundary'),
  () => assertIncludes(modelOpsPage, 'geminiVariantRows', 'model-ops Gemini variant row binding'),
  () => assertIncludes(modelOpsPage, 'Calibration payload', 'model-ops cheap-first payload evaluator'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenCheapFirstPayloadText', 'model-ops cheap-first payload guard'),
  () => assertIncludes(modelOpsPage, 'blocked payload fields', 'model-ops cheap-first backend payload safety summary'),
  () => assertIncludes(modelOpsPage, 'research sources', 'model-ops cheap-first research source summary'),
  () => assertIncludes(modelOpsPage, 'external_research_mappings', 'model-ops cheap-first research mapping binding'),
  () => assertIncludes(modelOpsPage, 'route_telemetry_remediation', 'model-ops route remediation binding'),
  () => assertIncludes(modelOpsApi, 'evaluateCheapFirstCalibration', 'model-ops cheap-first evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-calibration', 'model-ops cheap-first calibration endpoint'),
  () => assertIncludes(modelOpsApi, 'MODEL_OPS_API_TIMEOUT_MS', 'model-ops API timeout guard'),
  () => assertIncludes(modelOpsApi, 'MODEL_OPS_TOTAL_TIMEOUT_MS', 'model-ops wall-clock timeout guard'),
  () => assertIncludes(modelOpsApi, 'isModelOpsTimeoutError', 'model-ops timeout fallback guard'),
  () => assertIncludes(modelOpsApi, 'AbortController', 'model-ops fetch abort guard'),
  () => assertIncludes(modelOpsApi, 'fetchModelOpsApi', 'model-ops same-origin fetch helper'),
  () => assertIncludes(modelOpsApi, 'same_origin_fetch_first', 'model-ops same-origin fetch budget type'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsPerformanceBudget', 'model-ops performance budget evaluation API'),
  () => assertIncludes(modelOpsApi, 'fallback_after_timeout_disabled', 'model-ops timeout fallback disabled type'),
  () => assertBefore(modelOpsApi, 'return await fetchModelOpsApi<T>(request);', 'client.apiCall.invoke', 'model-ops same-origin fetch before SDK fallback'),
  () => assertIncludes(modelOpsApi, 'ModelOpsPerformanceBudget', 'model-ops performance budget type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstReleaseDecision', 'model-ops cheap-first release decision type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsDefaultChangeQueue', 'model-ops default change queue type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsDefaultChangeQueue', 'model-ops default change queue API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/default-change-queue', 'model-ops default change queue endpoint'),
  () => assertIncludes(modelOpsApi, 'default_change_queue', 'model-ops default change queue response binding'),
  () => assertIncludes(modelOpsApi, 'queue_items', 'model-ops default change queue payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryPlan', 'model-ops cheap-first canary plan type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCanaryPlan', 'model-ops cheap-first canary plan API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-plan', 'model-ops cheap-first canary plan endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_plan', 'model-ops cheap-first canary plan response binding'),
  () => assertIncludes(modelOpsApi, 'canary_steps', 'model-ops cheap-first canary payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryObservation', 'model-ops canary observation type'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsCheapFirstCanaryObservation', 'model-ops canary observation evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-observation', 'model-ops canary observation endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_observation', 'model-ops canary observation response binding'),
  () => assertIncludes(modelOpsApi, 'observation_rows', 'model-ops canary observation payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryPromotionDecision', 'model-ops canary promotion decision type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCanaryPromotionDecision', 'model-ops canary promotion decision API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-promotion-decision', 'model-ops canary promotion decision endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_promotion_decision', 'model-ops canary promotion decision response binding'),
  () => assertIncludes(modelOpsApi, 'promotion_items', 'model-ops canary promotion payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryApprovalPacket', 'model-ops canary approval packet type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCanaryApprovalPacket', 'model-ops canary approval packet API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-approval-packet', 'model-ops canary approval packet endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_approval_packet', 'model-ops canary approval packet response binding'),
  () => assertIncludes(modelOpsApi, 'approval_items', 'model-ops canary approval payload guard'),
  () => assertIncludes(modelOpsApi, 'claim_boundary', 'model-ops cheap-first release decision claim boundary type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstReleaseDecision', 'model-ops cheap-first release decision API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-release-decision', 'model-ops cheap-first release decision endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_release_decision', 'model-ops cheap-first release decision response binding'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/performance-budget', 'model-ops performance budget endpoint'),
  () => assertIncludes(modelOpsApi, 'ModelRouteQualityBudget', 'model-ops route quality budget type'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/route-quality-budget', 'model-ops route quality budget endpoint'),
  () => assertIncludes(modelOpsApi, 'GeminiVariantMatrix', 'model-ops Gemini variant matrix type'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogSourceAudit', 'model-ops Gemini catalog source audit type'),
  () => assertIncludes(modelOpsApi, 'getModelCatalogSourceAudit', 'model-ops Gemini catalog source audit API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/catalog-source-audit', 'model-ops Gemini catalog source audit endpoint'),
  () => assertIncludes(modelOpsApi, 'catalog_source_audit', 'model-ops Gemini catalog source audit response binding'),
  () => assertIncludes(modelOpsApi, 'GeminiVariantMatrixObservedModelExtraction', 'model-ops Gemini extraction summary type'),
  () => assertIncludes(modelOpsApi, 'source_summaries', 'model-ops Gemini source summaries binding'),
  () => assertIncludes(modelOpsApi, 'evaluateGeminiVariantMatrix', 'model-ops Gemini variant matrix evaluation API'),
  () => assertIncludes(modelOpsApi, 'gemini_variant_matrix', 'model-ops Gemini variant matrix response binding'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-variant-matrix', 'model-ops Gemini variant matrix endpoint'),
  () => assertIncludes(modelOpsApi, 'external_research_mappings', 'model-ops cheap-first research mapping type'),
];

for (const check of checks) {
  check();
}

assertNotMatches(relevantSources, /\bsk-[A-Za-z0-9]{20,}\b/, 'frontend UI regression sources');
assertNotMatches(relevantSources, /raw private narrative/i, 'frontend UI regression sources');
assertNotMatches(relevantSources, /client@example\.com/i, 'frontend UI regression sources');

console.log(
  JSON.stringify(
    {
      status: 'pass',
      checked_files: Object.values(files).filter((file) => file !== 'package.json'),
      command_gates: requiredScripts,
      assertions: checks.length + 3,
    },
    null,
    2,
  ),
);
