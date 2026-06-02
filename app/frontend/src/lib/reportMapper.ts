/**
 * Maps the AI backend response (DeepReviewReport from deepReviewApi.ts)
 * to the frontend display format (DeepReviewReport from mockData.ts)
 */
import type {
  DeepReviewReport as FrontendReport,
  RiskItemDetail,
  LegalSource,
  MissingClause,
  FavorableClause,
  PendingFact,
  RiskMatrix,
  LegalAnalysis,
  RevisionPlan,
} from './mockData';
import type { DeepReviewReport as AIReport } from './deepReviewApi';

// Map AI risk level string to frontend risk level key
function mapRiskLevel(level: string): 'critical' | 'high' | 'medium' | 'low' {
  const map: Record<string, 'critical' | 'high' | 'medium' | 'low'> = {
    '重大': 'critical',
    '高': 'high',
    '中': 'medium',
    '低': 'low',
  };
  return map[level] || 'medium';
}

// Map AI source_type to frontend source_type key
function mapSourceType(sourceType: string): string {
  const map: Record<string, string> = {
    '法律': 'LAW',
    '行政法规': 'ADMIN_REG',
    '司法解释': 'JUDICIAL_INTERPRETATION',
    '部门规章': 'DEPARTMENT_RULE',
    '地方性法规': 'LOCAL_REG',
    '指导性案例': 'GUIDING_CASE',
    '人民法院案例库参考案例': 'REFERENCE_CASE',
    '普通裁判文书': 'JUDGMENT',
    '实务清单': 'TEMPLATE',
    '学理观点': 'COMMENTARY',
  };
  return map[sourceType] || sourceType;
}

function text(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map(text).filter(Boolean).join('；');
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const oldText = text(record.old_text);
    const newText = text(record.new_text);
    if (oldText || newText) return `将「${oldText || '原内容'}」改为「${newText || '新内容'}」`;

    const preferred = [
      'action',
      'title',
      'name',
      'field',
      'text',
      'value',
      'message',
      'description',
      'reason',
      'risk',
      'risk_impact',
      'impact',
      'recommendation',
      'suggestion',
    ];
    const selected = preferred.map((key) => text(record[key])).filter(Boolean);
    if (selected.length) return selected.join('；');

    return Object.entries(record)
      .map(([key, entry]) => {
        const rendered = text(entry);
        return rendered ? `${key}：${rendered}` : '';
      })
      .filter(Boolean)
      .join('；');
  }
  return String(value).trim();
}

function hasText(value: unknown): boolean {
  return text(value).length > 0;
}

function toTextList(value: unknown): string[] {
  const items = Array.isArray(value) ? value : value === null || value === undefined || value === '' ? [] : [value];
  return items.map(text).filter(Boolean);
}

const GENERIC_FAVORABLE_REASON = '该条款对当前审查立场相对有利，但仍需结合全文和履行事实复核。';
const GENERIC_FAVORABLE_RECOMMENDATION = '保留；如与其他条款冲突，应同步微调。';

function normalizeTextKey(value: string): string {
  return value.replace(/\s+/g, '').toLowerCase();
}

function isGenericText(value: string, generic: string): boolean {
  return normalizeTextKey(value) === normalizeTextKey(generic);
}

function favorableRecommendation(reference: string, originalText: string, reason: string): string {
  const blob = `${reference}\n${originalText}\n${reason}`.toLowerCase();
  if (blob.includes('insurance') || blob.includes('保险')) {
    return '建议保留完整保险安排，并进一步核对投保责任主体、保险金额、承保险别和索赔文件，避免 CIF/FOB 选择后责任主体不清。';
  }
  if (blob.includes('arbitration') || blob.includes('gafta') || blob.includes('仲裁')) {
    return '建议保留专业仲裁机制，同时补充仲裁语言、仲裁员人数、送达方式和紧急救济安排，确保争议解决条款可执行。';
  }
  if (blob.includes('governing law') || blob.includes('english law') || blob.includes('适用法律')) {
    return '建议保留适用法条款，但需与仲裁地、合同履行地和强制性法律规定一并复核，避免法律适用与争议解决安排冲突。';
  }
  if (blob.includes('quality') || blob.includes('surveyor') || blob.includes('inspection') || blob.includes('质量') || blob.includes('检验')) {
    return '建议保留独立第三方检验安排，并补充检验机构资质、检验地点、异议复检程序和费用承担，降低质量争议。';
  }
  return '建议保留该条款的核心安排，并结合全文校验其与风险转移、付款、验收、违约责任和争议解决条款是否一致。';
}

