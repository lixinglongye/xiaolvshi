import { useEffect, useMemo, useState, type ReactNode } from 'react';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  CheckCircle2,
  ClipboardList,
  Database,
  FilePlus2,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { toast } from 'sonner';
import { client } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';

type Row = Record<string, any>;
type ListPayload = { items: Row[]; total: number };
type Overview = Record<string, number>;

const tabs = [
  { value: 'users', label: '用户/权益' },
  { value: 'orders', label: '订单' },
  { value: 'reports', label: '报告' },
  { value: 'templates', label: '模板' },
  { value: 'prompts', label: 'Prompt' },
  { value: 'feedback', label: '反馈' },
  { value: 'deletions', label: '删除请求' },
  { value: 'teams', label: '团队' },
  { value: 'evals', label: '评测集' },
];

const planOptions = ['free', 'personal', 'lawyer', 'enterprise', 'admin'];

const feedbackPriorityClass: Record<string, string> = {
  P0: 'border-red-200 bg-red-50 text-red-800',
  P1: 'border-amber-200 bg-amber-50 text-amber-900',
  P2: 'border-sky-200 bg-sky-50 text-sky-800',
  P3: 'border-stone-200 bg-stone-50 text-stone-700',
};

function listText(value: unknown, fallback = '-') {
  return Array.isArray(value) && value.length > 0 ? value.join(', ') : fallback;
}

async function adminApi<T>(path: string, method = 'GET', data?: unknown): Promise<T> {
  const resp = await client.apiCall.invoke({
    url: `/api/v1/admin/ops${path}`,
    method,
    data,
  });
  return (resp?.data ?? resp) as T;
}

function shortDate(value?: string) {
  if (!value) return '';
  return value.replace('T', ' ').slice(0, 19);
}

function safeJson(value: string) {
  try {
    JSON.parse(value);
    return value;
  } catch {
    return JSON.stringify([value], null, 2);
  }
}

export default function AdminPage() {
  return (
    <AuthGuard>
      <Inner />
    </AuthGuard>
  );
}

