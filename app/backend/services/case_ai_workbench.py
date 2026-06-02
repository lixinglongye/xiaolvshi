import json
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.case_files import Case_files
from models.case_facts import Case_facts
from models.case_materials import Case_materials
from models.case_parties import Case_parties
from models.case_tasks import Case_tasks
from models.cases import Cases
from models.claims import Claims
from models.evidence_items import Evidence_items
from models.fact_events import Fact_events
from models.generated_documents import Generated_documents
from models.legal_sources import Legal_sources
from schemas.aihub import ChatMessage, GenTxtRequest
from services.aihub import AIHubService
from services.model_catalog import resolve_model

logger = logging.getLogger(__name__)


def _clip(value: Any, limit: int = 1200) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...【已截断】"


def _json_loads(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


class CaseAIWorkbenchService:
    """Evidence-aware AI chat over one case workspace."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def chat(
        self,
        *,
        case_id: int,
        user_id: str,
        message: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        clean_message = (message or "").strip()
        if not clean_message:
            raise ValueError("请输入问题")

        workspace = await self._load_workspace(case_id, user_id)
        context_text = self._build_context(workspace)
        messages = self._build_messages(
            case_title=workspace["case"].title,
            context_text=context_text,
            message=clean_message,
            conversation_history=conversation_history or [],
        )
        model = resolve_model(settings.app_ai_review_model or settings.app_ai_fast_model, task="review")
        response = await AIHubService().gentxt(
            GenTxtRequest(
                model=model,
                temperature=0.2,
                max_tokens=2600,
                messages=messages,
            )
        )

        return {
            "success": True,
            "response": response.content,
            "model": response.model,
            "usage": response.usage,
            "case_snapshot": self._snapshot(workspace),
        }

    async def _load_workspace(self, case_id: int, user_id: str) -> dict[str, Any]:
        case_result = await self.db.execute(select(Cases).where(Cases.id == case_id, Cases.user_id == user_id))
        case = case_result.scalar_one_or_none()
        if not case:
            raise ValueError("Case not found")

        async def rows(stmt):
            result = await self.db.execute(stmt)
            return result.scalars().all()

        materials = await rows(
            select(Case_materials)
            .where(Case_materials.case_id == case_id, Case_materials.user_id == user_id)
            .order_by(Case_materials.material_no, Case_materials.id)
        )
        case_files = await rows(
            select(Case_files)
            .where(Case_files.case_id == case_id, Case_files.user_id == user_id)
            .order_by(Case_files.id)
        )
        facts = await rows(
            select(Case_facts)
            .where(Case_facts.case_id == case_id, Case_facts.user_id == user_id)
            .order_by(Case_facts.event_date, Case_facts.id)
        )
        fact_events = await rows(
            select(Fact_events)
            .where(Fact_events.case_id == case_id, Fact_events.user_id == user_id)
            .order_by(Fact_events.event_date, Fact_events.id)
        )
        parties = await rows(
            select(Case_parties)
            .where(Case_parties.case_id == case_id, Case_parties.user_id == user_id)
            .order_by(Case_parties.id)
        )
        evidence_items = await rows(
            select(Evidence_items)
            .where(Evidence_items.case_id == case_id, Evidence_items.user_id == user_id)
            .order_by(Evidence_items.sequence_no, Evidence_items.id)
        )
        claims = await rows(
            select(Claims)
            .where(Claims.case_id == case_id, Claims.user_id == user_id)
            .order_by(Claims.claim_no, Claims.id)
        )
        tasks = await rows(
            select(Case_tasks)
            .where(Case_tasks.case_id == case_id, Case_tasks.user_id == user_id)
            .order_by(Case_tasks.due_date, Case_tasks.id)
        )
        documents = await rows(
            select(Generated_documents)
            .where(Generated_documents.case_id == case_id, Generated_documents.user_id == user_id)
            .order_by(Generated_documents.created_at.desc(), Generated_documents.id.desc())
            .limit(8)
        )
        legal_sources = await rows(select(Legal_sources).order_by(Legal_sources.id).limit(12))

        return {
            "case": case,
            "materials": materials,
            "case_files": case_files,
            "facts": facts,
            "fact_events": fact_events,
            "parties": parties,
            "evidence_items": evidence_items,
            "claims": claims,
            "tasks": tasks,
            "documents": documents,
            "legal_sources": legal_sources,
        }

    def _build_messages(
        self,
        *,
        case_title: str,
        context_text: str,
        message: str,
        conversation_history: list[dict[str, str]],
    ) -> list[ChatMessage]:
        system_prompt = """你是律审雷达的案件 AI 工作台，不是通用闲聊助手。

回答规则：
1. 只能基于“当前案件上下文”和用户问题回答；上下文没有的信息必须明确说缺失，并给出需要补充的材料或问题。
2. 区分已确认事实、待核实事实、推断和律师复核意见；不得编造当事人、证据、金额、日期、法条或裁判结论。
3. 涉及证据时尽量引用材料编号、证据编号、文件名、页码/段落或事实编号。
4. 涉及法律依据时只引用上下文给出的本地法条库；不足时说明“需进一步检索并核验现行有效性”。
5. 输出要像律师助理工作底稿：结论先行、分点清楚、给出下一步可执行清单。
6. 如果用户问“能不能生成/起诉/提交”，必须提示正式文书需执业律师复核。
"""
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(
                role="user",
                content=f"当前案件：{case_title}\n\n以下是结构化案件上下文：\n{context_text}",
            ),
        ]
        for item in conversation_history[-8:]:
            role = item.get("role")
            if role not in {"user", "assistant"}:
                continue
            content = _clip(item.get("content"), 1000)
            if content:
                messages.append(ChatMessage(role=role, content=content))
        messages.append(ChatMessage(role="user", content=message))
        return messages

    def _build_context(self, workspace: dict[str, Any]) -> str:
        case: Cases = workspace["case"]
        sections = [
            "## 案件基础信息",
            f"- 案件ID：{case.id}",
            f"- 案件名称：{case.title}",
            f"- 类型/阶段：{case.case_type or '待补充'} / {case.stage or '待补充'}",
            f"- 委托人：{case.client_name or '待补充'}",
            f"- 对方当事人：{case.opposing_party or '待补充'}",
            f"- 代理立场：{case.role or '待确认'}",
            f"- 管辖/仲裁：{case.court_or_arbitration or case.jurisdiction or '待补充'}",
            f"- 金额：{case.amount or '待补充'}",
            f"- 案情摘要：{_clip(case.summary, 900) or '待补充'}",
            f"- 争议焦点：{_clip(case.dispute_focus, 900) or '待补充'}",
            f"- 请求/目标：{_clip(case.claims, 900) or '待补充'}",
            f"- 缺失材料：{_clip(case.missing_materials, 900) or '待系统继续识别'}",
            f"- 下一步：{_clip(case.next_steps, 900) or '待系统继续识别'}",
        ]

        sections.extend(["", "## 当事人/团队"])
        parties: list[Case_parties] = workspace["parties"]
        if parties:
            for party in parties[:12]:
                sections.append(
                    f"- {party.name}｜{party.party_type or '角色待补'}｜{party.identity_type or '身份类型待补'}｜"
                    f"证件/代码：{party.id_number or '待补'}｜联系方式：{party.contact or '待补'}"
                )
        else:
            sections.append("- 暂无结构化当事人信息。")

        sections.extend(["", "## 用户登记材料"])
        materials: list[Case_materials] = workspace["materials"]
        if materials:
            for item in materials[:16]:
                sections.append(
                    f"- {item.material_no or item.id}｜{item.title}｜类型：{item.material_type or '待分类'}｜"
                    f"证据：{'是' if item.is_evidence else '否'}｜来源：{item.source or '待补'}｜页码：{item.page_refs or '待补'}｜"
                    f"证明目的：{_clip(item.proof_purpose, 260) or '待补'}｜摘录：{_clip(item.parsed_text, 700) or '暂无解析文本'}"
                )
        else:
            sections.append("- 暂无用户登记材料。")

        sections.extend(["", "## 导入文件解析"])
        case_files: list[Case_files] = workspace["case_files"]
        if case_files:
            for item in case_files[:14]:
                sections.append(
                    f"- {item.file_id}｜{item.original_name}｜路径：{item.relative_path or '-'}｜"
                    f"类型：{item.doc_type or '待分类'}｜证据类别：{item.evidence_category or '待分类'}｜"
                    f"页数：{item.page_count or '未知'}｜OCR：{'需要' if item.ocr_required else '否/未知'}｜"
                    f"摘录：{_clip(item.parsed_text or item.text_excerpt, 900) or '暂无文本'}"
                )
        else:
            sections.append("- 暂无 ZIP 导入文件记录。")

        sections.extend(["", "## 事实库"])
        facts: list[Case_facts] = workspace["facts"]
        if facts:
            for fact in facts[:24]:
                sections.append(
                    f"- {fact.fact_no or fact.id}｜{fact.event_date or '时间待核实'}｜{_clip(fact.fact_text, 420)}｜"
                    f"来源：{fact.source_refs or '待核实'}｜置信度：{fact.confidence or '中'}｜矛盾：{fact.contradiction_note or '-'}"
                )
        else:
            sections.append("- 暂无人工确认事实。")

        fact_events: list[Fact_events] = workspace["fact_events"]
        if fact_events:
            sections.extend(["", "## AI 提取事实事件"])
            for event in fact_events[:24]:
                refs = _json_loads(event.evidence_refs_json, [])
                sections.append(
                    f"- {event.event_id or event.id}｜{event.event_date or '时间待核实'}｜{event.event_title}｜"
                    f"{_clip(event.event_detail, 420)}｜证据引用：{_clip(refs, 300)}"
                )

        sections.extend(["", "## 证据目录/证据项"])
        evidence_items: list[Evidence_items] = workspace["evidence_items"]
        if evidence_items:
            for evidence in evidence_items[:20]:
                sections.append(
                    f"- {evidence.evidence_id or evidence.id}｜{evidence.evidence_name}｜来源：{evidence.evidence_source or '待补'}｜"
                    f"页码：{evidence.page_range or '待补'}｜证明目的：{_clip(evidence.proof_purpose, 420) or '待补'}｜"
                    f"弱点：{_clip(evidence.weakness, 260) or '待律师复核'}"
                )
        else:
            marked = [item for item in materials if item.is_evidence]
            if marked:
                for item in marked[:20]:
                    sections.append(
                        f"- {item.material_no or item.id}｜{item.title}｜证明目的：{_clip(item.proof_purpose, 360) or '待补'}｜"
                        f"证据风险：{item.admissibility_risk or '待复核'}"
                    )
            else:
                sections.append("- 暂无已确认电子证据。")

        sections.extend(["", "## 请求/主张"])
        claims: list[Claims] = workspace["claims"]
        if claims:
            for claim in claims[:12]:
                sections.append(
                    f"- 请求{claim.claim_no or claim.id}｜{_clip(claim.claim_text, 500)}｜金额：{claim.amount or '待补'}｜"
                    f"计算：{_clip(claim.calculation_detail, 260) or '待补'}｜风险：{_clip(claim.risk_notes, 260) or '-'}"
                )
        else:
            sections.append(f"- 案件请求字段：{_clip(case.claims, 800) or '待补充'}")

        sections.extend(["", "## 任务/期限"])
        tasks: list[Case_tasks] = workspace["tasks"]
        if tasks:
            for task in tasks[:16]:
                sections.append(
                    f"- {task.status or '待开始'}｜{task.priority or '中'}｜{task.due_date or '无期限'}｜"
                    f"{task.title}｜{_clip(task.description, 260)}"
                )
        else:
            sections.append("- 暂无任务。")

        sections.extend(["", "## 已生成文书"])
        documents: list[Generated_documents] = workspace["documents"]
        if documents:
            for doc in documents:
                qa = _json_loads(doc.qa_report_json, {})
                sections.append(
                    f"- {doc.doc_type}｜{doc.title or doc.doc_type}｜状态：{doc.status or '草稿'}｜"
                    f"QA：{_clip(qa, 320)}｜摘要：{_clip(doc.content or doc.content_markdown, 500)}"
                )
        else:
            sections.append("- 暂无生成文书。")

        sections.extend(["", "## 本地法条库摘录"])
        legal_sources: list[Legal_sources] = workspace["legal_sources"]
        if legal_sources:
            for source in legal_sources:
                sections.append(
                    f"- {source.title}｜{source.code_ref or source.article_no or ''}｜层级：{source.legal_effect_level or '待核验'}｜"
                    f"摘要：{_clip(source.summary or source.content_snippet, 420)}"
                )
        else:
            sections.append("- 暂无法条库条目。")

        return "\n".join(sections)

    def _snapshot(self, workspace: dict[str, Any]) -> dict[str, Any]:
        case: Cases = workspace["case"]
        return {
            "case_id": case.id,
            "title": case.title,
            "material_count": len(workspace["materials"]),
            "imported_file_count": len(workspace["case_files"]),
            "evidence_count": len(workspace["evidence_items"]) or len([m for m in workspace["materials"] if m.is_evidence]),
            "fact_count": len(workspace["facts"]) or len(workspace["fact_events"]),
            "claim_count": len(workspace["claims"]),
            "document_count": len(workspace["documents"]),
        }
