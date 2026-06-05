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
  () => assertIncludes(maintenancePage, 'User need benchmark coverage', 'user need benchmark coverage panel'),
  () => assertIncludes(maintenancePage, 'Legal document benchmark coverage', 'legal document benchmark coverage panel'),
  () => assertIncludes(maintenancePage, 'returns_raw_model_output', 'maintenance privacy boundary'),
  () => assertIncludes(maintenanceApi, 'getFrontendUiRegressionGate', 'frontend UI gate API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/frontend-ui-regression-gate', 'frontend UI gate endpoint'),
  () => assertIncludes(modelOpsPage, 'Promise.allSettled', 'model-ops partial-load resilience'),
  () => assertIncludes(modelOpsPage, 'Route telemetry', 'model-ops route telemetry panel'),
  () => assertIncludes(modelOpsPage, 'cheap-first', 'model-ops cheap-first copy'),
  () => assertIncludes(modelOpsPage, 'research sources', 'model-ops cheap-first research source summary'),
  () => assertIncludes(modelOpsPage, 'external_research_mappings', 'model-ops cheap-first research mapping binding'),
  () => assertIncludes(modelOpsPage, 'route_telemetry_remediation', 'model-ops route remediation binding'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-calibration', 'model-ops cheap-first calibration endpoint'),
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
