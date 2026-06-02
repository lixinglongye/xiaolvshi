import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Plus, Search, Briefcase, Calendar, FileText, AlertTriangle, Users, ChevronRight, FileArchive,
} from 'lucide-react';
import { toast } from 'sonner';
import { listCases, type CaseRecord } from '@/lib/caseApi';
import { useI18n } from '@/contexts/I18nContext';

const riskColors: Record<string, string> = {
  high: 'bg-red-100 text-red-700 border-red-300',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  low: 'bg-green-100 text-green-700 border-green-300',
};

const riskLabels = {
  zh: { high: '高风险', medium: '中风险', low: '低风险', 高: '高风险', 中: '中风险', 低: '低风险' },
  en: { high: 'High risk', medium: 'Medium risk', low: 'Low risk', 高: 'High risk', 中: 'Medium risk', 低: 'Low risk' },
};

const stageColors: Record<string, string> = {
  '咨询': 'bg-slate-100 text-slate-700',
  '诉前': 'bg-blue-100 text-blue-700',
  '一审': 'bg-indigo-100 text-indigo-700',
  '二审': 'bg-purple-100 text-purple-700',
  '仲裁': 'bg-amber-100 text-amber-700',
  '执行': 'bg-teal-100 text-teal-700',
  '结案': 'bg-gray-100 text-gray-700',
};

const completenessLabels = {
  zh: {
    high: { label: '完整', color: 'text-green-600' },
    medium: { label: '部分完整', color: 'text-yellow-600' },
    low: { label: '待补充', color: 'text-red-600' },
  },
  en: {
    high: { label: 'complete', color: 'text-green-600' },
    medium: { label: 'partly complete', color: 'text-yellow-600' },
    low: { label: 'needs evidence', color: 'text-red-600' },
  },
};

const stageLabels = {
  zh: { 咨询: '咨询', 诉前: '诉前', 一审: '一审', 二审: '二审', 仲裁: '仲裁', 执行: '执行', 结案: '结案' },
  en: { 咨询: 'Consultation', 诉前: 'Pre-litigation', 一审: 'First instance', 二审: 'Appeal', 仲裁: 'Arbitration', 执行: 'Enforcement', 结案: 'Closed' },
};

function riskKey(level?: string | null) {
  if (level === '高' || level === 'high') return 'high';
  if (level === '低' || level === 'low') return 'low';
  return 'medium';
}

function normalizedCompleteness(value?: string | null): 'high' | 'medium' | 'low' {
  if (value === '高' || value === '完整' || value === 'high') return 'high';
  if (value === '中' || value === '部分完整' || value === 'medium') return 'medium';
  return 'low';
}

