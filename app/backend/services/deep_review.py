# @File: backend/services/deep_review.py
# @Desc: Deep legal review service - calls an OpenAI-compatible AI gateway with Agent Team prompts
import json
import logging
import re
import time
import uuid
from datetime import datetime
from collections.abc import Awaitable, Callable
from typing import Any, Dict, Optional

from core.config import settings
from services.aihub import AIHubService
from schemas.aihub import GenTxtRequest, ChatMessage
from services.citation_audit import CitationAuditService
from services.document_strategy import build_strategy_pending_facts, get_document_strategy
from services.evidence_audit import EvidenceAuditService
from services.legal_research import LocalLegalResearchService
from services.model_catalog import resolve_model
from services.report_quality_gate import ReportQualityGate
from services.risk_scoring import RiskScoringService

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], Awaitable[None] | None]

STAGE_PROGRESS: dict[str, tuple[int, str]] = {
    "document-preflight": (34, "正在确认文档属于可审查的法律文书。"),
    "stage-1": (42, "Intake Agent 正在识别文书类型、角色、目标和缺失事实。"),
    "stage-1b": (48, "正在选择文书专项审查策略和必审字段。"),
    "stage-2": (56, "Clause Mapping Agent 正在切分条款并定位关键原文。"),
    "stage-2b": (62, "规则预扫描正在捕捉高风险关键词和缺失条款候选。"),
    "stage-3": (72, "Issue Spotter Agent 正在生成风险矩阵、风险项和待补事实。"),
    "stage-4": (80, "Legal Research Agent 正在匹配本地法律依据和实务清单。"),
    "stage-5": (84, "Citation Validator Agent 正在校验引用来源和适用说明。"),
    "stage-6": (90, "Senior Lawyer Review Agent 正在复核风险等级、签署建议和律师复核触发项。"),
    "stage-7": (96, "Drafting Agent 正在生成可复制修改条款和谈判策略。"),
    "stage-8": (98, "Report Assembly Agent 正在整理报告结构和交付质量审计。"),
}

RISK_DIMENSIONS = [
    "主体资格",
    "标的/范围",
    "价款/付款/租金",
    "交付/验收",
    "质量/维修",
    "违约责任",
    "解除/终止",
    "通知送达",
    "保密/知识产权",
    "个人信息/数据",
    "不可抗力",
    "争议解决",
    "附件/签章",
    "税费/发票",
    "证据留存",
]

RISK_KEYWORD_RULES = [
    {
        "rule_id": "unilateral_or_format_terms",
        "title": "单方决定、免责或格式条款效力风险",
        "risk_level": "高",
        "risk_type": "法律风险",
        "keywords": ("单方", "自行决定", "最终解释", "无需通知", "不承担", "免责", "免除", "概不负责"),
        "applicable_rule": "需要核验是否构成格式条款提示说明不足、不合理免除责任、加重对方责任或排除主要权利。",
        "user_impact": "相关条款可能在争议中被限缩解释或被认定为无效，同时增加举证和谈判成本。",
    },
    {
        "rule_id": "breach_liability",
        "title": "违约责任、违约金或赔偿范围需要细化",
        "risk_level": "中",
        "risk_type": "法律风险",
        "keywords": ("违约", "违约金", "赔偿", "损失", "逾期", "滞纳金", "每日", "百分之", "%"),
        "applicable_rule": "需要核验违约责任构成、损失范围、可预见性限制和违约金调整风险。",
        "user_impact": "违约责任过宽或过窄都会影响索赔、抗辩和谈判筹码。",
    },
    {
        "rule_id": "acceptance_quality",
        "title": "交付、验收或质量异议机制不够清晰",
        "risk_level": "中",
        "risk_type": "履约风险",
        "keywords": ("交付", "验收", "检验", "质量", "异议", "视为验收", "合格", "维修", "修缮"),
        "applicable_rule": "需要核验交付标准、验收期限、质量异议通知和维修责任是否可执行。",
        "user_impact": "标准和期限不清会削弱后续主张瑕疵、拒付、维修或赔偿的证据基础。",
    },
    {
        "rule_id": "termination",
        "title": "解除或终止条件及后果需要核验",
        "risk_level": "中",
        "risk_type": "法律风险",
        "keywords": ("解除", "终止", "提前退租", "提前终止", "合同期满", "续租", "不定期", "催告"),
        "applicable_rule": "需要核验约定解除、法定解除、通知期限和解除后的返还结算安排。",
        "user_impact": "解除条件不清会造成退出成本、押金/价款返还和损失赔偿争议。",
    },
    {
        "rule_id": "notice_delivery",
        "title": "通知送达方式和证据留存不足",
        "risk_level": "中",
        "risk_type": "证据风险",
        "keywords": ("通知", "送达", "邮件", "短信", "微信", "地址", "联系人", "变更地址", "书面"),
        "applicable_rule": "需要核验通知方式、送达生效时间、地址变更责任和电子证据留存。",
        "user_impact": "通知无法证明送达时，解除、催告、验收异议和违约追责都可能受影响。",
    },
    {
        "rule_id": "dispute_resolution",
        "title": "争议解决条款可能不明确或不可执行",
        "risk_level": "高",
        "risk_type": "诉讼风险",
        "keywords": ("仲裁", "法院", "管辖", "争议解决", "诉讼", "仲裁委员会", "所在地", "人民法院"),
        "applicable_rule": "需要核验法院管辖或仲裁机构是否明确，避免同时约定诉讼和仲裁导致条款效力争议。",
        "user_impact": "争议解决约定不明会增加立案、管辖异议或仲裁协议效力争议成本。",
    },
    {
        "rule_id": "confidentiality_ip_data",
        "title": "保密、知识产权或数据处理义务需要细化",
        "risk_level": "中",
        "risk_type": "合规风险",
        "keywords": ("保密", "商业秘密", "知识产权", "著作权", "商标", "专利", "个人信息", "数据", "隐私"),
        "applicable_rule": "需要核验保密范围、例外、期限、成果权属、个人信息处理基础和安全义务。",
        "user_impact": "范围和责任不清可能导致成果归属、数据合规和泄密赔偿争议。",
    },
    {
        "rule_id": "labor_special",
        "title": "劳动合同特别规则需要核验",
        "risk_level": "高",
        "risk_type": "合规风险",
        "keywords": ("劳动合同", "试用期", "工资", "劳动报酬", "社保", "竞业限制", "经济补偿", "工时"),
        "applicable_rule": "需要核验劳动合同必备条款、试用期、劳动报酬、社会保险和竞业限制补偿。",
        "user_impact": "劳动用工条款不合规会带来双倍工资、补偿金、社保和仲裁风险。",
    },
    {
        "rule_id": "guarantee_special",
        "title": "担保或保证责任范围需要明确",
        "risk_level": "高",
        "risk_type": "法律风险",
        "keywords": ("担保", "保证", "连带", "一般保证", "保证期间", "抵押", "质押"),
        "applicable_rule": "需要核验保证方式、保证范围、保证期间和担保物权实现条件。",
        "user_impact": "约定不明会影响债权实现或导致保证责任范围超出预期。",
    },
]

MISSING_CLAUSE_RULES = [
    {
        "name": "违约责任",
        "keywords": ("违约", "违约金", "赔偿", "逾期"),
        "risk": "缺少违约责任会降低追责和抗辩的确定性。",
        "recommended_clause": "建议明确违约情形、宽限期、违约金/赔偿计算方式、继续履行和损失减损义务。",
    },
    {
        "name": "解除/终止",
        "keywords": ("解除", "终止", "提前终止", "合同期满"),
        "risk": "缺少解除和终止机制会增加退出成本和结算争议。",
        "recommended_clause": "建议明确约定解除事由、通知期限、解除生效时间、已履行部分结算和资料返还。",
    },
    {
        "name": "通知送达",
        "keywords": ("通知", "送达", "地址", "电子邮件", "联系人"),
        "risk": "缺少通知送达条款会削弱催告、解除、验收异议等关键事实的证明力。",
        "recommended_clause": "建议约定联系人、地址、电子邮箱、送达生效时间、地址变更责任和留痕方式。",
    },
    {
        "name": "争议解决",
        "keywords": ("争议解决", "仲裁", "法院", "管辖", "诉讼"),
        "risk": "缺少明确争议解决条款会增加管辖或仲裁协议效力争议。",
        "recommended_clause": "建议二选一明确约定管辖法院或具体仲裁委员会，并避免诉讼和仲裁并列冲突。",
    },
]

# The complete Agent Team system prompt from v1.2
AGENT_TEAM_SYSTEM_PROMPT = """你是"律审雷达"的法律审查 Agent Team。你的任务是根据用户上传的法律文书、用户角色、案件事实和可检索法律资料，生成结构化、可验证、可复核的法律审查报告。

你必须遵守以下原则：

1. 你不是执业律师，不得宣称输出构成正式法律意见。
2. 不得编造法律条文、案例号、法院名称、裁判日期、法规名称。
3. 如果没有检索到可靠来源，必须标注"依据不足/待核验"，不得假装已核验。
4. 所有法律依据必须说明来源类型、效力层级、适用理由和校验状态。
5. 对于案例，必须区分"指导性案例""人民法院案例库参考案例""普通裁判文书"。
6. 普通裁判文书只能作为类案参考，不得作为裁判依据。
7. 对诉讼、仲裁、律师函、代理词、起诉状、答辩状等高风险内容，必须提示执业律师复核。
8. 输出必须面向中国大陆法域，除非用户另行指定。
9. 不确定的事项要列入"待补事实"，不得强行判断。
10. 修改建议必须具体到可复制条款，不能只写原则性建议。

---

## Agent 角色

你需要依次扮演以下 8 个 Agent 角色，逐步完成审查：

### 1. Intake Agent
任务：识别文书基础信息。
输出：文书类型、法域、用户角色、对方角色、合同目的、合同金额、合同期限、履行地点、争议解决方式、审查重点、待补信息。

### 2. Clause Mapping Agent
任务：把合同切分为条款。
输出：clause_id, clause_number, page_number, title, original_text, context_before, context_after, clause_type。

### 3. Issue Spotter Agent
任务：根据审查清单识别风险和缺失条款。
审查维度：主体资格、标的描述、付款/租金/价款、交付/使用、验收、质量/维修、违约责任、解除/终止、通知送达、保密、知识产权、个人信息/数据、不可抗力、争议解决、附件效力、税费、授权/签章、证据留存。

### 4. Legal Research Agent
任务：为每个风险项检索法律依据、司法解释、案例、实务清单。
输出字段：source_id, source_name, article_or_case_number, source_type, authority_level, legal_effect_note, text_excerpt_or_holding, relevance_reason, verification_status, confidence。

### 5. Citation Validator Agent
任务：校验引用。
必须检查：依据是否存在、条文是否和风险匹配、是否过度推断、是否误把案例当裁判依据、是否缺少适用理由。
输出：pass/fail, correction_suggestion, missing_source_warning。

### 6. Senior Lawyer Review Agent
任务：从资深律师视角复核报告质量。
检查：风险等级是否合理、法律分析是否完整、是否考虑相对方抗辩、是否考虑法院/仲裁关注事实、是否考虑举证责任、替代条款是否可执行、结论是否过度承诺。

### 7. Drafting Agent
任务：生成替代条款。
每个重要风险项至少输出：保守版（最大限度保护用户）、平衡版（更容易谈判接受）、底线版（最低可接受方案）。

### 8. Report Assembly Agent
任务：组装最终报告。
报告必须包含：报告首页、执行摘要、合同结构摘要、风险矩阵、逐条分析、缺失条款、有利条款、待补事实、法律依据附录、免责声明。

---

## 输出风格要求

1. 专业、克制、律师工作底稿风格。
2. 不要使用"绝对违法""必胜""一定无效"等绝对表述，除非来源明确支持。
3. 对每个风险说明：为什么是风险、依据是什么、如何修改、如何谈判、如何保存证据。
4. 不能把商业风险包装成法律结论。
5. 无依据时必须说"当前材料不足，无法判断"。

---

## 质量检查清单

生成报告后，自检：
- 是否每个风险都有原文位置？
- 是否每个高/中风险都有法律依据？
- 是否每个法律依据都有来源类型和效力说明？
- 是否说明了适用理由？
- 是否存在编造条文或案例？
- 是否有待补事实？
- 是否有替代条款三版本？
- 是否有证据建议？
- 是否有法律依据附录？
- 是否避免了正式法律意见表述？

---

## 输出格式

你必须严格按照以下 JSON Schema 输出，不要输出任何其他内容，只输出纯 JSON：

```json
{
  "report_meta": {
    "report_id": "string",
    "generated_at": "ISO datetime string",
    "document_type": "string",
    "jurisdiction": "中国大陆",
    "user_role": "string",
    "overall_risk_level": "低/中/高/重大",
    "recommendation": "可签署/修改后签署/谨慎签署/不建议直接签署",
    "lawyer_review_required": "boolean"
  },
  "executive_summary": {
    "top_risks": ["string"],
    "priority_actions": ["string"],
    "missing_facts": ["string"]
  },
  "contract_summary": {
    "purpose": "string",
    "main_obligations": ["string"],
    "payment_terms": "string",
    "term": "string",
    "dispute_resolution": "string"
  },
  "risk_matrix": [
    {
      "risk_id": "R-001",
      "title": "string",
      "risk_level": "低/中/高/重大",
      "risk_type": "法律风险/商业风险/证据风险/履约风险/合规风险/诉讼风险",
      "clause_reference": "第x页第x条",
      "probability": "低/中/高",
      "severity": "低/中/高",
      "priority": "number"
    }
  ],
  "risk_items": [
    {
      "risk_id": "R-001",
      "title": "string",
      "risk_level": "低/中/高/重大",
      "original_clause": {
        "clause_number": "string",
        "page_number": "number",
        "text": "string"
      },
      "issue_location": "具体问题语句",
      "legal_analysis": {
        "legal_relationship": "string",
        "applicable_rule": "string",
        "application_to_clause": "string",
        "user_impact": "string",
        "counterparty_argument": "string",
        "court_or_arbitration_focus": "string",
        "burden_of_proof": "string",
        "evidence_suggestion": ["string"]
      },
      "citations": [
        {
          "source_id": "string",
          "source_name": "string",
          "article_or_case_number": "string",
          "source_type": "法律/行政法规/司法解释/部门规章/地方性法规/指导性案例/人民法院案例库参考案例/普通裁判文书/实务清单",
          "authority_level": "裁判依据/审判适用依据/类案参照/类案参考/说理参考/实务参考/需核验",
          "legal_effect_note": "string",
          "text_excerpt_or_holding": "string",
          "relevance_reason": "string",
          "verification_status": "已校验/待核验/未检索到",
          "confidence": "number 0-100"
        }
      ],
      "revision_plan": {
        "delete": ["string"],
        "add": ["string"],
        "replace": ["string"],
        "conservative_clause": "string",
        "balanced_clause": "string",
        "bottom_line_clause": "string",
        "negotiation_strategy": "string"
      },
      "status": "未处理/已采纳/暂缓/需律师复核"
    }
  ],
  "missing_clauses": [
    {
      "name": "string",
      "risk": "string",
      "recommended_clause": "string",
      "citations": ["source_id"]
    }
  ],
  "favorable_clauses": [
    {
      "clause_reference": "string",
      "reason": "string",
      "keep_or_modify": "保留/小幅修改"
    }
  ],
  "pending_facts": [
    {
      "field": "string",
      "reason": "string",
      "impact": "string"
    }
  ],
  "legal_authority_appendix": [
    {
      "source_id": "string",
      "source_name": "string",
      "source_type": "string",
      "authority_level": "string",
      "legal_effect_note": "string",
      "cited_by_risks": ["R-001"]
    }
  ],
  "disclaimer": "本报告为 AI 辅助生成的风险提示和文书草稿，不构成正式法律意见；复杂事项请咨询执业律师。"
}
```
"""

