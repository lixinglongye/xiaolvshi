import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '@/components/Layout';
import AuthGuard from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Download, ChevronDown, ChevronUp, Copy, Scale, ExternalLink,
  AlertTriangle, CheckCircle2, XCircle, Info, Shield, Clock,
  MapPin, Hash, Target, Lightbulb, AlertCircle, FileCheck, Gavel,
  BookOpen, FileText, User, Upload, Loader2, Sparkles, ArrowLeft,
} from 'lucide-react';
import { toast } from 'sonner';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import {
  mockDeepReport, sourceTypeConfig, verificationStatusConfig, riskLevelConfig,
  type DeepReviewReport, type RiskItemDetail, type LegalSource,
} from '@/lib/mockData';
import { analyzeDocument, downloadDeepReviewReport, getDeepReviewReport } from '@/lib/deepReviewApi';
import { mapAIReportToFrontend } from '@/lib/reportMapper';

export default function DeepReportPage() {
  return (<AuthGuard><Inner /></AuthGuard>);
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => toast.success('已复制到剪贴板'));
}

const riskIcons: Record<string, React.ReactNode> = {
  critical: <XCircle className="w-4 h-4" />,
  high: <AlertTriangle className="w-4 h-4" />,
  medium: <Info className="w-4 h-4" />,
  low: <CheckCircle2 className="w-4 h-4" />,
};

function riskLevelKey(level?: string): 'critical' | 'high' | 'medium' | 'low' {
  if (level === '重大' || level === 'critical') return 'critical';
  if (level === '高' || level === 'high') return 'high';
  if (level === '低' || level === 'low') return 'low';
  return 'medium';
}

function sourceCoverageStatus(ratio?: number): string {
  if ((ratio ?? 0) >= 0.8) return '依据核验覆盖较充分';
  if ((ratio ?? 0) > 0) return '部分依据已核验';
  return '待补充已校验依据';
}

function LegalEffectBadge({ source }: { source: LegalSource }) {
  const cfg = sourceTypeConfig[source.source_type];
  const vCfg = verificationStatusConfig[source.verification_status] || verificationStatusConfig['待核验'];
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      <Badge className={`text-xs ${cfg?.color || 'bg-gray-500 text-white'}`}>{cfg?.label || source.source_type}</Badge>
      <Badge variant="outline" className={`text-xs ${vCfg.color}`}>{vCfg.label}</Badge>
      <span className="text-xs text-slate-500">{source.authority_level}</span>
      {source.confidence > 0 && <span className="text-xs text-slate-400">置信度 {source.confidence}%</span>}
    </div>
  );
}

