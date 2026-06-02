// ═══════════════════════════════════════════════════════════════════════════════
// 律审雷达 v2.0 - Deep Legal Review Mock Data
// Comprehensive lawyer-grade contract review report + case workspace data
// ═══════════════════════════════════════════════════════════════════════════════

// ==================== TYPE DEFINITIONS ====================

export interface LegalSource {
  source_id: string;
  title: string;
  source_type: string; // LAW | ADMIN_REG | JUDICIAL_INTERPRETATION | DEPARTMENT_RULE | LOCAL_REG | GUIDING_CASE | REFERENCE_CASE | JUDGMENT | TEMPLATE | COMMENTARY
  authority_level: string; // 裁判依据 | 审判适用依据 | 类案参照 | 类案参考 | 说理参考 | 实务参考 | 需核验
  issuing_body: string;
  article_number: string;
  text_excerpt: string;
  legal_effect_note: string;
  effective_status: string; // 现行有效 | 已修改 | 已废止 | 待核验
  verification_status: string; // 已校验 | 待核验 | 未检索到
  confidence: number; // 0-100
  applicability_reason: string;
  source_url: string;
  checked_at: string;
}

export interface LegalAnalysis {
  legal_relationship: string;
  applicable_rule: string;
  application_to_clause: string;
  user_impact: string;
  counterparty_argument: string;
  court_focus: string;
  burden_of_proof: string;
  evidence_suggestions: string[];
}

export interface RevisionPlan {
  delete_items: string[];
  add_items: string[];
  replace_items: string[];
  conservative_clause: string;
  balanced_clause: string;
  bottom_line_clause: string;
}

export interface RiskItemDetail {
  risk_id: string;
  risk_no: string;
  title: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  risk_score?: number;
  risk_score_rank?: number;
  risk_score_level?: string;
  risk_score_explanation?: string;
  evidence_confidence_score?: number;
  risk_type: string; // 法律风险 | 商业风险 | 证据风险 | 履约风险 | 合规风险 | 诉讼风险
  clause_location: string;
  page_number: number;
  original_clause_text: string;
  issue_location: string;
  probability: string; // 极高 | 高 | 中 | 低
  severity: string; // 极高 | 高 | 中 | 低
  priority: number;
  legal_analysis: LegalAnalysis;
  legal_sources: LegalSource[];
  revision_plan: RevisionPlan;
  negotiation_strategy: string;
  evidence_suggestions: string[];
  status: string; // 未处理 | 已采纳 | 暂缓 | 需律师复核
  confidence: number;
}

export interface MissingClause {
  id: string;
  title: string;
  category: string;
  importance: 'critical' | 'high' | 'medium';
  reason: string;
  suggested_clause: string;
  legal_basis: string;
}

export interface FavorableClause {
  id: string;
  title: string;
  clause_location: string;
  original_text: string;
  reason: string;
  recommendation: string;
}

export interface PendingFact {
  id: string;
  field: string;
  reason: string;
  impact: string;
}

interface ContractBasicInfo {
  contract_type: string;
  contract_name: string;
  party_a: string;
  party_b: string;
  user_role: string;
  amount: string;
  term: string;
  signing_date: string;
  performance_location: string;
  payment_method: string;
  dispute_resolution: string;
  jurisdiction: string;
  pages: number;
  total_clauses: number;
}

interface ContractStructureSummary {
  purpose: string;
  main_obligations: string[];
  payment_arrangement: string;
  delivery_arrangement: string;
  acceptance_arrangement: string;
  breach_liability: string;
  termination: string;
  dispute_resolution: string;
  attachments: string[];
}