// Map AI citation to frontend LegalSource
function mapCitationToLegalSource(citation: AIReport['risk_items'][0]['citations'][0], index: number): LegalSource {
  return {
    source_id: text(citation.source_id) || `LS-${String(index + 1).padStart(3, '0')}`,
    title: text(citation.source_name),
    source_type: mapSourceType(text(citation.source_type)),
    authority_level: text(citation.authority_level),
    issuing_body: '', // Not available in AI response
    article_number: text(citation.article_or_case_number),
    text_excerpt: text(citation.text_excerpt_or_holding),
    legal_effect_note: text(citation.legal_effect_note),
    effective_status: '待核验', // Default since AI doesn't provide this
    verification_status: text(citation.verification_status) || '待核验',
    confidence: citation.confidence || 0,
    applicability_reason: text(citation.relevance_reason),
    source_url: '',
    checked_at: new Date().toISOString().split('T')[0],
  };
}

function buildCitationLookup(aiReport: AIReport): Map<string, LegalSource> {
  const lookup = new Map<string, LegalSource>();
  for (const risk of aiReport.risk_items || []) {
    for (const citation of risk.citations || []) {
      if (!citation?.source_id || lookup.has(citation.source_id)) continue;
      lookup.set(citation.source_id, mapCitationToLegalSource(citation, lookup.size));
    }
  }
  return lookup;
}

// Map AI risk item to frontend RiskItemDetail
function mapRiskItem(item: AIReport['risk_items'][0], index: number): RiskItemDetail {
  const legalAnalysis: LegalAnalysis = {
    legal_relationship: text(item.legal_analysis?.legal_relationship),
    applicable_rule: text(item.legal_analysis?.applicable_rule),
    application_to_clause: text(item.legal_analysis?.application_to_clause),
    user_impact: text(item.legal_analysis?.user_impact),
    counterparty_argument: text(item.legal_analysis?.counterparty_argument),
    court_focus: text(item.legal_analysis?.court_or_arbitration_focus),
    burden_of_proof: text(item.legal_analysis?.burden_of_proof),
    evidence_suggestions: toTextList(item.legal_analysis?.evidence_suggestion),
  };

  const revisionPlan: RevisionPlan = {
    delete_items: toTextList(item.revision_plan?.delete),
    add_items: toTextList(item.revision_plan?.add),
    replace_items: toTextList(item.revision_plan?.replace),
    conservative_clause: text(item.revision_plan?.conservative_clause),
    balanced_clause: text(item.revision_plan?.balanced_clause),
    bottom_line_clause: text(item.revision_plan?.bottom_line_clause),
  };

  const legalSources: LegalSource[] = (item.citations || []).map((c, i) => mapCitationToLegalSource(c, i));

  return {
    risk_id: text(item.risk_id) || `R-${String(index + 1).padStart(3, '0')}`,
    risk_no: text(item.risk_id) || `R-${String(index + 1).padStart(3, '0')}`,
    title: text(item.title) || '未命名风险',
    risk_level: mapRiskLevel(text(item.risk_level)),
    risk_type: '法律风险', // Default; AI response has risk_type in risk_matrix
    clause_location: text(item.original_clause?.clause_number),
    page_number: item.original_clause?.page_number || 0,
    original_clause_text: text(item.original_clause?.text),
    issue_location: text(item.issue_location),
    probability: '中',
    severity: '中',
    priority: index + 1,
    legal_analysis: legalAnalysis,
    legal_sources: legalSources,
    revision_plan: revisionPlan,
    negotiation_strategy: text(item.revision_plan?.negotiation_strategy),
    evidence_suggestions: toTextList(item.legal_analysis?.evidence_suggestion),
    status: text(item.status) || '未处理',
    confidence: 80,
  };
}

// Build risk matrix from AI risk items
function buildRiskMatrix(aiReport: AIReport): RiskMatrix {
  const matrix: RiskMatrix = { critical: 0, high: 0, medium: 0, low: 0 };

  // Use risk_matrix array if available
  if (aiReport.risk_matrix && Array.isArray(aiReport.risk_matrix)) {
    for (const item of aiReport.risk_matrix) {
      const level = mapRiskLevel(item.risk_level);
      matrix[level]++;
    }
  } else if (aiReport.risk_items) {
    // Fallback: count from risk_items
    for (const item of aiReport.risk_items) {
      const level = mapRiskLevel(item.risk_level);
      matrix[level]++;
    }
  }

  return matrix;
}