function LegalSourceCard({ source, compact = false }: { source: LegalSource; compact?: boolean }) {
  const title = source.title?.trim() || '未命名法律依据';
  const articleNumber = source.article_number?.trim() || '条文待补';
  const excerpt = source.text_excerpt?.trim() || '暂无条文摘录，请以权威法库复核为准。';

  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white space-y-2 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Scale className="w-4 h-4 text-blue-600 shrink-0" />
          <span className="font-medium text-sm text-slate-800 truncate">{title}</span>
          <span className="text-xs text-slate-500 shrink-0">{articleNumber}</span>
        </div>
        {source.source_url && (
          <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 shrink-0">
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
      <LegalEffectBadge source={source} />
      <div className="text-xs text-slate-600 italic border-l-2 border-blue-300 pl-2 bg-blue-50/50 py-1 rounded-r">
        &ldquo;{excerpt}&rdquo;
      </div>
      {!compact && (
        <>
          <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
            <span>发布机关：{source.issuing_body}</span>
            <span>效力说明：{source.legal_effect_note}</span>
          </div>
          {source.applicability_reason && (
            <div className="text-xs text-slate-700 bg-amber-50 border border-amber-100 rounded p-2">
              <span className="font-medium text-amber-800">适用理由：</span>{source.applicability_reason}
            </div>
          )}
        </>
      )}
    </div>
  );
}

const tocSections = [
  { id: 'cover', label: '报告封面' },
  { id: 'executive-summary', label: '执行摘要' },
  { id: 'review-framework', label: '审查框架' },
  { id: 'contract-structure', label: '合同结构' },
  { id: 'risk-matrix', label: '风险矩阵' },
  { id: 'risk-analysis', label: '逐条分析' },
  { id: 'missing-clauses', label: '缺失条款' },
  { id: 'favorable-clauses', label: '有利条款' },
  { id: 'pending-facts', label: '待补事实' },
  { id: 'legal-appendix', label: '法律依据附录' },
  { id: 'disclaimer-section', label: '免责声明' },
];

function Sidebar({ activeSection }: { activeSection: string }) {
  return (
    <nav className="sticky top-20 space-y-1">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-3">报告目录</h3>
      {tocSections.map((s) => (
        <a key={s.id} href={`#${s.id}`}
          className={`block px-3 py-2 text-sm rounded-full transition-colors ${activeSection === s.id ? 'bg-white text-slate-950 font-medium shadow-sm ring-1 ring-slate-200' : 'text-slate-600 hover:bg-white/70 hover:text-slate-950'}`}
        >{s.label}</a>
      ))}
    </nav>
  );
}

function RiskItemCard({ item }: { item: RiskItemDetail }) {
  const [expanded, setExpanded] = useState(false);
  const [clauseVersion, setClauseVersion] = useState<'conservative' | 'balanced' | 'bottom_line'>('conservative');
  const lvl = riskLevelConfig[item.risk_level];
  const versions = {
    conservative: { label: '保守版（最大保护）', text: item.revision_plan.conservative_clause },
    balanced: { label: '平衡版', text: item.revision_plan.balanced_clause },
    bottom_line: { label: '底线版', text: item.revision_plan.bottom_line_clause },
  };

  return (
    <div className={`border-l-4 rounded-lg border ${lvl.bgColor} overflow-hidden`}>
      <Collapsible open={expanded} onOpenChange={setExpanded}>
        <CollapsibleTrigger asChild>
          <div className="p-4 cursor-pointer hover:bg-white/50 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge className={`text-xs ${lvl.color}`}>{riskIcons[item.risk_level]}<span className="ml-1">{lvl.label}</span></Badge>
                  <Badge variant="outline" className="text-xs">{item.risk_type}</Badge>
                  <span className="text-xs text-slate-500">{item.risk_no}</span>
                  <span className="text-xs text-slate-400">P{item.priority}</span>
                  {typeof item.risk_score === 'number' && (
                    <Badge variant="outline" className="text-xs bg-white/70">评分 {item.risk_score}</Badge>
                  )}
                  {typeof item.evidence_confidence_score === 'number' && (
                    <span className="text-xs text-slate-500">证据信心 {item.evidence_confidence_score}</span>
                  )}
                </div>
                <h4 className="font-semibold text-slate-800 text-sm">{item.title}</h4>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 flex-wrap">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{item.clause_location}{item.page_number > 0 && ` (第${item.page_number}页)`}</span>
                  <span className="flex items-center gap-1"><Target className="w-3 h-3" />概率: {item.probability}</span>
                  <span className="flex items-center gap-1"><AlertCircle className="w-3 h-3" />严重度: {item.severity}</span>
                </div>
              </div>
              <div className="shrink-0">{expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}</div>
            </div>
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-4 border-t border-slate-100 pt-4">
            {/* Original Clause */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><FileText className="w-3.5 h-3.5" />原条款摘录</h5>
              <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-slate-700 italic">
                &ldquo;{item.original_clause_text}&rdquo;
                <div className="mt-1 text-xs text-red-600 font-medium">问题定位：{item.issue_location}</div>
              </div>
            </div>

            {/* Legal Analysis */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><Gavel className="w-3.5 h-3.5" />律师式法律分析</h5>
              <div className="bg-slate-50 rounded-lg p-3 space-y-2 text-sm">
                <div><span className="font-medium text-slate-700">法律关系定性：</span><span className="text-slate-600">{item.legal_analysis.legal_relationship}</span></div>
                <div><span className="font-medium text-slate-700">适用规则：</span><span className="text-slate-600">{item.legal_analysis.applicable_rule}</span></div>
                <div><span className="font-medium text-slate-700">规则适用于本条款：</span><span className="text-slate-600">{item.legal_analysis.application_to_clause}</span></div>
                <div><span className="font-medium text-slate-700">对承租方的影响：</span><span className="text-red-700">{item.legal_analysis.user_impact}</span></div>
                <div><span className="font-medium text-slate-700">相对方可能抗辩：</span><span className="text-slate-600">{item.legal_analysis.counterparty_argument}</span></div>
                <div><span className="font-medium text-slate-700">法院/仲裁关注点：</span><span className="text-slate-600">{item.legal_analysis.court_focus}</span></div>
                <div><span className="font-medium text-slate-700">举证责任：</span><span className="text-slate-600">{item.legal_analysis.burden_of_proof}</span></div>
              </div>
            </div>

            {/* Legal Sources */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" />法律依据 ({item.legal_sources.length}条)</h5>
              <div className="space-y-2">
                {item.legal_sources.map((s) => <LegalSourceCard key={s.source_id} source={s} />)}
              </div>
            </div>

            {/* Revision Plan */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><Lightbulb className="w-3.5 h-3.5" />修改方案</h5>
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 space-y-2 text-sm">
                {item.revision_plan.delete_items.length > 0 && (
                  <div><span className="font-medium text-red-700">建议删除：</span>{item.revision_plan.delete_items.map((d, i) => <Badge key={i} variant="outline" className="text-xs ml-1 text-red-700 border-red-200">{d}</Badge>)}</div>
                )}
                {item.revision_plan.add_items.length > 0 && (
                  <div><span className="font-medium text-green-700">建议新增：</span>{item.revision_plan.add_items.map((a, i) => <Badge key={i} variant="outline" className="text-xs ml-1 text-green-700 border-green-200">{a}</Badge>)}</div>
                )}
                {item.revision_plan.replace_items.length > 0 && (
                  <div><span className="font-medium text-blue-700">建议替换：</span>{item.revision_plan.replace_items.map((r, i) => <Badge key={i} variant="outline" className="text-xs ml-1 text-blue-700 border-blue-200">{r}</Badge>)}</div>
                )}
              </div>
            </div>

            {/* Alternative Clauses - 3 versions */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><FileCheck className="w-3.5 h-3.5" />替代条款（三版本）</h5>
              <Tabs value={clauseVersion} onValueChange={(v) => setClauseVersion(v as typeof clauseVersion)}>
                <TabsList className="grid grid-cols-3 w-full">
                  <TabsTrigger value="conservative" className="text-xs">保守版</TabsTrigger>
                  <TabsTrigger value="balanced" className="text-xs">平衡版</TabsTrigger>
                  <TabsTrigger value="bottom_line" className="text-xs">底线版</TabsTrigger>
                </TabsList>
                {(Object.keys(versions) as Array<keyof typeof versions>).map((k) => (
                  <TabsContent key={k} value={k}>
                    <div className="bg-green-50 border border-green-100 rounded-lg p-3 relative">
                      <p className="text-sm text-slate-700 whitespace-pre-wrap">{versions[k].text}</p>
                      <Button variant="ghost" size="sm" className="absolute top-2 right-2 h-7 text-xs" onClick={() => copyText(versions[k].text)}>
                        <Copy className="w-3 h-3 mr-1" />复制
                      </Button>
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </div>

            {/* Negotiation Strategy */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><User className="w-3.5 h-3.5" />谈判策略</h5>
              <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 text-sm text-slate-700 whitespace-pre-wrap">{item.negotiation_strategy}</div>
            </div>

            {/* Evidence Suggestions */}
            <div>
              <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1"><Shield className="w-3.5 h-3.5" />证据保存建议</h5>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1 bg-slate-50 rounded-lg p-3">
                {item.evidence_suggestions.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>

            {/* Status */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">处理状态：</span>
                <Badge variant="outline" className="text-xs">{item.status}</Badge>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="text-xs h-7">已采纳</Button>
                <Button variant="outline" size="sm" className="text-xs h-7">暂缓</Button>
                <Button variant="outline" size="sm" className="text-xs h-7 text-orange-600 border-orange-200">需律师复核</Button>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Main Report Page
// ═══════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════
// Upload Form Component
// ═══════════════════════════════════════════════════════════

interface UploadFormProps {
  onReportGenerated: (report: DeepReviewReport) => void;
  onUseMockData: () => void;
}

function UploadForm({ onReportGenerated, onUseMockData }: UploadFormProps) {
  const [documentText, setDocumentText] = useState('');
  const [documentType, setDocumentType] = useState('合同');
  const [userRole, setUserRole] = useState('甲方');
  const [reviewGoal, setReviewGoal] = useState('签署前审查');
  const [knownFacts, setKnownFacts] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const progressSteps = [
    { pct: 10, text: 'Intake Agent: 识别文书基础信息...' },
    { pct: 20, text: 'Clause Mapping Agent: 切分条款结构...' },
    { pct: 35, text: 'Issue Spotter Agent: 识别风险与缺失条款...' },
    { pct: 50, text: 'Legal Research Agent: 检索法律依据...' },
    { pct: 65, text: 'Citation Validator Agent: 校验引用准确性...' },
    { pct: 75, text: 'Senior Lawyer Review Agent: 资深律师复核...' },
    { pct: 85, text: 'Drafting Agent: 生成替代条款三版本...' },
    { pct: 95, text: 'Report Assembly Agent: 组装最终报告...' },
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const textTypes = ['text/plain', 'text/markdown', 'application/json'];
    const textExtensions = ['.txt', '.md', '.json', '.csv'];
    const isTextFile = textTypes.includes(file.type) || textExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (isTextFile) {
      const text = await file.text();
      setDocumentText(text);
      toast.success(`已加载文件: ${file.name}（${text.length} 字）`);
    } else if (file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc')) {
      toast.error('暂不支持直接解析 PDF/Word 文件，请将文书内容复制粘贴到下方文本框中');
    } else {
      toast.error('不支持该文件格式，请将文书内容粘贴到文本框中');
    }
    // Reset input so the same file can be re-uploaded
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    if (!documentText || documentText.trim().length < 50) {
      toast.error('请输入至少50字的法律文书内容');
      return;
    }

    setIsLoading(true);
    setProgress(0);
    setProgressText('正在初始化 Agent Team...');

    // Simulate progress steps while waiting for AI
    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < progressSteps.length) {
        setProgress(progressSteps[stepIndex].pct);
        setProgressText(progressSteps[stepIndex].text);
        stepIndex++;
      }
    }, 3000);

    try {
      const factsArray = knownFacts.trim()
        ? knownFacts.split('\n').filter(f => f.trim())
        : [];

      const response = await analyzeDocument({
        document_text: documentText,
        document_type: documentType,
        user_role: userRole,
        review_goal: reviewGoal,
        known_facts: factsArray,
        jurisdiction: '中国大陆',
      });

      clearInterval(interval);

      if (response.success && response.report) {
        setProgress(100);
        setProgressText('报告生成完成！');
        const frontendReport = mapAIReportToFrontend(response.report);
        setTimeout(() => {
          onReportGenerated(frontendReport);
          toast.success('深度审查报告已生成');
        }, 500);
      } else {
        setProgress(0);
        setProgressText('');
        // Show specific error message - especially for non-legal document detection
        const errorMsg = response.error || '报告生成失败，请重试';
        if (errorMsg.includes('不属于法律') || errorMsg.includes('无法进行法律审查')) {
          toast.error(errorMsg, { duration: 8000 });
        } else {
          toast.error(errorMsg);
        }
      }
    } catch {
      clearInterval(interval);
      setProgress(0);
      setProgressText('');
      toast.error('网络错误，请检查连接后重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <DisclaimerBanner />

        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-full">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">AI 深度法律审查</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">上传法律文书，获取深度审查报告</h1>
          <p className="text-slate-500 max-w-2xl mx-auto">
            8位AI Agent协同工作：文书识别 → 条款切分 → 风险识别 → 法律检索 → 引用校验 → 律师复核 → 条款起草 → 报告组装
          </p>
        </div>

        {/* Upload Card */}
        <Card className="border-blue-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-600" />
              文书内容
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* File Upload */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                <Upload className="w-4 h-4 mr-1" />选择文件
              </Button>
              <span className="text-xs text-slate-500">支持 .txt / .md 文件，或直接粘贴文书内容</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md"
                className="hidden"
                onChange={handleFileUpload}
              />
            </div>

            {/* Text Area */}
            <textarea
              className="w-full h-64 border border-slate-200 rounded-lg p-4 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="请在此粘贴完整的法律文书内容（合同、协议、律师函、起诉状等）...&#10;&#10;至少需要50字以上的文书内容才能进行深度审查。"
              value={documentText}
              onChange={(e) => setDocumentText(e.target.value)}
              disabled={isLoading}
            />
            <div className="text-xs text-slate-400 text-right">
              已输入 {documentText.length} 字
            </div>
          </CardContent>
        </Card>

        {/* Configuration Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-600" />
              审查配置
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">文书类型</label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="合同">合同/协议</option>
                  <option value="起诉状">起诉状</option>
                  <option value="答辩状">答辩状</option>
                  <option value="律师函">律师函</option>
                  <option value="仲裁申请书">仲裁申请书</option>
                  <option value="代理词">代理词</option>
                  <option value="其他">其他法律文书</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">您的角色</label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={userRole}
                  onChange={(e) => setUserRole(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="甲方">甲方</option>
                  <option value="乙方">乙方</option>
                  <option value="承租方">承租方</option>
                  <option value="出租方">出租方</option>
                  <option value="买方">买方</option>
                  <option value="卖方">卖方</option>
                  <option value="公司">公司</option>
                  <option value="员工">员工</option>
                  <option value="原告">原告</option>
                  <option value="被告">被告</option>
                  <option value="其他">其他</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">审查目标</label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={reviewGoal}
                  onChange={(e) => setReviewGoal(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="签署前审查">签署前审查</option>
                  <option value="争议处理">争议处理</option>
                  <option value="律师复核前初审">律师复核前初审</option>
                  <option value="合规审查">合规审查</option>
                </select>
              </div>
            </div>

            {/* Known Facts */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-slate-700 mb-1">已知事实（可选，每行一条）</label>
              <textarea
                className="w-full h-24 border border-slate-200 rounded-lg p-3 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：&#10;合同签署日期为2024年3月1日&#10;甲方已支付首期款项50万元&#10;乙方尚未完成交付"
                value={knownFacts}
                onChange={(e) => setKnownFacts(e.target.value)}
                disabled={isLoading}
              />
            </div>
          </CardContent>
        </Card>

        {/* Progress */}
        {isLoading && (
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="py-6">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  <span className="text-sm font-medium text-blue-800">{progressText}</span>
                </div>
                <div className="w-full bg-blue-100 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-blue-600">
                  AI Agent Team 正在协同工作，深度审查通常需要 30-60 秒...
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Submit */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={onUseMockData}
            disabled={isLoading}
            className="text-slate-500 hover:text-slate-700"
          >
            <FileText className="w-4 h-4 mr-1" />查看演示报告（租赁合同样例）
          </Button>
          <Button
            className="bg-blue-600 hover:bg-blue-700 text-white px-8"
            onClick={handleSubmit}
            disabled={isLoading || documentText.trim().length < 50}
          >
            {isLoading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />生成中...</>
            ) : (
              <><Sparkles className="w-4 h-4 mr-2" />开始深度审查</>
            )}
          </Button>
        </div>
      </div>
    </Layout>
  );
}

// ═══════════════════════════════════════════════════════════
// Main Report Page
// ═══════════════════════════════════════════════════════════

function Inner() {
  const { id } = useParams();
  const [mode, setMode] = useState<'upload' | 'report'>(id ? 'report' : 'upload');
  const [report, setReport] = useState<DeepReviewReport | null>(id ? null : mockDeepReport);
  const [loadingReport, setLoadingReport] = useState(Boolean(id));
  const [loadError, setLoadError] = useState('');
  const [activeSection, setActiveSection] = useState('cover');
  const mainRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback(() => {
    if (!mainRef.current) return;
    const sections = tocSections.map(s => document.getElementById(s.id)).filter(Boolean);
    for (let i = sections.length - 1; i >= 0; i--) {
      const el = sections[i];
      if (el && el.getBoundingClientRect().top <= 120) {
        setActiveSection(tocSections[i].id);
        break;
      }
    }
  }, []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoadingReport(true);
    setLoadError('');
    getDeepReviewReport(id).then((response) => {
      if (cancelled) return;
      if (response.success && response.report) {
        setReport(mapAIReportToFrontend(response.report));
        setMode('report');
      } else {
        setLoadError(response.error || '深度审查报告加载失败');
      }
    }).catch((error) => {
      if (!cancelled) {
        setLoadError(error instanceof Error ? error.message : '深度审查报告加载失败');
      }
    }).finally(() => {
      if (!cancelled) setLoadingReport(false);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleReportGenerated = (newReport: DeepReviewReport) => {
    setReport(newReport);
    setMode('report');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleUseMockData = () => {
    setReport(mockDeepReport);
    setMode('report');
  };

  const handleBackToUpload = () => {
    setMode('upload');
  };

  const handleDownload = async (format: 'pdf' | 'doc' | 'md' | 'json') => {
    if (!id) {
      toast.error('当前报告尚未保存，无法直接下载。请从上传页生成持久化报告后下载。');
      return;
    }
    try {
      await downloadDeepReviewReport(id, format);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '下载失败');
    }
  };

  if (loadingReport) {
    return (
      <Layout>
        <div className="min-h-[50vh] flex flex-col items-center justify-center text-slate-600">
          <Loader2 className="w-8 h-8 animate-spin text-blue-700 mb-3" />
          <div className="text-sm">正在加载深度审查报告...</div>
        </div>
      </Layout>
    );
  }

  if (loadError) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto px-4 py-16">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6">
              <div className="font-semibold text-red-800 mb-2">报告加载失败</div>
              <div className="text-sm text-red-700">{loadError}</div>
              <Button className="mt-4" variant="outline" onClick={handleBackToUpload}>新建审查</Button>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  // Show upload form
  if (mode === 'upload') {
    return <UploadForm onReportGenerated={handleReportGenerated} onUseMockData={handleUseMockData} />;
  }

  if (!report) {
    return null;
  }

  const signRecConfig: Record<string, { label: string; color: string }> = {
    '修改后签署': { label: '建议修改后签署', color: 'text-amber-700 bg-amber-50 border-amber-200' },
    '建议签署': { label: '建议直接签署', color: 'text-green-700 bg-green-50 border-green-200' },
    '可签署': { label: '可直接签署', color: 'text-green-700 bg-green-50 border-green-200' },
    '谨慎签署': { label: '谨慎签署', color: 'text-orange-700 bg-orange-50 border-orange-200' },
    '不建议签署': { label: '不建议签署', color: 'text-red-700 bg-red-50 border-red-200' },
    '不建议直接签署': { label: '不建议直接签署', color: 'text-red-700 bg-red-50 border-red-200' },
  };
  const signRec = signRecConfig[report.executive_summary.signing_recommendation] || signRecConfig['修改后签署'];
  const framework = report.professional_review_framework ?? {
    document_type: report.contract_basic_info.contract_type,
    matter_type: '合同审查',
    must_review_dimensions: [],
    required_fields: [],
    evidence_checklist: [],
    lawyer_review_triggers: [],
  };
  const coverage = report.coverage_audit;
  const quality = report.quality_audit;
  const qualityGate = report.quality_gate;
  const citationAudit = report.citation_audit;
  const evidenceAudit = report.evidence_audit;
  const releaseDecision = report.release_decision;
  const riskScoring = report.risk_scoring;
  const delivery = report.delivery_audit;
  const humanWorkflow = report.human_review_workflow;
  const overallRisk = riskLevelConfig[riskLevelKey(report.executive_summary.overall_risk_level)];

  return (
    <Layout>
        <div className="flex gap-6 max-w-7xl mx-auto px-4 py-6">
        {/* Left Sidebar */}
        <aside className="hidden lg:block w-52 shrink-0">
          <Sidebar activeSection={activeSection} />
          <div className="mt-4">
            <Button variant="outline" size="sm" className="w-full" onClick={handleBackToUpload}>
              <ArrowLeft className="w-4 h-4 mr-1" />新建审查
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main ref={mainRef} className="flex-1 min-w-0 space-y-8">
          <DisclaimerBanner />

          {/* ═══ Section 1: Cover ═══ */}
          <section id="cover">
            <Card className="surface-card">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <CardTitle className="text-xl text-slate-950 flex items-center gap-2"><Shield className="w-6 h-6 text-emerald-800" />深度法律审查报告</CardTitle>
                    <p className="text-sm text-slate-500 mt-1">报告编号：{report.report_no} | 生成时间：{report.generated_at} | 版本：{report.version}</p>
                  </div>
                  <Button variant="outline" size="sm" className="no-print soft-button rounded-full" onClick={() => handleDownload('pdf')}><Download className="w-4 h-4 mr-1" />下载报告</Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                  <div><span className="text-slate-500">合同类型：</span><span className="font-medium">{report.contract_basic_info.contract_type}</span></div>
                  <div><span className="text-slate-500">合同名称：</span><span className="font-medium">{report.contract_basic_info.contract_name}</span></div>
                  <div><span className="text-slate-500">审查立场：</span><Badge variant="secondary">{report.contract_basic_info.user_role}</Badge></div>
                  <div><span className="text-slate-500">甲方：</span><span>{report.contract_basic_info.party_a}</span></div>
                  <div><span className="text-slate-500">乙方：</span><span>{report.contract_basic_info.party_b}</span></div>
                  <div><span className="text-slate-500">合同金额：</span><span className="font-medium text-blue-700">{report.contract_basic_info.amount}</span></div>
                  <div><span className="text-slate-500">合同期限：</span><span>{report.contract_basic_info.term}</span></div>
                  <div><span className="text-slate-500">履行地点：</span><span>{report.contract_basic_info.performance_location}</span></div>
                  <div><span className="text-slate-500">争议解决：</span><span>{report.contract_basic_info.dispute_resolution}（{report.contract_basic_info.jurisdiction}）</span></div>
                  <div><span className="text-slate-500">付款方式：</span><span>{report.contract_basic_info.payment_method}</span></div>
                  <div><span className="text-slate-500">页数/条款：</span><span>{report.contract_basic_info.pages}页 / {report.contract_basic_info.total_clauses}条</span></div>
                  <div><span className="text-slate-500">法域：</span><span>中国大陆</span></div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 2: Executive Summary ═══ */}
          <section id="executive-summary">
            <Card className="surface-card">
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Hash className="w-5 h-5 text-emerald-800" />执行摘要</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
                  <div className="text-center p-3 bg-[#fbfbf8] rounded-lg border border-slate-200/80">
                    <Badge className={`text-sm ${overallRisk?.color || 'bg-orange-500 text-white'}`}>{report.executive_summary.overall_risk_level}</Badge>
                    <div className="text-xs text-slate-500 mt-1">总体风险等级</div>
                  </div>
                  <div className="text-center p-3 bg-[#fbfbf8] rounded-lg border border-slate-200/80">
                    <div className="text-2xl font-semibold text-slate-900">{typeof riskScoring?.overall_score === 'number' ? riskScoring.overall_score : '-'}</div>
                    <div className="text-xs text-slate-500 mt-1">确定性风险评分</div>
                  </div>
                  <div className="text-center p-3 bg-[#fbfbf8] rounded-lg border border-slate-200/80">
                    <div className="text-2xl font-semibold text-slate-900">{typeof releaseDecision?.readiness_score === 'number' ? releaseDecision.readiness_score : '-'}</div>
                    <div className="text-xs text-slate-500 mt-1">交付就绪分</div>
                  </div>
                  <div className="text-center p-3 bg-[#fbfbf8] rounded-lg border border-slate-200/80">
                    <Badge className={`text-sm border ${signRec.color}`}>{signRec.label}</Badge>
                    <div className="text-xs text-slate-500 mt-1">签署建议</div>
                  </div>
                  <div className="text-center p-3 bg-[#fbfbf8] rounded-lg border border-slate-200/80">
                    <div className="text-sm font-medium text-orange-700">{report.executive_summary.lawyer_review_recommended ? '建议律师复核' : '无需复核'}</div>
                    <div className="text-xs text-slate-500 mt-1">律师复核建议</div>
                  </div>
                </div>

                <div className="bg-[#fbfbf8] border border-slate-200/80 rounded-lg p-4 text-sm text-slate-700 whitespace-pre-wrap">{report.executive_summary.summary_text}</div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="text-sm font-semibold text-red-700 mb-2">Top 5 核心风险</h5>
                    <ol className="list-decimal list-inside text-sm text-slate-600 space-y-1">
                      {report.executive_summary.top5_risks.map((r, i) => <li key={i}>{r}</li>)}
                    </ol>
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-blue-700 mb-2">Top 5 优先修改事项</h5>
                    <ol className="list-decimal list-inside text-sm text-slate-600 space-y-1">
                      {report.executive_summary.top5_modifications.map((m, i) => <li key={i}>{m}</li>)}
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Professional Review Framework ═══ */}
          {framework && (
            <section id="review-framework">
              <Card className="surface-card">
                <CardHeader><CardTitle className="text-lg flex items-center gap-2"><FileCheck className="w-5 h-5 text-emerald-800" />专业审查框架</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                    <div className="bg-slate-50 rounded-lg p-3"><span className="text-slate-500">审查策略：</span><span className="font-medium">{framework.document_type || coverage?.strategy_name || '通用审查'}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="text-slate-500">事项类型：</span><span className="font-medium">{framework.matter_type || '法律文书'}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="text-slate-500">交付状态：</span><span className="font-medium">{delivery?.readiness_level || quality?.quality_level || '待律师复核'}</span></div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="text-sm font-semibold text-slate-700 mb-2">必审维度</h5>
                      <div className="flex flex-wrap gap-1.5">
                        {(framework.must_review_dimensions || []).map((item) => <Badge key={item} variant="outline" className="text-xs">{item}</Badge>)}
                      </div>
                    </div>
                    <div>
                      <h5 className="text-sm font-semibold text-slate-700 mb-2">必备字段</h5>
                      <div className="flex flex-wrap gap-1.5">
                        {(framework.required_fields || []).map((item) => <Badge key={item} className="text-xs bg-blue-50 text-blue-700 border border-blue-200">{item}</Badge>)}
                      </div>
                    </div>
                    <div>
                      <h5 className="text-sm font-semibold text-slate-700 mb-2">证据清单</h5>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        {(framework.evidence_checklist || []).slice(0, 8).map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                    <div>
                      <h5 className="text-sm font-semibold text-slate-700 mb-2">律师复核触发项</h5>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        {(framework.lawyer_review_triggers || []).slice(0, 8).map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                  </div>

                  {quality?.warnings && quality.warnings.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                      <span className="font-medium">质量提示：</span>{quality.warnings[0]}
                    </div>
                  )}

                  {releaseDecision && (
                    <div className={`rounded-lg border p-4 text-sm space-y-3 ${
                      releaseDecision.status === 'ready_for_spot_check'
                        ? 'border-emerald-200 bg-emerald-50/80 text-emerald-950'
                        : releaseDecision.status === 'lawyer_review_required'
                          ? 'border-amber-200 bg-amber-50/80 text-amber-950'
                          : 'border-red-200 bg-red-50/80 text-red-950'
                    }`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <div className="font-semibold text-base">交付决策</div>
                          <div className="text-slate-700 mt-1">{releaseDecision.summary || '等待审计汇总。'}</div>
                        </div>
                        <Badge variant="outline" className="bg-white/80">
                          {(releaseDecision.status || 'unknown').replace(/_/g, ' ')} / {releaseDecision.readiness_score ?? 0}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-700">
                        <div>交付：{releaseDecision.client_delivery_allowed ? '允许' : '暂缓'}</div>
                        <div>复核：{releaseDecision.lawyer_review_required ? '必须' : '抽检'}</div>
                        <div>分级：{releaseDecision.triage_level || 'normal'}</div>
                        <div>层级：{releaseDecision.release_level || 'unknown'}</div>
                      </div>
                      {(releaseDecision.blocking_reasons || []).length > 0 && (
                        <ul className="text-slate-700 space-y-1 list-disc list-inside">
                          {(releaseDecision.blocking_reasons || []).slice(0, 3).map((reason) => <li key={reason}>{reason}</li>)}
                        </ul>
                      )}
                      {(releaseDecision.required_actions || []).length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {(releaseDecision.required_actions || []).slice(0, 5).map((action) => <Badge key={action} variant="outline" className="bg-white/80 text-xs">{action}</Badge>)}
                        </div>
                      )}
                    </div>
                  )}

                  {qualityGate && (
                    <div className={`rounded-lg border p-3 text-sm space-y-2 ${
                      qualityGate.status === 'pass'
                        ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900'
                        : qualityGate.status === 'warn'
                          ? 'border-amber-200 bg-amber-50/70 text-amber-900'
                          : 'border-red-200 bg-red-50/70 text-red-900'
                    }`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-semibold">Quality Gate</div>
                        <Badge variant="outline" className="bg-white/80">
                          {(qualityGate.status || 'unknown').toUpperCase()} / {qualityGate.score ?? 0}
                        </Badge>
                      </div>
                      <div className="text-slate-700">Release level: {qualityGate.release_level || 'not evaluated'}</div>
                      {(qualityGate.blocking_gate_ids || []).length > 0 && (
                        <div className="text-slate-700">
                          Blocking gates: {(qualityGate.blocking_gate_ids || []).join(', ')}
                        </div>
                      )}
                      {(qualityGate.warning_gate_ids || []).length > 0 && (
                        <div className="text-slate-700">
                          Warning gates: {(qualityGate.warning_gate_ids || []).join(', ')}
                        </div>
                      )}
                    </div>
                  )}

                  {citationAudit && (
                    <div className={`rounded-lg border p-3 text-sm space-y-2 ${
                      citationAudit.status === 'pass'
                        ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900'
                        : citationAudit.status === 'warn'
                          ? 'border-amber-200 bg-amber-50/70 text-amber-900'
                          : 'border-red-200 bg-red-50/70 text-red-900'
                    }`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-semibold">引用审计</div>
                        <Badge variant="outline" className="bg-white/80">
                          {(citationAudit.status || 'unknown').toUpperCase()} / {citationAudit.score ?? 0}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-700">
                        <div>来源：{citationAudit.source_count ?? 0}</div>
                        <div>引用：{citationAudit.citation_count ?? 0}</div>
                        <div>已核验：{Math.round((citationAudit.verified_ratio ?? 0) * 100)}%</div>
                        <div>可复核：{Math.round((citationAudit.reviewable_ratio ?? 0) * 100)}%</div>
                      </div>
                      {(citationAudit.high_risk_without_reviewable_citation || []).length > 0 && (
                        <div className="text-slate-700">
                          高风险缺少可复核引用：{(citationAudit.high_risk_without_reviewable_citation || []).join(', ')}
                        </div>
                      )}
                      {(citationAudit.recommended_actions || []).length > 0 && (
                        <ul className="text-slate-700 space-y-1 list-disc list-inside">
                          {(citationAudit.recommended_actions || []).slice(0, 3).map((action) => <li key={action}>{action}</li>)}
                        </ul>
                      )}
                    </div>
                  )}

                  {evidenceAudit && (
                    <div className={`rounded-lg border p-3 text-sm space-y-2 ${
                      evidenceAudit.status === 'pass'
                        ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900'
                        : evidenceAudit.status === 'warn'
                          ? 'border-amber-200 bg-amber-50/70 text-amber-900'
                          : 'border-red-200 bg-red-50/70 text-red-900'
                    }`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-semibold">证据审计</div>
                        <Badge variant="outline" className="bg-white/80">
                          {(evidenceAudit.status || 'unknown').toUpperCase()} / {evidenceAudit.score ?? 0}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-700">
                        <div>证据覆盖：{Math.round((evidenceAudit.risk_evidence_coverage ?? 0) * 100)}%</div>
                        <div>建议数：{evidenceAudit.evidence_suggestion_count ?? 0}</div>
                        <div>待补事实：{evidenceAudit.pending_fact_count ?? 0}</div>
                        <div>阻断事实：{evidenceAudit.blocking_pending_fact_count ?? 0}</div>
                      </div>
                      {(evidenceAudit.high_risk_without_evidence_plan || []).length > 0 && (
                        <div className="text-slate-700">
                          高风险缺少证据计划：{(evidenceAudit.high_risk_without_evidence_plan || []).join(', ')}
                        </div>
                      )}
                      {(evidenceAudit.recommended_actions || []).length > 0 && (
                        <ul className="text-slate-700 space-y-1 list-disc list-inside">
                          {(evidenceAudit.recommended_actions || []).slice(0, 3).map((action) => <li key={action}>{action}</li>)}
                        </ul>
                      )}
                    </div>
                  )}

                  {(delivery || humanWorkflow) && (
                    <div className="grid md:grid-cols-2 gap-4">
                      {delivery && (
                        <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-3 text-sm space-y-2">
                          <div className="font-semibold text-emerald-900">交付审计</div>
                          <div className="text-slate-700">状态：{delivery.readiness_level || '待评估'}</div>
                          <div className="text-slate-700">{sourceCoverageStatus(delivery.verified_source_ratio)}</div>
                          {typeof delivery.reviewable_source_ratio === 'number' && (
                            <div className="text-slate-700">可复核来源：{Math.round(delivery.reviewable_source_ratio * 100)}%</div>
                          )}
                          {typeof delivery.risk_evidence_coverage === 'number' && (
                            <div className="text-slate-700">证据计划覆盖：{Math.round(delivery.risk_evidence_coverage * 100)}%</div>
                          )}
                          <div className="flex flex-wrap gap-1.5">
                            {(delivery.reviewable_artifacts || []).slice(0, 6).map((item) => <Badge key={item} variant="outline" className="text-xs bg-white">{item}</Badge>)}
                          </div>
                        </div>
                      )}
                      {humanWorkflow && (
                        <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-3 text-sm space-y-2">
                          <div className="font-semibold text-blue-900">人工复核任务包</div>
                          <div className="text-slate-700">状态：{humanWorkflow.status === 'required' ? '必须复核' : '建议复核'} / {humanWorkflow.triage_level || 'normal'}</div>
                          <ul className="text-slate-600 space-y-1 list-disc list-inside">
                            {(humanWorkflow.review_tasks || []).slice(0, 3).map((task) => <li key={task.task_id || task.title}>{task.title}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </section>
          )}

          {/* ═══ Section 3: Contract Structure ═══ */}
          <section id="contract-structure">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><FileText className="w-5 h-5 text-blue-600" />合同结构摘要</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="grid md:grid-cols-2 gap-3">
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">合同目的：</span><span className="text-slate-600">{report.contract_structure.purpose}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">付款安排：</span><span className="text-slate-600">{report.contract_structure.payment_arrangement}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">交付安排：</span><span className="text-slate-600">{report.contract_structure.delivery_arrangement}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">验收安排：</span><span className="text-slate-600">{report.contract_structure.acceptance_arrangement}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">违约责任：</span><span className="text-slate-600">{report.contract_structure.breach_liability}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">解除终止：</span><span className="text-slate-600">{report.contract_structure.termination}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">争议解决：</span><span className="text-slate-600">{report.contract_structure.dispute_resolution}</span></div>
                    <div className="bg-slate-50 rounded-lg p-3"><span className="font-medium text-slate-700">附件：</span><span className="text-slate-600">{report.contract_structure.attachments.join('、')}</span></div>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-3">
                    <span className="font-medium text-slate-700">主要权利义务：</span>
                    <ul className="list-disc list-inside text-slate-600 mt-1">
                      {report.contract_structure.main_obligations.map((o, i) => <li key={i}>{o}</li>)}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 4: Risk Matrix ═══ */}
          <section id="risk-matrix">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Target className="w-5 h-5 text-blue-600" />风险矩阵</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-3 mb-4">
                  <div className="text-center p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="text-2xl font-bold text-red-700">{report.risk_matrix.critical}</div>
                    <div className="text-xs text-red-600">重大风险</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="text-2xl font-bold text-orange-700">{report.risk_matrix.high}</div>
                    <div className="text-xs text-orange-600">高风险</div>
                  </div>
                  <div className="text-center p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="text-2xl font-bold text-amber-700">{report.risk_matrix.medium}</div>
                    <div className="text-xs text-amber-600">中风险</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="text-2xl font-bold text-green-700">{report.risk_matrix.low}</div>
                    <div className="text-xs text-green-600">低风险</div>
                  </div>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">编号</TableHead>
                      <TableHead>风险标题</TableHead>
                      <TableHead className="w-20">等级</TableHead>
                      <TableHead className="w-24">类型</TableHead>
                      <TableHead className="w-20">位置</TableHead>
                      <TableHead className="w-16">概率</TableHead>
                      <TableHead className="w-16">严重度</TableHead>
                      <TableHead className="w-16">评分</TableHead>
                      <TableHead className="w-16">优先级</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.risk_items.map((item) => {
                      const lvl = riskLevelConfig[item.risk_level];
                      return (
                        <TableRow key={item.risk_id}>
                          <TableCell className="text-xs font-mono">{item.risk_no}</TableCell>
                          <TableCell className="text-sm font-medium">{item.title}</TableCell>
                          <TableCell><Badge className={`text-xs ${lvl.color}`}>{lvl.label}</Badge></TableCell>
                          <TableCell className="text-xs">{item.risk_type}</TableCell>
                          <TableCell className="text-xs">{item.clause_location}</TableCell>
                          <TableCell className="text-xs">{item.probability}</TableCell>
                          <TableCell className="text-xs">{item.severity}</TableCell>
                          <TableCell className="text-xs font-medium">{typeof item.risk_score === 'number' ? item.risk_score : '-'}</TableCell>
                          <TableCell className="text-xs font-medium">P{item.priority}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 5: Risk Analysis (Clause by Clause) ═══ */}
          <section id="risk-analysis">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2"><Gavel className="w-5 h-5 text-blue-600" />逐条律师式分析</h2>
              <span className="text-sm text-slate-500">共 {report.risk_items.length} 项风险</span>
            </div>
            <div className="space-y-3">
              {report.risk_items.map((item) => <RiskItemCard key={item.risk_id} item={item} />)}
            </div>
          </section>

          {/* ═══ Section 6: Missing Clauses ═══ */}
          <section id="missing-clauses">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><AlertCircle className="w-5 h-5 text-amber-600" />缺失条款审查</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {report.missing_clauses.length > 0 ? (
                  report.missing_clauses.map((mc) => (
                    <div key={mc.id} className="border border-amber-100 bg-amber-50/50 rounded-lg p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge className={`text-xs ${mc.importance === 'critical' ? 'bg-red-600 text-white' : mc.importance === 'high' ? 'bg-orange-500 text-white' : 'bg-amber-500 text-white'}`}>
                          {mc.importance === 'critical' ? '必须补充' : mc.importance === 'high' ? '建议补充' : '可选'}
                        </Badge>
                        <Badge variant="outline" className="text-xs">{mc.category}</Badge>
                        <span className="font-medium text-sm text-slate-800">{mc.title}</span>
                      </div>
                      <p className="text-sm text-slate-600">{mc.reason}</p>
                      <div className="bg-white border border-amber-200 rounded p-2 text-sm text-slate-700">
                        <span className="font-medium text-amber-800">建议条款：</span>{mc.suggested_clause}
                      </div>
                      <div className="text-xs text-slate-500">法律依据：{mc.legal_basis}</div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                    未识别到明确缺失条款；仍建议结合全文由律师复核核心条款覆盖情况。
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 7: Favorable Clauses ═══ */}
          <section id="favorable-clauses">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-green-600" />有利条款</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {report.favorable_clauses.length > 0 ? (
                  report.favorable_clauses.map((fc) => (
                    <div key={fc.id} className="border border-green-100 bg-green-50/50 rounded-lg p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge className="text-xs bg-green-600 text-white">有利</Badge>
                        <span className="font-medium text-sm text-slate-800">{fc.title}</span>
                        <span className="text-xs text-slate-500">{fc.clause_location}</span>
                      </div>
                      <div className="text-sm text-slate-600 italic border-l-2 border-green-300 pl-2">&ldquo;{fc.original_text}&rdquo;</div>
                      <p className="text-sm text-slate-600"><span className="font-medium text-green-700">有利原因：</span>{fc.reason}</p>
                      <p className="text-sm text-slate-600"><span className="font-medium text-slate-700">建议：</span>{fc.recommendation}</p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                    未识别到可直接保留且对当前立场明确有利的完整条款。本报告已优先展示需修改和需补充的条款。
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 8: Pending Facts ═══ */}
          <section id="pending-facts">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Clock className="w-5 h-5 text-purple-600" />待补事实</CardTitle></CardHeader>
              <CardContent>
                {evidenceAudit && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
                    <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-3">
                      <div className="text-xs text-purple-700">证据计划覆盖</div>
                      <div className="text-lg font-semibold text-purple-950">{Math.round((evidenceAudit.risk_evidence_coverage ?? 0) * 100)}%</div>
                    </div>
                    <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-3">
                      <div className="text-xs text-purple-700">证据建议</div>
                      <div className="text-lg font-semibold text-purple-950">{evidenceAudit.evidence_suggestion_count ?? 0}</div>
                    </div>
                    <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-3">
                      <div className="text-xs text-purple-700">阻断事实</div>
                      <div className="text-lg font-semibold text-purple-950">{evidenceAudit.blocking_pending_fact_count ?? 0}</div>
                    </div>
                    <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-3">
                      <div className="text-xs text-purple-700">待办任务</div>
                      <div className="text-lg font-semibold text-purple-950">{(evidenceAudit.evidence_tasks || []).length}</div>
                    </div>
                  </div>
                )}
                <div className="space-y-2">
                  {report.pending_facts.map((pf) => (
                    <div key={pf.id} className="border border-purple-100 bg-purple-50/50 rounded-lg p-3 flex items-start gap-3">
                      <AlertTriangle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-medium text-sm text-slate-800">{pf.field}</div>
                        <div className="text-sm text-slate-600">{pf.reason}</div>
                        <div className="text-xs text-purple-700 mt-1">影响：{pf.impact}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 9: Legal Authority Appendix ═══ */}
          <section id="legal-appendix">
            <Card>
              <CardHeader><CardTitle className="text-lg flex items-center gap-2"><BookOpen className="w-5 h-5 text-blue-600" />法律依据附录</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm text-slate-500 mb-4">以下为本报告引用的全部法律依据，按效力层级排列。</p>
                {citationAudit && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="text-xs text-slate-500">来源数量</div>
                      <div className="text-lg font-semibold text-slate-900">{citationAudit.source_count ?? 0}</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="text-xs text-slate-500">风险覆盖</div>
                      <div className="text-lg font-semibold text-slate-900">{Math.round((citationAudit.risk_citation_coverage ?? 0) * 100)}%</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="text-xs text-slate-500">已核验</div>
                      <div className="text-lg font-semibold text-slate-900">{Math.round((citationAudit.verified_ratio ?? 0) * 100)}%</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="text-xs text-slate-500">可复核</div>
                      <div className="text-lg font-semibold text-slate-900">{Math.round((citationAudit.reviewable_ratio ?? 0) * 100)}%</div>
                    </div>
                  </div>
                )}
                <div className="space-y-3">
                  {report.legal_source_appendix.length > 0 ? (
                    report.legal_source_appendix.map((s) => <LegalSourceCard key={s.source_id} source={s} />)
                  ) : (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                      未命中已校验法律依据；建议接入权威法库后重新生成并由律师复核。
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </section>

          {/* ═══ Section 10: Disclaimer ═══ */}
          <section id="disclaimer-section">
            <Card className="border-slate-300 bg-slate-50">
              <CardHeader><CardTitle className="text-lg flex items-center gap-2 text-slate-600"><Info className="w-5 h-5" />免责声明</CardTitle></CardHeader>
              <CardContent>
                <div className="text-sm text-slate-600 whitespace-pre-wrap">{report.disclaimer}</div>
              </CardContent>
            </Card>
          </section>

          {/* Action Bar */}
          <div className="no-print flex items-center justify-between p-4 bg-white border rounded-lg shadow-sm sticky bottom-4">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => handleDownload('pdf')}><Download className="w-4 h-4 mr-1" />下载PDF</Button>
              <Button variant="outline" size="sm" onClick={() => handleDownload('doc')}><FileText className="w-4 h-4 mr-1" />下载Word</Button>
            </div>
            <Button size="sm" className="bg-orange-600 hover:bg-orange-700 text-white" onClick={() => toast.success('已提交律师复核请求')}>
              <Gavel className="w-4 h-4 mr-1" />请求律师复核
            </Button>
          </div>
        </main>
      </div>
    </Layout>
  );
}
