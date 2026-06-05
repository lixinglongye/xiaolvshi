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
  () => assertIncludes(modelOpsPage, 'Route telemetry', 'model-ops route telemetry panel'),
  () => assertIncludes(modelOpsPage, 'cheap-first', 'model-ops cheap-first copy'),
  () => assertIncludes(modelOpsPage, 'Gemini variant matrix', 'model-ops Gemini variant matrix panel'),
  () => assertIncludes(modelOpsPage, 'Prefix compatibility', 'model-ops Gemini prefix compatibility panel'),
  () => assertIncludes(modelOpsPage, 'Observed model review', 'model-ops Gemini observed model review form'),
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
  () => assertIncludes(modelOpsApi, 'GeminiVariantMatrix', 'model-ops Gemini variant matrix type'),
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