// Map AI risk_matrix items to enrich risk_items with risk_type, probability, severity
function enrichRiskItems(riskItems: RiskItemDetail[], aiRiskMatrix: AIReport['risk_matrix']): RiskItemDetail[] {
  if (!aiRiskMatrix || !Array.isArray(aiRiskMatrix)) return riskItems;

  const matrixMap = new Map(aiRiskMatrix.map(m => [m.risk_id, m]));

  return riskItems.map(item => {
    const matrixItem = matrixMap.get(item.risk_id);
    if (matrixItem) {
      return {
        ...item,
        risk_type: text(matrixItem.risk_type) || item.risk_type,
        probability: text(matrixItem.probability) || item.probability,
        severity: text(matrixItem.severity) || item.severity,
        priority: matrixItem.priority || item.priority,
      };
    }
    return item;
  });
}

/**
 * Main mapping function: converts AI API response to frontend display format
 */
export function mapAIReportToFrontend(aiReport: AIReport): FrontendReport {
  const meta = aiReport.report_meta;
  const summary = aiReport.executive_summary;
  const contractSummary = aiReport.contract_summary;
  const citationLookup = buildCitationLookup(aiReport);

  // Map risk items
  let riskItems: RiskItemDetail[] = (aiReport.risk_items || []).map((item, i) => mapRiskItem(item, i));
  riskItems = enrichRiskItems(riskItems, aiReport.risk_matrix);

  // Map missing clauses
  const missingClauses: MissingClause[] = (aiReport.missing_clauses || [])
    .filter((mc) => {
      const raw = mc as unknown as Record<string, unknown>;
      return (
        hasText(mc.name) ||
        hasText(raw.clause_name) ||
        hasText(raw.missing_clause_name) ||
        hasText(mc.risk) ||
        hasText(raw.risk_description) ||
        hasText(raw.risk_if_missing) ||
        hasText(mc.recommended_clause) ||
        hasText(raw.recommendation) ||
        hasText(raw.recommended_clause_text)
      );
    })
    .map((mc, i) => {
      const raw = mc as unknown as Record<string, unknown>;
      const citationIds = toTextList(mc.citations);
      return {
        id: `MC-${String(i + 1).padStart(3, '0')}`,
        title: text(mc.name) || text(raw.clause_name) || text(raw.missing_clause_name) || '建议补充条款',
        category: '合同条款',
        importance: 'high' as const,
        reason:
          text(mc.risk) ||
          text(raw.risk_description) ||
          text(raw.risk_if_missing) ||
          '缺少该条款可能导致权利义务或争议处理不明确。',
        suggested_clause:
          text(mc.recommended_clause) ||
          text(raw.recommended_clause_text) ||
          text(raw.recommendation) ||
          '建议结合交易背景补充具体、可执行的条款文本。',
        legal_basis: citationIds.join('、') || '待补充/待核验',
      };
    });

  // Map favorable clauses
  const favorableClauses: FavorableClause[] = (aiReport.favorable_clauses || [])
    .filter((fc) => {
      const raw = fc as unknown as Record<string, unknown>;
      return (
        hasText(fc.clause_reference) ||
        hasText(fc.reason) ||
        hasText(fc.keep_or_modify) ||
        hasText(raw.analysis) ||
        hasText(raw.text)
      );
    })
    .map((fc, i) => {
      const raw = fc as unknown as Record<string, unknown>;
      const reference = text(fc.clause_reference) || text(raw.clause_number) || '有利条款';
      const originalText = text(raw.original_text) || text(raw.text);
      const analysis = text(raw.analysis) || text(raw.favorable_reason) || text(raw.advantage) || text(raw.benefit);
      let reason = text(fc.reason) || analysis || '该条款对当前审查立场相对有利，但需结合全文复核。';
      if (isGenericText(reason, GENERIC_FAVORABLE_REASON) && analysis) {
        reason = analysis;
      }
      let recommendation = text(fc.keep_or_modify) || text(raw.recommendation);
      if (!recommendation || isGenericText(recommendation, GENERIC_FAVORABLE_RECOMMENDATION)) {
        recommendation = favorableRecommendation(reference, originalText, reason);
      }
      return {
        id: `FC-${String(i + 1).padStart(3, '0')}`,
        title: reference,
        clause_location: reference || '未定位',
        original_text: originalText,
        reason,
        recommendation,
      };
    });

  // Map pending facts
  const pendingFacts: PendingFact[] = (aiReport.pending_facts || []).map((pf, i) => {
    const raw = pf as unknown as Record<string, unknown>;
    return {
      id: `PF-${String(i + 1).padStart(3, '0')}`,
      field: text(raw.field) || text(pf) || '待补事实',
      reason: text(raw.reason) || '需补充后再形成稳定判断。',
      impact: text(raw.impact) || '可能影响风险等级、修改建议或证据策略。',
    };
  });

  // Map legal authority appendix to LegalSource[]
  const legalSourceAppendix: LegalSource[] = (aiReport.legal_authority_appendix || [])
    .filter((la) => hasText(la.source_id) || hasText(la.source_name))
    .map((la, i) => {
      const hydrated = la.source_id ? citationLookup.get(la.source_id) : undefined;
      return {
        source_id: la.source_id || `LA-${String(i + 1).padStart(3, '0')}`,
        title: text(la.source_name) || hydrated?.title || '待核验来源',
        source_type: mapSourceType(text(la.source_type) || hydrated?.source_type || '实务清单'),
        authority_level: text(la.authority_level) || hydrated?.authority_level || '需核验',
        issuing_body: hydrated?.issuing_body || '',
        article_number: text(la.article_or_case_number) || hydrated?.article_number || '',
        text_excerpt: text(la.text_excerpt_or_holding) || hydrated?.text_excerpt || '暂无条文摘录，请以权威法库复核为准。',
        legal_effect_note: text(la.legal_effect_note) || hydrated?.legal_effect_note || '需进一步核验效力和适用性。',
        effective_status: hydrated?.effective_status || '待核验',
        verification_status: text(la.verification_status) || hydrated?.verification_status || '待核验',
        confidence: typeof la.confidence === 'number' ? la.confidence : hydrated?.confidence || 0,
        applicability_reason:
          text(la.relevance_reason) ||
          hydrated?.applicability_reason ||
          `被以下风险项引用: ${toTextList(la.cited_by_risks).join(', ') || '未明确'}`,
        source_url: hydrated?.source_url || '',
        checked_at: new Date().toISOString().split('T')[0],
      };
    });

  // Build the frontend report
  const frontendReport: FrontendReport = {
    id: Date.now(),
    report_no: meta?.report_id || `LAR-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-001`,
    generated_at: meta?.generated_at || new Date().toISOString(),
    version: 'v2.0-AI',
    contract_basic_info: {
      contract_type: meta?.document_type || '合同',
      contract_name: contractSummary?.purpose || '法律文书',
      party_a: '（由AI从文书中提取）',
      party_b: '（由AI从文书中提取）',
      user_role: meta?.user_role || '甲方',
      amount: contractSummary?.payment_terms || '见合同约定',
      term: contractSummary?.term || '见合同约定',
      signing_date: '',
      performance_location: '',
      payment_method: contractSummary?.payment_terms || '',
      dispute_resolution: contractSummary?.dispute_resolution || '',
      jurisdiction: meta?.jurisdiction || '中国大陆',
      pages: 0,
      total_clauses: aiReport.risk_items?.length || 0,
    },
    executive_summary: {
      overall_risk_level: meta?.overall_risk_level || '中',
      signing_recommendation: meta?.recommendation || '修改后签署',
      top5_risks: toTextList(summary?.top_risks).slice(0, 5),
      top5_modifications: toTextList(summary?.priority_actions).slice(0, 5),
      pending_facts: toTextList(summary?.missing_facts),
      lawyer_review_recommended: meta?.lawyer_review_required ?? true,
      summary_text: `本合同经 AI 深度审查，总体风险等级为"${meta?.overall_risk_level || '中'}"。共发现${riskItems.length}项风险，${missingClauses.length}项缺失条款。签署建议：${meta?.recommendation || '修改后签署'}。`,
    },
    contract_structure: {
      purpose: contractSummary?.purpose || '',
      main_obligations: toTextList(contractSummary?.main_obligations),
      payment_arrangement: contractSummary?.payment_terms || '',
      delivery_arrangement: '',
      acceptance_arrangement: '',
      breach_liability: '',
      termination: '',
      dispute_resolution: contractSummary?.dispute_resolution || '',
      attachments: [],
    },
    risk_matrix: buildRiskMatrix(aiReport),
    risk_items: riskItems,
    missing_clauses: missingClauses,
    favorable_clauses: favorableClauses,
    pending_facts: pendingFacts,
    legal_source_appendix: legalSourceAppendix,
    professional_review_framework: aiReport.professional_review_framework,
    coverage_audit: aiReport.coverage_audit,
    quality_audit: aiReport.quality_audit,
    quality_gate: aiReport.quality_gate,
    delivery_audit: aiReport.delivery_audit,
    human_review_workflow: aiReport.human_review_workflow,
    disclaimer: aiReport.disclaimer || '本报告为 AI 辅助生成的风险提示，不构成正式法律意见；复杂事项请咨询执业律师。',
  };

  return frontendReport;
}