STAGE_DELIVERY_CONTRACT = """
你正在为法律审查 SaaS 交付系统生产结构化中间结果，不是普通聊天回复。必须遵守：
1. 每个结论必须能追溯到原文位置、文书类型策略、待补事实或已校验来源之一。
2. 不输出模板化默认文案；如果只能给默认判断，必须说明缺少哪些事实。
3. 不把其他文书类型的模板套入当前文书；必须优先遵循 review_strategy。
4. 涉及法律依据时只能把系统提供或本地检索命中的来源标为已校验，模型推测来源必须待核验。
5. 输出要服务于律师复核和客户交付：字段完整、措辞克制、修改建议可复制、风险可排序。
"""


DOCUMENT_GENERATION_SYSTEM_PROMPT = """你是"律审雷达"的法律文书生成 Agent。你的任务是根据用户提供的案件信息、法律关系和具体需求，从第一性原理出发生成专业的法律文书。

你必须遵守以下原则：

1. 你不是执业律师，生成的文书为草稿，需提示用户请执业律师复核。
2. 不得编造法律条文、案例号、法院名称。
3. 文书格式必须符合中国大陆法律文书规范。
4. 语言必须专业、精确、无歧义。
5. 关键条款必须具体、可执行，不能只写原则性内容。
6. 必须包含必要的法律要素（主体、标的、权利义务、违约责任、争议解决等）。
7. 对于诉讼文书，必须符合法院立案要求的格式。

## 输出格式

输出纯 JSON：
```json
{
  "document_meta": {
    "doc_type": "string",
    "title": "string",
    "generated_at": "ISO datetime",
    "jurisdiction": "中国大陆",
    "disclaimer": "本文书为AI辅助生成的草稿，不构成正式法律文件，请执业律师复核后使用。"
  },
  "content": "完整的法律文书正文（Markdown格式）",
  "key_clauses": [
    {
      "clause_name": "string",
      "clause_text": "string",
      "legal_basis": "string",
      "notes": "string"
    }
  ],
  "review_notes": ["需要用户确认或补充的事项"],
  "legal_references": ["引用的法律依据"]
}
```
"""


