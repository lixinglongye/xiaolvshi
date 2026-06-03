import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Markdown from 'markdown-to-jsx';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import CaseWorkbenchRuntimePanel from '@/components/cases/CaseWorkbenchRuntimePanel';
import LegalRagResearchPanel from '@/components/cases/LegalRagResearchPanel';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  AlertTriangle, BookOpen, Bot, Briefcase, Calendar, CheckSquare, ChevronLeft,
  ChevronRight, Copy, Download, FileText, FolderOpen, Loader2, Plus,
  Scale, Search, Send, Settings, Shield, Target, User, Users,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  caseAiChat,
  createCaseFact,
  createCaseMaterial,
  createCaseParty,
  createCaseTask,
  createGeneratedCaseDocument,
  generateCaseCivilComplaint,
  generateCaseEvidenceCatalog,
  getCase,
  listCaseFacts,
  listCaseMaterials,
  listCaseParties,
  listCaseTasks,
  listGeneratedCaseDocuments,
  updateCase,
  updateCaseMaterial,
  updateCaseTask,
  type CaseFactRecord,
  type CaseMaterialRecord,
  type CasePartyRecord,
  type CaseRecord,
  type CaseTaskRecord,
  type GeneratedCaseDocument,
} from '@/lib/caseApi';
import { useI18n } from '@/contexts/I18nContext';

type TabKey = 'overview' | 'materials' | 'evidence' | 'facts' | 'timeline' | 'research' | 'documents' | 'tasks' | 'team' | 'settings';
type ChatMessageItem = { role: 'user' | 'assistant'; content: string };
type ChatSession = { id: string; title: string; messages: ChatMessageItem[] };

const materialTypes = ['合同', '证据', '沟通记录', '身份/主体材料', '诉讼材料', '仲裁材料', '行政材料', '图片/视频/音频', '内部材料', '其他'];
const docTypes = ['案件分析报告', '证据目录', '起诉状', '答辩状', '律师函', '仲裁申请书', '庭审提纲', '补证清单', '法律研究备忘录'];
const OLD_CHAT_WELCOME = '我会读取本案材料、证据、事实、请求、任务和已生成文书后回答。没有证据支撑的内容会标注待核实，不会当作已确认事实。';

function createChatSession(index: number): ChatSession {
  return {
    id: `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: `对话 ${index}`,
    messages: [],
  };
}

function lines(value?: string | null): string[] {
  return String(value || '')
    .split(/\n|；|;/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function riskClass(level?: string | null): string {
  if (level === '高' || level === 'high') return 'bg-red-100 text-red-700 border-red-200';
  if (level === '低' || level === 'low') return 'bg-green-100 text-green-700 border-green-200';
  return 'bg-amber-100 text-amber-700 border-amber-200';
}

function evidenceClass(value?: string | null): string {
  if (value === '高' || value === '无争议' || value === '直接相关' || value === '合法') return 'bg-green-50 text-green-700 border-green-200';
  if (value === '低' || value?.includes('高')) return 'bg-red-50 text-red-700 border-red-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
}

function dateText(value?: string | null): string {
  if (!value) return '未设置';
  return value.length > 19 ? new Date(value).toLocaleString('zh-CN') : value;
}

function money(value?: number | null): string {
  if (!value) return '待补充';
  return `¥${Number(value).toLocaleString()}`;
}

function materialPrefix(type: string, isEvidence: boolean): string {
  if (isEvidence) return 'E';
  if (type.includes('合同')) return 'C';
  if (type.includes('沟通')) return 'CH';
  if (type.includes('转账') || type.includes('付款')) return 'PAY';
  if (type.includes('发票') || type.includes('收据')) return 'INV';
  return 'M';
}

function nextNo(prefix: string, existing: Array<{ material_no?: string | null; fact_no?: string | null }>, field: 'material_no' | 'fact_no'): string {
  const max = existing.reduce((acc, item) => {
    const raw = item[field] || '';
    const match = raw.match(new RegExp(`^${prefix}-(\\d+)$`));
    return match ? Math.max(acc, Number(match[1])) : acc;
  }, 0);
  return `${prefix}-${String(max + 1).padStart(3, '0')}`;
}

function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function copyToClipboard(content: string, message = '已复制') {
  navigator.clipboard.writeText(content || '');
  toast.success(message);
}

function buildEvidenceDirectory(materials: CaseMaterialRecord[]): string {
  const evidences = materials.filter((item) => item.is_evidence);
  if (!evidences.length) return '当前案件尚未标记证据。';
  return [
    '# 证据目录',
    '',
    ...evidences.flatMap((item, index) => [
      `## 证据${index + 1}：${item.title}`,
      `- 证据编号：${item.material_no || `E-${String(index + 1).padStart(3, '0')}`}`,
      `- 证据类型：${item.material_type || '待补充'}`,
      `- 来源：${item.source || '待补充'}`,
      `- 证明目的：${item.proof_purpose || '待补充'}`,
      `- 页码/段落：${item.page_refs || '待补充'}`,
      `- 真实性：${item.authenticity_status || '待核实'}`,
      `- 关联性：${item.relevance_status || '待核实'}`,
      `- 合法性：${item.legality_status || '待核实'}`,
      `- 采信风险：${item.admissibility_risk || '待律师复核'}`,
      '',
    ]),
  ].join('\n');
}

function buildDocumentContent(
  docType: string,
  item: CaseRecord,
  materials: CaseMaterialRecord[],
  facts: CaseFactRecord[],
): string {
  const evidences = materials.filter((m) => m.is_evidence);
  const factLines = facts.length
    ? facts.map((fact) => `- ${fact.event_date || '时间待核实'}：${fact.fact_text}【${fact.source_refs || '待核实事实，需补充证据'}】`)
    : [`- ${item.summary || '案件事实待补充'}【待核实事实，需补充证据】`];
  const evidenceLines = evidences.length
    ? evidences.map((m, index) => `- ${m.material_no || `E-${index + 1}`}：${m.title}，证明目的：${m.proof_purpose || '待补充'}`)
    : ['- 暂无已确认电子证据，请先在材料库中标记证据并填写证明目的。'];

  if (docType === '证据目录') return buildEvidenceDirectory(materials);
  if (docType === '补证清单') {
    return [
      '# 补证清单',
      '',
      '## 待补材料',
      ...(lines(item.missing_materials).length ? lines(item.missing_materials).map((x) => `- ${x}`) : ['- 身份/主体材料、完整合同文本、付款凭证、沟通记录、送达凭证等需按案件实际补充。']),
      '',
      '## 证据短板',
      ...evidences.filter((m) => m.need_notarization || m.admissibility_risk).map((m) => `- ${m.material_no || ''} ${m.title}：${m.admissibility_risk || '建议公证/保全'}`),
    ].join('\n');
  }

  return [
    `# ${docType}`,
    '',
    '## 生成前核验清单',
    '- 当事人名称、证件号、地址和联系方式需由用户确认；',
    '- 管辖法院/仲裁机构需与合同、案件事实和法律规定核验；',
    '- 诉讼请求、金额计算和证据链需由律师复核；',
    '- 未有证据支持的事实已标注为“待核实”。',
    '',
    '## 案件基础信息',
    `- 案件名称：${item.title}`,
    `- 案件类型：${item.case_type || '待补充'}`,
    `- 代理方：${item.role || '待补充'}`,
    `- 委托人：${item.client_name || '待补充'}`,
    `- 对方当事人：${item.opposing_party || '待补充'}`,
    `- 管辖法院/仲裁机构：${item.court_or_arbitration || item.jurisdiction || '待补充'}`,
    `- 案涉金额：${money(item.amount)}`,
    '',
    '## 诉讼请求/目标',
    ...(lines(item.claims).length ? lines(item.claims).map((x) => `- ${x}`) : ['- 待补充明确请求事项、金额和计算方式。']),
    '',
    '## 事实与证据引用',
    ...factLines,
    '',
    '## 证据目录摘要',
    ...evidenceLines,
    '',
    '## 法律依据',
    ...(lines(item.legal_basis).length ? lines(item.legal_basis).map((x) => `- ${x}`) : ['- 法律依据待接入法条/案例检索后补充，正式提交前必须核验。']),
    '',
    '## 律师复核提示',
    '- 本草稿由 AI 基于案件工作台材料生成，不构成正式法律意见；诉讼、仲裁、律师函等正式文书应由执业律师复核后使用。',
  ].join('\n');
}

