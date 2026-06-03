import { useEffect, useMemo, useState } from 'react';
import AuthGuard from '@/components/AuthGuard';
import Layout from '@/components/Layout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
  getLegalFixtureImprovementPlan,
  getLegalFixturePromptPack,
  getLegalFixtureRunPlan,
  getLegalFixtureRunReport,
  getLegalKnowledgeAudit,
  getLegalReviewFixtureSmoke,
  getLegalReviewBenchmark,
  getLegalRagEvaluationPolicy,
  getMaintenanceEvidence,
  getFeedbackRoadmapCatalog,
  getReleaseReadiness,
  getUserNeedsRadar,
  type FeedbackRoadmapCatalog,
  type LegalFixtureImprovementPlan,
  type LegalFixturePromptPack,
  type LegalFixtureRunPlan,
  type LegalFixtureRunReport,
  type LegalKnowledgeAudit,
  type LegalReviewBenchmark,
  type LegalReviewFixtureSmoke,
  type LegalRagEvaluationPolicy,
  type MaintenanceEvidenceProfile,
  type MaintenanceLanguage,
  type ReleaseReadinessResult,
  type ReleaseValidationCommand,
  type UserNeedsRadar,
} from '@/lib/maintenanceApi';

const categoryClass: Record<string, string> = {
  model_ops: 'bg-sky-50 text-sky-800 border-sky-200',
  quality: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  review_ops: 'bg-amber-50 text-amber-900 border-amber-200',
  release_management: 'bg-red-50 text-red-800 border-red-200',
  product: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  maintenance: 'bg-stone-50 text-stone-800 border-stone-200',
};

const priorityClass: Record<string, string> = {
  high: 'border-red-200 bg-red-50 text-red-800',
  medium: 'border-amber-200 bg-amber-50 text-amber-900',
  low: 'border-stone-200 bg-stone-50 text-stone-700',
};

const statusClass: Record<string, string> = {
  pass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  ready: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  not_run: 'border-stone-200 bg-stone-50 text-stone-700',
  warn: 'border-amber-200 bg-amber-50 text-amber-900',
  review_recommended: 'border-amber-200 bg-amber-50 text-amber-900',
  needs_escalation: 'border-red-200 bg-red-50 text-red-800',
  needs_improvement: 'border-red-200 bg-red-50 text-red-800',
  fail: 'border-red-200 bg-red-50 text-red-800',
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
  const [feedbackRoadmap, setFeedbackRoadmap] = useState<FeedbackRoadmapCatalog | null>(null);
  const [benchmark, setBenchmark] = useState<LegalReviewBenchmark | null>(null);
  const [fixturePromptPack, setFixturePromptPack] = useState<LegalFixturePromptPack | null>(null);
  const [fixtureRunPlan, setFixtureRunPlan] = useState<LegalFixtureRunPlan | null>(null);
  const [fixtureRunReport, setFixtureRunReport] = useState<LegalFixtureRunReport | null>(null);
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
        feedbackMap,
        benchmarkData,
        fixturePromptPackData,
        fixtureRunPlanData,
        fixtureRunReportData,
        fixtureSmokeData,
        fixtureImprovementData,
        legalKnowledge,
        ragEvaluation,
      ] = await Promise.all([
        getMaintenanceEvidence(nextLanguage),
        getReleaseReadiness(),
        getUserNeedsRadar(),
        getFeedbackRoadmapCatalog(),
        getLegalReviewBenchmark(),
        getLegalFixturePromptPack(),
        getLegalFixtureRunPlan(),
        getLegalFixtureRunReport(),
        getLegalReviewFixtureSmoke(),
        getLegalFixtureImprovementPlan(),
        getLegalKnowledgeAudit(),
        getLegalRagEvaluationPolicy(),
      ]);
      setData(evidence);
      setReleaseReadiness(readiness.data);
      setValidationCommands(readiness.validation_commands);
      setUserNeeds(needsRadar);
      setFeedbackRoadmap(feedbackMap);
      setBenchmark(benchmarkData);
      setFixturePromptPack(fixturePromptPackData);
      setFixtureRunPlan(fixtureRunPlanData);
      setFixtureRunReport(fixtureRunReportData);
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

  const controls = data?.release_management.release_readiness_controls ?? [];
  const blockingCount = releaseReadiness?.blocking_check_ids.length ?? 0;
  const totalEvidencePaths = useMemo(
    () => (data?.signals ?? []).reduce((total, signal) => total + signal.evidence_paths.length, 0),
    [data],
  );

  const copyAnswer = async () => {
    if (!data?.form_answer) return;
    await navigator.clipboard.writeText(data.form_answer);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
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