class DeepReviewService:
    """Service for generating deep legal review reports using AI."""

    def __init__(
        self,
        review_prompt_extension: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.aihub = AIHubService()
        self.citation_audit = CitationAuditService()
        self.evidence_audit = EvidenceAuditService()
        self.legal_research = LocalLegalResearchService()
        self.quality_gate = ReportQualityGate()
        self.risk_scoring = RiskScoringService()
        self.review_prompt_extension = (review_prompt_extension or "").strip()
        self.progress_callback = progress_callback

    @staticmethod
    def _model_task_for_stage(stage_id: str) -> str:
        fast_stages = {"document-preflight", "stage-1", "stage-1b", "stage-2", "stage-2b", "stage-5"}
        review_stages = {"stage-3", "stage-4", "stage-6", "stage-7", "stage-8", "document-generation"}
        if stage_id in fast_stages:
            return "fast"
        if stage_id in review_stages:
            return "review"
        return "review"

    def _stage_prompt(self, stage_instruction: str) -> str:
        prompt = STAGE_DELIVERY_CONTRACT
        if self.review_prompt_extension:
            prompt += "\n\n## 当前激活的运营 Prompt 版本\n" + self.review_prompt_extension
        return prompt + stage_instruction

    async def _emit_progress(
        self,
        *,
        stage_id: str,
        stage_name: str,
        status: str = "running",
        detail: Optional[str] = None,
        percent: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self.progress_callback:
            return
        default_percent, default_detail = STAGE_PROGRESS.get(stage_id, (60, "正在执行深度法律审查。"))
        payload: dict[str, Any] = {
            "phase": "analyzing",
            "stage_id": stage_id,
            "stage_name": stage_name,
            "status": status,
            "detail": detail or default_detail,
            "percent": percent if percent is not None else default_percent,
        }
        if extra:
            payload.update(extra)
        try:
            result = self.progress_callback(payload)
            if result is not None:
                await result
        except Exception as exc:
            logger.debug("Review progress callback failed: %s", exc)

    def _looks_like_legal_document(self, document_text: str) -> bool:
        normalized = re.sub(r"\s+", "", document_text or "")
        if not normalized:
            return False

        strong_markers = (
            "合同", "协议", "起诉状", "答辩状", "律师函", "仲裁申请", "判决书", "裁定书",
            "调解书", "授权委托书", "保密协议", "竞业限制", "劳动合同", "租赁合同",
            "买卖合同", "借款合同", "担保合同", "股权转让",
        )
        if any(marker in normalized[:3000] for marker in strong_markers):
            return True

        weak_markers = (
            "甲方", "乙方", "出租人", "承租人", "出卖人", "买受人", "贷款人", "借款人",
            "违约责任", "争议解决", "人民法院", "仲裁委员会", "签订", "履行", "标的",
            "价款", "租金", "押金", "保证金", "生效", "解除", "管辖", "送达",
        )
        score = sum(1 for marker in weak_markers if marker in normalized[:6000])
        return score >= 3

    async def _check_document_is_legal(self, document_text: str) -> Optional[str]:
        """
        Pre-check whether the uploaded document is a legal document.
        Returns None if it's a legal document, or an error message if not.
        """
        if self._looks_like_legal_document(document_text):
            return None

        check_prompt = """你是一个文档分类助手。请判断以下文本是否属于法律文书范畴。

法律文书包括但不限于：合同、协议、起诉状、答辩状、律师函、仲裁申请书、判决书、裁定书、调解书、公证书、授权委托书、保密协议、竞业禁止协议、劳动合同、租赁合同、买卖合同、服务协议、借款合同、担保合同、股权转让协议等。

非法律文书包括：学术论文、作业、新闻报道、小说、诗歌、技术文档、产品说明书、菜谱、日记、聊天记录等。

请只回答一个 JSON：
{"is_legal_document": true/false, "detected_type": "检测到的文档类型", "reason": "判断理由"}

以下是待判断的文本（前2000字）：
"""
        text_preview = document_text[:2000]
        
        messages = [
            ChatMessage(role="system", content=check_prompt),
            ChatMessage(role="user", content=text_preview),
        ]

        request = GenTxtRequest(
            messages=messages,
            model=resolve_model(settings.app_ai_fast_model, task="fast"),
            stream=False,
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"},
        )

        try:
            response = await self.aihub.gentxt(request)
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            if not result.get("is_legal_document", True):
                detected_type = result.get("detected_type", "未知类型")
                reason = result.get("reason", "")
                return f"该文档被识别为「{detected_type}」，不属于法律合同或文书范畴，无法进行法律审查。{reason}"
            return None
        except Exception as e:
            logger.warning(f"Document type check failed (proceeding anyway): {e}")
            # If the check fails, proceed with the review anyway
            return None

    def _extract_json(self, content: str) -> Any:
        """Extract JSON from a model response that may contain markdown fences."""
        raw = (content or "").strip()
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw:
            raw = raw.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = min([idx for idx in [raw.find("{"), raw.find("[")] if idx >= 0], default=-1)
            end = max(raw.rfind("}"), raw.rfind("]"))
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise

    async def _call_json_agent(
        self,
        *,
        stage_id: str,
        stage_name: str,
        system_prompt: str,
        user_payload: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[Any, Dict[str, Any]]:
        """Run one bounded agent step and return parsed JSON plus trace metadata."""
        started = time.time()
        model = resolve_model(model or settings.app_ai_review_model, task=self._model_task_for_stage(stage_id))
        messages = [
            ChatMessage(role="system", content=system_prompt.strip()),
            ChatMessage(
                role="user",
                content=(
                    "请只输出 JSON，不要输出 Markdown 或解释文字。\n\n"
                    + json.dumps(user_payload, ensure_ascii=False, indent=2)
                ),
            ),
        ]
        request = GenTxtRequest(
            messages=messages,
            model=model,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        await self._emit_progress(stage_id=stage_id, stage_name=stage_name, status="running")
        try:
            response = await self.aihub.gentxt(request)
            repair_trace: dict[str, Any] | None = None
            try:
                parsed = self._extract_json(response.content)
            except Exception as parse_exc:
                try:
                    parsed, repair_trace = await self._repair_json_response(
                        stage_name=stage_name,
                        raw_content=response.content,
                        parse_error=str(parse_exc),
                        model=model,
                        max_tokens=max_tokens,
                    )
                except Exception as repair_exc:
                    logger.warning(
                        "Agent stage returned malformed JSON after repair: %s - parse=%s repair=%s",
                        stage_name,
                        parse_exc,
                        repair_exc,
                    )
                    await self._emit_progress(
                        stage_id=stage_id,
                        stage_name=stage_name,
                        status="completed",
                        detail=f"{stage_name} 输出 JSON 解析失败，系统将使用规则预扫描结果继续。{repair_exc}",
                    )
                    return {}, {
                        "stage_id": stage_id,
                        "stage_name": stage_name,
                        "status": "parse_error",
                        "model": model,
                        "duration_ms": int((time.time() - started) * 1000),
                        "error": str(repair_exc),
                        "parse_error": str(parse_exc),
                        "raw_length": len(response.content or ""),
                        "usage": getattr(response, "usage", None),
                    }
            trace = {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "status": "completed",
                "model": model,
                "duration_ms": int((time.time() - started) * 1000),
                "usage": response.usage,
            }
            if repair_trace:
                trace["json_repair"] = repair_trace
            await self._emit_progress(
                stage_id=stage_id,
                stage_name=stage_name,
                status="completed",
                extra={"duration_ms": trace["duration_ms"]},
            )
            return parsed, trace
        except Exception as exc:
            logger.error("Agent stage failed: %s - %s", stage_name, exc)
            await self._emit_progress(
                stage_id=stage_id,
                stage_name=stage_name,
                status="error",
                detail=f"{stage_name} 执行失败：{exc}",
            )
            return {}, {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "status": "error",
                "model": model,
                "duration_ms": int((time.time() - started) * 1000),
                "error": str(exc),
            }

    async def _repair_json_response(
        self,
        *,
        stage_name: str,
        raw_content: str,
        parse_error: str,
        model: str,
        max_tokens: int,
    ) -> tuple[Any, dict[str, Any]]:
        """Ask the model to convert a malformed response into strict JSON once."""
        started = time.time()
        repair_prompt = """
你是 JSON 修复器。输入是一段法律审查 Agent 的输出，它本应是 JSON，但可能包含 Markdown、注释、截断前后缀或轻微格式错误。
任务：只修复为合法 JSON，尽量保留原有字段和值；不要新增法律分析内容；不要输出 Markdown。
"""
        clipped = (raw_content or "")[: max(2000, min(18000, max_tokens * 2))]
        request = GenTxtRequest(
            messages=[
                ChatMessage(role="system", content=repair_prompt.strip()),
                ChatMessage(
                    role="user",
                    content=json.dumps(
                        {
                            "stage_name": stage_name,
                            "parse_error": parse_error,
                            "raw_output": clipped,
                        },
                        ensure_ascii=False,
                    ),
                ),
            ],
            model=model,
            stream=False,
            temperature=0.0,
            max_tokens=max(2048, min(max_tokens, 10000)),
            response_format={"type": "json_object"},
        )
        response = await self.aihub.gentxt(request)
        parsed = self._extract_json(response.content)
        return parsed, {
            "status": "completed",
            "duration_ms": int((time.time() - started) * 1000),
            "parse_error": parse_error,
            "usage": response.usage,
        }

    def _document_excerpt(self, document_text: str, limit: int = 45_000) -> str:
        if len(document_text) <= limit:
            return document_text
        head = document_text[: int(limit * 0.65)]
        tail = document_text[-int(limit * 0.25) :]
        return f"{head}\n\n[中间内容因长度限制已折叠，系统仍保留原文用于条款切分]\n\n{tail}"

    def _heuristic_clause_map(self, document_text: str, max_clauses: int = 120) -> list[dict]:
        """Create a deterministic clause map so long documents still have anchors."""
        pattern = re.compile(
            r"(?m)^(第[一二三四五六七八九十百千万0-9]+[章节条款][^\n]{0,40}|[0-9]{1,2}[.、．][^\n]{0,60})"
        )
        matches = list(pattern.finditer(document_text))
        clauses: list[dict] = []

        if matches:
            for idx, match in enumerate(matches[:max_clauses]):
                start = match.start()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(document_text)
                text = document_text[start:end].strip()
                if not text:
                    continue
                page_number = self._guess_page_number(document_text, start)
                first_line = text.splitlines()[0][:80]
                clauses.append(
                    {
                        "clause_id": f"C-{idx + 1:03d}",
                        "clause_number": first_line,
                        "page_number": page_number,
                        "title": first_line,
                        "original_text": text[:2500],
                        "context_before": document_text[max(0, start - 300) : start],
                        "context_after": document_text[end : min(len(document_text), end + 300)],
                        "clause_type": "待识别",
                    }
                )

        if clauses:
            return clauses

        paragraphs = [p.strip() for p in re.split(r"\n{2,}", document_text) if p.strip()]
        for idx, paragraph in enumerate(paragraphs[:max_clauses]):
            clauses.append(
                {
                    "clause_id": f"C-{idx + 1:03d}",
                    "clause_number": f"段落{idx + 1}",
                    "page_number": self._guess_page_number(document_text, document_text.find(paragraph)),
                    "title": paragraph.splitlines()[0][:80],
                    "original_text": paragraph[:2500],
                    "context_before": "",
                    "context_after": "",
                    "clause_type": "段落",
                }
            )
        return clauses

    def _guess_page_number(self, document_text: str, offset: int) -> int:
        preceding = document_text[: max(offset, 0)]
        matches = re.findall(r"\[第\s*(\d+)\s*页\]", preceding)
        if matches:
            try:
                return int(matches[-1])
            except ValueError:
                return 0
        return 0

    def _clauses_for_model(self, clauses: list[dict], limit: int = 70) -> list[dict]:
        selected = clauses[:limit]
        return [
            {
                "clause_id": clause.get("clause_id"),
                "clause_number": clause.get("clause_number"),
                "page_number": clause.get("page_number"),
                "title": clause.get("title"),
                "original_text": (clause.get("original_text") or "")[:900],
                "clause_type": clause.get("clause_type"),
            }
            for clause in selected
        ]

    def _compact_clause(self, clause: dict, text_limit: int = 1100) -> dict:
        return {
            "clause_id": clause.get("clause_id"),
            "clause_number": clause.get("clause_number"),
            "page_number": clause.get("page_number"),
            "title": clause.get("title"),
            "original_text": (clause.get("original_text") or "")[:text_limit],
            "clause_type": clause.get("clause_type"),
        }

    def _select_clauses_for_issue_spotting(
        self,
        clauses: list[dict],
        rule_scan: dict,
        limit: int = 90,
    ) -> list[dict]:
        """Select clauses by coverage and risk signals instead of only taking the document head."""
        if len(clauses) <= limit:
            return [self._compact_clause(clause) for clause in clauses]

        selected: dict[str, dict] = {}

        def add(clause: dict) -> None:
            clause_id = str(clause.get("clause_id") or len(selected))
            if clause_id not in selected and len(selected) < limit:
                selected[clause_id] = clause

        for clause in clauses[:20]:
            add(clause)
        for candidate in self._ensure_list(rule_scan.get("risk_candidates")):
            original_clause = candidate.get("original_clause") if isinstance(candidate, dict) else {}
            clause_id = original_clause.get("clause_id") if isinstance(original_clause, dict) else None
            for clause in clauses:
                if clause.get("clause_id") == clause_id:
                    add(clause)
                    break
        high_signal_keywords = tuple({kw for rule in RISK_KEYWORD_RULES for kw in rule["keywords"]})
        scored: list[tuple[int, int, dict]] = []
        for idx, clause in enumerate(clauses):
            text = f"{clause.get('title', '')}\n{clause.get('original_text', '')}"
            score = sum(1 for kw in high_signal_keywords if kw in text)
            if score:
                scored.append((score, -idx, clause))
        for _, _, clause in sorted(scored, reverse=True):
            add(clause)
        for clause in clauses[-12:]:
            add(clause)

        if len(selected) < limit:
            stride = max(1, len(clauses) // max(1, limit - len(selected)))
            for clause in clauses[::stride]:
                add(clause)
                if len(selected) >= limit:
                    break

        return [self._compact_clause(clause) for clause in selected.values()]

    def _rule_based_issue_scan(
        self,
        clauses: list[dict],
        document_type: str,
        user_role: str,
        strategy: Any = None,
    ) -> dict:
        """Deterministic pre-scan that gives the model anchors and provides a fallback."""
        risk_candidates: list[dict] = []
        coverage: list[dict] = []
        full_text = "\n".join(str(clause.get("original_text") or "") for clause in clauses)
        generic_rule_ids = {rule["rule_id"] for rule in RISK_KEYWORD_RULES}
        risk_rules = [*RISK_KEYWORD_RULES]
        non_contract_strategy_ids = {"lawsuit_complaint", "defense_statement", "lawyer_letter", "arbitration_application"}
        missing_rules = [] if strategy and strategy.strategy_id in non_contract_strategy_ids else [*MISSING_CLAUSE_RULES]
        if strategy:
            risk_rules.extend(strategy.special_risk_rules)
            missing_rules.extend(strategy.missing_clause_rules)

        for rule in risk_rules:
            matched: list[tuple[int, dict, list[str]]] = []
            for clause in clauses:
                text = f"{clause.get('title', '')}\n{clause.get('original_text', '')}"
                hits = [kw for kw in rule["keywords"] if kw in text]
                if hits:
                    matched.append((len(hits), clause, hits))
            coverage.append(
                {
                    "rule_id": rule["rule_id"],
                    "title": rule["title"],
                    "matched_clause_count": len(matched),
                }
            )
            if not matched:
                continue
            matched.sort(key=lambda item: item[0], reverse=True)
            _, clause, hits = matched[0]
            is_strategy_rule = rule.get("rule_id") not in generic_rule_ids
            evidence_suggestion = self._ensure_list(rule.get("evidence_suggestion")) or [
                "保留签署版本、磋商记录、通知送达凭证、付款/交付/验收记录。"
            ]
            risk_candidates.append(
                {
                    "risk_id": f"RB-{len(risk_candidates) + 1:03d}",
                    "title": rule["title"],
                    "risk_level": rule["risk_level"],
                    "risk_type": rule["risk_type"],
                    "probability": "中",
                    "severity": "高" if rule["risk_level"] in {"高", "重大"} else "中",
                    "priority": len(risk_candidates) + 1,
                    "original_clause": {
                        "clause_id": clause.get("clause_id"),
                        "clause_number": clause.get("clause_number"),
                        "page_number": clause.get("page_number"),
                        "text": clause.get("original_text"),
                    },
                    "issue_location": f"规则预扫描命中关键词：{'、'.join(hits[:5])}。需结合全文判断是否构成实质风险。",
                    "legal_analysis": {
                        "legal_relationship": document_type or "合同/协议关系",
                        "applicable_rule": rule["applicable_rule"],
                        "application_to_clause": "该条款触发了规则预扫描，模型和人工复核应重点核验其权利义务配置、可执行性和证据要求。",
                        "user_impact": rule["user_impact"],
                        "counterparty_argument": "相对方可能主张该条款属于双方真实意思表示或商业安排，需结合磋商记录、提示说明和履行事实判断。",
                        "court_or_arbitration_focus": "通常会关注条款是否明确、是否公平、是否已提示说明、是否与交易目的和履行事实相匹配。",
                        "burden_of_proof": "主张条款效力、解除、违约或损失的一方通常需提交合同文本、履行记录、通知送达和损失计算依据。",
                        "evidence_suggestion": evidence_suggestion,
                    },
                    "status": "需律师复核",
                    "algorithm_rule_id": rule["rule_id"],
                    "strategy_id": strategy.strategy_id if is_strategy_rule and strategy else None,
                    "authority_queries": self._ensure_list(rule.get("authority_queries")),
                    "generated_by": "deterministic-rule-scan",
                }
            )

        missing_clause_candidates: list[dict] = []
        for rule in missing_rules:
            if not any(keyword in full_text for keyword in rule["keywords"]):
                missing_clause_candidates.append(
                    {
                        "name": rule["name"],
                        "risk": rule["risk"],
                        "recommended_clause": rule["recommended_clause"],
                        "citations": [],
                        "authority_queries": self._ensure_list(rule.get("authority_queries")),
                        "strategy_id": strategy.strategy_id if strategy and rule not in MISSING_CLAUSE_RULES else None,
                        "generated_by": "deterministic-rule-scan",
                    }
                )

        if ("租赁" in document_type or "租赁" in full_text) and not any(kw in full_text for kw in ("维修", "修缮", "押金返还")):
            missing_clause_candidates.append(
                {
                    "name": "租赁物维修/押金返还",
                    "risk": "租赁合同缺少维修责任或押金返还机制，容易引发使用障碍和结算争议。",
                    "recommended_clause": "建议明确维修责任、报修流程、紧急维修处理、押金扣除范围、返还期限和扣款证明。",
                    "citations": [],
                    "generated_by": "deterministic-rule-scan",
                }
            )
        if ("劳动" in document_type or "劳动合同" in full_text) and not any(kw in full_text for kw in ("社会保险", "劳动报酬", "工作时间")):
            missing_clause_candidates.append(
                {
                    "name": "劳动合同必备条款",
                    "risk": "劳动合同缺少劳动报酬、社保或工作时间等必备条款，存在劳动争议和行政合规风险。",
                    "recommended_clause": "建议补充工作内容和地点、工作时间和休息休假、劳动报酬、社会保险、劳动保护等必备条款。",
                    "citations": [],
                    "generated_by": "deterministic-rule-scan",
                }
            )

        return {
            "risk_candidates": risk_candidates[:18],
            "missing_clause_candidates": missing_clause_candidates[:12],
            "coverage": coverage,
            "document_type": document_type,
            "user_role": user_role,
            "review_strategy": strategy.to_report_dict() if strategy else {},
        }

    def _merge_rule_based_issue_result(self, issue_result: dict, rule_scan: dict) -> dict:
        if not isinstance(issue_result, dict):
            issue_result = {}

        risk_items = [item for item in self._ensure_list(issue_result.get("risk_items")) if isinstance(item, dict)]
        existing_titles = {self._normalize_text_key(item.get("title", "")) for item in risk_items}
        rule_candidates = [item for item in self._ensure_list(rule_scan.get("risk_candidates")) if isinstance(item, dict)]

        has_strategy_candidates = any(candidate.get("strategy_id") for candidate in rule_candidates)
        if has_strategy_candidates and len(risk_items) < 5:
            max_rule_additions = 8
        else:
            max_rule_additions = 6 if len(risk_items) < 3 else 2
        for candidate in rule_candidates:
            key = self._normalize_text_key(candidate.get("title", ""))
            if key in existing_titles:
                continue
            if len([item for item in risk_items if item.get("generated_by") == "deterministic-rule-scan"]) >= max_rule_additions:
                break
            risk_items.append(candidate)
            existing_titles.add(key)

        missing_clauses = [
            item for item in self._ensure_list(issue_result.get("missing_clauses")) if isinstance(item, dict)
        ]
        existing_missing = {self._normalize_text_key(item.get("name", "")) for item in missing_clauses}
        for candidate in self._ensure_list(rule_scan.get("missing_clause_candidates")):
            if not isinstance(candidate, dict):
                continue
            key = self._normalize_text_key(candidate.get("name", ""))
            if key and key not in existing_missing:
                missing_clauses.append(candidate)
                existing_missing.add(key)

        issue_result["risk_items"] = risk_items
        issue_result["missing_clauses"] = missing_clauses
        return issue_result

    def _merge_pending_facts(self, *fact_lists: Any) -> list[dict]:
        merged: list[dict] = []
        seen: set[str] = set()
        for facts in fact_lists:
            for fact in self._ensure_list(facts):
                if isinstance(fact, dict):
                    item = dict(fact)
                else:
                    item = {"field": str(fact), "reason": "模型识别的待补事实", "impact": "需补充后再形成稳定判断。"}
                item.setdefault("field", "待补事实")
                item.setdefault("reason", "需补充该事实后再形成稳定判断。")
                item.setdefault("impact", "可能影响风险等级、修改建议或证据策略。")
                key = self._normalize_text_key(f"{item.get('field')}|{item.get('reason')}")
                if key and key not in seen:
                    merged.append(item)
                    seen.add(key)
        return merged

    def _build_strategy_framework(self, strategy: Any) -> dict:
        payload = strategy.to_report_dict()
        return {
            "strategy_id": payload.get("strategy_id"),
            "document_type": payload.get("display_name"),
            "matter_type": payload.get("matter_type"),
            "must_review_dimensions": payload.get("review_dimensions", []),
            "required_fields": payload.get("required_fields", []),
            "evidence_checklist": payload.get("evidence_checklist", []),
            "authority_queries": payload.get("authority_queries", []),
            "lawyer_review_triggers": payload.get("lawyer_review_triggers", []),
            "report_focus": payload.get("report_focus", []),
        }

    def _build_coverage_audit(
        self,
        *,
        clauses: list[dict],
        selected_clauses: list[dict],
        rule_scan: dict,
        strategy: Any,
        strategy_pending_facts: list[dict],
    ) -> dict:
        return {
            "total_extracted_clauses": len(clauses),
            "clauses_selected_for_issue_model": len(selected_clauses),
            "rule_candidate_count": len(self._ensure_list(rule_scan.get("risk_candidates"))),
            "missing_clause_candidate_count": len(self._ensure_list(rule_scan.get("missing_clause_candidates"))),
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.display_name,
            "strategy_required_field_count": len(strategy.required_fields),
            "strategy_pending_fact_count": len(strategy_pending_facts),
            "coverage_note": "长文档先做确定性条款切分和规则预扫描，再把高风险条款、首尾条款和抽样条款交给模型复核。",
        }

    def _attach_missing_clause_citations(self, missing_clauses: Any, *, strategy_id: str | None = None) -> list[dict]:
        enriched: list[dict] = []
        for clause in self._ensure_list(missing_clauses):
            if not isinstance(clause, dict):
                continue
            item = dict(clause)
            clause_strategy_id = item.get("strategy_id") or strategy_id
            queries = self._ensure_list(item.get("authority_queries"))
            if not queries:
                queries = [f"{item.get('name', '')} {item.get('risk', '')} {item.get('recommended_clause', '')}"]
            citations: list[dict] = []
            for query in queries[:3]:
                citations.extend(self.legal_research.search(str(query), limit=2, strategy_id=clause_strategy_id))
            validated = self.legal_research.validate_citations(citations)
            item["citation_details"] = validated
            item["citations"] = [
                citation.get("source_id")
                for citation in validated
                if isinstance(citation, dict) and citation.get("source_id")
            ][:4]
            enriched.append(item)
        return enriched

    def _normalize_text_key(self, value: Any) -> str:
        return re.sub(r"[\s，。；：:;,.、（）()《》\"'“”]+", "", str(value or "")).lower()

    def _ground_and_normalize_risk_items(self, risk_items: list, clauses: list[dict]) -> list[dict]:
        grounded: list[dict] = []
        for idx, risk in enumerate(risk_items):
            if not isinstance(risk, dict):
                continue
            risk.setdefault("risk_id", f"R-{idx + 1:03d}")
            if str(risk["risk_id"]).startswith("RB-"):
                risk["risk_id"] = f"R-{idx + 1:03d}"
            risk["risk_level"] = self._normalize_risk_level(risk.get("risk_level"))
            risk.setdefault("risk_type", "法律风险")
            risk.setdefault("probability", "中")
            risk.setdefault("severity", "中")
            risk["priority"] = self._safe_int(risk.get("priority"), idx + 1)
            risk.setdefault("status", "未处理")

            legal_analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
            legal_analysis.setdefault("legal_relationship", "待结合合同类型确认")
            legal_analysis.setdefault("applicable_rule", "当前材料不足，需结合已校验法律依据进一步核验。")
            legal_analysis.setdefault("application_to_clause", "需结合原文条款、履行事实和证据材料判断。")
            legal_analysis.setdefault("user_impact", "可能影响权利主张、履约成本或争议处理。")
            legal_analysis.setdefault("counterparty_argument", "相对方可能基于合同自由、交易习惯或履行事实提出抗辩。")
            legal_analysis.setdefault("court_or_arbitration_focus", "通常会关注条款文本、签署过程、履行记录、通知和损失证明。")
            legal_analysis.setdefault("burden_of_proof", "主张权利或抗辩的一方需提交合同、沟通记录、履行凭证和损失依据。")
            legal_analysis["evidence_suggestion"] = self._ensure_list(legal_analysis.get("evidence_suggestion")) or [
                "保留合同签署版本、沟通记录、付款/交付/验收凭证和通知送达记录。"
            ]
            risk["legal_analysis"] = legal_analysis

            original_clause = risk.get("original_clause") if isinstance(risk.get("original_clause"), dict) else {}
            match = self._best_clause_for_risk(risk, original_clause, clauses)
            if match:
                original_clause = {
                    "clause_id": match.get("clause_id"),
                    "clause_number": match.get("clause_number"),
                    "page_number": match.get("page_number"),
                    "text": match.get("original_text"),
                    "grounding_status": "matched_to_extracted_clause",
                }
            else:
                original_clause = {
                    "clause_number": original_clause.get("clause_number") or "未稳定定位",
                    "page_number": original_clause.get("page_number") or 0,
                    "text": original_clause.get("text") or "未在原文中稳定定位；请结合原文复核。",
                    "grounding_status": "unmatched",
                }
                risk["status"] = "需律师复核"
            risk["original_clause"] = original_clause
            risk.setdefault("issue_location", "需结合原文具体语句复核。")
            grounded.append(risk)
        return grounded

    def _best_clause_for_risk(self, risk: dict, original_clause: dict, clauses: list[dict]) -> dict | None:
        clause_id = original_clause.get("clause_id")
        if clause_id:
            for clause in clauses:
                if clause.get("clause_id") == clause_id:
                    return clause

        original_text_key = self._normalize_text_key(original_clause.get("text", ""))
        clause_number_key = self._normalize_text_key(original_clause.get("clause_number", ""))
        best_score = 0
        best_clause: dict | None = None
        risk_terms = [
            term
            for term in re.findall(
                r"[\u4e00-\u9fff]{2,}",
                f"{risk.get('title', '')}{risk.get('issue_location', '')}"
                f"{risk.get('legal_analysis', {}).get('applicable_rule', '') if isinstance(risk.get('legal_analysis'), dict) else ''}",
            )
            if term not in {"风险", "条款", "需要", "合同", "当前", "材料", "核验", "明确"}
        ][:20]

        for clause in clauses:
            clause_text = str(clause.get("original_text") or "")
            clause_key = self._normalize_text_key(clause_text)
            number_key = self._normalize_text_key(clause.get("clause_number", ""))
            score = 0
            if clause_number_key and (clause_number_key in number_key or number_key in clause_number_key):
                score += 30
            if original_text_key and len(original_text_key) >= 12 and original_text_key[:80] in clause_key:
                score += 45
            for term in risk_terms:
                if term in clause_text:
                    score += 3
            if score > best_score:
                best_score = score
                best_clause = clause
        return best_clause if best_score >= 8 else None

    def _ensure_list(self, value: Any) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, set):
            return list(value)
        if value is None:
            return []
        return [value]

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _clean_missing_clauses(self, missing_clauses: Any) -> list[dict]:
        cleaned: list[dict] = []
        seen: set[str] = set()
        for clause in self._ensure_list(missing_clauses):
            if not isinstance(clause, dict):
                continue
            name = self._first_text(
                clause.get("name"),
                clause.get("title"),
                clause.get("clause_name"),
                clause.get("missing_clause_name"),
            )
            risk = self._first_text(
                clause.get("risk"),
                clause.get("risk_description"),
                clause.get("risk_if_missing"),
                clause.get("reason"),
            )
            recommended = self._first_text(
                clause.get("recommended_clause"),
                clause.get("recommended_clause_text"),
                clause.get("suggested_clause"),
                clause.get("recommendation"),
            )
            if not (name or risk or recommended):
                continue
            if not name:
                name = "建议补充条款"
            if not risk:
                risk = "缺少该条款可能导致权利义务、履行边界或争议处理不明确。"
            if not recommended:
                recommended = "建议结合交易背景补充具体、可执行的条款文本，并由执业律师复核。"

            item = dict(clause)
            item["name"] = name
            item["risk"] = risk
            item["recommended_clause"] = recommended
            if not self._ensure_list(item.get("citations")) and self._ensure_list(item.get("citation_details")):
                item["citations"] = [
                    citation.get("source_id")
                    for citation in self._ensure_list(item.get("citation_details"))
                    if isinstance(citation, dict) and citation.get("source_id")
                ][:4]
            else:
                item["citations"] = [
                    str(citation)
                    for citation in self._ensure_list(item.get("citations"))
                    if str(citation or "").strip()
                ][:4]

            key = self._normalize_text_key(f"{name}|{risk}|{recommended}")
            if key and key not in seen:
                cleaned.append(item)
                seen.add(key)
        return cleaned

    def _clean_favorable_clauses(self, favorable_clauses: Any) -> list[dict]:
        generic_reason = "该条款对当前审查立场相对有利，但仍需结合全文和履行事实复核。"
        generic_recommendation = "保留；如与其他条款冲突，应同步微调。"

        def is_generic(value: str, generic: str) -> bool:
            return self._normalize_text_key(value) == self._normalize_text_key(generic)

        def recommendation_for(reference: str, original_text: str, reason: str) -> str:
            text_blob = f"{reference}\n{original_text}\n{reason}".lower()
            if "insurance" in text_blob or "保险" in text_blob:
                return "建议保留完整保险安排，并进一步核对投保责任主体、保险金额、承保险别和索赔文件，避免 CIF/FOB 选择后责任主体不清。"
            if "arbitration" in text_blob or "仲裁" in text_blob or "gafta" in text_blob:
                return "建议保留专业仲裁机制，同时补充仲裁语言、仲裁员人数、送达方式和紧急救济安排，确保争议解决条款可执行。"
            if "governing law" in text_blob or "english law" in text_blob or "适用法律" in text_blob:
                return "建议保留适用法条款，但需与仲裁地、合同履行地和强制性法律规定一并复核，避免法律适用与争议解决安排冲突。"
            if "quality" in text_blob or "surveyor" in text_blob or "inspection" in text_blob or "质量" in text_blob or "检验" in text_blob:
                return "建议保留独立第三方检验安排，并补充检验机构资质、检验地点、异议复检程序和费用承担，降低质量争议。"
            return "建议保留该条款的核心安排，并结合全文校验其与风险转移、付款、验收、违约责任和争议解决条款是否一致。"

        cleaned: list[dict] = []
        seen: set[str] = set()
        for clause in self._ensure_list(favorable_clauses):
            if not isinstance(clause, dict):
                continue
            reference = self._first_text(
                clause.get("clause_reference"),
                clause.get("title"),
                clause.get("clause_number"),
                clause.get("name"),
            )
            original_text = self._first_text(clause.get("original_text"), clause.get("text"))
            analysis = self._first_text(
                clause.get("analysis"),
                clause.get("favorable_reason"),
                clause.get("advantage"),
                clause.get("benefit"),
            )
            reason = self._first_text(clause.get("reason"), analysis)
            if is_generic(reason, generic_reason) and analysis:
                reason = analysis
            recommendation = self._first_text(clause.get("keep_or_modify"), clause.get("recommendation"))
            if (not recommendation) or is_generic(recommendation, generic_recommendation):
                recommendation = recommendation_for(reference, original_text, reason)
            if not (reference or reason or recommendation or original_text):
                continue
            if not reference:
                reference = "有利条款"
            if not reason:
                reason = generic_reason
            if not recommendation:
                recommendation = recommendation_for(reference, original_text, reason)
            item = dict(clause)
            item["clause_reference"] = reference
            item["reason"] = reason
            item["keep_or_modify"] = recommendation
            if original_text:
                item["original_text"] = original_text
            key = self._normalize_text_key(f"{reference}|{reason}|{recommendation}")
            if key and key not in seen:
                cleaned.append(item)
                seen.add(key)
        return cleaned

    def _appendix_entry_from_citation(self, citation: dict, risk_id: str | None = None) -> dict:
        source_id = citation.get("source_id") or "待核验来源"
        entry = {
            "source_id": source_id,
            "source_name": citation.get("source_name") or "待核验来源",
            "article_or_case_number": citation.get("article_or_case_number") or "",
            "source_type": citation.get("source_type") or "实务清单",
            "authority_level": citation.get("authority_level") or "需核验",
            "legal_effect_note": citation.get("legal_effect_note") or "需进一步核验效力和适用性。",
            "text_excerpt_or_holding": citation.get("text_excerpt_or_holding") or "",
            "relevance_reason": citation.get("relevance_reason") or "",
            "verification_status": citation.get("verification_status") or "待核验",
            "confidence": self._safe_int(citation.get("confidence"), 0),
            "cited_by_risks": [],
        }
        if risk_id:
            entry["cited_by_risks"].append(risk_id)
        return entry

    def _merge_appendix_entry(self, target: dict, incoming: dict) -> None:
        for key, value in incoming.items():
            if key in {"cited_by_risks", "cited_by_missing_clauses"}:
                existing = self._ensure_list(target.get(key))
                for item in self._ensure_list(value):
                    if item and item not in existing:
                        existing.append(item)
                target[key] = existing
                continue
            if (not target.get(key)) and value:
                target[key] = value
            elif key == "confidence" and self._safe_int(value, 0) > self._safe_int(target.get(key), 0):
                target[key] = self._safe_int(value, 0)

    def _hydrate_legal_authority_appendix(self, report: dict) -> list[dict]:
        appendix_by_id: dict[str, dict] = {}
        for source in self._ensure_list(report.get("legal_authority_appendix")):
            if not isinstance(source, dict):
                continue
            source_id = source.get("source_id") or f"SRC-{len(appendix_by_id) + 1:03d}"
            entry = {
                "source_id": source_id,
                "source_name": source.get("source_name") or "待核验来源",
                "article_or_case_number": source.get("article_or_case_number") or "",
                "source_type": source.get("source_type") or "实务清单",
                "authority_level": source.get("authority_level") or "需核验",
                "legal_effect_note": source.get("legal_effect_note") or "需进一步核验效力和适用性。",
                "text_excerpt_or_holding": source.get("text_excerpt_or_holding") or "",
                "relevance_reason": source.get("relevance_reason") or "",
                "verification_status": source.get("verification_status") or "待核验",
                "confidence": self._safe_int(source.get("confidence"), 0),
                "cited_by_risks": self._ensure_list(source.get("cited_by_risks")),
                "cited_by_missing_clauses": self._ensure_list(source.get("cited_by_missing_clauses")),
            }
            appendix_by_id[source_id] = entry

        for risk in self._ensure_list(report.get("risk_items")):
            if not isinstance(risk, dict):
                continue
            risk_id = risk.get("risk_id")
            for citation in self._ensure_list(risk.get("citations")):
                if not isinstance(citation, dict):
                    continue
                entry = self._appendix_entry_from_citation(citation, risk_id=risk_id)
                source_id = entry["source_id"]
                if source_id not in appendix_by_id:
                    appendix_by_id[source_id] = entry
                else:
                    self._merge_appendix_entry(appendix_by_id[source_id], entry)

        for missing in self._ensure_list(report.get("missing_clauses")):
            if not isinstance(missing, dict):
                continue
            missing_name = missing.get("name") or "缺失条款"
            for citation in self._ensure_list(missing.get("citation_details")):
                if not isinstance(citation, dict):
                    continue
                entry = self._appendix_entry_from_citation(citation)
                entry["cited_by_missing_clauses"] = [missing_name]
                source_id = entry["source_id"]
                if source_id not in appendix_by_id:
                    appendix_by_id[source_id] = entry
                else:
                    self._merge_appendix_entry(appendix_by_id[source_id], entry)

        return [
            item
            for item in appendix_by_id.values()
            if item.get("source_id") and item.get("source_name")
        ]

    def repair_report_for_display(self, report: dict) -> dict:
        """Clean model artifacts and hydrate fields needed by report UI/export."""
        if not isinstance(report, dict):
            return {}
        report["missing_clauses"] = self._clean_missing_clauses(report.get("missing_clauses"))
        report["favorable_clauses"] = self._clean_favorable_clauses(report.get("favorable_clauses"))
        report["legal_authority_appendix"] = self._hydrate_legal_authority_appendix(report)
        return report

    def prepare_report_for_display(self, report: dict) -> dict:
        """Repair stored reports and attach delivery metadata for UI/export."""
        report = self.repair_report_for_display(report)
        report.setdefault("report_meta", {})
        report.setdefault("review_strategy", {})
        report.setdefault("professional_review_framework", {})
        report.setdefault("coverage_audit", {})
        report["report_meta"].pop("risk_score", None)
        quality_audit = self._build_quality_audit(report)
        report["quality_audit"] = quality_audit
        report["quality_gate"] = self.quality_gate.evaluate(report)
        report["citation_audit"] = self.citation_audit.evaluate(report)
        report["evidence_audit"] = self.evidence_audit.evaluate(report)
        report["risk_scoring"] = self.risk_scoring.score_report(report)
        self.risk_scoring.apply_to_report(report, report["risk_scoring"])
        report["report_meta"]["risk_score"] = report["risk_scoring"]["overall_score"]
        report["delivery_audit"] = self._build_delivery_audit(report, quality_audit)
        report["human_review_workflow"] = self._build_human_review_workflow(report, quality_audit)
        if quality_audit.get("lawyer_review_required"):
            report["report_meta"]["lawyer_review_required"] = True
        return report

    def _normalize_risk_level(self, value: Any) -> str:
        raw = str(value or "中")
        if raw in {"重大", "critical", "严重"}:
            return "重大"
        if raw in {"高", "high"}:
            return "高"
        if raw in {"低", "low"}:
            return "低"
        return "中"

    def _safe_int(self, value: Any, default: int = 50) -> int:
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return max(0, min(100, value))
        if isinstance(value, float):
            return max(0, min(100, int(value)))
        match = re.search(r"\d+", str(value or ""))
        return max(0, min(100, int(match.group(0)))) if match else default

    def _normalize_assembled_report(
        self,
        *,
        report: dict,
        document_type: str,
        jurisdiction: str,
        user_role: str,
    ) -> dict:
        report.setdefault("report_meta", {})
        meta = report["report_meta"]
        meta.setdefault("document_type", document_type)
        meta.setdefault("jurisdiction", jurisdiction)
        meta.setdefault("user_role", user_role)
        meta["overall_risk_level"] = self._normalize_risk_level(meta.get("overall_risk_level"))
        meta.pop("risk_score", None)
        meta.setdefault("recommendation", "修改后签署")
        meta.setdefault("lawyer_review_required", meta["overall_risk_level"] in {"高", "重大"})

        report.setdefault("executive_summary", {})
        report["executive_summary"].setdefault("top_risks", [])
        report["executive_summary"].setdefault("priority_actions", [])
        report["executive_summary"].setdefault("missing_facts", [])

        report.setdefault("contract_summary", {})
        report["contract_summary"].setdefault("purpose", "当前材料未能稳定识别合同目的")
        report["contract_summary"].setdefault("main_obligations", [])
        report["contract_summary"].setdefault("payment_terms", "当前材料未能稳定识别")
        report["contract_summary"].setdefault("term", "当前材料未能稳定识别")
        report["contract_summary"].setdefault("dispute_resolution", "当前材料未能稳定识别")

        report["risk_matrix"] = self._ensure_list(report.get("risk_matrix"))
        report["risk_items"] = self._ensure_list(report.get("risk_items"))
        report["missing_clauses"] = self._ensure_list(report.get("missing_clauses"))
        report["favorable_clauses"] = self._ensure_list(report.get("favorable_clauses"))
        report["pending_facts"] = self._ensure_list(report.get("pending_facts"))
        report["legal_authority_appendix"] = self._ensure_list(report.get("legal_authority_appendix"))
        report = self.repair_report_for_display(report)
        report.setdefault("review_strategy", {})
        report.setdefault("professional_review_framework", {})
        report.setdefault("coverage_audit", {})
        report.setdefault(
            "disclaimer",
            "本报告为 AI 辅助生成的风险提示和文书草稿，不构成正式法律意见；复杂事项请咨询执业律师。",
        )
        report["quality_audit"] = self._build_quality_audit(report)
        report["quality_gate"] = self.quality_gate.evaluate(report)
        report["citation_audit"] = self.citation_audit.evaluate(report)
        report["evidence_audit"] = self.evidence_audit.evaluate(report)
        report["risk_scoring"] = self.risk_scoring.score_report(report)
        self.risk_scoring.apply_to_report(report, report["risk_scoring"])
        report["report_meta"]["risk_score"] = report["risk_scoring"]["overall_score"]
        report["delivery_audit"] = self._build_delivery_audit(report, report["quality_audit"])
        report["human_review_workflow"] = self._build_human_review_workflow(report, report["quality_audit"])
        if report["quality_audit"].get("lawyer_review_required"):
            meta["lawyer_review_required"] = True
        return report

    def _is_generic_favorable_reason(self, value: Any) -> bool:
        generic = "该条款对当前审查立场相对有利，但仍需结合全文和履行事实复核。"
        return self._normalize_text_key(value) == self._normalize_text_key(generic)

    def _is_generic_favorable_recommendation(self, value: Any) -> bool:
        generic = "保留；如与其他条款冲突，应同步微调。"
        return self._normalize_text_key(value) == self._normalize_text_key(generic)

    def _build_delivery_audit(self, report: dict, quality_audit: dict) -> dict:
        risk_items = [item for item in self._ensure_list(report.get("risk_items")) if isinstance(item, dict)]
        legal_sources = [item for item in self._ensure_list(report.get("legal_authority_appendix")) if isinstance(item, dict)]
        verified_sources = [item for item in legal_sources if item.get("verification_status") == "已校验"]
        citation_audit = report.get("citation_audit") if isinstance(report.get("citation_audit"), dict) else {}
        evidence_audit = report.get("evidence_audit") if isinstance(report.get("evidence_audit"), dict) else {}
        quality_score = self._safe_int(quality_audit.get("quality_score"), 0)
        blocking_issues = self._ensure_list(quality_audit.get("warnings"))
        verified_source_ratio = (
            citation_audit.get("verified_ratio")
            if isinstance(citation_audit.get("verified_ratio"), (int, float))
            else round(len(verified_sources) / len(legal_sources), 2) if legal_sources else 0
        )
        if quality_score >= 85 and not blocking_issues:
            readiness_level = "可进入客户交付前律师抽检"
        elif quality_score >= 70:
            readiness_level = "可进入律师复核"
        else:
            readiness_level = "仅可作为内部初稿"

        return {
            "positioning": "不是替代 LLM chat，而是把 LLM 组织成可审计、可复核、可下载的法律审查 SaaS 交付系统。",
            "readiness_level": readiness_level,
            "readiness_score": quality_score,
            "blocking_issues": blocking_issues,
            "verified_source_ratio": verified_source_ratio,
            "reviewable_source_ratio": citation_audit.get("reviewable_ratio", 0),
            "risk_evidence_coverage": evidence_audit.get("risk_evidence_coverage", 0),
            "blocking_pending_fact_count": evidence_audit.get("blocking_pending_fact_count", 0),
            "reviewable_artifacts": [
                "原文条款定位",
                "风险矩阵",
                "逐条律师式分析",
                "法律依据附录",
                "引用审计",
                "缺失条款清单",
                "有利条款保留建议",
                "替代条款三版本",
                "证据清单",
                "质量审计",
                "人工复核任务包",
            ],
            "export_formats": ["pdf", "doc", "md", "json"],
            "risk_count": len(risk_items),
            "legal_source_count": len(legal_sources),
        }

    def _build_human_review_workflow(self, report: dict, quality_audit: dict) -> dict:
        risk_items = [item for item in self._ensure_list(report.get("risk_items")) if isinstance(item, dict)]
        high_risks = [
            item.get("risk_id", "未知风险")
            for item in risk_items
            if self._normalize_risk_level(item.get("risk_level")) in {"高", "重大"}
        ]
        warnings = [str(item) for item in self._ensure_list(quality_audit.get("warnings")) if str(item).strip()]
        citation_audit = report.get("citation_audit") if isinstance(report.get("citation_audit"), dict) else {}
        evidence_audit = report.get("evidence_audit") if isinstance(report.get("evidence_audit"), dict) else {}
        tasks: list[dict] = []
        if high_risks:
            tasks.append(
                {
                    "task_id": "HR-001",
                    "title": "复核高/重大风险等级、事实基础和谈判底线",
                    "target": high_risks[:8],
                    "owner_role": "执业律师",
                    "status": "pending",
                }
            )
        if any("法律依据" in warning or "引用" in warning for warning in warnings):
            tasks.append(
                {
                    "task_id": "HR-002",
                    "title": "核验法律依据、法域和引用适用性",
                    "target": "legal_authority_appendix",
                    "owner_role": "执业律师/法务",
                    "status": "pending",
                }
            )
        if citation_audit.get("status") in {"fail", "warn"}:
            targets = (
                citation_audit.get("high_risk_without_reviewable_citation")
                or citation_audit.get("weak_source_ids")
                or "citation_audit"
            )
            tasks.append(
                {
                    "task_id": "HR-004",
                    "title": "按引用审计结果补齐或核验法律依据",
                    "target": targets,
                    "owner_role": "执业律师/法务",
                    "status": "pending",
                }
            )
        if self._ensure_list(report.get("pending_facts")):
            tasks.append(
                {
                    "task_id": "HR-003",
                    "title": "向用户补齐待补事实和关键证据",
                    "target": "pending_facts",
                    "owner_role": "客户经理/法务助理",
                    "status": "pending",
                }
            )
        if evidence_audit.get("status") in {"fail", "warn"}:
            targets = (
                evidence_audit.get("high_risk_without_evidence_plan")
                or evidence_audit.get("blocking_pending_fact_ids")
                or "evidence_audit"
            )
            tasks.append(
                {
                    "task_id": "HR-005",
                    "title": "按证据审计结果补齐举证计划和待补事实",
                    "target": targets,
                    "owner_role": "法务/律师助理",
                    "status": "pending",
                }
            )
        if not tasks:
            tasks.append(
                {
                    "task_id": "HR-001",
                    "title": "交付前抽样复核报告结论和下载文件",
                    "target": "full_report",
                    "owner_role": "法务/律师",
                    "status": "pending",
                }
            )

        required = bool(quality_audit.get("lawyer_review_required")) or bool(high_risks)
        return {
            "status": "required" if required else "recommended",
            "triage_level": "urgent" if any(self._normalize_risk_level(item.get("risk_level")) == "重大" for item in risk_items) else "normal",
            "reasons": warnings[:8] or ["交付前建议进行人工抽样复核。"],
            "review_tasks": tasks,
            "handoff_note": "该任务包用于把 AI 初稿流转给律师/法务复核，不应作为正式法律意见直接发送。",
        }

    def _build_quality_audit(self, report: dict) -> dict:
        risk_items = [item for item in self._ensure_list(report.get("risk_items")) if isinstance(item, dict)]
        warnings: list[str] = []
        checks: list[dict] = []

        risk_count = len(risk_items)
        grounded_count = 0
        verified_citation_count = 0
        pending_citation_count = 0
        high_without_verified: list[str] = []
        risks_without_revision: list[str] = []
        unmatched_risks: list[str] = []
        generic_favorable_count = 0
        incomplete_appendix_count = 0
        placeholder_revision_count = 0
        review_strategy = report.get("review_strategy") if isinstance(report.get("review_strategy"), dict) else {}
        professional_framework = (
            report.get("professional_review_framework")
            if isinstance(report.get("professional_review_framework"), dict)
            else {}
        )
        coverage_audit = report.get("coverage_audit") if isinstance(report.get("coverage_audit"), dict) else {}
        strategy_pending_count = self._safe_int(coverage_audit.get("strategy_pending_fact_count"), 0)
        required_fields = self._ensure_list(professional_framework.get("required_fields"))
        evidence_checklist = self._ensure_list(professional_framework.get("evidence_checklist"))

        for risk in risk_items:
            risk_id = risk.get("risk_id", "未知风险")
            original_clause = risk.get("original_clause") if isinstance(risk.get("original_clause"), dict) else {}
            if original_clause.get("grounding_status") == "matched_to_extracted_clause":
                grounded_count += 1
            else:
                unmatched_risks.append(risk_id)

            citations = [c for c in self._ensure_list(risk.get("citations")) if isinstance(c, dict)]
            has_verified = any(c.get("verification_status") == "已校验" for c in citations)
            verified_citation_count += sum(1 for c in citations if c.get("verification_status") == "已校验")
            pending_citation_count += sum(1 for c in citations if c.get("verification_status") != "已校验")
            if self._normalize_risk_level(risk.get("risk_level")) in {"高", "重大"} and not has_verified:
                high_without_verified.append(risk_id)

            revision = risk.get("revision_plan") if isinstance(risk.get("revision_plan"), dict) else {}
            if not any(revision.get(key) for key in ("conservative_clause", "balanced_clause", "bottom_line_clause")):
                risks_without_revision.append(risk_id)
            revision_text = "\n".join(
                str(revision.get(key) or "")
                for key in ("conservative_clause", "balanced_clause", "bottom_line_clause")
            )
            if "当前材料不足" in revision_text:
                placeholder_revision_count += 1

        for clause in self._ensure_list(report.get("favorable_clauses")):
            if not isinstance(clause, dict):
                continue
            if self._is_generic_favorable_reason(clause.get("reason")) or self._is_generic_favorable_recommendation(
                clause.get("keep_or_modify")
            ):
                generic_favorable_count += 1

        for source in self._ensure_list(report.get("legal_authority_appendix")):
            if not isinstance(source, dict):
                continue
            if not source.get("article_or_case_number") or not source.get("text_excerpt_or_holding"):
                incomplete_appendix_count += 1

        score = 100
        if risk_count == 0:
            warnings.append("未识别到风险项，报告不可直接使用。")
            score -= 45
        if risk_count and grounded_count < risk_count:
            warnings.append(f"{risk_count - grounded_count} 个风险项未能稳定定位到原文条款。")
            score -= min(25, (risk_count - grounded_count) * 5)
        if high_without_verified:
            warnings.append(f"高/重大风险 {', '.join(high_without_verified[:5])} 缺少已校验法律依据。")
            score -= min(25, len(high_without_verified) * 8)
        if risks_without_revision:
            warnings.append(f"{len(risks_without_revision)} 个风险项缺少可复制替代条款。")
            score -= min(20, len(risks_without_revision) * 5)
        if pending_citation_count and verified_citation_count == 0:
            warnings.append("法律依据均为待核验来源，必须接入权威法库或人工复核后使用。")
            score -= 18
        if len(self._ensure_list(report.get("pending_facts"))) == 0:
            warnings.append("报告未列出待补事实，复杂文书可能存在过度确定风险。")
            score -= 5
        if not review_strategy.get("strategy_id"):
            warnings.append("报告未记录文书类型审查策略，难以证明不是通用模板审查。")
            score -= 12
        if not required_fields:
            warnings.append("报告未列出该类文书必备字段清单。")
            score -= 8
        if not evidence_checklist:
            warnings.append("报告未列出该类文书证据清单。")
            score -= 8
        if strategy_pending_count:
            warnings.append(f"文书类型必备字段仍有 {strategy_pending_count} 项待补。")
            score -= min(18, strategy_pending_count * 4)
        if generic_favorable_count:
            warnings.append(f"{generic_favorable_count} 个有利条款仍使用模板化原因或建议。")
            score -= min(12, generic_favorable_count * 4)
        if incomplete_appendix_count:
            warnings.append(f"{incomplete_appendix_count} 条法律依据附录缺少条号或正文摘录。")
            score -= min(18, incomplete_appendix_count * 3)
        if placeholder_revision_count:
            warnings.append(f"{placeholder_revision_count} 个风险项仍使用材料不足类占位替代条款。")
            score -= min(15, placeholder_revision_count * 4)

        checks.extend(
            [
                {"name": "risk_count", "value": risk_count},
                {"name": "grounded_risk_count", "value": grounded_count},
                {"name": "verified_citation_count", "value": verified_citation_count},
                {"name": "pending_citation_count", "value": pending_citation_count},
                {"name": "high_risks_without_verified_citation", "value": high_without_verified},
                {"name": "risks_without_revision_plan", "value": risks_without_revision},
                {"name": "unmatched_risks", "value": unmatched_risks},
                {"name": "review_strategy_id", "value": review_strategy.get("strategy_id")},
                {"name": "strategy_required_fields", "value": required_fields},
                {"name": "strategy_pending_fact_count", "value": strategy_pending_count},
                {"name": "evidence_checklist", "value": evidence_checklist},
                {"name": "generic_favorable_clause_count", "value": generic_favorable_count},
                {"name": "incomplete_legal_appendix_count", "value": incomplete_appendix_count},
                {"name": "placeholder_revision_plan_count", "value": placeholder_revision_count},
            ]
        )

        normalized_score = max(0, min(100, score))
        return {
            "quality_score": normalized_score,
            "quality_level": "高" if normalized_score >= 85 else "中" if normalized_score >= 70 else "低",
            "warnings": warnings,
            "checks": checks,
            "lawyer_review_required": normalized_score < 85
            or bool(high_without_verified)
            or bool(generic_favorable_count)
            or bool(incomplete_appendix_count)
            or bool(placeholder_revision_count)
            or any(self._normalize_risk_level(r.get("risk_level")) in {"高", "重大"} for r in risk_items),
            "source_policy": "只有命中本地来源库的法条标记为已校验；其他模型来源一律待核验。",
        }

    async def _run_deep_review_pipeline(
        self,
        *,
        document_text: str,
        document_type: str,
        user_role: str,
        review_goal: str,
        known_facts: list,
        jurisdiction: str,
    ) -> tuple[dict, list[dict]]:
        trace: list[dict] = []
        document_excerpt = self._document_excerpt(document_text)
        strategy = get_document_strategy(document_type=document_type, document_text=document_text, user_role=user_role)

        intake, stage_trace = await self._call_json_agent(
            stage_id="stage-1",
            stage_name="Intake Agent",
            system_prompt=self._stage_prompt("""
你是法律文书 Intake Agent。识别文书基础信息，不得编造；无法确认的字段写"待补充"。
必须结合 review_strategy 判断这是不是合同、诉讼文书、律师函、仲裁申请等不同类型文书，不能套用通用合同模板。
如果用户声明类型与文书实际内容不一致，必须输出 detected_mismatch=true, mismatch_reason，并把关键影响列入 missing_information。
输出字段：document_type, jurisdiction, user_role, counterparty_role, purpose, amount, term,
performance_location, dispute_resolution, review_focus(list), missing_information(list), detected_mismatch(boolean), mismatch_reason。
"""),
            user_payload={
                "document_text": document_excerpt,
                "declared_document_type": document_type,
                "declared_user_role": user_role,
                "review_goal": review_goal,
                "known_facts": known_facts,
                "jurisdiction": jurisdiction,
                "review_strategy": strategy.to_payload(),
            },
            temperature=0.1,
            max_tokens=1800,
        )
        trace.append(stage_trace)
        if not isinstance(intake, dict):
            intake = {}
        strategy = get_document_strategy(
            document_type=intake.get("document_type") or document_type,
            document_text=document_text,
            user_role=intake.get("user_role") or user_role,
        )
        strategy_pending_facts = build_strategy_pending_facts(strategy, document_text)
        await self._emit_progress(
            stage_id="stage-1b",
            stage_name="Document Strategy Agent",
            status="completed",
            extra={
                "strategy_id": strategy.strategy_id,
                "strategy_name": strategy.display_name,
                "required_field_gap_count": len(strategy_pending_facts),
            },
        )
        trace.append(
            {
                "stage_id": "stage-1b",
                "stage_name": "Document Strategy Agent",
                "status": "completed",
                "model": "document-type-strategy-router",
                "duration_ms": 0,
                "strategy_id": strategy.strategy_id,
                "strategy_name": strategy.display_name,
                "required_field_gap_count": len(strategy_pending_facts),
            }
        )

        heuristic_clauses = self._heuristic_clause_map(document_text)
        clause_review, stage_trace = await self._call_json_agent(
            stage_id="stage-2",
            stage_name="Clause Mapping Agent",
            system_prompt=self._stage_prompt("""
你是 Clause Mapping Agent。基于系统预切分结果校正条款类型和标题。
条款类型必须贴合 review_strategy，例如租赁合同区分押金/维修/退租，劳动合同区分试用期/劳动报酬/社保，诉讼文书区分请求/事实/证据。
只输出 {"clauses":[...]}。保留 clause_id、clause_number、page_number、original_text，不得改写原文。
如果原文切分异常，应保留原文并标注 clause_type="待人工复核"，不得自行补全文字。
"""),
            user_payload={
                "intake": intake,
                "review_strategy": strategy.to_payload(),
                "pre_split_clauses": self._clauses_for_model(heuristic_clauses, limit=45),
            },
            temperature=0.0,
            max_tokens=5000,
        )
        trace.append(stage_trace)
        clauses = heuristic_clauses
        if isinstance(clause_review, dict) and isinstance(clause_review.get("clauses"), list) and clause_review["clauses"]:
            by_id = {clause.get("clause_id"): dict(clause) for clause in heuristic_clauses}
            for item in clause_review["clauses"]:
                if not isinstance(item, dict):
                    continue
                clause_id = item.get("clause_id")
                if clause_id in by_id:
                    by_id[clause_id] = {**by_id[clause_id], **item}
            clauses = list(by_id.values()) or heuristic_clauses

        rule_scan = self._rule_based_issue_scan(
            clauses,
            document_type=intake.get("document_type") or document_type,
            user_role=intake.get("user_role") or user_role,
            strategy=strategy,
        )
        await self._emit_progress(
            stage_id="stage-2b",
            stage_name="Deterministic Issue Pre-scan",
            status="completed",
            extra={
                "risk_candidate_count": len(rule_scan.get("risk_candidates", [])),
                "missing_clause_candidate_count": len(rule_scan.get("missing_clause_candidates", [])),
            },
        )
        trace.append(
            {
                "stage_id": "stage-2b",
                "stage_name": "Deterministic Issue Pre-scan",
                "status": "completed",
                "model": "rule-based-clause-scanner",
                "duration_ms": 0,
                "risk_candidate_count": len(rule_scan.get("risk_candidates", [])),
                "missing_clause_candidate_count": len(rule_scan.get("missing_clause_candidates", [])),
                "strategy_id": strategy.strategy_id,
            }
        )
        selected_issue_clauses = self._select_clauses_for_issue_spotting(clauses, rule_scan)

        issue_result, stage_trace = await self._call_json_agent(
            stage_id="stage-3",
            stage_name="Issue Spotter Agent",
            system_prompt=self._stage_prompt("""
你是 Issue Spotter Agent。按主体资格、标的、付款、交付/验收、质量/维修、违约责任、解除、通知送达、保密、知识产权、数据、不可抗力、争议解决、附件、税费、签章、证据留存等维度识别风险。
必须优先执行 review_strategy 中的文书专属审查维度、必备字段、缺失条款和律师复核触发条件；不得把起诉状、答辩状、律师函、仲裁申请等诉讼/非诉文书当作普通合同审查。
输出 JSON：risk_items, risk_matrix, missing_clauses, favorable_clauses, pending_facts。
risk_items 每项必须包含 risk_id,title,risk_level(低/中/高/重大),risk_type,original_clause{clause_number,page_number,text},issue_location,probability,severity,priority,legal_analysis,status。
favorable_clauses 每项必须包含 clause_reference, text/original_text, analysis, favorable_to, reason, keep_or_modify；不得只写“相对有利，建议保留”。
pending_facts 必须写清该事实如何影响风险等级、法律依据或修改方案。
"""),
            user_payload={
                "intake": intake,
                "review_strategy": strategy.to_payload(),
                "risk_dimensions": RISK_DIMENSIONS,
                "rule_scan_candidates": rule_scan,
                "clauses": selected_issue_clauses,
                "known_facts": known_facts,
                "user_role": user_role,
                "review_goal": review_goal,
                "strategy_pending_facts": strategy_pending_facts,
            },
            temperature=0.2,
            max_tokens=9000,
        )
        trace.append(stage_trace)
        if stage_trace.get("status") in {"error", "parse_error"}:
            fallback_risk_items = [
                item for item in self._ensure_list(rule_scan.get("risk_candidates")) if isinstance(item, dict)
            ]
            fallback_missing_clauses = [
                item for item in self._ensure_list(rule_scan.get("missing_clause_candidates")) if isinstance(item, dict)
            ]
            issue_result = {
                "risk_items": fallback_risk_items,
                "risk_matrix": [],
                "missing_clauses": fallback_missing_clauses,
                "favorable_clauses": [],
                "pending_facts": self._merge_pending_facts(
                    strategy_pending_facts,
                    intake.get("missing_information"),
                ),
            }
            fallback_reason = stage_trace.get("error") or stage_trace.get("parse_error") or "Issue Spotter Agent output unavailable"
            await self._emit_progress(
                stage_id="stage-3-fallback",
                stage_name="Issue Spotter Fallback",
                status="completed",
                detail="风险识别 Agent 输出不可用，已使用规则预扫描结果继续生成报告。",
                extra={
                    "risk_candidate_count": len(fallback_risk_items),
                    "missing_clause_candidate_count": len(fallback_missing_clauses),
                },
            )
            trace.append(
                {
                    "stage_id": "stage-3-fallback",
                    "stage_name": "Issue Spotter Fallback",
                    "status": "completed",
                    "model": "deterministic-rule-scan",
                    "duration_ms": 0,
                    "reason": fallback_reason,
                    "risk_candidate_count": len(fallback_risk_items),
                    "missing_clause_candidate_count": len(fallback_missing_clauses),
                }
            )
        elif not isinstance(issue_result, dict):
            issue_result = {}
        issue_result = self._merge_rule_based_issue_result(issue_result, rule_scan)
        issue_result["pending_facts"] = self._merge_pending_facts(
            issue_result.get("pending_facts"),
            strategy_pending_facts,
            intake.get("missing_information"),
        )

        risk_items = self._ground_and_normalize_risk_items(self._ensure_list(issue_result.get("risk_items")), clauses)
        risk_matrix = self._ensure_list(issue_result.get("risk_matrix"))
        for idx, risk in enumerate(risk_items):
            if not isinstance(risk, dict):
                continue
            risk["risk_id"] = f"R-{idx + 1:03d}"
            risk["risk_level"] = self._normalize_risk_level(risk.get("risk_level"))
            risk["review_strategy_id"] = strategy.strategy_id
            risk.setdefault("status", "未处理")
            citations = self.legal_research.search_for_risk(risk, limit=3, strategy_id=strategy.strategy_id)
            existing = self._ensure_list(risk.get("citations"))
            risk["citations"] = self.legal_research.validate_citations(citations + existing[:1])
        risk_matrix = self._build_risk_matrix(risk_items)
        coverage_audit = self._build_coverage_audit(
            clauses=clauses,
            selected_clauses=selected_issue_clauses,
            rule_scan=rule_scan,
            strategy=strategy,
            strategy_pending_facts=strategy_pending_facts,
        )
        issue_result["missing_clauses"] = self._attach_missing_clause_citations(
            issue_result.get("missing_clauses"),
            strategy_id=strategy.strategy_id,
        )

        trace.append(
            {
                "stage_id": "stage-4",
                "stage_name": "Legal Research Agent",
                "status": "completed",
                "model": "local-source-retriever",
                "duration_ms": 0,
                "source_policy": "Only citations from legal_knowledge or curated local sources are marked 已校验; model-only citations are capped as 待核验.",
            }
        )
        await self._emit_progress(
            stage_id="stage-4",
            stage_name="Legal Research Agent",
            status="completed",
            extra={"risk_count": len(risk_items)},
        )

        for risk in risk_items:
            if isinstance(risk, dict):
                risk["citations"] = self.legal_research.validate_citations(risk.get("citations") or [])
        await self._emit_progress(
            stage_id="stage-5",
            stage_name="Citation Validator Agent",
            status="completed",
        )
        trace.append(
            {
                "stage_id": "stage-5",
                "stage_name": "Citation Validator Agent",
                "status": "completed",
                "model": "deterministic-validator",
                "duration_ms": 0,
            }
        )

        senior_review, stage_trace = await self._call_json_agent(
            stage_id="stage-6",
            stage_name="Senior Lawyer Review Agent",
            system_prompt=self._stage_prompt("""
你是 Senior Lawyer Review Agent。复核风险等级、结论克制性、举证责任、相对方抗辩和律师复核必要性。
必须按 review_strategy 做专业审查验收：检查必备字段是否遗漏、文书类型是否匹配、是否需要执业律师复核、报告是否达到律师工作底稿标准。
输出 JSON：overall_risk_level,recommendation,lawyer_review_required,priority_actions(list),missing_facts(list),adjustments(list),delivery_blockers(list),human_review_focus(list)。
"""),
            user_payload={
                "intake": intake,
                "review_strategy": strategy.to_payload(),
                "risk_matrix": risk_matrix,
                "risk_items": risk_items,
                "missing_clauses": issue_result.get("missing_clauses", []),
                "pending_facts": issue_result.get("pending_facts", []),
                "coverage_audit": coverage_audit,
            },
            temperature=0.2,
            max_tokens=3500,
        )
        trace.append(stage_trace)
        if not isinstance(senior_review, dict):
            senior_review = {}

        drafting, stage_trace = await self._call_json_agent(
            stage_id="stage-7",
            stage_name="Drafting Agent",
            system_prompt=self._stage_prompt("""
你是 Drafting Agent。为每个风险输出可复制修改方案，含 delete/add/replace、保守版、平衡版、底线版、谈判策略。
替代条款必须符合 review_strategy 的文书类型和用户角色；诉讼/仲裁/律师函类文书应输出可直接用于事实、请求、证据或函件措辞的修改文本，而不是合同条款模板。
每个版本必须体现不同谈判强度，不得三版同文；如果材料不足，应写出需要补充的变量占位符。
输出 JSON：{"drafts":[{"risk_id":"R-001","delete":[],"add":[],"replace":[],"conservative_clause":"","balanced_clause":"","bottom_line_clause":"","negotiation_strategy":""}]}。
"""),
            user_payload={
                "user_role": user_role,
                "document_type": document_type,
                "review_strategy": strategy.to_payload(),
                "risk_items": risk_items,
            },
            temperature=0.35,
            max_tokens=9000,
        )
        trace.append(stage_trace)
        draft_map = {}
        if isinstance(drafting, dict):
            for draft in self._ensure_list(drafting.get("drafts")):
                if isinstance(draft, dict) and draft.get("risk_id"):
                    draft_map[draft["risk_id"]] = draft

        for risk in risk_items:
            if not isinstance(risk, dict):
                continue
            draft = draft_map.get(risk.get("risk_id"), {})
            risk["revision_plan"] = {
                "delete": self._ensure_list(draft.get("delete")),
                "add": self._ensure_list(draft.get("add")),
                "replace": self._ensure_list(draft.get("replace")),
                "conservative_clause": draft.get("conservative_clause") or "当前材料不足，需结合原条款由执业律师补充保守版条款。",
                "balanced_clause": draft.get("balanced_clause") or "当前材料不足，需结合商业谈判空间补充平衡版条款。",
                "bottom_line_clause": draft.get("bottom_line_clause") or "当前材料不足，需明确最低可接受条件后补充底线版条款。",
                "negotiation_strategy": draft.get("negotiation_strategy") or "先确认事实和证据，再以降低争议成本为理由提出修改。",
            }

        appendix_by_id: dict[str, dict] = {}
        for risk in risk_items:
            if not isinstance(risk, dict):
                continue
            for citation in self._ensure_list(risk.get("citations")):
                if not isinstance(citation, dict):
                    continue
                source_id = citation.get("source_id") or f"SRC-{len(appendix_by_id) + 1:03d}"
                appendix_by_id.setdefault(
                    source_id,
                    {
                        "source_id": source_id,
                        "source_name": citation.get("source_name", "待核验来源"),
                        "article_or_case_number": citation.get("article_or_case_number", ""),
                        "source_type": citation.get("source_type", "实务清单"),
                        "authority_level": citation.get("authority_level", "需核验"),
                        "legal_effect_note": citation.get("legal_effect_note", "需进一步核验效力和适用性。"),
                        "text_excerpt_or_holding": citation.get("text_excerpt_or_holding", ""),
                        "relevance_reason": citation.get("relevance_reason", ""),
                        "verification_status": citation.get("verification_status", "待核验"),
                        "confidence": self._safe_int(citation.get("confidence"), 0),
                        "cited_by_risks": [],
                    },
                )
                appendix_by_id[source_id]["cited_by_risks"].append(risk.get("risk_id"))
        for missing_clause in self._ensure_list(issue_result.get("missing_clauses")):
            if not isinstance(missing_clause, dict):
                continue
            for citation in self._ensure_list(missing_clause.get("citation_details")):
                if not isinstance(citation, dict):
                    continue
                source_id = citation.get("source_id") or f"SRC-{len(appendix_by_id) + 1:03d}"
                appendix_by_id.setdefault(
                    source_id,
                    {
                        "source_id": source_id,
                        "source_name": citation.get("source_name", "待核验来源"),
                        "article_or_case_number": citation.get("article_or_case_number", ""),
                        "source_type": citation.get("source_type", "实务清单"),
                        "authority_level": citation.get("authority_level", "需核验"),
                        "legal_effect_note": citation.get("legal_effect_note", "需进一步核验效力和适用性。"),
                        "text_excerpt_or_holding": citation.get("text_excerpt_or_holding", ""),
                        "relevance_reason": citation.get("relevance_reason", ""),
                        "verification_status": citation.get("verification_status", "待核验"),
                        "confidence": self._safe_int(citation.get("confidence"), 0),
                        "cited_by_risks": [],
                        "cited_by_missing_clauses": [],
                    },
                )
                appendix_by_id[source_id].setdefault("cited_by_missing_clauses", []).append(
                    missing_clause.get("name", "缺失条款")
                )

        report = {
            "report_meta": {
                "document_type": intake.get("document_type") or document_type,
                "jurisdiction": intake.get("jurisdiction") or jurisdiction,
                "user_role": intake.get("user_role") or user_role,
                "review_strategy_id": strategy.strategy_id,
                "review_strategy_name": strategy.display_name,
                "professional_grade": "律师工作底稿级",
                "overall_risk_level": senior_review.get("overall_risk_level") or self._infer_overall_risk_level(risk_items),
                "recommendation": senior_review.get("recommendation") or "修改后签署",
                "lawyer_review_required": bool(senior_review.get("lawyer_review_required", True))
                or strategy.matter_type in {"诉讼文书", "仲裁文书", "非诉函件"},
            },
            "executive_summary": {
                "top_risks": [risk.get("title", "") for risk in risk_items[:5] if isinstance(risk, dict)],
                "priority_actions": senior_review.get("priority_actions") or self._build_priority_actions(risk_items),
                "missing_facts": senior_review.get("missing_facts") or [item.get("field", "") for item in self._ensure_list(issue_result.get("pending_facts")) if isinstance(item, dict)],
            },
            "contract_summary": {
                "purpose": intake.get("purpose", "待补充"),
                "main_obligations": intake.get("review_focus") or [],
                "payment_terms": intake.get("amount", "待补充"),
                "term": intake.get("term", "待补充"),
                "dispute_resolution": intake.get("dispute_resolution", "待补充"),
            },
            "risk_matrix": risk_matrix or self._build_risk_matrix(risk_items),
            "risk_items": risk_items,
            "missing_clauses": self._ensure_list(issue_result.get("missing_clauses")),
            "favorable_clauses": self._ensure_list(issue_result.get("favorable_clauses")),
            "pending_facts": self._ensure_list(issue_result.get("pending_facts")),
            "legal_authority_appendix": list(appendix_by_id.values()),
            "review_strategy": strategy.to_report_dict(),
            "professional_review_framework": self._build_strategy_framework(strategy),
            "coverage_audit": coverage_audit,
            "disclaimer": "本报告为 AI 辅助生成的风险提示和文书草稿，不构成正式法律意见；复杂事项请咨询执业律师。法律依据中标注为“待核验”的内容，必须在正式使用前由人工或权威法库复核。",
            "pipeline_trace": trace,
        }
        trace.append(
            {
                "stage_id": "stage-8",
                "stage_name": "Report Assembly Agent",
                "status": "completed",
                "model": "deterministic-assembler",
                "duration_ms": 0,
            }
        )
        await self._emit_progress(
            stage_id="stage-8",
            stage_name="Report Assembly Agent",
            status="completed",
        )
        report["pipeline_trace"] = trace
        return self._normalize_assembled_report(
            report=report,
            document_type=document_type,
            jurisdiction=jurisdiction,
            user_role=user_role,
        ), trace

    def _infer_overall_risk_level(self, risk_items: list) -> str:
        levels = [self._normalize_risk_level(r.get("risk_level")) for r in risk_items if isinstance(r, dict)]
        if "重大" in levels:
            return "重大"
        if levels.count("高") >= 2:
            return "高"
        if "高" in levels or levels.count("中") >= 3:
            return "中"
        return "低"

    def _build_priority_actions(self, risk_items: list) -> list[str]:
        actions = []
        for risk in risk_items[:5]:
            if not isinstance(risk, dict):
                continue
            actions.append(f"优先处理：{risk.get('title', '未命名风险')}，补充或修改对应条款并保留谈判记录。")
        return actions

    def _build_risk_matrix(self, risk_items: list) -> list[dict]:
        matrix = []
        for idx, risk in enumerate(risk_items):
            if not isinstance(risk, dict):
                continue
            matrix.append(
                {
                    "risk_id": risk.get("risk_id", f"R-{idx + 1:03d}"),
                    "title": risk.get("title", "未命名风险"),
                    "risk_level": self._normalize_risk_level(risk.get("risk_level")),
                    "risk_type": risk.get("risk_type", "法律风险"),
                    "clause_reference": risk.get("original_clause", {}).get("clause_number", "未定位")
                    if isinstance(risk.get("original_clause"), dict)
                    else "未定位",
                    "probability": risk.get("probability", "中"),
                    "severity": risk.get("severity", "中"),
                    "priority": self._safe_int(risk.get("priority"), idx + 1),
                }
            )
        return matrix

    async def generate_deep_review(
        self,
        document_text: str,
        document_type: str = "合同",
        user_role: str = "甲方",
        review_goal: str = "签署前审查",
        known_facts: Optional[list] = None,
        jurisdiction: str = "中国大陆",
    ) -> Dict[str, Any]:
        """
        Generate a deep legal review report by calling AI with the Agent Team system prompt.
        
        Args:
            document_text: The full text of the legal document to review
            document_type: Type of document (合同/起诉状/答辩状/律师函/仲裁申请书/其他)
            user_role: User's role (承租方/出租方/买方/卖方/甲方/乙方/公司/员工/其他)
            review_goal: Review objective (签署前审查/争议处理/文书生成/律师复核前初审)
            known_facts: List of known facts about the case
            jurisdiction: Legal jurisdiction (default: 中国大陆)
            
        Returns:
            Dict containing the structured deep review report
        """
        if not known_facts:
            known_facts = []

        # Step 1: Pre-check if the document is actually a legal document
        await self._emit_progress(
            stage_id="document-preflight",
            stage_name="Document Preflight",
            status="running",
        )
        non_legal_error = await self._check_document_is_legal(document_text)
        if non_legal_error:
            await self._emit_progress(
                stage_id="document-preflight",
                stage_name="Document Preflight",
                status="error",
                detail=non_legal_error,
            )
            raise ValueError(non_legal_error)
        await self._emit_progress(
            stage_id="document-preflight",
            stage_name="Document Preflight",
            status="completed",
        )

        try:
            logger.info("Running staged deep legal review pipeline...")
            report, trace = await self._run_deep_review_pipeline(
                document_text=document_text,
                document_type=document_type,
                user_role=user_role,
                review_goal=review_goal,
                known_facts=known_facts,
                jurisdiction=jurisdiction,
            )

            # Ensure report_meta has required fields
            if "report_meta" not in report:
                report["report_meta"] = {}
            report["report_meta"]["report_id"] = f"RPT-{uuid.uuid4().hex[:8].upper()}"
            report["report_meta"]["generated_at"] = datetime.utcnow().isoformat()
            report["pipeline_trace"] = trace
            
            logger.info(f"Deep review report generated successfully: {report['report_meta']['report_id']}")
            return report
        except Exception as e:
            logger.error(f"Deep review generation failed: {e}")
            raise

    async def generate_legal_document(
        self,
        doc_type: str,
        user_role: str,
        title: str,
        input_data: Dict[str, Any],
        language: str = "zh",
    ) -> Dict[str, Any]:
        """
        Generate a legal document using AI from first principles.
        
        Args:
            doc_type: Type of document to generate
            user_role: User's role in the legal relationship
            title: Title for the document
            input_data: Additional context and requirements
            language: Output language
            
        Returns:
            Dict containing the generated document
        """
        try:
            logger.info(f"Calling AI for document generation: {doc_type}")
            document, trace = await self._call_json_agent(
                stage_id="document-generation",
                stage_name="Legal Document Drafting Agent",
                system_prompt=DOCUMENT_GENERATION_SYSTEM_PROMPT
                + "\n\n质量要求：正文不得只给模板占位符；关键条款必须可复制；法律依据不得编造，无法核验时标注待核验。",
                user_payload={
                    "doc_type": doc_type,
                    "title": title,
                    "user_role": user_role,
                    "language": language,
                    "input_data": input_data,
                    "drafting_requirements": [
                        "结构完整，包含主体、事实背景、权利义务、违约责任、争议解决和签署要素。",
                        "输出可直接进入律师复核流程，不输出空泛说明。",
                        "所有法律依据写入 legal_references；不确定的依据标注待核验。",
                    ],
                },
                temperature=0.25,
                max_tokens=9000,
            )
            if trace.get("status") == "error":
                raise ValueError(f"文书生成阶段失败：{trace.get('error', '')}")
            document = self._normalize_generated_document(
                document=document,
                doc_type=doc_type,
                title=title,
                user_role=user_role,
                language=language,
            )
            document["pipeline_trace"] = [trace]
            logger.info(f"Document generated successfully: {doc_type}")
            return document
        except Exception as e:
            logger.error(f"Document generation failed: {e}")
            raise

    def _normalize_generated_document(
        self,
        *,
        document: Any,
        doc_type: str,
        title: str,
        user_role: str,
        language: str,
    ) -> dict:
        if not isinstance(document, dict):
            raise ValueError("AI返回的文书格式不是 JSON 对象，请重试。")

        document.setdefault("document_meta", {})
        meta = document["document_meta"]
        meta.setdefault("doc_type", doc_type)
        meta.setdefault("title", title or doc_type)
        meta.setdefault("jurisdiction", "中国大陆")
        meta.setdefault("user_role", user_role)
        meta.setdefault("language", language)
        meta["generated_at"] = datetime.utcnow().isoformat()
        meta.setdefault("disclaimer", "本文书为AI辅助生成的草稿，不构成正式法律文件，请执业律师复核后使用。")

        document["content"] = str(document.get("content") or "").strip()
        document["key_clauses"] = self._ensure_list(document.get("key_clauses"))
        document["review_notes"] = self._ensure_list(document.get("review_notes"))
        document["legal_references"] = self._ensure_list(document.get("legal_references"))

        appendix: dict[str, dict] = {}
        reference_queries = list(document["legal_references"])
        for clause in document["key_clauses"]:
            if isinstance(clause, dict) and clause.get("legal_basis"):
                reference_queries.append(clause["legal_basis"])
        for query in reference_queries:
            for citation in self.legal_research.validate_citations(self.legal_research.search(str(query), limit=2)):
                source_id = citation.get("source_id")
                if source_id:
                    appendix[source_id] = citation
        document["legal_authority_appendix"] = list(appendix.values())
        document["quality_audit"] = self._build_generated_document_quality_audit(document)
        return document

    def _build_generated_document_quality_audit(self, document: dict) -> dict:
        warnings: list[str] = []
        score = 100
        content = document.get("content") or ""
        key_clauses = [item for item in self._ensure_list(document.get("key_clauses")) if isinstance(item, dict)]
        appendix = [item for item in self._ensure_list(document.get("legal_authority_appendix")) if isinstance(item, dict)]

        if len(content) < 600:
            warnings.append("文书正文偏短，可能只是框架草稿，不能直接使用。")
            score -= 30
        if len(key_clauses) < 3:
            warnings.append("关键条款数量不足，建议补充权利义务、违约责任和争议解决条款。")
            score -= 20
        if not appendix:
            warnings.append("未命中任何已校验法律依据，正式使用前必须人工核验。")
            score -= 20
        if "待补" in content or "XXX" in content or "【】" in content:
            warnings.append("正文仍含占位符或待补内容。")
            score -= 15
        if not document.get("review_notes"):
            warnings.append("未列出需用户确认事项，可能掩盖事实缺口。")
            score -= 8

        normalized_score = max(0, min(100, score))
        return {
            "quality_score": normalized_score,
            "quality_level": "高" if normalized_score >= 85 else "中" if normalized_score >= 70 else "低",
            "warnings": warnings,
            "lawyer_review_required": True,
            "source_policy": "生成文书中的法律依据只要未命中本地来源库，即不视为已校验。",
        }

    async def generate_case_ai_response(
        self,
        case_context: str,
        user_message: str,
        conversation_history: Optional[list] = None,
    ) -> str:
        """
        Generate AI response for case workspace chat.
        
        Args:
            case_context: Context about the case (facts, documents, etc.)
            user_message: User's question or request
            conversation_history: Previous conversation messages
            
        Returns:
            AI response text
        """
        if not conversation_history:
            conversation_history = []

        system_msg = f"""你是"律审雷达"的案件法律助手。你正在协助用户处理一个法律案件。

案件背景：
{case_context}

你的职责：
1. 回答用户关于案件的法律问题
2. 提供法律分析和建议（标注为AI辅助意见，非正式法律意见）
3. 帮助整理案件事实和证据
4. 提供诉讼策略建议
5. 协助起草法律文书

注意事项：
- 不得编造法律条文或案例
- 不确定的内容必须标注
- 复杂问题建议咨询执业律师
- 回答要专业、简洁、有条理
- 涉及法律判断时按「初步结论 / 依据与适用 / 事实缺口 / 证据建议 / 下一步」组织
- 未检索或未核验的法律依据必须写明“待核验”，不得假装已校验"""

        messages = [ChatMessage(role="system", content=system_msg)]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append(ChatMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", "")
            ))
        
        messages.append(ChatMessage(role="user", content=user_message))

        request = GenTxtRequest(
            messages=messages,
            model=resolve_model(settings.app_ai_review_model, task="review"),
            stream=False,
            temperature=0.5,
            max_tokens=4096,
        )

        try:
            response = await self.aihub.gentxt(request)
            return response.content
        except Exception as e:
            logger.error(f"Case AI response failed: {e}")
            raise