export interface RiskMatrix {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface RiskScoring {
  schema_version?: string;
  overall_score: number;
  overall_level: string;
  risk_count: number;
  counts?: Partial<RiskMatrix>;
  top_risk_ids?: string[];
  score_distribution?: {
    max?: number;
    average?: number;
    top3_average?: number;
  };
  risk_scores?: Array<{
    risk_id: string;
    title?: string;
    normalized_level?: string;
    score: number;
    score_level?: string;
    citation_score?: number;
    grounding_score?: number;
    revision_score?: number;
    evidence_confidence_score?: number;
    penalty?: number;
    priority_rank?: number;
    explanation?: string;
  }>;
}

export interface CitationAudit {
  schema_version?: string;
  status?: 'pass' | 'warn' | 'fail' | string;
  score?: number;
  source_count?: number;
  citation_count?: number;
  risk_count?: number;
  cited_risk_count?: number;
  verified_source_count?: number;
  reviewable_source_count?: number;
  verified_ratio?: number;
  reviewable_ratio?: number;
  risk_citation_coverage?: number;
  source_type_counts?: Record<string, number>;
  authority_counts?: Record<string, number>;
  weak_source_ids?: string[];
  verified_source_ids?: string[];
  reviewable_source_ids?: string[];
  high_risk_without_reviewable_citation?: string[];
  high_risk_without_verified_citation?: string[];
  risks_without_any_citation?: string[];
  missing_appendix_source_ids?: string[];
  orphan_appendix_source_ids?: string[];
  duplicate_source_ids?: string[];
  recommended_actions?: string[];
}

export interface EvidenceAudit {
  schema_version?: string;
  status?: 'pass' | 'warn' | 'fail' | string;
  score?: number;
  risk_count?: number;
  risk_with_evidence_count?: number;
  risk_evidence_coverage?: number;
  evidence_suggestion_count?: number;
  framework_evidence_count?: number;
  pending_fact_count?: number;
  blocking_pending_fact_count?: number;
  risks_without_evidence_plan?: string[];
  high_risk_without_evidence_plan?: string[];
  blocking_pending_fact_ids?: string[];
  duplicate_evidence_suggestions?: string[];
  recommended_actions?: string[];
  evidence_tasks?: Array<{
    task_id?: string;
    type?: string;
    target?: unknown;
    priority?: string;
    description?: string;
  }>;
}

interface ExecutiveSummary {
  overall_risk_level: string;
  signing_recommendation: string;
  top5_risks: string[];
  top5_modifications: string[];
  pending_facts: string[];
  lawyer_review_recommended: boolean;
  summary_text: string;
}

export interface DeepReviewReport {
  id: number;
  report_no: string;
  generated_at: string;
  version: string;
  contract_basic_info: ContractBasicInfo;
  executive_summary: ExecutiveSummary;
  contract_structure: ContractStructureSummary;
  risk_matrix: RiskMatrix;
  citation_audit?: CitationAudit;
  evidence_audit?: EvidenceAudit;
  risk_scoring?: RiskScoring;
  risk_items: RiskItemDetail[];
  missing_clauses: MissingClause[];
  favorable_clauses: FavorableClause[];
  pending_facts: PendingFact[];
  legal_source_appendix: LegalSource[];
  professional_review_framework?: {
    strategy_id?: string;
    document_type?: string;
    matter_type?: string;
    must_review_dimensions?: string[];
    required_fields?: string[];
    evidence_checklist?: string[];
    authority_queries?: string[];
    lawyer_review_triggers?: string[];
    report_focus?: string[];
  };
  coverage_audit?: {
    total_extracted_clauses?: number;
    clauses_selected_for_issue_model?: number;
    rule_candidate_count?: number;
    missing_clause_candidate_count?: number;
    strategy_id?: string;
    strategy_name?: string;
    strategy_required_field_count?: number;
    strategy_pending_fact_count?: number;
    coverage_note?: string;
  };
  quality_audit?: {
    quality_score?: number;
    quality_level?: string;
    warnings?: string[];
    checks?: Array<{ name: string; value: unknown }>;
    lawyer_review_required?: boolean;
    source_policy?: string;
  };
  quality_gate?: {
    status?: 'pass' | 'warn' | 'fail' | string;
    release_level?: string;
    score?: number;
    pass_count?: number;
    warn_count?: number;
    fail_count?: number;
    blocking_gate_ids?: string[];
    warning_gate_ids?: string[];
    evaluations?: Array<{
      gate_id?: string;
      status?: string;
      severity?: string;
      description?: string;
      evidence?: Record<string, unknown>;
    }>;
  };
  delivery_audit?: {
    positioning?: string;
    readiness_level?: string;
    readiness_score?: number;
    blocking_issues?: string[];
    verified_source_ratio?: number;
    reviewable_source_ratio?: number;
    risk_evidence_coverage?: number;
    blocking_pending_fact_count?: number;
    reviewable_artifacts?: string[];
    export_formats?: string[];
    risk_count?: number;
    legal_source_count?: number;
  };
  human_review_workflow?: {
    status?: string;
    triage_level?: string;
    reasons?: string[];
    review_tasks?: Array<{
      task_id?: string;
      title?: string;
      target?: unknown;
      owner_role?: string;
      status?: string;
    }>;
    handoff_note?: string;
  };
  disclaimer: string;
}

// ==================== LEGAL SOURCE EFFECT SYSTEM ====================

export const sourceTypeConfig: Record<string, { label: string; color: string; effectLabel: string }> = {
  'LAW': { label: '法律', color: 'bg-red-700 text-white', effectLabel: '裁判依据/强制性规范' },
  'ADMIN_REG': { label: '行政法规', color: 'bg-orange-600 text-white', effectLabel: '裁判依据/行政管理依据' },
  'JUDICIAL_INTERPRETATION': { label: '司法解释', color: 'bg-orange-500 text-white', effectLabel: '审判适用依据' },
  'DEPARTMENT_RULE': { label: '部门规章', color: 'bg-yellow-600 text-white', effectLabel: '行政监管依据/参考' },
  'LOCAL_REG': { label: '地方性法规', color: 'bg-yellow-700 text-white', effectLabel: '地方适用依据' },
  'GUIDING_CASE': { label: '指导性案例', color: 'bg-blue-700 text-white', effectLabel: '类案参照/强参考' },
  'REFERENCE_CASE': { label: '入库参考案例', color: 'bg-sky-600 text-white', effectLabel: '类案参考/不作为裁判依据' },
  'TYPICAL_CASE': { label: '典型案例', color: 'bg-slate-500 text-white', effectLabel: '趋势参考' },
  'JUDGMENT': { label: '普通裁判文书', color: 'bg-gray-500 text-white', effectLabel: '个案参考' },
  'TEMPLATE': { label: '实务模板', color: 'bg-gray-400 text-white', effectLabel: '实务参考/非法律规范' },
  'COMMENTARY': { label: '学理观点', color: 'bg-gray-400 text-white', effectLabel: '说理参考' },
};

export const verificationStatusConfig: Record<string, { label: string; color: string }> = {
  '已校验': { label: '已校验', color: 'bg-green-100 text-green-800 border-green-300' },
  '待核验': { label: '待核验', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  '未检索到': { label: '未检索到', color: 'bg-red-100 text-red-800 border-red-300' },
};


export const riskLevelConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  critical: { label: '重大', color: 'bg-red-600 text-white', bgColor: 'border-red-500 bg-red-50' },
  high: { label: '高', color: 'bg-orange-500 text-white', bgColor: 'border-orange-400 bg-orange-50' },
  medium: { label: '中', color: 'bg-amber-500 text-white', bgColor: 'border-amber-400 bg-amber-50' },
  low: { label: '低', color: 'bg-green-500 text-white', bgColor: 'border-green-400 bg-green-50' },
};

// ==================== DEEP REVIEW REPORT MOCK DATA ====================
// 房屋租赁合同深度审查报告 - 承租方视角

const mockLegalSources: LegalSource[] = [
  {
    source_id: 'LS-001',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第七百一十三条',
    text_excerpt: '承租人在租赁物需要维修时可以请求出租人在合理期限内维修。出租人未履行维修义务的，承租人可以自行维修，维修费用由出租人负担。因维修租赁物影响承租人使用的，应当相应减少租金或者延长租期。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据，对全国法院具有约束力',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 95,
    applicability_reason: '本条直接规定了出租人的维修义务，合同中将全部维修责任转嫁给承租人的条款与本条规定相悖，承租人可援引本条主张权利。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-002',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第五百八十五条',
    text_excerpt: '当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。约定的违约金低于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以增加；约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 95,
    applicability_reason: '合同约定承租人违约金为全年租金的30%，可能构成"过分高于造成的损失"，承租人可据此请求法院酌减。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-003',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第七百二十四条',
    text_excerpt: '有下列情形之一，非因承租人原因致使租赁物无法使用的，承租人可以解除合同：（一）租赁物被依法查封、扣押；（二）租赁物权属有争议；（三）租赁物具有违反法律、行政法规关于使用条件的强制性规定情形。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 95,
    applicability_reason: '合同未约定承租人法定解除权情形，但本条赋予承租人在特定情形下的法定解除权，不因合同未约定而丧失。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-004',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第七百三十一条',
    text_excerpt: '租赁物危及承租人的安全或者健康的，即使承租人订立合同时明知该租赁物质量不合格，承租人仍然可以随时解除合同。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据，属于强制性规范不可排除适用',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 95,
    applicability_reason: '合同中"承租人不得以任何理由提前解除"的条款不能排除本条法定解除权的适用。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-005',
    title: '《最高人民法院关于审理城镇房屋租赁合同纠纷案件具体应用法律若干问题的解释》',
    source_type: 'JUDICIAL_INTERPRETATION',
    authority_level: '审判适用依据',
    issuing_body: '最高人民法院',
    article_number: '第四条',
    text_excerpt: '当事人以房屋租赁合同未按照法律、行政法规规定办理登记备案手续为由，请求确认合同无效的，人民法院不予支持。',
    legal_effect_note: '司法解释对全国法院审判工作具有约束力，是审判适用依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 90,
    applicability_reason: '合同未约定登记备案义务，但本条明确未备案不影响合同效力，承租人无需担心合同因未备案而无效。',
    source_url: '',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-006',
    title: '《最高人民法院关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》',
    source_type: 'JUDICIAL_INTERPRETATION',
    authority_level: '审判适用依据',
    issuing_body: '最高人民法院',
    article_number: '第六十五条',
    text_excerpt: '当事人一方请求对方支付违约金，对方以合同不成立、合同无效、合同被撤销或者不构成违约等为由抗辩，经审理，对方的抗辩成立的，人民法院应当驳回当事人一方的诉讼请求；对方的抗辩不成立，但是其请求调整违约金的，人民法院应当依法予以调整。',
    legal_effect_note: '司法解释，审判适用依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 88,
    applicability_reason: '违约金过高时，法院应依职权或依申请予以调整，承租人可据此主张酌减。',
    source_url: '',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-007',
    title: '《北京市房屋租赁合同》（示范文本）',
    source_type: 'TEMPLATE',
    authority_level: '实务参考',
    issuing_body: '北京市住房和城乡建设委员会/北京市市场监督管理局',
    article_number: 'BF-2022-2002',
    text_excerpt: '出租人应当在租赁期限内保持房屋及其附属设施正常使用。出租人对房屋进行检查、维修时，应提前通知承租人。',
    legal_effect_note: '政府发布的示范文本，不是法律规范，但代表行业最佳实践和监管导向',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 70,
    applicability_reason: '示范文本明确出租人维修义务，可作为行业惯例的参考依据，证明将全部维修责任转嫁承租人不符合行业惯例。',
    source_url: '',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-008',
    title: '北京某房屋租赁合同纠纷案',
    source_type: 'REFERENCE_CASE',
    authority_level: '类案参考',
    issuing_body: '北京市第二中级人民法院',
    article_number: '(2024)京02民终xxxx号',
    text_excerpt: '法院认为，出租人将房屋结构性维修义务全部转嫁给承租人的条款，加重了承租人的负担，根据公平原则，应认定该条款对承租人不产生约束力。',
    legal_effect_note: '入库参考案例，可作为类案参考和说理依据，但不能直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '待核验',
    confidence: 65,
    applicability_reason: '该案与本案事实相似（出租人转嫁结构性维修义务），法院判决对本案具有参考价值。',
    source_url: '',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-009',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第四百九十七条',
    text_excerpt: '有下列情形之一的，该格式条款无效：（一）具有本法第一编第六章第三节和本法第五百零六条规定的无效情形；（二）提供格式条款一方不合理地免除或者减轻其责任、加重对方责任、限制对方主要权利；（三）提供格式条款一方排除对方主要权利。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 92,
    applicability_reason: '如合同为出租方提供的格式合同，其中不合理加重承租人责任的条款可能被认定为无效格式条款。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-010',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第七百一十六条',
    text_excerpt: '承租人经出租人同意，可以将租赁物转租给第三人。承租人转租的，承租人与出租人之间的租赁合同继续有效；第三人造成租赁物损失的，承租人应当赔偿损失。承租人未经出租人同意转租的，出租人可以解除合同。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 90,
    applicability_reason: '合同禁止转租但未约定违反后果，本条明确未经同意转租的法律后果为出租人可解除合同。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-011',
    title: '上海某商铺租赁违约金纠纷案',
    source_type: 'GUIDING_CASE',
    authority_level: '类案参照',
    issuing_body: '最高人民法院',
    article_number: '指导案例第xxx号',
    text_excerpt: '裁判要旨：商业租赁合同中约定的违约金超过实际损失30%的，一般可认定为"过分高于造成的损失"，人民法院应根据当事人请求予以适当减少。',
    legal_effect_note: '指导性案例，各级法院在审理类似案件时应当参照，具有强参考效力',
    effective_status: '现行有效',
    verification_status: '待核验',
    confidence: 75,
    applicability_reason: '本案违约金为全年租金30%（约7.2万元），如实际损失远低于此数额，可参照本指导案例请求酌减。',
    source_url: '',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-012',
    title: '《中华人民共和国民法典》',
    source_type: 'LAW',
    authority_level: '裁判依据',
    issuing_body: '全国人民代表大会',
    article_number: '第五百零九条',
    text_excerpt: '当事人应当按照约定全面履行自己的义务。当事人应当遵循诚信原则，根据合同的性质、目的和交易习惯履行通知、协助、保密等义务。',
    legal_effect_note: '法律层级最高，可直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 88,
    applicability_reason: '合同未约定出租人的通知义务，但根据诚信原则和交易习惯，出租人仍负有通知义务。',
    source_url: 'https://flk.npc.gov.cn/detail2.html?ZmY4MDgxODE3OTZhNjMzNjAxNzk2YWJiNDMwMDA2NTI',
    checked_at: '2026-05-14',
  },
  {
    source_id: 'LS-013',
    title: '《商品房屋租赁管理办法》',
    source_type: 'DEPARTMENT_RULE',
    authority_level: '行政监管依据',
    issuing_body: '住房和城乡建设部',
    article_number: '第九条',
    text_excerpt: '出租人应当按照合同约定履行房屋的维修义务并确保房屋和室内设施安全。未及时修复损坏的房屋，影响承租人正常使用的，应当按照约定承担赔偿责任或者减少租金。',
    legal_effect_note: '部门规章，行政监管依据，法院裁判时可参考但不能直接作为裁判依据',
    effective_status: '现行有效',
    verification_status: '已校验',
    confidence: 80,
    applicability_reason: '部门规章进一步明确出租人维修义务和未履行的法律后果，可作为法院裁判的参考依据。',
    source_url: '',
    checked_at: '2026-05-14',
  },
];

const mockRiskItems: RiskItemDetail[] = [
  {
    risk_id: 'RISK-001',
    risk_no: 'R-001',
    title: '维修责任全部转嫁承租人，违反法定义务分配',
    risk_level: 'critical',
    risk_type: '法律风险',
    clause_location: '第六条第2款',
    page_number: 3,
    original_clause_text: '租赁期间，房屋及其附属设施的一切维修、保养费用均由承租人承担，包括但不限于房屋结构、屋顶防水、外墙、管道、电路等。出租人不承担任何维修义务。',
    issue_location: '"一切维修、保养费用均由承租人承担"及"出租人不承担任何维修义务"',
    probability: '极高',
    severity: '高',
    priority: 1,
    legal_analysis: {
      legal_relationship: '房屋租赁合同关系，出租人负有保持租赁物适用状态的法定义务',
      applicable_rule: '《民法典》第713条规定出租人负有维修义务，第497条规定格式条款不合理加重对方责任的无效',
      application_to_clause: '本条将房屋结构性维修（屋顶防水、外墙、管道等）义务全部转嫁给承租人，属于不合理加重承租人责任。房屋结构性维修属于出租人的法定义务，不因合同约定而免除。',
      user_impact: '承租人可能需承担数万元甚至数十万元的结构性维修费用（如屋顶漏水修缮、管道老化更换），且无法向出租人追偿。',
      counterparty_argument: '出租人可能主张：(1)双方系自愿约定，意思自治；(2)租金已考虑维修成本因素；(3)承租人签字即表示接受。',
      court_focus: '法院将关注：(1)合同是否为格式合同；(2)出租人是否尽到提示说明义务；(3)维修费用是否与租金水平相称；(4)维修项目是否属于结构性/非结构性。',
      burden_of_proof: '承租人需举证：(1)维修项目属于结构性维修；(2)合同为格式合同且未经充分协商；(3)实际发生的维修费用。出租人需举证：(1)租金定价已包含维修成本；(2)已对该条款进行提示说明。',
      evidence_suggestions: ['保留房屋交付时的现状照片/视频', '保留维修通知记录（微信/短信/邮件）', '保留维修费用发票和施工合同', '保留房屋质量问题的鉴定报告'],
    },
    legal_sources: [mockLegalSources[0], mockLegalSources[7], mockLegalSources[8], mockLegalSources[12]],
    revision_plan: {
      delete_items: ['"一切维修、保养费用均由承租人承担"', '"出租人不承担任何维修义务"'],
      add_items: ['区分结构性维修与日常维护的责任划分', '明确维修响应时限', '约定紧急维修时承租人的自行维修权和费用追偿权'],
      replace_items: ['将"一切维修"替换为"日常使用维护"'],
      conservative_clause: '租赁期间，房屋主体结构、屋顶防水、外墙、公共管道、电路主线等结构性维修由出租人负责，承租人应在发现问题后三日内书面通知出租人，出租人应在接到通知后七日内安排维修。承租人负责房屋内部日常使用维护（如灯泡更换、水龙头垫圈等）。因出租人未及时维修导致承租人损失的，出租人应予赔偿。紧急情况下（如水管爆裂、漏电等危及安全的情形），承租人有权先行维修，费用由出租人承担。',
      balanced_clause: '租赁期间，房屋结构性维修（含屋顶、外墙、承重结构、公共管道主线）由出租人负责；房屋内部设施的日常维护和因承租人使用不当造成的损坏由承租人负责。出租人应在接到维修通知后十个工作日内完成维修。',
      bottom_line_clause: '租赁期间，房屋结构性维修由出租人负责，日常维护由承租人负责。双方对维修责任有争议的，按照《民法典》第七百一十三条处理。',
    },
    negotiation_strategy: '建议以"行业惯例"和"政府示范文本"为切入点：\n1. 指出北京市住建委发布的租赁合同示范文本明确区分了出租人和承租人的维修责任；\n2. 强调结构性维修费用可能很高，如不区分责任，承租人难以接受当前租金水平；\n3. 提出折中方案：承租人承担5000元以下的日常维护，超出部分由出租人承担。',
    evidence_suggestions: ['房屋交付现状照片/视频（含水电表读数）', '维修通知书面记录', '维修费用票据', '类似房屋租金水平对比'],
    status: '未处理',
    confidence: 92,
  },
  {
    risk_id: 'RISK-002',
    risk_no: 'R-002',
    title: '违约金过高（全年租金30%），可能被法院酌减',
    risk_level: 'critical',
    risk_type: '法律风险',
    clause_location: '第九条第1款',
    page_number: 5,
    original_clause_text: '承租人提前解除合同或逾期支付租金超过三十日的，应向出租人支付相当于全年租金百分之三十的违约金（即人民币72,000元），并赔偿出租人因此遭受的一切损失。',
    issue_location: '"全年租金百分之三十"及"一切损失"',
    probability: '高',
    severity: '极高',
    priority: 2,
    legal_analysis: {
      legal_relationship: '合同违约责任，涉及违约金调整规则',
      applicable_rule: '《民法典》第585条违约金调整规则，合同编通则解释第65条',
      application_to_clause: '违约金72,000元（全年租金30%）是否"过分高于造成的损失"需具体分析。如承租人提前3个月通知解除，出租人实际损失可能仅为1-2个月空置期租金（约20,000-40,000元），72,000元可能构成过高违约金。',
      user_impact: '承租人如因合理原因需提前解除合同（如工作调动、家庭变故），将面临高额违约金负担。同时"一切损失"表述无上限，理论上出租人可主张装修损失、预期租金收益等。',
      counterparty_argument: '出租人可能主张：(1)违约金系双方协商确定；(2)提前解除导致房屋空置、重新招租成本；(3)装修折旧损失；(4)中介费损失。',
      court_focus: '法院将关注：(1)违约金与实际损失的比例关系；(2)出租人的实际损失举证；(3)房屋再出租的难易程度；(4)承租人违约的主观过错程度。',
      burden_of_proof: '如承租人主张违约金过高请求酌减，需初步举证违约金与实际损失不相称。出租人需举证实际损失的具体数额和构成。',
      evidence_suggestions: ['保留提前通知解除的书面证据', '收集同地段同类型房屋的出租周期数据', '保留租金支付记录证明履约诚意'],
    },
    legal_sources: [mockLegalSources[1], mockLegalSources[5], mockLegalSources[10]],
    revision_plan: {
      delete_items: ['"一切损失"的无上限表述'],
      add_items: ['违约金上限条款', '提前通知减免机制', '出租人同等违约责任'],
      replace_items: ['将固定30%违约金替换为阶梯式违约金'],
      conservative_clause: '任何一方提前解除合同的，应提前六十日书面通知对方，并支付相当于两个月租金的违约金。如提前通知期不足六十日的，每少一日加付日租金的百分之五十作为补偿。违约金总额不超过三个月租金。因不可抗力、政府征收、房屋重大安全隐患等原因解除的，不适用违约金条款。',
      balanced_clause: '任何一方提前解除合同的，应提前三十日书面通知对方，并支付相当于一个月租金的违约金。逾期支付租金超过三十日的，出租人有权解除合同并要求承租人支付逾期期间租金及日万分之五的滞纳金。',
      bottom_line_clause: '承租人提前解除合同的，应提前三十日通知出租人并支付两个月租金作为违约金。出租人提前解除合同的，应提前三十日通知承租人并退还剩余租金及押金，另支付两个月租金作为违约金。',
    },
    negotiation_strategy: '建议分步谈判：\n1. 首先指出当前违约金条款是单向的（仅约束承租人），提出对等原则要求；\n2. 引用指导性案例说明30%违约金可能被法院酌减，建议双方约定合理数额避免诉讼；\n3. 提出阶梯式方案：提前60天通知免违约金，提前30天通知付1个月租金，未提前通知付2个月租金。',
    evidence_suggestions: ['保留所有租金支付凭证', '如需提前解除，务必书面通知并保留送达证据', '了解同地段房屋空置率和再出租周期'],
    status: '未处理',
    confidence: 90,
  },
  {
    risk_id: 'RISK-003',
    risk_no: 'R-003',
    title: '承租人解除权被不当限制，排除法定解除权',
    risk_level: 'high',
    risk_type: '法律风险',
    clause_location: '第十条第3款',
    page_number: 5,
    original_clause_text: '租赁期间，承租人不得以任何理由提前解除本合同。如承租人因自身原因需提前退租，仍应支付剩余租期全部租金。',
    issue_location: '"不得以任何理由提前解除"及"支付剩余租期全部租金"',
    probability: '高',
    severity: '高',
    priority: 3,
    legal_analysis: {
      legal_relationship: '合同解除权，涉及法定解除权与约定解除权的关系',
      applicable_rule: '《民法典》第724条、第731条赋予承租人法定解除权，不可通过合同约定排除',
      application_to_clause: '"不得以任何理由提前解除"的表述试图排除承租人的法定解除权，该约定因违反法律强制性规定而无效。同时，"支付剩余租期全部租金"实质上是预定损害赔偿，可能构成违约金过高。',
      user_impact: '如房屋出现重大安全隐患、被依法查封等情形，承租人仍被迫继续履行或承担全部剩余租金，严重损害承租人合法权益。',
      counterparty_argument: '出租人可能主张：(1)承租人签字确认即接受；(2)租金优惠已考虑长期租约因素；(3)出租人基于长期租约做出了投资决策。',
      court_focus: '法院将关注：(1)该条款是否排除了法定解除权；(2)"剩余租期全部租金"是否构成过高违约金；(3)承租人解除的具体原因是否属于法定解除情形。',
      burden_of_proof: '承租人需举证解除原因属于法定解除情形（如房屋安全隐患、权属争议等）。如主张违约金过高，需举证实际损失远低于剩余租金总额。',
      evidence_suggestions: ['保留房屋安全隐患的证据（照片、视频、检测报告）', '保留与出租人沟通解除事宜的书面记录', '了解法定解除权的具体适用情形'],
    },
    legal_sources: [mockLegalSources[2], mockLegalSources[3], mockLegalSources[8]],
    revision_plan: {
      delete_items: ['"不得以任何理由提前解除"', '"支付剩余租期全部租金"'],
      add_items: ['明确法定解除权情形', '约定合理的提前解除程序和违约金'],
      replace_items: ['将绝对禁止解除替换为有条件解除'],
      conservative_clause: '有下列情形之一的，承租人可以解除合同且不承担违约责任：(1)房屋存在危及人身安全的质量问题且出租人未在通知后十五日内修复的；(2)房屋被依法查封、扣押致使无法正常使用的；(3)出租人未经承租人同意擅自变更房屋用途或结构的；(4)不可抗力致使合同目的无法实现的。除上述情形外，承租人提前解除合同的，按本合同第九条约定承担违约责任。',
      balanced_clause: '承租人因法定事由或提前六十日书面通知出租人的，可以解除合同。提前通知解除的，承租人应支付一个月租金作为补偿。',
      bottom_line_clause: '承租人提前解除合同应提前三十日通知出租人。法定解除情形不受通知期限限制。',
    },
    negotiation_strategy: '直接指出该条款的法律效力问题：\n1. 明确告知出租人，排除法定解除权的条款依法无效，即使写入合同也不能阻止承租人行使法定解除权；\n2. 建议双方约定合理的提前解除机制，既保护出租人的租金预期，也给承租人合理退出通道；\n3. 强调合理的解除机制有利于双方关系维护，避免因僵局导致更大损失。',
    evidence_suggestions: ['保留房屋现状记录', '如需解除，先发书面通知并保留证据', '了解当地法院对类似条款的裁判倾向'],
    status: '未处理',
    confidence: 88,
  },
  {
    risk_id: 'RISK-004',
    risk_no: 'R-004',
    title: '押金退还条件不明确，出租人可能无理由扣押',
    risk_level: 'high',
    risk_type: '商业风险',
    clause_location: '第四条第3款',
    page_number: 2,
    original_clause_text: '租赁期满或合同解除后，出租人应在确认房屋及设施完好无损后退还押金。如有损坏，出租人有权从押金中扣除相应维修费用。',
    issue_location: '"确认房屋及设施完好无损"及"有权扣除相应维修费用"',
    probability: '高',
    severity: '中',
    priority: 4,
    legal_analysis: {
      legal_relationship: '押金（租赁保证金）的法律性质为担保，退还条件应明确具体',
      applicable_rule: '《民法典》第509条诚信原则，交易习惯中押金退还应有明确标准和时限',
      application_to_clause: '"完好无损"标准过于模糊，未区分正常使用磨损与人为损坏。"相应维修费用"未约定评估方式和争议解决机制。出租人可能以"墙面有污渍""地板有划痕"等正常使用痕迹为由拒绝退还押金。',
      user_impact: '承租人退租时可能面临押金被无理扣除的风险，且缺乏有效的争议解决途径。押金金额为两个月租金（40,000元），损失不可忽视。',
      counterparty_argument: '出租人可能主张：(1)房屋交付时状态良好，退租时应恢复原状；(2)任何损坏都应由承租人负责修复；(3)维修费用由出租人合理评估。',
      court_focus: '法院将关注：(1)房屋交付时的状态记录；(2)退租时的状态对比；(3)损坏是否属于正常使用磨损；(4)扣除金额是否合理。',
      burden_of_proof: '出租人主张扣除押金的，应举证：(1)房屋交付时的状态；(2)退租时的损坏情况；(3)维修费用的合理性。承租人应举证：(1)损坏属于正常使用磨损；(2)已尽到合理使用义务。',
      evidence_suggestions: ['入住时拍摄房屋全面照片/视频并双方签字确认', '退租时同样拍摄记录', '保留日常维护记录', '了解"正常使用磨损"的行业标准'],
    },
    legal_sources: [mockLegalSources[11], mockLegalSources[6]],
    revision_plan: {
      delete_items: ['"完好无损"的模糊表述'],
      add_items: ['押金退还时限', '房屋交付和退还时的状态确认机制', '正常使用磨损免责条款', '争议解决方式'],
      replace_items: ['将"完好无损"替换为"正常使用状态"'],
      conservative_clause: '租赁期满或合同解除后十五日内，双方共同对房屋进行验收。正常使用磨损不视为损坏。如有超出正常磨损的损坏，双方协商确定维修费用；协商不成的，委托双方认可的第三方评估。出租人应在验收完成后十五日内退还押金（扣除经双方确认的合理费用）。出租人逾期退还的，每逾期一日按押金总额的万分之三支付滞纳金。',
      balanced_clause: '合同终止后十五日内退还押金。如有损坏（正常磨损除外），出租人应提供维修费用明细和票据，经承租人确认后从押金中扣除。',
      bottom_line_clause: '合同终止后三十日内退还押金。有争议的损坏项目，双方协商或委托第三方评估。',
    },
    negotiation_strategy: '以"双方保护"为切入点：\n1. 提出入住时双方共同拍照确认房屋状态，作为退租时的对比基准；\n2. 建议明确"正常使用磨损"不扣押金（如墙面轻微变色、地板轻微划痕）；\n3. 约定押金退还时限（如15天内），避免出租人无限期拖延。',
    evidence_suggestions: ['入住前全面拍照录像', '双方签署《房屋交付确认书》', '保留所有维修和保养记录'],
    status: '未处理',
    confidence: 85,
  },
  {
    risk_id: 'RISK-005',
    risk_no: 'R-005',
    title: '租金调整机制缺失，出租人可能单方涨租',
    risk_level: 'high',
    risk_type: '商业风险',
    clause_location: '第三条',
    page_number: 2,
    original_clause_text: '月租金为人民币20,000元。租赁期间，出租人有权根据市场行情调整租金，调整幅度不受限制。',
    issue_location: '"有权根据市场行情调整租金，调整幅度不受限制"',
    probability: '中',
    severity: '高',
    priority: 5,
    legal_analysis: {
      legal_relationship: '租金给付义务，涉及合同变更规则',
      applicable_rule: '《民法典》第543条合同变更须经双方协商一致，单方变更权需有明确约定且不得违反公平原则',
      application_to_clause: '"出租人有权调整"赋予出租人单方变更租金的权利，但"不受限制"的表述可能因违反公平原则而被认定为无效。合同变更原则上需双方协商一致。',
      user_impact: '承租人面临租金大幅上涨的不确定性，无法进行合理的财务规划。如出租人大幅涨租，承租人要么接受高租金，要么被迫搬离并承担违约责任。',
      counterparty_argument: '出租人可能主张：(1)市场租金上涨，调整合理；(2)承租人签字同意了调整机制；(3)长期租约中租金调整是惯例。',
      court_focus: '法院将关注：(1)调整机制是否公平合理；(2)是否给予承租人合理的异议权和退出权；(3)调整幅度是否符合市场水平。',
      burden_of_proof: '如发生争议，出租人需举证租金调整符合市场行情。承租人可举证调整幅度明显超出市场水平。',
      evidence_suggestions: ['保留周边同类房屋租金水平证据', '保留出租人发出的涨租通知', '了解当地租金指导价（如有）'],
    },
    legal_sources: [mockLegalSources[11]],
    revision_plan: {
      delete_items: ['"调整幅度不受限制"'],
      add_items: ['年度调整上限', '调整通知期', '承租人异议权和退出权'],
      replace_items: ['将单方调整权替换为双方协商机制'],
      conservative_clause: '租赁期内前两年租金固定不变。自第三年起，出租人可于每年租期届满前九十日书面通知承租人调整次年租金，年度调整幅度不超过上一年度租金的百分之五。承租人不同意调整的，有权在收到通知后三十日内书面通知出租人解除合同，且不承担违约责任。',
      balanced_clause: '租赁期内每年租金调整幅度不超过8%，且出租人应提前60日书面通知。承租人不接受调整的，可在通知后30日内解除合同。',
      bottom_line_clause: '租金调整须双方协商一致。协商不成的，维持原租金水平。',
    },
    negotiation_strategy: '以"稳定预期"为核心论点：\n1. 指出无限制涨租条款使承租人无法做财务规划，不利于长期合作；\n2. 提出参照CPI或当地租金指导价设定年度调整上限（如5%-8%）；\n3. 如出租人坚持保留调整权，要求增加承租人在涨租时的无责解除权。',
    evidence_suggestions: ['收集同地段近3年租金变化数据', '了解当地是否有租金指导价政策'],
    status: '未处理',
    confidence: 82,
  },
  {
    risk_id: 'RISK-006',
    risk_no: 'R-006',
    title: '转租和转让限制过严，缺乏合理退出机制',
    risk_level: 'medium',
    risk_type: '商业风险',
    clause_location: '第十一条',
    page_number: 6,
    original_clause_text: '未经出租人书面同意，承租人不得将房屋全部或部分转租、转借给第三人，不得将租赁权转让给第三人。违反本条约定的，出租人有权立即解除合同并没收全部押金。',
    issue_location: '"没收全部押金"',
    probability: '中',
    severity: '中',
    priority: 6,
    legal_analysis: {
      legal_relationship: '转租权限制与违约后果',
      applicable_rule: '《民法典》第716条规定未经同意转租的后果为出租人可解除合同，但"没收押金"无法律依据',
      application_to_clause: '禁止未经同意转租本身合法，但"没收全部押金"的约定超出了法律规定的违约后果。押金的性质是担保，不是违约金，出租人无权"没收"。',
      user_impact: '承租人如因工作变动等原因需转租（即使已找到合适的承接人），也可能面临押金被没收的风险。',
      counterparty_argument: '出租人可能主张：(1)禁止转租是为了保护房屋安全；(2)没收押金是对违约行为的惩罚；(3)承租人明知禁止转租仍签约。',
      court_focus: '法院将关注：(1)"没收押金"的性质认定（违约金还是不当得利）；(2)承租人违约的具体情节；(3)出租人的实际损失。',
      burden_of_proof: '出租人主张没收押金的，需举证因转租行为遭受的实际损失。承租人可主张"没收押金"条款无效或请求酌减。',
      evidence_suggestions: ['如需转租，务必先取得出租人书面同意', '保留与出租人协商转租的沟通记录'],
    },
    legal_sources: [mockLegalSources[9], mockLegalSources[8]],
    revision_plan: {
      delete_items: ['"没收全部押金"'],
      add_items: ['出租人不得无理由拒绝转租的条款', '转租审批时限'],
      replace_items: ['将"没收押金"替换为合理的违约金'],
      conservative_clause: '承租人转租须经出租人书面同意，出租人不得无正当理由拒绝。承租人提出转租申请后，出租人应在十五日内书面答复；逾期未答复的，视为同意。未经同意擅自转租的，出租人有权解除合同，承租人应支付一个月租金作为违约金。',
      balanced_clause: '转租须经出租人同意，出租人应在收到申请后15日内答复。未经同意转租的，出租人可解除合同。',
      bottom_line_clause: '转租须经出租人书面同意。违反约定的，出租人可解除合同并要求承租人承担合理损失。',
    },
    negotiation_strategy: '以"合理退出"为切入点：\n1. 指出长期租约中承租人可能因客观原因需要转租，完全禁止不利于双方；\n2. 建议改为"经出租人同意可转租，出租人不得无理由拒绝"；\n3. 删除"没收押金"条款，改为合理违约金。',
    evidence_suggestions: ['保留所有与出租人的沟通记录', '如需转租，先书面申请并保留证据'],
    status: '未处理',
    confidence: 80,
  },
  {
    risk_id: 'RISK-007',
    risk_no: 'R-007',
    title: '房屋用途限制过严且变更后果不明',
    risk_level: 'medium',
    risk_type: '履约风险',
    clause_location: '第二条第2款',
    page_number: 1,
    original_clause_text: '承租人应将房屋仅用于居住目的，不得改变房屋用途。如承租人擅自改变用途，出租人有权立即解除合同。',
    issue_location: '"仅用于居住目的"及"立即解除"',
    probability: '中',
    severity: '中',
    priority: 7,
    legal_analysis: {
      legal_relationship: '租赁物使用方式的约定',
      applicable_rule: '《民法典》第711条承租人应按约定使用租赁物，第728条出租人解除权需满足法定条件',
      application_to_clause: '"仅用于居住"的限制在远程办公日益普遍的背景下可能过于严格。如承租人在家办公是否构成"改变用途"存在争议。"立即解除"未给予承租人纠正机会，可能被认定为不合理。',
      user_impact: '承租人如在家办公、偶尔接待客户等，可能被出租人以"改变用途"为由解除合同。',
      counterparty_argument: '出租人可能主张：(1)住宅用途是规划要求；(2)商业使用增加房屋损耗；(3)影响其他住户。',
      court_focus: '法院将关注：(1)"改变用途"的具体认定标准；(2)承租人的使用行为是否实质改变了房屋用途；(3)是否给出租人或其他住户造成实际影响。',
      burden_of_proof: '出租人需举证承租人实质改变了房屋用途且造成了不利影响。',
      evidence_suggestions: ['了解小区管理规约对居家办公的规定', '保留房屋使用状态的记录'],
    },
    legal_sources: [mockLegalSources[11]],
    revision_plan: {
      delete_items: ['"立即解除"的过激后果'],
      add_items: ['允许居家办公的明确约定', '违反用途限制的纠正期'],
      replace_items: ['将"仅用于居住"细化为"主要用于居住，允许居家办公"'],
      conservative_clause: '承租人应将房屋主要用于居住目的，允许在不影响其他住户正常生活的前提下进行居家办公。承租人不得将房屋用于生产、加工、仓储等非居住用途，不得从事违法活动。如承租人违反用途约定，出租人应书面通知承租人限期纠正（不少于十五日），逾期未纠正的，出租人有权解除合同。',
      balanced_clause: '房屋用于居住及居家办公。不得用于经营性活动或违法用途。违反约定的，出租人通知后15日内未纠正的可解除合同。',
      bottom_line_clause: '房屋主要用于居住。承租人不得从事违法活动或严重影响相邻关系的活动。',
    },
    negotiation_strategy: '以"现代生活方式"为切入点，指出远程办公已成常态，建议明确允许居家办公。',
    evidence_suggestions: ['了解物业管理规约', '保留房屋使用状态照片'],
    status: '未处理',
    confidence: 75,
  },
  {
    risk_id: 'RISK-008',
    risk_no: 'R-008',
    title: '通知送达条款缺失，可能导致重要通知无法有效送达',
    risk_level: 'medium',
    risk_type: '证据风险',
    clause_location: '全文',
    page_number: 0,
    original_clause_text: '（合同全文未约定通知送达方式、送达地址和送达生效时间）',
    issue_location: '合同缺少通知送达条款',
    probability: '中',
    severity: '中',
    priority: 8,
    legal_analysis: {
      legal_relationship: '合同履行中的通知义务',
      applicable_rule: '《民法典》第509条诚信原则下的通知义务，实务中通知送达是争议高发环节',
      application_to_clause: '合同涉及多处需要通知的情形（维修通知、涨租通知、解除通知等），但未约定通知方式和送达标准。如发生争议，双方可能就"是否已有效通知"产生分歧。',
      user_impact: '承租人发出的维修通知、解除通知等可能因缺乏约定的送达方式而被出租人否认收到，影响承租人权利的行使。',
      counterparty_argument: '出租人可能主张未收到通知，或通知方式不符合要求。',
      court_focus: '法院将关注通知是否实际送达以及送达方式是否合理。',
      burden_of_proof: '发出通知的一方需举证通知已送达对方。',
      evidence_suggestions: ['所有重要通知通过书面方式（快递/挂号信）发送并保留回执', '同时通过微信/短信发送并截图保存', '记录出租人的联系方式和地址'],
    },
    legal_sources: [mockLegalSources[11]],
    revision_plan: {
      delete_items: [],
      add_items: ['完整的通知送达条款'],
      replace_items: [],
      conservative_clause: '双方确认以下通知送达方式和地址：\n甲方（出租人）：地址：____；电话：____；微信：____；电子邮箱：____\n乙方（承租人）：地址：____；电话：____；微信：____；电子邮箱：____\n\n通知可通过以下任一方式送达：(1)当面送达，以签收日为送达日；(2)快递/挂号信，以签收日为送达日，拒收的以退回日为送达日；(3)微信/短信，以发送成功后二十四小时为送达日；(4)电子邮件，以发送成功后四十八小时为送达日。\n\n任何一方变更联系方式的，应在变更后五日内书面通知对方，未通知的，原地址仍视为有效送达地址。',
      balanced_clause: '通知通过微信、短信或快递送达，以发送/签收之日起24小时后视为送达。双方应保持联系方式有效。',
      bottom_line_clause: '双方确认联系方式，通知以实际收到为准。',
    },
    negotiation_strategy: '这是对双方都有利的条款，通常容易达成一致。建议主动提出增加通知条款，展示专业性和合作诚意。',
    evidence_suggestions: ['确认并记录出租人所有联系方式', '所有通知保留发送记录'],
    status: '未处理',
    confidence: 78,
  },
  {
    risk_id: 'RISK-009',
    risk_no: 'R-009',
    title: '不可抗力条款缺失，疫情等情形下责任不明',
    risk_level: 'low',
    risk_type: '履约风险',
    clause_location: '全文',
    page_number: 0,
    original_clause_text: '（合同全文未约定不可抗力条款）',
    issue_location: '合同缺少不可抗力条款',
    probability: '低',
    severity: '中',
    priority: 9,
    legal_analysis: {
      legal_relationship: '不可抗力免责',
      applicable_rule: '《民法典》第180条、第590条规定了不可抗力的法定免责效果，即使合同未约定也可适用',
      application_to_clause: '虽然法律已有规定，但合同中明确约定不可抗力条款有助于减少争议。特别是对于"情势变更"（如疫情导致无法正常使用房屋）等边界情形，合同约定可以提供更明确的指引。',
      user_impact: '如发生疫情封控等情形导致承租人无法使用房屋，缺乏合同约定可能导致减租或解除的协商困难。',
      counterparty_argument: '出租人可能主张不可抗力不影响租金支付义务。',
      court_focus: '法院将根据法律规定和具体情况判断。',
      burden_of_proof: '主张不可抗力免责的一方需举证不可抗力事件的发生及其与合同履行障碍的因果关系。',
      evidence_suggestions: ['保留政府发布的管控通知', '保留无法使用房屋的证据'],
    },
    legal_sources: [mockLegalSources[11]],
    revision_plan: {
      delete_items: [],
      add_items: ['不可抗力条款'],
      replace_items: [],
      conservative_clause: '因不可抗力（包括但不限于自然灾害、战争、政府行为、疫情防控措施等）导致任何一方无法履行合同义务的，受影响方应在事件发生后五日内通知对方，并在合理期限内提供证明。不可抗力期间，受影响方免于承担违约责任。不可抗力持续超过六十日的，任何一方有权解除合同，双方互不承担违约责任。因不可抗力导致承租人无法正常使用房屋的，租金应按实际无法使用的天数相应减免。',
      balanced_clause: '不可抗力导致无法履行的，免除违约责任。持续超过30日的，任一方可解除合同。',
      bottom_line_clause: '不可抗力按法律规定处理。',
    },
    negotiation_strategy: '以"双方保护"为切入点，指出不可抗力条款对双方都有利。',
    evidence_suggestions: ['了解当地不可抗力相关政策'],
    status: '未处理',
    confidence: 72,
  },
];

// Missing Clauses
const mockMissingClauses: MissingClause[] = [
  {
    id: 'MC-001',
    title: '房屋交付标准和验收条款',
    category: '交付验收',
    importance: 'critical',
    reason: '合同未约定房屋交付时的状态标准（如装修状态、家具家电清单、水电气表底数等），也未约定验收程序。退租时可能因缺乏交付基准而产生争议。',
    suggested_clause: '出租人应在交付日将房屋以____状态交付承租人使用，并附《房屋交付确认书》，载明房屋现状、家具家电清单、水电气表底数、钥匙数量等。双方签字确认后视为交付完成。',
    legal_basis: '《民法典》第708条：出租人应当按照约定将租赁物交付承租人',
  },
  {
    id: 'MC-002',
    title: '个人信息保护条款',
    category: '数据保护',
    importance: 'high',
    reason: '合同涉及双方身份信息、联系方式等个人信息，但未约定个人信息的使用范围、保密义务和违规责任。',
    suggested_clause: '双方应对因本合同获取的对方个人信息（包括但不限于身份证号、联系方式、银行账号等）承担保密义务，不得向第三方披露或用于本合同目的以外的用途。',
    legal_basis: '《个人信息保护法》第6条：处理个人信息应当具有明确、合理的目的',
  },
  {
    id: 'MC-003',
    title: '房屋附属设施设备清单',
    category: '标的描述',
    importance: 'high',
    reason: '合同未列明房屋内的家具、家电、设施设备清单及其状态，退租时可能因设备缺失或损坏产生争议。',
    suggested_clause: '房屋内家具、家电及设施设备详见附件《设施设备清单》，双方应在交付时逐项确认并签字。退租时按清单逐项交接。',
    legal_basis: '交易习惯及《民法典》第509条诚信原则',
  },
  {
    id: 'MC-004',
    title: '税费承担条款',
    category: '税费',
    importance: 'medium',
    reason: '合同未约定租赁相关税费（如房产税、个人所得税、增值税、印花税等）由哪方承担，以及是否需要开具发票。',
    suggested_clause: '因本合同产生的税费，按照法律规定由各自的纳税义务人承担。如承租人需要出租人开具租金发票，出租人应予配合，相关税费由____方承担。',
    legal_basis: '《税收征收管理法》相关规定',
  },
];

// Favorable Clauses
const mockFavorableClauses: FavorableClause[] = [
  {
    id: 'FC-001',
    title: '优先续租权',
    clause_location: '第十二条',
    original_text: '租赁期满前三十日，承租人如需续租，在同等条件下享有优先续租权。',
    reason: '优先续租权保护了承租人的稳定居住预期，避免租期届满后被迫搬离。这是对承租人有利的条款。',
    recommendation: '建议保留，并进一步明确"同等条件"的具体含义和续租程序。',
  },
  {
    id: 'FC-002',
    title: '租金支付宽限期',
    clause_location: '第三条第3款',
    original_text: '承租人逾期支付租金未超过五日的，不视为违约。',
    reason: '5天的宽限期为承租人提供了一定的缓冲时间，避免因银行转账延迟等非主观原因被认定为违约。',
    recommendation: '建议保留。如可能，争取延长至7-10日。',
  },
  {
    id: 'FC-003',
    title: '承租人装修权',
    clause_location: '第七条',
    original_text: '经出租人书面同意，承租人可以对房屋进行合理装修和改善，装修费用由承租人承担。',
    reason: '允许承租人进行合理装修，有利于提升居住体验。但需注意装修残值在退租时的处理。',
    recommendation: '建议保留，并补充约定退租时装修残值的处理方式（如恢复原状或折价补偿）。',
  },
];

// Pending Facts
const mockPendingFacts: PendingFact[] = [
  {
    id: 'PF-001',
    field: '房屋产权证明',
    reason: '需确认出租人是否为房屋所有权人或合法转租人，避免无权处分风险',
    impact: '如出租人非产权人且未获授权，合同可能因无权处分而产生效力争议',
  },
  {
    id: 'PF-002',
    field: '房屋是否存在抵押或查封',
    reason: '需查询房屋是否存在抵押登记或司法查封，影响承租人的居住稳定性',
    impact: '如房屋被拍卖，"买卖不破租赁"规则的适用可能受限',
  },
  {
    id: 'PF-003',
    field: '房屋实际用途是否符合规划',
    reason: '需确认房屋规划用途是否为住宅，商业用房作为住宅出租可能存在合规风险',
    impact: '如房屋用途不符合规划，可能面临行政处罚或合同效力争议',
  },
  {
    id: 'PF-004',
    field: '出租人是否已告知共有人或配偶',
    reason: '如房屋为共有财产，需全体共有人同意出租',
    impact: '未经共有人同意的出租行为可能被主张无效',
  },
];

// ==================== MAIN REPORT OBJECT ====================

export const mockDeepReport: DeepReviewReport = {
  id: 1,
  report_no: 'LAR-2026-0514-001',
  generated_at: '2026-05-14 10:30:00',
  version: 'v2.0',
  contract_basic_info: {
    contract_type: '房屋租赁合同',
    contract_name: '北京市朝阳区某小区房屋租赁合同',
    party_a: '张某某（出租人）',
    party_b: '李某某（承租人）',
    user_role: '承租方',
    amount: '月租金 ¥20,000 / 年租金 ¥240,000',
    term: '2026年6月1日至2029年5月31日（三年）',
    signing_date: '2026年5月20日',
    performance_location: '北京市朝阳区某路某号某小区X栋X单元XXX室',
    payment_method: '月付，每月5日前支付当月租金',
    dispute_resolution: '诉讼',
    jurisdiction: '北京市朝阳区人民法院',
    pages: 8,
    total_clauses: 14,
  },
  executive_summary: {
    overall_risk_level: '高',
    signing_recommendation: '修改后签署',
    top5_risks: [
      '维修责任全部转嫁承租人，违反法定义务分配（重大）',
      '违约金过高（全年租金30%），可能被法院酌减（重大）',
      '承租人解除权被不当限制，排除法定解除权（高）',
      '押金退还条件不明确，出租人可能无理由扣押（高）',
      '租金调整机制缺失，出租人可能单方涨租（高）',
    ],
    top5_modifications: [
      '区分结构性维修与日常维护责任',
      '将违约金调整为合理水平（1-2个月租金）并增加对等条款',
      '删除"不得以任何理由解除"，保留法定解除权',
      '明确押金退还时限和标准，区分正常磨损',
      '设定租金年度调整上限（建议5%-8%）',
    ],
    pending_facts: [
      '需核实出租人产权证明',
      '需查询房屋抵押/查封状态',
      '需确认房屋规划用途',
      '需确认共有人是否知情同意',
    ],
    lawyer_review_recommended: true,
    summary_text: '本合同整体风险偏高，存在2项重大风险和3项高风险。主要问题集中在：(1)维修责任分配严重失衡；(2)违约金条款单向且过高；(3)承租人解除权被不当限制。合同多处条款可能构成格式条款中"不合理加重对方责任"的情形。建议在签署前就上述条款与出租人充分协商修改，并强烈建议由执业律师进行人工复核。\n\n⚠️ 特别提示：本合同中"出租人不承担任何维修义务"和"承租人不得以任何理由提前解除"两项条款可能因违反法律强制性规定而无效，但无效条款的存在仍可能导致履约期间的争议和纠纷成本。',
  },
  contract_structure: {
    purpose: '出租人将其所有的住宅房屋出租给承租人用于居住，承租人按月支付租金',
    main_obligations: [
      '出租人义务：交付房屋、保证房屋可正常使用、不干扰承租人正常使用',
      '承租人义务：按时支付租金和押金、合理使用房屋、不擅自转租、到期返还房屋',
    ],
    payment_arrangement: '月租金20,000元，每月5日前支付当月租金，押金40,000元（两个月租金）',
    delivery_arrangement: '2026年6月1日交付，交付时提供钥匙',
    acceptance_arrangement: '未约定验收标准和程序（⚠️ 缺失）',
    breach_liability: '承租人违约金为全年租金30%（72,000元），出租人违约责任未明确约定（⚠️ 失衡）',
    termination: '租期届满自然终止；承租人不得提前解除（⚠️ 排除法定解除权）',
    dispute_resolution: '诉讼，北京市朝阳区人民法院管辖',
    attachments: ['无附件（⚠️ 建议增加设施设备清单、房屋现状确认书）'],
  },
  risk_matrix: {
    critical: 2,
    high: 3,
    medium: 3,
    low: 1,
  },
  citation_audit: {
    schema_version: 'citation-audit-v1',
    status: 'warn',
    score: 82,
    source_count: 6,
    citation_count: 9,
    risk_count: 9,
    cited_risk_count: 8,
    verified_source_count: 4,
    reviewable_source_count: 6,
    verified_ratio: 0.67,
    reviewable_ratio: 1,
    risk_citation_coverage: 0.89,
    source_type_counts: { law: 3, judicial_interpretation: 1, practice_reference: 2 },
    high_risk_without_verified_citation: ['R-003'],
    weak_source_ids: [],
    missing_appendix_source_ids: [],
    duplicate_source_ids: [],
    recommended_actions: ['Verify cited authorities for high-risk items: R-003'],
  },
  evidence_audit: {
    schema_version: 'evidence-audit-v1',
    status: 'warn',
    score: 84,
    risk_count: 9,
    risk_with_evidence_count: 8,
    risk_evidence_coverage: 0.89,
    evidence_suggestion_count: 18,
    framework_evidence_count: 6,
    pending_fact_count: 4,
    blocking_pending_fact_count: 1,
    risks_without_evidence_plan: ['R-009'],
    high_risk_without_evidence_plan: [],
    blocking_pending_fact_ids: ['PF-001'],
    duplicate_evidence_suggestions: [],
    recommended_actions: ['Resolve blocking pending facts: PF-001'],
    evidence_tasks: [
      {
        task_id: 'EV-001',
        type: 'pending_fact',
        target: 'PF-001',
        priority: 'high',
        description: 'Resolve pending fact before external delivery: 需核实出租人产权证明',
      },
    ],
  },
  risk_scoring: {
    schema_version: 'risk-scoring-v1',
    overall_score: 86,
    overall_level: 'high',
    risk_count: 9,
    counts: { critical: 2, high: 3, medium: 3, low: 1 },
    top_risk_ids: ['R-001', 'R-002', 'R-003'],
    score_distribution: { max: 93, average: 68.4, top3_average: 85.3 },
    risk_scores: [
      {
        risk_id: 'R-001',
        score: 93,
        score_level: 'critical',
        citation_score: 92,
        grounding_score: 100,
        revision_score: 100,
        evidence_confidence_score: 96,
        penalty: 0,
        priority_rank: 1,
        explanation: 'Weighted deterministic score.',
      },
    ],
  },
  risk_items: mockRiskItems,
  missing_clauses: mockMissingClauses,
  favorable_clauses: mockFavorableClauses,
  pending_facts: mockPendingFacts,
  legal_source_appendix: mockLegalSources,
  disclaimer: '【免责声明】\n\n本报告由"律审雷达"AI辅助法律审查系统自动生成，仅供参考，不构成法律意见。\n\n1. 本报告基于用户提交的合同文本进行分析，不对合同文本的真实性、完整性负责。\n2. 本报告中引用的法律条文、司法解释、案例等法律依据均标注了来源类型和校验状态，标注为"待核验"或"未检索到"的依据需要用户自行核实。\n3. 本报告不能替代执业律师的专业判断。对于重大交易、高风险条款或复杂法律问题，强烈建议咨询执业律师。\n4. 法律法规可能随时修订，本报告基于分析时点的现行有效法律，不保证未来适用性。\n5. 本报告中的替代条款仅为参考建议，具体条款应根据交易实际情况和双方协商结果确定。\n6. 使用本报告即表示用户理解并接受上述限制。如需正式法律服务，请联系持有执业证书的律师。\n\n报告生成时间：2026年5月14日\n系统版本：律审雷达 v2.0\n审查深度：深度审查（8-Agent Pipeline）',
};