export default function CaseDetailPage() {
  return <AuthGuard><Inner /></AuthGuard>;
}

function Inner() {
  const { id } = useParams();
  const caseId = Number(id);
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [caseItem, setCaseItem] = useState<CaseRecord | null>(null);
  const [materials, setMaterials] = useState<CaseMaterialRecord[]>([]);
  const [facts, setFacts] = useState<CaseFactRecord[]>([]);
  const [tasks, setTasks] = useState<CaseTaskRecord[]>([]);
  const [parties, setParties] = useState<CasePartyRecord[]>([]);
  const [documents, setDocuments] = useState<GeneratedCaseDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [workspaceCollapsed, setWorkspaceCollapsed] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>(() => [createChatSession(1)]);
  const [activeChatId, setActiveChatId] = useState('');
  const [chatCacheReady, setChatCacheReady] = useState(false);
  const [materialDialog, setMaterialDialog] = useState(false);
  const [factDialog, setFactDialog] = useState(false);
  const [taskDialog, setTaskDialog] = useState(false);
  const [partyDialog, setPartyDialog] = useState(false);
  const [docDialog, setDocDialog] = useState(false);
  const [viewDoc, setViewDoc] = useState<GeneratedCaseDocument | null>(null);
  const [researchQuery, setResearchQuery] = useState('');
  const [researchResults, setResearchResults] = useState<string[]>([]);
  const [researchLoading, setResearchLoading] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);

  const [materialForm, setMaterialForm] = useState({
    title: '',
    material_type: '证据',
    source: '用户上传',
    parsed_text: '',
    is_evidence: true,
    proof_purpose: '',
    page_refs: '',
  });
  const [factForm, setFactForm] = useState({ event_date: '', fact_text: '', persons: '', amount: '', source_refs: '', confidence: '中', verified_by_user: false, contradiction_note: '' });
  const [taskForm, setTaskForm] = useState({ title: '', description: '', assigned_to: '', due_date: '', priority: '中', status: '待开始' });
  const [partyForm, setPartyForm] = useState({ name: '', party_type: '当事人', identity_type: '待核实', id_number: '', address: '', contact: '', lawyer: '' });
  const [docForm, setDocForm] = useState({ doc_type: '案件分析报告' });

  const evidences = useMemo(() => materials.filter((item) => item.is_evidence), [materials]);
  const unsupportedFacts = useMemo(() => facts.filter((fact) => !fact.source_refs), [facts]);
  const urgentTasks = useMemo(() => tasks.filter((task) => task.status !== '已完成' && task.due_date), [tasks]);
  const activeChat = useMemo(
    () => chatSessions.find((session) => session.id === activeChatId) || chatSessions[0],
    [activeChatId, chatSessions],
  );
  const chatMessages = activeChat?.messages || [];

  const loadWorkspace = async () => {
    if (!Number.isFinite(caseId)) return;
    setLoading(true);
    try {
      const [c, materialRes, factRes, taskRes, partyRes, docRes] = await Promise.all([
        getCase(caseId),
        listCaseMaterials(caseId),
        listCaseFacts(caseId),
        listCaseTasks(caseId),
        listCaseParties(caseId),
        listGeneratedCaseDocuments(caseId),
      ]);
      setCaseItem(c);
      setMaterials(materialRes.items || []);
      setFacts(factRes.items || []);
      setTasks(taskRes.items || []);
      setParties(partyRes.items || []);
      setDocuments(docRes.items || []);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '案件加载失败');
      setCaseItem(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  useEffect(() => {
    if (!Number.isFinite(caseId)) return;
    setChatCacheReady(false);
    const fallback = [createChatSession(1)];
    try {
      const raw = window.localStorage.getItem(`case-chat-sessions-${caseId}`);
      const parsed = raw ? JSON.parse(raw) : null;
      if (Array.isArray(parsed) && parsed.length) {
        const sessions = parsed
          .filter((item) => item && typeof item.id === 'string' && typeof item.title === 'string' && Array.isArray(item.messages))
          .map((item) => ({
            id: item.id,
            title: item.title,
            messages: item.messages.filter((message: ChatMessageItem) => message?.role && message?.content && message.content !== OLD_CHAT_WELCOME),
          }));
        if (sessions.length) {
          setChatSessions(sessions);
          setActiveChatId(sessions[0].id);
          setChatCacheReady(true);
          return;
        }
      }
    } catch {
      // Ignore corrupted local chat cache and reset the current case chat windows.
    }
    setChatSessions(fallback);
    setActiveChatId(fallback[0].id);
    setChatCacheReady(true);
  }, [caseId]);

  useEffect(() => {
    if (!chatCacheReady || !Number.isFinite(caseId) || !chatSessions.length) return;
    window.localStorage.setItem(`case-chat-sessions-${caseId}`, JSON.stringify(chatSessions.slice(0, 12)));
  }, [caseId, chatCacheReady, chatSessions]);

  useEffect(() => {
    const container = chatScrollRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  const refreshCounts = async (updates: Partial<CaseRecord>) => {
    if (!caseItem) return;
    try {
      const updated = await updateCase(caseItem.id, updates);
      setCaseItem(updated);
    } catch {
      setCaseItem({ ...caseItem, ...updates });
    }
  };

  const submitMaterial = async () => {
    if (!caseItem || !materialForm.title.trim()) {
      toast.error('请输入材料名称');
      return;
    }
    const prefix = materialPrefix(materialForm.material_type, materialForm.is_evidence);
    const created = await createCaseMaterial({
      case_id: caseItem.id,
      material_no: nextNo(prefix, materials, 'material_no'),
      title: materialForm.title.trim(),
      material_type: materialForm.material_type,
      source: materialForm.source,
      parsed_text: materialForm.parsed_text,
      ocr_status: materialForm.parsed_text ? '已解析' : '待解析',
      is_evidence: materialForm.is_evidence,
      proof_purpose: materialForm.proof_purpose,
      page_refs: materialForm.page_refs,
      authenticity_status: materialForm.is_evidence ? '待核实' : '',
      relevance_status: materialForm.is_evidence ? '待分析' : '',
      legality_status: materialForm.is_evidence ? '待核实' : '',
      admissibility_risk: materialForm.is_evidence ? '待律师复核' : '',
      need_notarization: materialForm.material_type.includes('沟通') || materialForm.material_type.includes('音频') || materialForm.material_type.includes('视频'),
      source_reliability: '中',
    });
    const nextMaterials = [...materials, created];
    setMaterials(nextMaterials);
    await refreshCounts({ material_count: nextMaterials.length, evidence_completeness: nextMaterials.some((m) => m.is_evidence && !m.proof_purpose) ? '中' : '高' });
    setMaterialDialog(false);
    setMaterialForm({ title: '', material_type: '证据', source: '用户上传', parsed_text: '', is_evidence: true, proof_purpose: '', page_refs: '' });
    toast.success('材料已入库');
  };

  const markAsEvidence = async (material: CaseMaterialRecord) => {
    const updated = await updateCaseMaterial(material.id, {
      is_evidence: true,
      material_no: material.material_no?.startsWith('E-') ? material.material_no : nextNo('E', materials, 'material_no'),
      authenticity_status: material.authenticity_status || '待核实',
      relevance_status: material.relevance_status || '待分析',
      legality_status: material.legality_status || '待核实',
      admissibility_risk: material.admissibility_risk || '待律师复核',
    });
    setMaterials((prev) => prev.map((item) => (item.id === material.id ? updated : item)));
    toast.success('已标记为证据');
  };

  const submitFact = async () => {
    if (!caseItem || !factForm.fact_text.trim()) {
      toast.error('请输入事实内容');
      return;
    }
    const created = await createCaseFact({
      case_id: caseItem.id,
      fact_no: nextNo('F', facts, 'fact_no'),
      ...factForm,
    });
    setFacts((prev) => [...prev, created]);
    setFactDialog(false);
    setFactForm({ event_date: '', fact_text: '', persons: '', amount: '', source_refs: '', confidence: '中', verified_by_user: false, contradiction_note: '' });
    toast.success('事实已加入时间线');
  };

  const submitTask = async () => {
    if (!caseItem || !taskForm.title.trim()) {
      toast.error('请输入任务名称');
      return;
    }
    const created = await createCaseTask({ case_id: caseItem.id, ...taskForm });
    setTasks((prev) => [...prev, created]);
    setTaskDialog(false);
    setTaskForm({ title: '', description: '', assigned_to: '', due_date: '', priority: '中', status: '待开始' });
    toast.success('任务已创建');
  };

  const submitParty = async () => {
    if (!caseItem || !partyForm.name.trim()) {
      toast.error('请输入当事人名称');
      return;
    }
    const created = await createCaseParty({ case_id: caseItem.id, ...partyForm });
    setParties((prev) => [...prev, created]);
    setPartyDialog(false);
    setPartyForm({ name: '', party_type: '当事人', identity_type: '待核实', id_number: '', address: '', contact: '', lawyer: '' });
    toast.success('当事人已加入');
  };

  const generateDocument = async (docType = docForm.doc_type) => {
    if (!caseItem) return;
    if (docType === '证据目录' || docType === '起诉状') {
      try {
        const result = docType === '证据目录'
          ? await generateCaseEvidenceCatalog(caseItem.id)
          : await generateCaseCivilComplaint(caseItem.id, true);
        if (!result.success || !result.document) {
          toast.error(result.message || `${docType}生成失败`);
          return;
        }
        setDocuments((prev) => [result.document as GeneratedCaseDocument, ...prev]);
        setDocDialog(false);
        setActiveTab('documents');
        const missing = result.preflight?.missing_required || [];
        if (missing.length) {
          toast.warning(`${docType}已生成带缺口草稿：${missing.slice(0, 2).join('、')}`);
        } else {
          toast.success(`${docType}已生成并完成 QA Gate`);
        }
        return;
      } catch (error) {
        toast.error(error instanceof Error ? error.message : `${docType}生成失败`);
        return;
      }
    }
    const content = buildDocumentContent(docType, caseItem, materials, facts);
    const citationMap = {
      materials: materials.filter((m) => content.includes(m.material_no || '')).map((m) => m.material_no),
      unsupported_facts: unsupportedFacts.map((fact) => fact.fact_no),
    };
    const created = await createGeneratedCaseDocument({
      case_id: caseItem.id,
      doc_type: docType,
      title: `${docType} - ${caseItem.title}`,
      content,
      draft_label: 'AI草稿',
      status: docType.includes('目录') ? '待复核' : '草稿',
      generated_by: 'case_workspace',
      citation_map: JSON.stringify(citationMap),
      input_data_json: JSON.stringify({ case_id: caseItem.id, material_count: materials.length, fact_count: facts.length }),
    });
    setDocuments((prev) => [created, ...prev]);
    setDocDialog(false);
    setActiveTab('documents');
    toast.success(`${docType}已生成`);
  };

  const runResearch = async () => {
    if (!caseItem) return;
    const query = researchQuery.trim() || caseItem?.case_type || '案件法律研究';
    setResearchLoading(true);
    try {
      const result = await caseAiChat(caseItem.id, {
        message: `请基于当前案件上下文和本地法条库，围绕“${query}”做法律研究提纲。要求：区分已有依据和需继续检索核验的依据，绑定争议焦点、证据短板和下一步。`,
        conversation_history: chatMessages.slice(-6),
      });
      setResearchResults([result.response]);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '法律研究失败');
    } finally {
      setResearchLoading(false);
    }
  };

  const sendChat = async (preset?: string) => {
    if (!caseItem || chatLoading || !activeChat) return;
    const prompt = (preset || chatInput).trim();
    if (!prompt) return;
    const targetChatId = activeChat.id;
    const history = chatMessages.slice(-8);
    setChatSessions((prev) => prev.map((session) => {
      if (session.id !== targetChatId) return session;
      const nextTitle = session.messages.length ? session.title : prompt.slice(0, 18);
      return {
        ...session,
        title: nextTitle || session.title,
        messages: [...session.messages, { role: 'user', content: prompt }],
      };
    }));
    setChatInput('');
    setChatLoading(true);
    try {
      const result = await caseAiChat(caseItem.id, {
        message: prompt,
        conversation_history: history,
      });
      setChatSessions((prev) => prev.map((session) => (
        session.id === targetChatId
          ? { ...session, messages: [...session.messages, { role: 'assistant', content: result.response || '模型未返回有效内容。' }] }
          : session
      )));
    } catch (error) {
      const message = error instanceof Error ? error.message : '案件 AI 分析失败';
      setChatSessions((prev) => prev.map((session) => (
        session.id === targetChatId
          ? { ...session, messages: [...session.messages, { role: 'assistant', content: `接口调用失败：${message}` }] }
          : session
      )));
      toast.error(message);
    } finally {
      setChatLoading(false);
    }
  };

  const createNewChat = () => {
    const next = createChatSession(chatSessions.length + 1);
    setChatSessions((prev) => [...prev, next]);
    setActiveChatId(next.id);
    setChatInput('');
  };

  const saveSettings = async () => {
    if (!caseItem) return;
    setSavingSettings(true);
    try {
      const updated = await updateCase(caseItem.id, caseItem);
      setCaseItem(updated);
      toast.success('案件设置已保存');
    } finally {
      setSavingSettings(false);
    }
  };

  if (loading) {
    return (
      <Layout hideFooter>
        <div className="min-h-[50vh] flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />正在加载案件工作台...
        </div>
      </Layout>
    );
  }

  if (!caseItem) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto p-8 text-center">
          <Briefcase className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600">未找到该案件。</p>
          <Button asChild className="mt-4"><Link to="/cases">返回案件列表</Link></Button>
        </div>
      </Layout>
    );
  }

  const quickActions = [
    '案件分析报告',
    '证据目录',
    '起诉状',
    '答辩状',
    '律师函',
    '庭审提纲',
    '补证清单',
  ];
  const tabPaneClass = 'mt-4 min-h-0 flex-1 overflow-y-auto pr-1';
  const workspaceGridClass = workspaceCollapsed
    ? 'lg:grid-cols-[64px_minmax(0,1fr)]'
    : 'lg:grid-cols-[minmax(320px,420px)_minmax(0,1fr)]';

  return (
    <Layout hideFooter>
      <div className="case-workspace min-h-[calc(100vh-68px)] lg:h-[calc(100vh-68px)] lg:overflow-hidden">
        <div className={`grid h-full min-h-[calc(100vh-68px)] lg:min-h-0 lg:overflow-hidden ${workspaceGridClass}`}>
          <section data-testid="case-ai-chat-panel" className="case-chat-surface flex min-h-[620px] flex-col overflow-hidden lg:order-2 lg:h-full lg:min-h-0">
            <div className="px-5 pb-3 pt-4 lg:px-8">
              <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm font-semibold text-stone-900">
                    <Bot className="h-4 w-4 text-stone-500" />案件 AI
                  </div>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-8 rounded-full border-stone-950/10 bg-[#fffdf8]/80 px-3 text-xs shadow-none hover:bg-[#fffdf8]"
                  onClick={createNewChat}
                >
                  <Plus className="mr-1 h-3.5 w-3.5" />新对话
                </Button>
              </div>
              <div className="mx-auto mt-3 flex max-w-3xl flex-wrap gap-2">
                {chatSessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    className={`max-w-[190px] truncate rounded-full px-3 py-1.5 text-xs transition-colors ${session.id === activeChat?.id ? 'bg-stone-900 text-white' : 'bg-[#fffdf8]/75 text-stone-600 hover:bg-[#fffdf8]'}`}
                    onClick={() => setActiveChatId(session.id)}
                  >
                    {session.title}
                  </button>
                ))}
              </div>
            </div>
            <div data-testid="case-chat-scroll" ref={chatScrollRef} className="min-h-0 flex-1 overflow-y-auto px-5 py-5 lg:px-8">
              <div className="mx-auto max-w-3xl space-y-7">
                {chatMessages.map((message, index) => (
                  <ChatBubble key={index} message={message} />
                ))}
                {chatLoading && (
                  <div className="max-w-[760px] text-sm text-stone-600">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />正在调取案件上下文并调用模型分析...
                  </div>
                )}
              </div>
            </div>
            <div className="px-5 pb-5 pt-3 lg:px-8">
              <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-[24px] bg-[#fffdf8] p-2 shadow-[0_14px_46px_rgba(28,25,23,0.10)] ring-1 ring-stone-950/10">
                <Textarea
                  className="min-h-[54px] resize-none border-0 bg-transparent px-3 shadow-none focus-visible:ring-0"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendChat();
                    }
                  }}
                  placeholder="询问证据链、事实缺口、诉讼策略或文书草稿..."
                />
                <Button size="icon" className="h-[46px] w-[46px] shrink-0 rounded-full bg-stone-900 text-white hover:bg-stone-700" disabled={chatLoading || !chatInput.trim()} onClick={() => sendChat()}>
                  {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </section>

          {workspaceCollapsed ? (
            <aside data-testid="case-workspace-collapsed" className="hidden flex-col items-center gap-3 bg-[#f2eee6] p-2 lg:order-1 lg:flex lg:h-full lg:min-h-0">
              <Button
                type="button"
                size="icon"
                variant="outline"
                className="h-10 w-10 rounded-full border-0 bg-white/80 shadow-none"
                data-testid="case-workspace-expand"
                aria-label="展开案件侧栏"
                title="展开案件侧栏"
                onClick={() => setWorkspaceCollapsed(false)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <div className="mt-2 flex flex-col items-center gap-3 text-stone-500">
                <Briefcase className="h-4 w-4" />
                <FolderOpen className="h-4 w-4" />
                <Shield className="h-4 w-4" />
                <FileText className="h-4 w-4" />
              </div>
            </aside>
          ) : (
            <aside data-testid="case-workspace-panel" className="flex flex-col overflow-hidden bg-[#f2eee6] lg:order-1 lg:h-full lg:min-h-0">
              <div className="p-4">
                <Link to="/cases" className="mb-4 inline-flex items-center text-sm font-semibold text-stone-500 hover:text-stone-950">
                  <ChevronLeft className="w-4 h-4 mr-1" />案件列表
                </Link>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="eyebrow mb-2">Case file</div>
                    <h1 className="line-clamp-2 text-xl font-black leading-tight text-stone-950">{caseItem.title}</h1>
                    <p className="mt-2 text-xs text-stone-500">CASE-{String(caseItem.id).padStart(4, '0')} | {caseItem.case_type || '类型待补'} | {caseItem.stage || '阶段待补'}</p>
                  </div>
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    className="hidden h-9 w-9 shrink-0 rounded-full border-0 bg-white/80 shadow-none lg:inline-flex"
                    data-testid="case-workspace-collapse"
                    aria-label="收起案件侧栏"
                    title="收起案件侧栏"
                    onClick={() => setWorkspaceCollapsed(true)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Badge className={`border ${riskClass(caseItem.risk_level)}`}>{caseItem.risk_level || '中'}风险</Badge>
                  <Button size="sm" variant="outline" className="h-8 rounded-full border-stone-950/10 bg-white/70 px-3 text-xs shadow-none" onClick={() => downloadText(`${caseItem.title}-案件分析报告.md`, buildDocumentContent('案件分析报告', caseItem, materials, facts))}>
                    <Download className="w-3.5 h-3.5 mr-1" />报告下载
                  </Button>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <InfoItem icon={<User className="w-3.5 h-3.5" />} label="委托人" value={caseItem.client_name || '待补'} />
                  <InfoItem icon={<Briefcase className="w-3.5 h-3.5" />} label="对方" value={caseItem.opposing_party || '待补'} />
                  <InfoItem icon={<Scale className="w-3.5 h-3.5" />} label="管辖" value={caseItem.court_or_arbitration || caseItem.jurisdiction || '待补'} />
                  <InfoItem icon={<Target className="w-3.5 h-3.5" />} label="代理方" value={caseItem.role || '待补'} />
                  <InfoItem icon={<Calendar className="w-3.5 h-3.5" />} label="期限" value={caseItem.key_deadline || '待补'} />
                  <InfoItem icon={<Shield className="w-3.5 h-3.5" />} label="证据" value={`${evidences.length}份`} />
                </div>
              </div>
              <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabKey)} className="flex min-h-0 flex-1 flex-col px-3 pb-3">
              <TabsList className="flex h-auto flex-wrap justify-start gap-1 bg-transparent p-0">
                <Tab value="overview" icon={<Briefcase className="w-3.5 h-3.5" />} label="概览" />
                <Tab value="materials" icon={<FolderOpen className="w-3.5 h-3.5" />} label="材料" />
                <Tab value="evidence" icon={<Shield className="w-3.5 h-3.5" />} label="证据" />
                <Tab value="facts" icon={<HashIcon />} label="事实" />
                <Tab value="timeline" icon={<Calendar className="w-3.5 h-3.5" />} label="时间线" />
                <Tab value="research" icon={<BookOpen className="w-3.5 h-3.5" />} label="法律研究" />
                <Tab value="documents" icon={<FileText className="w-3.5 h-3.5" />} label="文书" />
                <Tab value="tasks" icon={<CheckSquare className="w-3.5 h-3.5" />} label="任务" />
                <Tab value="team" icon={<Users className="w-3.5 h-3.5" />} label="团队" />
                <Tab value="settings" icon={<Settings className="w-3.5 h-3.5" />} label="设置" />
              </TabsList>

              <TabsContent value="overview" className={tabPaneClass}>
                <div className="space-y-4">
                  <OverviewTab
                    caseItem={caseItem}
                    materials={materials}
                    facts={facts}
                    tasks={urgentTasks}
                    unsupportedFacts={unsupportedFacts}
                    quickActions={quickActions}
                    onGenerate={generateDocument}
                    onResearch={() => { setActiveTab('research'); runResearch(); }}
                  />
                  <CaseWorkbenchRuntimePanel
                    caseId={caseItem.id}
                    defaultTaskRefHash={urgentTasks[0]?.id ? `task_${urgentTasks[0].id}` : undefined}
                  />
                </div>
              </TabsContent>

              <TabsContent value="materials" className={tabPaneClass}>
                <MaterialsTab materials={materials} onOpenUpload={() => setMaterialDialog(true)} onMarkEvidence={markAsEvidence} />
              </TabsContent>

              <TabsContent value="evidence" className={tabPaneClass}>
                <EvidenceTab
                  evidences={evidences}
                  onExport={() => downloadText(`${caseItem.title}-证据目录.md`, buildEvidenceDirectory(materials))}
                  onReinforce={async (material) => {
                    const task = await createCaseTask({
                      case_id: caseItem.id,
                      title: `补强证据：${material.title}`,
                      description: material.admissibility_risk || '补充证据真实性、关联性或合法性材料。',
                      assigned_to: caseItem.owner_name || '',
                      due_date: caseItem.key_deadline?.slice(0, 10) || '',
                      priority: '高',
                      status: '待开始',
                      related_object_type: 'material',
                      related_object_id: material.id,
                    });
                    setTasks((prev) => [...prev, task]);
                    toast.success('补强任务已创建');
                  }}
                />
              </TabsContent>

              <TabsContent value="facts" className={tabPaneClass}>
                <FactsTab facts={facts} onAdd={() => setFactDialog(true)} />
              </TabsContent>

              <TabsContent value="timeline" className={tabPaneClass}>
                <TimelineTab facts={facts} />
              </TabsContent>

              <TabsContent value="research" className={tabPaneClass}>
                <LegalRagResearchPanel
                  caseId={caseItem.id}
                  defaultUseCase={caseItem.case_type || 'contract_review'}
                />
              </TabsContent>

              <TabsContent value="documents" className={tabPaneClass}>
                <DocumentsTab documents={documents} onOpenGenerate={() => setDocDialog(true)} onView={setViewDoc} />
              </TabsContent>

              <TabsContent value="tasks" className={tabPaneClass}>
                <TasksTab
                  tasks={tasks}
                  onAdd={() => setTaskDialog(true)}
                  onToggle={async (task) => {
                    const updated = await updateCaseTask(task.id, { status: task.status === '已完成' ? '进行中' : '已完成' });
                    setTasks((prev) => prev.map((item) => (item.id === task.id ? updated : item)));
                  }}
                />
              </TabsContent>

              <TabsContent value="team" className={tabPaneClass}>
                <TeamTab parties={parties} teamMembers={caseItem.team_members} onAdd={() => setPartyDialog(true)} />
              </TabsContent>

              <TabsContent value="settings" className={tabPaneClass}>
                <SettingsTab caseItem={caseItem} setCaseItem={setCaseItem} onSave={saveSettings} saving={savingSettings} />
              </TabsContent>
              </Tabs>
            </aside>
          )}
        </div>
      </div>

      <Dialog open={materialDialog} onOpenChange={setMaterialDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>上传/登记案件材料</DialogTitle>
            <DialogDescription className="sr-only">登记案件材料、解析文本、来源和证据字段。</DialogDescription>
          </DialogHeader>
          <div className="grid md:grid-cols-2 gap-4">
            <Field label="材料名称"><Input value={materialForm.title} onChange={(e) => setMaterialForm({ ...materialForm, title: e.target.value })} placeholder="例：银行转账记录" /></Field>
            <Field label="材料类型">
              <Select value={materialForm.material_type} onValueChange={(v) => setMaterialForm({ ...materialForm, material_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{materialTypes.map((type) => <SelectItem key={type} value={type}>{type}</SelectItem>)}</SelectContent>
              </Select>
            </Field>
            <Field label="来源"><Input value={materialForm.source} onChange={(e) => setMaterialForm({ ...materialForm, source: e.target.value })} /></Field>
            <Field label="页码/段落引用"><Input value={materialForm.page_refs} onChange={(e) => setMaterialForm({ ...materialForm, page_refs: e.target.value })} placeholder="例：第1页 / 第15行" /></Field>
            <div className="md:col-span-2 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={materialForm.is_evidence} onChange={(e) => setMaterialForm({ ...materialForm, is_evidence: e.target.checked })} />
              入库时同步标记为证据并生成证据编号
            </div>
            <Field label="证明目的" className="md:col-span-2"><Textarea rows={2} value={materialForm.proof_purpose} onChange={(e) => setMaterialForm({ ...materialForm, proof_purpose: e.target.value })} placeholder="说明该材料证明什么事实" /></Field>
            <Field label="解析文本/摘要" className="md:col-span-2"><Textarea rows={4} value={materialForm.parsed_text} onChange={(e) => setMaterialForm({ ...materialForm, parsed_text: e.target.value })} placeholder="可粘贴 OCR/转写/材料摘要，后续将用于事实提取" /></Field>
          </div>
          <DialogFooter><Button onClick={submitMaterial}>入库</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={factDialog} onOpenChange={setFactDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>补充案件事实</DialogTitle>
            <DialogDescription className="sr-only">补充事实发生时间、内容、来源证据和待核实说明。</DialogDescription>
          </DialogHeader>
          <div className="grid md:grid-cols-2 gap-4">
            <Field label="发生日期"><Input value={factForm.event_date} onChange={(e) => setFactForm({ ...factForm, event_date: e.target.value })} placeholder="2026-05-15" /></Field>
            <Field label="涉及人物"><Input value={factForm.persons} onChange={(e) => setFactForm({ ...factForm, persons: e.target.value })} /></Field>
            <Field label="金额"><Input value={factForm.amount} onChange={(e) => setFactForm({ ...factForm, amount: e.target.value })} /></Field>
            <Field label="来源证据"><Input value={factForm.source_refs} onChange={(e) => setFactForm({ ...factForm, source_refs: e.target.value })} placeholder="例：E-001 第2页" /></Field>
            <Field label="事实内容" className="md:col-span-2"><Textarea rows={3} value={factForm.fact_text} onChange={(e) => setFactForm({ ...factForm, fact_text: e.target.value })} /></Field>
            <Field label="矛盾提示/待核实说明" className="md:col-span-2"><Textarea rows={2} value={factForm.contradiction_note} onChange={(e) => setFactForm({ ...factForm, contradiction_note: e.target.value })} /></Field>
          </div>
          <DialogFooter><Button onClick={submitFact}>加入事实库</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={taskDialog} onOpenChange={setTaskDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建任务/期限</DialogTitle>
            <DialogDescription className="sr-only">创建案件任务、负责人、截止日期和说明。</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Field label="任务名称"><Input value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} /></Field>
            <Field label="负责人"><Input value={taskForm.assigned_to} onChange={(e) => setTaskForm({ ...taskForm, assigned_to: e.target.value })} /></Field>
            <Field label="截止日期"><Input value={taskForm.due_date} onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })} placeholder="2026-06-01" /></Field>
            <Field label="说明"><Textarea value={taskForm.description} onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} /></Field>
          </div>
          <DialogFooter><Button onClick={submitTask}>创建任务</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={partyDialog} onOpenChange={setPartyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新增当事人/团队对象</DialogTitle>
            <DialogDescription className="sr-only">新增案件相关人员、当事人或团队对象信息。</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Field label="名称"><Input value={partyForm.name} onChange={(e) => setPartyForm({ ...partyForm, name: e.target.value })} /></Field>
            <Field label="身份/角色"><Input value={partyForm.party_type} onChange={(e) => setPartyForm({ ...partyForm, party_type: e.target.value })} /></Field>
            <Field label="证件号/统一社会信用代码"><Input value={partyForm.id_number} onChange={(e) => setPartyForm({ ...partyForm, id_number: e.target.value })} /></Field>
            <Field label="联系方式"><Input value={partyForm.contact} onChange={(e) => setPartyForm({ ...partyForm, contact: e.target.value })} /></Field>
            <Field label="代理人"><Input value={partyForm.lawyer} onChange={(e) => setPartyForm({ ...partyForm, lawyer: e.target.value })} /></Field>
          </div>
          <DialogFooter><Button onClick={submitParty}>保存</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={docDialog} onOpenChange={setDocDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>生成案件文书</DialogTitle>
            <DialogDescription className="sr-only">选择文书类型并生成带事实和证据引用链的草稿。</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Field label="文书类型">
              <Select value={docForm.doc_type} onValueChange={(v) => setDocForm({ doc_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{docTypes.map((type) => <SelectItem key={type} value={type}>{type}</SelectItem>)}</SelectContent>
              </Select>
            </Field>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              生成前会强制保留事实引用链；没有来源证据的事实将标注“待核实”。正式提交前仍需律师复核。
            </div>
          </div>
          <DialogFooter><Button onClick={() => generateDocument()}>生成草稿</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!viewDoc} onOpenChange={(open) => { if (!open) setViewDoc(null); }}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          {viewDoc && (
            <>
              <DialogHeader>
                <DialogTitle>{viewDoc.title || viewDoc.doc_type}</DialogTitle>
                <DialogDescription className="sr-only">查看、复制或下载生成的案件文书草稿。</DialogDescription>
              </DialogHeader>
              <pre className="whitespace-pre-wrap rounded-lg bg-slate-50 border p-4 text-sm text-slate-700">{viewDoc.content}</pre>
              <DialogFooter>
                <Button variant="outline" onClick={() => { navigator.clipboard.writeText(viewDoc.content || ''); toast.success('已复制'); }}><Copy className="w-4 h-4 mr-1" />复制</Button>
                <Button onClick={() => downloadText(`${viewDoc.title || viewDoc.doc_type}.md`, viewDoc.content || '')}><Download className="w-4 h-4 mr-1" />下载</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
}

function InfoItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-[10px] bg-[#efebe1]/70 border border-stone-950/12 px-2.5 py-2 min-w-0">
      <span className="text-amber-700 shrink-0">{icon}</span>
      <span className="text-stone-500 shrink-0">{label}：</span>
      <span className="font-semibold text-stone-800 truncate">{value}</span>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessageItem }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[72%] whitespace-pre-wrap rounded-[18px] bg-stone-900 px-4 py-2.5 text-sm leading-7 text-white shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="group relative max-w-[760px]">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-stone-500">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-stone-900 text-white">
            <Bot className="h-3.5 w-3.5" />
          </span>
          案件 AI
        </div>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-7 rounded-full px-2 text-xs text-stone-400 opacity-0 transition-opacity hover:bg-stone-100 hover:text-stone-700 group-hover:opacity-100"
          onClick={() => copyToClipboard(message.content, 'AI 回复已复制')}
        >
          <Copy className="mr-1 h-3.5 w-3.5" />复制
        </Button>
      </div>
      <div className="case-chat-answer">
        <Markdown>{message.content}</Markdown>
      </div>
    </div>
  );
}

function Tab({ value, icon, label }: { value: string; icon: React.ReactNode; label: string }) {
  return (
    <TabsTrigger value={value} className="h-9 rounded-[10px] border border-stone-950/15 bg-[#fbfaf6] px-3 text-xs font-semibold text-stone-600 data-[state=active]:bg-stone-950 data-[state=active]:text-white">
      {icon}<span className="ml-1">{label}</span>
    </TabsTrigger>
  );
}

function HashIcon() {
  return <span className="inline-flex h-3.5 w-3.5 items-center justify-center text-[11px] font-semibold">F</span>;
}

function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return <div className={className}><Label className="text-xs text-slate-600">{label}</Label>{children}</div>;
}

function OverviewTab({
  caseItem,
  materials,
  facts,
  tasks,
  unsupportedFacts,
  quickActions,
  onGenerate,
  onResearch,
}: {
  caseItem: CaseRecord;
  materials: CaseMaterialRecord[];
  facts: CaseFactRecord[];
  tasks: CaseTaskRecord[];
  unsupportedFacts: CaseFactRecord[];
  quickActions: string[];
  onGenerate: (docType: string) => void;
  onResearch: () => void;
}) {
  const { lang } = useI18n();
  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-4 gap-3">
        <Metric label="材料" value={materials.length} />
        <Metric label="证据" value={materials.filter((m) => m.is_evidence).length} />
        <Metric label="事实" value={facts.length} />
        <Metric label="待办" value={tasks.length} />
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <Card><CardHeader><CardTitle className="text-base">案件摘要</CardTitle></CardHeader><CardContent className="text-sm text-slate-700 whitespace-pre-wrap">{caseItem.summary || '暂无摘要，请在设置中补充案件背景。'}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">争议焦点</CardTitle></CardHeader><CardContent><BulletList items={lines(caseItem.dispute_focus)} empty="暂无争议焦点。" /></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">诉讼请求/目标</CardTitle></CardHeader><CardContent><BulletList items={lines(caseItem.claims)} empty="暂无诉讼请求或非诉目标。" /></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">待补材料</CardTitle></CardHeader><CardContent><BulletList items={lines(caseItem.missing_materials)} empty="暂无待补材料清单。" /></CardContent></Card>
      </div>
      {unsupportedFacts.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4 text-sm text-amber-800">
            <AlertTriangle className="w-4 h-4 inline mr-1" />
            {lang === 'zh'
              ? <>有 {unsupportedFacts.length} 项事实缺少证据来源，生成正式文书时会标注“待核实”。</>
              : <>{unsupportedFacts.length} fact(s) lack evidence sources; formal drafts will mark them as "to be verified".</>}
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader><CardTitle className="text-base">一键生成</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {quickActions.map((action) => <Button key={action} variant="outline" size="sm" onClick={() => onGenerate(action)}>{action}</Button>)}
          <Button size="sm" onClick={onResearch}><Search className="w-4 h-4 mr-1" />开始类案检索</Button>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <Card className="case-workspace-panel"><CardContent className="p-4"><div className="text-3xl font-black text-stone-950">{value}</div><div className="text-xs text-stone-500 mt-1">{label}</div></CardContent></Card>;
}

function BulletList({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) return <p className="text-sm text-slate-500">{empty}</p>;
  return <ul className="list-disc list-inside text-sm text-slate-700 space-y-1">{items.map((item) => <li key={item}>{item}</li>)}</ul>;
}

function MaterialsTab({ materials, onOpenUpload, onMarkEvidence }: { materials: CaseMaterialRecord[]; onOpenUpload: () => void; onMarkEvidence: (m: CaseMaterialRecord) => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">材料库</CardTitle><Button size="sm" onClick={onOpenUpload}><Plus className="w-4 h-4 mr-1" />上传材料</Button></CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow><TableHead>编号</TableHead><TableHead>材料</TableHead><TableHead>类型</TableHead><TableHead>来源</TableHead><TableHead>证明目的</TableHead><TableHead>状态</TableHead><TableHead>操作</TableHead></TableRow></TableHeader>
          <TableBody>
            {materials.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-mono text-xs">{item.material_no}</TableCell>
                <TableCell className="font-medium">{item.title}</TableCell>
                <TableCell>{item.material_type}</TableCell>
                <TableCell>{item.source}</TableCell>
                <TableCell className="max-w-[260px] truncate">{item.proof_purpose || '-'}</TableCell>
                <TableCell>{item.is_evidence ? <Badge className="bg-emerald-50 text-emerald-700 border border-emerald-200">证据</Badge> : <Badge variant="outline">材料</Badge>}</TableCell>
                <TableCell>{!item.is_evidence && <Button size="sm" variant="outline" onClick={() => onMarkEvidence(item)}>标记证据</Button>}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!materials.length && <EmptyState text="暂无材料，请先上传合同、转账记录、聊天记录或主体资料。" />}
      </CardContent>
    </Card>
  );
}

function EvidenceTab({ evidences, onExport, onReinforce }: { evidences: CaseMaterialRecord[]; onExport: () => void; onReinforce: (m: CaseMaterialRecord) => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">证据目录</CardTitle><Button size="sm" variant="outline" onClick={onExport}><Download className="w-4 h-4 mr-1" />导出证据目录</Button></CardHeader>
      <CardContent className="space-y-3">
        {evidences.map((item) => (
          <div key={item.id} className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary">{item.material_no}</Badge>
              <span className="font-medium">{item.title}</span>
              {item.need_notarization && <Badge className="bg-amber-100 text-amber-700">建议公证/保全</Badge>}
            </div>
            <p className="text-sm text-slate-600"><span className="font-medium">证明目的：</span>{item.proof_purpose || '待补充'}</p>
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge variant="outline" className={evidenceClass(item.authenticity_status)}>真实性：{item.authenticity_status || '待核实'}</Badge>
              <Badge variant="outline" className={evidenceClass(item.relevance_status)}>关联性：{item.relevance_status || '待分析'}</Badge>
              <Badge variant="outline" className={evidenceClass(item.legality_status)}>合法性：{item.legality_status || '待核实'}</Badge>
            </div>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500">采信风险：{item.admissibility_risk || '待律师复核'}</p>
              <Button size="sm" variant="outline" onClick={() => onReinforce(item)}>生成补强任务</Button>
            </div>
          </div>
        ))}
        {!evidences.length && <EmptyState text="暂无证据。请在材料库上传材料并标记为证据。" />}
      </CardContent>
    </Card>
  );
}

function FactsTab({ facts, onAdd }: { facts: CaseFactRecord[]; onAdd: () => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">事实库</CardTitle><Button size="sm" onClick={onAdd}><Plus className="w-4 h-4 mr-1" />补充事实</Button></CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow><TableHead>编号</TableHead><TableHead>日期</TableHead><TableHead>事实</TableHead><TableHead>来源证据</TableHead><TableHead>置信度</TableHead><TableHead>矛盾提示</TableHead></TableRow></TableHeader>
          <TableBody>
            {facts.map((fact) => (
              <TableRow key={fact.id}>
                <TableCell className="font-mono text-xs">{fact.fact_no}</TableCell>
                <TableCell>{fact.event_date || '待核实'}</TableCell>
                <TableCell className="max-w-[360px]">{fact.fact_text}</TableCell>
                <TableCell>{fact.source_refs || <Badge variant="outline" className="text-amber-700">待核实</Badge>}</TableCell>
                <TableCell>{fact.confidence || '中'}</TableCell>
                <TableCell>{fact.contradiction_note || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!facts.length && <EmptyState text="暂无事实。可从材料解析后确认，也可手动补充。" />}
      </CardContent>
    </Card>
  );
}

function TimelineTab({ facts }: { facts: CaseFactRecord[] }) {
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">事实时间线</CardTitle></CardHeader>
      <CardContent>
        <div className="relative pl-6">
          <div className="absolute left-2 top-0 bottom-0 w-px bg-slate-200" />
          {facts.map((fact) => (
            <div key={fact.id} className="relative mb-4">
              <div className="absolute -left-[21px] top-1.5 h-3 w-3 rounded-full bg-slate-950 ring-4 ring-white" />
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="text-xs text-slate-500 mb-1">{fact.event_date || '时间待核实'} | {fact.fact_no}</div>
                <p className="text-sm text-slate-700">{fact.fact_text}</p>
                <p className="text-xs text-slate-500 mt-1">来源：{fact.source_refs || '待核实'}</p>
              </div>
            </div>
          ))}
        </div>
        {!facts.length && <EmptyState text="暂无时间线。" />}
      </CardContent>
    </Card>
  );
}

function ResearchTab({ query, setQuery, results, onRun, loading }: { query: string; setQuery: (v: string) => void; results: string[]; onRun: () => void; loading: boolean }) {
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">法律研究</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="输入争议焦点、法条关键词或类案方向" />
          <Button onClick={onRun} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {loading ? '分析中' : '开始检索'}
          </Button>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
          检索策略：法律、司法解释优先；指导性案例和人民法院案例库参考案例用于类案说理；普通裁判文书仅作参考。
        </div>
        <BulletList items={results} empty="暂无检索结果，请输入关键词后开始检索。" />
      </CardContent>
    </Card>
  );
}

function DocumentsTab({ documents, onOpenGenerate, onView }: { documents: GeneratedCaseDocument[]; onOpenGenerate: () => void; onView: (d: GeneratedCaseDocument) => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">文书</CardTitle><Button size="sm" onClick={onOpenGenerate}><Plus className="w-4 h-4 mr-1" />生成文书</Button></CardHeader>
      <CardContent className="space-y-3">
        {documents.map((doc) => (
          <div key={doc.id} className="rounded-lg border border-slate-200 p-3 bg-white">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1"><Badge variant="secondary">{doc.doc_type}</Badge><Badge variant="outline">{doc.status || '草稿'}</Badge></div>
                <h3 className="font-medium text-slate-800">{doc.title || doc.doc_type}</h3>
                <p className="text-xs text-slate-500 mt-1">{dateText(doc.created_at)}</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => onView(doc)}>查看</Button>
            </div>
          </div>
        ))}
        {!documents.length && <EmptyState text="暂无文书。可生成起诉状、答辩状、律师函、证据目录或案件分析报告。" />}
      </CardContent>
    </Card>
  );
}

function TasksTab({ tasks, onAdd, onToggle }: { tasks: CaseTaskRecord[]; onAdd: () => void; onToggle: (task: CaseTaskRecord) => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">任务/期限</CardTitle><Button size="sm" onClick={onAdd}><Plus className="w-4 h-4 mr-1" />新建任务</Button></CardHeader>
      <CardContent className="space-y-2">
        {tasks.map((task) => (
          <div key={task.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3">
            <div>
              <div className="font-medium text-sm">{task.title}</div>
              <div className="text-xs text-slate-500 mt-1">{task.assigned_to || '未分配'} | {task.due_date || '未设置期限'}</div>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={task.priority === '高' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'}>{task.priority || '中'}</Badge>
              <Button size="sm" variant="outline" onClick={() => onToggle(task)}>{task.status || '待开始'}</Button>
            </div>
          </div>
        ))}
        {!tasks.length && <EmptyState text="暂无任务。建议添加举证、开庭、补证、发函、回访等关键期限。" />}
      </CardContent>
    </Card>
  );
}

function TeamTab({ parties, teamMembers, onAdd }: { parties: CasePartyRecord[]; teamMembers?: string | null; onAdd: () => void }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between"><CardTitle className="text-base">团队协作 / 当事人</CardTitle><Button size="sm" onClick={onAdd}><Plus className="w-4 h-4 mr-1" />新增对象</Button></CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-700">团队成员：{teamMembers || '待配置主办律师、助理、客户可见范围'}</div>
        <Table>
          <TableHeader><TableRow><TableHead>名称</TableHead><TableHead>角色</TableHead><TableHead>身份类型</TableHead><TableHead>联系方式</TableHead><TableHead>代理人</TableHead></TableRow></TableHeader>
          <TableBody>
            {parties.map((party) => (
              <TableRow key={party.id}><TableCell>{party.name}</TableCell><TableCell>{party.party_type}</TableCell><TableCell>{party.identity_type}</TableCell><TableCell>{party.contact}</TableCell><TableCell>{party.lawyer}</TableCell></TableRow>
            ))}
          </TableBody>
        </Table>
        {!parties.length && <EmptyState text="暂无当事人信息。" />}
      </CardContent>
    </Card>
  );
}

function SettingsTab({ caseItem, setCaseItem, onSave, saving }: { caseItem: CaseRecord; setCaseItem: (c: CaseRecord) => void; onSave: () => void; saving: boolean }) {
  const update = (key: keyof CaseRecord, value: string) => setCaseItem({ ...caseItem, [key]: key === 'amount' ? Number(value) : value });
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">案件设置</CardTitle></CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-4">
        <Field label="案件名称" className="md:col-span-2"><Input value={caseItem.title} onChange={(e) => update('title', e.target.value)} /></Field>
        <Field label="案件阶段"><Input value={caseItem.stage || ''} onChange={(e) => update('stage', e.target.value)} /></Field>
        <Field label="风险等级"><Input value={caseItem.risk_level || ''} onChange={(e) => update('risk_level', e.target.value)} /></Field>
        <Field label="委托人"><Input value={caseItem.client_name || ''} onChange={(e) => update('client_name', e.target.value)} /></Field>
        <Field label="对方当事人"><Input value={caseItem.opposing_party || ''} onChange={(e) => update('opposing_party', e.target.value)} /></Field>
        <Field label="管辖法院/仲裁机构"><Input value={caseItem.court_or_arbitration || ''} onChange={(e) => update('court_or_arbitration', e.target.value)} /></Field>
        <Field label="关键期限"><Input value={caseItem.key_deadline || ''} onChange={(e) => update('key_deadline', e.target.value)} /></Field>
        <Field label="案件摘要" className="md:col-span-2"><Textarea rows={3} value={caseItem.summary || ''} onChange={(e) => update('summary', e.target.value)} /></Field>
        <Field label="争议焦点" className="md:col-span-2"><Textarea rows={3} value={caseItem.dispute_focus || ''} onChange={(e) => update('dispute_focus', e.target.value)} /></Field>
        <Field label="诉讼请求/目标" className="md:col-span-2"><Textarea rows={3} value={caseItem.claims || ''} onChange={(e) => update('claims', e.target.value)} /></Field>
        <div className="md:col-span-2 flex justify-end"><Button onClick={onSave} disabled={saving}>{saving ? '保存中...' : '保存设置'}</Button></div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-[12px] border border-dashed border-stone-950/20 bg-[#efebe1]/70 p-6 text-center text-sm text-stone-500">{text}</div>;
}
