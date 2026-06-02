import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  ArrowRight,
  BookOpen,
  Boxes,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  ClipboardList,
  Cpu,
  Database,
  FileArchive,
  FileCheck,
  FileSearch,
  FileText,
  FolderGit2,
  Gavel,
  LayoutDashboard,
  LockKeyhole,
  MessageSquareText,
  PenLine,
  Scale,
  ShieldCheck,
  Sparkles,
  Upload,
  Users,
  type LucideIcon,
} from 'lucide-react';
import Layout from '@/components/Layout';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import { useI18n } from '@/contexts/I18nContext';

const IMG_REVIEW = '/images/workflow/workflow-intake.png';
const IMG_AI = '/images/workflow/workflow-analysis.png';
const IMG_REPORT = '/images/workflow/workflow-report.png';

type LinkItem = {
  icon: LucideIcon;
  title: string;
  body: string;
  meta: string;
  to: string;
  action: string;
};

export default function Index() {
  const { t, lang } = useI18n();

  const copy = lang === 'zh'
    ? {
        eyebrow: 'LEGAL OPERATING SYSTEM',
        heroTitle: '从一份文书，到完整案件工作台。',
        heroBody:
          '律审雷达把上传审查、案件包导入、证据事实整理、类案法研、文书生成和团队协作放进同一条法律工作流。',
        primary: '导入案件包',
        secondary: '上传文书审查',
        tertiary: '进入案件工作台',
        heroStats: [
          ['8-Agent', '深度审查管线'],
          ['ZIP/OCR', '案件材料入库'],
          ['CN/EN', '双语输出'],
        ],
        liveCase: '买卖合同纠纷',
        liveCourt: '杭州滨江法院',
        liveRisk: '中风险',
        liveAssistant: '案件 AI 助手',
        liveQuestion: '预付款返还的证据链是否完整？',
        liveAnswer: '还缺付款流水原件、催告回执与损失测算依据。可先生成补证任务，再输出律师函和起诉状草稿。',
        lanes: [
          ['01', '导入', 'ZIP 安全解压、OCR、材料分类、自动聚类建案。'],
          ['02', '审查', '风险识别、法律依据、替代条款和谈判话术。'],
          ['03', '工作台', '材料、证据、事实、时间线、任务集中管理。'],
          ['04', '交付', '报告、文书草稿、补证清单、团队协同。'],
        ],
        systemsTitle: '目前功能已经是一套案件操作系统。',
        systemsBody: '按任务拆分入口：导入案件包、审查单份文书、推进案件、生成文书和组织团队。',
        systems: [
          { icon: FileArchive, title: '案件包导入', body: '上传律师案件 ZIP，系统扫描文件、识别案件分组并写入案件库。', meta: 'ZIP / OCR / 聚类', to: '/lawyer/import', action: '开始导入' },
          { icon: Upload, title: '单份文书审查', body: '合同、起诉状、答辩状、律师函等文书直接上传，生成风险摘要和完整报告。', meta: 'docx / pdf / txt', to: '/upload', action: '上传审查' },
          { icon: Briefcase, title: '案件工作台', body: '围绕单个案件管理委托人、对方、管辖、材料、证据、事实和任务。', meta: 'Cases', to: '/cases', action: '查看案件' },
          { icon: MessageSquareText, title: '案件 AI 助手', body: '在案件详情页追问证据链、事实缺口、诉讼策略和文书草稿。', meta: '上下文问答', to: '/cases/1', action: '打开示例' },
          { icon: PenLine, title: '智能文书生成', body: '按事实、请求和主体信息生成起诉状、答辩状、律师函和仲裁申请书。', meta: '草稿 / 缺口提示', to: '/generate', action: '生成文书' },
          { icon: Users, title: '团队与权限', body: '按律师版或企业版组织团队、邀请成员、管理席位和报告额度。', meta: 'Team workspace', to: '/team', action: '配置团队' },
        ] as LinkItem[],
        workflowTitle: '一条线串起审查、证据和交付。',
        workflowBody: '从材料进入系统开始，每一步都保留来源、状态和可复核输出。',
        workflow: [
          { icon: FileSearch, title: '材料入库', body: '文件识别、OCR、材料分类和页码/段落引用。' },
          { icon: ClipboardList, title: '事实抽取', body: '把材料转为事实、时间线、争议焦点和待补清单。' },
          { icon: BookOpen, title: '法律研究', body: '围绕案件类型检索依据，沉淀到报告和文书。' },
          { icon: FileCheck, title: '报告交付', body: '风险矩阵、修改建议、谈判策略和下载交付。' },
        ],
        entryTitle: '不同用户，进入同一套底层能力。',
        entries: [
          { icon: Scale, title: '个人用户', body: '先上传单份合同，快速看到风险和建议。', to: '/upload', action: '审查一份文书' },
          { icon: Gavel, title: '律师 / 法务', body: '先导入案件包，随后在工作台里补证、问 AI、出草稿。', to: '/lawyer/import', action: '导入案件材料' },
          { icon: Boxes, title: '企业团队', body: '用团队席位和文档库统一沉淀审查记录。', to: '/team', action: '管理团队' },
        ],
        depthTitle: '深度报告不是一页摘要。',
        depthBody: '完整审查会覆盖条款定位、法律依据、风险等级、替代条款、谈判话术、证据建议和律师复核触发项。',
        depthPoints: ['风险矩阵', '三版本替代条款', '法律依据附录', '人工复核任务包'],
        opsTitle: '后台和运营能力也已经接入。',
        ops: [
          ['工作台看板', '查看文书数量、已审报告、生成草稿和最近文档。'],
          ['文档库', '按状态管理上传文书，查看、删除和追踪审查结果。'],
          ['AI 管线', '8-Agent 审查阶段、模型配置、耗时和输出结构可监控。'],
          ['付费解锁', '支持单份报告解锁、订阅方案和团队权益。'],
        ],
        finalTitle: '把下一份材料放进工作流。',
        finalBody: '从上传一份文书开始，或直接导入一个案件包。系统会把后续证据、事实、文书和团队协作接起来。',
        finalCta: '开始处理',
        pricingCta: '查看方案',
      }
    : {
        eyebrow: 'LEGAL OPERATING SYSTEM',
        heroTitle: 'From one document to a complete case workspace.',
        heroBody:
          'LawAudit Radar connects upload review, case bundle ingestion, evidence and fact work, legal research, drafting, and team collaboration in one legal workflow.',
        primary: 'Import case bundle',
        secondary: 'Upload for review',
        tertiary: 'Open case workspace',
        heroStats: [
          ['8-Agent', 'deep review pipeline'],
          ['ZIP/OCR', 'case material ingestion'],
          ['CN/EN', 'bilingual delivery'],
        ],
        liveCase: 'Sale contract dispute',
        liveCourt: "Hangzhou Binjiang People's Court",
        liveRisk: 'Medium risk',
        liveAssistant: 'Case AI assistant',
        liveQuestion: 'Is the evidence chain for prepayment refund complete?',
        liveAnswer:
          'Payment originals, demand delivery receipt, and loss calculations are still missing. Create evidence tasks first, then draft the lawyer letter and complaint.',
        lanes: [
          ['01', 'Ingest', 'Secure ZIP extraction, OCR, material classification, and case clustering.'],
          ['02', 'Review', 'Risk detection, legal basis, replacement clauses, and negotiation scripts.'],
          ['03', 'Work', 'Materials, evidence, facts, timeline, and tasks in one case file.'],
          ['04', 'Deliver', 'Reports, drafts, evidence tasks, and team collaboration.'],
        ],
        systemsTitle: 'The product is now a case operating system.',
        systemsBody: 'Start from the task at hand: import a case bundle, review one document, move a case forward, draft, or organize a team.',
        systems: [
          { icon: FileArchive, title: 'Case bundle ingestion', body: 'Upload a lawyer ZIP bundle; the system scans files, detects case clusters, and writes them into the case library.', meta: 'ZIP / OCR / clustering', to: '/lawyer/import', action: 'Start import' },
          { icon: Upload, title: 'Single document review', body: 'Upload contracts, complaints, defenses, and lawyer letters to produce a risk summary and full report.', meta: 'docx / pdf / txt', to: '/upload', action: 'Upload now' },
          { icon: Briefcase, title: 'Case workspace', body: 'Manage client, opponent, venue, materials, evidence, facts, timeline, and tasks around one case.', meta: 'Cases', to: '/cases', action: 'View cases' },
          { icon: MessageSquareText, title: 'Case AI assistant', body: 'Ask about evidence chains, factual gaps, litigation strategy, and document drafts inside the case page.', meta: 'Context Q&A', to: '/cases/1', action: 'Open sample' },
          { icon: PenLine, title: 'Smart drafting', body: 'Generate complaints, defenses, lawyer letters, and arbitration applications from facts, claims, and parties.', meta: 'Drafts / gaps', to: '/generate', action: 'Generate draft' },
          { icon: Users, title: 'Team and access', body: 'Create organizations, invite members, manage seats, and track report quotas for lawyer or enterprise plans.', meta: 'Team workspace', to: '/team', action: 'Configure team' },
        ] as LinkItem[],
        workflowTitle: 'One line connects review, evidence, and delivery.',
        workflowBody: 'From the moment materials enter the system, every step keeps sources, status, and reviewable outputs visible.',
        workflow: [
          { icon: FileSearch, title: 'Material intake', body: 'File recognition, OCR, material classification, and page or paragraph references.' },
          { icon: ClipboardList, title: 'Fact extraction', body: 'Turn materials into facts, timelines, disputed issues, and missing-evidence lists.' },
          { icon: BookOpen, title: 'Legal research', body: 'Retrieve legal basis by matter type and carry it into reports and drafts.' },
          { icon: FileCheck, title: 'Report delivery', body: 'Risk matrix, revisions, negotiation strategy, and downloadable output.' },
        ],
        entryTitle: 'Different users enter the same core workflow.',
        entries: [
          { icon: Scale, title: 'Individuals', body: 'Start with one contract and see risks and revisions quickly.', to: '/upload', action: 'Review one document' },
          { icon: Gavel, title: 'Lawyers / legal teams', body: 'Import a case bundle, then use the workspace to patch evidence, ask AI, and draft.', to: '/lawyer/import', action: 'Import materials' },
          { icon: Boxes, title: 'Enterprise teams', body: 'Use team seats and the document library to retain review records in one place.', to: '/team', action: 'Manage team' },
        ],
        depthTitle: 'The deep report is more than a summary.',
        depthBody:
          'Full review covers clause location, legal basis, risk level, replacement clauses, negotiation scripts, evidence suggestions, and lawyer-review triggers.',
        depthPoints: ['Risk matrix', 'Three replacement versions', 'Legal authority appendix', 'Human review task pack'],
        opsTitle: 'Admin and operating surfaces are connected too.',
        ops: [
          ['Dashboard', 'Track document count, completed reviews, generated drafts, and recent documents.'],
          ['Document library', 'Manage uploaded documents by status, view, delete, and trace review results.'],
          ['AI pipeline', 'Monitor 8-Agent review stages, model config, duration, and output schema.'],
          ['Payments', 'Support single report unlocks, subscription plans, and team entitlements.'],
        ],
        finalTitle: 'Put the next material into the workflow.',
        finalBody:
          'Start with one document, or import a full case bundle. The system will connect evidence, facts, drafts, and collaboration from there.',
        finalCta: 'Start processing',
        pricingCta: 'See plans',
      };

  const heroStatus = [
    { label: lang === 'zh' ? '材料' : 'Materials', value: '9' },
    { label: lang === 'zh' ? '证据' : 'Evidence', value: '6' },
    { label: lang === 'zh' ? '事实' : 'Facts', value: '14' },
    { label: lang === 'zh' ? '任务' : 'Tasks', value: '5' },
  ];

  const outputTabs = [
    lang === 'zh' ? '风险矩阵' : 'Risk matrix',
    lang === 'zh' ? '证据目录' : 'Evidence catalog',
    lang === 'zh' ? '起诉状草稿' : 'Complaint draft',
    lang === 'zh' ? '补证清单' : 'Evidence tasks',
  ];

  return (
    <Layout>
      <section className="home-hero-pattern border-b border-stone-950/20 bg-[#fbfaf6]">
        <div className="law-container min-h-[calc(100svh-112px)] py-10 lg:py-14">
          <div className="grid min-h-[640px] gap-10 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
            <div className="hero-enter">
              <div className="eyebrow mb-5">{copy.eyebrow}</div>
              <h1 className="max-w-4xl text-6xl font-black leading-[0.9] text-stone-950 sm:text-7xl lg:text-8xl">
                {t('brand')}
              </h1>
              <p className="mt-7 max-w-3xl text-3xl font-black leading-[1] text-stone-950 sm:text-5xl">
                {copy.heroTitle}
              </p>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-700 sm:text-xl sm:leading-9">
                {copy.heroBody}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button asChild size="lg" className="quiet-button">
                  <Link to="/lawyer/import">
                    <FileArchive className="h-4 w-4" />
                    {copy.primary}
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline" className="soft-button">
                  <Link to="/upload">
                    <Upload className="h-4 w-4" />
                    {copy.secondary}
                  </Link>
                </Button>
                <Link to="/cases" className="editorial-link inline-flex items-center gap-2 px-1 py-3 text-sm font-black">
                  {copy.tertiary}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              <div className="mt-10 grid max-w-2xl grid-cols-3 overflow-hidden rounded-[24px] border border-stone-950/15 bg-[#efebe1]/70">
                {copy.heroStats.map(([value, label]) => (
                  <div key={value} className="border-l border-stone-950/15 p-4 first:border-l-0">
                    <div className="text-xl font-black text-stone-950">{value}</div>
                    <div className="mt-1 text-xs leading-5 text-stone-600">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="hero-enter-delay rounded-[30px] border border-stone-950/15 bg-stone-950 p-3 text-stone-50 shadow-none">
              <div className="grid gap-3 lg:grid-cols-[1fr_260px]">
                <div className="rounded-[24px] border border-white/12 bg-[#171512] p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/12 pb-4">
                    <div>
                      <div className="text-xs uppercase text-amber-300">{lang === 'zh' ? '当前案件' : 'Active case'}</div>
                      <div className="mt-1 text-2xl font-black leading-tight">{copy.liveCase}</div>
                      <div className="mt-2 text-xs text-stone-400">{copy.liveCourt}</div>
                    </div>
                    <div className="rounded-full border border-amber-300/30 px-3 py-1 text-xs font-semibold text-amber-200">
                      {copy.liveRisk}
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-4 overflow-hidden rounded-[20px] border border-white/12">
                    {heroStatus.map((item) => (
                      <div key={item.label} className="border-l border-white/12 p-3 first:border-l-0">
                        <div className="text-3xl font-black">{item.value}</div>
                        <div className="mt-1 text-xs text-stone-400">{item.label}</div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-[1fr_0.88fr]">
                    <div className="space-y-2">
                      {[
                        lang === 'zh' ? '付款流水与合同金额一致' : 'Payment flow matches contract amount',
                        lang === 'zh' ? '催告函送达证据待补' : 'Demand letter delivery proof missing',
                        lang === 'zh' ? '违约金计算口径需统一' : 'Liquidated damages formula needs alignment',
                      ].map((item, index) => (
                        <div key={item} className="flex items-center gap-3 rounded-[16px] border border-white/10 bg-white/[0.03] px-3 py-2 text-sm">
                          <CircleDot className={`h-4 w-4 ${index === 1 ? 'text-amber-300' : 'text-emerald-300'}`} />
                          <span className="min-w-0 truncate">{item}</span>
                        </div>
                      ))}
                    </div>
                    <div className="rounded-[20px] bg-[#f8f5ee] p-4 text-stone-950">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-stone-500">
                        <Sparkles className="h-4 w-4 text-amber-700" />
                        {copy.liveAssistant}
                      </div>
                      <p className="mt-4 text-sm font-black leading-5">{copy.liveQuestion}</p>
                      <p className="mt-3 text-xs leading-5 text-stone-600">{copy.liveAnswer}</p>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {outputTabs.map((item) => (
                      <span key={item} className="rounded-full border border-white/14 px-3 py-1 text-xs text-stone-300">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="rounded-[24px] border border-white/12 bg-[#0f0d0b] p-4">
                  <div className="mb-5 flex items-center justify-between">
                    <div className="text-xs uppercase text-stone-400">{lang === 'zh' ? '工作流' : 'Workflow'}</div>
                    <Database className="h-4 w-4 text-amber-300" />
                  </div>
                  <div className="space-y-4">
                    {copy.lanes.map(([number, title, body]) => (
                      <div key={number} className="grid grid-cols-[34px_1fr] gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-amber-300/30 text-xs font-black text-amber-200">
                          {number}
                        </div>
                        <div className="border-b border-white/10 pb-4">
                          <div className="font-black">{title}</div>
                          <p className="mt-1 text-xs leading-5 text-stone-400">{body}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="law-container py-14 lg:py-20">
        <div className="grid gap-8 border-b border-stone-950/20 pb-12 lg:grid-cols-[0.78fr_1.22fr]">
          <div>
            <div className="eyebrow mb-4">Product surface</div>
            <h2 className="section-title">{copy.systemsTitle}</h2>
            <p className="mt-5 max-w-md text-base leading-7 text-stone-600">{copy.systemsBody}</p>
          </div>
          <div className="grid overflow-hidden rounded-[26px] border border-stone-950/15 bg-[#fbfaf6] md:grid-cols-2">
            {copy.systems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.title}
                  to={item.to}
                  className="interactive-button group relative min-h-[236px] border-t border-stone-950/12 p-5 transition-colors hover:bg-[#f2ede3] md:border-l md:[&:nth-child(-n+2)]:border-t-0 md:[&:nth-child(2n+1)]:border-l-0"
                >
                  <div className="relative z-[1] flex h-full flex-col">
                    <div className="flex items-start justify-between gap-4">
                      <Icon className="h-6 w-6 text-amber-700" />
                      <span className="text-xs font-semibold text-stone-500">{item.meta}</span>
                    </div>
                    <h3 className="mt-8 text-2xl font-black leading-none text-stone-950">{item.title}</h3>
                    <p className="mt-4 max-w-sm text-sm leading-6 text-stone-600">{item.body}</p>
                    <div className="mt-auto flex items-center gap-2 pt-6 text-sm font-black text-stone-950">
                      {item.action}
                      <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-y border-stone-950/20 bg-[#efebe1]">
        <div className="law-container py-14 lg:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="lg:sticky lg:top-24 lg:self-start">
              <div className="eyebrow mb-4">Case flow</div>
              <h2 className="section-title">{copy.workflowTitle}</h2>
              <p className="mt-5 max-w-md text-base leading-7 text-stone-600">{copy.workflowBody}</p>
              <div className="mt-8 grid grid-cols-3 overflow-hidden rounded-[24px] border border-stone-950/15 bg-[#fbfaf6]">
                {[IMG_REVIEW, IMG_AI, IMG_REPORT].map((src, index) => (
                  <div key={src} className="aspect-square border-l border-stone-950/12 first:border-l-0">
                    <img src={src} alt="" className="h-full w-full object-cover" />
                    <span className="sr-only">{index + 1}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {copy.workflow.map((item, index) => {
                const Icon = item.icon;
                return (
                  <article key={item.title} className="grid gap-4 border-t border-stone-950/20 pt-5 sm:grid-cols-[72px_1fr]">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-black text-amber-700">{String(index + 1).padStart(2, '0')}</span>
                      <div className="flex h-12 w-12 items-center justify-center rounded-[18px] border border-stone-950/12 bg-[#fbfaf6]">
                        <Icon className="h-5 w-5 text-stone-950" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-3xl font-black leading-none text-stone-950">{item.title}</h3>
                      <p className="mt-4 max-w-2xl text-sm leading-6 text-stone-600">{item.body}</p>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="law-container py-14 lg:py-20">
        <div className="mb-10 grid gap-4 lg:grid-cols-[0.86fr_1.14fr] lg:items-end">
          <div>
            <div className="eyebrow mb-4">Entry points</div>
            <h2 className="section-title">{copy.entryTitle}</h2>
          </div>
          <p className="max-w-2xl text-base leading-7 text-stone-600">
            {lang === 'zh'
              ? '个人、律师和企业团队都从同一套能力出发：材料进入系统后，会沉淀为可追踪的证据、事实、文书和交付记录。'
              : 'Individuals, lawyers, and enterprise teams use the same core workflow: materials become traceable evidence, facts, drafts, and delivery records.'}
          </p>
        </div>

        <div className="grid overflow-hidden rounded-[26px] border border-stone-950/15 bg-[#fbfaf6] lg:grid-cols-3">
          {copy.entries.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.title}
                to={item.to}
                className="interactive-button group relative min-h-[260px] border-t border-stone-950/12 p-6 transition-colors first:border-t-0 hover:bg-[#f2ede3] lg:border-l lg:border-t-0 lg:first:border-l-0"
              >
                <div className="relative z-[1] flex h-full flex-col">
                  <Icon className="h-7 w-7 text-amber-700" />
                  <h3 className="mt-10 text-3xl font-black leading-none">{item.title}</h3>
                  <p className="mt-4 text-sm leading-6 text-stone-600">{item.body}</p>
                  <div className="mt-auto flex items-center gap-2 pt-8 text-sm font-black">
                    {item.action}
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="bg-stone-950 text-stone-50">
        <div className="law-container py-14 lg:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.82fr_1.18fr] lg:items-center">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-300">Deep review</div>
              <h2 className="mt-4 text-5xl font-black leading-[0.94] sm:text-6xl">{copy.depthTitle}</h2>
              <p className="mt-6 max-w-xl text-base leading-7 text-stone-400">{copy.depthBody}</p>
              <div className="mt-8 flex flex-wrap gap-2">
                {copy.depthPoints.map((item) => (
                  <span key={item} className="rounded-full border border-white/15 px-4 py-2 text-sm text-stone-300">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="rounded-[28px] border border-white/15 bg-[#14110f] p-4">
              <div className="grid gap-3 sm:grid-cols-[0.92fr_1.08fr]">
                <div className="rounded-[22px] bg-[#f8f5ee] p-4 text-stone-950">
                  <div className="flex items-center justify-between border-b border-stone-950/12 pb-3">
                    <div className="text-xs font-semibold uppercase text-stone-500">{lang === 'zh' ? '报告结构' : 'Report structure'}</div>
                    <ShieldCheck className="h-4 w-4 text-emerald-800" />
                  </div>
                  <div className="mt-4 space-y-3">
                    {[72, 54, 88, 38].map((width) => (
                      <div key={width} className="rounded-[16px] border border-stone-950/10 p-3">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-700" />
                          <div className="h-3 flex-1 rounded-full bg-stone-950/12">
                            <div className="h-full rounded-full bg-amber-500" style={{ width: `${width}%` }} />
                          </div>
                        </div>
                        <div className="mt-3 h-2 w-10/12 bg-stone-950/10" />
                        <div className="mt-2 h-2 w-7/12 bg-stone-950/10" />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[22px] border border-white/12 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-xs uppercase text-stone-400">{lang === 'zh' ? '交付输出' : 'Deliverables'}</div>
                    <LockKeyhole className="h-4 w-4 text-amber-300" />
                  </div>
                  <div className="mt-5 space-y-3">
                    {[
                      lang === 'zh' ? '风险条款逐条分析' : 'Clause-by-clause risk analysis',
                      lang === 'zh' ? '法律依据与适用理由' : 'Legal basis and applicability',
                      lang === 'zh' ? '保守 / 平衡 / 底线替代条款' : 'Conservative / balanced / bottom-line clauses',
                      lang === 'zh' ? '证据保存与补证任务' : 'Evidence preservation and task list',
                    ].map((item) => (
                      <div key={item} className="flex items-center gap-3 rounded-[16px] border border-white/10 px-3 py-3 text-sm">
                        <FileText className="h-4 w-4 text-amber-300" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                  <Button asChild className="quiet-button mt-6 w-full bg-white text-stone-950 hover:bg-stone-200">
                    <Link to="/upload">
                      {copy.secondary}
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="law-container py-14 lg:py-20">
        <div className="grid gap-8 lg:grid-cols-[0.7fr_1.3fr]">
          <div>
            <div className="eyebrow mb-4">Operations</div>
            <h2 className="section-title">{copy.opsTitle}</h2>
          </div>
          <div className="grid overflow-hidden rounded-[26px] border border-stone-950/15 bg-[#fbfaf6] sm:grid-cols-2">
            {copy.ops.map(([title, body], index) => {
              const icons = [LayoutDashboard, Database, Cpu, FileCheck];
              const Icon = icons[index] || LayoutDashboard;
              const links = ['/dashboard', '/documents', '/pipeline', '/pricing'];
              return (
                <Link
                  key={title}
                  to={links[index]}
                  className="interactive-button group relative min-h-[190px] border-t border-stone-950/12 p-5 transition-colors hover:bg-[#f2ede3] sm:border-l sm:[&:nth-child(-n+2)]:border-t-0 sm:[&:nth-child(2n+1)]:border-l-0"
                >
                  <div className="relative z-[1]">
                    <Icon className="h-6 w-6 text-amber-700" />
                    <h3 className="mt-8 text-2xl font-black">{title}</h3>
                    <p className="mt-3 text-sm leading-6 text-stone-600">{body}</p>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="law-container pb-14">
        <div className="grid gap-6 rounded-[30px] border border-stone-950/15 bg-[#efebe1] p-6 sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <div className="flex items-center gap-3">
              <FolderGit2 className="h-6 w-6 text-amber-700" />
              <h2 className="text-4xl font-black leading-none text-stone-950 sm:text-6xl">{copy.finalTitle}</h2>
            </div>
            <p className="mt-5 max-w-3xl text-base leading-7 text-stone-600">{copy.finalBody}</p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Button asChild size="lg" className="quiet-button">
              <Link to="/lawyer/import">
                {copy.finalCta}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="soft-button">
              <Link to="/pricing">{copy.pricingCta}</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="law-container pb-8">
        <DisclaimerBanner />
      </section>
    </Layout>
  );
}