function Inner() {
  const { t } = useI18n();
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<Overview>({});
  const [data, setData] = useState<Record<string, ListPayload>>({});
  const [teams, setTeams] = useState<{ organizations: Row[]; members: Row[] }>({ organizations: [], members: [] });
  const [templateForm, setTemplateForm] = useState({
    doc_type: '合同',
    title: '',
    content: '',
    language: 'zh',
  });
  const [promptForm, setPromptForm] = useState({
    name: '深度审查主 Prompt',
    purpose: 'deep_review',
    version: `v${new Date().toISOString().slice(0, 10)}`,
    system_prompt:
      '报告必须以律师工作底稿为标准：每个风险定位原文、说明依据、给出可复制修改方案；不得编造法条或案例；缺少事实时列入待补事实。',
    user_prompt: '',
    status: 'draft',
  });
  const [evalForm, setEvalForm] = useState({
    title: '',
    document_type: '合同',
    user_role: '甲方',
    input_text: '',
    expected_risks_json: '[]',
    expected_sources_json: '[]',
    tags: '',
  });

  const activePrompt = useMemo(
    () => (data.prompts?.items ?? []).find((item) => item.is_active),
    [data.prompts],
  );

  const load = async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      const [
        overviewRes,
        users,
        orders,
        reports,
        templatesRes,
        prompts,
        feedback,
        deletions,
        teamsRes,
        evalCases,
        evalRuns,
      ] = await Promise.all([
        adminApi<Overview>('/overview'),
        adminApi<ListPayload>('/users'),
        adminApi<ListPayload>('/orders'),
        adminApi<ListPayload>('/reports'),
        adminApi<ListPayload>('/templates'),
        adminApi<ListPayload>('/prompt-versions'),
        adminApi<ListPayload>('/feedback'),
        adminApi<ListPayload>('/deletion-requests'),
        adminApi<{ organizations: Row[]; members: Row[] }>('/teams'),
        adminApi<ListPayload>('/evaluation-cases'),
        adminApi<ListPayload>('/evaluation-runs'),
      ]);
      setOverview(overviewRes);
      setData({
        users,
        orders,
        reports,
        templates: templatesRes,
        prompts,
        feedback,
        deletions,
        evalCases,
        evalRuns,
      });
      setTeams(teamsRes);
    } catch (e) {
      console.error(e);
      toast.error('后台数据加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [isAdmin]);

  const updateUserPlan = async (userId: string, plan_type: string) => {
    await adminApi(`/users/${encodeURIComponent(userId)}/subscription`, 'PUT', { plan_type, status: 'active' });
    toast.success('订阅权益已更新');
    load();
  };

  const updateUserRole = async (userId: string, role: string) => {
    await adminApi(`/users/${encodeURIComponent(userId)}/role`, 'PATCH', { role });
    toast.success('用户角色已更新');
    load();
  };

  const createTemplate = async () => {
    if (!templateForm.title.trim()) return toast.error('请填写模板标题');
    await adminApi('/templates', 'POST', { ...templateForm, is_active: true });
    toast.success('模板已创建');
    setTemplateForm({ ...templateForm, title: '', content: '' });
    load();
  };

  const createPrompt = async () => {
    if (!promptForm.name.trim() || !promptForm.system_prompt.trim()) return toast.error('请填写 Prompt 名称和内容');
    await adminApi('/prompt-versions', 'POST', { ...promptForm, is_active: false });
    toast.success('Prompt 版本已创建');
    load();
  };

  const seedDefaultPrompt = async () => {
    const res = await adminApi<{ created: number; message?: string }>('/prompt-versions/seed-default', 'POST');
    toast.success(res.created ? '默认深度审查 Prompt 已创建并激活' : res.message || 'Prompt 已存在');
    load();
  };

  const activatePrompt = async (id: number) => {
    await adminApi(`/prompt-versions/${id}/activate`, 'POST');
    toast.success('Prompt 已激活');
    load();
  };

  const updateStatus = async (path: string, status: string, operator_note?: string) => {
    await adminApi(path, 'PATCH', { status, operator_note });
    toast.success('状态已更新');
    load();
  };

  const createEvalCase = async () => {
    if (!evalForm.title.trim() || !evalForm.input_text.trim()) return toast.error('请填写评测标题和文书样本');
    await adminApi('/evaluation-cases', 'POST', {
      ...evalForm,
      expected_risks_json: safeJson(evalForm.expected_risks_json),
      expected_sources_json: safeJson(evalForm.expected_sources_json),
      status: 'active',
    });
    toast.success('评测用例已创建');
    setEvalForm({ ...evalForm, title: '', input_text: '', expected_risks_json: '[]', expected_sources_json: '[]', tags: '' });
    load();
  };

  const seedEvalCases = async () => {
    const res = await adminApi<{ created: number; message?: string }>('/evaluation-cases/seed-contracts', 'POST');
    toast.success(res.created ? `已创建 ${res.created} 条评测用例` : res.message || '评测用例已存在');
    load();
  };

  const runEval = async () => {
    if (!activePrompt) return toast.error('请先激活一个 deep_review Prompt');
    toast.info('评测运行中，可能需要等待模型返回');
    await adminApi('/evaluation-runs/run', 'POST', { prompt_version_id: activePrompt.id, limit: 3 });
    toast.success('评测运行完成');
    load();
  };

  if (!isAdmin) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto px-4 py-12">
          <Alert className="border-amber-200 bg-amber-50">
            <ShieldCheck className="w-4 h-4 text-amber-700" />
            <AlertDescription className="text-amber-900">
              当前账号不是管理员。请使用管理员开发登录或在后台将账号角色设为 admin。
            </AlertDescription>
          </Alert>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="eyebrow mb-2">Operations</div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{t('admin_title')}</h1>
            <p className="text-sm text-slate-600 mt-2">
              管理用户权益、订单、报告、模板、Prompt、反馈、删除请求、团队和评测回归。
            </p>
          </div>
          <Button onClick={load} disabled={loading} variant="outline" className="rounded-full">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Metric icon={<Users />} label="用户" value={overview.users} />
          <Metric icon={<ClipboardList />} label="报告" value={overview.reports} />
          <Metric icon={<Database />} label="Prompt 版本" value={overview.prompt_versions} />
          <Metric icon={<CheckCircle2 />} label="评测运行" value={overview.evaluation_runs} />
        </div>

        <Tabs defaultValue="users" className="space-y-4">
          <TabsList className="flex h-auto flex-wrap justify-start bg-slate-100 p-1">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value} className="rounded-full">
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle>用户、角色和订阅权益</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable
                  rows={data.users?.items ?? []}
                  columns={['email', 'role', 'plan', 'quota', 'used', 'remaining', 'created_at']}
                  render={(row, col) => {
                    const sub = row.subscription ?? {};
                    if (col === 'role') {
                      return (
                        <Select value={row.role || 'user'} onValueChange={(value) => updateUserRole(row.id, value)}>
                          <SelectTrigger className="h-8 w-[110px]"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">user</SelectItem>
                            <SelectItem value="admin">admin</SelectItem>
                          </SelectContent>
                        </Select>
                      );
                    }
                    if (col === 'plan') {
                      return (
                        <Select value={sub.plan_type || 'free'} onValueChange={(value) => updateUserPlan(row.id, value)}>
                          <SelectTrigger className="h-8 w-[130px]"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {planOptions.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      );
                    }
                    if (col === 'quota') return sub.report_quota_monthly ?? '';
                    if (col === 'used') return sub.reports_used_month ?? 0;
                    if (col === 'remaining') return sub.reports_remaining ?? '';
                    if (col === 'created_at') return shortDate(row.created_at);
                    return row[col];
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="orders">
            <SimpleCard title="订单管理" rows={data.orders?.items ?? []} columns={['id', 'user_id', 'sku', 'amount', 'currency', 'status', 'created_at']} />
          </TabsContent>

          <TabsContent value="reports">
            <SimpleCard title="报告管理" rows={data.reports?.items ?? []} columns={['id', 'user_id', 'document_id', 'contract_type', 'status', 'is_paid', 'created_at']} />
          </TabsContent>

          <TabsContent value="templates">
            <Card className="mb-4">
              <CardHeader><CardTitle className="flex items-center gap-2"><FilePlus2 className="w-5 h-5" /> 新建模板</CardTitle></CardHeader>
              <CardContent className="grid md:grid-cols-4 gap-3">
                <Field label="文书类型"><Input value={templateForm.doc_type} onChange={(e) => setTemplateForm({ ...templateForm, doc_type: e.target.value })} /></Field>
                <Field label="标题"><Input value={templateForm.title} onChange={(e) => setTemplateForm({ ...templateForm, title: e.target.value })} /></Field>
                <Field label="语言"><Input value={templateForm.language} onChange={(e) => setTemplateForm({ ...templateForm, language: e.target.value })} /></Field>
                <div className="flex items-end"><Button onClick={createTemplate} className="w-full quiet-button rounded-full">创建模板</Button></div>
                <div className="md:col-span-4">
                  <Label>模板内容</Label>
                  <Textarea rows={4} value={templateForm.content} onChange={(e) => setTemplateForm({ ...templateForm, content: e.target.value })} />
                </div>
              </CardContent>
            </Card>
            <SimpleCard title="模板列表" rows={data.templates?.items ?? []} columns={['id', 'doc_type', 'title', 'language', 'is_active', 'created_at']} />
          </TabsContent>

          <TabsContent value="prompts">
            <Card className="mb-4">
              <CardHeader><CardTitle>Prompt 版本管理</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="outline" onClick={seedDefaultPrompt}>导入默认深度审查 Prompt</Button>
                  <Badge variant="secondary">激活版本：{activePrompt ? `${activePrompt.name} ${activePrompt.version}` : '未激活'}</Badge>
                </div>
                <div className="grid md:grid-cols-4 gap-3">
                  <Field label="名称"><Input value={promptForm.name} onChange={(e) => setPromptForm({ ...promptForm, name: e.target.value })} /></Field>
                  <Field label="用途"><Input value={promptForm.purpose} onChange={(e) => setPromptForm({ ...promptForm, purpose: e.target.value })} /></Field>
                  <Field label="版本"><Input value={promptForm.version} onChange={(e) => setPromptForm({ ...promptForm, version: e.target.value })} /></Field>
                  <div className="flex items-end"><Button onClick={createPrompt} className="w-full quiet-button rounded-full">保存版本</Button></div>
                </div>
                <div>
                  <Label>系统 Prompt</Label>
                  <Textarea rows={5} value={promptForm.system_prompt} onChange={(e) => setPromptForm({ ...promptForm, system_prompt: e.target.value })} />
                </div>
                <div>
                  <Label>用户 Prompt 补充</Label>
                  <Textarea rows={3} value={promptForm.user_prompt} onChange={(e) => setPromptForm({ ...promptForm, user_prompt: e.target.value })} />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Prompt 列表</CardTitle></CardHeader>
              <CardContent>
                <DataTable
                  rows={data.prompts?.items ?? []}
                  columns={['id', 'name', 'purpose', 'version', 'status', 'is_active', 'eval_score', 'actions']}
                  render={(row, col) => {
                    if (col === 'is_active') return row.is_active ? <Badge>active</Badge> : <Badge variant="secondary">draft</Badge>;
                    if (col === 'actions') {
                      return (
                        <Button size="sm" variant="outline" onClick={() => activatePrompt(row.id)} disabled={row.is_active}>
                          激活
                        </Button>
                      );
                    }
                    return row[col];
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="feedback">
            <Card>
              <CardHeader><CardTitle>用户反馈处理</CardTitle></CardHeader>
              <CardContent>
                <DataTable
                  rows={data.feedback?.items ?? []}
                  columns={[
                    'id',
                    'priority',
                    'category',
                    'content',
                    'assignee',
                    'roadmap',
                    'lifecycle',
                    'closure',
                    'contact',
                    'status',
                    'resolution_note',
                    'actions',
                  ]}
                  render={(row, col) => {
                    if (col === 'priority') {
                      return (
                        <Badge variant="outline" className={feedbackPriorityClass[row.priority] ?? feedbackPriorityClass.P3}>
                          {row.priority || 'P3'}
                        </Badge>
                      );
                    }
                    if (col === 'assignee') {
                      return <span className="font-mono text-xs">{row.assignee || '-'}</span>;
                    }
                    if (col === 'roadmap') {
                      const needId = row.capture_summary?.linked_need_id ?? row.roadmap_summary?.top_need_id;
                      const gates = row.capture_summary?.release_gate_links;
                      return (
                        <div className="space-y-1">
                          <div className="font-mono text-xs">{needId || '-'}</div>
                          <div className="text-[11px] text-slate-500">{listText(gates, 'no gates')}</div>
                        </div>
                      );
                    }
                    if (col === 'lifecycle') {
                      return (
                        <div className="space-y-1">
                          <Badge variant="outline">{row.lifecycle_summary?.state || row.status || 'open'}</Badge>
                          <div className="text-[11px] text-slate-500">
                            next: {row.lifecycle_summary?.next_state || '-'}
                          </div>
                        </div>
                      );
                    }
                    if (col === 'closure') {
                      const blockers = row.lifecycle_summary?.blocking_check_ids ?? [];
                      const missing = row.capture_summary?.missing_required_fields ?? [];
                      return (
                        <div className="space-y-1 text-xs">
                          <Badge variant="outline" className={blockers.length ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'}>
                            {blockers.length ? `${blockers.length} blockers` : 'ready'}
                          </Badge>
                          <div className="text-[11px] text-slate-500">missing: {listText(missing, 'none')}</div>
                        </div>
                      );
                    }
                    if (col === 'resolution_note') {
                      return <span title={row.resolution_note || ''}>{row.resolution_note || '-'}</span>;
                    }
                    if (col === 'actions') {
                      return (
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => updateStatus(`/feedback/${row.id}`, 'processing')}>处理中</Button>
                          <Button size="sm" variant="outline" onClick={() => updateStatus(`/feedback/${row.id}`, 'resolved')}>已解决</Button>
                        </div>
                      );
                    }
                    return row[col];
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deletions">
            <Card>
              <CardHeader><CardTitle>删除请求处理</CardTitle></CardHeader>
              <CardContent>
                <DataTable
                  rows={data.deletions?.items ?? []}
                  columns={['id', 'user_id', 'document_id', 'reason', 'status', 'processed_by', 'processed_at', 'actions']}
                  render={(row, col) => {
                    if (col === 'processed_at') return shortDate(row.processed_at);
                    if (col === 'actions') {
                      return (
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => updateStatus(`/deletion-requests/${row.id}`, 'approved', '管理员批准删除')}>批准</Button>
                          <Button size="sm" variant="outline" onClick={() => updateStatus(`/deletion-requests/${row.id}`, 'rejected', '管理员驳回删除')}>驳回</Button>
                        </div>
                      );
                    }
                    return row[col];
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="teams">
            <div className="grid lg:grid-cols-2 gap-4">
              <SimpleCard title="组织" rows={teams.organizations} columns={['id', 'user_id', 'name', 'plan_type', 'description', 'created_at']} />
              <SimpleCard title="成员" rows={teams.members} columns={['id', 'org_id', 'member_email', 'role', 'status', 'created_at']} />
            </div>
          </TabsContent>

          <TabsContent value="evals">
            <Card className="mb-4">
              <CardHeader><CardTitle className="flex items-center gap-2"><PlayCircle className="w-5 h-5" /> 评测集和回归</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={seedEvalCases}>导入合同高频评测集</Button>
                  <Button onClick={runEval} className="quiet-button rounded-full">运行当前 Prompt 评测</Button>
                  <Badge variant="secondary">当前 Prompt：{activePrompt ? `${activePrompt.name} ${activePrompt.version}` : '未激活'}</Badge>
                </div>
                <div className="grid md:grid-cols-3 gap-3">
                  <Field label="标题"><Input value={evalForm.title} onChange={(e) => setEvalForm({ ...evalForm, title: e.target.value })} /></Field>
                  <Field label="文书类型"><Input value={evalForm.document_type} onChange={(e) => setEvalForm({ ...evalForm, document_type: e.target.value })} /></Field>
                  <Field label="用户角色"><Input value={evalForm.user_role} onChange={(e) => setEvalForm({ ...evalForm, user_role: e.target.value })} /></Field>
                </div>
                <div>
                  <Label>文书样本</Label>
                  <Textarea rows={4} value={evalForm.input_text} onChange={(e) => setEvalForm({ ...evalForm, input_text: e.target.value })} />
                </div>
                <div className="grid md:grid-cols-3 gap-3">
                  <Field label="期望风险 JSON"><Textarea rows={3} value={evalForm.expected_risks_json} onChange={(e) => setEvalForm({ ...evalForm, expected_risks_json: e.target.value })} /></Field>
                  <Field label="期望依据 JSON"><Textarea rows={3} value={evalForm.expected_sources_json} onChange={(e) => setEvalForm({ ...evalForm, expected_sources_json: e.target.value })} /></Field>
                  <div className="space-y-3">
                    <Field label="标签"><Input value={evalForm.tags} onChange={(e) => setEvalForm({ ...evalForm, tags: e.target.value })} /></Field>
                    <Button onClick={createEvalCase} className="w-full quiet-button rounded-full">创建用例</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
            <div className="grid xl:grid-cols-2 gap-4">
              <SimpleCard title="评测用例" rows={data.evalCases?.items ?? []} columns={['id', 'title', 'document_type', 'user_role', 'tags', 'status']} />
              <SimpleCard title="运行记录" rows={data.evalRuns?.items ?? []} columns={['id', 'prompt_version_id', 'evaluation_case_id', 'status', 'score', 'created_at']} />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value?: number }) {
  return (
    <Card className="surface-card">
      <CardContent className="p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-950 text-white flex items-center justify-center [&_svg]:w-5 [&_svg]:h-5">
          {icon}
        </div>
        <div>
          <div className="text-xs text-slate-500">{label}</div>
          <div className="text-2xl font-semibold text-slate-950">{value ?? 0}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <Label className="text-xs text-slate-500">{label}</Label>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function SimpleCard({ title, rows, columns }: { title: string; rows: Row[]; columns: string[] }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <DataTable rows={rows} columns={columns} />
      </CardContent>
    </Card>
  );
}

function DataTable({
  rows,
  columns,
  render,
}: {
  rows: Row[];
  columns: string[];
  render?: (row: Row, column: string) => ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((c) => (
              <TableHead key={c} className="whitespace-nowrap">{c}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="text-center text-slate-500 py-8">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            rows.map((r) => (
              <TableRow key={`${r.id}-${r.created_at ?? ''}`}>
                {columns.map((c) => (
                  <TableCell key={c} className="max-w-[260px] truncate text-sm">
                    {render ? render(r, c) : c.endsWith('_at') ? shortDate(r[c]) : String(r[c] ?? '')}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