function CaseCard({ c }: { c: CaseRecord }) {
  const { lang } = useI18n();
  const dateText = c.key_deadline?.slice(0, 10) || '';
  const deadlineDate = dateText ? new Date(dateText) : null;
  const now = new Date();
  const daysLeft = deadlineDate ? Math.ceil((deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)) : 9999;
  const isUrgent = daysLeft <= 7 && daysLeft >= 0;
  const comp = completenessLabels[lang][normalizedCompleteness(c.evidence_completeness)];
  const risk = riskKey(c.risk_level);
  const copy = lang === 'zh'
    ? {
        clientPending: '委托人待补',
        opponentPending: '对方待补',
        unstaged: '未分阶段',
        materials: '份材料',
        evidence: '证据',
        deadlineIn: (days: number) => `${days}天后到期`,
        noDeadline: '未设置期限',
        amount: '案涉金额',
        updated: '最近更新',
        justNow: '刚刚',
        unassigned: '未分配',
      }
    : {
        clientPending: 'Client pending',
        opponentPending: 'Opponent pending',
        unstaged: 'Unstaged',
        materials: 'materials',
        evidence: 'Evidence ',
        deadlineIn: (days: number) => `Due in ${days} days`,
        noDeadline: 'No deadline',
        amount: 'Amount in dispute',
        updated: 'Updated',
        justNow: 'just now',
        unassigned: 'Unassigned',
      };

  return (
    <Link to={`/cases/${c.id}`}>
      <Card className="surface-card cursor-pointer border-l-4 transition-colors hover:bg-[#f2ede3]" style={{ borderLeftColor: risk === 'high' ? '#dc2626' : risk === 'medium' ? '#d19a43' : '#3f7a54' }}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-slate-800 text-sm truncate">{c.title}</h3>
              <p className="text-xs text-slate-500 mt-0.5">{c.client_name || copy.clientPending} vs {c.opposing_party || copy.opponentPending}</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400 shrink-0 ml-2" />
          </div>

          <div className="flex flex-wrap gap-1.5 mb-3">
            <Badge variant="secondary" className="text-xs">{c.case_type}</Badge>
            <Badge className={`text-xs ${stageColors[c.stage || ''] || 'bg-slate-100 text-slate-700'}`}>{c.stage ? (stageLabels[lang][c.stage as keyof typeof stageLabels.zh] || c.stage) : copy.unstaged}</Badge>
            <Badge variant="outline" className={`text-xs ${riskColors[risk]}`}>{riskLabels[lang][c.risk_level || risk] || riskLabels[lang][risk]}</Badge>
            {c.role ? <Badge variant="outline" className="text-xs">{c.role}</Badge> : null}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div className="flex items-center gap-1 text-slate-600">
              <Users className="w-3 h-3" />
              <span>{c.owner_name || copy.unassigned}</span>
            </div>
            <div className="flex items-center gap-1 text-slate-600">
              <FileText className="w-3 h-3" />
              <span>{c.material_count ?? 0} {copy.materials}</span>
            </div>
            <div className={`flex items-center gap-1 ${comp.color}`}>
              <AlertTriangle className="w-3 h-3" />
              <span>{copy.evidence}{comp.label}</span>
            </div>
            <div className={`flex items-center gap-1 ${isUrgent ? 'text-red-600 font-semibold' : 'text-slate-600'}`}>
              <Calendar className="w-3 h-3" />
              <span>{c.key_deadline ? (isUrgent ? copy.deadlineIn(daysLeft) : c.key_deadline) : copy.noDeadline}</span>
            </div>
          </div>

          {!!c.amount && c.amount > 0 && (
            <p className="text-xs text-slate-500 mt-2">{copy.amount}: ¥{Number(c.amount).toLocaleString()}</p>
          )}

          <p className="text-xs text-slate-500 mt-1 line-clamp-1">{c.summary}</p>
          <p className="text-xs text-slate-400 mt-1">{copy.updated}: {c.updated_at ? new Date(c.updated_at).toLocaleString(lang === 'zh' ? 'zh-CN' : 'en-US') : copy.justNow}</p>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function CasesPage() {
  return (
    <AuthGuard>
      <CasesInner />
    </AuthGuard>
  );
}

function CasesInner() {
  const { lang } = useI18n();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [stageFilter, setStageFilter] = useState('all');
  const [ownerFilter, setOwnerFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const copy = lang === 'zh'
    ? {
        eyebrow: 'Case workspace',
        title: '案件工作台',
        subtitle: '管理您的所有案件、证据、材料和文书',
        importPackage: '导入案件包',
        newCase: '新建案件',
        allCases: '全部案件',
        highRiskCases: '高风险案件',
        dueSoon: '即将到期',
        totalMaterials: '总材料数',
        search: '搜索案件名称、客户…',
        caseType: '案件类型',
        stage: '案件阶段',
        owner: '负责人',
        risk: '风险等级',
        allTypes: '全部类型',
        allStages: '全部阶段',
        allOwners: '全部负责人',
        allRisks: '全部风险',
        loading: '正在加载案件...',
        loadFailed: '案件加载失败',
        noCases: '暂无案件，请先新建案件',
        noMatches: '暂无匹配的案件',
      }
    : {
        eyebrow: 'Case workspace',
        title: 'Case workspace',
        subtitle: 'Manage cases, evidence, materials, and legal documents.',
        importPackage: 'Import case bundle',
        newCase: 'New case',
        allCases: 'All cases',
        highRiskCases: 'High-risk cases',
        dueSoon: 'Due soon',
        totalMaterials: 'Total materials',
        search: 'Search case name or client...',
        caseType: 'Case type',
        stage: 'Stage',
        owner: 'Owner',
        risk: 'Risk level',
        allTypes: 'All types',
        allStages: 'All stages',
        allOwners: 'All owners',
        allRisks: 'All risks',
        loading: 'Loading cases...',
        loadFailed: 'Failed to load cases',
        noCases: 'No cases yet. Create a case first.',
        noMatches: 'No matching cases.',
      };

  useEffect(() => {
    let alive = true;
    setLoading(true);
    listCases()
      .then((res) => {
        if (alive) setCases(res.items || []);
      })
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : copy.loadFailed);
        if (alive) setCases([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  const filtered = useMemo(() => cases.filter((c) => {
    const haystack = `${c.title} ${c.client_name || ''} ${c.opposing_party || ''} ${c.owner_name || ''}`;
    if (search && !haystack.includes(search)) return false;
    if (typeFilter !== 'all' && c.case_type !== typeFilter) return false;
    if (stageFilter !== 'all' && c.stage !== stageFilter) return false;
    if (ownerFilter !== 'all' && c.owner_name !== ownerFilter) return false;
    if (riskFilter !== 'all' && riskKey(c.risk_level) !== riskFilter) return false;
    return true;
  }), [cases, ownerFilter, riskFilter, search, stageFilter, typeFilter]);

  const caseTypes = [...new Set(cases.map((c) => c.case_type).filter(Boolean))] as string[];
  const stages = [...new Set(cases.map((c) => c.stage).filter(Boolean))] as string[];
  const owners = [...new Set(cases.map((c) => c.owner_name).filter(Boolean))] as string[];

  return (
    <Layout>
      <div className="law-container py-10 lg:py-14 space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-stone-950/20 pb-6">
          <div>
            <div className="eyebrow mb-3">{copy.eyebrow}</div>
            <h1 className="text-4xl sm:text-6xl font-black leading-none text-stone-950 flex items-center gap-3">
              <Briefcase className="w-8 h-8 text-amber-700" />{copy.title}
            </h1>
            <p className="text-sm text-stone-600 mt-3">{copy.subtitle}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/lawyer/import">
              <Button variant="outline" className="soft-button">
                <FileArchive className="w-4 h-4 mr-2" />{copy.importPackage}
              </Button>
            </Link>
            <Link to="/cases/new">
              <Button className="quiet-button">
                <Plus className="w-4 h-4 mr-2" />{copy.newCase}
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="surface-card">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-slate-800">{cases.length}</p>
              <p className="text-xs text-slate-500">{copy.allCases}</p>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-red-600">{cases.filter((c) => riskKey(c.risk_level) === 'high').length}</p>
              <p className="text-xs text-slate-500">{copy.highRiskCases}</p>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-600">
                {cases.filter((c) => {
                  if (!c.key_deadline) return false;
                  const d = new Date(c.key_deadline.slice(0, 10));
                  const diff = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                  return diff <= 7 && diff >= 0;
                }).length}
              </p>
              <p className="text-xs text-slate-500">{copy.dueSoon}</p>
            </CardContent>
          </Card>
          <Card className="surface-card">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{cases.reduce((s, c) => s + (c.material_count ?? 0), 0)}</p>
              <p className="text-xs text-slate-500">{copy.totalMaterials}</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder={copy.search}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-[#fbfaf6] border-stone-950/25"
            />
          </div>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={copy.caseType} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{copy.allTypes}</SelectItem>
              {caseTypes.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={stageFilter} onValueChange={setStageFilter}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={copy.stage} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{copy.allStages}</SelectItem>
              {stages.map((s) => <SelectItem key={s} value={s}>{stageLabels[lang][s as keyof typeof stageLabels.zh] || s}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={ownerFilter} onValueChange={setOwnerFilter}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={copy.owner} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{copy.allOwners}</SelectItem>
              {owners.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={riskFilter} onValueChange={setRiskFilter}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={copy.risk} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{copy.allRisks}</SelectItem>
              <SelectItem value="high">{riskLabels[lang].high}</SelectItem>
              <SelectItem value="medium">{riskLabels[lang].medium}</SelectItem>
              <SelectItem value="low">{riskLabels[lang].low}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Case List */}
        {loading ? (
          <Card className="surface-card">
            <CardContent className="p-8 text-center text-slate-500">{copy.loading}</CardContent>
          </Card>
        ) : filtered.length === 0 ? (
          <Card className="surface-card">
            <CardContent className="p-8 text-center text-slate-500">
              <Briefcase className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>{cases.length === 0 ? copy.noCases : copy.noMatches}</p>
              <Link to="/cases/new">
                <Button className="mt-4 quiet-button">
                  <Plus className="w-4 h-4 mr-2" />{copy.newCase}
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filtered.map((c) => <CaseCard key={c.id} c={c} />)}
          </div>
        )}
      </div>
    </Layout>
  );
}
