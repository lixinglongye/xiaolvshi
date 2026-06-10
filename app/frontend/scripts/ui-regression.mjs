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
  workbenchRuntimeApi: 'src/lib/workbenchRuntimeApi.ts',
  feedbackApi: 'src/lib/feedbackApi.ts',
  feedbackCapturePanel: 'src/components/feedback/FeedbackCapturePanel.tsx',
  caseWorkbenchRuntimePanel: 'src/components/cases/CaseWorkbenchRuntimePanel.tsx',
  caseDetailPage: 'src/pages/CaseDetailPage.tsx',
  deepReportPage: 'src/pages/DeepReportPage.tsx',
  settingsPage: 'src/pages/SettingsPage.tsx',
  adminPage: 'src/pages/AdminPage.tsx',
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

function sourceSection(source, startNeedle, endNeedle, label) {
  const startIndex = source.indexOf(startNeedle);
  const endIndex = source.indexOf(endNeedle, Math.max(startIndex, 0));
  if (startIndex === -1 || endIndex === -1 || startIndex >= endIndex) {
    throw new Error(`${label}: expected section from "${startNeedle}" to "${endNeedle}"`);
  }
  return source.slice(startIndex, endIndex);
}

const packageJson = JSON.parse(read(files.packageJson));
const maintenancePage = read(files.maintenancePage);
const modelOpsPage = read(files.modelOpsPage);
const maintenanceApi = read(files.maintenanceApi);
const modelOpsApi = read(files.modelOpsApi);
const workbenchRuntimeApi = read(files.workbenchRuntimeApi);
const feedbackApi = read(files.feedbackApi);
const feedbackCapturePanel = read(files.feedbackCapturePanel);
const caseWorkbenchRuntimePanel = read(files.caseWorkbenchRuntimePanel);
const caseDetailPage = read(files.caseDetailPage);
const deepReportPage = read(files.deepReportPage);
const settingsPage = read(files.settingsPage);
const adminPage = read(files.adminPage);
const relevantSources = [
  maintenancePage,
  modelOpsPage,
  maintenanceApi,
  modelOpsApi,
  workbenchRuntimeApi,
  feedbackApi,
  feedbackCapturePanel,
  caseWorkbenchRuntimePanel,
  caseDetailPage,
  deepReportPage,
  settingsPage,
  adminPage,
].join('\n');
const geminiAliasMatrixPanel = sourceSection(
  maintenancePage,
  'Gemini/NewAPI model alias matrix',
  'Gemini/NewAPI selector replay',
  'maintenance Gemini/NewAPI model alias matrix panel',
);
const geminiCheapFirstPolicyPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI cheap-first policy</h2>',
  '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap readiness packet</h2>',
  'maintenance Gemini/NewAPI cheap-first policy panel',
);
const maintenanceNewApiChannelBootstrapPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap readiness packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
  'maintenance NewAPI channel bootstrap readiness packet panel',
);
const maintenanceObservedGeminiCoverageGapQueuePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini premium exception review</h2>',
  'maintenance observed Gemini coverage gap queue panel',
);
const maintenanceObservedGeminiPremiumExceptionReviewPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini premium exception review</h2>',
  '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
  'maintenance observed Gemini premium exception review panel',
);
const modelPriceRefreshMonitorPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
  '<h2 className="text-xl font-black text-stone-950">Model cost regression snapshots</h2>',
  'maintenance model price refresh monitor panel',
);
const modelCostRegressionSnapshotsPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Model cost regression snapshots</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
  'maintenance model cost regression snapshots panel',
);
const maintenanceHeartbeatEvidencePanel = sourceSection(
  maintenancePage,
  'Maintenance heartbeat evidence',
  'Continuous session review packet',
  'maintenance heartbeat evidence panel',
);
const billingEntitlementGapPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Billing entitlement gap</h2>',
  '<h2 className="text-xl font-black text-stone-950">24h evidence timeline</h2>',
  'maintenance billing entitlement gap section',
);
const catalogCandidatePatchPlanPanel = sourceSection(
  modelOpsPage,
  'Model catalog candidate patch plan',
  'Model catalog candidate impact replay',
  'model-ops catalog candidate patch plan section',
);
const geminiOfficialCheapFirstSourceReviewPanel = sourceSection(
  modelOpsPage,
  '{(activeGeminiOfficialCheapFirstSourceReview || geminiOfficialCheapFirstSourceReviewError) && (',
  '{(activeGeminiOfficialLifecycleDriftGate || geminiOfficialLifecycleDriftGateError) && (',
  'model-ops Gemini official cheap-first source review section',
);
const geminiOfficialLifecycleDriftGatePanel = sourceSection(
  modelOpsPage,
  '{(activeGeminiOfficialLifecycleDriftGate || geminiOfficialLifecycleDriftGateError) && (',
  '{(activeGeminiOfficialModelFamilyRoadmapEvidence || geminiOfficialModelFamilyRoadmapEvidenceError) && (',
  'model-ops Gemini official lifecycle drift gate section',
);
const geminiOfficialModelFamilyRoadmapEvidencePanel = sourceSection(
  modelOpsPage,
  '{(activeGeminiOfficialModelFamilyRoadmapEvidence || geminiOfficialModelFamilyRoadmapEvidenceError) && (',
  '{catalogCandidatePatchPlan && (',
  'model-ops Gemini official model family roadmap evidence section',
);
const catalogCandidateImpactReplayPanel = sourceSection(
  modelOpsPage,
  'Model catalog candidate impact replay',
  'Gateway connection profile',
  'model-ops catalog candidate impact replay section',
);
const modelCatalogPanel = sourceSection(
  modelOpsPage,
  '<h2 className="mb-3 text-xl font-black text-stone-950">Model catalog</h2>',
  '<h2 className="mb-3 text-xl font-black text-stone-950">Usage counters</h2>',
  'model-ops model catalog section',
);
const gatewayConnectionProfilePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gateway connection profile</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gateway runtime configuration</h2>',
  'model-ops gateway connection profile section',
);
const gatewayRuntimeConfigurationPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gateway runtime configuration</h2>',
  '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap</h2>',
  'model-ops gateway runtime configuration section',
);
const newapiChannelBootstrapPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gateway health plan</h2>',
  'model-ops NewAPI channel bootstrap section',
);
const gatewayHealthPlanPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gateway health plan</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gateway probe runbook gate</h2>',
  'model-ops gateway health plan section',
);
const gatewayProbeRunbookGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gateway probe runbook gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gateway probe evaluation</h2>',
  'model-ops gateway probe runbook gate section',
);
const geminiAliasCapabilityCoveragePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
  'model-ops Gemini/NewAPI alias capability coverage section',
);
const geminiNewApiModelSelectorPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
  'model-ops Gemini/NewAPI model selector section',
);
const modelDefaultCandidateSelectorPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Model default candidate selector</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
  'model-ops model default candidate selector section',
);
const geminiNewApiSelectorReplayPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI selector replay</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
  'model-ops Gemini/NewAPI selector replay section',
);
const aihubMediaSpeechDefaultCatalogGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">AIHub media/speech default catalog gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">AIHub media runtime compatibility gate</h2>',
  'model-ops AIHub media/speech default catalog gate section',
);
const aihubMediaRuntimeCompatibilityGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">AIHub media runtime compatibility gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
  'model-ops AIHub media runtime compatibility gate section',
);
const geminiEmbeddingCheapFirstPreflightPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
  '<h2 className="text-xl font-black text-stone-950">AIHub gentxt routing guard</h2>',
  'model-ops Gemini embedding cheap-first preflight section',
);
const observedGeminiCoverageGapQueuePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
  'model-ops observed Gemini coverage gap queue section',
);
const modelOpsUserNeedReleaseBridgePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">ModelOps user-need release bridge</h2>',
  '<h2 className="text-xl font-black text-stone-950">ModelOps user-need Gemini route coverage</h2>',
  'model-ops user-need release bridge section',
);
const modelOpsUserNeedGeminiRouteCoveragePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">ModelOps user-need Gemini route coverage</h2>',
  '<h2 className="text-xl font-black text-stone-950">ModelOps user-need cheap-first handoff</h2>',
  'model-ops user-need Gemini route coverage section',
);
const modelOpsUserNeedCheapFirstHandoffPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">ModelOps user-need cheap-first handoff</h2>',
  '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
  'model-ops user-need cheap-first handoff section',
);
const modelOpsCheapFirstCascadeResearchGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Cheap-first cascade research gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
  'model-ops cheap-first cascade research gate section',
);
const caseWorkbenchRiskRefreshPanel = sourceSection(
  caseWorkbenchRuntimePanel,
  'Risk refresh plan',
  '<form onSubmit={submitTaskEvent}',
  'case workbench risk refresh plan section',
);
const caseExportReadinessPayloadBuilder = sourceSection(
  caseDetailPage,
  'function buildCaseExportReadinessPayload',
  'export default function CaseDetailPage',
  'case detail export readiness payload builder',
);
const caseExportReadinessDownloadGuard = sourceSection(
  caseDetailPage,
  'const runExportReadinessThenDownload',
  'const emitMaterialRuntimeEvent',
  'case detail export readiness download guard',
);
const caseExportReadinessApiCall = sourceSection(
  caseExportReadinessDownloadGuard,
  'const readiness = await getMaintenanceCaseExportReadiness(',
  'setExportReadiness(readiness);',
  'case detail export readiness API call',
);
const settingsAiModelProviderSection = sourceSection(
  settingsPage,
  'AI model provider',
  '<FeedbackCapturePanel />',
  'settings AI model provider section',
);
const settingsFeedbackCaptureSection = feedbackCapturePanel;

const requiredScripts = ['lint', 'typecheck', 'build', 'ui:regression'];
for (const script of requiredScripts) {
  if (!packageJson.scripts?.[script]) {
    throw new Error(`package scripts: missing ${script}`);
  }
}

const checks = [
  () => assertIncludes(maintenancePage, 'runMaintenanceLoadTask', 'maintenance partial-load resilience'),
  () => assertIncludes(maintenancePage, 'MAINTENANCE_LOAD_CONCURRENCY', 'maintenance limited-concurrency load guard'),
  () => assertIncludes(maintenancePage, 'MAINTENANCE_TASK_TIMEOUT_MS', 'maintenance request timeout guard'),
  () => assertIncludes(maintenancePage, 'task.apply(await runMaintenanceLoadTask(task))', 'maintenance incremental render'),
  () => assertIncludes(maintenancePage, 'Partial maintenance evidence loaded', 'maintenance partial-load banner'),
  () => assertIncludes(maintenancePage, 'Frontend UI regression gate', 'maintenance UI gate panel'),
  () => assertIncludes(maintenanceApi, 'GeminiNewApiCheapFirstPolicy', 'maintenance Gemini/NewAPI cheap-first policy type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'GeminiNewApiCheapFirstPolicyFamily',
      'maintenance Gemini/NewAPI cheap-first family type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'GeminiNewApiCheapFirstPolicyRecommendation',
      'maintenance Gemini/NewAPI cheap-first recommendation type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getGeminiNewApiCheapFirstPolicyEvidence',
      'maintenance Gemini/NewAPI cheap-first policy getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'postGeminiNewApiCheapFirstPolicyEvidence',
      'maintenance Gemini/NewAPI cheap-first policy evaluator',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/gemini-newapi-cheap-first-policy',
      'maintenance Gemini/NewAPI cheap-first policy endpoint',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'supported_gemini_model_families',
      'maintenance Gemini/NewAPI cheap-first family payload binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'default_model_recommendations',
      'maintenance Gemini/NewAPI cheap-first recommendation payload binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'forbidden_default_rules',
      'maintenance Gemini/NewAPI cheap-first forbidden rule payload binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'observed_model_review',
      'maintenance Gemini/NewAPI cheap-first observed review payload binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getGeminiNewApiCheapFirstPolicyEvidence',
      'maintenance Gemini/NewAPI cheap-first policy load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'geminiNewApiCheapFirstPolicy',
      'maintenance Gemini/NewAPI cheap-first policy state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'Gemini/NewAPI cheap-first policy',
      'maintenance Gemini/NewAPI cheap-first policy panel',
    ),
  () => assertIncludes(maintenancePage, 'supported_gemini_model_families', 'maintenance Gemini family row binding'),
  () => assertIncludes(maintenancePage, 'default_model_recommendations', 'maintenance Gemini default recommendation binding'),
  () => assertIncludes(maintenancePage, 'newapi_openai_compatible_prefix_compatibility', 'maintenance NewAPI prefix binding'),
  () => assertIncludes(maintenancePage, 'forbidden_default_rules', 'maintenance Gemini forbidden rules binding'),
  () => assertIncludes(maintenancePage, 'unknown_gemini_like_model_handling', 'maintenance unknown Gemini handling binding'),
  () => assertIncludes(maintenancePage, 'gemini-flash-lite', 'maintenance Gemini Flash-Lite policy signal'),
  () =>
    assertIncludes(
      maintenancePage,
      'no_premium_or_preview_high_frequency_default',
      'maintenance Gemini premium default block signal',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'unknown_gemini_like_needs_catalog_review',
      'maintenance unknown Gemini catalog review signal',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI cheap-first policy</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      'maintenance model price refresh follows Gemini cheap-first policy',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model cost regression snapshots</h2>',
      'maintenance model cost regression follows Gemini cheap-first policy',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Model cost regression snapshots</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
      'maintenance model cost regression precedes selector',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI cheap-first policy</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model alias matrix</h2>',
      'maintenance Gemini cheap-first policy precedes alias matrix',
    ),
  () =>
    assertNotMatches(
      geminiCheapFirstPolicyPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|request_body|response_body|gateway_response|headers/i,
      'maintenance Gemini/NewAPI cheap-first policy sensitive field guard',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceNewApiChannelBootstrap',
      'maintenance NewAPI channel bootstrap type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceNewApiChannelBootstrapRole',
      'maintenance NewAPI channel bootstrap role type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceNewApiChannelBootstrap',
      'maintenance NewAPI channel bootstrap getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'evaluateMaintenanceNewApiChannelBootstrap',
      'maintenance NewAPI channel bootstrap evaluator',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/gemini/newapi-channel-bootstrap',
      'maintenance NewAPI channel bootstrap endpoint',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'NewAPI channel bootstrap readiness packet',
      'maintenance NewAPI channel bootstrap panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceNewApiChannelBootstrap',
      'maintenance NewAPI channel bootstrap state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceNewApiChannelRoleRows',
      'maintenance NewAPI channel bootstrap role rows binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceNewApiChannelSetupSteps',
      'maintenance NewAPI channel bootstrap setup steps binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceNewApiChannelEnvEntries',
      'maintenance NewAPI channel bootstrap env binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'normalized_base_url_display',
      'maintenance NewAPI channel bootstrap normalized URL binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'configuration_written',
      'maintenance NewAPI channel bootstrap no-write boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'gateway_called',
      'maintenance NewAPI channel bootstrap no-gateway boundary',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI cheap-first policy</h2>',
      '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap readiness packet</h2>',
      'maintenance NewAPI channel bootstrap follows Gemini cheap-first policy',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap readiness packet</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      'maintenance NewAPI channel bootstrap precedes observed Gemini queue',
    ),
  () =>
    assertIncludes(
      maintenanceNewApiChannelBootstrapPanel,
      'Cheap-first role readiness',
      'maintenance NewAPI channel bootstrap role readiness panel',
    ),
  () =>
    assertIncludes(
      maintenanceNewApiChannelBootstrapPanel,
      'Bootstrap checks',
      'maintenance NewAPI channel bootstrap checks panel',
    ),
  () =>
    assertIncludes(
      maintenanceNewApiChannelBootstrapPanel,
      'Recommended env',
      'maintenance NewAPI channel bootstrap recommended env panel',
    ),
  () =>
    assertIncludes(
      maintenanceNewApiChannelBootstrapPanel,
      'Validation commands',
      'maintenance NewAPI channel bootstrap validation commands panel',
    ),
  () =>
    assertNotMatches(
      maintenanceNewApiChannelBootstrapPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer_token|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|gateway_response|client_email|phone)\b/i,
      'maintenance NewAPI channel bootstrap no secrets or raw request/response fields',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiCoverageGapQueue',
      'maintenance observed Gemini coverage gap queue type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiCoverageGapFamilyRow',
      'maintenance observed Gemini coverage gap family row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiCoverageGapTaskRow',
      'maintenance observed Gemini coverage gap task row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiCoverageGapItem',
      'maintenance observed Gemini coverage gap item type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceObservedGeminiCoverageGapQueue',
      'maintenance observed Gemini coverage gap queue getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/gemini/observed-coverage-gap-queue',
      'maintenance observed Gemini coverage gap queue endpoint',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'high_frequency_task_rows',
      'maintenance observed Gemini coverage gap task rows payload binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'gap_items',
      'maintenance observed Gemini coverage gap items payload binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getMaintenanceObservedGeminiCoverageGapQueue',
      'maintenance observed Gemini coverage gap queue load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceObservedGeminiCoverageGapQueue',
      'maintenance observed Gemini coverage gap queue state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'Observed Gemini coverage gap queue',
      'maintenance observed Gemini coverage gap queue panel',
    ),
  () => assertIncludes(maintenancePage, 'family_gap_count', 'maintenance observed Gemini family gap metric'),
  () => assertIncludes(maintenancePage, 'cheap_first_task_gap_count', 'maintenance observed Gemini task gap metric'),
  () =>
    assertIncludes(
      maintenancePage,
      'ready_cheap_first_candidate_count',
      'maintenance observed Gemini ready cheap-first candidate metric',
    ),
  () => assertIncludes(maintenancePage, 'high_frequency_task_rows', 'maintenance observed Gemini task row binding'),
  () => assertIncludes(maintenancePage, 'gap_items', 'maintenance observed Gemini gap item binding'),
  () =>
    assertIncludes(
      maintenancePage,
      'modelops-observed-gemini-coverage-gap-queue',
      'maintenance observed Gemini release gate id binding',
    ),
  () => assertIncludes(maintenancePage, 'privacy_boundary', 'maintenance observed Gemini privacy boundary binding'),
  () => assertIncludes(maintenancePage, 'claim_boundary', 'maintenance observed Gemini claim boundary binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI cheap-first policy</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      'maintenance observed Gemini queue follows cheap-first policy',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      'maintenance price refresh follows observed Gemini queue',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      'Family coverage',
      'maintenance observed Gemini family coverage panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      'High-frequency task coverage',
      'maintenance observed Gemini high-frequency task coverage panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      'Gap queue',
      'maintenance observed Gemini gap queue panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      'Privacy and claims',
      'maintenance observed Gemini privacy and claims panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      'Validation commands',
      'maintenance observed Gemini validation commands panel',
    ),
  () =>
    assertNotMatches(
      maintenanceObservedGeminiCoverageGapQueuePanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|gateway_response|headers|client_contact_details|email|phone|identity|benchmark_sample)\b/i,
      'maintenance observed Gemini coverage gap queue sensitive field guard',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiPremiumExceptionReview',
      'maintenance observed Gemini premium exception review type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsObservedGeminiPremiumExceptionReviewRow',
      'maintenance observed Gemini premium exception row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceObservedGeminiPremiumExceptionReview',
      'maintenance observed Gemini premium exception review getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/gemini/observed-premium-exception-review',
      'maintenance observed Gemini premium exception review endpoint',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getMaintenanceObservedGeminiPremiumExceptionReview',
      'maintenance observed Gemini premium exception review load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceObservedGeminiPremiumExceptionReview',
      'maintenance observed Gemini premium exception review state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'Observed Gemini premium exception review',
      'maintenance observed Gemini premium exception review panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'modelops-observed-gemini-premium-exception-review',
      'maintenance observed Gemini premium exception release gate id binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'premium_review_count',
      'maintenance observed Gemini premium exception review count metric',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'explicit_route_supported_count',
      'maintenance observed Gemini premium exception explicit-route metric',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'default_blocked_count',
      'maintenance observed Gemini premium exception default block metric',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'review_decision',
      'maintenance observed Gemini premium exception review decision binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'allowed_route_modes',
      'maintenance observed Gemini premium exception allowed route binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'blocked_default_tasks',
      'maintenance observed Gemini premium exception blocked default binding',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini premium exception review</h2>',
      'maintenance observed Gemini premium exception follows coverage gap queue',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini premium exception review</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      'maintenance price refresh follows observed Gemini premium exception review',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiPremiumExceptionReviewPanel,
      'Premium exception rows',
      'maintenance observed Gemini premium exception rows panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiPremiumExceptionReviewPanel,
      'Release checks',
      'maintenance observed Gemini premium exception release checks panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiPremiumExceptionReviewPanel,
      'Privacy and claims',
      'maintenance observed Gemini premium exception privacy panel',
    ),
  () =>
    assertIncludes(
      maintenanceObservedGeminiPremiumExceptionReviewPanel,
      'Validation commands',
      'maintenance observed Gemini premium exception validation panel',
    ),
  () =>
    assertNotMatches(
      maintenanceObservedGeminiPremiumExceptionReviewPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|gateway_response|headers|client_contact_details|email|phone|identity|benchmark_sample)\b/i,
      'maintenance observed Gemini premium exception review sensitive field guard',
    ),
  () => assertIncludes(maintenanceApi, 'ModelPriceRefreshMonitor', 'maintenance model price refresh monitor type'),
  () => assertIncludes(maintenanceApi, 'ModelPriceRefreshMonitorCheck', 'maintenance model price refresh check type'),
  () => assertIncludes(maintenanceApi, 'ModelPriceRefreshMonitorSignal', 'maintenance model price refresh signal type'),
  () => assertIncludes(maintenanceApi, 'getModelPriceRefreshMonitor', 'maintenance model price refresh getter'),
  () => assertIncludes(maintenanceApi, 'postModelPriceRefreshMonitor', 'maintenance model price refresh evaluator'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/model-price-refresh-monitor',
      'maintenance model price refresh endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getModelPriceRefreshMonitor', 'maintenance model price refresh load task'),
  () => assertIncludes(maintenancePage, 'postModelPriceRefreshMonitor', 'maintenance model price refresh observed review load task'),
  () => assertIncludes(maintenancePage, 'modelPriceRefreshMonitor', 'maintenance model price refresh state binding'),
  () => assertIncludes(maintenancePage, 'modelPriceRefreshObservedReview', 'maintenance model price refresh observed review state'),
  () => assertIncludes(maintenancePage, 'Model price refresh monitor', 'maintenance model price refresh panel'),
  () => assertIncludes(maintenancePage, 'observed-gateway-model-refresh-review', 'maintenance observed gateway model review binding'),
  () => assertIncludes(maintenancePage, 'modelPriceRefreshObservedModelsSample', 'maintenance observed model review sample binding'),
  () => assertIncludes(maintenancePage, 'google/gemini-9-flash-lite', 'maintenance observed unknown Gemini sample'),
  () => assertIncludes(maintenancePage, 'models/gemini-3.1-flash-lite', 'maintenance observed Gemini 3.1 Flash-Lite sample'),
  () => assertIncludes(maintenancePage, 'google/gemini-3.5-flash', 'maintenance observed Gemini 3.5 Flash sample'),
  () => assertIncludes(maintenancePage, 'models/gemini-3.1-pro-preview', 'maintenance observed premium preview sample'),
  () => assertIncludes(maintenancePage, 'yibu/gemini-3.1-flash-image', 'maintenance observed Yibu Gemini image sample'),
  () => assertIncludes(maintenancePage, 'high_frequency_tasks', 'maintenance model price refresh high-frequency binding'),
  () => assertIncludes(maintenancePage, 'specialized_text_tasks', 'maintenance model price refresh specialized text binding'),
  () => assertIncludes(maintenancePage, 'media_tasks', 'maintenance model price refresh media binding'),
  () => assertIncludes(maintenancePage, 'drift_signals', 'maintenance model price refresh drift signal binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model cost regression snapshots</h2>',
      'maintenance price refresh precedes cost regression snapshots',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Model price refresh monitor</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
      'maintenance price refresh precedes selector',
    ),
  () =>
    assertNotMatches(
      modelPriceRefreshMonitorPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|request_body|response_body|gateway_response|headers|email/i,
      'maintenance model price refresh sensitive field guard',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelCostRegressionSnapshots',
      'maintenance model cost regression snapshots type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelCostRegressionSnapshot',
      'maintenance model cost regression snapshot row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelCostRegressionCheck',
      'maintenance model cost regression check type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getModelCostRegressionSnapshots',
      'maintenance model cost regression getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/model-cost-regression-snapshots',
      'maintenance model cost regression endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getModelCostRegressionSnapshots', 'maintenance model cost regression load task'),
  () => assertIncludes(maintenancePage, 'modelCostRegressionSnapshots', 'maintenance model cost regression state binding'),
  () => assertIncludes(maintenancePage, 'Model cost regression snapshots', 'maintenance model cost regression panel'),
  () => assertIncludes(maintenancePage, 'cheap_first_monthly_cost_usd', 'maintenance model cost regression cheap cost binding'),
  () => assertIncludes(maintenancePage, 'premium_baseline_monthly_cost_usd', 'maintenance model cost regression baseline binding'),
  () => assertIncludes(maintenancePage, 'estimated_savings_ratio', 'maintenance model cost regression savings binding'),
  () => assertIncludes(maintenancePage, 'regression_checks', 'maintenance model cost regression checks binding'),
  () => assertIncludes(maintenancePage, 'fast-routing-5000', 'maintenance model cost regression fast scenario signal'),
  () => assertIncludes(maintenancePage, 'classification-2500', 'maintenance model cost regression classification scenario signal'),
  () => assertIncludes(maintenancePage, 'ocr-extraction-3500', 'maintenance model cost regression OCR scenario signal'),
  () =>
    assertNotMatches(
      modelCostRegressionSnapshotsPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|request_body|response_body|gateway_response|headers|email/i,
      'maintenance model cost regression sensitive field guard',
    ),
  () => assertIncludes(maintenanceApi, 'GeminiNewApiModelAliasMatrixEvidence', 'maintenance Gemini/NewAPI alias matrix type'),
  () => assertIncludes(maintenanceApi, 'GeminiNewApiModelAliasMatrixRow', 'maintenance Gemini/NewAPI alias matrix row type'),
  () => assertIncludes(maintenanceApi, 'getGeminiNewApiModelAliasMatrixEvidence', 'maintenance Gemini/NewAPI alias matrix getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/gemini-newapi-model-alias-matrix', 'maintenance Gemini/NewAPI alias matrix endpoint'),
  () => assertIncludes(maintenancePage, 'getGeminiNewApiModelAliasMatrixEvidence', 'maintenance Gemini/NewAPI alias matrix load task'),
  () => assertIncludes(maintenancePage, 'geminiNewApiModelAliasMatrix', 'maintenance Gemini/NewAPI alias matrix state'),
  () => assertIncludes(maintenancePage, 'Gemini/NewAPI model alias matrix', 'maintenance Gemini/NewAPI alias matrix panel'),
  () => assertIncludes(maintenancePage, 'Accepted shapes', 'maintenance Gemini/NewAPI alias shape list'),
  () => assertIncludes(maintenancePage, 'Alias privacy boundary', 'maintenance Gemini/NewAPI alias privacy panel'),
  () => assertIncludes(maintenancePage, 'high_frequency_default_allowed', 'maintenance Gemini/NewAPI high-frequency default binding'),
  () => assertIncludes(maintenancePage, 'premium_exception', 'maintenance Gemini/NewAPI premium exception binding'),
  () => assertIncludes(maintenancePage, 'rejected_sensitive_count', 'maintenance Gemini/NewAPI rejected sensitive summary'),
  () => assertBefore(maintenancePage, 'Gemini/NewAPI model selector', 'Gemini/NewAPI model alias matrix', 'maintenance Gemini alias matrix after selector'),
  () => assertBefore(maintenancePage, 'Gemini/NewAPI model alias matrix', 'Gemini/NewAPI selector replay', 'maintenance Gemini alias matrix before replay'),
  () =>
    assertNotMatches(
      geminiAliasMatrixPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|email/i,
      'maintenance Gemini/NewAPI alias matrix sensitive field guard',
    ),
  () => assertIncludes(workbenchRuntimeApi, 'CaseWorkbenchRiskRefreshPlan', 'case workbench risk refresh plan API type'),
  () => assertIncludes(workbenchRuntimeApi, 'CaseWorkbenchRiskStateBadge', 'case workbench risk state badge API type'),
  () => assertIncludes(workbenchRuntimeApi, 'risk_refresh_plan?: CaseWorkbenchRiskRefreshPlan', 'case workbench state payload risk refresh plan binding'),
  () => assertIncludes(workbenchRuntimeApi, 'section_refresh_rows', 'case workbench risk refresh section rows'),
  () => assertIncludes(workbenchRuntimeApi, 'event_trigger_rows', 'case workbench risk refresh event rows'),
  () => assertIncludes(workbenchRuntimeApi, 'risk_state_badges: CaseWorkbenchRiskStateBadge[]', 'case workbench risk state badge rows'),
  () => assertIncludes(workbenchRuntimeApi, 'risk_state_badge_summary', 'case workbench risk state badge summary'),
  () => assertIncludes(workbenchRuntimeApi, 'risk_state_written', 'case workbench risk refresh no-write summary'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'Risk refresh plan', 'case workbench risk refresh UI panel'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'Risk state badges', 'case workbench risk state badges UI panel'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'riskRefreshPlan', 'case workbench risk refresh state binding'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'riskStateBadges', 'case workbench risk state badge binding'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'riskBadgeClass', 'case workbench risk state badge severity classes'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'riskRefreshRows', 'case workbench risk refresh row binding'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'riskTriggerRows', 'case workbench risk trigger row binding'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'raw_event_payload_returned', 'case workbench risk refresh raw event boundary'),
  () => assertIncludes(caseWorkbenchRuntimePanel, 'risk_state_written', 'case workbench risk refresh write boundary'),
  () =>
    assertNotMatches(
      caseWorkbenchRiskRefreshPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details/i,
      'case workbench risk refresh panel sensitive field guard',
    ),
  () => assertIncludes(caseDetailPage, 'getMaintenanceCaseExportReadiness', 'case detail export readiness API binding'),
  () => assertIncludes(caseDetailPage, 'buildCaseExportReadinessPayload', 'case detail export readiness payload builder'),
  () => assertIncludes(caseDetailPage, 'runExportReadinessThenDownload', 'case detail export readiness download guard'),
  () => assertIncludes(caseDetailPage, 'case_header_report_download', 'case detail report download readiness source'),
  () => assertIncludes(caseDetailPage, 'case_evidence_tab_export', 'case detail evidence export readiness source'),
  () => assertIncludes(caseDetailPage, 'case_generated_document_dialog_download', 'case detail generated document download readiness source'),
  () => assertIncludes(caseDetailPage, 'case-export-readiness-panel', 'case detail export readiness UI panel'),
  () => assertIncludes(caseDetailPage, 'reason_codes:', 'case detail export readiness reason codes UI'),
  () => assertIncludes(caseDetailPage, 'recommended_actions:', 'case detail export readiness recommended actions UI'),
  () => assertIncludes(caseDetailPage, 'raw_document_text_included: {String(exportReadiness.privacy_boundary.raw_document_text_included)}', 'case detail export readiness privacy UI'),
  () => assertIncludes(caseExportReadinessPayloadBuilder, 'report_meta', 'case detail export readiness report_meta section'),
  () => assertIncludes(caseExportReadinessPayloadBuilder, 'risk_scoring', 'case detail export readiness risk_scoring section'),
  () => assertIncludes(caseExportReadinessPayloadBuilder, 'citations', 'case detail export readiness citations section'),
  () => assertIncludes(caseExportReadinessPayloadBuilder, 'evidence', 'case detail export readiness evidence section'),
  () => assertIncludes(caseExportReadinessPayloadBuilder, 'release_decision', 'case detail export readiness release_decision section'),
  () => assertIncludes(caseExportReadinessDownloadGuard, 'downloadText(filename, content)', 'case detail download only after readiness gate'),
  () => {
    const count = caseDetailPage.match(/downloadText\(/g)?.length ?? 0;
    if (count !== 2) {
      throw new Error(`case detail direct downloadText call count: expected 2, got ${count}`);
    }
  },
  () =>
    assertNotMatches(
      caseExportReadinessPayloadBuilder,
      /viewDoc\.content|params\.content|content_json|raw_document_text["']?\s*:|document_text["']?\s*:|parsed_text|file_url/i,
      'case detail export readiness metadata-only payload guard',
    ),
  () =>
    assertNotMatches(
      caseExportReadinessApiCall,
      /viewDoc\.content|content\s*:|buildDocumentContent\(|buildEvidenceDirectory\(|raw_document_text["']?\s*:|document_text["']?\s*:/i,
      'case detail export readiness API call must stay metadata-only',
    ),
  () => assertIncludes(feedbackApi, 'FeedbackCapturePlan', 'feedback capture plan API type'),
  () => assertIncludes(feedbackApi, '/api/v1/entities/feedback_tickets/capture-plan', 'feedback capture plan endpoint binding'),
  () => assertIncludes(feedbackCapturePanel, 'FeedbackCapturePanelProps', 'feedback capture reusable component props'),
  () => assertIncludes(feedbackCapturePanel, 'previewFeedbackCapturePlan', 'feedback capture panel preview API binding'),
  () => assertIncludes(feedbackCapturePanel, 'client.entities.feedback_tickets.create', 'feedback capture panel ticket create binding'),
  () => assertIncludes(feedbackCapturePanel, 'raw feedback returned', 'feedback capture panel privacy boundary UI'),
  () => assertIncludes(feedbackCapturePanel, 'calls_ai_model', 'feedback capture panel model-call privacy binding'),
  () => assertIncludes(settingsPage, 'getModelGatewayRuntimeConfiguration', 'settings AI provider runtime configuration API binding'),
  () => assertIncludes(settingsPage, 'ModelGatewayRuntimeConfiguration', 'settings AI provider runtime configuration type'),
  () => assertIncludes(settingsPage, 'AI model provider', 'settings AI provider status card'),
  () =>
    assertIncludes(
      settingsPage,
      'Gemini cheap-first routing is read-only here',
      'settings AI provider read-only deployment-secret copy',
    ),
  () => assertIncludes(settingsPage, 'normalized base URL via', 'settings AI provider normalized base URL status label'),
  () => assertIncludes(settingsPage, 'credential presence via', 'settings AI provider credential presence label'),
  () => assertIncludes(settingsPage, 'cheap_first_ready_count', 'settings AI provider cheap-first count binding'),
  () => assertIncludes(settingsPage, 'credentials_included', 'settings AI provider credentials-included boundary binding'),
  () => assertIncludes(settingsPage, 'configuration_written', 'settings AI provider configuration write boundary binding'),
  () => assertIncludes(settingsPage, 'APP_AI_CHEAP_MODEL', 'settings AI provider cheap model env name'),
  () => assertIncludes(settingsPage, 'APP_AI_EMBEDDING_MODEL', 'settings AI provider embedding env name'),
  () => assertIncludes(settingsPage, '/model-ops', 'settings AI provider model-ops evidence link'),
  () => assertBefore(settingsPage, 'AI model provider', '<FeedbackCapturePanel />', 'settings AI provider before feedback form'),
  () =>
    assertNotMatches(
      settingsAiModelProviderSection,
      /api_key_display|base_url_display|dry_run_contracts|headers|request_body|response_body|gateway_response|\/api\/v1\/admin|adminSettings|updateEnv|setEnv|localStorage/i,
      'settings AI provider forbidden raw/admin field guard',
    ),
  () =>
    assertNotMatches(
      settingsAiModelProviderSection,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text/i,
      'settings AI provider sensitive field guard',
    ),
  () => assertIncludes(settingsPage, 'FeedbackCapturePanel', 'settings feedback capture import'),
  () => assertIncludes(settingsPage, '<FeedbackCapturePanel />', 'settings feedback capture component binding'),
  () => assertIncludes(deepReportPage, 'FeedbackCapturePanel', 'deep report feedback capture component binding'),
  () => assertIncludes(deepReportPage, 'Report feedback', 'deep report feedback panel title'),
  () => assertIncludes(deepReportPage, 'defaultCategory="report_quality"', 'deep report feedback category default'),
  () => assertIncludes(deepReportPage, 'defaultAffectedArtifactId={id ?? report.report_no}', 'deep report feedback report id binding'),
  () => assertIncludes(feedbackCapturePanel, 'Product feedback', 'settings product feedback panel'),
  () => assertIncludes(feedbackCapturePanel, 'Preview triage', 'settings feedback triage preview action'),
  () => assertIncludes(feedbackCapturePanel, 'Send feedback', 'settings feedback submit action'),
  () => assertIncludes(feedbackCapturePanel, 'Related report/case/document ID', 'settings feedback artifact link field'),
  () => assertIncludes(adminPage, "'roadmap'", 'admin feedback roadmap column'),
  () => assertIncludes(adminPage, "'lifecycle'", 'admin feedback lifecycle column'),
  () => assertIncludes(adminPage, "'closure'", 'admin feedback closure column'),
  () => assertIncludes(adminPage, 'row.capture_summary?.linked_need_id', 'admin feedback linked need binding'),
  () => assertIncludes(adminPage, 'row.lifecycle_summary?.state', 'admin feedback lifecycle state binding'),
  () => assertIncludes(adminPage, 'row.lifecycle_summary?.blocking_check_ids', 'admin feedback closure blocker binding'),
  () =>
    assertNotMatches(
      settingsFeedbackCaptureSection,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|payment_secret/i,
      'settings feedback capture panel sensitive field guard',
    ),
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
  () => assertIncludes(maintenanceApi, 'MaintenanceHeartbeatEvidence', 'maintenance heartbeat evidence API type'),
  () => assertIncludes(maintenanceApi, 'MaintenanceHeartbeatRecord', 'maintenance heartbeat record API type'),
  () => assertIncludes(maintenanceApi, 'getMaintenanceHeartbeatEvidence', 'maintenance heartbeat evidence getter'),
  () => assertIncludes(maintenanceApi, 'postMaintenanceHeartbeatEvidence', 'maintenance heartbeat evidence review API binding'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/maintenance-heartbeat-evidence',
      'maintenance heartbeat evidence endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getMaintenanceHeartbeatEvidence', 'maintenance heartbeat evidence load task'),
  () => assertIncludes(maintenancePage, 'maintenanceHeartbeatEvidence', 'maintenance heartbeat evidence state binding'),
  () => assertIncludes(maintenancePage, 'Maintenance heartbeat evidence', 'maintenance heartbeat evidence panel'),
  () => assertIncludes(maintenancePage, 'Event type schema', 'maintenance heartbeat schema table'),
  () => assertIncludes(maintenancePage, 'Heartbeat records', 'maintenance heartbeat record table'),
  () => assertIncludes(maintenancePage, 'Gap analysis', 'maintenance heartbeat gap panel'),
  () => assertIncludes(maintenancePage, 'recommended_actions', 'maintenance heartbeat recommended action source binding'),
  () => assertIncludes(maintenancePage, 'verified_continuous_hours', 'maintenance heartbeat verified hours binding'),
  () => assertIncludes(maintenancePage, 'missing_event_types', 'maintenance heartbeat missing event binding'),
  () => assertIncludes(maintenancePage, 'heartbeat_records', 'maintenance heartbeat records binding'),
  () => assertIncludes(maintenancePage, 'event_type_schema', 'maintenance heartbeat schema binding'),
  () => assertIncludes(maintenancePage, 'raw_payload_echoed', 'maintenance heartbeat raw payload boundary binding'),
  () => assertIncludes(maintenancePage, 'ready_for_goal_claim', 'maintenance heartbeat goal claim boundary binding'),
  () =>
    assertBefore(
      maintenancePage,
      'Continuous session run monitor',
      'Maintenance heartbeat evidence',
      'maintenance heartbeat evidence follows run monitor',
    ),
  () =>
    assertBefore(
      maintenancePage,
      'Maintenance heartbeat evidence',
      'Continuous session review packet',
      'maintenance heartbeat evidence precedes review packet',
    ),
  () =>
    assertNotMatches(
      maintenanceHeartbeatEvidencePanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|payment_secret/i,
      'maintenance heartbeat evidence sensitive field guard',
    ),
  () => assertIncludes(maintenancePage, 'User need benchmark coverage', 'user need benchmark coverage panel'),
  () => assertIncludes(maintenancePage, 'Public benchmark review gaps', 'user need benchmark public review gap panel'),
  () => assertIncludes(maintenancePage, 'public sampler network', 'user need benchmark public sampler boundary'),
  () => assertIncludes(maintenancePage, 'public_benchmark_status', 'user need benchmark public status binding'),
  () => assertIncludes(maintenancePage, 'Calibration attention gaps', 'user need benchmark calibration attention panel'),
  () => assertIncludes(maintenancePage, 'cheap-first calibration', 'user need benchmark calibration summary'),
  () => assertIncludes(maintenancePage, 'linked_calibration_task_ids', 'user need benchmark calibration task binding'),
  () => assertIncludes(maintenancePage, 'User need Gemini route coverage', 'user need Gemini route coverage panel'),
  () => assertIncludes(maintenancePage, 'userNeedGeminiRouteCoverage', 'user need Gemini route coverage state binding'),
  () => assertIncludes(maintenancePage, 'getUserNeedGeminiRouteCoverage', 'user need Gemini route coverage API binding'),
  () => assertIncludes(maintenancePage, 'route_task_source', 'user need Gemini route task source binding'),
  () => assertIncludes(maintenancePage, 'linked_route_tasks', 'user need Gemini linked route tasks binding'),
  () => assertIncludes(maintenancePage, 'linked_default_models', 'user need Gemini linked default models binding'),
  () => assertIncludes(maintenancePage, 'returns_route_payloads', 'user need Gemini route payload boundary binding'),
  () => assertIncludes(maintenancePage, 'changes_default_routes', 'user need Gemini default route change boundary'),
  () => assertIncludes(maintenancePage, 'claims_default_route_changed', 'user need Gemini no default route change claim binding'),
  () => assertIncludes(maintenancePage, 'claims_public_benchmark_scores', 'user need Gemini no public benchmark score claim binding'),
  () => assertIncludes(maintenancePage, 'claims_live_gateway_execution', 'user need Gemini no live gateway claim binding'),
  () => assertIncludes(maintenancePage, 'route preflight endpoint', 'user need Gemini route preflight endpoint label'),
  () => assertIncludes(maintenancePage, 'official_source_urls', 'user need Gemini official source URL binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need benchmark coverage</h2>',
      '<h2 className="text-xl font-black text-stone-950">User need Gemini route coverage</h2>',
      'user need Gemini route coverage follows benchmark coverage',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need Gemini route coverage</h2>',
      '<h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>',
      'user need Gemini route coverage precedes implementation queue',
    ),
  () => assertIncludes(maintenancePage, 'User need implementation priority queue', 'user need implementation priority queue panel'),
  () => assertIncludes(maintenancePage, 'userNeedImplementationQueue', 'user need implementation queue state binding'),
  () => assertIncludes(maintenancePage, 'getUserNeedImplementationPriorityQueue', 'user need implementation queue API binding'),
  () => assertIncludes(maintenancePage, 'implementation_tracks', 'user need implementation queue track binding'),
  () => assertIncludes(maintenancePage, 'queue_priority_score', 'user need implementation queue priority binding'),
  () => assertIncludes(maintenancePage, 'imports public samples', 'user need implementation queue public sample boundary'),
  () => assertIncludes(maintenancePage, 'uses raw legal text', 'user need implementation queue raw legal text boundary'),
  () =>
    assertIncludes(
      maintenanceApi,
      'UserNeedLegalDocumentBenchmarkEvidence',
      'user need legal-document benchmark evidence type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'UserNeedLegalDocumentBenchmarkEvidenceRow',
      'user need legal-document benchmark evidence row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getUserNeedLegalDocumentBenchmarkEvidence',
      'user need legal-document benchmark evidence API binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/user-needs/legal-document-benchmark-evidence',
      'user need legal-document benchmark evidence endpoint',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getUserNeedLegalDocumentBenchmarkEvidence',
      'user need legal-document benchmark evidence load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'userNeedLegalDocumentBenchmarkEvidence',
      'user need legal-document benchmark evidence state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'User need legal-document benchmark evidence',
      'user need legal-document benchmark evidence panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'document_evaluation_status',
      'user need legal-document benchmark evidence document evaluation status binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'fact_consistency_status',
      'user need legal-document benchmark evidence fact consistency status binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'cheap_first_default_change_allowed',
      'user need legal-document benchmark evidence cheap-first default flag',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'public_benchmark_score_claimed',
      'user need legal-document benchmark evidence no public score claim binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_raw_candidate_text',
      'user need legal-document benchmark evidence raw candidate boundary binding',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">User need legal-document benchmark evidence</h2>',
      'user need legal-document benchmark evidence follows implementation queue',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need legal-document benchmark evidence</h2>',
      '<h2 className="text-xl font-black text-stone-950">User need cheap-first handoff</h2>',
      'user need legal-document benchmark evidence precedes cheap-first handoff',
    ),
  () => assertIncludes(maintenanceApi, 'ModelOpsUserNeedCheapFirstHandoff', 'maintenance user need cheap-first handoff type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsUserNeedCheapFirstHandoffRow',
      'maintenance user need cheap-first handoff row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'ModelOpsUserNeedCheapFirstHandoffSection',
      'maintenance user need cheap-first handoff section type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceUserNeedCheapFirstHandoff',
      'maintenance user need cheap-first handoff API binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/user-needs/cheap-first-evidence-handoff',
      'maintenance user need cheap-first handoff endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'cheap_first_route_protected', 'maintenance user need cheap-first protected route type'),
  () => assertIncludes(maintenanceApi, 'reviewer_action', 'maintenance user need cheap-first reviewer action type'),
  () => assertIncludes(maintenancePage, 'getMaintenanceUserNeedCheapFirstHandoff', 'maintenance user need cheap-first handoff load task'),
  () =>
    assertIncludes(
      maintenancePage,
      'maintenanceUserNeedCheapFirstHandoff',
      'maintenance user need cheap-first handoff state binding',
    ),
  () => assertIncludes(maintenancePage, 'User need cheap-first handoff', 'maintenance user need cheap-first handoff panel'),
  () =>
    assertIncludes(
      maintenancePage,
      'cheap_first_route_protected_need_count',
      'maintenance user need cheap-first protected summary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'high_priority_route_protected_count',
      'maintenance user need cheap-first high-priority protection summary',
    ),
  () => assertIncludes(maintenancePage, 'default_change_allowed', 'maintenance user need cheap-first default change flag'),
  () => assertIncludes(maintenancePage, 'row.cheap_first_route_protected', 'maintenance user need cheap-first row route flag'),
  () => assertIncludes(maintenancePage, 'row.reviewer_action', 'maintenance user need cheap-first reviewer action binding'),
  () => assertIncludes(maintenancePage, 'row.linked_release_gates', 'maintenance user need cheap-first release gates binding'),
  () => assertIncludes(maintenancePage, 'privacy_boundary', 'maintenance user need cheap-first privacy boundary binding'),
  () => assertIncludes(maintenancePage, 'claim_boundary', 'maintenance user need cheap-first claim boundary binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">User need cheap-first handoff</h2>',
      'user need cheap-first handoff follows implementation queue',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">User need cheap-first handoff</h2>',
      '<h2 className="text-xl font-black text-stone-950">Product feature gap radar</h2>',
      'user need cheap-first handoff precedes product gap radar',
    ),
  () => assertIncludes(maintenanceApi, 'BillingEntitlementGap', 'maintenance billing entitlement gap type'),
  () => assertIncludes(maintenanceApi, 'getBillingEntitlementGap', 'maintenance billing entitlement gap getter'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/billing-entitlement-gap',
      'maintenance billing entitlement gap endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'implemented_controls', 'maintenance billing entitlement implemented controls type'),
  () => assertIncludes(maintenanceApi, 'remaining_product_gaps', 'maintenance billing entitlement remaining gaps type'),
  () => assertIncludes(maintenanceApi, 'privacy_note', 'maintenance billing entitlement privacy note type'),
  () => assertIncludes(maintenancePage, 'getBillingEntitlementGap', 'maintenance billing entitlement gap load task'),
  () => assertIncludes(maintenancePage, 'billingEntitlementGap', 'maintenance billing entitlement gap state binding'),
  () => assertIncludes(maintenancePage, 'Billing entitlement gap', 'maintenance billing entitlement gap panel'),
  () => assertIncludes(maintenancePage, 'implemented_controls', 'maintenance billing entitlement implemented controls binding'),
  () => assertIncludes(maintenancePage, 'remaining_product_gaps', 'maintenance billing entitlement remaining gaps binding'),
  () => assertIncludes(maintenancePage, 'validation_commands', 'maintenance billing entitlement validation binding'),
  () =>
    assertIncludes(
      maintenancePage,
      'stripe-webhook-signature-verification',
      'maintenance billing entitlement webhook signature signal',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'frontend-entitlement-state-messaging',
      'maintenance billing entitlement frontend messaging signal',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">100+ maintenance gates</h2>',
      '<h2 className="text-xl font-black text-stone-950">Billing entitlement gap</h2>',
      'billing entitlement gap follows maintenance gate summary',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Billing entitlement gap</h2>',
      '<h2 className="text-xl font-black text-stone-950">24h evidence timeline</h2>',
      'billing entitlement gap precedes continuous timeline',
    ),
  () =>
    assertNotMatches(
      billingEntitlementGapPanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|client_contact_details|payment_session|card_number|payment_secret/i,
      'maintenance billing entitlement gap sensitive field guard',
    ),
  () => assertIncludes(maintenanceApi, 'FeedbackLifecyclePolicy', 'maintenance feedback lifecycle policy type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceFeedbackUserNeedLegalDocumentBenchmarkBacklog',
      'maintenance feedback user-need legal-document benchmark backlog type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceFeedbackUserNeedLegalDocumentBenchmarkBacklogItem',
      'maintenance feedback user-need legal-document benchmark backlog item type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceFeedbackUserNeedLegalDocumentBenchmarkBacklog',
      'maintenance feedback user-need legal-document benchmark backlog API binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog',
      'maintenance feedback user-need legal-document benchmark backlog endpoint',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'Feedback user-need legal-document benchmark backlog',
      'maintenance feedback user-need legal-document benchmark backlog panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'feedbackUserNeedLegalDocumentBenchmarkBacklog',
      'maintenance feedback user-need legal-document benchmark backlog state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getMaintenanceFeedbackUserNeedLegalDocumentBenchmarkBacklog',
      'maintenance feedback user-need legal-document benchmark backlog load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'mapped_need_ids',
      'maintenance feedback user-need legal-document benchmark backlog mapped need binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'linked_document_case_ids',
      'maintenance feedback user-need legal-document benchmark backlog document case binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'linked_document_type_ids',
      'maintenance feedback user-need legal-document benchmark backlog document type binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'release_gate_links',
      'maintenance feedback user-need legal-document benchmark backlog release gate binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'reason_codes',
      'maintenance feedback user-need legal-document benchmark backlog reason code binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'next_actions',
      'maintenance feedback user-need legal-document benchmark backlog next action binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_raw_feedback_text',
      'maintenance feedback user-need legal-document benchmark backlog raw feedback boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_public_benchmark_text',
      'maintenance feedback user-need legal-document benchmark backlog public benchmark boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_raw_model_output',
      'maintenance feedback user-need legal-document benchmark backlog model output boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_payload_bodies',
      'maintenance feedback user-need legal-document benchmark backlog payload boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_credentials',
      'maintenance feedback user-need legal-document benchmark backlog credential boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'public_benchmark_score_claimed',
      'maintenance feedback user-need legal-document benchmark backlog claim boundary',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceFeedbackUserNeedLegalDocumentBenchmarkReleasePacket',
      'maintenance feedback user-need legal-document benchmark release packet type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceFeedbackUserNeedLegalDocumentBenchmarkReleasePacketRow',
      'maintenance feedback user-need legal-document benchmark release packet row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceFeedbackUserNeedLegalDocumentBenchmarkReleasePacket',
      'maintenance feedback user-need legal-document benchmark release packet API binding',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/feedback/user-need-legal-document-benchmark-release-packet',
      'maintenance feedback user-need legal-document benchmark release packet endpoint',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'Feedback user-need legal-document benchmark release packet',
      'maintenance feedback user-need legal-document benchmark release packet panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'feedbackUserNeedLegalDocumentBenchmarkReleasePacket',
      'maintenance feedback user-need legal-document benchmark release packet state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getMaintenanceFeedbackUserNeedLegalDocumentBenchmarkReleasePacket',
      'maintenance feedback user-need legal-document benchmark release packet load task',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'release_action_status',
      'maintenance feedback user-need legal-document benchmark release packet action status binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'customer_resolution_allowed',
      'maintenance feedback user-need legal-document benchmark release packet customer gate binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'customer_resolution_claimed',
      'maintenance feedback user-need legal-document benchmark release packet customer claim boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'lifecycle_blocking_check_ids',
      'maintenance feedback user-need legal-document benchmark release packet lifecycle blocker binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_customer_notes',
      'maintenance feedback user-need legal-document benchmark release packet customer note boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'returns_public_resolution_text',
      'maintenance feedback user-need legal-document benchmark release packet public resolution boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'customer_notification_claimed',
      'maintenance feedback user-need legal-document benchmark release packet notification claim boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'validation_commands',
      'maintenance feedback user-need legal-document benchmark release packet validation binding',
    ),
  () => assertIncludes(maintenanceApi, 'FeedbackLifecycleState', 'maintenance feedback lifecycle state type'),
  () => assertIncludes(maintenanceApi, 'FeedbackLifecycleTransition', 'maintenance feedback lifecycle transition type'),
  () => assertIncludes(maintenanceApi, 'FeedbackLifecycleCheck', 'maintenance feedback lifecycle check type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'FeedbackLifecycleSampleEvaluation',
      'maintenance feedback lifecycle sample evaluation type',
    ),
  () => assertIncludes(maintenanceApi, 'getFeedbackLifecyclePolicy', 'maintenance feedback lifecycle API binding'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/feedback-lifecycle-policy',
      'maintenance feedback lifecycle endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getFeedbackLifecyclePolicy', 'maintenance feedback lifecycle load task'),
  () => assertIncludes(maintenancePage, 'feedbackLifecyclePolicy', 'maintenance feedback lifecycle state binding'),
  () => assertIncludes(maintenancePage, 'setFeedbackLifecyclePolicy', 'maintenance feedback lifecycle state setter'),
  () => assertIncludes(maintenancePage, 'Feedback lifecycle policy', 'maintenance feedback lifecycle panel'),
  () => assertIncludes(maintenancePage, 'state_machine.happy_path', 'maintenance feedback lifecycle happy path binding'),
  () => assertIncludes(maintenancePage, 'transition_checks', 'maintenance feedback lifecycle transition checks binding'),
  () => assertIncludes(maintenancePage, 'high_risk_policy', 'maintenance feedback lifecycle high-risk policy binding'),
  () => assertIncludes(maintenancePage, 'customer_visible_resolution', 'maintenance feedback lifecycle customer resolution checkpoint'),
  () => assertIncludes(maintenancePage, 'high_risk_feedback_linked', 'maintenance feedback lifecycle high-risk linkage check'),
  () => assertIncludes(maintenancePage, 'blocking_sample_ticket_ids', 'maintenance feedback lifecycle blocker summary'),
  () => assertIncludes(maintenancePage, 'sample_tickets_evaluation', 'maintenance feedback lifecycle sample table'),
  () => assertIncludes(maintenancePage, 'privacy-safe public note', 'maintenance feedback lifecycle privacy-safe note check'),
  () => assertIncludes(maintenancePage, 'validation_commands', 'maintenance feedback lifecycle validation binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Feedback roadmap</h2>',
      '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark backlog</h2>',
      'feedback user-need legal-document benchmark backlog follows roadmap',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark backlog</h2>',
      '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark release packet</h2>',
      'feedback user-need legal-document benchmark release packet follows backlog',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark release packet</h2>',
      '<h2 className="text-xl font-black text-stone-950">Feedback lifecycle policy</h2>',
      'feedback lifecycle policy follows feedback benchmark release packet',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Feedback lifecycle policy</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal review benchmark</h2>',
      'feedback lifecycle policy precedes legal review benchmark',
    ),
  () => assertIncludes(maintenancePage, 'Legal document benchmark coverage', 'legal document benchmark coverage panel'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentBenchmarkFixtures', 'legal document benchmark fixtures type'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentBenchmarkPrediction', 'legal document benchmark structured prediction type'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentBenchmarkEvaluation', 'legal document benchmark evaluation type'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentBenchmarkLocalBaseline', 'legal document benchmark local baseline type'),
  () => assertIncludes(maintenanceApi, 'getLegalDocumentBenchmarkFixtures', 'legal document benchmark fixtures API binding'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalDocumentBenchmarkFixtures', 'legal document benchmark evaluation API binding'),
  () => assertIncludes(maintenanceApi, 'getLegalDocumentBenchmarkLocalBaseline', 'legal document benchmark local baseline API binding'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-review-benchmark/document-fixtures',
      'legal document benchmark fixtures endpoint',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-review-benchmark/document-fixtures/local-baseline',
      'legal document benchmark local baseline endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getLegalDocumentBenchmarkFixtures', 'legal document benchmark fixtures load task'),
  () => assertIncludes(maintenancePage, 'evaluateLegalDocumentBenchmarkFixtures({})', 'legal document benchmark not-run evaluation load task'),
  () => assertIncludes(maintenancePage, 'getLegalDocumentBenchmarkLocalBaseline', 'legal document benchmark local baseline load task'),
  () => assertIncludes(maintenancePage, 'legalDocumentBenchmarkFixtures', 'legal document benchmark fixtures state binding'),
  () => assertIncludes(maintenancePage, 'legalDocumentBenchmarkEvaluation', 'legal document benchmark evaluation state binding'),
  () => assertIncludes(maintenancePage, 'legalDocumentBenchmarkLocalBaseline', 'legal document benchmark local baseline state binding'),
  () => assertIncludes(maintenancePage, 'Legal document benchmark fixtures', 'legal document benchmark fixtures panel'),
  () => assertIncludes(maintenancePage, 'Local rule baseline', 'legal document benchmark local baseline panel'),
  () => assertIncludes(maintenancePage, 'supports_low_resource_laptop', 'legal document benchmark local baseline low-resource binding'),
  () => assertIncludes(maintenancePage, 'raw_prediction_payload_returned', 'legal document benchmark local baseline raw prediction boundary'),
  () => assertIncludes(maintenancePage, 'returns_raw_predictions', 'legal document benchmark local baseline raw prediction privacy boundary'),
  () => assertIncludes(maintenancePage, 'production_extraction_claimed', 'legal document benchmark local baseline production claim boundary'),
  () => assertIncludes(maintenancePage, 'raw snippet rendered: false', 'legal document benchmark raw snippet UI boundary'),
  () => assertIncludes(maintenancePage, 'maintenance_ui_renders_raw_fixture_snippets', 'legal document benchmark explicit UI raw snippet boundary'),
  () => assertIncludes(maintenancePage, 'public_benchmark_score_claimed', 'legal document benchmark public score claim boundary'),
  () => assertIncludes(maintenancePage, 'expected_fields', 'legal document benchmark expected fields binding'),
  () => assertIncludes(maintenancePage, 'model_call_policy', 'legal document benchmark model call policy binding'),
  () => assertIncludes(maintenancePage, 'returns_raw_model_output', 'maintenance privacy boundary'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentFactConsistencyBenchmark', 'legal document fact consistency benchmark type'),
  () => assertIncludes(maintenanceApi, 'LegalDocumentFactConsistencyEvaluation', 'legal document fact consistency evaluation type'),
  () => assertIncludes(maintenanceApi, 'getLegalDocumentFactConsistencyBenchmark', 'legal document fact consistency API binding'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-review-benchmark/document-fact-consistency',
      'legal document fact consistency endpoint',
    ),
  () => assertIncludes(maintenancePage, 'getLegalDocumentFactConsistencyBenchmark', 'legal document fact consistency load task'),
  () => assertIncludes(maintenancePage, 'legalDocumentFactConsistencyBenchmark', 'legal document fact consistency state binding'),
  () => assertIncludes(maintenancePage, 'Legal document fact consistency benchmark', 'legal document fact consistency panel'),
  () => assertIncludes(maintenancePage, 'amount_expectations', 'legal document fact consistency amount binding'),
  () => assertIncludes(maintenancePage, 'deadline_expectations', 'legal document fact consistency deadline binding'),
  () => assertIncludes(maintenancePage, 'required_fact_ids', 'legal document fact consistency required fact binding'),
  () => assertIncludes(maintenancePage, 'contradiction_pairs', 'legal document fact consistency contradiction binding'),
  () => assertIncludes(maintenancePage, 'returns_raw_document_text', 'legal document fact consistency raw document boundary'),
  () =>
    assertBefore(
      maintenancePage,
      'Legal document benchmark coverage',
      'Legal document benchmark fixtures',
      'document fixture suite follows document coverage',
    ),
  () =>
    assertBefore(
      maintenancePage,
      'Local rule baseline',
      'Evaluation case',
      'local baseline precedes empty-prediction evaluation table',
    ),
  () =>
    assertBefore(
      maintenancePage,
      'Legal document benchmark fixtures',
      'Legal document fact consistency benchmark',
      'fact consistency follows document fixture suite',
    ),
  () =>
    assertBefore(
      maintenancePage,
      'Legal document fact consistency benchmark',
      'Public benchmark sampler',
      'fact consistency precedes public sampler',
    ),
  () => assertIncludes(maintenanceApi, 'LegalBenchmarkFixtureCrosswalk', 'legal benchmark fixture crosswalk type'),
  () => assertIncludes(maintenanceApi, 'getLegalBenchmarkFixtureCrosswalk', 'legal benchmark fixture crosswalk API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk', 'legal benchmark fixture crosswalk endpoint'),
  () => assertIncludes(maintenanceApi, 'document_fixture_ids?: string[]', 'public benchmark sampler document fixture ids type'),
  () => assertIncludes(maintenanceApi, 'LegalPublicBenchmarkLicenseGate', 'public benchmark license gate type'),
  () => assertIncludes(maintenanceApi, 'getLegalPublicBenchmarkLicenseGate', 'public benchmark license gate API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/public-license-gate', 'public benchmark license gate endpoint'),
  () => assertIncludes(maintenanceApi, 'raw_text_import_allowed: boolean', 'public benchmark license gate raw text boundary type'),
  () => assertIncludes(maintenanceApi, 'public_score_claim_allowed: boolean', 'public benchmark license gate public score boundary type'),
  () => assertIncludes(maintenanceApi, 'dataset_download_allowed: boolean', 'public benchmark license gate dataset boundary type'),
  () => assertIncludes(maintenanceApi, 'linked_route_task_ids: string[]', 'public benchmark license gate route task type'),
  () => assertIncludes(maintenancePage, 'getLegalPublicBenchmarkLicenseGate', 'public benchmark license gate load task'),
  () => assertIncludes(maintenancePage, 'publicBenchmarkLicenseGate', 'public benchmark license gate state binding'),
  () => assertIncludes(maintenancePage, 'Legal public benchmark license gate', 'public benchmark license gate load label'),
  () => assertIncludes(maintenancePage, 'Public benchmark license gate', 'public benchmark license gate panel'),
  () => assertIncludes(maintenancePage, 'release_claim_blocked_source_count', 'public benchmark license gate blocked source summary'),
  () => assertIncludes(maintenancePage, 'linked_route_task_count', 'public benchmark license gate route task summary'),
  () => assertIncludes(maintenancePage, 'required_checks', 'public benchmark license gate checklist binding'),
  () => assertIncludes(maintenancePage, 'public score claim:', 'public benchmark license gate public score label'),
  () => assertIncludes(maintenancePage, 'datasets downloaded:', 'public benchmark license gate dataset label'),
  () => assertIncludes(maintenancePage, 'gateway calls:', 'public benchmark license gate gateway label'),
  () => assertIncludes(maintenancePage, 'credentials returned:', 'public benchmark license gate credential label'),
  () => assertIncludes(maintenancePage, 'publicBenchmarkLicenseGate.validation_commands', 'public benchmark license gate validation binding'),
  () => assertIncludes(maintenancePage, 'getLegalBenchmarkFixtureCrosswalk', 'legal benchmark fixture crosswalk load task'),
  () => assertIncludes(maintenancePage, 'benchmarkFixtureCrosswalk', 'legal benchmark fixture crosswalk state binding'),
  () => assertIncludes(maintenancePage, 'Legal benchmark fixture crosswalk', 'legal benchmark fixture crosswalk panel'),
  () => assertIncludes(maintenancePage, 'source_with_document_fixture_count', 'legal benchmark fixture crosswalk document count binding'),
  () => assertIncludes(maintenancePage, 'source_with_small_corpus_count', 'legal benchmark fixture crosswalk corpus count binding'),
  () => assertIncludes(maintenancePage, 'small-corpus-*', 'legal benchmark fixture crosswalk small corpus label'),
  () => assertIncludes(maintenancePage, 'public benchmark scores claimed:', 'legal benchmark fixture crosswalk no public score claim label'),
  () => assertIncludes(maintenancePage, 'fixture snippets returned:', 'legal benchmark fixture crosswalk fixture text boundary'),
  () => assertIncludes(maintenancePage, 'datasets downloaded:', 'legal benchmark fixture crosswalk no dataset download boundary'),
  () => assertIncludes(maintenanceApi, 'LegalPublicFixturePriorityQueue', 'public fixture priority queue type'),
  () => assertIncludes(maintenanceApi, 'getLegalPublicFixturePriorityQueue', 'public fixture priority queue API binding'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue',
      'public fixture priority queue endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'lawbench_source_present: boolean', 'public fixture priority queue LawBench type binding'),
  () => assertIncludes(maintenanceApi, 'recommended_synthetic_fixture_shapes', 'public fixture priority queue synthetic shape type'),
  () => assertIncludes(maintenancePage, 'getLegalPublicFixturePriorityQueue', 'public fixture priority queue load task'),
  () => assertIncludes(maintenancePage, 'publicFixturePriorityQueue', 'public fixture priority queue state binding'),
  () => assertIncludes(maintenancePage, 'Legal public fixture priority queue', 'public fixture priority queue load label'),
  () => assertIncludes(maintenancePage, 'Public fixture priority queue', 'public fixture priority queue panel'),
  () => assertIncludes(maintenancePage, 'LawBench/LexEval/LegalBench signals', 'public fixture priority queue panel copy'),
  () => assertIncludes(maintenancePage, 'lawbench_source_present', 'public fixture priority queue LawBench summary binding'),
  () => assertIncludes(maintenancePage, 'recommended_synthetic_fixture_shapes', 'public fixture priority queue fixture shape binding'),
  () => assertIncludes(maintenancePage, 'linked_high_priority_need_ids', 'public fixture priority queue high priority need binding'),
  () => assertIncludes(maintenancePage, 'external datasets downloaded:', 'public fixture priority queue dataset boundary label'),
  () => assertIncludes(maintenancePage, 'dataset examples returned:', 'public fixture priority queue raw dataset boundary'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Public benchmark sampler</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>',
      'crosswalk follows public sampler',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Public benchmark license gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>',
      'license gate precedes crosswalk',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>',
      '<h2 className="text-xl font-black text-stone-950">Public fixture priority queue</h2>',
      'public fixture priority queue follows crosswalk',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Public fixture priority queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence bundle</h2>',
      'public fixture priority queue precedes evidence bundle',
    ),
  () => assertIncludes(maintenancePage, 'Legal benchmark research refresh', 'legal benchmark research refresh panel'),
  () => assertIncludes(maintenancePage, 'getLegalBenchmarkResearchRefresh', 'legal benchmark research refresh route/API binding'),
  () => assertIncludes(maintenancePage, 'Metadata-only/no benchmark score claims boundary', 'legal benchmark research refresh claim boundary panel'),
  () => assertIncludes(maintenancePage, 'no benchmark score claims', 'legal benchmark research refresh metadata-only copy'),
  () => assertIncludes(maintenancePage, 'benchmark score claims:', 'legal benchmark research refresh non-score-claim flag'),
  () => assertIncludes(maintenancePage, 'cheap-first/local validation', 'legal benchmark research refresh cheap-first/local wording'),
  () => assertIncludes(maintenancePage, 'cheap-first local validation', 'legal benchmark research refresh local validation summary'),
  () => assertIncludes(maintenancePage, 'legalBenchmarkResearchRefresh.validation_commands', 'legal benchmark research refresh validation binding'),
  () => assertIncludes(maintenancePage, 'Model route legal benchmark risk queue', 'model route legal benchmark risk queue panel'),
  () => assertIncludes(maintenancePage, 'getModelRouteLegalBenchmarkRiskQueue', 'model route legal benchmark risk queue API binding'),
  () => assertIncludes(maintenancePage, 'cheap-first/legal benchmark/user-need risk queue', 'model route legal benchmark risk queue reviewer copy'),
  () => assertIncludes(maintenancePage, 'automatic routing change claimed', 'model route legal benchmark risk queue claim boundary'),
  () => assertIncludes(maintenancePage, 'routing payloads returned', 'model route legal benchmark risk queue privacy boundary'),
  () => assertIncludes(maintenancePage, 'modelRouteLegalBenchmarkRiskQueue.validation_commands', 'model route legal benchmark risk queue validation binding'),
  () => assertIncludes(maintenancePage, 'Legal RAG authority citation gate', 'legal RAG authority citation gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagAuthorityCitationGate', 'legal RAG authority citation gate API binding'),
  () => assertIncludes(maintenancePage, 'Metadata-only authority and citation quality review', 'legal RAG authority citation gate metadata-only copy'),
  () => assertIncludes(maintenancePage, 'citation mismatches', 'legal RAG authority citation mismatch summary'),
  () => assertIncludes(maintenancePage, 'retrieval gaps', 'legal RAG retrieval gap summary'),
  () => assertIncludes(maintenancePage, 'legalRagAuthorityCitationGate.validation_commands', 'legal RAG authority citation validation binding'),
  () => assertIncludes(maintenancePage, 'Legal RAG hallucination triage gate', 'legal RAG hallucination triage gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagHallucinationTriageGate', 'legal RAG hallucination triage gate API binding'),
  () => assertIncludes(maintenancePage, 'Metadata-only fixture taxonomy, blocker status', 'legal RAG hallucination triage metadata-only copy'),
  () => assertIncludes(maintenancePage, 'fixture cases', 'legal RAG hallucination fixture count summary'),
  () => assertIncludes(maintenancePage, 'taxonomy labels', 'legal RAG hallucination taxonomy count summary'),
  () => assertIncludes(maintenancePage, 'missing_citation', 'legal RAG hallucination missing citation taxonomy'),
  () => assertIncludes(maintenancePage, 'stale_regulation', 'legal RAG hallucination stale regulation taxonomy'),
  () => assertIncludes(maintenancePage, 'jurisdiction_mismatch', 'legal RAG hallucination jurisdiction mismatch taxonomy'),
  () => assertIncludes(maintenancePage, 'unsupported_conclusion', 'legal RAG hallucination unsupported conclusion taxonomy'),
  () => assertIncludes(maintenancePage, 'hallucinated_article', 'legal RAG hallucination hallucinated article taxonomy'),
  () => assertIncludes(maintenancePage, 'conflicting_facts', 'legal RAG hallucination conflicting facts taxonomy'),
  () => assertIncludes(maintenancePage, 'release_action', 'legal RAG hallucination release action binding'),
  () => assertIncludes(maintenancePage, 'evidence_signals', 'legal RAG hallucination evidence signal binding'),
  () => assertIncludes(maintenancePage, 'hallucination-free claimed', 'legal RAG hallucination claim boundary panel'),
  () => assertIncludes(maintenancePage, 'retrieved context returned', 'legal RAG hallucination retrieval privacy boundary'),
  () => assertIncludes(maintenancePage, 'credential material returned', 'legal RAG hallucination credential privacy boundary'),
  () => assertIncludes(maintenancePage, 'legalRagHallucinationTriageGate.validation_commands', 'legal RAG hallucination validation binding'),
  () => assertIncludes(maintenancePage, 'Legal RAG abstention escalation gate', 'legal RAG abstention escalation gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagAbstentionEscalationGate', 'legal RAG abstention escalation gate API binding'),
  () => assertIncludes(maintenancePage, 'legalRagAbstentionEscalationGate', 'legal RAG abstention escalation gate state binding'),
  () => assertIncludes(maintenancePage, "['answer', 'answer_with_warning', 'abstain', 'ask_clarification', 'lawyer_review', 'premium_exception']", 'legal RAG abstention decision modes'),
  () => assertIncludes(maintenancePage, 'decision row count', 'legal RAG abstention decision row count summary'),
  () => assertIncludes(maintenancePage, 'evidence sufficient', 'legal RAG abstention evidence sufficiency summary'),
  () => assertIncludes(maintenancePage, 'authority citation gate:', 'legal RAG abstention authority linkage'),
  () => assertIncludes(maintenancePage, 'hallucination triage gate:', 'legal RAG abstention hallucination linkage'),
  () => assertIncludes(maintenancePage, 'cheap-first route:', 'legal RAG abstention cheap-first boundary'),
  () => assertIncludes(maintenancePage, 'premium exception boundary:', 'legal RAG abstention premium exception boundary'),
  () => assertIncludes(maintenancePage, 'raw fixture returned:', 'legal RAG abstention raw fixture privacy boundary'),
  () => assertIncludes(maintenancePage, 'raw legal text returned:', 'legal RAG abstention raw legal text privacy boundary'),
  () => assertIncludes(maintenancePage, 'false / not included', 'legal RAG abstention false/not-included boundary copy'),
  () => assertIncludes(maintenancePage, 'gate.validation_commands', 'legal RAG abstention validation binding'),
  () => assertIncludes(maintenancePage, 'Legal RAG retrieval diagnostics gate', 'legal RAG retrieval diagnostics gate panel'),
  () => assertIncludes(maintenancePage, 'Legal RAG index coverage gate', 'legal RAG index coverage gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagIndexCoverageGate', 'legal RAG index coverage API binding'),
  () => assertIncludes(maintenancePage, 'legalRagIndexCoverageGate', 'legal RAG index coverage state binding'),
  () => assertIncludes(maintenancePage, 'index plan rows', 'legal RAG index coverage row count summary'),
  () => assertIncludes(maintenancePage, 'ready plans', 'legal RAG index coverage ready summary'),
  () => assertIncludes(maintenancePage, 'review plans', 'legal RAG index coverage review summary'),
  () => assertIncludes(maintenancePage, 'blocked plans', 'legal RAG index coverage blocked summary'),
  () => assertIncludes(maintenancePage, 'missing locators', 'legal RAG index coverage missing locator summary'),
  () => assertIncludes(maintenancePage, 'forbidden filters', 'legal RAG index coverage forbidden filter summary'),
  () => assertIncludes(maintenancePage, 'index_binding_status_counts', 'legal RAG index coverage status distribution'),
  () => assertIncludes(maintenancePage, 'locator_status_counts', 'legal RAG index coverage locator distribution'),
  () => assertIncludes(maintenancePage, 'index_plan_policy', 'legal RAG index coverage policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_plan_fields', 'legal RAG index coverage input fields'),
  () => assertIncludes(maintenancePage, 'raw_text_fields_ignored', 'legal RAG index coverage raw fields ignored'),
  () => assertIncludes(maintenancePage, 'source ids returned', 'legal RAG index coverage source-id boundary label'),
  () => assertIncludes(maintenancePage, 'index quality claimed', 'legal RAG index coverage claim boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding readiness gate', 'legal RAG embedding readiness gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingReadinessGate', 'legal RAG embedding readiness API binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingReadinessGate', 'legal RAG embedding readiness state binding'),
  () => assertIncludes(maintenancePage, 'readiness rows', 'legal RAG embedding readiness row count summary'),
  () => assertIncludes(maintenancePage, 'embedding default model', 'legal RAG embedding default model summary'),
  () => assertIncludes(maintenancePage, 'text embedding ready', 'legal RAG text embedding ready summary'),
  () => assertIncludes(maintenancePage, 'multimodal review required', 'legal RAG multimodal embedding review summary'),
  () => assertIncludes(maintenancePage, 'index blockers', 'legal RAG embedding readiness index blocker summary'),
  () => assertIncludes(maintenancePage, 'readiness_status_counts', 'legal RAG embedding readiness status distribution'),
  () => assertIncludes(maintenancePage, 'readiness_policy', 'legal RAG embedding readiness policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_fields', 'legal RAG embedding readiness input fields'),
  () => assertIncludes(maintenancePage, 'forbidden_fields_ignored', 'legal RAG embedding readiness forbidden fields'),
  () => assertIncludes(maintenancePage, 'embedding vectors returned', 'legal RAG embedding vector boundary label'),
  () => assertIncludes(maintenancePage, 'index writes', 'legal RAG embedding index write boundary label'),
  () => assertIncludes(maintenancePage, 'embedding quality claimed', 'legal RAG embedding claim boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding chunk policy gate', 'legal RAG embedding chunk policy gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingChunkPolicyGate', 'legal RAG embedding chunk policy API binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingChunkPolicyGate', 'legal RAG embedding chunk policy state binding'),
  () => assertIncludes(maintenancePage, 'source rows', 'legal RAG embedding chunk policy source row summary'),
  () => assertIncludes(maintenancePage, 'planned chunks', 'legal RAG embedding chunk policy planned chunk summary'),
  () => assertIncludes(maintenancePage, 'estimated tokens', 'legal RAG embedding chunk policy token summary'),
  () => assertIncludes(maintenancePage, 'missing anchors', 'legal RAG embedding chunk policy citation anchor summary'),
  () => assertIncludes(maintenancePage, 'missing locators', 'legal RAG embedding chunk policy locator summary'),
  () => assertIncludes(maintenancePage, 'chunk_policy_status_counts', 'legal RAG embedding chunk policy status distribution'),
  () => assertIncludes(maintenancePage, 'chunk_policy', 'legal RAG embedding chunk policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_fields', 'legal RAG embedding chunk policy accepted fields'),
  () => assertIncludes(maintenancePage, 'forbidden_fields_ignored', 'legal RAG embedding chunk policy forbidden fields'),
  () => assertIncludes(maintenancePage, 'source chunks returned', 'legal RAG embedding chunk policy source chunk boundary label'),
  () => assertIncludes(maintenancePage, 'embedding vectors returned', 'legal RAG embedding chunk policy vector boundary label'),
  () => assertIncludes(maintenancePage, 'creates embeddings', 'legal RAG embedding chunk policy creation boundary label'),
  () => assertIncludes(maintenancePage, 'chunk quality claimed', 'legal RAG embedding chunk policy claim boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding index dry-run gate', 'legal RAG embedding index dry-run gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingIndexDryRunGate', 'legal RAG embedding index dry-run API binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingIndexDryRunGate', 'legal RAG embedding index dry-run state binding'),
  () => assertIncludes(maintenancePage, 'dry-run rows', 'legal RAG embedding index dry-run row summary'),
  () => assertIncludes(maintenancePage, 'manifest ready rows', 'legal RAG embedding index dry-run ready summary'),
  () => assertIncludes(maintenancePage, 'planned vector slots', 'legal RAG embedding index dry-run vector slot summary'),
  () => assertIncludes(maintenancePage, 'dry_run_status_counts', 'legal RAG embedding index dry-run status distribution'),
  () => assertIncludes(maintenancePage, 'commit_action_counts', 'legal RAG embedding index dry-run commit distribution'),
  () => assertIncludes(maintenancePage, 'dry_run_policy', 'legal RAG embedding index dry-run policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_manifest_fields', 'legal RAG embedding index dry-run manifest input fields'),
  () => assertIncludes(maintenancePage, 'repository_persistence_fields', 'legal RAG embedding index dry-run repository field binding'),
  () => assertIncludes(maintenancePage, 'database writes', 'legal RAG embedding index dry-run database write boundary label'),
  () => assertIncludes(maintenancePage, 'index commit claimed', 'legal RAG embedding index dry-run commit claim boundary label'),
  () => assertIncludes(maintenancePage, 'vector store quality claimed', 'legal RAG embedding index dry-run vector quality boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding batch budget gate', 'legal RAG embedding batch budget gate panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingBatchBudgetGate', 'legal RAG embedding batch budget API binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingBatchBudgetGate', 'legal RAG embedding batch budget state binding'),
  () => assertIncludes(maintenancePage, 'budget rows', 'legal RAG embedding batch budget row summary'),
  () => assertIncludes(maintenancePage, 'planned batches', 'legal RAG embedding batch budget planned batch summary'),
  () => assertIncludes(maintenancePage, 'estimated batch cost', 'legal RAG embedding batch budget cost summary'),
  () => assertIncludes(maintenancePage, 'batch price / 1M tokens', 'legal RAG embedding batch budget batch price summary'),
  () => assertIncludes(maintenancePage, 'batch_status_counts', 'legal RAG embedding batch budget status distribution'),
  () => assertIncludes(maintenancePage, 'batch_budget_policy', 'legal RAG embedding batch budget policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_batch_fields', 'legal RAG embedding batch budget input fields'),
  () => assertIncludes(maintenancePage, 'model call allowed', 'legal RAG embedding batch budget no model call binding'),
  () => assertIncludes(maintenancePage, 'embedding batch executed claimed', 'legal RAG embedding batch budget claim boundary label'),
  () => assertIncludes(maintenancePage, 'pricing accuracy claimed', 'legal RAG embedding batch budget pricing claim boundary label'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingBatchPreflight', 'legal RAG embedding batch preflight API type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingBatchPreflight', 'legal RAG embedding batch preflight GET binding'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalRagEmbeddingBatchPreflight', 'legal RAG embedding batch preflight POST binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-batch-preflight', 'legal RAG embedding batch preflight endpoint'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding batch preflight', 'legal RAG embedding batch preflight panel'),
  () => assertIncludes(maintenancePage, 'loadEmbeddingBatchPreflightSample', 'legal RAG embedding batch preflight sample loader'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingBatchPreflight', 'legal RAG embedding batch preflight state binding'),
  () => assertIncludes(maintenancePage, 'defaultLegalRagEmbeddingBatchPreflightPayload', 'legal RAG embedding batch preflight sample payload'),
  () => assertIncludes(maintenancePage, 'hasForbiddenEmbeddingBatchPreflightPayloadText', 'legal RAG embedding batch preflight forbidden payload guard'),
  () => assertIncludes(maintenancePage, 'preflight rows', 'legal RAG embedding batch preflight row summary'),
  () => assertIncludes(maintenancePage, 'duplicate hashes', 'legal RAG embedding batch preflight duplicate hash summary'),
  () => assertIncludes(maintenancePage, 'PII signals', 'legal RAG embedding batch preflight pii summary'),
  () => assertIncludes(maintenancePage, 'secret signals', 'legal RAG embedding batch preflight secret summary'),
  () => assertIncludes(maintenancePage, 'preflight_status_counts', 'legal RAG embedding batch preflight status distribution'),
  () => assertIncludes(maintenancePage, 'preflight_policy', 'legal RAG embedding batch preflight policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_chunk_fields', 'legal RAG embedding batch preflight input fields'),
  () => assertIncludes(maintenancePage, 'source_identifier_hashed', 'legal RAG embedding batch preflight source hash boundary'),
  () => assertIncludes(maintenancePage, 'source text returned', 'legal RAG embedding batch preflight source text boundary'),
  () => assertIncludes(maintenancePage, 'sensitive values returned', 'legal RAG embedding batch preflight sensitive value boundary'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding batch approval packet', 'legal RAG embedding batch approval packet panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingBatchApprovalPacket', 'legal RAG embedding batch approval API binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingBatchApprovalPacket', 'legal RAG embedding batch approval state binding'),
  () => assertIncludes(maintenancePage, 'approval items', 'legal RAG embedding batch approval item summary'),
  () => assertIncludes(maintenancePage, 'ready approvals', 'legal RAG embedding batch approval ready summary'),
  () => assertIncludes(maintenancePage, 'required signoffs', 'legal RAG embedding batch approval signoff summary'),
  () => assertIncludes(maintenancePage, 'max parallel requests', 'legal RAG embedding batch approval serial summary'),
  () => assertIncludes(maintenancePage, 'approval_status_counts', 'legal RAG embedding batch approval status distribution'),
  () => assertIncludes(maintenancePage, 'run_action_counts', 'legal RAG embedding batch approval action distribution'),
  () => assertIncludes(maintenancePage, 'approval_policy', 'legal RAG embedding batch approval policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_approval_fields', 'legal RAG embedding batch approval input fields'),
  () => assertIncludes(maintenancePage, 'approval_identity_collected', 'legal RAG embedding batch approval no identity collection binding'),
  () => assertIncludes(maintenancePage, 'approver identity returned', 'legal RAG embedding batch approval approver identity boundary label'),
  () => assertIncludes(maintenancePage, 'maintainer approval claimed', 'legal RAG embedding batch approval claim boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding batch observation gate', 'legal RAG embedding batch observation gate panel'),
  () => assertIncludes(maintenancePage, 'evaluateLegalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation POST binding'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation GET fallback binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation state binding'),
  () => assertIncludes(maintenancePage, 'defaultLegalRagEmbeddingBatchObservationPayload', 'legal RAG embedding batch observation sample payload'),
  () => assertIncludes(maintenancePage, 'hasForbiddenEmbeddingBatchObservationPayloadText', 'legal RAG embedding batch observation forbidden key guard'),
  () => assertIncludes(maintenancePage, 'ready index reviews', 'legal RAG embedding batch observation ready summary'),
  () => assertIncludes(maintenancePage, 'pending observations', 'legal RAG embedding batch observation pending summary'),
  () => assertIncludes(maintenancePage, 'observed vector slots', 'legal RAG embedding batch observation vector summary'),
  () => assertIncludes(maintenancePage, 'observation_status_counts', 'legal RAG embedding batch observation status distribution'),
  () => assertIncludes(maintenancePage, 'release_action_counts', 'legal RAG embedding batch observation release distribution'),
  () => assertIncludes(maintenancePage, 'observation_policy', 'legal RAG embedding batch observation policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_observation_fields', 'legal RAG embedding batch observation input fields'),
  () => assertIncludes(maintenancePage, 'source_approval_item_id_echoed', 'legal RAG embedding batch observation no approval id echo binding'),
  () => assertIncludes(maintenancePage, 'source approval ids returned', 'legal RAG embedding batch observation source approval boundary label'),
  () => assertIncludes(maintenancePage, 'embedding batch executed claimed', 'legal RAG embedding batch observation execution claim boundary label'),
  () => assertIncludes(maintenancePage, 'index commit claimed', 'legal RAG embedding batch observation index claim boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG embedding index commit review packet', 'legal RAG embedding index commit review packet panel'),
  () => assertIncludes(maintenancePage, 'evaluateLegalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review POST binding'),
  () => assertIncludes(maintenancePage, 'getLegalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review GET fallback binding'),
  () => assertIncludes(maintenancePage, 'legalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review state binding'),
  () => assertIncludes(maintenancePage, 'loadEmbeddingIndexCommitReviewSample', 'legal RAG embedding index commit review load task binding'),
  () => assertIncludes(maintenancePage, 'hasForbiddenEmbeddingIndexCommitReviewPayloadText', 'legal RAG embedding index commit review forbidden key guard'),
  () => assertIncludes(maintenancePage, 'commit review items', 'legal RAG embedding index commit review item summary'),
  () => assertIncludes(maintenancePage, 'ready commit reviews', 'legal RAG embedding index commit review ready summary'),
  () => assertIncludes(maintenancePage, 'held commit reviews', 'legal RAG embedding index commit review held summary'),
  () => assertIncludes(maintenancePage, 'blocked commit reviews', 'legal RAG embedding index commit review blocked summary'),
  () => assertIncludes(maintenancePage, 'required signoffs', 'legal RAG embedding index commit review signoff summary'),
  () => assertIncludes(maintenancePage, 'commit_review_status_counts', 'legal RAG embedding index commit review status distribution'),
  () => assertIncludes(maintenancePage, 'commit_review_action_counts', 'legal RAG embedding index commit review action distribution'),
  () => assertIncludes(maintenancePage, 'commit_review_action', 'legal RAG embedding index commit review action binding'),
  () => assertIncludes(maintenancePage, 'pre_commit_checks', 'legal RAG embedding index commit review pre-commit checks binding'),
  () => assertIncludes(maintenancePage, 'commit_review_policy', 'legal RAG embedding index commit review policy binding'),
  () => assertIncludes(maintenancePage, 'accepted_review_fields', 'legal RAG embedding index commit review input fields'),
  () => assertIncludes(maintenancePage, 'commit_record_written', 'legal RAG embedding index commit review no commit record binding'),
  () => assertIncludes(maintenancePage, 'committer_identity_collected', 'legal RAG embedding index commit review no committer identity binding'),
  () => assertIncludes(maintenancePage, 'committer identity returned', 'legal RAG embedding index commit review committer boundary label'),
  () => assertIncludes(maintenancePage, 'maintainer commit approval claimed', 'legal RAG embedding index commit review approval claim boundary label'),
  () => assertIncludes(maintenancePage, 'index commit allowed', 'legal RAG embedding index commit review no index commit binding'),
  () =>
    assertIncludes(
      maintenancePage,
      'Legal RAG embedding index post-commit verification gate',
      'legal RAG embedding index post-commit verification gate panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'evaluateLegalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification POST binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getLegalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification GET fallback binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'legalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'defaultLegalRagEmbeddingIndexPostCommitVerificationPayload',
      'legal RAG embedding index post-commit verification sample payload',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'loadEmbeddingIndexPostCommitVerificationSample',
      'legal RAG embedding index post-commit verification load task binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'hasForbiddenEmbeddingIndexPostCommitVerificationPayloadText',
      'legal RAG embedding index post-commit verification forbidden key guard',
    ),
  () => assertIncludes(maintenancePage, 'verification rows', 'legal RAG embedding index post-commit verification row summary'),
  () =>
    assertIncludes(
      maintenancePage,
      'verified for retrieval diagnostics',
      'legal RAG embedding index post-commit verification verified summary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'verification review required',
      'legal RAG embedding index post-commit verification review summary',
    ),
  () => assertIncludes(maintenancePage, 'verification blocked', 'legal RAG embedding index post-commit verification blocked summary'),
  () =>
    assertIncludes(
      maintenancePage,
      'verification_status_counts',
      'legal RAG embedding index post-commit verification status distribution',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'verification_action_counts',
      'legal RAG embedding index post-commit verification action distribution',
    ),
  () => assertIncludes(maintenancePage, 'post_commit_status', 'legal RAG embedding index post-commit status binding'),
  () => assertIncludes(maintenancePage, 'verification_action', 'legal RAG embedding index post-commit action binding'),
  () => assertIncludes(maintenancePage, 'rollback_action', 'legal RAG embedding index post-commit rollback binding'),
  () =>
    assertIncludes(
      maintenancePage,
      'post_commit_verification_policy',
      'legal RAG embedding index post-commit verification policy binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'accepted_verification_fields',
      'legal RAG embedding index post-commit verification input fields',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'post_commit_observation_only',
      'legal RAG embedding index post-commit verification observation-only binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'retrieval diagnostics review only',
      'legal RAG embedding index post-commit verification diagnostics-only label',
    ),
  () => assertIncludes(maintenancePage, 'retrieval use allowed', 'legal RAG embedding index post-commit no retrieval use label'),
  () =>
    assertIncludes(
      maintenancePage,
      'Legal RAG embedding retrieval diagnostics handoff gate',
      'legal RAG embedding retrieval diagnostics handoff gate panel',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'evaluateLegalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff POST binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'getLegalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff GET fallback binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'legalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff state binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'defaultLegalRagEmbeddingRetrievalDiagnosticsHandoffPayload',
      'legal RAG embedding retrieval diagnostics handoff sample payload',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'loadEmbeddingRetrievalDiagnosticsHandoffSample',
      'legal RAG embedding retrieval diagnostics handoff load task binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'hasForbiddenEmbeddingRetrievalDiagnosticsHandoffPayloadText',
      'legal RAG embedding retrieval diagnostics handoff forbidden key guard',
    ),
  () => assertIncludes(maintenancePage, 'handoff rows', 'legal RAG embedding retrieval diagnostics handoff row summary'),
  () => assertIncludes(maintenancePage, 'ready handoffs', 'legal RAG embedding retrieval diagnostics handoff ready summary'),
  () => assertIncludes(maintenancePage, 'hold handoffs', 'legal RAG embedding retrieval diagnostics handoff hold summary'),
  () => assertIncludes(maintenancePage, 'blocked handoffs', 'legal RAG embedding retrieval diagnostics handoff blocked summary'),
  () => assertIncludes(maintenancePage, 'handoff_status', 'legal RAG embedding retrieval diagnostics handoff status binding'),
  () => assertIncludes(maintenancePage, 'handoff_action', 'legal RAG embedding retrieval diagnostics handoff action binding'),
  () =>
    assertIncludes(
      maintenancePage,
      'post_commit_verification_status',
      'legal RAG embedding retrieval diagnostics handoff post-commit status binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'retrieval_diagnostics_review_allowed',
      'legal RAG embedding retrieval diagnostics handoff diagnostics review boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'production_retrieval_allowed',
      'legal RAG embedding retrieval diagnostics handoff production retrieval boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'retrieval_query_allowed',
      'legal RAG embedding retrieval diagnostics handoff query boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'retrieved_context_allowed',
      'legal RAG embedding retrieval diagnostics handoff context boundary',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'handoff_status_counts',
      'legal RAG embedding retrieval diagnostics handoff status distribution',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'handoff_action_counts',
      'legal RAG embedding retrieval diagnostics handoff action distribution',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'safe_handoff_payload_fields',
      'legal RAG embedding retrieval diagnostics handoff safe payload fields binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'source_id_echoed',
      'legal RAG embedding retrieval diagnostics handoff no source id echo binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'query_payload_collected',
      'legal RAG embedding retrieval diagnostics handoff no query payload binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'retrieved_context_collected',
      'legal RAG embedding retrieval diagnostics handoff no context payload binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'committer_identity_collected',
      'legal RAG embedding retrieval diagnostics handoff no committer identity binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'handoff_payload_materialized',
      'legal RAG embedding retrieval diagnostics handoff no materialized payload binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'handoff_policy',
      'legal RAG embedding retrieval diagnostics handoff policy binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'allows_retrieval_diagnostics_review_only',
      'legal RAG embedding retrieval diagnostics handoff diagnostics-only policy',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'allows_production_retrieval',
      'legal RAG embedding retrieval diagnostics handoff no production retrieval policy',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG authority citation gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG index coverage gate</h2>',
      'authority citation gate precedes index coverage gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG index coverage gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding readiness gate</h2>',
      'index coverage gate precedes embedding readiness',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding readiness gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding chunk policy gate</h2>',
      'embedding readiness gate precedes chunk policy gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding chunk policy gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index dry-run gate</h2>',
      'chunk policy gate precedes embedding index dry-run gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index dry-run gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch budget gate</h2>',
      'embedding index dry-run gate precedes embedding batch budget gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch budget gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch approval packet</h2>',
      'embedding batch budget gate precedes embedding batch approval packet',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch approval packet</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch observation gate</h2>',
      'embedding batch approval packet precedes embedding batch observation gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch observation gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index commit review packet</h2>',
      'embedding batch observation gate precedes embedding index commit review packet',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index commit review packet</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index post-commit verification gate</h2>',
      'embedding index commit review packet precedes post-commit verification gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index post-commit verification gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding retrieval diagnostics handoff gate</h2>',
      'embedding index post-commit verification gate precedes retrieval diagnostics handoff',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding retrieval diagnostics handoff gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval diagnostics gate</h2>',
      'embedding retrieval diagnostics handoff gate precedes retrieval diagnostics',
    ),
  () =>
    assertBefore(
      maintenancePage,
      "label: 'Legal RAG embedding index post-commit verification gate'",
      "label: 'Legal RAG embedding retrieval diagnostics handoff gate'",
      'post-commit verification load task precedes handoff load task',
    ),
  () =>
    assertBefore(
      maintenancePage,
      "label: 'Legal RAG embedding retrieval diagnostics handoff gate'",
      "label: 'Legal RAG retrieval diagnostics gate'",
      'handoff load task precedes retrieval diagnostics load task',
    ),
  () => assertIncludes(maintenancePage, 'getLegalRagRetrievalDiagnosticsGate', 'legal RAG retrieval diagnostics gate API binding'),
  () => assertIncludes(maintenancePage, 'legalRagRetrievalDiagnosticsGate', 'legal RAG retrieval diagnostics gate state binding'),
  () => assertIncludes(maintenancePage, 'diagnostic rows', 'legal RAG retrieval diagnostics row count summary'),
  () => assertIncludes(maintenancePage, 'ready rows', 'legal RAG retrieval diagnostics ready summary'),
  () => assertIncludes(maintenancePage, 'review rows', 'legal RAG retrieval diagnostics review summary'),
  () => assertIncludes(maintenancePage, 'blocked rows', 'legal RAG retrieval diagnostics blocked summary'),
  () => assertIncludes(maintenancePage, 'authority coverage', 'legal RAG retrieval diagnostics authority coverage summary'),
  () => assertIncludes(maintenancePage, 'retrieval depth gaps', 'legal RAG retrieval diagnostics depth gap summary'),
  () => assertIncludes(maintenancePage, 'jurisdiction/freshness gaps', 'legal RAG retrieval diagnostics jurisdiction/freshness summary'),
  () => assertIncludes(maintenancePage, 'cheap-first retry count', 'legal RAG retrieval diagnostics cheap-first retry summary'),
  () => assertIncludes(maintenancePage, 'query_intent', 'legal RAG retrieval diagnostics query intent binding'),
  () => assertIncludes(maintenancePage, 'retrieval_status', 'legal RAG retrieval diagnostics retrieval status binding'),
  () => assertIncludes(maintenancePage, 'source_coverage_status', 'legal RAG retrieval diagnostics source coverage binding'),
  () => assertIncludes(maintenancePage, 'top_k_depth_status', 'legal RAG retrieval diagnostics top-k binding'),
  () => assertIncludes(maintenancePage, 'jurisdiction_status', 'legal RAG retrieval diagnostics jurisdiction binding'),
  () => assertIncludes(maintenancePage, 'freshness_status', 'legal RAG retrieval diagnostics freshness binding'),
  () => assertIncludes(maintenancePage, 'cheap_first_action', 'legal RAG retrieval diagnostics cheap-first action binding'),
  () => assertIncludes(maintenancePage, 'release_action', 'legal RAG retrieval diagnostics release action binding'),
  () => assertIncludes(maintenancePage, 'linked_gate_ids', 'legal RAG retrieval diagnostics linked gate ids binding'),
  () => assertIncludes(maintenancePage, 'legal-rag-index-binding', 'legal RAG retrieval diagnostics index binding linkage'),
  () => assertIncludes(maintenancePage, 'legal-rag-authority-citation-gate', 'legal RAG retrieval diagnostics authority linkage'),
  () => assertIncludes(maintenancePage, 'legal-rag-abstention-escalation-gate', 'legal RAG retrieval diagnostics abstention linkage'),
  () => assertIncludes(maintenancePage, 'Claim/privacy boundary', 'legal RAG retrieval diagnostics boundary panel'),
  () => assertIncludes(maintenancePage, 'raw query', 'legal RAG retrieval diagnostics raw query false boundary label'),
  () => assertIncludes(maintenancePage, 'raw context', 'legal RAG retrieval diagnostics raw context false boundary label'),
  () => assertIncludes(maintenancePage, 'raw legal text', 'legal RAG retrieval diagnostics raw legal text false boundary label'),
  () => assertIncludes(maintenancePage, 'prompts', 'legal RAG retrieval diagnostics prompt boundary label'),
  () => assertIncludes(maintenancePage, 'model output', 'legal RAG retrieval diagnostics model output boundary label'),
  () => assertIncludes(maintenancePage, 'credentials', 'legal RAG retrieval diagnostics credential boundary label'),
  () => assertIncludes(maintenancePage, 'includedBoundaryLabel(item.value)', 'legal RAG retrieval diagnostics false/not-included boundary binding'),
  () => assertIncludes(maintenancePage, 'legalRagRetrievalDiagnosticsGate.validation_commands', 'legal RAG retrieval diagnostics validation binding'),
  () => assertIncludes(maintenancePage, 'Legal RAG retrieval observation gate', 'legal RAG retrieval observation gate panel'),
  () => assertIncludes(maintenancePage, 'evaluateLegalRagRetrievalObservationGate', 'legal RAG retrieval observation API binding'),
  () => assertIncludes(maintenancePage, 'legalRagRetrievalObservationGate', 'legal RAG retrieval observation state binding'),
  () => assertIncludes(maintenancePage, 'defaultLegalRagRetrievalObservationPayload', 'legal RAG retrieval observation sample payload'),
  () => assertIncludes(maintenancePage, 'retrievalObservationPayloadText', 'legal RAG retrieval observation payload editor'),
  () => assertIncludes(maintenancePage, 'Evaluate observations', 'legal RAG retrieval observation submit button'),
  () => assertIncludes(maintenancePage, 'observation rows', 'legal RAG retrieval observation row count summary'),
  () => assertIncludes(maintenancePage, 'retrieval_status_counts', 'legal RAG retrieval observation status distribution'),
  () => assertIncludes(maintenancePage, 'release_action_counts', 'legal RAG retrieval observation release distribution'),
  () => assertIncludes(maintenancePage, 'accepted_container_keys', 'legal RAG retrieval observation input contract'),
  () => assertIncludes(maintenancePage, 'source_validation_counts', 'legal RAG retrieval observation source validation counts'),
  () => assertIncludes(maintenancePage, 'hasForbiddenRetrievalObservationPayloadText', 'legal RAG retrieval observation forbidden key guard'),
  () => assertIncludes(maintenancePage, 'source ids are accepted as inputs but are not returned', 'legal RAG retrieval observation source-id boundary copy'),
  () => assertIncludes(maintenancePage, 'query content returned', 'legal RAG retrieval observation query boundary label'),
  () => assertIncludes(maintenancePage, 'gateway payloads returned', 'legal RAG retrieval observation gateway payload boundary label'),
  () => assertIncludes(maintenancePage, 'Legal RAG answer release readiness gate', 'legal RAG answer release readiness gate panel'),
  () => assertIncludes(maintenancePage, 'legalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness state binding'),
  () => assertIncludes(maintenancePage, 'getLegalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness GET binding'),
  () => assertIncludes(maintenancePage, 'evaluateLegalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness POST binding'),
  () => assertIncludes(maintenancePage, 'defaultLegalRagAnswerReleaseReadinessPayload', 'legal RAG answer release readiness sample payload'),
  () => assertIncludes(maintenancePage, 'loadAnswerReleaseReadinessSample', 'legal RAG answer release readiness load task binding'),
  () => assertIncludes(maintenancePage, 'hasForbiddenAnswerReleaseReadinessPayloadText', 'legal RAG answer release readiness forbidden key guard'),
  () => assertIncludes(maintenancePage, 'answer rows', 'legal RAG answer release readiness row summary'),
  () => assertIncludes(maintenancePage, 'ready answers', 'legal RAG answer release readiness ready summary'),
  () => assertIncludes(maintenancePage, 'review required', 'legal RAG answer release readiness review summary'),
  () => assertIncludes(maintenancePage, 'blocked answers', 'legal RAG answer release readiness blocked summary'),
  () => assertIncludes(maintenancePage, 'internal drafts', 'legal RAG answer release readiness internal draft summary'),
  () => assertIncludes(maintenancePage, 'citation packets', 'legal RAG answer release readiness citation packet summary'),
  () => assertIncludes(maintenancePage, 'lawyer reviews', 'legal RAG answer release readiness lawyer review summary'),
  () => assertIncludes(maintenancePage, 'client deliveries', 'legal RAG answer release readiness client delivery summary'),
  () => assertIncludes(maintenancePage, 'answer_release_status', 'legal RAG answer release readiness status binding'),
  () => assertIncludes(maintenancePage, 'answer_release_action', 'legal RAG answer release readiness action binding'),
  () => assertIncludes(maintenancePage, 'internal_answer_draft_allowed', 'legal RAG answer release readiness draft boundary'),
  () => assertIncludes(maintenancePage, 'citation_packet_required', 'legal RAG answer release readiness citation boundary'),
  () => assertIncludes(maintenancePage, 'lawyer_review_required', 'legal RAG answer release readiness lawyer review boundary'),
  () => assertIncludes(maintenancePage, 'client_delivery_allowed', 'legal RAG answer release readiness client delivery boundary'),
  () => assertIncludes(maintenancePage, 'answer_release_status_counts', 'legal RAG answer release readiness status distribution'),
  () => assertIncludes(maintenancePage, 'answer_release_action_counts', 'legal RAG answer release readiness action distribution'),
  () => assertIncludes(maintenancePage, 'answer_release_policy', 'legal RAG answer release readiness policy binding'),
  () => assertIncludes(maintenancePage, 'requires_ready_retrieval_status', 'legal RAG answer release readiness retrieval requirement'),
  () => assertIncludes(maintenancePage, 'requires_citation_packet_for_all_ready_rows', 'legal RAG answer release readiness citation policy'),
  () => assertIncludes(maintenancePage, 'allows_client_delivery', 'legal RAG answer release readiness no client delivery policy'),
  () => assertIncludes(maintenancePage, 'allows_legal_advice_claim', 'legal RAG answer release readiness no legal advice policy'),
  () => assertIncludes(maintenancePage, 'client_delivery_materialized', 'legal RAG answer release readiness no materialized delivery binding'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval diagnostics gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval observation gate</h2>',
      'retrieval diagnostics precedes retrieval observation gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval observation gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG answer release readiness gate</h2>',
      'retrieval observation gate precedes answer release readiness',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG answer release readiness gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG benchmark alignment scorecard</h2>',
      'answer release readiness precedes benchmark alignment',
    ),
  () =>
    assertBefore(
      maintenancePage,
      "label: 'Legal RAG retrieval observation gate'",
      "label: 'Legal RAG answer release readiness gate'",
      'retrieval observation load task precedes answer release readiness load task',
    ),
  () =>
    assertBefore(
      maintenancePage,
      "label: 'Legal RAG answer release readiness gate'",
      "label: 'Legal RAG benchmark alignment'",
      'answer release readiness load task precedes benchmark alignment load task',
    ),
  () => assertIncludes(maintenancePage, 'Legal RAG benchmark alignment scorecard', 'legal RAG benchmark alignment panel'),
  () => assertIncludes(maintenancePage, 'getLegalRagBenchmarkAlignment', 'legal RAG benchmark alignment API binding'),
  () => assertIncludes(maintenancePage, 'legalRagBenchmarkAlignment', 'legal RAG benchmark alignment state binding'),
  () => assertIncludes(maintenancePage, 'blocked claims', 'legal RAG benchmark alignment blocked claim summary'),
  () => assertIncludes(maintenancePage, 'crosswalk gaps', 'legal RAG benchmark alignment crosswalk gap summary'),
  () => assertIncludes(maintenancePage, 'benchmark_signal_ids', 'legal RAG benchmark alignment signal binding'),
  () => assertIncludes(maintenancePage, 'missing_validation_targets', 'legal RAG benchmark alignment missing target binding'),
  () => assertIncludes(maintenancePage, 'premium_exception_allowed', 'legal RAG benchmark alignment premium exception boundary'),
  () => assertIncludes(maintenancePage, 'returns_public_benchmark_text', 'legal RAG benchmark alignment public text boundary'),
  () => assertIncludes(maintenancePage, 'returns_retrieved_context', 'legal RAG benchmark alignment retrieved context boundary'),
  () => assertIncludes(maintenancePage, 'Legal RAG export readiness packet', 'legal RAG export readiness packet panel'),
  () => assertIncludes(maintenancePage, 'getMaintenanceLegalRagExportReadinessPacket', 'legal RAG export readiness API binding'),
  () => assertIncludes(maintenancePage, 'legalRagExportReadinessPacket', 'legal RAG export readiness state binding'),
  () => assertIncludes(maintenancePage, 'release_action', 'legal RAG export readiness release action binding'),
  () => assertIncludes(maintenancePage, 'deep-review-export-readiness-route-gate', 'legal RAG export readiness route gate linkage'),
  () => assertIncludes(maintenancePage, 'raw report returned', 'legal RAG export readiness raw report boundary label'),
  () => assertIncludes(maintenancePage, 'network calls', 'legal RAG export readiness network boundary label'),
  () => assertIncludes(maintenancePage, 'Final document delivery release gate', 'final document delivery release gate panel'),
  () =>
    assertIncludes(
      maintenancePage,
      'getMaintenanceFinalDocumentDeliveryReleaseGate',
      'final document delivery release gate API binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'finalDocumentDeliveryReleaseGate',
      'final document delivery release gate state binding',
    ),
  () => assertIncludes(maintenancePage, 'ready_for_final_delivery', 'final document delivery ready label'),
  () => assertIncludes(maintenancePage, 'client_delivery_allowed', 'final document delivery client delivery binding'),
  () => assertIncludes(maintenancePage, 'linked_release_gates', 'final document delivery linked gates panel'),
  () => assertIncludes(maintenancePage, 'raw document text', 'final document delivery raw document boundary label'),
  () => assertIncludes(maintenancePage, 'client contact details', 'final document delivery contact boundary label'),
  () => assertIncludes(maintenancePage, 'provider settlement verified', 'final document delivery provider claim boundary'),
  () => assertIncludes(maintenancePage, 'Small legal document benchmark runbook evidence', 'small legal document benchmark runbook evidence panel'),
  () =>
    assertIncludes(
      maintenancePage,
      'getSmallLegalDocumentBenchmarkRunbookEvidence',
      'small legal document benchmark runbook API binding',
    ),
  () =>
    assertIncludes(
      maintenancePage,
      'smallLegalDocumentBenchmarkRunbookEvidence',
      'small legal document benchmark runbook state binding',
    ),
  () => assertIncludes(maintenancePage, 'max_parallel_requests', 'small legal document benchmark runbook serial cap'),
  () => assertIncludes(maintenancePage, 'runbook_steps', 'small legal document benchmark runbook steps binding'),
  () => assertIncludes(maintenancePage, 'evidence_rows', 'small legal document benchmark evidence rows binding'),
  () => assertIncludes(maintenancePage, 'document_benchmark_rows', 'small legal document benchmark document rows binding'),
  () => assertIncludes(maintenancePage, 'fact_consistency_rows', 'small legal document benchmark fact rows binding'),
  () => assertIncludes(maintenancePage, 'delivery_gate_rows', 'small legal document benchmark delivery rows binding'),
  () => assertIncludes(maintenancePage, 'public_benchmark_score_claimed', 'small legal document benchmark public score boundary'),
  () => assertIncludes(maintenancePage, 'production_legal_quality_claimed', 'small legal document benchmark production claim boundary'),
  () => assertIncludes(maintenancePage, 'returns_generated_text', 'small legal document benchmark generated text boundary'),
  () => assertIncludes(maintenancePage, 'network_called', 'small legal document benchmark network boundary'),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Legal RAG export readiness packet</h2>',
      '<h2 className="text-xl font-black text-stone-950">Final document delivery release gate</h2>',
      'final document delivery gate follows Legal RAG export readiness',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Final document delivery release gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Small legal document benchmark runbook evidence</h2>',
      'small legal document runbook evidence follows final document delivery gate',
    ),
  () =>
    assertBefore(
      maintenancePage,
      '<h2 className="text-xl font-black text-stone-950">Small legal document benchmark runbook evidence</h2>',
      '<h2 className="text-xl font-black text-stone-950">Legal RAG hallucination triage gate</h2>',
      'small legal document runbook evidence precedes hallucination triage',
    ),
  () => assertIncludes(maintenanceApi, 'linked_public_source_ids', 'user need benchmark public source type'),
  () => assertIncludes(maintenanceApi, 'returns_public_benchmark_text', 'user need benchmark public text boundary type'),
  () => assertIncludes(maintenanceApi, 'public_sampler_network_access', 'user need benchmark public sampler summary type'),
  () => assertIncludes(maintenanceApi, 'linked_calibration_task_ids', 'user need benchmark calibration task type'),
  () => assertIncludes(maintenanceApi, 'returns_calibration_payloads', 'user need benchmark calibration payload boundary type'),
  () => assertIncludes(maintenanceApi, 'cheap_first_calibration_mapped_need_count', 'user need benchmark calibration summary type'),
  () => assertIncludes(maintenanceApi, 'UserNeedGeminiRouteCoverage', 'user need Gemini route coverage type'),
  () => assertIncludes(maintenanceApi, 'UserNeedGeminiRouteCoverageRow', 'user need Gemini route coverage row type'),
  () => assertIncludes(maintenanceApi, 'getUserNeedGeminiRouteCoverage', 'user need Gemini route coverage API'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/user-needs/gemini-route-coverage', 'user need Gemini route coverage endpoint'),
  () => assertIncludes(maintenanceApi, 'linked_route_tasks: string[]', 'user need Gemini linked route task type'),
  () => assertIncludes(maintenanceApi, 'linked_default_models: string[]', 'user need Gemini linked default model type'),
  () => assertIncludes(maintenanceApi, 'returns_route_payloads: boolean', 'user need Gemini route payload boundary type'),
  () => assertIncludes(maintenanceApi, 'claims_default_route_changed: boolean', 'user need Gemini default route claim boundary type'),
  () => assertIncludes(maintenanceApi, 'UserNeedImplementationPriorityQueue', 'user need implementation queue type'),
  () => assertIncludes(maintenanceApi, 'getUserNeedImplementationPriorityQueue', 'user need implementation queue API'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/user-needs/implementation-priority-queue', 'user need implementation queue endpoint'),
  () => assertIncludes(maintenanceApi, 'queue_items', 'user need implementation queue item list type'),
  () => assertIncludes(maintenanceApi, 'imports_public_benchmark_samples', 'user need implementation queue public sample boundary type'),
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
  () => assertIncludes(maintenanceApi, 'LegalBenchmarkResearchRefresh', 'legal benchmark research refresh type'),
  () => assertIncludes(maintenanceApi, 'research_sources', 'legal benchmark research refresh source metadata type'),
  () => assertIncludes(maintenanceApi, 'refresh_rows', 'legal benchmark research refresh row type'),
  () => assertIncludes(maintenanceApi, 'user_need_rows', 'legal benchmark research refresh user need row type'),
  () => assertIncludes(maintenanceApi, 'claim_boundary', 'legal benchmark research refresh claim boundary type'),
  () => assertIncludes(maintenanceApi, 'getLegalBenchmarkResearchRefresh', 'legal benchmark research refresh API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-benchmark-research-refresh', 'legal benchmark research refresh endpoint'),
  () => assertIncludes(maintenanceApi, 'cheap_first_local_validation_status', 'legal benchmark research refresh cheap-first/local type'),
  () => assertIncludes(maintenanceApi, 'ModelRouteLegalBenchmarkRiskQueue', 'model route legal benchmark risk queue type'),
  () => assertIncludes(maintenanceApi, 'queue_rows', 'model route legal benchmark risk queue rows type'),
  () => assertIncludes(maintenanceApi, 'routing_policy', 'model route legal benchmark risk queue routing policy type'),
  () => assertIncludes(maintenanceApi, 'privacy_boundary', 'model route legal benchmark risk queue privacy boundary type'),
  () => assertIncludes(maintenanceApi, 'claim_boundary', 'model route legal benchmark risk queue claim boundary type'),
  () => assertIncludes(maintenanceApi, 'returns_routing_payloads', 'model route legal benchmark risk queue routing payload boundary'),
  () => assertIncludes(maintenanceApi, 'getModelRouteLegalBenchmarkRiskQueue', 'model route legal benchmark risk queue API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/model-route-legal-benchmark-risk-queue', 'model route legal benchmark risk queue endpoint'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureCheapFirstBenchmarkGate', 'legal fixture cheap-first benchmark gate type'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureCheapFirstBenchmarkGatePrivacyBoundary', 'legal fixture cheap-first benchmark gate explicit privacy boundary type'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureCheapFirstBenchmarkGateClaimBoundary', 'legal fixture cheap-first benchmark gate explicit claim boundary type'),
  () => assertIncludes(maintenanceApi, 'gate_rows', 'legal fixture cheap-first benchmark gate rows type'),
  () => assertIncludes(maintenanceApi, 'document_benchmark_summary', 'legal fixture cheap-first benchmark document summary type'),
  () => assertIncludes(maintenanceApi, 'document_benchmark_rows', 'legal fixture cheap-first benchmark document rows type'),
  () => assertIncludes(maintenanceApi, 'raw_document_snippets_returned', 'legal fixture cheap-first benchmark no raw document snippets type'),
  () => assertIncludes(maintenanceApi, 'raw_candidate_text_returned', 'legal fixture cheap-first benchmark no raw candidate text type'),
  () => assertIncludes(maintenanceApi, 'document_benchmark_required_for_default_change', 'legal fixture cheap-first benchmark required routing type'),
  () => assertIncludes(maintenanceApi, 'linked_calibration_task_ids: string[]', 'legal fixture cheap-first benchmark linked calibration task type'),
  () => assertIncludes(maintenanceApi, 'calibration_status: string', 'legal fixture cheap-first benchmark calibration status type'),
  () => assertIncludes(maintenanceApi, 'calibration_decisions: string[]', 'legal fixture cheap-first benchmark calibration decisions type'),
  () => assertIncludes(maintenanceApi, 'calibration_release_gates: string[]', 'legal fixture cheap-first benchmark calibration release gates type'),
  () => assertIncludes(maintenanceApi, 'calibration_required_for_default_change', 'legal fixture cheap-first benchmark calibration routing requirement type'),
  () => assertIncludes(maintenanceApi, 'returns_calibration_payloads', 'legal fixture cheap-first benchmark no calibration payload boundary type'),
  () => assertIncludes(maintenanceApi, 'legal_document_benchmark_scores_claimed', 'legal fixture cheap-first benchmark no benchmark score claim type'),
  () => assertIncludes(maintenanceApi, 'default_change_evidence_allowed', 'legal fixture cheap-first benchmark gate evidence decision type'),
  () => assertIncludes(maintenanceApi, 'getModelOpsLegalFixtureCheapFirstBenchmarkGate', 'legal fixture cheap-first benchmark gate API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate', 'legal fixture cheap-first benchmark gate endpoint'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket', 'legal fixture cheap-first default promotion packet type'),
  () => assertIncludes(maintenanceApi, 'promotion_items', 'legal fixture cheap-first default promotion packet items type'),
  () => assertIncludes(maintenanceApi, 'requires_cheap_first_calibration_pass', 'legal fixture cheap-first default promotion calibration requirement type'),
  () => assertIncludes(maintenanceApi, 'fact_consistency_status: string', 'legal fixture cheap-first default promotion fact status type'),
  () => assertIncludes(maintenanceApi, 'linked_calibration_task_count: number', 'legal fixture cheap-first default promotion linked calibration summary type'),
  () => assertIncludes(maintenanceApi, 'default_change_allowed_by_packet', 'legal fixture cheap-first default promotion packet no auto-default type'),
  () => assertIncludes(maintenanceApi, 'getModelOpsLegalFixtureCheapFirstDefaultPromotionPacket', 'legal fixture cheap-first default promotion packet API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet', 'legal fixture cheap-first default promotion packet endpoint'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureEvidenceHandoff', 'legal fixture evidence handoff type'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureEvidenceHandoffRow', 'legal fixture evidence handoff row type'),
  () => assertIncludes(maintenanceApi, 'ModelOpsLegalFixtureEvidenceHandoffCheck', 'legal fixture evidence handoff check type'),
  () => assertIncludes(maintenanceApi, 'handoff_rows', 'legal fixture evidence handoff rows type'),
  () => assertIncludes(maintenanceApi, 'handoff_evidence_summary', 'legal fixture evidence handoff source summary type'),
  () => assertIncludes(maintenanceApi, 'raw_input_field_count', 'legal fixture evidence handoff input boundary summary type'),
  () => assertIncludes(maintenanceApi, 'completion_claimed', 'legal fixture evidence handoff completion non-claim type'),
  () => assertIncludes(maintenanceApi, 'getModelOpsLegalFixtureEvidenceHandoff', 'legal fixture evidence handoff API binding'),
  () => assertIncludes(maintenanceApi, 'evaluateModelOpsLegalFixtureEvidenceHandoff', 'legal fixture evidence handoff evaluate API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-review-benchmark/evidence-handoff', 'legal fixture evidence handoff endpoint'),
  () => assertIncludes(maintenanceApi, 'ModelOpsCheapFirstReleaseDecision', 'maintenance cheap-first release decision type'),
  () => assertIncludes(maintenanceApi, 'getModelOpsCheapFirstReleaseDecision', 'maintenance cheap-first release decision API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/aihub/models/cheap-first-release-decision', 'maintenance cheap-first release decision endpoint'),
  () => assertIncludes(maintenancePage, 'Legal fixture cheap-first benchmark gate', 'legal fixture cheap-first benchmark gate panel'),
  () => assertIncludes(maintenancePage, 'Document benchmark gate', 'legal fixture cheap-first benchmark document panel'),
  () => assertIncludes(maintenancePage, 'document_benchmark_rows ?? []', 'legal fixture cheap-first benchmark document rows fallback'),
  () => assertIncludes(maintenancePage, 'raw document snippets', 'legal fixture cheap-first benchmark no raw document snippets label'),
  () => assertIncludes(maintenancePage, 'raw candidate text', 'legal fixture cheap-first benchmark no raw candidate text label'),
  () => assertIncludes(maintenancePage, 'modelOpsLegalFixtureCheapFirstBenchmarkGate', 'legal fixture cheap-first benchmark gate state binding'),
  () => assertIncludes(maintenancePage, 'raw fixture text', 'legal fixture cheap-first benchmark gate raw fixture boundary label'),
  () => assertIncludes(maintenancePage, 'automatic default change', 'legal fixture cheap-first benchmark gate no default-change claim'),
  () => assertIncludes(maintenancePage, 'configuration_write_allowed', 'legal fixture cheap-first benchmark gate no config write binding'),
  () => assertIncludes(maintenancePage, 'linked_calibration_task_ids', 'legal fixture cheap-first benchmark calibration task binding'),
  () => assertIncludes(maintenancePage, 'calibration_decisions', 'legal fixture cheap-first benchmark calibration decision binding'),
  () => assertIncludes(maintenancePage, 'calibration required', 'legal fixture cheap-first benchmark calibration required label'),
  () => assertIncludes(maintenancePage, 'calibration payloads', 'legal fixture cheap-first benchmark no calibration payload label'),
  () => assertIncludes(maintenancePage, 'Legal fixture cheap-first default promotion packet', 'legal fixture cheap-first default promotion packet panel'),
  () => assertIncludes(maintenancePage, 'modelOpsLegalFixtureCheapFirstDefaultPromotionPacket', 'legal fixture cheap-first default promotion packet state binding'),
  () => assertIncludes(maintenancePage, 'legalFixtureDefaultPromotionRows', 'legal fixture cheap-first default promotion packet rows fallback'),
  () => assertIncludes(maintenancePage, 'promotion_items ?? []', 'legal fixture cheap-first default promotion packet no undefined rows'),
  () => assertIncludes(maintenancePage, 'default_change_allowed_by_packet', 'legal fixture cheap-first default promotion packet no auto default label'),
  () => assertIncludes(maintenancePage, 'configuration_write_allowed', 'legal fixture cheap-first default promotion packet no config write label'),
  () => assertIncludes(maintenancePage, 'traffic_shift_allowed', 'legal fixture cheap-first default promotion packet no traffic shift label'),
  () => assertIncludes(maintenancePage, 'requires_cheap_first_calibration_pass', 'legal fixture cheap-first default promotion calibration requirement label'),
  () => assertIncludes(maintenancePage, 'linked_calibration_task_ids', 'legal fixture cheap-first default promotion calibration task binding'),
  () => assertIncludes(maintenancePage, 'modelOpsLegalFixtureEvidenceHandoff', 'legal fixture evidence handoff state binding'),
  () => assertIncludes(maintenancePage, 'Legal fixture evidence handoff', 'legal fixture evidence handoff panel'),
  () => assertIncludes(maintenancePage, 'legalFixtureEvidenceHandoffRows', 'legal fixture evidence handoff rows fallback'),
  () => assertIncludes(maintenancePage, 'legalFixtureEvidenceHandoffChecks', 'legal fixture evidence handoff checks fallback'),
  () => assertIncludes(maintenancePage, 'legalFixtureEvidenceHandoffBoundaryRows', 'legal fixture evidence handoff boundary rows'),
  () => assertIncludes(maintenancePage, 'returns_run_report_payload', 'legal fixture evidence handoff run report boundary binding'),
  () => assertIncludes(maintenancePage, 'returns_credentials', 'legal fixture evidence handoff credential boundary binding'),
  () => assertIncludes(maintenancePage, 'completion_claimed', 'legal fixture evidence handoff completion claim binding'),
  () => assertIncludes(maintenancePage, 'modelOpsCheapFirstReleaseDecision', 'maintenance cheap-first release decision state binding'),
  () => assertIncludes(maintenancePage, 'Cheap-first release decision', 'maintenance cheap-first release decision panel'),
  () => assertIncludes(maintenancePage, 'cheapFirstReleaseDecisionLegalChecks', 'maintenance cheap-first release legal checks binding'),
  () => assertIncludes(maintenancePage, 'cheapFirstReleaseDecisionAttentionChecks', 'maintenance cheap-first release attention checks binding'),
  () => assertIncludes(maintenancePage, 'legal_fixture_cheap_first_benchmark_gate', 'maintenance cheap-first release legal fixture source binding'),
  () => assertIncludes(maintenancePage, 'legal_fixture_cheap_first_default_promotion_packet', 'maintenance cheap-first release promotion packet source binding'),
  () => assertIncludes(maintenancePage, 'legal_benchmark_risk_bridge', 'maintenance cheap-first release risk bridge source binding'),
  () => assertIncludes(maintenancePage, 'source_warning_id_count', 'maintenance cheap-first release source warning count binding'),
  () => assertIncludes(maintenancePage, 'source_blocking_id_count', 'maintenance cheap-first release source blocker count binding'),
  () => assertIncludes(maintenancePage, 'legal_fixture_policy', 'maintenance cheap-first release legal fixture policy binding'),
  () => assertIncludes(maintenancePage, 'legal_benchmark_policy', 'maintenance cheap-first release legal benchmark policy binding'),
  () => assertBefore(maintenancePage, 'Maintainer-only packet for cheap-first legal fixture default review', '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>', 'maintenance legal fixture evidence handoff follows legal promotion packet'),
  () => assertBefore(maintenancePage, '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>', '<h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>', 'maintenance cheap-first release follows legal fixture evidence handoff'),
  () => assertBefore(maintenancePage, '<h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>', '                      Model route legal benchmark risk queue', 'maintenance cheap-first release precedes legal route risk queue'),
  () => assertIncludes(maintenanceApi, 'LegalRagAuthorityCitationGate', 'legal RAG authority citation gate type'),
  () => assertIncludes(maintenanceApi, 'legalRagAuthorityCitationGate', 'legal RAG authority citation gate payload binding'),
  () => assertIncludes(maintenanceApi, 'source_tier', 'legal RAG source tier type'),
  () => assertIncludes(maintenanceApi, 'citation_mismatch_count', 'legal RAG citation mismatch type'),
  () => assertIncludes(maintenanceApi, 'retrieval_gap_count', 'legal RAG retrieval gap type'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-authority-citation-gate', 'legal RAG authority citation gate endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagHallucinationTriageGate', 'legal RAG hallucination triage gate type'),
  () => assertIncludes(maintenanceApi, 'legalRagHallucinationTriageGate', 'legal RAG hallucination triage payload binding'),
  () => assertIncludes(maintenanceApi, 'triage_rows', 'legal RAG hallucination triage rows type'),
  () => assertIncludes(maintenanceApi, 'failure_label_counts', 'legal RAG hallucination failure taxonomy counts type'),
  () => assertIncludes(maintenanceApi, 'severity_counts', 'legal RAG hallucination severity counts type'),
  () => assertIncludes(maintenanceApi, 'returns_retrieved_context', 'legal RAG hallucination retrieved context boundary type'),
  () => assertIncludes(maintenanceApi, 'returns_model_outputs', 'legal RAG hallucination model output boundary type'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-hallucination-triage-gate', 'legal RAG hallucination triage endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagAbstentionEscalationGate', 'legal RAG abstention escalation gate type'),
  () => assertIncludes(maintenanceApi, 'legalRagAbstentionEscalationGate', 'legal RAG abstention escalation camelCase payload binding'),
  () => assertIncludes(maintenanceApi, 'legal_rag_abstention_escalation_gate', 'legal RAG abstention escalation snake_case payload binding'),
  () => assertIncludes(maintenanceApi, 'decision_rows', 'legal RAG abstention decision rows type'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-abstention-escalation-gate', 'legal RAG abstention escalation endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagRetrievalDiagnosticsGate', 'legal RAG retrieval diagnostics gate type'),
  () => assertIncludes(maintenanceApi, 'LegalRagIndexCoverageGate', 'legal RAG index coverage gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-index-coverage-gate' | string", 'legal RAG index coverage gate id'),
  () => assertIncludes(maintenanceApi, 'index_plan_rows', 'legal RAG index coverage rows type'),
  () => assertIncludes(maintenanceApi, 'index_binding_status_counts', 'legal RAG index coverage status counts type'),
  () => assertIncludes(maintenanceApi, 'locator_status_counts', 'legal RAG index coverage locator counts type'),
  () => assertIncludes(maintenanceApi, 'accepted_plan_fields', 'legal RAG index coverage input contract type'),
  () => assertIncludes(maintenanceApi, 'returns_source_ids', 'legal RAG index coverage no source id return boundary'),
  () => assertIncludes(maintenanceApi, 'getLegalRagIndexCoverageGate', 'legal RAG index coverage getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-index-coverage-gate', 'legal RAG index coverage endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingReadinessGate', 'legal RAG embedding readiness gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-embedding-readiness-gate' | string", 'legal RAG embedding readiness gate id'),
  () => assertIncludes(maintenanceApi, 'readiness_rows', 'legal RAG embedding readiness rows type'),
  () => assertIncludes(maintenanceApi, 'readiness_status_counts', 'legal RAG embedding readiness status counts type'),
  () => assertIncludes(maintenanceApi, 'embedding_default_model', 'legal RAG embedding default model type'),
  () => assertIncludes(maintenanceApi, 'returns_embedding_vectors', 'legal RAG embedding vector return boundary type'),
  () => assertIncludes(maintenanceApi, 'writes_index', 'legal RAG embedding index write boundary type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingReadinessGate', 'legal RAG embedding readiness getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-readiness-gate', 'legal RAG embedding readiness endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingChunkPolicyGate', 'legal RAG embedding chunk policy gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-embedding-chunk-policy-gate' | string", 'legal RAG embedding chunk policy gate id'),
  () => assertIncludes(maintenanceApi, 'chunk_policy_rows', 'legal RAG embedding chunk policy rows type'),
  () => assertIncludes(maintenanceApi, 'chunk_policy_status_counts', 'legal RAG embedding chunk policy status counts type'),
  () => assertIncludes(maintenanceApi, 'planned_chunk_total', 'legal RAG embedding chunk policy planned chunk type'),
  () => assertIncludes(maintenanceApi, 'returns_source_chunks', 'legal RAG embedding chunk policy source chunk boundary type'),
  () => assertIncludes(maintenanceApi, 'creates_embeddings', 'legal RAG embedding chunk policy creation boundary type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingChunkPolicyGate', 'legal RAG embedding chunk policy getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-chunk-policy-gate', 'legal RAG embedding chunk policy endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingIndexDryRunGate', 'legal RAG embedding index dry-run gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-embedding-index-dry-run-gate' | string", 'legal RAG embedding index dry-run gate id'),
  () => assertIncludes(maintenanceApi, 'dry_run_rows', 'legal RAG embedding index dry-run rows type'),
  () => assertIncludes(maintenanceApi, 'dry_run_status_counts', 'legal RAG embedding index dry-run status counts type'),
  () => assertIncludes(maintenanceApi, 'commit_action_counts', 'legal RAG embedding index dry-run commit counts type'),
  () => assertIncludes(maintenanceApi, 'planned_vector_slot_total', 'legal RAG embedding index dry-run planned vector type'),
  () => assertIncludes(maintenanceApi, 'writes_database', 'legal RAG embedding index dry-run database write boundary type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingIndexDryRunGate', 'legal RAG embedding index dry-run getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-index-dry-run-gate', 'legal RAG embedding index dry-run endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingBatchBudgetGate', 'legal RAG embedding batch budget gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-embedding-batch-budget-gate' | string", 'legal RAG embedding batch budget gate id'),
  () => assertIncludes(maintenanceApi, 'batch_budget_rows', 'legal RAG embedding batch budget rows type'),
  () => assertIncludes(maintenanceApi, 'batch_status_counts', 'legal RAG embedding batch budget status counts type'),
  () => assertIncludes(maintenanceApi, 'planned_batch_total', 'legal RAG embedding batch budget planned batch type'),
  () => assertIncludes(maintenanceApi, 'estimated_batch_cost_usd', 'legal RAG embedding batch budget cost type'),
  () => assertIncludes(maintenanceApi, 'model_call_allowed', 'legal RAG embedding batch budget no model call type'),
  () => assertIncludes(maintenanceApi, 'embedding_batch_executed_claimed', 'legal RAG embedding batch budget no execution claim type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingBatchBudgetGate', 'legal RAG embedding batch budget getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-batch-budget-gate', 'legal RAG embedding batch budget endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingBatchApprovalPacket', 'legal RAG embedding batch approval packet type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-embedding-batch-approval-packet' | string", 'legal RAG embedding batch approval packet id'),
  () => assertIncludes(maintenanceApi, 'approval_items', 'legal RAG embedding batch approval items type'),
  () => assertIncludes(maintenanceApi, 'approval_status_counts', 'legal RAG embedding batch approval status counts type'),
  () => assertIncludes(maintenanceApi, 'run_action_counts', 'legal RAG embedding batch approval action counts type'),
  () => assertIncludes(maintenanceApi, 'ready_for_approval_count', 'legal RAG embedding batch approval ready count type'),
  () => assertIncludes(maintenanceApi, 'required_signoffs', 'legal RAG embedding batch approval signoffs type'),
  () => assertIncludes(maintenanceApi, 'approval_identity_collected', 'legal RAG embedding batch approval no identity type'),
  () => assertIncludes(maintenanceApi, 'writes_approval_record', 'legal RAG embedding batch approval no approval write type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingBatchApprovalPacket', 'legal RAG embedding batch approval getter'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-embedding-batch-approval-packet', 'legal RAG embedding batch approval endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation gate type'),
  () =>
    assertIncludes(
      maintenanceApi,
      "id: 'legal-rag-embedding-batch-observation-gate' | string",
      'legal RAG embedding batch observation gate id',
    ),
  () => assertIncludes(maintenanceApi, 'observation_rows', 'legal RAG embedding batch observation rows type'),
  () => assertIncludes(maintenanceApi, 'observation_status_counts', 'legal RAG embedding batch observation status counts type'),
  () => assertIncludes(maintenanceApi, 'release_action_counts', 'legal RAG embedding batch observation release counts type'),
  () => assertIncludes(maintenanceApi, 'observed_vector_slot_total', 'legal RAG embedding batch observation observed vector type'),
  () => assertIncludes(maintenanceApi, 'source_approval_item_id_echoed', 'legal RAG embedding batch observation no approval id echo type'),
  () => assertIncludes(maintenanceApi, 'embeddings_created_by_gate', 'legal RAG embedding batch observation no creation claim type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation getter'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalRagEmbeddingBatchObservationGate', 'legal RAG embedding batch observation POST helper'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-rag-embedding-batch-observation-gate',
      'legal RAG embedding batch observation endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'LegalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review packet type'),
  () =>
    assertIncludes(
      maintenanceApi,
      "id: 'legal-rag-embedding-index-commit-review-packet' | string",
      'legal RAG embedding index commit review packet id',
    ),
  () => assertIncludes(maintenanceApi, 'commit_review_items', 'legal RAG embedding index commit review items type'),
  () => assertIncludes(maintenanceApi, 'commit_review_status_counts', 'legal RAG embedding index commit review status counts type'),
  () => assertIncludes(maintenanceApi, 'commit_review_action_counts', 'legal RAG embedding index commit review action counts type'),
  () => assertIncludes(maintenanceApi, 'index_commit_allowed_by_packet', 'legal RAG embedding index commit review no packet commit type'),
  () => assertIncludes(maintenanceApi, 'ready_for_commit_review_count', 'legal RAG embedding index commit review ready count type'),
  () => assertIncludes(maintenanceApi, 'hold_for_commit_review_count', 'legal RAG embedding index commit review hold count type'),
  () => assertIncludes(maintenanceApi, 'blocked_commit_review_count', 'legal RAG embedding index commit review blocked count type'),
  () => assertIncludes(maintenanceApi, 'required_signoffs', 'legal RAG embedding index commit review signoffs type'),
  () => assertIncludes(maintenanceApi, 'pre_commit_checks', 'legal RAG embedding index commit review pre-commit checks type'),
  () => assertIncludes(maintenanceApi, 'commit_record_written', 'legal RAG embedding index commit review no commit record type'),
  () => assertIncludes(maintenanceApi, 'approval_item_id_echoed', 'legal RAG embedding index commit review no approval item echo type'),
  () => assertIncludes(maintenanceApi, 'returns_approval_item_ids', 'legal RAG embedding index commit review no approval item ids return type'),
  () => assertIncludes(maintenanceApi, 'writes_commit_record', 'legal RAG embedding index commit review no write commit record type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'embedding_batch_executed_claimed_by_packet',
      'legal RAG embedding index commit review no execution claim type',
    ),
  () => assertIncludes(maintenanceApi, 'committer_identity_collected', 'legal RAG embedding index commit review no committer identity type'),
  () => assertIncludes(maintenanceApi, 'returns_committer_identity', 'legal RAG embedding index commit review no committer identity return type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review getter'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalRagEmbeddingIndexCommitReviewPacket', 'legal RAG embedding index commit review POST helper'),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-rag-embedding-index-commit-review-packet',
      'legal RAG embedding index commit review endpoint',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'LegalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification gate type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'LegalRagEmbeddingIndexPostCommitVerificationGateRow',
      'legal RAG embedding index post-commit verification row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      "id: 'legal-rag-embedding-index-post-commit-verification-gate' | string",
      'legal RAG embedding index post-commit verification gate id',
    ),
  () => assertIncludes(maintenanceApi, 'verification_rows', 'legal RAG embedding index post-commit verification rows type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'verification_status_counts',
      'legal RAG embedding index post-commit verification status counts type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'verification_action_counts',
      'legal RAG embedding index post-commit verification action counts type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'verified_for_retrieval_diagnostics_count',
      'legal RAG embedding index post-commit verification verified count type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'verification_review_required_count',
      'legal RAG embedding index post-commit verification review count type',
    ),
  () => assertIncludes(maintenanceApi, 'verification_blocked_count', 'legal RAG embedding index post-commit blocked count type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'post_commit_verification_policy',
      'legal RAG embedding index post-commit verification policy type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'accepted_verification_fields',
      'legal RAG embedding index post-commit verification input fields type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'post_commit_observation_only',
      'legal RAG embedding index post-commit verification observation-only type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'returns_committer_identity',
      'legal RAG embedding index post-commit no committer identity return type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getLegalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'evaluateLegalRagEmbeddingIndexPostCommitVerificationGate',
      'legal RAG embedding index post-commit verification POST helper',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate',
      'legal RAG embedding index post-commit verification endpoint',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'LegalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff gate type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'LegalRagEmbeddingRetrievalDiagnosticsHandoffGateRow',
      'legal RAG embedding retrieval diagnostics handoff row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      "id: 'legal-rag-embedding-retrieval-diagnostics-handoff-gate' | string",
      'legal RAG embedding retrieval diagnostics handoff gate id',
    ),
  () => assertIncludes(maintenanceApi, 'handoff_rows', 'legal RAG embedding retrieval diagnostics handoff rows type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'handoff_status_counts',
      'legal RAG embedding retrieval diagnostics handoff status counts type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'handoff_action_counts',
      'legal RAG embedding retrieval diagnostics handoff action counts type',
    ),
  () => assertIncludes(maintenanceApi, 'ready_handoff_count', 'legal RAG embedding retrieval diagnostics handoff ready count type'),
  () => assertIncludes(maintenanceApi, 'hold_handoff_count', 'legal RAG embedding retrieval diagnostics handoff hold count type'),
  () => assertIncludes(maintenanceApi, 'blocked_handoff_count', 'legal RAG embedding retrieval diagnostics handoff blocked count type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'diagnostics_review_ready_count',
      'legal RAG embedding retrieval diagnostics handoff diagnostics-ready count type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'safe_handoff_payload_fields',
      'legal RAG embedding retrieval diagnostics handoff safe payload fields type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'handoff_policy',
      'legal RAG embedding retrieval diagnostics handoff policy type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'allows_retrieval_diagnostics_review_only',
      'legal RAG embedding retrieval diagnostics handoff diagnostics-only policy type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'allows_production_retrieval',
      'legal RAG embedding retrieval diagnostics handoff production retrieval policy type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getLegalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff getter',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'evaluateLegalRagEmbeddingRetrievalDiagnosticsHandoffGate',
      'legal RAG embedding retrieval diagnostics handoff POST helper',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate',
      'legal RAG embedding retrieval diagnostics handoff endpoint',
    ),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-retrieval-diagnostics-gate' | string", 'legal RAG retrieval diagnostics gate id'),
  () => assertIncludes(maintenanceApi, 'diagnostic_rows', 'legal RAG retrieval diagnostics rows type'),
  () => assertIncludes(maintenanceApi, 'query_intent', 'legal RAG retrieval diagnostics query intent type'),
  () => assertIncludes(maintenanceApi, 'source_coverage_status', 'legal RAG retrieval diagnostics source coverage type'),
  () => assertIncludes(maintenanceApi, 'top_k_depth_status', 'legal RAG retrieval diagnostics top-k depth type'),
  () => assertIncludes(maintenanceApi, 'cheap_first_retry_count', 'legal RAG retrieval diagnostics cheap-first retry type'),
  () => assertIncludes(maintenanceApi, 'legal_rag_index_binding_status', 'legal RAG retrieval diagnostics index linkage type'),
  () => assertIncludes(maintenanceApi, 'legal_rag_authority_citation_gate_status', 'legal RAG retrieval diagnostics authority linkage type'),
  () => assertIncludes(maintenanceApi, 'legal_rag_abstention_escalation_gate_status', 'legal RAG retrieval diagnostics abstention linkage type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagRetrievalDiagnosticsGate', 'legal RAG retrieval diagnostics API binding'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-retrieval-diagnostics-gate', 'legal RAG retrieval diagnostics endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagRetrievalObservationGate', 'legal RAG retrieval observation gate type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-retrieval-observation-gate' | string", 'legal RAG retrieval observation gate id'),
  () => assertIncludes(maintenanceApi, 'observation_rows', 'legal RAG retrieval observation rows type'),
  () => assertIncludes(maintenanceApi, 'source_validation_counts', 'legal RAG retrieval observation source validation type'),
  () => assertIncludes(maintenanceApi, 'retrieval_status_counts', 'legal RAG retrieval observation status counts type'),
  () => assertIncludes(maintenanceApi, 'release_action_counts', 'legal RAG retrieval observation release counts type'),
  () => assertIncludes(maintenanceApi, 'accepted_container_keys', 'legal RAG retrieval observation input contract type'),
  () => assertIncludes(maintenanceApi, 'returns_source_ids', 'legal RAG retrieval observation no source id return boundary'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalRagRetrievalObservationGate', 'legal RAG retrieval observation POST helper'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-retrieval-observation-gate', 'legal RAG retrieval observation endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness gate type'),
  () => assertIncludes(maintenanceApi, 'LegalRagAnswerReleaseReadinessGateRow', 'legal RAG answer release readiness row type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-answer-release-readiness-gate' | string", 'legal RAG answer release readiness gate id'),
  () => assertIncludes(maintenanceApi, 'answer_release_rows', 'legal RAG answer release readiness rows type'),
  () => assertIncludes(maintenanceApi, 'answer_release_status_counts', 'legal RAG answer release readiness status counts type'),
  () => assertIncludes(maintenanceApi, 'answer_release_action_counts', 'legal RAG answer release readiness action counts type'),
  () => assertIncludes(maintenanceApi, 'ready_answer_count', 'legal RAG answer release readiness ready count type'),
  () => assertIncludes(maintenanceApi, 'review_required_count', 'legal RAG answer release readiness review count type'),
  () => assertIncludes(maintenanceApi, 'blocked_answer_count', 'legal RAG answer release readiness blocked count type'),
  () => assertIncludes(maintenanceApi, 'internal_draft_allowed_count', 'legal RAG answer release readiness draft count type'),
  () => assertIncludes(maintenanceApi, 'citation_packet_required_count', 'legal RAG answer release readiness citation count type'),
  () => assertIncludes(maintenanceApi, 'lawyer_review_required_count', 'legal RAG answer release readiness lawyer count type'),
  () => assertIncludes(maintenanceApi, 'client_delivery_allowed_count', 'legal RAG answer release readiness client delivery count type'),
  () => assertIncludes(maintenanceApi, 'answer_release_policy', 'legal RAG answer release readiness policy type'),
  () => assertIncludes(maintenanceApi, 'allows_client_delivery', 'legal RAG answer release readiness no client delivery type'),
  () => assertIncludes(maintenanceApi, 'allows_legal_advice_claim', 'legal RAG answer release readiness no legal advice type'),
  () => assertIncludes(maintenanceApi, 'writes_answer', 'legal RAG answer release readiness no answer write type'),
  () => assertIncludes(maintenanceApi, 'sends_client_delivery', 'legal RAG answer release readiness no client delivery send type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness getter'),
  () => assertIncludes(maintenanceApi, 'evaluateLegalRagAnswerReleaseReadinessGate', 'legal RAG answer release readiness POST helper'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-answer-release-readiness-gate', 'legal RAG answer release readiness endpoint'),
  () => assertIncludes(maintenanceApi, 'LegalRagBenchmarkAlignment', 'legal RAG benchmark alignment type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-benchmark-alignment' | string", 'legal RAG benchmark alignment id'),
  () => assertIncludes(maintenanceApi, 'alignment_rows', 'legal RAG benchmark alignment rows type'),
  () => assertIncludes(maintenanceApi, 'benchmark_signal_ids', 'legal RAG benchmark alignment benchmark signals type'),
  () => assertIncludes(maintenanceApi, 'raw_public_benchmark_text_included', 'legal RAG benchmark alignment raw benchmark boundary type'),
  () => assertIncludes(maintenanceApi, 'getLegalRagBenchmarkAlignment', 'legal RAG benchmark alignment API'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag-benchmark-alignment', 'legal RAG benchmark alignment endpoint'),
  () => assertIncludes(maintenanceApi, 'MaintenanceLegalRagExportReadinessPacket', 'legal RAG export readiness packet type'),
  () => assertIncludes(maintenanceApi, "id: 'legal-rag-export-readiness-packet' | string", 'legal RAG export readiness packet id'),
  () => assertIncludes(maintenanceApi, 'selected_source_binding', 'legal RAG export readiness selected-source binding type'),
  () => assertIncludes(maintenanceApi, 'raw_report_returned', 'legal RAG export readiness raw report boundary type'),
  () => assertIncludes(maintenanceApi, 'getMaintenanceLegalRagExportReadinessPacket', 'legal RAG export readiness packet API'),
  () => assertIncludes(maintenanceApi, '/api/v1/maintenance/legal-rag/export-readiness-packet', 'legal RAG export readiness packet endpoint'),
  () =>
    assertIncludes(
      maintenanceApi,
      'MaintenanceFinalDocumentDeliveryReleaseGate',
      'final document delivery release gate type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getMaintenanceFinalDocumentDeliveryReleaseGate',
      'final document delivery release gate API',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/final-document-delivery-release-gate',
      'final document delivery release gate endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'component_gates', 'final document delivery component gate type'),
  () => assertIncludes(maintenanceApi, 'package_release_allowed', 'final document delivery package release type'),
  () => assertIncludes(maintenanceApi, 'final_docx_pdf_generated', 'final document delivery no generation claim type'),
  () => assertIncludes(maintenanceApi, 'live_payment_provider_settlement_verified', 'final document delivery provider claim type'),
  () =>
    assertIncludes(
      maintenanceApi,
      'SmallLegalDocumentBenchmarkRunbookEvidence',
      'small legal document benchmark runbook evidence type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'SmallLegalDocumentBenchmarkRunbookEvidenceRow',
      'small legal document benchmark runbook row type',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'getSmallLegalDocumentBenchmarkRunbookEvidence',
      'small legal document benchmark runbook API',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      'evaluateSmallLegalDocumentBenchmarkRunbookEvidence',
      'small legal document benchmark runbook evaluate API',
    ),
  () =>
    assertIncludes(
      maintenanceApi,
      '/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence',
      'small legal document benchmark runbook endpoint',
    ),
  () => assertIncludes(maintenanceApi, 'runbook_steps', 'small legal document benchmark runbook steps type'),
  () => assertIncludes(maintenanceApi, 'document_benchmark_rows', 'small legal document benchmark document rows type'),
  () => assertIncludes(maintenanceApi, 'fact_consistency_rows', 'small legal document benchmark fact rows type'),
  () => assertIncludes(maintenanceApi, 'delivery_gate_rows', 'small legal document benchmark delivery rows type'),
  () => assertIncludes(maintenanceApi, 'public_benchmark_score_claimed: boolean', 'small legal document benchmark public score type'),
  () => assertIncludes(maintenanceApi, 'production_legal_quality_claimed: boolean', 'small legal document benchmark production claim type'),
  () => assertIncludes(modelOpsPage, 'Promise.allSettled', 'model-ops partial-load resilience'),
  () => assertIncludes(modelOpsPage, 'applyModelOpsPayload', 'model-ops early aggregate payload renderer'),
  () => assertIncludes(modelOpsPage, 'const modelOpsRequest = getModelOps()', 'model-ops shared aggregate request'),
  () => assertIncludes(modelOpsPage, 'const modelOpsResult: PromiseSettledResult<ModelOpsResponse> = await modelOpsRequest', 'model-ops aggregate request before secondary evidence'),
  () => assertIncludes(modelOpsPage, 'aggregateOrRequest', 'model-ops secondary endpoint dedupe helper'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.legal_fixture_cheap_first_benchmark_gate', 'model-ops legal fixture gate aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.legal_fixture_cheap_first_default_promotion_packet', 'model-ops promotion packet aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.legal_fixture_cheap_first_regression_budget', 'model-ops regression budget aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.legal_fixture_evidence_handoff', 'model-ops legal fixture evidence handoff aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'getModelOpsLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff fallback request'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.user_need_gemini_route_coverage', 'model-ops user-need Gemini route coverage aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'getModelOpsUserNeedGeminiRouteCoverage', 'model-ops user-need Gemini route coverage fallback request'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.user_need_cheap_first_handoff', 'model-ops user-need cheap-first handoff aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'getModelOpsUserNeedCheapFirstHandoff', 'model-ops user-need cheap-first handoff fallback request'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.cheap_first_cascade_research_gate', 'model-ops cheap-first cascade research gate aggregate reuse'),
  () => assertIncludes(modelOpsPage, 'getModelOpsCheapFirstCascadeResearchGate', 'model-ops cheap-first cascade research gate fallback request'),
  () => assertIncludes(modelOpsPage, 'initialModelOpsApplied', 'model-ops early aggregate load guard'),
  () => assertIncludes(modelOpsPage, 'setLoading(false)', 'model-ops aggregate payload unblocks first paint'),
  () => assertIncludes(modelOpsPage, 'ModelOps load guard', 'model-ops performance budget panel'),
  () => assertIncludes(modelOpsPage, 'Cheap-first cascade research gate', 'model-ops cheap-first cascade research gate panel'),
  () => assertIncludes(modelOpsPage, 'cascadeResearchSourceRows', 'model-ops cheap-first cascade source row binding'),
  () => assertIncludes(modelOpsPage, 'cascadeResearchBasisRows', 'model-ops cheap-first cascade research basis binding'),
  () => assertIncludes(modelOpsPage, 'cascadeResearchPolicyEntries', 'model-ops cheap-first cascade policy binding'),
  () => assertIncludes(modelOpsPage, 'cascadeResearchBoundaryEntries', 'model-ops cheap-first cascade privacy boundary binding'),
  () => assertIncludes(modelOpsPage, 'cascadeResearchClaimEntries', 'model-ops cheap-first cascade claim boundary binding'),
  () => assertIncludes(modelOpsPage, 'default_routes_changed', 'model-ops cheap-first cascade no default change summary'),
  () => assertIncludes(modelOpsPage, 'source_rows ?? []', 'model-ops cheap-first cascade source rows fallback'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCascadeResearchGate', 'model-ops cheap-first cascade research gate type'),
  () => assertIncludes(modelOpsApi, 'cheap_first_cascade_research_gate?: ModelOpsCheapFirstCascadeResearchGate', 'model-ops cheap-first cascade research gate response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCascadeResearchGateSourceRow', 'model-ops cheap-first cascade source row type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCascadeResearchGate', 'model-ops cheap-first cascade research gate getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-cascade-research-gate', 'model-ops cheap-first cascade research gate endpoint'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">ModelOps user-need cheap-first handoff</h2>',
      '<h2 className="text-xl font-black text-stone-950">Cheap-first cascade research gate</h2>',
      'model-ops cascade research gate follows user-need handoff',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Cheap-first cascade research gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
      'model-ops cascade research gate precedes default change queue',
    ),
  () =>
    assertNotMatches(
      modelOpsCheapFirstCascadeResearchGatePanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_email|email|phone|identity|messages|content)\b/i,
      'model-ops cheap-first cascade research gate no secret or raw prompt/output fields',
    ),
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
  () => assertIncludes(modelOpsPage, 'Route telemetry repository', 'model-ops route telemetry repository panel'),
  () => assertIncludes(modelOpsPage, 'Route telemetry result archive', 'model-ops route telemetry result archive panel'),
  () => assertIncludes(modelOpsPage, 'Route telemetry ops summary', 'model-ops route telemetry ops summary panel'),
  () => assertIncludes(modelOpsPage, 'Route telemetry triage queue', 'model-ops route telemetry triage queue panel'),
  () => assertIncludes(modelOpsPage, 'Route telemetry remediation plan', 'model-ops route telemetry remediation plan panel'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryRows', 'model-ops route telemetry row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryRepositoryRows', 'model-ops route telemetry repository row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryResultArchiveRows', 'model-ops route telemetry archive row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryCostLedgerRows', 'model-ops route telemetry cost ledger row binding'),
  () => assertIncludes(modelOpsPage, 'safeMetadataText', 'model-ops route telemetry archive metadata display guard'),
  () => assertIncludes(modelOpsPage, 'formatReasonCounts(row.reason_code_counts)', 'model-ops route telemetry ops reason-code binding'),
  () => assertIncludes(modelOpsPage, 'item.reason_code ??', 'model-ops route telemetry triage reason-code binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryOpsRows', 'model-ops route telemetry ops row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryTriageRows', 'model-ops route telemetry triage row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryRemediationRows', 'model-ops route telemetry remediation row binding'),
  () => assertIncludes(modelOpsPage, 'routeTelemetryRemediationEnvRows', 'model-ops route telemetry remediation env row binding'),
  () => assertIncludes(modelOpsPage, 'raw payload storage', 'model-ops route telemetry raw-payload storage boundary copy'),
  () => assertIncludes(modelOpsPage, 'Reasons', 'model-ops route telemetry reason-code column'),
  () => assertIncludes(modelOpsPage, 'formatReasonCounts', 'model-ops route telemetry reason-code formatter'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops route telemetry remediation no config-write binding'),
  () => assertIncludes(modelOpsPage, 'newapi_called', 'model-ops route telemetry remediation no NewAPI-call binding'),
  () => assertIncludes(modelOpsPage, 'recommended_env_assignment', 'model-ops route telemetry remediation env suggestion binding'),
  () => assertBefore(modelOpsPage, 'Route telemetry', 'Route telemetry repository', 'model-ops route telemetry before repository'),
  () => assertBefore(modelOpsPage, 'Route telemetry repository', 'Route telemetry result archive', 'model-ops route telemetry repository before result archive'),
  () => assertBefore(modelOpsPage, 'Route telemetry result archive', 'Route telemetry ops summary', 'model-ops route telemetry result archive before ops summary'),
  () => assertBefore(modelOpsPage, 'Route telemetry repository', 'Route telemetry ops summary', 'model-ops route telemetry repository before ops summary'),
  () => assertBefore(modelOpsPage, 'Route telemetry ops summary', 'Route telemetry triage queue', 'model-ops route telemetry ops summary before triage queue'),
  () => assertBefore(modelOpsPage, 'Route telemetry triage queue', 'Route telemetry remediation plan', 'model-ops route telemetry triage queue before remediation plan'),
  () => assertBefore(modelOpsPage, 'Route telemetry remediation plan', 'Route guardrails', 'model-ops route telemetry remediation before route guardrails'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryRepository', 'model-ops route telemetry repository type'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryResultArchive', 'model-ops route telemetry result archive type'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryOpsSummary', 'model-ops route telemetry ops summary type'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryTriage', 'model-ops route telemetry triage type'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryRemediation', 'model-ops route telemetry remediation type'),
  () => assertIncludes(modelOpsApi, 'ModelRouteTelemetryRecommendedEnv', 'model-ops route telemetry remediation env type'),
  () => assertIncludes(modelOpsApi, 'route_telemetry_repository?: ModelRouteTelemetryRepository', 'model-ops route telemetry repository response binding'),
  () => assertIncludes(modelOpsApi, 'route_telemetry_result_archive?: ModelRouteTelemetryResultArchive', 'model-ops route telemetry result archive response binding'),
  () => assertIncludes(modelOpsApi, 'model_ops_route_telemetry_archive?: ModelRouteTelemetryResultArchive', 'model-ops route telemetry archive aggregate alias'),
  () => assertIncludes(modelOpsApi, 'route_telemetry_ops_summary?: ModelRouteTelemetryOpsSummary', 'model-ops route telemetry ops response binding'),
  () => assertIncludes(modelOpsApi, 'route_telemetry_triage?: ModelRouteTelemetryTriage', 'model-ops route telemetry triage response binding'),
  () => assertIncludes(modelOpsApi, 'route_telemetry_remediation?: ModelRouteTelemetryRemediation', 'model-ops route telemetry remediation response binding'),
  () => assertIncludes(modelOpsApi, 'getModelRouteTelemetryResultArchive', 'model-ops route telemetry result archive API helper'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/route-telemetry-result-archive', 'model-ops route telemetry result archive endpoint'),
  () => assertIncludes(modelOpsApi, 'archive_rows?: ModelRouteTelemetryResultArchiveRow[]', 'model-ops route telemetry archive row type'),
  () => assertIncludes(modelOpsApi, 'cost_ledger_rows?: ModelRouteTelemetryCostLedgerRow[]', 'model-ops route telemetry cost ledger row type'),
  () => assertIncludes(modelOpsApi, 'release_review_rows?: ModelRouteTelemetryReleaseReviewRow[]', 'model-ops route telemetry release review row type'),
  () => assertIncludes(modelOpsApi, 'raw_payload_storage_allowed: boolean', 'model-ops route telemetry raw-payload storage boundary type'),
  () => assertIncludes(modelOpsApi, 'reason_code_counts: Record<string, number>', 'model-ops route telemetry reason-code counts type'),
  () => assertIncludes(modelOpsApi, 'top_reason_codes: Array<{ reason_code: string; count: number; ratio: number }>', 'model-ops route telemetry top reason-code type'),
  () => assertIncludes(modelOpsApi, 'reason_code_hotspots: Array<', 'model-ops route telemetry reason-code hotspot type'),
  () => assertIncludes(modelOpsApi, 'configuration_written: boolean', 'model-ops route telemetry remediation no config-write type'),
  () => assertIncludes(modelOpsApi, 'newapi_called: boolean', 'model-ops route telemetry remediation no NewAPI-call type'),
  () => assertIncludes(modelOpsPage, 'cheap-first', 'model-ops cheap-first copy'),
  () => assertIncludes(modelOpsPage, 'Gemini variant matrix', 'model-ops Gemini variant matrix panel'),
  () => assertIncludes(modelOpsPage, 'Observed Gemini model intake queue', 'model-ops observed Gemini intake queue panel'),
  () => assertIncludes(modelOpsPage, 'activeObservedGeminiModelIntakeQueue', 'model-ops observed Gemini intake active binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiModelIntakeRows', 'model-ops observed Gemini intake row binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiPromotionSafetyChecks', 'model-ops observed Gemini intake safety checks binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiIntakeRunbookSteps', 'model-ops observed Gemini intake runbook binding'),
  () => assertIncludes(modelOpsPage, 'defaultObservedGeminiModelIntakePayload', 'model-ops observed Gemini intake template payload'),
  () => assertIncludes(modelOpsPage, 'yibu/gemini-3.1-flash-image', 'model-ops observed Gemini image route intake example'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenObservedGeminiModelIntakePayloadText', 'model-ops observed Gemini intake payload guard'),
  () => assertIncludes(modelOpsPage, 'Evaluate intake queue', 'model-ops observed Gemini intake submit button'),
  () => assertIncludes(modelOpsPage, 'cheap_first_default_candidate', 'model-ops observed Gemini intake cheap-first candidate binding'),
  () => assertIncludes(modelOpsPage, 'Promotion safety checks', 'model-ops observed Gemini intake safety checks panel'),
  () => assertIncludes(modelOpsPage, 'Intake runbook', 'model-ops observed Gemini intake runbook panel'),
  () => assertIncludes(modelOpsPage, 'promotion_safety_blocking_count', 'model-ops observed Gemini intake safety blocker summary'),
  () => assertIncludes(modelOpsPage, 'intake_runbook_step_count', 'model-ops observed Gemini intake runbook summary'),
  () => assertIncludes(modelOpsPage, 'safe_to_enter_default_change_queue', 'model-ops observed Gemini intake default queue safety summary'),
  () => assertIncludes(modelOpsPage, 'automatic_default_change_claimed', 'model-ops observed Gemini intake no automatic default change claim'),
  () => assertIncludes(modelOpsPage, 'raw payload echoed', 'model-ops observed Gemini intake raw payload boundary'),
  () => assertIncludes(modelOpsPage, 'Observed Gemini coverage gap queue', 'model-ops observed Gemini coverage gap queue panel'),
  () => assertIncludes(modelOpsPage, 'activeObservedGeminiCoverageGapQueue', 'model-ops observed Gemini coverage gap active binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiCoverageGapFamilyRows', 'model-ops observed Gemini coverage gap family row binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiCoverageGapTaskRows', 'model-ops observed Gemini coverage gap task row binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiCoverageGapItems', 'model-ops observed Gemini coverage gap item binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiCoverageGapPrivacyEntries', 'model-ops observed Gemini coverage gap privacy binding'),
  () => assertIncludes(modelOpsPage, 'observedGeminiCoverageGapClaimEntries', 'model-ops observed Gemini coverage gap claim binding'),
  () => assertIncludes(modelOpsPage, 'family_gap_count', 'model-ops observed Gemini coverage gap family summary'),
  () => assertIncludes(modelOpsPage, 'cheap_first_task_gap_count', 'model-ops observed Gemini coverage gap task summary'),
  () => assertIncludes(modelOpsPage, 'ready_cheap_first_candidate_count', 'model-ops observed Gemini coverage gap ready summary'),
  () => assertIncludes(modelOpsPage, 'raw_payload_echoed', 'model-ops observed Gemini coverage gap raw payload boundary'),
  () => assertIncludes(observedGeminiCoverageGapQueuePanel, 'Privacy boundary', 'model-ops observed Gemini coverage gap privacy panel'),
  () => assertIncludes(observedGeminiCoverageGapQueuePanel, 'Claim boundary', 'model-ops observed Gemini coverage gap claim panel'),
  () => assertIncludes(observedGeminiCoverageGapQueuePanel, 'Validation commands', 'model-ops observed Gemini coverage gap validation panel'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiCoverageGapQueue', 'model-ops observed Gemini coverage gap queue type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiCoverageGapFamilyRow', 'model-ops observed Gemini coverage gap family row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiCoverageGapTaskRow', 'model-ops observed Gemini coverage gap task row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiCoverageGapItem', 'model-ops observed Gemini coverage gap item type'),
  () => assertIncludes(modelOpsApi, 'observed_gemini_coverage_gap_queue?: ModelOpsObservedGeminiCoverageGapQueue', 'model-ops observed Gemini coverage gap response binding'),
  () => assertIncludes(modelOpsApi, 'high_frequency_task_rows?: unknown', 'model-ops observed Gemini coverage gap payload guard task rows'),
  () => assertIncludes(modelOpsApi, 'gap_items?: unknown', 'model-ops observed Gemini coverage gap payload guard gap items'),
  () => assertIncludes(modelOpsApi, 'getModelOpsObservedGeminiCoverageGapQueue', 'model-ops observed Gemini coverage gap getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/observed-gemini-coverage-gap-queue', 'model-ops observed Gemini coverage gap endpoint'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini variant matrix</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      'model-ops observed Gemini coverage gap queue follows variant matrix',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Observed Gemini coverage gap queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Model default candidate selector</h2>',
      'model-ops model default candidate selector follows observed Gemini coverage gaps',
    ),
  () => assertIncludes(modelOpsApi, 'ModelDefaultCandidateSelector', 'model-ops model default candidate selector type'),
  () => assertIncludes(modelOpsApi, 'ModelDefaultCandidateSelectorRecommendation', 'model-ops model default candidate selector recommendation type'),
  () => assertIncludes(modelOpsApi, 'ModelDefaultCandidateSelectorCandidate', 'model-ops model default candidate selector candidate type'),
  () => assertIncludes(modelOpsApi, 'default_candidate_selector?: ModelDefaultCandidateSelector', 'model-ops model default candidate selector response binding'),
  () => assertIncludes(modelOpsApi, 'recommendations?: unknown', 'model-ops model default candidate selector payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelDefaultCandidateSelector', 'model-ops model default candidate selector getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelDefaultCandidateSelector', 'model-ops model default candidate selector evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/model-default-candidate-selector', 'model-ops model default candidate selector endpoint'),
  () => assertIncludes(modelOpsPage, 'Model default candidate selector', 'model-ops model default candidate selector panel'),
  () => assertIncludes(modelOpsPage, 'defaultCandidateSelectorRows', 'model-ops model default candidate selector row binding'),
  () => assertIncludes(modelOpsPage, 'defaultCandidateTopRows', 'model-ops model default candidate selector candidate binding'),
  () => assertIncludes(modelOpsPage, 'defaultModelDefaultCandidateSelectorPayload', 'model-ops model default candidate selector default payload'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenModelDefaultCandidatePayloadText', 'model-ops model default candidate selector payload guard'),
  () => assertIncludes(modelOpsPage, 'raw_payload_echoed', 'model-ops model default candidate selector raw payload boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops model default candidate selector gateway boundary'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops model default candidate selector write boundary'),
  () => assertIncludes(modelDefaultCandidateSelectorPanel, 'Evaluate task subset', 'model-ops model default candidate selector evaluation panel'),
  () => assertIncludes(modelDefaultCandidateSelectorPanel, 'Privacy boundary', 'model-ops model default candidate selector privacy panel'),
  () => assertIncludes(modelDefaultCandidateSelectorPanel, 'Validation commands', 'model-ops model default candidate selector validation panel'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Model default candidate selector</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
      'model-ops model default candidate selector precedes alias coverage',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Model default candidate selector</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
      'model-ops model default candidate selector precedes Gemini/NewAPI selector',
    ),
  () =>
    assertNotMatches(
      modelDefaultCandidateSelectorPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_email|email|phone|identity|messages|content)\b/i,
      'model-ops model default candidate selector no secret or raw request/output fields',
    ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiNewApiModelSelector', 'model-ops Gemini/NewAPI model selector exported type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiNewApiSelectorReplay', 'model-ops Gemini/NewAPI selector replay exported type'),
  () => assertIncludes(modelOpsApi, 'gemini_newapi_model_selector?: GeminiNewApiModelSelectorEvidence', 'model-ops Gemini/NewAPI model selector response binding'),
  () => assertIncludes(modelOpsApi, 'gemini_newapi_selector_replay?: GeminiNewApiSelectorReplayEvidence', 'model-ops Gemini/NewAPI selector replay response binding'),
  () => assertIncludes(maintenanceApi, 'balanced_route_count?: number', 'Gemini/NewAPI selector replay balanced summary type'),
  () => assertIncludes(maintenanceApi, 'premium_exception?: boolean', 'Gemini/NewAPI selector replay premium exception type'),
  () => assertIncludes(maintenanceApi, 'selector_status?: string | null', 'Gemini/NewAPI selector replay selector status type'),
  () => assertIncludes(maintenanceApi, 'method?:', 'Gemini/NewAPI selector replay method metadata type'),
  () => assertIncludes(modelOpsApi, 'task_recommendations?: unknown', 'model-ops Gemini/NewAPI model selector payload guard task recommendations'),
  () => assertIncludes(modelOpsApi, 'observed_model_reviews?: unknown', 'model-ops Gemini/NewAPI model selector payload guard observed reviews'),
  () => assertIncludes(modelOpsApi, 'replay_results?: unknown', 'model-ops Gemini/NewAPI selector replay payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiNewApiModelSelector', 'model-ops Gemini/NewAPI model selector getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsGeminiNewApiModelSelector', 'model-ops Gemini/NewAPI model selector evaluator'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiNewApiSelectorReplay', 'model-ops Gemini/NewAPI selector replay getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsGeminiNewApiSelectorReplay', 'model-ops Gemini/NewAPI selector replay evaluator'),
  () => assertIncludes(modelOpsApi, "method: 'POST'", 'model-ops Gemini/NewAPI selector replay POST binding available'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-newapi-model-selector', 'model-ops Gemini/NewAPI model selector endpoint'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-newapi-selector-replay', 'model-ops Gemini/NewAPI selector replay endpoint'),
  () => assertIncludes(modelOpsPage, 'Gemini/NewAPI model selector', 'model-ops Gemini/NewAPI model selector panel'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiModelSelectorRows', 'model-ops Gemini/NewAPI model selector row binding'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiObservedModelRows', 'model-ops Gemini/NewAPI observed model row binding'),
  () => assertIncludes(modelOpsPage, 'Gemini/NewAPI selector replay', 'model-ops Gemini/NewAPI selector replay panel'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiSelectorReplayRows', 'model-ops Gemini/NewAPI selector replay row binding'),
  () => assertIncludes(modelOpsPage, 'defaultGeminiNewApiSelectorReplayPayload', 'model-ops Gemini/NewAPI selector replay template payload'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiSelectorReplayPayloadText', 'model-ops Gemini/NewAPI selector replay textarea state'),
  () => assertIncludes(modelOpsPage, 'setGeminiNewApiSelectorReplayPayloadText', 'model-ops Gemini/NewAPI selector replay text setter'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiSelectorReplayLoading', 'model-ops Gemini/NewAPI selector replay loading state'),
  () => assertIncludes(modelOpsPage, 'loadGeminiNewApiSelectorReplayTemplate', 'model-ops Gemini/NewAPI selector replay template handler'),
  () => assertIncludes(modelOpsPage, 'evaluateGeminiNewApiSelectorReplayPayload', 'model-ops Gemini/NewAPI selector replay POST handler'),
  () => assertIncludes(modelOpsPage, 'evaluateModelOpsGeminiNewApiSelectorReplay', 'model-ops Gemini/NewAPI selector replay evaluator import use'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenGeminiNewApiSelectorReplayPayloadText', 'model-ops Gemini/NewAPI selector replay sensitive input guard'),
  () =>
    assertIncludes(
      modelOpsPage,
      'setGeminiNewApiSelectorReplay(',
      'model-ops Gemini/NewAPI selector replay POST result replaces panel state',
    ),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'Scenario replay workbench', 'model-ops Gemini/NewAPI selector replay workbench heading'),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, '<Textarea', 'model-ops Gemini/NewAPI selector replay textarea control'),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'Template', 'model-ops Gemini/NewAPI selector replay template button'),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'Reset', 'model-ops Gemini/NewAPI selector replay reset button'),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'Evaluate replay', 'model-ops Gemini/NewAPI selector replay evaluate button'),
  () =>
    assertIncludes(
      geminiNewApiSelectorReplayPanel,
      'disabled={geminiNewApiSelectorReplayLoading}',
      'model-ops Gemini/NewAPI selector replay loading-gated evaluate button',
    ),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'metadata-only scenarios', 'model-ops Gemini/NewAPI selector replay metadata boundary'),
  () => assertIncludes(geminiNewApiSelectorReplayPanel, 'no gateway call', 'model-ops Gemini/NewAPI selector replay no gateway call boundary'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI model selector</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
      'model-ops Gemini/NewAPI model selector precedes alias coverage',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI selector replay</h2>',
      'model-ops Gemini/NewAPI alias coverage precedes selector replay',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI selector replay</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
      'model-ops Gemini/NewAPI selector replay precedes cheap-first coverage gate',
    ),
  () =>
    assertNotMatches(
      geminiNewApiModelSelectorPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_email|email|phone|identity|messages|content)\b/i,
      'model-ops Gemini/NewAPI model selector no secret or raw prompt/output fields',
    ),
  () =>
    assertNotMatches(
      geminiNewApiSelectorReplayPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_email|email|phone|identity|messages|content)\b/i,
      'model-ops Gemini/NewAPI selector replay no secret or raw prompt/output fields',
    ),
  () => assertIncludes(modelOpsPage, 'Gemini cheap-first coverage gate', 'model-ops Gemini cheap-first coverage gate panel'),
  () => assertIncludes(modelOpsPage, 'getGeminiCheapFirstCoverageGate', 'model-ops Gemini cheap-first coverage gate API binding'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstCoverageGate', 'model-ops Gemini cheap-first coverage gate state binding'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstCoverageRows', 'model-ops Gemini cheap-first coverage row binding'),
  () => assertIncludes(modelOpsPage, 'modelops-gemini-cheap-first-coverage-gate', 'model-ops Gemini cheap-first coverage gate id'),
  () => assertIncludes(modelOpsPage, 'coverage_row_count', 'model-ops Gemini cheap-first coverage row count summary'),
  () => assertIncludes(modelOpsPage, 'ready_row_count', 'model-ops Gemini cheap-first ready row summary'),
  () => assertIncludes(modelOpsPage, 'review_row_count', 'model-ops Gemini cheap-first review row summary'),
  () => assertIncludes(modelOpsPage, 'blocked_row_count', 'model-ops Gemini cheap-first blocked row summary'),
  () => assertIncludes(modelOpsPage, 'cheap_first_ready_count', 'model-ops Gemini cheap-first ready count summary'),
  () => assertIncludes(modelOpsPage, 'premium_exception_count', 'model-ops Gemini cheap-first premium exception summary'),
  () => assertIncludes(modelOpsPage, 'unknown_model_count', 'model-ops Gemini cheap-first unknown model summary'),
  () => assertIncludes(modelOpsPage, 'non_gemini_default_count', 'model-ops Gemini cheap-first non-Gemini summary'),
  () => assertIncludes(modelOpsPage, 'missing_price_count', 'model-ops Gemini cheap-first missing price summary'),
  () => assertIncludes(modelOpsPage, 'missing_reasoning_policy_count', 'model-ops Gemini cheap-first missing reasoning summary'),
  () => assertIncludes(modelOpsPage, 'model_called', 'model-ops Gemini cheap-first model call boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops Gemini cheap-first gateway boundary'),
  () => assertIncludes(modelOpsPage, 'network_called', 'model-ops Gemini cheap-first network boundary'),
  () => assertIncludes(modelOpsPage, 'credentials_included', 'model-ops Gemini cheap-first credential boundary'),
  () => assertIncludes(modelOpsPage, 'coverage_status', 'model-ops Gemini cheap-first coverage status binding'),
  () => assertIncludes(modelOpsPage, 'release_action', 'model-ops Gemini cheap-first release action binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_aligned', 'model-ops Gemini cheap-first alignment binding'),
  () => assertIncludes(modelOpsPage, 'premium_exception', 'model-ops Gemini cheap-first premium exception binding'),
  () => assertIncludes(modelOpsPage, 'reasoning_policy_status', 'model-ops Gemini cheap-first reasoning policy binding'),
  () => assertIncludes(modelOpsPage, 'gateway_compatibility_status', 'model-ops Gemini cheap-first gateway compatibility binding'),
  () => assertIncludes(modelOpsPage, 'linked_gate_ids', 'model-ops Gemini cheap-first linked gate binding'),
  () => assertIncludes(modelOpsPage, 'Privacy boundary', 'model-ops Gemini cheap-first privacy boundary panel'),
  () => assertIncludes(modelOpsPage, 'Claim boundary', 'model-ops Gemini cheap-first claim boundary panel'),
  () => assertIncludes(modelOpsPage, 'Metadata only; no prompt text, request bodies, secrets, or model/gateway calls are included.', 'model-ops Gemini cheap-first privacy copy'),
  () => assertIncludes(modelOpsPage, 'Validation commands', 'model-ops Gemini cheap-first validation commands panel'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiCheapFirstRoutePreflight', 'model-ops Gemini cheap-first route preflight type'),
  () => assertIncludes(modelOpsApi, 'gemini_cheap_first_route_preflight', 'model-ops Gemini cheap-first route preflight response binding'),
  () => assertIncludes(modelOpsApi, 'route_task_rows', 'model-ops Gemini cheap-first route preflight task rows payload guard'),
  () => assertIncludes(modelOpsApi, 'variant_preflight_rows', 'model-ops Gemini cheap-first route preflight variant rows payload guard'),
  () => assertIncludes(modelOpsApi, 'official_source_rows', 'model-ops Gemini cheap-first route preflight source rows payload guard'),
  () => assertIncludes(modelOpsApi, 'getGeminiCheapFirstRoutePreflight', 'model-ops Gemini cheap-first route preflight getter'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiCheapFirstRoutePreflightPayload', 'model-ops Gemini cheap-first route preflight payload type'),
  () => assertIncludes(modelOpsApi, 'evaluateGeminiCheapFirstRoutePreflight', 'model-ops Gemini cheap-first route preflight evaluator'),
  () => assertIncludes(modelOpsApi, "method: 'POST'", 'model-ops Gemini cheap-first route preflight POST binding'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-cheap-first-route-preflight', 'model-ops Gemini cheap-first route preflight endpoint'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiResearchRefreshGate', 'model-ops Gemini research refresh gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiResearchRefreshSourceRow', 'model-ops Gemini research refresh source row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiResearchRefreshAdoptionRow', 'model-ops Gemini research refresh adoption row type'),
  () => assertIncludes(modelOpsApi, 'gemini_research_refresh_gate', 'model-ops Gemini research refresh response binding'),
  () => assertIncludes(modelOpsApi, 'research_source_rows', 'model-ops Gemini research refresh source rows payload guard'),
  () => assertIncludes(modelOpsApi, 'adoption_rows', 'model-ops Gemini research refresh adoption rows payload guard'),
  () => assertIncludes(modelOpsApi, 'refresh_policy', 'model-ops Gemini research refresh policy payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiResearchRefreshGate', 'model-ops Gemini research refresh getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsGeminiResearchRefreshGate', 'model-ops Gemini research refresh evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-research-refresh-gate', 'model-ops Gemini research refresh endpoint'),
  () => assertIncludes(modelOpsPage, 'Gemini cheap-first route preflight', 'model-ops Gemini cheap-first route preflight panel'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstRoutePreflight', 'model-ops Gemini cheap-first route preflight state binding'),
  () => assertIncludes(modelOpsPage, 'geminiResearchRefreshGate', 'model-ops Gemini research refresh state binding'),
  () => assertIncludes(modelOpsPage, 'activeGeminiResearchRefreshGate', 'model-ops Gemini research refresh active binding'),
  () => assertIncludes(modelOpsPage, 'geminiResearchRefreshSourceRows', 'model-ops Gemini research refresh source rows binding'),
  () => assertIncludes(modelOpsPage, 'geminiResearchRefreshAdoptionRows', 'model-ops Gemini research refresh adoption rows binding'),
  () => assertIncludes(modelOpsPage, 'geminiResearchRefreshChecks', 'model-ops Gemini research refresh checks binding'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstLegalBenchmarkRouteRows', 'model-ops Gemini legal benchmark route join binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkRiskRouteReviews', 'model-ops Gemini legal benchmark route source binding'),
  () => assertIncludes(modelOpsPage, 'defaultGeminiCheapFirstRoutePreflightPayload', 'model-ops Gemini cheap-first route preflight default payload'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenGeminiRoutePreflightPayloadText', 'model-ops Gemini cheap-first route preflight payload guard'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstRoutePreflightPayloadText', 'model-ops Gemini cheap-first route preflight payload textarea state'),
  () => assertIncludes(modelOpsPage, 'evaluateGeminiCheapFirstRoutePreflightPayload', 'model-ops Gemini cheap-first route preflight submit handler'),
  () => assertIncludes(modelOpsPage, 'Route preflight payload', 'model-ops Gemini cheap-first route preflight payload panel'),
  () => assertIncludes(modelOpsPage, 'Evaluate route preflight', 'model-ops Gemini cheap-first route preflight submit button'),
  () => assertIncludes(modelOpsPage, 'observed_models', 'model-ops Gemini cheap-first route preflight observed models sample'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstRouteRows', 'model-ops Gemini cheap-first route row binding'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstVariantRows', 'model-ops Gemini cheap-first variant row binding'),
  () => assertIncludes(modelOpsPage, 'geminiCheapFirstSourceRows', 'model-ops Gemini cheap-first source row binding'),
  () => assertIncludes(modelOpsPage, 'Gemini research refresh gate', 'model-ops Gemini research refresh panel'),
  () => assertIncludes(modelOpsPage, 'Legal benchmark routing metadata', 'model-ops Gemini legal benchmark routing metadata panel'),
  () => assertIncludes(modelOpsPage, 'Research source rows', 'model-ops Gemini research source rows panel'),
  () => assertIncludes(modelOpsPage, 'required_source_ids', 'model-ops Gemini research required source ids binding'),
  () => assertIncludes(modelOpsPage, 'public_benchmark_statuses', 'model-ops Gemini public benchmark status binding'),
  () => assertIncludes(modelOpsPage, 'release_gate_links', 'model-ops Gemini legal benchmark release gate links binding'),
  () => assertIncludes(modelOpsPage, 'external_refresh_completed', 'model-ops Gemini research external refresh boundary'),
  () => assertIncludes(modelOpsPage, 'public_benchmark_downloaded', 'model-ops Gemini benchmark download boundary'),
  () => assertIncludes(modelOpsPage, 'default_allowed_without_review', 'model-ops Gemini cheap-first route default boundary'),
  () => assertIncludes(modelOpsPage, 'accepted_alias_examples', 'model-ops Gemini cheap-first route alias examples'),
  () => assertIncludes(modelOpsPage, 'source_signal_summary', 'model-ops Gemini cheap-first route source signal summary type'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops Gemini cheap-first route no-write boundary'),
  () => assertIncludes(modelOpsPage, 'credentials_included', 'model-ops Gemini cheap-first route credential boundary'),
  () => assertBefore(modelOpsPage, 'Legal benchmark routing metadata', 'geminiCheapFirstVariantRows.slice(0, 8)', 'model-ops Gemini research/benchmark metadata precedes variant details'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit matrix type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGatewayModelFitTaskRow', 'model-ops observed gateway model fit task row type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/observed-gateway-model-fit-matrix', 'model-ops observed gateway model fit endpoint'),
  () => assertIncludes(modelOpsApi, 'observed_gateway_model_fit_matrix?: ModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit response binding'),
  () => assertIncludes(modelOpsApi, 'task_fit_rows: ModelOpsObservedGatewayModelFitTaskRow[]', 'model-ops observed gateway model fit task rows type'),
  () => assertIncludes(modelOpsApi, 'observed_model_rows: ModelOpsObservedGatewayModelFitModelRow[]', 'model-ops observed gateway model fit model rows type'),
  () => assertIncludes(modelOpsApi, 'gateway_fit_status: string', 'model-ops observed gateway model fit status type'),
  () => assertIncludes(modelOpsApi, 'cheapest_gateway_model?: string | null', 'model-ops observed gateway cheapest model type'),
  () => assertIncludes(modelOpsApi, 'cheapest_canonical_model?: string | null', 'model-ops observed gateway cheapest canonical type'),
  () => assertIncludes(modelOpsApi, 'observed_model_candidate_count', 'model-ops observed model candidate summary type'),
  () => assertIncludes(modelOpsApi, 'accepted_observed_model_count', 'model-ops accepted observed model summary type'),
  () => assertIncludes(modelOpsApi, 'source_summaries', 'model-ops observed gateway source summaries type'),
  () => assertIncludes(modelOpsPage, 'Observed gateway model fit matrix', 'model-ops observed gateway model fit panel'),
  () => assertIncludes(modelOpsPage, 'activeObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit active binding'),
  () => assertIncludes(modelOpsPage, 'observedGatewayFitTaskRows', 'model-ops observed gateway task rows binding'),
  () => assertIncludes(modelOpsPage, 'observedGatewayFitModelRows', 'model-ops observed gateway model rows binding'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiRouteCoverageBridgeRows', 'model-ops observed gateway bridge rows binding'),
  () => assertIncludes(modelOpsPage, 'Gemini/NewAPI cheap-first route coverage bridge', 'model-ops observed gateway bridge panel'),
  () => assertIncludes(modelOpsPage, 'alias_count', 'model-ops observed gateway bridge alias count'),
  () => assertIncludes(modelOpsPage, 'cheap_first_aligned', 'model-ops observed gateway bridge cheap-first alignment'),
  () => assertIncludes(modelOpsPage, 'default_allowed_without_review', 'model-ops observed gateway bridge default boundary'),
  () => assertIncludes(modelOpsPage, 'uses_runtime_router', 'model-ops observed gateway bridge runtime router'),
  () => assertIncludes(modelOpsPage, 'returns_route_payloads', 'model-ops observed gateway bridge route payload boundary'),
  () => assertIncludes(modelOpsPage, 'route_gap_reason_codes', 'model-ops observed gateway bridge route gap reasons'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRuntimeExplicitModelFitRequestRow', 'model-ops runtime explicit model fit request row type'),
  () => assertIncludes(modelOpsApi, 'runtime_explicit_model_fit_gate?: ModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit response binding'),
  () => assertIncludes(modelOpsApi, 'request_rows: ModelOpsRuntimeExplicitModelFitRequestRow[]', 'model-ops runtime explicit model fit row payload type'),
  () => assertIncludes(modelOpsApi, 'runtime_policy: Record<string, string>', 'model-ops runtime explicit model fit policy type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/runtime-explicit-model-fit-gate', 'model-ops runtime explicit model fit endpoint'),
  () => assertIncludes(modelOpsPage, 'Runtime explicit model fit gate', 'model-ops runtime explicit model fit panel'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitGate', 'model-ops runtime explicit model fit state binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitRows', 'model-ops runtime explicit model fit rows binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitChecks', 'model-ops runtime explicit model fit checks binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitPolicyEntries', 'model-ops runtime explicit model fit policy binding'),
  () => assertIncludes(modelOpsPage, 'unknown_gateway_passthrough_count', 'model-ops runtime explicit model fit unknown passthrough summary'),
  () => assertIncludes(modelOpsPage, 'explicit_over_budget_allowed_count', 'model-ops runtime explicit model fit over-budget summary'),
  () => assertIncludes(modelOpsPage, 'downgraded_to_recommended_count', 'model-ops runtime explicit model fit downgrade summary'),
  () => assertIncludes(modelOpsPage, 'cheap_first_enforced_count', 'model-ops runtime explicit model fit cheap-first summary'),
  () => assertIncludes(modelOpsPage, 'observed_fit_review_count', 'model-ops runtime explicit model fit observed review summary'),
  () => assertIncludes(modelOpsPage, 'forbidden_payload_field_count', 'model-ops runtime explicit model fit payload field summary'),
  () => assertIncludes(modelOpsPage, 'requested_resolved_model', 'model-ops runtime explicit requested resolved model binding'),
  () => assertIncludes(modelOpsPage, 'resolved_model', 'model-ops runtime explicit resolved model binding'),
  () => assertIncludes(modelOpsPage, 'canonical_model', 'model-ops runtime explicit canonical model binding'),
  () => assertIncludes(modelOpsPage, 'known_catalog_model', 'model-ops runtime explicit catalog binding'),
  () => assertIncludes(modelOpsPage, 'allow_over_budget_model', 'model-ops runtime explicit allow over budget binding'),
  () => assertIncludes(modelOpsPage, 'routed_to_recommended_model', 'model-ops runtime explicit route enforcement binding'),
  () => assertIncludes(modelOpsPage, 'observed_fit_status', 'model-ops runtime explicit observed fit binding'),
  () => assertIncludes(modelOpsPage, 'runtime_fit_status', 'model-ops runtime explicit fit status binding'),
  () => assertIncludes(modelOpsPage, 'route_reason_codes', 'model-ops runtime explicit route reason binding'),
  () => assertIncludes(modelOpsPage, 'runtime_behavior_changed', 'model-ops runtime explicit behavior-change claim boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops runtime explicit gateway boundary'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops runtime explicit no config-write boundary'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubEndpointRouteCoverageGate', 'model-ops AIHub endpoint route coverage gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubEndpointRouteCoverageRow', 'model-ops AIHub endpoint route coverage row type'),
  () => assertIncludes(modelOpsApi, 'aihub_endpoint_route_coverage_gate?: ModelOpsAIHubEndpointRouteCoverageGate', 'model-ops AIHub endpoint route coverage response binding'),
  () => assertIncludes(modelOpsApi, 'returns_task_inference: boolean', 'model-ops AIHub endpoint task inference coverage type'),
  () => assertIncludes(modelOpsApi, 'returns_usage_units: boolean', 'model-ops AIHub endpoint usage unit coverage type'),
  () => assertIncludes(modelOpsApi, 'returns_usage_units_count: number', 'model-ops AIHub endpoint usage unit summary type'),
  () => assertIncludes(modelOpsApi, 'endpoint_rows?: unknown', 'model-ops AIHub endpoint route coverage payload guard endpoint rows'),
  () => assertIncludes(modelOpsApi, 'coverage_matrix?: unknown', 'model-ops AIHub endpoint route coverage payload guard matrix'),
  () => assertIncludes(modelOpsApi, 'getModelOpsAIHubEndpointRouteCoverageGate', 'model-ops AIHub endpoint route coverage getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/aihub-endpoint-route-coverage-gate', 'model-ops AIHub endpoint route coverage endpoint'),
  () => assertIncludes(modelOpsPage, 'AIHub endpoint route coverage gate', 'model-ops AIHub endpoint route coverage panel'),
  () => assertIncludes(modelOpsPage, 'aihubEndpointRouteCoverageGate', 'model-ops AIHub endpoint route coverage state binding'),
  () => assertIncludes(modelOpsPage, 'aihubEndpointRouteRows', 'model-ops AIHub endpoint route coverage row binding'),
  () => assertIncludes(modelOpsPage, 'aihubEndpointRouteCoverageMatrixRows', 'model-ops AIHub endpoint route coverage matrix binding'),
  () => assertIncludes(modelOpsPage, 'aihubEndpointRouteChecks', 'model-ops AIHub endpoint route coverage checks binding'),
  () => assertIncludes(modelOpsPage, 'uses_runtime_router', 'model-ops AIHub endpoint route runtime-router flag'),
  () => assertIncludes(modelOpsPage, 'uses_budget_decision', 'model-ops AIHub endpoint route budget-decision flag'),
  () => assertIncludes(modelOpsPage, 'records_route_telemetry', 'model-ops AIHub endpoint route telemetry flag'),
  () => assertIncludes(modelOpsPage, 'returns_route_payloads', 'model-ops AIHub endpoint route payload flag'),
  () => assertIncludes(modelOpsPage, 'returns_task_inference', 'model-ops AIHub endpoint task inference flag'),
  () => assertIncludes(modelOpsPage, 'returns_usage_units', 'model-ops AIHub endpoint usage units flag'),
  () => assertIncludes(modelOpsPage, 'media_speech_review', 'model-ops AIHub endpoint route media/speech review flag'),
  () => assertIncludes(modelOpsPage, 'route_gap_reason_codes', 'model-ops AIHub endpoint route gap reason binding'),
  () => assertIncludes(modelOpsPage, 'claims_default_route_changed', 'model-ops AIHub endpoint route default-change claim boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops AIHub endpoint route gateway boundary'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops AIHub endpoint route no config-write boundary'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaSpeechDefaultCatalogGate', 'model-ops AIHub media/speech default catalog gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaSpeechDefaultCatalogDefaultRow', 'model-ops AIHub media/speech default catalog default row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaSpeechDefaultCatalogReviewItem', 'model-ops AIHub media/speech default catalog review item type'),
  () => assertIncludes(modelOpsApi, 'aihub_media_speech_default_catalog_gate?: ModelOpsAIHubMediaSpeechDefaultCatalogGate', 'model-ops AIHub media/speech default catalog response binding'),
  () => assertIncludes(modelOpsApi, 'default_rows?: unknown', 'model-ops AIHub media/speech default catalog payload guard default rows'),
  () => assertIncludes(modelOpsApi, 'review_items?: unknown', 'model-ops AIHub media/speech default catalog payload guard review items'),
  () => assertIncludes(modelOpsApi, 'getModelOpsAIHubMediaSpeechDefaultCatalogGate', 'model-ops AIHub media/speech default catalog getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/aihub-media-speech-default-catalog-gate', 'model-ops AIHub media/speech default catalog endpoint'),
  () => assertIncludes(modelOpsPage, 'AIHub media/speech default catalog gate', 'model-ops AIHub media/speech default catalog panel'),
  () => assertIncludes(modelOpsPage, 'activeAihubMediaSpeechDefaultCatalogGate', 'model-ops AIHub media/speech default catalog active binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaSpeechDefaultCatalogDefaultRows', 'model-ops AIHub media/speech default catalog default row binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaSpeechDefaultCatalogReviewItems', 'model-ops AIHub media/speech default catalog review item binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaSpeechDefaultCatalogChecks', 'model-ops AIHub media/speech default catalog checks binding'),
  () => assertIncludes(modelOpsPage, 'privacy_boundary', 'model-ops AIHub media/speech default catalog privacy boundary'),
  () => assertIncludes(modelOpsPage, 'validation_commands', 'model-ops AIHub media/speech default catalog validation binding'),
  () => assertIncludes(modelOpsPage, 'missing_catalog_default_count', 'model-ops AIHub media/speech default catalog gap summary'),
  () => assertIncludes(modelOpsPage, 'future_family_gap_count', 'model-ops AIHub media/speech default catalog future gap summary'),
  () => assertNotMatches(
    aihubMediaSpeechDefaultCatalogGatePanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|request_body_value|response_body_value|headers_value|client_email|email|phone|identity|messages|content|file_url|media_url|download_url|signed_url|sample_text|input_excerpt|audio_bytes|image_bytes|video_bytes|binary_payload|base64|raw_audio|raw_image|audio_transcript|transcript_text|voice_sample)\b/i,
    'model-ops AIHub media/speech default catalog gate no secrets or raw media/speech/request/model fields',
  ),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaRuntimeCompatibilityGate', 'model-ops AIHub media runtime compatibility gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaRuntimeCompatibilityShapeRow', 'model-ops AIHub media runtime compatibility row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsAIHubMediaRuntimeCompatibilityReviewItem', 'model-ops AIHub media runtime compatibility review item type'),
  () => assertIncludes(modelOpsApi, 'aihub_media_runtime_compatibility_gate?: ModelOpsAIHubMediaRuntimeCompatibilityGate', 'model-ops AIHub media runtime compatibility response binding'),
  () => assertIncludes(modelOpsApi, 'runtime_shape_rows?: unknown', 'model-ops AIHub media runtime compatibility payload guard runtime rows'),
  () => assertIncludes(modelOpsApi, 'getModelOpsAIHubMediaRuntimeCompatibilityGate', 'model-ops AIHub media runtime compatibility getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/aihub-media-runtime-compatibility-gate', 'model-ops AIHub media runtime compatibility endpoint'),
  () => assertIncludes(modelOpsPage, 'AIHub media runtime compatibility gate', 'model-ops AIHub media runtime compatibility panel'),
  () => assertIncludes(modelOpsPage, 'activeAihubMediaRuntimeCompatibilityGate', 'model-ops AIHub media runtime compatibility active binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaRuntimeCompatibilityShapeRows', 'model-ops AIHub media runtime compatibility shape rows binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaRuntimeCompatibilityReviewItems', 'model-ops AIHub media runtime compatibility review items binding'),
  () => assertIncludes(modelOpsPage, 'aihubMediaRuntimeCompatibilityChecks', 'model-ops AIHub media runtime compatibility checks binding'),
  () => assertIncludes(modelOpsPage, 'openai_compatible_shape_count', 'model-ops AIHub media runtime OpenAI-compatible summary'),
  () => assertIncludes(modelOpsPage, 'adapter_review_required_count', 'model-ops AIHub media runtime adapter review summary'),
  () => assertIncludes(modelOpsPage, 'future_route_required_count', 'model-ops AIHub media runtime future route summary'),
  () => assertIncludes(modelOpsPage, 'current_endpoint_shape', 'model-ops AIHub media runtime current shape binding'),
  () => assertIncludes(modelOpsPage, 'current_runtime_methods', 'model-ops AIHub media runtime method binding'),
  () => assertIncludes(modelOpsPage, 'current_response_contract', 'model-ops AIHub media runtime response-contract binding'),
  () => assertIncludes(modelOpsPage, 'native_runtime_shape', 'model-ops AIHub media runtime native shape binding'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.aihub_media_runtime_compatibility_gate', 'model-ops AIHub media runtime aggregate reuse'),
  () => assertBefore(
    modelOpsPage,
    'AIHub media/speech default catalog gate',
    'AIHub media runtime compatibility gate',
    'model-ops AIHub media runtime compatibility follows media/speech default catalog',
  ),
  () => assertBefore(
    modelOpsPage,
    'AIHub media runtime compatibility gate',
    'Gemini embedding cheap-first preflight',
    'model-ops AIHub media runtime compatibility precedes embedding preflight',
  ),
  () => assertNotMatches(
    aihubMediaRuntimeCompatibilityGatePanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|request_body_value|response_body_value|headers_value|client_email|email|phone|identity|messages|content|file_url|media_url|download_url|signed_url|sample_text|input_excerpt|audio_bytes|image_bytes|video_bytes|binary_payload|base64|raw_audio|raw_image|audio_transcript|transcript_text|voice_sample)\b/i,
    'model-ops AIHub media runtime compatibility gate no secrets or raw media/speech/request/model fields',
  ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiEmbeddingCheapFirstPreflight', 'model-ops Gemini embedding cheap-first preflight type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiEmbeddingCheapFirstPreflightEmbeddingRow', 'model-ops Gemini embedding row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiEmbeddingCheapFirstPreflightRouteRow', 'model-ops Gemini embedding route row type'),
  () => assertIncludes(modelOpsApi, 'gemini_embedding_cheap_first_preflight?: ModelOpsGeminiEmbeddingCheapFirstPreflight', 'model-ops Gemini embedding preflight response binding'),
  () => assertIncludes(modelOpsApi, 'embedding_rows?: unknown', 'model-ops Gemini embedding preflight payload guard embedding rows'),
  () => assertIncludes(modelOpsApi, 'route_rows?: unknown', 'model-ops Gemini embedding preflight payload guard route rows'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiEmbeddingCheapFirstPreflight', 'model-ops Gemini embedding preflight getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-embedding-cheap-first-preflight', 'model-ops Gemini embedding preflight endpoint'),
  () => assertIncludes(modelOpsPage, 'Gemini embedding cheap-first preflight', 'model-ops Gemini embedding preflight panel'),
  () => assertIncludes(modelOpsPage, 'geminiEmbeddingCheapFirstPreflight', 'model-ops Gemini embedding preflight state binding'),
  () => assertIncludes(modelOpsPage, 'activeGeminiEmbeddingCheapFirstPreflight', 'model-ops Gemini embedding preflight active binding'),
  () => assertIncludes(modelOpsPage, 'geminiEmbeddingRows', 'model-ops Gemini embedding rows binding'),
  () => assertIncludes(modelOpsPage, 'geminiEmbeddingRouteRows', 'model-ops Gemini embedding route rows binding'),
  () => assertIncludes(modelOpsPage, 'geminiEmbeddingChecks', 'model-ops Gemini embedding checks binding'),
  () => assertIncludes(modelOpsPage, 'text_embedding_ready_count', 'model-ops Gemini embedding text-ready summary'),
  () => assertIncludes(modelOpsPage, 'multimodal_review_count', 'model-ops Gemini embedding multimodal review summary'),
  () => assertIncludes(modelOpsPage, 'review_route_count', 'model-ops Gemini embedding review route summary'),
  () => assertIncludes(modelOpsPage, 'index_written', 'model-ops Gemini embedding no index-write boundary'),
  () => assertIncludes(modelOpsPage, 'default_changed', 'model-ops Gemini embedding no default-change boundary'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.gemini_embedding_cheap_first_preflight', 'model-ops Gemini embedding aggregate reuse'),
  () => assertNotMatches(
    geminiEmbeddingCheapFirstPreflightPanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|output_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|request_body_value|response_body_value|headers_value|client_email|email|phone|identity|messages|content|source_chunk|source_chunks|raw_embedding|embedding_vector|embedding_vectors|vector_values|index_document_text|file_url|media_url|download_url|signed_url|sample_text|input_excerpt|base64|binary_payload)\b/i,
    'model-ops Gemini embedding cheap-first preflight no secrets or raw embedding/request/model/index fields',
  ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGenTxtRoutingGuard', 'model-ops gentxt routing guard type'),
  () => assertIncludes(modelOpsApi, 'gentxt_routing_guard?: ModelOpsGenTxtRoutingGuard', 'model-ops gentxt routing guard response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGenTxtRoutingGuard', 'model-ops gentxt routing guard getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gentxt-routing-guard', 'model-ops gentxt routing guard endpoint'),
  () => assertIncludes(modelOpsPage, 'AIHub gentxt routing guard', 'model-ops gentxt routing guard panel'),
  () => assertIncludes(modelOpsPage, 'activeGenTxtRoutingGuard', 'model-ops gentxt routing guard active binding'),
  () => assertIncludes(modelOpsPage, 'genTxtRoutingGuardMediaRows', 'model-ops gentxt routing guard media row binding'),
  () => assertIncludes(modelOpsPage, 'media_task_blocked_count', 'model-ops gentxt routing guard blocked summary'),
  () => assertIncludes(modelOpsPage, 'text_task_allowed_count', 'model-ops gentxt routing guard allowlist summary'),
  () => assertIncludes(modelOpsPage, 'gentxt_allowed', 'model-ops gentxt routing guard alias boundary'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayConnectionProfile', 'model-ops gateway connection profile type'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayConnectionProfileRole', 'model-ops gateway connection profile role type'),
  () => assertIncludes(modelOpsApi, 'gateway_connection_profile?: ModelGatewayConnectionProfile', 'model-ops gateway connection profile response binding'),
  () => assertIncludes(modelOpsApi, 'getModelGatewayConnectionProfile', 'model-ops gateway connection profile getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelGatewayConnectionProfile', 'model-ops gateway connection profile evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gateway-connection-profile', 'model-ops gateway connection profile endpoint'),
  () => assertIncludes(modelOpsPage, 'Gateway connection profile', 'model-ops gateway connection profile panel'),
  () => assertIncludes(modelOpsPage, 'gatewayConnectionProfile', 'model-ops gateway connection profile binding'),
  () => assertIncludes(modelOpsPage, 'gatewayConnectionRows', 'model-ops gateway connection role rows binding'),
  () => assertIncludes(modelOpsPage, 'gatewayConnectionChecks', 'model-ops gateway connection checks binding'),
  () => assertIncludes(modelOpsPage, 'normalized_base_url_display', 'model-ops gateway connection normalized URL display binding'),
  () => assertIncludes(modelOpsPage, 'base_url_was_normalized', 'model-ops gateway connection normalization flag'),
  () => assertIncludes(modelOpsPage, 'remote_bare_url_normalized_to_v1', 'model-ops gateway connection bare remote normalization flag'),
  () => assertIncludes(modelOpsPage, 'runtime_client_uses_normalized_base_url', 'model-ops gateway connection runtime normalization boundary'),
  () => assertIncludes(modelOpsPage, 'runtime_base_url_source', 'model-ops gateway connection runtime source binding'),
  () => assertIncludes(modelOpsPage, 'api_key_display', 'model-ops gateway connection key placeholder binding'),
  () => assertIncludes(modelOpsPage, 'credentials_included', 'model-ops gateway connection credential boundary'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayRuntimeConfiguration', 'model-ops gateway runtime configuration type'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayRuntimeConfigurationRole', 'model-ops gateway runtime configuration role type'),
  () => assertIncludes(modelOpsApi, 'gateway_runtime_configuration?: ModelGatewayRuntimeConfiguration', 'model-ops gateway runtime configuration response binding'),
  () => assertIncludes(modelOpsApi, 'getModelGatewayRuntimeConfiguration', 'model-ops gateway runtime configuration getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelGatewayRuntimeConfiguration', 'model-ops gateway runtime configuration evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gateway-runtime-configuration', 'model-ops gateway runtime configuration endpoint'),
  () => assertIncludes(modelOpsApi, 'role_rows: ModelGatewayRuntimeConfigurationRole[]', 'model-ops gateway runtime configuration role rows type'),
  () => assertIncludes(modelOpsApi, 'runtime_probe_sequence', 'model-ops gateway runtime configuration probe sequence type'),
  () => assertIncludes(modelOpsPage, 'Gateway runtime configuration', 'model-ops gateway runtime configuration panel'),
  () => assertIncludes(modelOpsPage, 'gatewayRuntimeConfiguration', 'model-ops gateway runtime configuration binding'),
  () => assertIncludes(modelOpsPage, 'gatewayRuntimeRoleRows', 'model-ops gateway runtime role rows binding'),
  () => assertIncludes(modelOpsPage, 'gatewayRuntimeProbeRows', 'model-ops gateway runtime probe rows binding'),
  () => assertIncludes(modelOpsPage, 'client_base_url_source', 'model-ops gateway runtime client source binding'),
  () => assertIncludes(modelOpsPage, 'api_key_env', 'model-ops gateway runtime key env binding'),
  () => assertIncludes(modelOpsPage, 'runtime_probe_sequence', 'model-ops gateway runtime aggregate binding'),
  () => assertIncludes(modelOpsPage, 'configuration_policy', 'model-ops gateway runtime configuration policy binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsNewApiChannelBootstrap', 'model-ops NewAPI channel bootstrap type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsNewApiChannelBootstrapRole', 'model-ops NewAPI channel bootstrap role type'),
  () => assertIncludes(modelOpsApi, 'newapi_channel_bootstrap?: ModelOpsNewApiChannelBootstrap', 'model-ops NewAPI channel bootstrap response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsNewApiChannelBootstrap', 'model-ops NewAPI channel bootstrap getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsNewApiChannelBootstrap', 'model-ops NewAPI channel bootstrap evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/newapi-channel-bootstrap', 'model-ops NewAPI channel bootstrap endpoint'),
  () => assertIncludes(modelOpsPage, 'NewAPI channel bootstrap', 'model-ops NewAPI channel bootstrap panel'),
  () => assertIncludes(modelOpsPage, 'newapiChannelBootstrap', 'model-ops NewAPI channel bootstrap binding'),
  () => assertIncludes(modelOpsPage, 'newapiChannelRoleRows', 'model-ops NewAPI channel bootstrap role rows binding'),
  () => assertIncludes(modelOpsPage, 'newapiChannelSetupSteps', 'model-ops NewAPI channel bootstrap setup steps binding'),
  () => assertIncludes(modelOpsPage, 'newapiChannelEnvEntries', 'model-ops NewAPI channel bootstrap env binding'),
  () => assertIncludes(modelOpsPage, 'premium_exception_review_count', 'model-ops NewAPI channel bootstrap premium review summary'),
  () => assertIncludes(modelOpsPage, 'normalized_base_url_display', 'model-ops NewAPI channel bootstrap normalized URL display'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops NewAPI channel bootstrap no-write boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops NewAPI channel bootstrap no-gateway boundary'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayProbeRunbookGate', 'model-ops gateway probe runbook gate type'),
  () => assertIncludes(modelOpsApi, 'gateway_probe_runbook_gate?: ModelGatewayProbeRunbookGate', 'model-ops gateway probe runbook response binding'),
  () => assertIncludes(modelOpsApi, 'getModelGatewayProbeRunbookGate', 'model-ops gateway probe runbook getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelGatewayProbeRunbookGate', 'model-ops gateway probe runbook evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gateway-probe-runbook-gate', 'model-ops gateway probe runbook endpoint'),
  () => assertIncludes(modelOpsPage, 'Gateway probe runbook gate', 'model-ops gateway probe runbook panel'),
  () => assertIncludes(modelOpsPage, 'gatewayProbeRunbookGate', 'model-ops gateway probe runbook binding'),
  () => assertIncludes(modelOpsPage, 'gatewayProbeRunbookSteps', 'model-ops gateway probe runbook steps binding'),
  () => assertIncludes(modelOpsPage, 'gatewayProbeRunbookChecks', 'model-ops gateway probe runbook checks binding'),
  () => assertIncludes(modelOpsPage, 'ready_step_count', 'model-ops gateway probe runbook ready summary'),
  () => assertIncludes(modelOpsPage, 'next_step_id', 'model-ops gateway probe runbook next step binding'),
  () => assertIncludes(modelOpsPage, 'source_statuses', 'model-ops gateway probe runbook source status binding'),
  () => assertIncludes(modelOpsPage, 'forbidden_payload_field_count', 'model-ops gateway probe runbook forbidden field summary'),
  () => assertIncludes(modelOpsPage, 'default_model_changed', 'model-ops gateway probe runbook no default change boundary'),
  () => assertIncludes(modelOpsPage, 'traffic_shifted', 'model-ops gateway probe runbook no traffic shift boundary'),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Model catalog candidate impact replay</h2>',
    '<h2 className="text-xl font-black text-stone-950">Gateway connection profile</h2>',
    'model-ops gateway connection profile follows catalog impact replay',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Gateway connection profile</h2>',
    '<h2 className="text-xl font-black text-stone-950">Gateway runtime configuration</h2>',
    'model-ops gateway runtime configuration follows gateway connection profile',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Gateway runtime configuration</h2>',
    '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap</h2>',
    'model-ops NewAPI channel bootstrap follows gateway runtime configuration',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">NewAPI channel bootstrap</h2>',
    '<h2 className="text-xl font-black text-stone-950">Gateway health plan</h2>',
    'model-ops NewAPI channel bootstrap precedes gateway health plan',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Gateway health plan</h2>',
    '<h2 className="text-xl font-black text-stone-950">Gateway probe runbook gate</h2>',
    'model-ops gateway probe runbook follows gateway health plan',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Gateway probe runbook gate</h2>',
    '<h2 className="text-xl font-black text-stone-950">Gateway probe evaluation</h2>',
    'model-ops gateway probe evaluation follows runbook gate',
  ),
  () => assertNotMatches(
    gatewayRuntimeConfigurationPanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|gateway_response|email|phone|password)\b/i,
    'model-ops gateway runtime configuration no secrets or raw request/response fields',
  ),
  () => assertNotMatches(
    newapiChannelBootstrapPanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|gateway_response|client_email|phone|password)\b/i,
    'model-ops NewAPI channel bootstrap no secrets or raw request/response fields',
  ),
  () => assertNotMatches(
    gatewayProbeRunbookGatePanel,
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer_token|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|gateway_response|client_email|email|phone|password|raw_legal_text|document_text)\b/i,
    'model-ops gateway probe runbook no secrets or raw request/response fields',
  ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first route preflight</h2>',
      'model-ops route preflight follows cheap-first coverage gate',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first route preflight</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
      'model-ops observed gateway model fit matrix follows route preflight',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
      '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
      'model-ops runtime explicit model fit gate follows observed gateway fit matrix',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub endpoint route coverage gate</h2>',
      'model-ops AIHub endpoint route coverage follows route preflight',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">AIHub endpoint route coverage gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub media/speech default catalog gate</h2>',
      'model-ops AIHub media/speech default catalog follows AIHub endpoint route coverage',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">AIHub media/speech default catalog gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
      'model-ops Gemini embedding preflight follows AIHub media/speech default catalog',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub gentxt routing guard</h2>',
      'model-ops gentxt routing guard follows Gemini embedding preflight',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">AIHub gentxt routing guard</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini catalog source audit</h2>',
      'model-ops gentxt routing guard precedes catalog source audit',
    ),
  () => assertIncludes(modelOpsApi, 'ModelGatewayRequestCompatibilityGate', 'model-ops gateway request compatibility gate type'),
  () => assertIncludes(modelOpsApi, 'ModelGatewayRequestCompatibilityRow', 'model-ops gateway request compatibility row type'),
  () => assertIncludes(modelOpsApi, 'gateway_request_compatibility_gate', 'model-ops gateway request compatibility response binding'),
  () => assertIncludes(modelOpsApi, 'task_rows?: unknown', 'model-ops gateway request compatibility payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelGatewayRequestCompatibilityGate', 'model-ops gateway request compatibility getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelGatewayRequestCompatibilityGate', 'model-ops gateway request compatibility evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gateway-request-compatibility-gate', 'model-ops gateway request compatibility endpoint'),
  () => assertIncludes(modelOpsApi, 'reasoning_effort?: string | null', 'model-ops gateway request compatibility reasoning type'),
  () => assertIncludes(modelOpsApi, 'request_body_returned: boolean', 'model-ops gateway request compatibility request body boundary type'),
  () => assertIncludes(modelOpsApi, 'headers_returned: boolean', 'model-ops gateway request compatibility header boundary type'),
  () => assertIncludes(modelOpsPage, 'Gateway request compatibility gate', 'model-ops gateway request compatibility panel'),
  () => assertIncludes(modelOpsPage, 'gatewayRequestCompatibilityGate', 'model-ops gateway request compatibility state binding'),
  () => assertIncludes(modelOpsPage, 'gatewayRequestCompatibilityRows', 'model-ops gateway request compatibility row binding'),
  () => assertIncludes(modelOpsPage, 'gatewayRequestCompatibilityChecks', 'model-ops gateway request compatibility check binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_ready_count', 'model-ops gateway request compatibility cheap-first summary'),
  () => assertIncludes(modelOpsPage, 'json_response_format_count', 'model-ops gateway request compatibility JSON summary'),
  () => assertIncludes(modelOpsPage, 'reasoning_omitted_count', 'model-ops gateway request compatibility reasoning summary'),
  () => assertIncludes(modelOpsPage, 'gateway_request_shape', 'model-ops gateway request compatibility shape binding'),
  () => assertIncludes(modelOpsPage, 'request body returned:', 'model-ops gateway request compatibility request body boundary'),
  () => assertIncludes(modelOpsPage, 'headers returned:', 'model-ops gateway request compatibility headers boundary'),
  () => assertIncludes(modelOpsPage, 'gatewayRequestCompatibilityGate.validation_commands', 'model-ops gateway request compatibility validation command'),
  () => assertIncludes(modelOpsPage, 'release_action', 'model-ops gateway request compatibility release action binding'),
  () => assertBefore(modelOpsPage, 'Request policy', 'Gateway request compatibility gate', 'model-ops gateway request compatibility follows request policy'),
  () => assertBefore(modelOpsPage, 'Gateway request compatibility gate', 'Request execution preflight', 'model-ops gateway request compatibility before request execution preflight'),
  () => assertBefore(modelOpsPage, 'Request execution preflight', 'Request execution observation gate', 'model-ops request execution preflight before observation gate'),
  () => assertBefore(modelOpsPage, 'Request execution observation gate', 'Request cost bounds', 'model-ops request execution observation gate before request cost bounds'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionPreflight', 'model-ops request execution preflight type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionPreflightRow', 'model-ops request execution preflight row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionPreflightPayload', 'model-ops request execution preflight payload type'),
  () => assertIncludes(modelOpsApi, 'request_execution_preflight', 'model-ops request execution preflight response binding'),
  () => assertIncludes(modelOpsApi, 'request_rows?: unknown', 'model-ops request execution preflight payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelOpsRequestExecutionPreflight', 'model-ops request execution preflight getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsRequestExecutionPreflight', 'model-ops request execution preflight evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/request-execution-preflight', 'model-ops request execution preflight endpoint'),
  () => assertIncludes(modelOpsPage, 'Request execution preflight', 'model-ops request execution preflight panel'),
  () => assertIncludes(modelOpsPage, 'requestExecutionPreflight', 'model-ops request execution preflight state binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionRows', 'model-ops request execution preflight row binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionChecks', 'model-ops request execution preflight check binding'),
  () => assertIncludes(modelOpsPage, 'estimated_cost_usd_sum', 'model-ops request execution preflight cost summary'),
  () => assertIncludes(modelOpsPage, 'local_downgrade_count', 'model-ops request execution preflight downgrade summary'),
  () => assertIncludes(modelOpsPage, 'cheap_first_ready_count', 'model-ops request execution preflight cheap-first summary'),
  () => assertIncludes(modelOpsPage, 'fallback_rows', 'model-ops request execution preflight fallback binding'),
  () => assertIncludes(modelOpsPage, 'release_action', 'model-ops request execution preflight release action binding'),
  () => assertIncludes(modelOpsApi, 'request_body_included', 'model-ops request execution preflight request body boundary type'),
  () => assertIncludes(modelOpsApi, 'headers_included', 'model-ops request execution preflight headers boundary type'),
  () => assertIncludes(modelOpsApi, 'prompts_included', 'model-ops request execution preflight prompt boundary type'),
  () => assertIncludes(modelOpsPage, 'requestExecutionPrivacyEntries', 'model-ops request execution preflight privacy binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionClaimEntries', 'model-ops request execution preflight claim binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionPreflight.validation_commands', 'model-ops request execution preflight validation command'),
  () => assertIncludes(modelOpsPage, 'Execution policy', 'model-ops request execution policy section'),
  () => assertIncludes(modelOpsPage, 'Fallbacks', 'model-ops request execution fallback column'),
  () => assertIncludes(modelOpsPage, 'Tokens and cost', 'model-ops request execution token cost column'),
  () => assertNotMatches(
    sourceSection(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Request execution preflight</h2>',
      '<h2 className="text-xl font-black text-stone-950">Request cost bounds</h2>',
      'model-ops request execution preflight section',
    ),
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw[_ -]?prompt|prompt_payload|raw[_ -]?legal[_ -]?text|legal[_ -]?text|raw[_ -]?model[_ -]?output|model[_ -]?output|generated_text|candidate_text|document_text|client_email|email|phone|identity|user[_ -]?(?:id|identifier)|messages?|content)\b/i,
    'model-ops request execution preflight no raw legal/request/model/personal fields',
  ),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionObservationGate', 'model-ops request execution observation gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionObservationRow', 'model-ops request execution observation row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRequestExecutionObservationPayload', 'model-ops request execution observation payload type'),
  () => assertIncludes(modelOpsApi, 'request_execution_observation_gate', 'model-ops request execution observation response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsRequestExecutionObservationGate', 'model-ops request execution observation getter'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsRequestExecutionObservationGate', 'model-ops request execution observation evaluator'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/request-execution-observation-gate', 'model-ops request execution observation endpoint'),
  () => assertIncludes(modelOpsApi, 'gateway_response_included', 'model-ops request execution observation gateway response boundary type'),
  () => assertIncludes(modelOpsApi, 'request_sent_by_gate', 'model-ops request execution observation request sent claim type'),
  () => assertIncludes(modelOpsPage, 'Request execution observation gate', 'model-ops request execution observation panel'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationGate', 'model-ops request execution observation state binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationRows', 'model-ops request execution observation row binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationChecks', 'model-ops request execution observation check binding'),
  () => assertIncludes(modelOpsPage, 'matched_preflight_count', 'model-ops request execution observation preflight summary'),
  () => assertIncludes(modelOpsPage, 'cheap_first_observed_count', 'model-ops request execution observation cheap-first summary'),
  () => assertIncludes(modelOpsPage, 'fallback_used_count', 'model-ops request execution observation fallback summary'),
  () => assertIncludes(modelOpsPage, 'observed_cost_usd_sum', 'model-ops request execution observation cost summary'),
  () => assertIncludes(modelOpsPage, 'Observation policy', 'model-ops request execution observation policy section'),
  () => assertIncludes(modelOpsPage, 'Run metadata', 'model-ops request execution observation run metadata column'),
  () => assertIncludes(modelOpsPage, 'Preflight link', 'model-ops request execution observation preflight link column'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationPrivacyEntries', 'model-ops request execution observation privacy binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationClaimEntries', 'model-ops request execution observation claim binding'),
  () => assertIncludes(modelOpsPage, 'requestExecutionObservationGate.validation_commands', 'model-ops request execution observation validation command'),
  () => assertNotMatches(
    sourceSection(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Request execution observation gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Request cost bounds</h2>',
      'model-ops request execution observation section',
    ),
    /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw[_ -]?prompt|prompt_payload|raw[_ -]?legal[_ -]?text|legal[_ -]?text|raw[_ -]?model[_ -]?output|model[_ -]?output|generated_text|candidate_text|document_text|client_email|email|phone|identity|user[_ -]?(?:id|identifier)|messages?|content)\b/i,
    'model-ops request execution observation no raw legal/request/model/personal fields',
  ),
  () => assertIncludes(modelOpsPage, 'Gemini catalog source audit', 'model-ops Gemini catalog source audit panel'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogCandidatePatchPlan', 'model-ops catalog candidate patch plan type'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogCandidatePatchRow', 'model-ops catalog candidate patch row type'),
  () => assertIncludes(modelOpsApi, 'getModelCatalogCandidatePatchPlan', 'model-ops catalog candidate patch plan getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/catalog-candidate-patch-plan', 'model-ops catalog candidate patch plan endpoint'),
  () => assertIncludes(modelOpsApi, 'catalog_candidate_patch_plan', 'model-ops catalog candidate patch plan response binding'),
  () => assertIncludes(modelOpsApi, 'candidate_patch_rows', 'model-ops catalog candidate patch rows payload guard'),
  () => assertIncludes(modelOpsPage, 'Model catalog candidate patch plan', 'model-ops catalog candidate patch plan panel'),
  () => assertIncludes(modelOpsPage, 'catalogCandidatePatchRows', 'model-ops catalog candidate patch rows binding'),
  () => assertIncludes(modelOpsPage, 'catalogCandidatePatchChecks', 'model-ops catalog candidate patch checks binding'),
  () => assertIncludes(modelOpsPage, 'patch_action', 'model-ops catalog candidate patch action binding'),
  () => assertIncludes(modelOpsPage, 'release_action', 'model-ops catalog candidate release action binding'),
  () => assertIncludes(modelOpsPage, 'default_allowed_for_high_frequency', 'model-ops catalog candidate high-frequency binding'),
  () => assertIncludes(modelOpsPage, 'Privacy boundary', 'model-ops catalog candidate privacy boundary panel'),
  () => assertIncludes(modelOpsPage, 'Claim boundary', 'model-ops catalog candidate claim boundary panel'),
  () => assertBefore(modelOpsPage, 'Gemini catalog source audit', 'Model catalog candidate patch plan', 'model-ops catalog candidate after source audit'),
  () => assertBefore(modelOpsPage, 'Model catalog candidate patch plan', 'Model catalog candidate impact replay', 'model-ops catalog candidate patch before impact replay'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogCandidateImpactReplay', 'model-ops catalog candidate impact replay type'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogCandidateImpactRow', 'model-ops catalog candidate impact row type'),
  () => assertIncludes(modelOpsApi, 'ModelCatalogCandidateImpactTaskRow', 'model-ops catalog candidate impact task row type'),
  () => assertIncludes(modelOpsApi, 'getModelCatalogCandidateImpactReplay', 'model-ops catalog candidate impact replay getter'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/catalog-candidate-impact-replay', 'model-ops catalog candidate impact replay endpoint'),
  () => assertIncludes(modelOpsApi, 'catalog_candidate_impact_replay', 'model-ops catalog candidate impact replay response binding'),
  () => assertIncludes(modelOpsApi, 'candidate_rows', 'model-ops catalog candidate impact candidate rows payload guard'),
  () => assertIncludes(modelOpsApi, 'task_impact_rows', 'model-ops catalog candidate impact task rows payload guard'),
  () => assertIncludes(modelOpsPage, 'Model catalog candidate impact replay', 'model-ops catalog candidate impact replay panel'),
  () => assertIncludes(modelOpsPage, 'catalogCandidateImpactRows', 'model-ops catalog candidate impact task rows binding'),
  () => assertIncludes(modelOpsPage, 'catalogCandidateReplayRows', 'model-ops catalog candidate replay rows binding'),
  () => assertIncludes(modelOpsPage, 'catalogCandidateImpactChecks', 'model-ops catalog candidate impact checks binding'),
  () => assertIncludes(modelOpsPage, 'selected_model_changed', 'model-ops catalog candidate impact selected-change binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_would_promote', 'model-ops catalog candidate impact cheap-first binding'),
  () => assertIncludes(modelOpsPage, 'reason_codes', 'model-ops catalog candidate impact reason binding'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops catalog candidate impact no-write boundary'),
  () => assertIncludes(modelOpsPage, 'gateway_called', 'model-ops catalog candidate impact gateway boundary'),
  () => assertIncludes(modelOpsPage, 'network_called', 'model-ops catalog candidate impact network boundary'),
  () => assertBefore(modelOpsPage, 'Model catalog candidate impact replay', 'Gateway health plan', 'model-ops catalog candidate impact before gateway health'),
  () => assertIncludes(modelOpsPage, 'Warning drilldown', 'model-ops readiness warning drilldown panel'),
  () => assertIncludes(modelOpsPage, 'readinessWarningRows', 'model-ops readiness warning drilldown row binding'),
  () => assertIncludes(modelOpsPage, 'readinessWarningCategoryRows', 'model-ops readiness warning category binding'),
  () => assertIncludes(modelOpsPage, 'warning_drilldown_count', 'model-ops readiness warning drilldown summary binding'),
  () => assertIncludes(modelOpsPage, 'p0_warning_count', 'model-ops readiness P0 warning binding'),
  () => assertIncludes(modelOpsPage, 'warning_category_counts', 'model-ops readiness warning category counts binding'),
  () => assertIncludes(modelOpsPage, 'validation_hint', 'model-ops readiness warning validation hint binding'),
  () => assertIncludes(modelOpsPage, 'Default recommendation snapshot coverage is required', 'model-ops default recommendation snapshot UI note'),
  () => assertIncludes(modelOpsPage, 'default_recommendation_snapshot', 'model-ops default recommendation snapshot source key UI note'),
  () => assertIncludes(modelOpsApi, 'ModelOpsReadinessWarningDrilldown', 'model-ops readiness warning drilldown type'),
  () => assertIncludes(modelOpsApi, 'warning_drilldown', 'model-ops readiness warning drilldown response binding'),
  () => assertIncludes(modelOpsApi, 'warning_category_counts', 'model-ops readiness warning category response binding'),
  () => assertIncludes(modelOpsApi, 'p1_warning_count', 'model-ops readiness P1 warning summary type'),
  () =>
    assertNotMatches(
      catalogCandidatePatchPlanPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|raw_legal_text)\b/i,
      'model-ops catalog candidate patch plan no secret or raw prompt/payload/output fields',
    ),
  () =>
    assertNotMatches(
      catalogCandidateImpactReplayPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|raw_legal_text|gateway_response|request_body|response_body|headers|candidate_text|generated_text|output_text)\b/i,
      'model-ops catalog candidate impact replay no secret or raw prompt/payload/output fields',
    ),
  () => assertIncludes(modelOpsPage, 'Cheap-first release decision', 'model-ops cheap-first release decision panel'),
  () => assertIncludes(modelOpsPage, 'cheapFirstDecisionChecks', 'model-ops cheap-first decision row binding'),
  () => assertIncludes(modelOpsPage, 'Default change queue', 'model-ops default change queue panel'),
  () => assertIncludes(modelOpsPage, 'defaultChangeQueueRows', 'model-ops default change queue row binding'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops default change queue write boundary'),
  () => assertIncludes(modelOpsPage, 'automatic_default_change_claimed', 'model-ops default change queue auto-change non-claim'),
  () => assertIncludes(modelOpsPage, 'Cheap-first priority queue', 'model-ops cheap-first priority queue panel'),
  () => assertIncludes(modelOpsPage, 'cheapFirstPriorityRows', 'model-ops cheap-first priority queue row binding'),
  () => assertIncludes(modelOpsPage, 'priority_score', 'model-ops cheap-first priority score binding'),
  () => assertIncludes(modelOpsPage, 'priority_label', 'model-ops cheap-first priority label binding'),
  () => assertIncludes(modelOpsPage, 'hundred_update_completion_claimed', 'model-ops cheap-first priority 100-update non-claim'),
  () => assertIncludes(modelOpsPage, 'raw_payloads_included', 'model-ops cheap-first priority raw-payload boundary'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Cheap-first priority queue</h2>',
      'model-ops priority queue follows default queue',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Cheap-first priority queue</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini default change review</h2>',
      'model-ops priority queue precedes default review',
    ),
  () => assertIncludes(modelOpsPage, 'Gemini default change review', 'model-ops Gemini default change review panel'),
  () => assertIncludes(modelOpsPage, 'activeGeminiDefaultChangeReview', 'model-ops Gemini default change active review binding'),
  () => assertIncludes(modelOpsPage, 'geminiDefaultChangeRows', 'model-ops Gemini default change proposal row binding'),
  () => assertIncludes(modelOpsPage, 'defaultGeminiDefaultChangeReviewPayload', 'model-ops Gemini default change template payload'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenGeminiDefaultChangePayloadText', 'model-ops Gemini default change payload guard'),
  () => assertIncludes(modelOpsPage, 'Evaluate proposal', 'model-ops Gemini default change submit button'),
  () => assertIncludes(modelOpsPage, 'cheap-first regressions', 'model-ops Gemini default change cheap-first regression summary'),
  () => assertIncludes(modelOpsPage, 'raw payload echoed', 'model-ops Gemini default change raw payload boundary'),
  () => assertIncludes(modelOpsPage, 'Gemini default cost impact', 'model-ops Gemini default cost impact panel'),
  () => assertIncludes(modelOpsPage, 'activeGeminiDefaultCostImpact', 'model-ops Gemini default cost impact active binding'),
  () => assertIncludes(modelOpsPage, 'geminiDefaultCostRows', 'model-ops Gemini default cost impact row binding'),
  () => assertIncludes(modelOpsPage, 'defaultGeminiDefaultCostImpactPayload', 'model-ops Gemini default cost impact template payload'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenGeminiDefaultCostPayloadText', 'model-ops Gemini default cost impact payload guard'),
  () => assertIncludes(modelOpsPage, 'Evaluate cost impact', 'model-ops Gemini default cost impact submit button'),
  () => assertIncludes(modelOpsPage, 'monthly delta', 'model-ops Gemini default cost impact monthly delta'),
  () => assertIncludes(modelOpsPage, 'estimated savings delta', 'model-ops Gemini default cost impact savings delta'),
  () => assertIncludes(modelOpsPage, 'billing_accuracy_claimed', 'model-ops Gemini default cost impact billing non-claim'),
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
  () => assertIncludes(modelOpsPage, 'Cheap-first canary rollback drill', 'model-ops canary rollback drill panel'),
  () => assertIncludes(modelOpsPage, 'canaryRollbackDrillRows', 'model-ops canary rollback drill row binding'),
  () => assertIncludes(modelOpsPage, 'rollback_drill_items', 'model-ops canary rollback drill item binding'),
  () => assertIncludes(modelOpsPage, 'rollback_drill_policy', 'model-ops canary rollback drill policy panel'),
  () => assertIncludes(modelOpsPage, 'rollback_execution_allowed', 'model-ops canary rollback execution boundary'),
  () => assertIncludes(modelOpsPage, 'rollback_executed', 'model-ops canary rollback non-execution boundary'),
  () => assertIncludes(modelOpsPage, 'drill_record_written', 'model-ops canary rollback no-record boundary'),
  () => assertIncludes(modelOpsPage, 'requires_trigger_review', 'model-ops canary rollback trigger review binding'),
  () => assertIncludes(modelOpsPage, 'requires_holdout_confirmation', 'model-ops canary rollback holdout binding'),
  () => assertIncludes(modelOpsPage, 'trigger_review_status', 'model-ops canary rollback trigger status binding'),
  () => assertIncludes(modelOpsPage, 'rehearsal_steps', 'model-ops canary rollback rehearsal steps binding'),
  () => assertIncludes(modelOpsPage, 'rollback_drill_required', 'model-ops canary rollback required status'),
  () => assertIncludes(modelOpsPage, 'drill_ready', 'model-ops canary rollback ready status'),
  () => assertIncludes(modelOpsPage, 'Cheap-first canary change manifest', 'model-ops canary change manifest panel'),
  () => assertIncludes(modelOpsPage, 'canaryChangeManifestRows', 'model-ops canary change manifest row binding'),
  () => assertIncludes(modelOpsPage, 'change_manifest_items', 'model-ops canary change manifest item binding'),
  () => assertIncludes(modelOpsPage, 'change_manifest_policy', 'model-ops canary change manifest policy panel'),
  () => assertIncludes(modelOpsPage, 'external_change_set', 'model-ops canary change manifest external change-set binding'),
  () => assertIncludes(modelOpsPage, 'prerequisites', 'model-ops canary change manifest prerequisite binding'),
  () => assertIncludes(modelOpsPage, 'operator_steps', 'model-ops canary change manifest operator step binding'),
  () => assertIncludes(modelOpsPage, 'drill_status', 'model-ops canary change manifest rollback drill status binding'),
  () => assertIncludes(modelOpsPage, 'manifest_record_written', 'model-ops canary change manifest no-record boundary'),
  () => assertIncludes(modelOpsPage, 'external_execution_required', 'model-ops canary change manifest manual execution policy'),
  () => assertIncludes(modelOpsPage, 'configuration_write_allowed', 'model-ops canary change manifest config write boundary'),
  () => assertIncludes(modelOpsPage, 'env_file_write_allowed', 'model-ops canary change manifest env write boundary'),
  () => assertIncludes(modelOpsPage, 'change_applied', 'model-ops canary change manifest no-apply boundary'),
  () => assertIncludes(modelOpsPage, 'secret_value_included', 'model-ops canary change manifest secret value boundary'),
  () => assertIncludes(modelOpsPage, 'manifest_ready', 'model-ops canary change manifest ready status'),
  () => assertIncludes(modelOpsPage, 'manifest_blocked', 'model-ops canary change manifest blocked status'),
  () => assertIncludes(modelOpsPage, 'rollback_review_required', 'model-ops canary change manifest rollback review status'),
  () => assertBefore(modelOpsPage, 'Cheap-first canary rollback drill', 'Cheap-first canary change manifest', 'model-ops canary change manifest follows rollback drill'),
  () => assertIncludes(modelOpsPage, 'default_promotion_blocked', 'model-ops cheap-first default promotion boundary'),
  () => assertIncludes(modelOpsPage, 'maintainer_review_required', 'model-ops cheap-first maintainer review boundary'),
  () => assertIncludes(modelOpsPage, 'current_cheap_first_default_allowed', 'model-ops cheap-first current default decision'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed', 'model-ops cheap-first default change decision'),
  () => assertIncludes(modelOpsPage, 'Claim boundary', 'model-ops cheap-first claim boundary panel'),
  () => assertIncludes(modelOpsPage, 'public benchmark scores', 'model-ops cheap-first public benchmark non-claim'),
  () => assertIncludes(modelOpsPage, 'twenty_four_hour_completion_claimed', 'model-ops cheap-first 24h non-claim'),
  () => assertIncludes(modelOpsPage, 'raw model output', 'model-ops cheap-first raw-output privacy boundary'),
  () => assertIncludes(modelOpsPage, 'Official source review', 'model-ops Gemini catalog official source review'),
  () => assertIncludes(modelOpsPage, 'Source freshness', 'model-ops Gemini source freshness table'),
  () => assertIncludes(modelOpsPage, 'catalogSourceReviewRows', 'model-ops Gemini source freshness row binding'),
  () => assertIncludes(modelOpsPage, 'source_review_stale_count', 'model-ops Gemini stale source review summary'),
  () => assertIncludes(modelOpsPage, 'default_promotion_source_block_count', 'model-ops Gemini source default-promotion block summary'),
  () => assertIncludes(modelOpsPage, 'catalogSourceRows', 'model-ops Gemini catalog source row binding'),
  () => assertIncludes(modelOpsPage, 'catalog_source_audit', 'model-ops Gemini catalog source audit response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiOfficialCheapFirstSourceReview', 'model-ops Gemini official cheap-first source review type'),
  () => assertIncludes(modelOpsApi, 'gemini_official_cheap_first_source_review', 'model-ops Gemini official cheap-first source review response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiOfficialCheapFirstSourceReview', 'model-ops Gemini official cheap-first source review API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-official-cheap-first-source-review', 'model-ops Gemini official cheap-first source review endpoint'),
  () => assertIncludes(modelOpsApi, 'comparison_rows', 'model-ops Gemini official cheap-first comparison rows payload guard'),
  () => assertIncludes(modelOpsApi, 'task_default_rows', 'model-ops Gemini official cheap-first task rows payload guard'),
  () => assertIncludes(modelOpsApi, 'largest_output_cost_ratio_vs_flash_lite', 'model-ops Gemini official cheap-first cost ratio guard'),
  () => assertIncludes(modelOpsApi, 'automatic_default_change_claimed', 'model-ops Gemini official cheap-first non-claim guard'),
  () => assertIncludes(modelOpsPage, 'Gemini official cheap-first source review', 'model-ops Gemini official cheap-first source review panel'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialCheapFirstSourceReview', 'model-ops Gemini official cheap-first state binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialCheapFirstComparisonRows', 'model-ops Gemini official cheap-first comparison row binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialCheapFirstTaskRows', 'model-ops Gemini official cheap-first task row binding'),
  () => assertIncludes(modelOpsPage, 'output_cost_ratio_vs_flash_lite', 'model-ops Gemini official cheap-first output ratio binding'),
  () => assertIncludes(modelOpsPage, 'flash_lite_aligned', 'model-ops Gemini official cheap-first default alignment binding'),
  () => assertIncludes(modelOpsPage, 'default_promotion_allowed', 'model-ops Gemini official cheap-first source promotion binding'),
  () => assertIncludes(modelOpsPage, 'network called', 'model-ops Gemini official cheap-first network boundary display'),
  () => assertIncludes(modelOpsPage, 'automatic_default_change_claimed', 'model-ops Gemini official cheap-first automatic-default non-claim display'),
  () =>
    assertBefore(
      modelOpsPage,
      '{data?.catalog_source_audit && (',
      '{(activeGeminiOfficialCheapFirstSourceReview || geminiOfficialCheapFirstSourceReviewError) && (',
      'model-ops Gemini official cheap-first source review follows catalog source audit',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '{(activeGeminiOfficialCheapFirstSourceReview || geminiOfficialCheapFirstSourceReviewError) && (',
      '{(activeGeminiOfficialLifecycleDriftGate || geminiOfficialLifecycleDriftGateError) && (',
      'model-ops Gemini lifecycle drift gate follows cheap-first source review',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '{(activeGeminiOfficialLifecycleDriftGate || geminiOfficialLifecycleDriftGateError) && (',
      '{(activeGeminiOfficialModelFamilyRoadmapEvidence || geminiOfficialModelFamilyRoadmapEvidenceError) && (',
      'model-ops Gemini official roadmap follows lifecycle drift gate',
    ),
  () =>
    assertNotMatches(
      geminiOfficialCheapFirstSourceReviewPanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|email)\b/i,
      'model-ops Gemini official cheap-first source review no secrets or raw request/prompt/output fields',
    ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiOfficialLifecycleDriftGate', 'model-ops Gemini official lifecycle drift gate type'),
  () => assertIncludes(modelOpsApi, 'gemini_official_lifecycle_drift_gate', 'model-ops Gemini official lifecycle drift gate response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiOfficialLifecycleDriftGate', 'model-ops Gemini official lifecycle drift gate API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-official-lifecycle-drift-gate', 'model-ops Gemini official lifecycle drift gate endpoint'),
  () => assertIncludes(modelOpsApi, 'lifecycle_rows', 'model-ops Gemini official lifecycle row payload guard'),
  () => assertIncludes(modelOpsApi, 'default_task_rows', 'model-ops Gemini official lifecycle default row payload guard'),
  () => assertIncludes(modelOpsApi, 'stable_flash_lite_aligned', 'model-ops Gemini official lifecycle cheap-first alignment guard'),
  () => assertIncludes(modelOpsApi, 'blocked_default', 'model-ops Gemini official lifecycle default block guard'),
  () => assertIncludes(modelOpsApi, 'drift_status', 'model-ops Gemini official lifecycle drift status guard'),
  () => assertIncludes(modelOpsPage, 'Gemini official lifecycle drift gate', 'model-ops Gemini official lifecycle drift gate panel'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialLifecycleDriftGate', 'model-ops Gemini official lifecycle state binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialLifecycleDefaultRows', 'model-ops Gemini official lifecycle default row binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialLifecycleRows', 'model-ops Gemini official lifecycle row binding'),
  () => assertIncludes(modelOpsPage, 'stable_flash_lite_aligned', 'model-ops Gemini official lifecycle default alignment display'),
  () => assertIncludes(modelOpsPage, 'blocked_default', 'model-ops Gemini official lifecycle blocked default display'),
  () => assertIncludes(modelOpsPage, 'Official lifecycle sources', 'model-ops Gemini official lifecycle sources panel'),
  () => assertIncludes(modelOpsPage, 'Lifecycle checks', 'model-ops Gemini official lifecycle checks panel'),
  () => assertIncludes(modelOpsPage, 'Lifecycle boundary', 'model-ops Gemini official lifecycle boundary panel'),
  () =>
    assertNotMatches(
      geminiOfficialLifecycleDriftGatePanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|email)\b/i,
      'model-ops Gemini official lifecycle drift gate no secrets or raw request/prompt/output fields',
    ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiOfficialModelFamilyRoadmapEvidence', 'model-ops Gemini official model family roadmap evidence type'),
  () => assertIncludes(modelOpsApi, 'gemini_official_model_family_roadmap_evidence', 'model-ops Gemini official model family roadmap evidence response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiOfficialModelFamilyRoadmapEvidence', 'model-ops Gemini official model family roadmap evidence API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-official-model-family-roadmap-evidence', 'model-ops Gemini official model family roadmap evidence endpoint'),
  () => assertIncludes(modelOpsApi, 'roadmap_items', 'model-ops Gemini official roadmap items payload guard'),
  () => assertIncludes(modelOpsApi, 'cheap_first_evidence_rows', 'model-ops Gemini official cheap-first rows payload guard'),
  () => assertIncludes(modelOpsPage, 'Gemini official model family roadmap evidence', 'model-ops Gemini official roadmap evidence panel'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialModelFamilyRoadmapEvidence', 'model-ops Gemini official roadmap evidence state binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialModelFamilyRows', 'model-ops Gemini official family row binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialRoadmapItems', 'model-ops Gemini official roadmap item binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialCheapFirstEvidenceRows', 'model-ops Gemini official cheap-first evidence row binding'),
  () => assertIncludes(modelOpsPage, 'geminiOfficialRoadmapPrivacyEntries', 'model-ops Gemini official roadmap privacy binding'),
  () => assertIncludes(modelOpsPage, 'Roadmap queue', 'model-ops Gemini official roadmap queue panel'),
  () => assertIncludes(modelOpsPage, 'Cheap-first evidence', 'model-ops Gemini official cheap-first evidence panel'),
  () =>
    assertBefore(
      modelOpsPage,
      '{data?.catalog_source_audit && (',
      '{(activeGeminiOfficialModelFamilyRoadmapEvidence || geminiOfficialModelFamilyRoadmapEvidenceError) && (',
      'model-ops Gemini official roadmap evidence follows catalog source audit',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '{(activeGeminiOfficialModelFamilyRoadmapEvidence || geminiOfficialModelFamilyRoadmapEvidenceError) && (',
      '{catalogCandidatePatchPlan && (',
      'model-ops catalog candidate patch plan follows Gemini official roadmap evidence',
    ),
  () =>
    assertNotMatches(
      geminiOfficialModelFamilyRoadmapEvidencePanel,
      /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|request_body|response_body|headers|email)\b/i,
      'model-ops Gemini official roadmap evidence no secrets or raw request/prompt/output fields',
    ),
  () => assertIncludes(modelOpsPage, 'Prefix compatibility', 'model-ops Gemini prefix compatibility panel'),
  () => assertIncludes(modelOpsPage, 'Observed model review', 'model-ops Gemini observed model review form'),
  () => assertIncludes(modelOpsPage, 'models_response', 'model-ops Gemini model-list response template'),
  () => assertIncludes(modelOpsPage, 'google/gemini-3.5-flash', 'model-ops Gemini 3.5 Flash model-list example'),
  () => assertIncludes(modelOpsPage, 'gemini-3.1-flash-lite', 'model-ops Gemini 3.1 Flash-Lite visible sample'),
  () => assertIncludes(modelOpsPage, 'models/gemini-3.1-pro', 'model-ops Gemini review-only Pro model-list example'),
  () => assertIncludes(modelOpsPage, 'yibu/gemini-3.1-flash-image', 'model-ops Gemini image gateway sample'),
  () => assertIncludes(modelCatalogPanel, 'data?.models ?? []', 'model-ops catalog table data source'),
  () => assertIncludes(modelCatalogPanel, 'model.id', 'model-ops catalog model id binding'),
  () => assertIncludes(modelCatalogPanel, 'model.status', 'model-ops catalog status binding'),
  () => assertIncludes(modelCatalogPanel, 'model.context_window_tokens', 'model-ops catalog context window binding'),
  () => assertIncludes(modelCatalogPanel, 'pricingText(model)', 'model-ops catalog pricing display binding'),
  () => assertIncludes(modelCatalogPanel, 'roleText(model)', 'model-ops catalog role display binding'),
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
  () => assertBefore(modelOpsApi, 'return await fetchModelOpsApi<T>(fetchRequest);', 'client.apiCall.invoke', 'model-ops local/direct fetch before SDK fallback'),
  () => assertIncludes(modelOpsApi, 'ModelOpsPerformanceBudget', 'model-ops performance budget type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstReleaseDecision', 'model-ops cheap-first release decision type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsDefaultChangeQueue', 'model-ops default change queue type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsDefaultChangeQueue', 'model-ops default change queue API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/default-change-queue', 'model-ops default change queue endpoint'),
  () => assertIncludes(modelOpsApi, 'default_change_queue', 'model-ops default change queue response binding'),
  () => assertIncludes(modelOpsApi, 'queue_items', 'model-ops default change queue payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstPriorityQueue', 'model-ops cheap-first priority queue type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstPriorityQueue', 'model-ops cheap-first priority queue API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-priority-queue', 'model-ops cheap-first priority queue endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_priority_queue', 'model-ops cheap-first priority queue response binding'),
  () => assertIncludes(modelOpsApi, 'priority_items', 'model-ops cheap-first priority queue payload guard'),
  () => assertIncludes(modelOpsApi, 'source_review_records', 'model-ops Gemini catalog source freshness type'),
  () => assertIncludes(modelOpsApi, 'source_review_snapshot_as_of', 'model-ops Gemini catalog source snapshot type'),
  () => assertIncludes(modelOpsApi, 'default_promotion_allowed', 'model-ops Gemini catalog source promotion boundary type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiDefaultChangeReview', 'model-ops Gemini default change review type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiDefaultChangeReview', 'model-ops Gemini default change review API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsGeminiDefaultChangeReview', 'model-ops Gemini default change evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-default-change-review', 'model-ops Gemini default change review endpoint'),
  () => assertIncludes(modelOpsApi, 'gemini_default_change_review', 'model-ops Gemini default change response binding'),
  () => assertIncludes(modelOpsApi, 'proposal_rows', 'model-ops Gemini default change payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiDefaultCostImpact', 'model-ops Gemini default cost impact type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsGeminiDefaultCostImpact', 'model-ops Gemini default cost impact API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsGeminiDefaultCostImpact', 'model-ops Gemini default cost impact evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-default-cost-impact', 'model-ops Gemini default cost impact endpoint'),
  () => assertIncludes(modelOpsApi, 'gemini_default_cost_impact', 'model-ops Gemini default cost impact response binding'),
  () => assertIncludes(modelOpsApi, 'impact_rows', 'model-ops Gemini default cost impact payload guard'),
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
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryRollbackDrill', 'model-ops canary rollback drill type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCanaryRollbackDrill', 'model-ops canary rollback drill API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-rollback-drill', 'model-ops canary rollback drill endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_rollback_drill', 'model-ops canary rollback drill response binding'),
  () => assertIncludes(modelOpsApi, 'rollback_drill_items', 'model-ops canary rollback drill payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstCanaryChangeManifest', 'model-ops canary change manifest type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstCanaryChangeManifest', 'model-ops canary change manifest API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-canary-change-manifest', 'model-ops canary change manifest endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_canary_change_manifest', 'model-ops canary change manifest response binding'),
  () => assertIncludes(modelOpsApi, 'change_manifest_items', 'model-ops canary change manifest payload guard'),
  () => assertIncludes(modelOpsApi, 'change_manifest_policy', 'model-ops canary change manifest policy type'),
  () => assertIncludes(modelOpsApi, 'external_change_set', 'model-ops canary change manifest external change-set type'),
  () => assertIncludes(modelOpsApi, 'prerequisites', 'model-ops canary change manifest prerequisite type'),
  () => assertIncludes(modelOpsApi, 'operator_steps', 'model-ops canary change manifest operator step type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstMaintainerExecutionChecklist', 'model-ops maintainer execution checklist type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstMaintainerExecutionChecklist', 'model-ops maintainer execution checklist API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-maintainer-execution-checklist', 'model-ops maintainer execution checklist endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_maintainer_execution_checklist', 'model-ops maintainer execution checklist response binding'),
  () => assertIncludes(modelOpsApi, 'execution_items', 'model-ops maintainer execution checklist payload guard'),
  () => assertIncludes(modelOpsApi, 'execution_policy', 'model-ops maintainer execution checklist policy type'),
  () => assertIncludes(modelOpsApi, 'external_change_allowed', 'model-ops maintainer execution external change type'),
  () => assertIncludes(modelOpsPage, 'Cheap-first maintainer execution checklist', 'model-ops maintainer execution checklist panel'),
  () => assertIncludes(modelOpsPage, 'maintainerExecutionChecklist', 'model-ops maintainer execution checklist state binding'),
  () => assertIncludes(modelOpsPage, 'maintainerExecutionRows', 'model-ops maintainer execution checklist row binding'),
  () => assertIncludes(modelOpsPage, 'execution_policy', 'model-ops maintainer execution checklist policy panel'),
  () => assertIncludes(modelOpsPage, 'external_change_allowed', 'model-ops maintainer execution external change binding'),
  () => assertIncludes(modelOpsPage, 'missing_evidence', 'model-ops maintainer execution missing evidence binding'),
  () => assertIncludes(modelOpsPage, 'operator_action', 'model-ops maintainer execution operator action binding'),
  () => assertBefore(modelOpsPage, 'Cheap-first canary change manifest', 'Cheap-first maintainer execution checklist', 'model-ops maintainer checklist follows change manifest'),
  () => assertBefore(modelOpsPage, 'Cheap-first maintainer execution checklist', 'ModelOps load guard', 'model-ops maintainer checklist before performance budget'),
  () => assertIncludes(modelOpsApi, 'claim_boundary', 'model-ops cheap-first release decision claim boundary type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstReleaseDecision', 'model-ops cheap-first release decision API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-release-decision', 'model-ops cheap-first release decision endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_release_decision', 'model-ops cheap-first release decision response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedReleaseBridge', 'model-ops user-need release bridge type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedReleaseBridgeRow', 'model-ops user-need release bridge row type'),
  () => assertIncludes(modelOpsApi, 'user_need_release_bridge?: ModelOpsUserNeedReleaseBridge', 'model-ops user-need release bridge response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsUserNeedReleaseBridge', 'model-ops user-need release bridge API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/user-need-release-bridge', 'model-ops user-need release bridge endpoint'),
  () => assertIncludes(modelOpsApi, 'bridge_rows', 'model-ops user-need release bridge payload guard'),
  () => assertIncludes(modelOpsPage, 'ModelOps user-need release bridge', 'model-ops user-need release bridge panel'),
  () => assertIncludes(modelOpsPage, 'userNeedReleaseBridge', 'model-ops user-need release bridge state binding'),
  () => assertIncludes(modelOpsPage, 'setUserNeedReleaseBridge(payload.user_need_release_bridge ?? null)', 'model-ops user-need release bridge aggregate binding'),
  () => assertIncludes(modelOpsPage, 'aggregatePayload?.user_need_release_bridge', 'model-ops user-need release bridge fallback request binding'),
  () => assertIncludes(modelOpsPage, 'release_decision_effect', 'model-ops user-need release decision effect binding'),
  () => assertIncludes(modelOpsPage, 'implementation_action_status', 'model-ops user-need implementation action binding'),
  () => assertIncludes(modelOpsPage, 'high_priority_route_protected_count', 'model-ops user-need high-priority route protection binding'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>',
      '<h2 className="text-xl font-black text-stone-950">ModelOps user-need release bridge</h2>',
      'model-ops user-need bridge follows release decision',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">ModelOps user-need release bridge</h2>',
      '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
      'model-ops user-need bridge before default change queue',
    ),
  () =>
    assertNotMatches(
      modelOpsUserNeedReleaseBridgePanel,
      /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|sample_text|raw_legal_text|request_body|response_body|headers|email|phone/i,
      'model-ops user-need release bridge sensitive field guard',
    ),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/performance-budget', 'model-ops performance budget endpoint'),
  () => assertIncludes(modelOpsApi, 'ModelRouteQualityBudget', 'model-ops route quality budget type'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/route-quality-budget', 'model-ops route quality budget endpoint'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstEscalationBudget', 'model-ops cheap-first escalation budget type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsCheapFirstEscalationBudgetRow', 'model-ops cheap-first escalation budget row type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsCheapFirstEscalationBudget', 'model-ops cheap-first escalation budget API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsCheapFirstEscalationBudget', 'model-ops cheap-first escalation budget evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/cheap-first-escalation-budget', 'model-ops cheap-first escalation budget endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_escalation_budget', 'model-ops cheap-first escalation budget response binding'),
  () => assertIncludes(modelOpsApi, 'budget_rows', 'model-ops cheap-first escalation budget payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelFailureUpgradeBudget', 'model-ops model failure upgrade budget type'),
  () => assertIncludes(modelOpsApi, 'ModelFailureUpgradeBudgetPayloadShape', 'model-ops model failure upgrade budget template type'),
  () => assertIncludes(modelOpsApi, 'getModelFailureUpgradeBudget', 'model-ops model failure upgrade budget API'),
  () => assertIncludes(modelOpsApi, 'getModelFailureUpgradeBudgetTemplate', 'model-ops model failure upgrade budget template API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelFailureUpgradeBudget', 'model-ops model failure upgrade budget evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/failure-upgrade-budget', 'model-ops model failure upgrade budget endpoint'),
  () => assertIncludes(modelOpsApi, 'failure_upgrade_budget', 'model-ops model failure upgrade budget response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkRiskBridge', 'model-ops legal benchmark risk bridge type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkRiskBridgeRouteReview', 'model-ops legal benchmark risk bridge route type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalBenchmarkRiskBridge', 'model-ops legal benchmark risk bridge API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-benchmark-risk-bridge', 'model-ops legal benchmark risk bridge endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_benchmark_risk_bridge', 'model-ops legal benchmark risk bridge response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalMicroBenchmarkPreflight', 'model-ops legal micro benchmark preflight type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalMicroBenchmarkPreflightFixtureItem', 'model-ops legal micro benchmark fixture row type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalMicroBenchmarkPreflight', 'model-ops legal micro benchmark preflight API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-micro-benchmark-preflight', 'model-ops legal micro benchmark preflight endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_micro_benchmark_preflight', 'model-ops legal micro benchmark preflight response binding'),
  () => assertIncludes(modelOpsApi, 'fixture_run_items', 'model-ops legal micro benchmark fixture rows payload guard'),
  () => assertIncludes(modelOpsApi, 'document_check_items', 'model-ops legal micro benchmark document rows payload guard'),
  () => assertIncludes(modelOpsApi, 'fact_consistency_items', 'model-ops legal micro benchmark fact rows payload guard'),
  () => assertIncludes(modelOpsApi, 'run_sequence', 'model-ops legal micro benchmark run order payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureCheapFirstBenchmarkGate', 'model-ops legal fixture benchmark gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureCheapFirstDefaultPromotionPacket', 'model-ops legal fixture promotion packet type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureEvidenceHandoffRow', 'model-ops legal fixture evidence handoff row type export'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureEvidenceHandoffCheck', 'model-ops legal fixture evidence handoff check type export'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalFixtureCheapFirstBenchmarkGate', 'model-ops legal fixture benchmark gate API'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalFixtureCheapFirstDefaultPromotionPacket', 'model-ops legal fixture promotion packet API'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff evaluate API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-fixture-cheap-first-benchmark-gate', 'model-ops legal fixture benchmark gate endpoint'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet', 'model-ops legal fixture promotion packet endpoint'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-fixture-evidence-handoff', 'model-ops legal fixture evidence handoff endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_fixture_cheap_first_benchmark_gate', 'model-ops legal fixture benchmark gate response binding'),
  () => assertIncludes(modelOpsApi, 'legal_fixture_cheap_first_default_promotion_packet', 'model-ops legal fixture promotion packet response binding'),
  () => assertIncludes(modelOpsApi, 'legal_fixture_cheap_first_regression_budget', 'model-ops legal fixture regression budget response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalFixtureCheapFirstRegressionBudget', 'model-ops legal fixture regression budget API helper'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionBridge', 'model-ops legal benchmark default-promotion bridge type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionBridgeSourceRow', 'model-ops legal benchmark default-promotion bridge source row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionBridgePromotionRow', 'model-ops legal benchmark default-promotion bridge promotion row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionBridgeCheck', 'model-ops legal benchmark default-promotion bridge check type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalBenchmarkDefaultPromotionBridge', 'model-ops legal benchmark default-promotion bridge API helper'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-benchmark-default-promotion-bridge', 'model-ops legal benchmark default-promotion bridge endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_benchmark_default_promotion_bridge', 'model-ops legal benchmark default-promotion bridge response binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionChecklist', 'model-ops legal benchmark default-promotion checklist type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionChecklistRow', 'model-ops legal benchmark default-promotion checklist row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionChecklistSourceStatusRow', 'model-ops legal benchmark default-promotion checklist source row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionChecklistCheck', 'model-ops legal benchmark default-promotion checklist check type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalBenchmarkDefaultPromotionChecklist', 'model-ops legal benchmark default-promotion checklist API helper'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-benchmark-default-promotion-checklist', 'model-ops legal benchmark default-promotion checklist endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_benchmark_default_promotion_checklist', 'model-ops legal benchmark default-promotion checklist response binding'),
  () => assertIncludes(modelOpsApi, 'checklist_rows?: unknown', 'model-ops legal benchmark default-promotion checklist payload guard'),
  () => assertIncludes(modelOpsApi, 'source_status_rows?: unknown', 'model-ops legal benchmark default-promotion checklist source payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionSignoffPacket', 'model-ops legal benchmark default-promotion signoff packet type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketRow', 'model-ops legal benchmark default-promotion signoff packet row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketSourceStatusRow', 'model-ops legal benchmark default-promotion signoff packet source row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketCheck', 'model-ops legal benchmark default-promotion signoff packet check type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalBenchmarkDefaultPromotionSignoffPacket', 'model-ops legal benchmark default-promotion signoff packet API helper'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet', 'model-ops legal benchmark default-promotion signoff packet endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_benchmark_default_promotion_signoff_packet', 'model-ops legal benchmark default-promotion signoff packet response binding'),
  () => assertIncludes(modelOpsApi, 'signoff_items?: unknown', 'model-ops legal benchmark default-promotion signoff packet payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoff', 'model-ops legal benchmark default-promotion execution handoff type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffRow', 'model-ops legal benchmark default-promotion execution handoff row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffSourceStatusRow', 'model-ops legal benchmark default-promotion execution handoff source row type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffRollbackGateItem', 'model-ops legal benchmark default-promotion execution handoff rollback gate type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffCheck', 'model-ops legal benchmark default-promotion execution handoff check type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsLegalBenchmarkDefaultPromotionExecutionHandoff', 'model-ops legal benchmark default-promotion execution handoff API helper'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsLegalBenchmarkDefaultPromotionExecutionHandoff', 'model-ops legal benchmark default-promotion execution handoff evaluation helper'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff', 'model-ops legal benchmark default-promotion execution handoff endpoint'),
  () => assertIncludes(modelOpsApi, 'legal_benchmark_default_promotion_execution_handoff', 'model-ops legal benchmark default-promotion execution handoff response binding'),
  () => assertIncludes(modelOpsApi, 'rollback_gate_items?: unknown', 'model-ops legal benchmark default-promotion execution handoff payload guard'),
  () => assertIncludes(modelOpsPage, 'Legal fixture cheap-first regression budget', 'model-ops legal fixture regression budget panel'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_budget', 'model-ops legal fixture regression budget default-change boundary'),
  () => assertIncludes(modelOpsPage, 'source_regression_status', 'model-ops legal fixture regression budget source status summary'),
  () => assertIncludes(modelOpsPage, 'Legal benchmark default-promotion bridge', 'model-ops legal benchmark default-promotion bridge panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalBenchmarkDefaultPromotionBridge', 'model-ops legal benchmark default-promotion bridge active binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionSourceRows', 'model-ops legal benchmark default-promotion bridge source rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionRows', 'model-ops legal benchmark default-promotion bridge promotion rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionChecks', 'model-ops legal benchmark default-promotion bridge checks'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_bridge', 'model-ops legal benchmark default-promotion bridge default-change boundary'),
  () => assertIncludes(modelOpsPage, 'source_gemini_lifecycle_status', 'model-ops legal benchmark default-promotion bridge lifecycle source status'),
  () => assertIncludes(modelOpsPage, 'blocked_default_count', 'model-ops legal benchmark default-promotion bridge blocked lifecycle count'),
  () => assertIncludes(modelOpsPage, 'Legal benchmark default-promotion checklist', 'model-ops legal benchmark default-promotion checklist panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalBenchmarkDefaultPromotionChecklist', 'model-ops legal benchmark default-promotion checklist active binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionChecklistRows', 'model-ops legal benchmark default-promotion checklist rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionChecklistSourceRows', 'model-ops legal benchmark default-promotion checklist source rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionChecklistChecks', 'model-ops legal benchmark default-promotion checklist checks'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_checklist', 'model-ops legal benchmark default-promotion checklist default-change boundary'),
  () => assertIncludes(modelOpsPage, 'required_signoffs', 'model-ops legal benchmark default-promotion checklist signoff binding'),
  () => assertIncludes(modelOpsPage, 'Legal benchmark default-promotion signoff packet', 'model-ops legal benchmark default-promotion signoff packet panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalBenchmarkDefaultPromotionSignoffPacket', 'model-ops legal benchmark default-promotion signoff packet active binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionSignoffPacketRows', 'model-ops legal benchmark default-promotion signoff packet rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionSignoffPacketSourceRows', 'model-ops legal benchmark default-promotion signoff packet source rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionSignoffPacketChecks', 'model-ops legal benchmark default-promotion signoff packet checks'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_signoff_packet', 'model-ops legal benchmark default-promotion signoff packet default-change boundary'),
  () => assertIncludes(modelOpsPage, 'pre_signoff_checks', 'model-ops legal benchmark default-promotion signoff packet pre-check binding'),
  () => assertIncludes(modelOpsPage, 'Legal benchmark default-promotion execution handoff / rollback gate', 'model-ops legal benchmark default-promotion execution handoff panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalBenchmarkDefaultPromotionExecutionHandoff', 'model-ops legal benchmark default-promotion execution handoff active binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionExecutionHandoffRows', 'model-ops legal benchmark default-promotion execution handoff rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionExecutionHandoffRollbackGateRows', 'model-ops legal benchmark default-promotion execution rollback rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionExecutionHandoffSourceRows', 'model-ops legal benchmark default-promotion execution source rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkDefaultPromotionExecutionHandoffChecks', 'model-ops legal benchmark default-promotion execution checks'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_execution_handoff', 'model-ops legal benchmark default-promotion execution default-change boundary'),
  () => assertIncludes(modelOpsPage, 'rollback_execution_allowed', 'model-ops legal benchmark default-promotion execution rollback allowed boundary'),
  () => assertIncludes(modelOpsPage, 'rollback_executed', 'model-ops legal benchmark default-promotion execution rollback executed boundary'),
  () => assertIncludes(modelOpsPage, 'traffic_shifted', 'model-ops legal benchmark default-promotion execution traffic boundary'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops legal benchmark default-promotion execution config boundary'),
  () => assertIncludes(modelOpsApi, 'legal_fixture_evidence_handoff?: ModelOpsLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff response binding'),
  () => assertIncludes(modelOpsApi, 'gate_rows', 'model-ops legal fixture benchmark gate payload guard'),
  () => assertIncludes(modelOpsApi, 'handoff_rows?: unknown', 'model-ops legal fixture evidence handoff payload guard'),
  () => assertIncludes(modelOpsApi, 'handoff_evidence_summary?: unknown', 'model-ops legal fixture evidence handoff source payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsLegalFixtureCheapFirstBenchmarkGateRow', 'model-ops legal fixture benchmark gate row type export'),
  () => assertIncludes(modelOpsPage, 'Model failure upgrade budget', 'model-ops model failure upgrade budget panel'),
  () => assertIncludes(modelOpsPage, 'activeFailureUpgradeBudget', 'model-ops model failure upgrade budget state binding'),
  () => assertIncludes(modelOpsPage, 'failureUpgradeChecks', 'model-ops model failure upgrade budget check binding'),
  () => assertIncludes(modelOpsPage, 'attempt_budget_remaining', 'model-ops model failure upgrade budget attempt binding'),
  () => assertIncludes(modelOpsPage, 'incremental_cost_usd', 'model-ops model failure upgrade budget cost binding'),
  () => assertIncludes(modelOpsPage, 'premium_quota_allowed', 'model-ops model failure upgrade budget premium quota binding'),
  () => assertIncludes(modelOpsPage, 'operator_approved', 'model-ops model failure upgrade budget approval binding'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenFailureUpgradePayloadText', 'model-ops model failure upgrade budget payload guard'),
  () => assertIncludes(modelOpsPage, 'Evaluate failure upgrade budget', 'model-ops model failure upgrade budget submit button'),
  () => assertIncludes(modelOpsPage, 'Legal micro benchmark preflight', 'model-ops legal micro benchmark preflight panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalMicroBenchmarkPreflight', 'model-ops legal micro benchmark active binding'),
  () => assertIncludes(modelOpsPage, 'legalMicroFixtureRows', 'model-ops legal micro benchmark fixture rows'),
  () => assertIncludes(modelOpsPage, 'legalMicroDocumentRows', 'model-ops legal micro benchmark document rows'),
  () => assertIncludes(modelOpsPage, 'legalMicroFactRows', 'model-ops legal micro benchmark fact rows'),
  () => assertIncludes(modelOpsPage, 'legalMicroRunSteps', 'model-ops legal micro benchmark run order rows'),
  () => assertIncludes(modelOpsPage, 'max_parallel_requests', 'model-ops legal micro benchmark serial cap binding'),
  () => assertIncludes(modelOpsPage, 'benchmark_gate_required', 'model-ops legal micro benchmark gate binding'),
  () => assertIncludes(modelOpsPage, 'Legal fixture cheap-first benchmark gate', 'model-ops legal fixture benchmark gate panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalFixtureCheapFirstBenchmarkGate', 'model-ops legal fixture benchmark gate active binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureBenchmarkGateRows', 'model-ops legal fixture benchmark gate row binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureBenchmarkDocumentRows', 'model-ops legal fixture benchmark document row binding'),
  () => assertIncludes(modelOpsPage, 'linked_calibration_task_count', 'model-ops legal fixture linked calibration count binding'),
  () => assertIncludes(modelOpsPage, 'linked_calibration_task_ids', 'model-ops legal fixture linked calibration row binding'),
  () => assertIncludes(modelOpsPage, 'calibration_decisions', 'model-ops legal fixture calibration decision binding'),
  () => assertIncludes(modelOpsPage, 'Legal fixture cheap-first default promotion packet', 'model-ops legal fixture promotion packet panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalFixtureCheapFirstDefaultPromotionPacket', 'model-ops legal fixture promotion packet active binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureDefaultPromotionRows', 'model-ops legal fixture promotion packet row binding'),
  () => assertIncludes(modelOpsPage, 'default_change_allowed_by_packet', 'model-ops legal fixture promotion packet decision binding'),
  () => assertIncludes(modelOpsPage, 'requires_cheap_first_calibration_pass', 'model-ops legal fixture calibration requirement binding'),
  () => assertIncludes(modelOpsPage, 'Legal fixture evidence handoff', 'model-ops legal fixture evidence handoff panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalFixtureEvidenceHandoff', 'model-ops legal fixture evidence handoff active binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureEvidenceHandoffRows', 'model-ops legal fixture evidence handoff rows binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureEvidenceHandoffChecks', 'model-ops legal fixture evidence handoff checks binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureEvidenceHandoffMetrics', 'model-ops legal fixture evidence handoff metric binding'),
  () => assertIncludes(modelOpsPage, 'legalFixtureEvidenceHandoffUiRows', 'model-ops legal fixture evidence handoff safe row projection'),
  () => assertIncludes(modelOpsPage, 'raw_input_field_count', 'model-ops legal fixture evidence handoff input boundary binding'),
  () => assertIncludes(modelOpsPage, 'completion_claimed', 'model-ops legal fixture evidence handoff completion claim binding'),
  () => assertIncludes(modelOpsPage, 'ModelOps legal benchmark risk bridge', 'model-ops legal benchmark risk bridge panel'),
  () => assertIncludes(modelOpsPage, 'activeLegalBenchmarkRiskBridge', 'model-ops legal benchmark risk bridge active binding'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkRiskRouteReviews', 'model-ops legal benchmark risk bridge route rows'),
  () => assertIncludes(modelOpsPage, 'legalBenchmarkRiskUserNeedReviews', 'model-ops legal benchmark risk bridge user need rows'),
  () => assertIncludes(modelOpsPage, 'new_default_promotion_allowed', 'model-ops legal benchmark risk bridge default promotion policy'),
  () => assertIncludes(modelOpsPage, 'premium_exception_required', 'model-ops legal benchmark risk bridge premium exception binding'),
  () => assertIncludes(modelOpsPage, 'benchmark_license_watch_count', 'model-ops legal benchmark risk bridge license watch binding'),
  () => assertIncludes(modelOpsPage, 'dataset_downloaded', 'model-ops legal benchmark risk bridge dataset boundary'),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first regression budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion bridge</h2>',
    'model-ops legal benchmark default-promotion bridge follows regression budget',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion bridge</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion checklist</h2>',
    'model-ops legal benchmark default-promotion checklist follows bridge',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion checklist</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion signoff packet</h2>',
    'model-ops legal benchmark default-promotion signoff packet follows checklist',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion signoff packet</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion execution handoff / rollback gate</h2>',
    'model-ops legal benchmark default-promotion execution handoff follows signoff packet',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion execution handoff / rollback gate</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
    'model-ops legal benchmark default-promotion execution handoff precedes evidence handoff',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Cheap-first quality budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Model failure upgrade budget</h2>',
    'model-ops failure upgrade budget follows quality budget',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Model failure upgrade budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
    'model-ops failure upgrade budget precedes escalation budget',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Model failure upgrade budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal micro benchmark preflight</h2>',
    'model-ops legal micro benchmark preflight follows failure budget',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal micro benchmark preflight</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first benchmark gate</h2>',
    'model-ops legal fixture gate follows legal micro benchmark preflight',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first benchmark gate</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first default promotion packet</h2>',
    'model-ops legal fixture promotion packet follows fixture gate',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first default promotion packet</h2>',
    '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
    'model-ops legal fixture evidence handoff follows fixture promotion packet',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
    '<h2 className="text-xl font-black text-stone-950">ModelOps legal benchmark risk bridge</h2>',
    'model-ops legal benchmark bridge follows legal fixture evidence handoff',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">ModelOps legal benchmark risk bridge</h2>',
    '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
    'model-ops legal benchmark bridge precedes escalation budget',
  ),
  () => assertIncludes(modelOpsPage, 'Cheap-first escalation budget', 'model-ops cheap-first escalation budget panel'),
  () => assertIncludes(modelOpsPage, 'activeEscalationBudget', 'model-ops cheap-first escalation budget state binding'),
  () => assertIncludes(modelOpsPage, 'escalationBudgetRows', 'model-ops cheap-first escalation budget row binding'),
  () => assertIncludes(modelOpsPage, 'wasted_escalation_cost_ratio', 'model-ops cheap-first escalation wasted cost binding'),
  () => assertIncludes(modelOpsPage, 'premium_review_coverage', 'model-ops cheap-first escalation premium review binding'),
  () => assertIncludes(modelOpsPage, 'hasForbiddenEscalationBudgetPayloadText', 'model-ops cheap-first escalation payload guard'),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Cheap-first quality budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
    'model-ops escalation budget follows quality budget',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
    '<h2 className="text-xl font-black text-stone-950">Default optimization</h2>',
    'model-ops escalation budget precedes default optimization',
  ),
  () => assertIncludes(modelOpsApi, 'GeminiVariantMatrix', 'model-ops Gemini variant matrix type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiModelIntakeQueue', 'model-ops observed Gemini intake queue type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiPromotionSafetyCheck', 'model-ops observed Gemini intake safety check type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGeminiIntakeRunbookStep', 'model-ops observed Gemini intake runbook step type'),
  () => assertIncludes(modelOpsApi, 'promotion_safety_checks: ModelOpsObservedGeminiPromotionSafetyCheck[]', 'model-ops observed Gemini intake safety checks response type'),
  () => assertIncludes(modelOpsApi, 'intake_runbook_steps: ModelOpsObservedGeminiIntakeRunbookStep[]', 'model-ops observed Gemini intake runbook response type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsObservedGeminiModelIntakeQueue', 'model-ops observed Gemini intake queue API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsObservedGeminiModelIntakeQueue', 'model-ops observed Gemini intake queue evaluation API'),
  () => assertIncludes(modelOpsApi, 'observed_gemini_model_intake_queue', 'model-ops observed Gemini intake queue response binding'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/observed-gemini-model-intake-queue', 'model-ops observed Gemini intake queue endpoint'),
  () => assertIncludes(modelOpsApi, 'GeminiNewApiAliasCapabilityCoverage', 'model-ops Gemini/NewAPI alias capability coverage type'),
  () => assertIncludes(modelOpsApi, 'observed_model_extractor_version', 'model-ops Gemini/NewAPI alias observed extractor summary type'),
  () => assertIncludes(modelOpsApi, 'source_summaries?:', 'model-ops Gemini/NewAPI alias source summaries type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway model fit matrix type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsObservedGatewayModelFitTaskRow', 'model-ops observed gateway task fit row type'),
  () => assertIncludes(modelOpsApi, 'getModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway fit matrix API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsObservedGatewayModelFitMatrix', 'model-ops observed gateway fit matrix evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/observed-gateway-model-fit-matrix', 'model-ops observed gateway fit matrix endpoint'),
  () => assertIncludes(modelOpsApi, 'observed_gateway_model_fit_matrix', 'model-ops observed gateway fit matrix response binding'),
  () => assertIncludes(modelOpsApi, 'LOCAL_MODEL_OPS_BACKEND_ORIGIN', 'model-ops local backend direct fallback origin'),
  () => assertIncludes(modelOpsApi, 'localModelOpsBackendRequest', 'model-ops local backend direct fallback request'),
  () => assertIncludes(modelOpsApi, "import.meta.env.DEV && ['127.0.0.1', 'localhost'].includes(window.location.hostname)", 'model-ops local-only direct fallback guard'),
  () => assertIncludes(modelOpsApi, 'GeminiNewApiAliasCapabilityCoverageRow', 'model-ops Gemini/NewAPI alias capability row type'),
  () => assertIncludes(modelOpsApi, "id: 'gemini-newapi-alias-capability-coverage' | string", 'model-ops Gemini/NewAPI alias capability typed id'),
  () => assertIncludes(modelOpsApi, 'gemini_newapi_alias_capability_coverage', 'model-ops Gemini/NewAPI alias capability response binding'),
  () => assertIncludes(modelOpsApi, 'getGeminiNewApiAliasCapabilityCoverage', 'model-ops Gemini/NewAPI alias capability API'),
  () => assertIncludes(modelOpsApi, 'evaluateGeminiNewApiAliasCapabilityCoverage', 'model-ops Gemini/NewAPI alias capability evaluate API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-newapi-alias-capability-coverage', 'model-ops Gemini/NewAPI alias capability endpoint'),
  () => assertIncludes(modelOpsApi, 'task_alias_coverage', 'model-ops Gemini/NewAPI alias capability task coverage payload guard'),
  () => assertIncludes(modelOpsApi, 'accepted_alias_shapes', 'model-ops Gemini/NewAPI alias capability accepted shape payload guard'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedGeminiRouteCoverage', 'model-ops user-need Gemini route coverage type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedGeminiRouteCoverageRow', 'model-ops user-need Gemini route coverage row type'),
  () => assertIncludes(modelOpsApi, 'user_need_gemini_route_coverage', 'model-ops user-need Gemini route coverage response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsUserNeedGeminiRouteCoverage', 'model-ops user-need Gemini route coverage API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/user-need-gemini-route-coverage', 'model-ops user-need Gemini route coverage endpoint'),
  () => assertIncludes(modelOpsPage, 'ModelOps user-need Gemini route coverage', 'model-ops user-need Gemini route coverage panel'),
  () => assertIncludes(modelOpsPage, 'activeUserNeedGeminiRouteCoverage', 'model-ops user-need Gemini route coverage active binding'),
  () => assertIncludes(modelOpsPage, 'userNeedGeminiRouteCoverageRows', 'model-ops user-need Gemini route coverage row binding'),
  () => assertIncludes(modelOpsPage, 'high_priority_route_protected_count', 'model-ops user-need Gemini high-priority route protection summary'),
  () => assertIncludes(modelOpsPage, 'row.route_task_source', 'model-ops user-need Gemini route source binding'),
  () => assertIncludes(modelOpsPage, 'row.linked_route_tasks', 'model-ops user-need Gemini linked route tasks display'),
  () => assertIncludes(modelOpsPage, 'row.linked_default_models', 'model-ops user-need Gemini linked default models display'),
  () => assertIncludes(modelOpsPage, 'row.review_reason_codes', 'model-ops user-need Gemini review reasons display'),
  () => assertIncludes(modelOpsPage, 'changes_default_routes', 'model-ops user-need Gemini no default route change binding'),
  () => assertIncludes(modelOpsPage, 'claims_default_route_changed', 'model-ops user-need Gemini claim boundary binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedCheapFirstHandoff', 'model-ops user-need cheap-first handoff type'),
  () => assertIncludes(modelOpsApi, 'ModelOpsUserNeedCheapFirstHandoffRow', 'model-ops user-need cheap-first handoff row type'),
  () => assertIncludes(modelOpsApi, 'user_need_cheap_first_handoff', 'model-ops user-need cheap-first handoff response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsUserNeedCheapFirstHandoff', 'model-ops user-need cheap-first handoff API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/user-need-cheap-first-handoff', 'model-ops user-need cheap-first handoff endpoint'),
  () => assertIncludes(modelOpsApi, 'cheap_first_route_protected', 'model-ops user-need cheap-first protected flag binding'),
  () => assertIncludes(modelOpsApi, 'reviewer_action', 'model-ops user-need cheap-first reviewer action binding'),
  () => assertIncludes(modelOpsPage, 'ModelOps user-need cheap-first handoff', 'model-ops user-need cheap-first handoff panel'),
  () => assertIncludes(modelOpsPage, 'activeUserNeedCheapFirstHandoff', 'model-ops user-need cheap-first handoff active binding'),
  () => assertIncludes(modelOpsPage, 'userNeedCheapFirstHandoffRows', 'model-ops user-need cheap-first handoff row binding'),
  () => assertIncludes(modelOpsPage, 'userNeedCheapFirstHandoffSections', 'model-ops user-need cheap-first handoff section binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_route_protected_need_count', 'model-ops user-need cheap-first protected summary binding'),
  () => assertIncludes(modelOpsPage, 'row.cheap_first_route_protected', 'model-ops user-need cheap-first row protected binding'),
  () => assertIncludes(modelOpsPage, 'row.reviewer_action', 'model-ops user-need cheap-first reviewer action display'),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">ModelOps user-need release bridge</h2>',
    '<h2 className="text-xl font-black text-stone-950">ModelOps user-need Gemini route coverage</h2>',
    'model-ops release bridge precedes user-need Gemini route coverage',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">ModelOps user-need Gemini route coverage</h2>',
    '<h2 className="text-xl font-black text-stone-950">ModelOps user-need cheap-first handoff</h2>',
    'model-ops user-need Gemini route coverage precedes user-need handoff',
  ),
  () => assertBefore(
    modelOpsPage,
    '<h2 className="text-xl font-black text-stone-950">ModelOps user-need cheap-first handoff</h2>',
    '<h2 className="text-xl font-black text-stone-950">Default change queue</h2>',
    'model-ops user-need handoff precedes default change queue',
  ),
  () => assertIncludes(modelOpsPage, 'Gemini/NewAPI alias capability coverage', 'model-ops Gemini/NewAPI alias capability panel'),
  () => assertIncludes(modelOpsPage, 'Observed gateway model fit matrix', 'model-ops observed gateway fit matrix panel'),
  () => assertIncludes(modelOpsPage, 'Gemini/NewAPI cheap-first route coverage bridge', 'model-ops observed gateway bridge panel'),
  () => assertIncludes(modelOpsPage, 'observedGatewayModelFitMatrix', 'model-ops observed gateway fit matrix state binding'),
  () => assertIncludes(modelOpsPage, 'geminiNewApiRouteCoverageBridgeRows', 'model-ops observed gateway bridge rows binding'),
  () => assertIncludes(modelOpsPage, 'observedGatewayFitTaskRows', 'model-ops observed gateway task rows binding'),
  () => assertIncludes(modelOpsPage, 'observedGatewayFitModelRows', 'model-ops observed gateway model rows binding'),
  () => assertIncludes(modelOpsPage, 'alias_count', 'model-ops observed gateway bridge alias count binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_aligned', 'model-ops observed gateway bridge cheap-first binding'),
  () => assertIncludes(modelOpsPage, 'default_allowed_without_review', 'model-ops observed gateway bridge default boundary binding'),
  () => assertIncludes(modelOpsPage, 'uses_runtime_router', 'model-ops observed gateway bridge runtime router binding'),
  () => assertIncludes(modelOpsPage, 'returns_route_payloads', 'model-ops observed gateway bridge route payload binding'),
  () => assertIncludes(modelOpsPage, 'route_gap_reason_codes', 'model-ops observed gateway bridge gap code binding'),
  () => assertIncludes(modelOpsApi, 'ModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit gate type'),
  () => assertIncludes(modelOpsApi, 'runtime_explicit_model_fit_gate', 'model-ops runtime explicit model fit response binding'),
  () => assertIncludes(modelOpsApi, 'getModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit API'),
  () => assertIncludes(modelOpsApi, 'evaluateModelOpsRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit evaluation API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/runtime-explicit-model-fit-gate', 'model-ops runtime explicit model fit endpoint'),
  () => assertIncludes(modelOpsPage, 'Runtime explicit model fit gate', 'model-ops runtime explicit model fit panel'),
  () => assertIncludes(modelOpsPage, 'activeRuntimeExplicitModelFitGate', 'model-ops runtime explicit model fit active binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitRows', 'model-ops runtime explicit model fit row binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitChecks', 'model-ops runtime explicit model fit checks binding'),
  () => assertIncludes(modelOpsPage, 'runtimeExplicitModelFitPolicyEntries', 'model-ops runtime explicit model fit policy binding'),
  () => assertIncludes(modelOpsPage, 'unknown_gateway_passthrough', 'model-ops runtime explicit unknown gateway binding'),
  () => assertIncludes(modelOpsPage, 'explicit_over_budget_allowed', 'model-ops runtime explicit over-budget binding'),
  () => assertIncludes(modelOpsPage, 'cheap_first_aligned', 'model-ops runtime explicit cheap-first binding'),
  () => assertIncludes(modelOpsPage, 'runtime_behavior_changed', 'model-ops runtime explicit behavior boundary binding'),
  () => assertIncludes(modelOpsPage, 'geminiAliasCapabilityCoverage', 'model-ops Gemini/NewAPI alias capability state binding'),
  () => assertIncludes(modelOpsPage, 'geminiAliasCapabilityRows', 'model-ops Gemini/NewAPI alias capability row binding'),
  () => assertIncludes(modelOpsPage, 'geminiAliasTaskCoverageRows', 'model-ops Gemini/NewAPI alias task coverage binding'),
  () => assertIncludes(modelOpsPage, 'high_frequency_default_allowed', 'model-ops Gemini/NewAPI alias high-frequency flag binding'),
  () => assertIncludes(modelOpsPage, 'premium_or_media_review_required', 'model-ops Gemini/NewAPI alias premium/media review binding'),
  () => assertIncludes(modelOpsPage, 'configuration_written', 'model-ops Gemini/NewAPI alias no-write binding'),
  () => assertIncludes(modelOpsPage, 'accepted_alias_shapes.slice(0, 10)', 'model-ops Gemini/NewAPI accepted alias display cap'),
  () => assertIncludes(modelOpsPage, 'coverage_rows ?? []', 'model-ops Gemini/NewAPI alias coverage rows binding'),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini variant matrix</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
      'model-ops alias capability follows variant matrix',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini/NewAPI alias capability coverage</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
      'model-ops alias capability before cheap-first gate',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first route preflight</h2>',
      '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
      'model-ops observed gateway fit matrix follows route preflight',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
      '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
      'model-ops runtime explicit model fit gate follows observed gateway fit matrix',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub endpoint route coverage gate</h2>',
      'model-ops observed gateway fit matrix before AIHub endpoint coverage',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">AIHub endpoint route coverage gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub media/speech default catalog gate</h2>',
      'model-ops AIHub media/speech default catalog follows AIHub endpoint coverage',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">AIHub media/speech default catalog gate</h2>',
      '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
      'model-ops Gemini embedding preflight follows AIHub media/speech default catalog',
    ),
  () =>
    assertBefore(
      modelOpsPage,
      '<h2 className="text-xl font-black text-stone-950">Gemini embedding cheap-first preflight</h2>',
      '<h2 className="text-xl font-black text-stone-950">AIHub gentxt routing guard</h2>',
      'model-ops gentxt routing guard follows Gemini embedding preflight',
    ),
  () => assertIncludes(modelOpsApi, 'ModelOpsGeminiCheapFirstCoverageGate', 'model-ops Gemini cheap-first coverage gate type'),
  () => assertIncludes(modelOpsApi, "id: 'modelops-gemini-cheap-first-coverage-gate' | string", 'model-ops Gemini cheap-first coverage gate typed id'),
  () => assertIncludes(modelOpsApi, 'gemini_cheap_first_coverage_gate', 'model-ops Gemini cheap-first coverage response binding'),
  () => assertIncludes(modelOpsApi, 'coverage_rows', 'model-ops Gemini cheap-first coverage payload guard'),
  () => assertIncludes(modelOpsApi, 'getGeminiCheapFirstCoverageGate', 'model-ops Gemini cheap-first coverage API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/gemini-cheap-first-coverage-gate', 'model-ops Gemini cheap-first coverage endpoint'),
  () => assertIncludes(modelOpsPage, 'Default template alignment', 'model-ops default template alignment panel'),
  () => assertIncludes(modelOpsPage, 'defaultTemplateRows', 'model-ops default template row binding'),
  () => assertIncludes(modelOpsPage, 'APP_AI_AGENTIC_MODEL / APP_AI_GROUNDED_RESEARCH_MODEL', 'model-ops agentic grounded template visibility'),
  () => assertIncludes(modelOpsPage, 'auto-agentic / auto-grounded-research', 'model-ops agentic grounded alias visibility'),
  () => assertIncludes(modelOpsPage, 'agentic_grounded_defaults_visible', 'model-ops agentic grounded default summary binding'),
  () => assertIncludes(modelOpsPage, 'data.default_template_audit.validation_commands', 'model-ops default template validation binding'),
  () => assertIncludes(modelOpsApi, 'ModelDefaultTemplateAudit', 'model-ops default template audit type'),
  () => assertIncludes(modelOpsApi, 'default_template_audit', 'model-ops default template audit response binding'),
  () => assertIncludes(modelOpsApi, 'default_targets', 'model-ops default template target type and payload guard'),
  () => assertIncludes(modelOpsApi, 'getModelDefaultTemplateAudit', 'model-ops default template audit API'),
  () => assertIncludes(modelOpsApi, '/api/v1/aihub/models/default-template-audit', 'model-ops default template audit endpoint'),
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

const retrievalDiagnosticsPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval diagnostics gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval observation gate</h2>',
  'maintenance Legal RAG retrieval diagnostics section',
);
const legalRagIndexCoveragePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG index coverage gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding readiness gate</h2>',
  'maintenance Legal RAG index coverage section',
);
const legalRagEmbeddingReadinessPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding readiness gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding chunk policy gate</h2>',
  'maintenance Legal RAG embedding readiness section',
);
const legalRagEmbeddingChunkPolicyPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding chunk policy gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index dry-run gate</h2>',
  'maintenance Legal RAG embedding chunk policy section',
);
const legalRagEmbeddingIndexDryRunPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index dry-run gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch budget gate</h2>',
  'maintenance Legal RAG embedding index dry-run section',
);
const legalRagEmbeddingBatchBudgetPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch budget gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch approval packet</h2>',
  'maintenance Legal RAG embedding batch budget section',
);
const legalRagEmbeddingBatchApprovalPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch approval packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch observation gate</h2>',
  'maintenance Legal RAG embedding batch approval section',
);
const legalRagEmbeddingBatchObservationPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding batch observation gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index commit review packet</h2>',
  'maintenance Legal RAG embedding batch observation section',
);
const legalRagEmbeddingIndexCommitReviewPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index commit review packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index post-commit verification gate</h2>',
  'maintenance Legal RAG embedding index commit review section',
);
const legalRagEmbeddingIndexPostCommitVerificationPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding index post-commit verification gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding retrieval diagnostics handoff gate</h2>',
  'maintenance Legal RAG embedding index post-commit verification section',
);
const legalRagEmbeddingRetrievalDiagnosticsHandoffPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG embedding retrieval diagnostics handoff gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval diagnostics gate</h2>',
  'maintenance Legal RAG embedding retrieval diagnostics handoff section',
);
const retrievalObservationPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG retrieval observation gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG answer release readiness gate</h2>',
  'maintenance Legal RAG retrieval observation section',
);
const legalRagAnswerReleaseReadinessPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal RAG answer release readiness gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG benchmark alignment scorecard</h2>',
  'maintenance Legal RAG answer release readiness section',
);
const finalDocumentDeliveryReleaseGatePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Final document delivery release gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Small legal document benchmark runbook evidence</h2>',
  'maintenance final document delivery release gate section',
);
const smallLegalDocumentBenchmarkRunbookEvidencePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Small legal document benchmark runbook evidence</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal RAG hallucination triage gate</h2>',
  'maintenance small legal document benchmark runbook evidence section',
);
const feedbackLifecyclePolicyPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Feedback lifecycle policy</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal review benchmark</h2>',
  'maintenance feedback lifecycle policy section',
);
const feedbackUserNeedLegalDocumentBenchmarkBacklogPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark backlog</h2>',
  '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark release packet</h2>',
  'maintenance feedback user-need legal-document benchmark backlog section',
);
const feedbackUserNeedLegalDocumentBenchmarkReleasePacketPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Feedback user-need legal-document benchmark release packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Feedback lifecycle policy</h2>',
  'maintenance feedback user-need legal-document benchmark release packet section',
);
const geminiCheapFirstCoveragePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first coverage gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first route preflight</h2>',
  'model-ops Gemini cheap-first coverage gate section',
);
const geminiCheapFirstRoutePreflightPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini cheap-first route preflight</h2>',
  '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
  'model-ops Gemini cheap-first route preflight section',
);
const observedGatewayModelFitMatrixPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Observed gateway model fit matrix</h2>',
  '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
  'model-ops observed gateway model fit matrix section',
);
const runtimeExplicitModelFitGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Runtime explicit model fit gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">AIHub endpoint route coverage gate</h2>',
  'model-ops runtime explicit model fit gate section',
);
const defaultTemplateAlignmentPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Default template alignment</h2>',
  'Runtime router',
  'model-ops default template alignment section',
);
const observedGeminiModelIntakePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Observed Gemini model intake queue</h2>',
  'Gemini variant matrix',
  'model-ops observed Gemini intake queue section',
);
assertIncludes(
  observedGeminiModelIntakePanel,
  'Promotion safety checks',
  'model-ops observed Gemini intake safety checks inside intake panel',
);
assertIncludes(
  observedGeminiModelIntakePanel,
  'Intake runbook',
  'model-ops observed Gemini intake runbook inside intake panel',
);
assertIncludes(
  observedGeminiModelIntakePanel,
  'safe_to_enter_default_change_queue',
  'model-ops observed Gemini intake safety flag inside intake panel',
);
const geminiDefaultChangeReviewPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini default change review</h2>',
  'Gemini default cost impact',
  'model-ops Gemini default change review section',
);
const modelOpsReadinessPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Model ops readiness</h2>',
  'Cheap-first release decision',
  'model-ops readiness section',
);
const gatewayRequestCompatibilityPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gateway request compatibility gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Request execution preflight</h2>',
  'model-ops gateway request compatibility section',
);
const requestExecutionPreflightPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Request execution preflight</h2>',
  '<h2 className="text-xl font-black text-stone-950">Request cost bounds</h2>',
  'model-ops request execution preflight section',
);
const routeTelemetryPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Route telemetry</h2>',
  '<h2 className="text-xl font-black text-stone-950">Route guardrails</h2>',
  'model-ops route telemetry section',
);
const routeTelemetryResultArchivePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Route telemetry result archive</h2>',
  '<h2 className="text-xl font-black text-stone-950">Route telemetry ops summary</h2>',
  'model-ops route telemetry result archive section',
);
assertIncludes(
  routeTelemetryResultArchivePanel,
  'Archive status',
  'model-ops route telemetry result archive status column',
);
assertIncludes(
  routeTelemetryResultArchivePanel,
  'Cost ledger',
  'model-ops route telemetry result archive cost ledger column',
);
assertIncludes(
  routeTelemetryResultArchivePanel,
  'metadata-only',
  'model-ops route telemetry result archive metadata-only boundary',
);
assertNotMatches(
  routeTelemetryResultArchivePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw[_ -]?prompt|prompt_payload|prompt|raw[_ -]?legal[_ -]?text|legal[_ -]?text|request[_ -]?bod(?:y|ies)|response[_ -]?bod(?:y|ies)|headers?|raw[_ -]?model[_ -]?output|model[_ -]?output|generated_text|candidate_text|document_text|client_email|email|phone|identity|user[_ -]?(?:id|identifier)|messages?|content)\b/i,
  'model-ops route telemetry result archive no raw legal/request/model/personal fields',
);
const cheapFirstPriorityQueuePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Cheap-first priority queue</h2>',
  'Gemini default change review',
  'model-ops cheap-first priority queue section',
);
const cheapFirstMaintainerExecutionChecklistPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Cheap-first maintainer execution checklist</h2>',
  'ModelOps load guard',
  'model-ops cheap-first maintainer execution checklist section',
);
const modelFailureUpgradeBudgetPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Model failure upgrade budget</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal micro benchmark preflight</h2>',
  'model-ops model failure upgrade budget section',
);
const modelOpsLegalMicroBenchmarkPreflightPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal micro benchmark preflight</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first benchmark gate</h2>',
  'model-ops legal micro benchmark preflight section',
);
const modelOpsLegalFixtureCheapFirstBenchmarkGatePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first benchmark gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first default promotion packet</h2>',
  'model-ops legal fixture cheap-first benchmark gate section',
);
const modelOpsLegalFixtureCheapFirstDefaultPromotionPacketPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first default promotion packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal fixture cheap-first regression budget</h2>',
  'model-ops legal fixture cheap-first default promotion packet section',
);
const modelOpsLegalFixtureEvidenceHandoffPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
  '<h2 className="text-xl font-black text-stone-950">ModelOps legal benchmark risk bridge</h2>',
  'model-ops legal fixture evidence handoff section',
);
const modelOpsLegalBenchmarkDefaultPromotionBridgePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion bridge</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion checklist</h2>',
  'model-ops legal benchmark default-promotion bridge section',
);
assertNotMatches(
  modelOpsLegalBenchmarkDefaultPromotionBridgePanel,
  /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|BEGIN PRIVATE KEY/i,
  'model-ops legal benchmark default-promotion bridge sensitive field guard',
);
const modelOpsLegalBenchmarkDefaultPromotionChecklistPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion checklist</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion signoff packet</h2>',
  'model-ops legal benchmark default-promotion checklist section',
);
assertNotMatches(
  modelOpsLegalBenchmarkDefaultPromotionChecklistPanel,
  /sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|BEGIN PRIVATE KEY/i,
  'model-ops legal benchmark default-promotion checklist sensitive field guard',
);
const modelOpsLegalBenchmarkDefaultPromotionSignoffPacketPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion signoff packet</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion execution handoff / rollback gate</h2>',
  'model-ops legal benchmark default-promotion signoff packet section',
);
assertNotMatches(
  modelOpsLegalBenchmarkDefaultPromotionSignoffPacketPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|BEGIN PRIVATE KEY|raw_prompt|prompt_payload|raw_payload|raw_model_output_value|raw_model_output_text|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email_address|phone_number|identity_value|identity_token|messages|fixture_snippet|benchmark_sample|input_excerpt|output_text)\b/i,
  'model-ops legal benchmark default-promotion signoff packet no secrets or raw benchmark/model/payload fields',
);
const modelOpsLegalBenchmarkDefaultPromotionExecutionHandoffPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark default-promotion execution handoff / rollback gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
  'model-ops legal benchmark default-promotion execution handoff section',
);
assertNotMatches(
  modelOpsLegalBenchmarkDefaultPromotionExecutionHandoffPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|BEGIN PRIVATE KEY|raw_prompt|prompt_payload|raw_payload|raw_model_output_value|raw_model_output_text|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email_address|phone_number|identity_value|identity_token|messages|fixture_snippet|benchmark_sample|input_excerpt|output_text)\b/i,
  'model-ops legal benchmark default-promotion execution handoff no secrets or raw benchmark/model/payload fields',
);
const modelOpsLegalBenchmarkRiskBridgePanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">ModelOps legal benchmark risk bridge</h2>',
  '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
  'model-ops legal benchmark risk bridge section',
);
const cheapFirstEscalationBudgetPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Cheap-first escalation budget</h2>',
  '<h2 className="text-xl font-black text-stone-950">Default optimization</h2>',
  'model-ops cheap-first escalation budget section',
);
const geminiDefaultCostImpactPanel = sourceSection(
  modelOpsPage,
  '<h2 className="text-xl font-black text-stone-950">Gemini default cost impact</h2>',
  'Cheap-first canary plan',
  'model-ops Gemini default cost impact section',
);
const userNeedImplementationQueuePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>',
  '<h2 className="text-xl font-black text-stone-950">User need legal-document benchmark evidence</h2>',
  'maintenance user need implementation priority queue section',
);
const userNeedLegalDocumentBenchmarkEvidencePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">User need legal-document benchmark evidence</h2>',
  '<h2 className="text-xl font-black text-stone-950">User need cheap-first handoff</h2>',
  'maintenance user need legal-document benchmark evidence section',
);
const maintenanceUserNeedCheapFirstHandoffPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">User need cheap-first handoff</h2>',
  '<h2 className="text-xl font-black text-stone-950">Product feature gap radar</h2>',
  'maintenance user need cheap-first handoff section',
);
const userNeedGeminiRouteCoveragePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">User need Gemini route coverage</h2>',
  '<h2 className="text-xl font-black text-stone-950">User need implementation priority queue</h2>',
  'maintenance user need Gemini route coverage section',
);
const legalFixtureCheapFirstBenchmarkGatePanel = sourceSection(
  maintenancePage,
  'Small legal-document fixture gate for cheap Gemini default evidence before routing changes.',
  'Legal fixture cheap-first default promotion packet',
  'maintenance legal fixture cheap-first benchmark gate section',
);
const legalFixtureCheapFirstDefaultPromotionPacketPanel = sourceSection(
  maintenancePage,
  'Maintainer-only packet for cheap-first legal fixture default review',
  '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
  'maintenance legal fixture cheap-first default promotion packet section',
);
const legalFixtureEvidenceHandoffPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal fixture evidence handoff</h2>',
  '<h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>',
  'maintenance legal fixture evidence handoff section',
);
const maintenanceCheapFirstReleaseDecisionPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Cheap-first release decision</h2>',
  'Model route legal benchmark risk queue',
  'maintenance cheap-first release decision section',
);
const legalDocumentFactConsistencyPanel = sourceSection(
  maintenancePage,
  '{legalDocumentFactConsistencyBenchmark && (',
  '<h2 className="text-xl font-black text-stone-950">Public benchmark sampler</h2>',
  'maintenance legal document fact consistency section',
);
const publicBenchmarkLicenseGatePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Public benchmark license gate</h2>',
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>',
  'maintenance public benchmark license gate section',
);
const legalBenchmarkFixtureCrosswalkPanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Legal benchmark fixture crosswalk</h2>',
  '<h2 className="text-xl font-black text-stone-950">Public fixture priority queue</h2>',
  'maintenance legal benchmark fixture crosswalk section',
);
const publicFixturePriorityQueuePanel = sourceSection(
  maintenancePage,
  '<h2 className="text-xl font-black text-stone-950">Public fixture priority queue</h2>',
  'Legal fixture evidence bundle',
  'maintenance public fixture priority queue section',
);

assertNotMatches(relevantSources, /\bsk-[A-Za-z0-9]{20,}\b/, 'frontend UI regression sources');
assertNotMatches(relevantSources, /raw private narrative/i, 'frontend UI regression sources');
assertNotMatches(relevantSources, /client@example\.com/i, 'frontend UI regression sources');
assertNotMatches(
  retrievalDiagnosticsPanel,
  /\b(raw_query|raw_context|raw_legal_text|unsafe_answer)(_text|_content|s)?\b/i,
  'maintenance Legal RAG retrieval diagnostics no raw query/context/legal text or unsafe answer fields',
);
assertNotMatches(
  legalRagIndexCoveragePanel,
  /\b(UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|sk-[A-Za-z0-9]{20,}|client@example\.invalid)\b/i,
  'maintenance Legal RAG index coverage no raw sample text, secrets, or emails',
);
assertNotMatches(
  legalRagEmbeddingReadinessPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|sk-[A-Za-z0-9]{20,}|client@example\.invalid)\b/i,
  'maintenance Legal RAG embedding readiness no raw vectors, raw legal text, source ids, secrets, or emails',
);
assertNotMatches(
  legalRagEmbeddingChunkPolicyPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|sk-[A-Za-z0-9]{20,}|client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding chunk policy no raw chunks, raw legal text, source ids, secrets, or emails',
);
assertNotMatches(
  legalRagEmbeddingIndexDryRunPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|sk-[A-Za-z0-9]{20,}|client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding index dry-run no raw chunks, raw legal text, source ids, secrets, or emails',
);
assertNotMatches(
  legalRagEmbeddingBatchBudgetPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding batch budget no raw chunks, raw legal text, source ids, secrets, or emails',
);
assertNotMatches(
  legalRagEmbeddingBatchApprovalPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|do-not-echo-approval-source-id|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|approval-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding batch approval no raw chunks, raw legal text, source ids, secrets, approver identity, or emails',
);
assertNotMatches(
  legalRagEmbeddingBatchObservationPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_OBSERVATION_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|do-not-echo-approval-source-id|do-not-echo-observation-source-id|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|approval-client@example\.invalid|observation-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding batch observation no raw chunks, raw legal text, source ids, secrets, approver identity, vectors, or emails',
);
assertNotMatches(
  legalRagEmbeddingIndexCommitReviewPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_OBSERVATION_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_INDEX_COMMIT_TEXT|RAW_INDEX_COMMIT_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|do-not-echo-approval-source-id|do-not-echo-observation-source-id|do-not-echo-commit-source-id|do-not-echo-committer-email|do-not-echo-commit-signature|committer-name-value|commit_signature_value|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|approval-client@example\.invalid|observation-client@example\.invalid|commit-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding index commit review no raw chunks, raw legal text, source ids, secrets, committer identity, vectors, or emails',
);
assertNotMatches(
  legalRagEmbeddingIndexPostCommitVerificationPanel,
  /\b(RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_OBSERVATION_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_INDEX_COMMIT_TEXT|RAW_INDEX_COMMIT_TEXT_SHOULD_NOT_LEAK|RAW_POST_COMMIT_TEXT|RAW_POST_COMMIT_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|do-not-echo-approval-source-id|do-not-echo-observation-source-id|do-not-echo-commit-source-id|do-not-echo-post-commit-source-id|do-not-echo-committer-email|do-not-echo-commit-signature|committer-name-value|commit_signature_value|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|approval-client@example\.invalid|observation-client@example\.invalid|commit-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding index post-commit verification no raw chunks, raw legal text, source ids, secrets, committer identity, vectors, or emails',
);
assertNotMatches(
  legalRagEmbeddingRetrievalDiagnosticsHandoffPanel,
  /\b(RAW_HANDOFF_TEXT|RAW_HANDOFF_TEXT_SHOULD_NOT_LEAK|RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK|UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|UNSAFE_BATCH_OBSERVATION_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|RAW_INDEX_COMMIT_TEXT|RAW_INDEX_COMMIT_TEXT_SHOULD_NOT_LEAK|RAW_POST_COMMIT_TEXT|RAW_POST_COMMIT_TEXT_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|RAW_QUERY_SHOULD_NOT_LEAK|source_id_value|source-id-value|do-not-echo-source-id|do-not-echo-batch-source-id|do-not-echo-approval-source-id|do-not-echo-observation-source-id|do-not-echo-commit-source-id|do-not-echo-post-commit-source-id|do-not-echo-handoff-source-id|do-not-echo-committer-email|do-not-echo-commit-signature|committer-name-value|commit_signature_value|sk-[A-Za-z0-9]{20,}|client@example\.invalid|batch-client@example\.invalid|approval-client@example\.invalid|observation-client@example\.invalid|commit-client@example\.invalid|handoff-client@example\.invalid|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance Legal RAG embedding retrieval diagnostics handoff no raw handoff/query/context/legal text, source ids, secrets, committer identity, vectors, or emails',
);
assertNotMatches(
  retrievalObservationPanel,
  /\b(RAW_QUERY_SHOULD_NOT_LEAK|RAW_CONTEXT|sk-[A-Za-z0-9]{20,}|client@example\.com)\b/i,
  'maintenance Legal RAG retrieval observation no raw sample text, secrets, or emails',
);
assertNotMatches(
  legalRagAnswerReleaseReadinessPanel,
  /\b(RAW_QUERY_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|source_id_value|source-id-value|SRC-CONTRACT-1|SRC-UNKNOWN-1|do-not-echo-source-id|sk-[A-Za-z0-9]{20,}|client@example\.invalid|client@example\.com|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK|credential_value|secret_value|prompt_payload|raw_model_output)\b/i,
  'maintenance Legal RAG answer release readiness no raw example values, source id values, secrets, prompts, model output, or emails',
);
assertNotMatches(
  feedbackLifecyclePolicyPanel,
  /\b(raw_feedback_value|RAW_FEEDBACK_SHOULD_NOT_LEAK|client@example\.invalid|client@example\.com|sk-[A-Za-z0-9]{20,}|credential_value|secret_value|prompt_payload|raw_model_output|authorization|api_key|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance feedback lifecycle policy no raw feedback values, secrets, prompts, model output, authorization, or emails',
);
assertNotMatches(
  feedbackUserNeedLegalDocumentBenchmarkBacklogPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_feedback|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_email|email|phone|identity|benchmark_sample|sample_text|input_excerpt|output_text)\b/i,
  'maintenance feedback user-need legal-document benchmark backlog no raw feedback/document/model/payload fields or credentials',
);
assertNotMatches(
  feedbackUserNeedLegalDocumentBenchmarkReleasePacketPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_feedback|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_email|email|phone|identity|customer_note|public_resolution_note|public_resolution|customer_message|notification_text|benchmark_sample|sample_text|input_excerpt|output_text)\b/i,
  'maintenance feedback user-need legal-document benchmark release packet no raw feedback/customer/document/model/payload fields or credentials',
);
assertNotMatches(
  finalDocumentDeliveryReleaseGatePanel,
  /\b(RAW_DOCUMENT_SHOULD_NOT_LEAK|UNSAFE_RAW_DIFF|UNSAFE_MODEL_OUTPUT|document_text|client_contact_details|client@example\.invalid|client@example\.com|sk-[A-Za-z0-9]{20,}|credential_value|secret_value|prompt_payload|raw_model_output|authorization|api_key|billing_provider_payload|provider-payload|C:\\\\cases\\\\private|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK)\b/i,
  'maintenance final document delivery release gate no raw document examples, contact details, provider payloads, credentials, prompts, model output, or emails',
);
assertNotMatches(
  smallLegalDocumentBenchmarkRunbookEvidencePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_document_text|raw_legal_text|fixture_snippet|document_snippet|request_body|response_body|headers|gateway_payload|model_output|client_email|client@example\.invalid|client@example\.com|PRIVATE_USER_EMAIL_SHOULD_NOT_LEAK|PRIVATE_ALT_EMAIL_SHOULD_NOT_LEAK|phone|identity|benchmark_sample|sample_text|input_excerpt|output_text|public_score_value)\b/i,
  'maintenance small legal document benchmark runbook evidence no raw legal/model/payload fields, benchmark text, contacts, or credentials',
);
assertNotMatches(
  maintenancePage,
  /fixture problem|dangerous answer|dangerous_answer|raw_fixture_problem|unsafe_answer_text|raw_unsafe_answer/i,
  'maintenance Legal RAG abstention no raw fixture problem or answer text',
);
assertNotMatches(
  geminiCheapFirstCoveragePanel,
  /\b(raw prompt|raw_prompt|raw payload|raw_payload|prompt_payload|credential material|credential_value|api_key|authorization|secret_value)\b/i,
  'model-ops Gemini cheap-first coverage no raw prompt/payload/credential material fields',
);
assertNotMatches(
  defaultTemplateAlignmentPanel,
  /\b(sk-[A-Za-z0-9]{20,}|password|credential_value|api_key|authorization|secret_value|raw prompt|raw_prompt|raw payload|raw_payload|prompt_payload)\b/i,
  'model-ops default template alignment no secrets or raw prompt/payload fields',
);
assertNotMatches(
  observedGeminiModelIntakePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output|raw_legal_text)\b/i,
  'model-ops observed Gemini intake queue no secret or raw prompt/payload/legal text field names',
);
assertNotMatches(
  geminiAliasCapabilityCoveragePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|raw_legal_text|gateway_response|request_body|response_body|headers|candidate_text|generated_text|output_text|email)\b/i,
  'model-ops Gemini/NewAPI alias capability coverage no secret or raw request/response/prompt/output fields',
);
assertNotMatches(
  geminiDefaultChangeReviewPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output)\b/i,
  'model-ops Gemini default change review no secret or raw prompt/payload field names',
);
assertNotMatches(
  modelOpsReadinessPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|gateway_response|request_body|response_body|headers)\b/i,
  'model-ops readiness warning drilldown no secret or raw request/response/prompt field names',
);
assertNotMatches(
  gatewayRequestCompatibilityPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_payload_value|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body_value|response_body|headers_value|client_email|phone)\b/i,
  'model-ops gateway request compatibility no secrets or raw request/body/prompt/model/legal fields',
);
assertNotMatches(
  gatewayConnectionProfilePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body_value|response_body|headers_value|client_email|phone|identity)\b/i,
  'model-ops gateway connection profile no secrets or raw request/response/prompt/model/legal fields',
);
assertNotMatches(
  routeTelemetryPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|phone|identity|messages|content)\b/i,
  'model-ops route telemetry no secrets or raw request/prompt/model/legal fields',
);
assertNotMatches(
  cheapFirstPriorityQueuePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output|raw_legal_text|authorization)\b/i,
  'model-ops cheap-first priority queue no secret or raw prompt/payload/output field names',
);
assertNotMatches(
  cheapFirstMaintainerExecutionChecklistPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|raw_prompt|prompt_payload|raw_model_output|raw_legal_text|raw_gateway_response|candidate_text)\b/i,
  'model-ops maintainer execution checklist no secret or raw prompt/output/legal text field names',
);
assertNotMatches(
  modelFailureUpgradeBudgetPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|email|phone|identity|messages|content)\b/i,
  'model-ops model failure upgrade budget no secrets or raw model/payload fields',
);
assertNotMatches(
  modelOpsLegalMicroBenchmarkPreflightPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet)\b/i,
  'model-ops legal micro benchmark preflight no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsLegalFixtureCheapFirstBenchmarkGatePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|input_excerpt|output_text)\b/i,
  'model-ops legal fixture cheap-first benchmark gate no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsLegalFixtureCheapFirstDefaultPromotionPacketPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|input_excerpt|output_text)\b/i,
  'model-ops legal fixture cheap-first default promotion packet no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsLegalFixtureEvidenceHandoffPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_gateway_response|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|input_excerpt|output_text)\b/i,
  'model-ops legal fixture evidence handoff no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsLegalBenchmarkRiskBridgePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet)\b/i,
  'model-ops legal benchmark risk bridge no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsUserNeedCheapFirstHandoffPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|benchmark_sample)\b/i,
  'model-ops user-need cheap-first handoff no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  modelOpsUserNeedGeminiRouteCoveragePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|gateway_response|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|benchmark_sample)\b/i,
  'model-ops user-need Gemini route coverage no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  cheapFirstEscalationBudgetPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|phone|identity)\b/i,
  'model-ops cheap-first escalation budget no secrets or raw model/payload fields',
);
assertNotMatches(
  geminiDefaultCostImpactPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output)\b/i,
  'model-ops Gemini default cost impact no secret or raw prompt/payload field names',
);
assertNotMatches(
  userNeedGeminiRouteCoveragePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output|raw_legal_text|document_text|fixture_snippet|sample_text|input_excerpt|output_text|generated_text|candidate_text|request_body|response_body|headers)\b/i,
  'maintenance user need Gemini route coverage no secret or raw prompt/payload/legal text field names',
);
assertNotMatches(
  userNeedImplementationQueuePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|raw_prompt|raw_payload|prompt_payload|raw_model_output|raw_legal_text)\b/i,
  'maintenance user need implementation priority queue no secret or raw prompt/payload/legal text field names',
);
assertNotMatches(
  userNeedLegalDocumentBenchmarkEvidencePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|document_text|fixture_snippet|sample_text|input_excerpt|output_text|request_body|response_body|headers|client_email|phone|identity)\b/i,
  'maintenance user need legal-document benchmark evidence no secrets or raw document/model/payload fields',
);
assertNotMatches(
  maintenanceUserNeedCheapFirstHandoffPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|gateway_response|headers|client_contact_details|email|phone|identity|benchmark_sample)\b/i,
  'maintenance user need cheap-first handoff no secrets or raw benchmark/model/payload fields',
);
assertNotMatches(
  legalFixtureCheapFirstBenchmarkGatePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|input_excerpt|output_text|generated_text|missing_sections|missing_citations|missing_risk_labels|pii_findings|raw_prompt|prompt_payload)\b/i,
  'maintenance legal fixture cheap-first benchmark gate no secrets or raw fixture/output field names',
);
assertNotMatches(
  legalFixtureCheapFirstDefaultPromotionPacketPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|input_excerpt|output_text|generated_text|document_text|missing_sections|missing_citations|missing_risk_labels|pii_findings|raw_prompt|prompt_payload)\b/i,
  'maintenance legal fixture cheap-first default promotion packet no secrets or raw fixture/output field names',
);
assertNotMatches(
  legalFixtureEvidenceHandoffPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|password|raw_prompt|prompt_payload|raw_payload|raw_gateway_response|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body|response_body|headers|client_contact_details|client_email|email|phone|identity|messages|content|fixture_snippet|input_excerpt|output_text)\b/i,
  'maintenance legal fixture evidence handoff no secrets or raw fixture/model/payload field names',
);
assertNotMatches(
  maintenanceCheapFirstReleaseDecisionPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|input_excerpt|output_text|generated_text|document_text|missing_sections|missing_citations|missing_risk_labels|pii_findings|raw_prompt|prompt_payload|raw_model_output|raw_legal_text|request_body|response_body|headers)\b/i,
  'maintenance cheap-first release decision no secrets or raw legal/model/payload field names',
);
assertNotMatches(
  legalDocumentFactConsistencyPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_output|raw_response|raw_prompt|prompt_payload|request_body|response_body|headers|document_text|fixture_text|sample_text|input_excerpt|output_text|candidate_text)\b/i,
  'maintenance legal document fact consistency no secrets or raw document/model fields',
);
assertNotMatches(
  publicBenchmarkLicenseGatePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|public_benchmark_raw_text|raw_sample_text|sample_payload|gateway_response|model_output)\b/i,
  'maintenance public benchmark license gate no raw samples, model output, gateway payload, or credentials',
);
assertNotMatches(
  legalBenchmarkFixtureCrosswalkPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|sample_text|synthetic_excerpt|input_excerpt|output_text|raw_prompt|prompt_payload|candidate_text)\b/i,
  'maintenance legal benchmark fixture crosswalk no secrets or raw fixture/corpus/model fields',
);
assertNotMatches(
  publicFixturePriorityQueuePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|secret_value|sample_text|synthetic_excerpt|input_excerpt|output_text|raw_prompt|prompt_payload|candidate_text|raw_model_output|gateway_response|request_body|response_body|headers)\b/i,
  'maintenance public fixture priority queue no secrets or raw benchmark/fixture/model/payload fields',
);
assertNotMatches(
  geminiCheapFirstRoutePreflightPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|api_key|authorization|secret_value|raw_prompt|prompt_payload|raw_payload|request_body|response_body|headers|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|email|phone|identity)\b/i,
  'model-ops Gemini cheap-first route preflight no secrets or raw model/payload/legal fields',
);
assertNotMatches(
  observedGatewayModelFitMatrixPanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body_value|response_body|headers_value|client_email|phone|identity)\b/i,
  'model-ops observed gateway model fit matrix no secrets or raw request/response/prompt/model/legal fields',
);
assertNotMatches(
  runtimeExplicitModelFitGatePanel,
  /\b(sk-[A-Za-z0-9]{20,}|credential_value|secret_value|api_key|authorization|bearer_token|raw_prompt|prompt_payload|raw_payload|raw_model_output|generated_text|candidate_text|document_text|raw_legal_text|request_body_value|response_body|headers_value|gateway_response|client_email|phone|identity|messages|content)\b/i,
  'model-ops runtime explicit model fit gate no secrets or raw request/response/prompt/model/legal fields',
);

console.log(
  JSON.stringify(
    {
      status: 'pass',
      checked_files: Object.values(files).filter((file) => file !== 'package.json'),
      command_gates: requiredScripts,
      assertions: checks.length + 40,
    },
    null,
    2,
  ),
);
