import json
import logging
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.cases import Cases
from models.clarification_sessions import Clarification_sessions
from schemas.aihub import ChatMessage, GenTxtRequest
from services.aihub import AIHubService

logger = logging.getLogger(__name__)


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _json_loads(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


FIELD_QUESTIONS: dict[str, dict[str, str]] = {
    "plaintiff": {
        "question": "请补充原告/申请人的姓名或名称、证件号或统一社会信用代码、住所和联系方式。",
        "why_needed": "起诉状必须记明原告基本信息，且影响主体资格和送达。",
        "answer_type": "text",
    },
    "defendant": {
        "question": "请补充被告/被申请人的姓名或名称、住所、联系方式，法人还需统一社会信用代码和法定代表人。",
        "why_needed": "被告信息决定起诉对象、送达和管辖，不能凭空生成。",
        "answer_type": "text",
    },
    "claims": {
        "question": "请列明具体诉讼请求，包括金额、利息/违约金计算方式、是否请求承担费用。",
        "why_needed": "诉讼请求必须明确、可执行、可计算。",
        "answer_type": "text",
    },
    "key_facts": {
        "question": "请按时间顺序补充关键事实：签约、履行、违约、催告、损失形成等。",
        "why_needed": "事实与理由必须支撑每一项请求。",
        "answer_type": "text",
    },
    "evidence": {
        "question": "请说明已有证据及编号，例如合同、付款凭证、聊天记录、发票、通知送达凭证。",
        "why_needed": "关键事实需要证据来源，文书不得编造证据。",
        "answer_type": "file",
    },
    "court_or_arbitration": {
        "question": "请确认受诉法院/仲裁机构，或提供合同中的管辖/仲裁条款。",
        "why_needed": "管辖错误会影响立案或导致程序风险。",
        "answer_type": "text",
    },
    "amount_calculation": {
        "question": "请补充案涉金额、欠款/损失/利息/违约金的计算起止时间和标准。",
        "why_needed": "金额请求必须有计算依据，避免诉讼请求不明确。",
        "answer_type": "money",
    },
    "user_role": {
        "question": "请确认你代表合同哪一方，例如甲方、乙方、出租方、承租方、买方或卖方。",
        "why_needed": "审查立场会影响风险优先级和修改建议方向。",
        "answer_type": "select",
    },
    "signing_status": {
        "question": "请确认合同是否已经签署或履行。",
        "why_needed": "已签署合同侧重履行风险和补救，未签署合同侧重谈判修改。",
        "answer_type": "select",
    },
    "contract_type": {
        "question": "请确认合同类型，例如买卖、租赁、服务、劳动、借款、股权或知识产权。",
        "why_needed": "不同合同类型的必审字段和法律依据不同。",
        "answer_type": "select",
    },
    "transaction_background": {
        "question": "请补充交易背景、核心标的、金额和履行期限。",
        "why_needed": "交易背景决定条款风险是否真实重要，也影响替代条款设计。",
        "answer_type": "text",
    },
    "focus_points": {
        "question": "请说明你最关注哪些问题，例如付款、解除、违约、知识产权、保密、管辖。",
        "why_needed": "系统会按关注点调整审查权重和报告结构。",
        "answer_type": "text",
    },
    "document_type": {
        "question": "请确认需要生成的文书类型，例如起诉状、答辩状、律师函、仲裁申请书或证据目录。",
        "why_needed": "不同文书的必填字段、格式和校验规则不同。",
        "answer_type": "select",
    },
}

CONTRACT_REVIEW_LOW_VALUE_FIELDS = {
    "plaintiff",
    "defendant",
    "opposing_party",
    "counterparty",
    "counterparty_name",
    "party_a_name",
    "party_b_name",
    "party_name",
    "name",
}

CONTRACT_REVIEW_LOW_VALUE_PATTERNS = (
    r"(合同)?对方(当事人)?的?(名称|姓名|名字)",
    r"(甲方|乙方|买方|卖方|出租方|承租方)的?(名称|姓名|名字)",
    r"补充.*(对方|当事人).*(名称|姓名|名字)",
)


TASK_FIELD_RULES: dict[str, dict[str, list[str]]] = {
    "generate_civil_complaint": {
        "required": ["plaintiff", "defendant", "claims", "key_facts", "evidence", "court_or_arbitration"],
        "optional": ["amount_calculation", "agent_info", "third_party", "witnesses", "preservation"],
    },
    "generate_evidence_catalog": {
        "required": ["evidence", "key_facts", "claims"],
        "optional": ["dispute_focus", "original_copy_status", "page_range", "submitter"],
    },
    "contract_review": {
        "required": ["user_role", "signing_status", "contract_type", "transaction_background"],
        "optional": ["focus_points", "bottom_line_terms", "review_style"],
    },
    "generate_legal_document": {
        "required": ["document_type", "plaintiff", "defendant", "claims", "key_facts"],
        "optional": ["evidence", "court_or_arbitration", "amount_calculation"],
    },
    "case_import": {
        "required": ["upload_mode", "case_relation_hint"],
        "optional": ["client_role", "known_case_name", "known_case_number"],
    },
}


class PlanModeService:
    """Rule-based Plan Mode service used before legal generation or deep review."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        *,
        user_id: str,
        task_type: str,
        user_input: str,
        document_type: Optional[str] = None,
        case_id: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> Clarification_sessions:
        task = self._infer_task_type(task_type, document_type, user_input)
        case = await self._get_case(case_id, user_id) if case_id else None
        slots = self._extract_slots(user_input=user_input, document_type=document_type, case=case, context=context or {})
        ai_result = await self._ai_understand(
            task_type=task,
            document_type=document_type,
            user_input=user_input,
            case=case,
            slots=slots,
            context=context or {},
        )
        if ai_result:
            ai_task = str(ai_result.get("task_type") or "")
            if ai_task in TASK_FIELD_RULES:
                task = ai_task
            slots = self._merge_ai_slots(slots, ai_result.get("slots"))
        missing_required, missing_optional = self._missing_fields(task, slots)
        conflicts = self._detect_conflicts(user_input=user_input, slots=slots) + self._ai_conflicts(ai_result)
        questions = self._ai_questions(ai_result, task_type=task, slots=slots) or self._build_questions(
            missing_required, missing_optional
        )
        completeness = self._completeness_score(task, slots)
        assumptions = self._build_assumptions(missing_required, task)
        plan = self._build_generation_plan(task, slots, missing_required, conflicts)
        understanding = self._ai_understanding(ai_result) or self._build_understanding(task, slots, missing_required, conflicts)
        if ai_result:
            plan["understanding_source"] = "ai"
            plan["understanding_model"] = settings.app_ai_fast_model
            if isinstance(ai_result.get("generation_plan"), dict):
                plan["ai_generation_notes"] = ai_result["generation_plan"]
        else:
            plan["understanding_source"] = "rules"

        session = Clarification_sessions(
            user_id=user_id,
            case_id=case_id,
            task_type=task,
            document_type=document_type,
            status="needs_input" if missing_required else "ready",
            understanding=understanding,
            slots_json=_json_dumps(slots),
            missing_required_json=_json_dumps(missing_required),
            missing_optional_json=_json_dumps(missing_optional),
            conflicts_json=_json_dumps(conflicts),
            questions_json=_json_dumps(questions),
            user_answers_json=_json_dumps([]),
            generation_plan_json=_json_dumps(plan),
            completeness_score=completeness,
            can_generate_draft_with_assumptions=True,
            assumptions_json=_json_dumps(assumptions),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_answers(
        self,
        *,
        session_id: int,
        user_id: str,
        answers: list[dict[str, Any]],
    ) -> Clarification_sessions:
        session = await self.get_owned_session(session_id, user_id)
        prior_answers = _json_loads(session.user_answers_json, [])
        slots = _json_loads(session.slots_json, {})

        for answer in answers:
            field = answer.get("field") or answer.get("question_id")
            value = answer.get("answer") or answer.get("value")
            if field and _has_value(value):
                slots[str(field)] = value

        all_answers = prior_answers + answers
        case = await self._get_case(session.case_id, user_id) if session.case_id else None
        ai_result = await self._ai_understand(
            task_type=session.task_type,
            document_type=session.document_type,
            user_input=_json_dumps(all_answers),
            case=case,
            slots=slots,
            context={"prior_understanding": session.understanding or ""},
        )
        task_type = session.task_type
        if ai_result:
            ai_task = str(ai_result.get("task_type") or "")
            if ai_task in TASK_FIELD_RULES:
                task_type = ai_task
            slots = self._merge_ai_slots(slots, ai_result.get("slots"))
        missing_required, missing_optional = self._missing_fields(task_type, slots)
        conflicts = self._ai_conflicts(ai_result)
        questions = self._ai_questions(ai_result, task_type=task_type, slots=slots) or self._build_questions(
            missing_required, missing_optional
        )
        plan = self._build_generation_plan(task_type, slots, missing_required, conflicts)
        if ai_result:
            plan["understanding_source"] = "ai"
            plan["understanding_model"] = settings.app_ai_fast_model
            if isinstance(ai_result.get("generation_plan"), dict):
                plan["ai_generation_notes"] = ai_result["generation_plan"]
            session.understanding = self._ai_understanding(ai_result) or session.understanding

        session.task_type = task_type
        session.slots_json = _json_dumps(slots)
        session.user_answers_json = _json_dumps(all_answers)
        session.missing_required_json = _json_dumps(missing_required)
        session.missing_optional_json = _json_dumps(missing_optional)
        session.conflicts_json = _json_dumps(conflicts)
        session.questions_json = _json_dumps(questions)
        session.generation_plan_json = _json_dumps(plan)
        session.completeness_score = self._completeness_score(task_type, slots)
        session.status = "ready" if not missing_required else "needs_input"
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_owned_session(self, session_id: int, user_id: str) -> Clarification_sessions:
        result = await self.db.execute(
            select(Clarification_sessions).where(
                Clarification_sessions.id == session_id,
                Clarification_sessions.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Plan Mode session not found")
        return session

    def serialize(self, session: Clarification_sessions) -> dict[str, Any]:
        return {
            "session_id": session.id,
            "status": session.status,
            "task_type": session.task_type,
            "document_type": session.document_type,
            "case_id": session.case_id,
            "completeness_score": session.completeness_score or 0,
            "understanding": session.understanding or "",
            "known_slots": _json_loads(session.slots_json, {}),
            "missing_required": _json_loads(session.missing_required_json, []),
            "missing_optional": _json_loads(session.missing_optional_json, []),
            "conflicts": _json_loads(session.conflicts_json, []),
            "questions": _json_loads(session.questions_json, []),
            "generation_plan": _json_loads(session.generation_plan_json, {}),
            "can_generate_draft_with_assumptions": bool(session.can_generate_draft_with_assumptions),
            "assumptions_if_generate_now": _json_loads(session.assumptions_json, []),
        }

    def generate_assumption_draft(self, session: Clarification_sessions) -> dict[str, Any]:
        slots = _json_loads(session.slots_json, {})
        missing = _json_loads(session.missing_required_json, [])
        plan = _json_loads(session.generation_plan_json, {})
        assumptions = _json_loads(session.assumptions_json, [])
        title = plan.get("document_type") or session.document_type or "法律文书草稿"
        content = [
            f"# {title}",
            "",
            "## 生成前说明",
            "本草稿处于 Plan Mode：部分关键信息尚未补齐，正式使用前必须由律师复核。",
            "",
            "## 已知信息",
        ]
        for key, value in slots.items():
            if _has_value(value):
                content.append(f"- {key}：{value}")
        content.extend(["", "## 缺失字段"])
        if missing:
            content.extend(f"- 【待补充：{field}】" for field in missing)
        else:
            content.append("- 暂无阻断字段。")
        content.extend(["", "## 基于现有信息的草稿框架"])
        for section in plan.get("structure", []):
            content.append(f"### {section}")
            content.append("【待根据已确认事实、证据和法律依据展开】")
            content.append("")
        if assumptions:
            content.append("## 当前假设")
            content.extend(f"- {item}" for item in assumptions)
        return {
            "title": title,
            "content": "\n".join(content),
            "missing_fields": missing,
            "assumptions": assumptions,
            "qa_report": {
                "pass": not missing,
                "severity": "high" if missing else "low",
                "human_review_required": True,
                "issues": [f"缺少必填字段：{field}" for field in missing],
            },
        }

    async def _get_case(self, case_id: Optional[int], user_id: str) -> Optional[Cases]:
        if not case_id:
            return None
        result = await self.db.execute(select(Cases).where(Cases.id == case_id, Cases.user_id == user_id))
        return result.scalar_one_or_none()

    async def _ai_understand(
        self,
        *,
        task_type: str,
        document_type: Optional[str],
        user_input: str,
        case: Optional[Cases],
        slots: dict[str, Any],
        context: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        if not settings.app_ai_base_url or not settings.app_ai_key:
            return None
        case_context = {}
        if case:
            case_context = {
                "title": case.title,
                "case_type": case.case_type,
                "stage": case.stage,
                "client_name": case.client_name,
                "opposing_party": case.opposing_party,
                "role": case.role,
                "court_or_arbitration": case.court_or_arbitration or case.jurisdiction,
                "amount": case.amount,
                "summary": case.summary,
                "dispute_focus": case.dispute_focus,
                "claims": case.claims,
                "missing_materials": case.missing_materials,
                "next_steps": case.next_steps,
                "material_count": case.material_count,
            }
        prompt = {
            "task_type_guess": task_type,
            "document_type": document_type,
            "user_input": user_input,
            "case_context": case_context,
            "rule_extracted_slots": slots,
            "additional_context": context,
            "allowed_task_types": list(TASK_FIELD_RULES.keys()),
            "field_definitions": FIELD_QUESTIONS,
            "output_schema": {
                "task_type": "one of allowed_task_types",
                "understanding": "用中文概括用户真实目标、已知事实、证据状态和阻断缺口",
                "slots": "object，提取或确认的字段；不确定不要填",
                "conflicts": [{"field": "字段名", "message": "冲突说明"}],
                "questions": [
                    {
                        "question_id": "Q001",
                        "priority": "required/optional",
                        "field": "字段名",
                        "question": "面向用户的追问",
                        "why_needed": "为什么法律交付需要该信息",
                        "answer_type": "text/file/money/select",
                        "options": [],
                        "can_skip": False,
                    }
                ],
                "generation_plan": "object，文书/审查的结构、引用要求、QA Gate 和下一步",
            },
        }
        try:
            response = await AIHubService().gentxt(
                GenTxtRequest(
                    model=settings.app_ai_fast_model,
                    temperature=0.1,
                    max_tokens=4096,
                    messages=[
                        ChatMessage(
                            role="system",
                            content=(
                                "你是法律 SaaS 的 Plan Mode 规划代理。"
                                "你的任务是理解用户目标、识别已知槽位、找出缺口/冲突、生成必要追问和交付计划。"
                                "不要编造事实、证据、当事人或法条。"
                                "questions 最多 6 个，每个问题和理由都要简洁。"
                                "只输出一个完整 JSON 对象，不要 Markdown。"
                            ),
                        ),
                        ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=False, default=str)),
                    ],
                )
            )
            parsed = self._parse_ai_json(response.content)
            return parsed if isinstance(parsed, dict) else None
        except Exception as exc:
            logger.warning("Plan Mode AI understanding failed; falling back to rules: %s", exc)
            return None

    def _parse_ai_json(self, raw: str) -> Optional[dict[str, Any]]:
        text = (raw or "").strip()
        if not text:
            return None
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            value = json.loads(text)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    value = json.loads(text[start : end + 1])
                    return value if isinstance(value, dict) else None
                except json.JSONDecodeError:
                    return None
        return None

    def _merge_ai_slots(self, slots: dict[str, Any], ai_slots: Any) -> dict[str, Any]:
        if not isinstance(ai_slots, dict):
            return slots
        merged = dict(slots)
        for key, value in ai_slots.items():
            if not isinstance(key, str) or not _has_value(value):
                continue
            if not _has_value(merged.get(key)):
                merged[key] = value
        return merged

    def _ai_conflicts(self, ai_result: Optional[dict[str, Any]]) -> list[dict[str, str]]:
        if not ai_result or not isinstance(ai_result.get("conflicts"), list):
            return []
        conflicts = []
        for item in ai_result["conflicts"][:8]:
            if isinstance(item, dict) and item.get("message"):
                conflicts.append({"field": str(item.get("field") or ""), "message": str(item["message"])})
        return conflicts

    def _is_low_value_contract_review_question(self, question: dict[str, Any], slots: dict[str, Any]) -> bool:
        field = str(question.get("field") or "").strip().lower()
        question_text = str(question.get("question") or "")
        why_needed = str(question.get("why_needed") or "")
        combined = f"{question_text}\n{why_needed}"

        if field in CONTRACT_REVIEW_LOW_VALUE_FIELDS:
            return True
        if any(re.search(pattern, combined) for pattern in CONTRACT_REVIEW_LOW_VALUE_PATTERNS):
            return True

        has_uploaded_file_hint = any("文件名" in str(value) or ".pdf" in str(value).lower() for value in slots.values())
        if has_uploaded_file_hint and field in {"evidence", "contract_file", "document_file"} and "上传" in combined:
            return True
        return False

    def _ai_questions(
        self,
        ai_result: Optional[dict[str, Any]],
        *,
        task_type: str = "",
        slots: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        if not ai_result or not isinstance(ai_result.get("questions"), list):
            return []
        questions = []
        slots = slots or {}
        for idx, item in enumerate(ai_result["questions"][:6], start=1):
            if not isinstance(item, dict) or not item.get("field") or not item.get("question"):
                continue
            priority = str(item.get("priority") or "required")
            question = {
                "question_id": str(item.get("question_id") or f"Q{len(questions) + 1:03d}"),
                "priority": priority if priority in {"required", "optional"} else "required",
                "field": str(item["field"]),
                "question": str(item["question"]),
                "why_needed": str(item.get("why_needed") or "该信息会影响生成计划和法律风险判断。"),
                "answer_type": str(item.get("answer_type") or "text"),
                "options": item.get("options") if isinstance(item.get("options"), list) else self._options_for_field(str(item["field"])),
                "can_skip": bool(item.get("can_skip", priority != "required")),
            }
            if task_type == "contract_review" and self._is_low_value_contract_review_question(question, slots):
                continue
            questions.append(question)
        return questions

    def _ai_understanding(self, ai_result: Optional[dict[str, Any]]) -> str:
        if not ai_result:
            return ""
        understanding = str(ai_result.get("understanding") or "").strip()
        return understanding[:1800]

    def _infer_task_type(self, task_type: str, document_type: Optional[str], user_input: str) -> str:
        raw = (task_type or "").strip()
        text = f"{document_type or ''} {user_input or ''}"
        if raw and raw != "auto":
            return raw
        if "证据目录" in text:
            return "generate_evidence_catalog"
        if "起诉状" in text or "起诉" in text:
            return "generate_civil_complaint"
        if "合同" in text and ("审查" in text or "审核" in text):
            return "contract_review"
        if "导入" in text or "zip" in text.lower():
            return "case_import"
        return "generate_legal_document"

    def _extract_slots(
        self,
        *,
        user_input: str,
        document_type: Optional[str],
        case: Optional[Cases],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        text = user_input or ""
        slots: dict[str, Any] = {k: v for k, v in context.items() if _has_value(v)}
        if document_type:
            slots.setdefault("document_type", document_type)
            if "合同" in document_type:
                slots.setdefault("contract_type", document_type)
        if case:
            slots.setdefault("plaintiff", case.client_name)
            slots.setdefault("defendant", case.opposing_party)
            slots.setdefault("claims", case.claims)
            slots.setdefault("key_facts", case.summary)
            slots.setdefault("court_or_arbitration", case.court_or_arbitration or case.jurisdiction)
            slots.setdefault("amount_calculation", case.amount)
            slots.setdefault("case_type", case.case_type)
            slots.setdefault("client_role", case.role)
            slots.setdefault("evidence", "案件工作台材料" if (case.material_count or 0) > 0 else "")

        role_match = re.search(r"(甲方|乙方|出租方|承租方|买方|卖方|出借人|借款人|用人单位|劳动者)", text)
        if role_match:
            slots.setdefault("user_role", role_match.group(1))
        if re.search(r"已签|已经签|签署后|履行中|已履行", text):
            slots.setdefault("signing_status", "已签署/履行中")
        elif re.search(r"未签|签署前|准备签|待签", text):
            slots.setdefault("signing_status", "未签署")
        amount_match = re.search(r"([0-9][0-9,，.]*\s*(?:万元|元|人民币|RMB|¥))", text)
        if amount_match:
            slots.setdefault("amount_calculation", amount_match.group(1))
            slots.setdefault("transaction_background", text[:240])
        if any(word in text for word in ("付款", "解除", "违约", "知识产权", "保密", "管辖", "竞业", "担保")):
            focuses = [word for word in ("付款", "解除", "违约", "知识产权", "保密", "管辖", "竞业", "担保") if word in text]
            slots.setdefault("focus_points", "、".join(focuses))
        if len(text.strip()) > 20:
            slots.setdefault("key_facts", text.strip())
            slots.setdefault("transaction_background", text.strip()[:500])
        if re.search(r"合同|协议|聊天|转账|发票|证据|材料", text):
            slots.setdefault("evidence", "用户描述中提到材料/证据，仍需编号和来源确认")
        return slots

    def _missing_fields(self, task_type: str, slots: dict[str, Any]) -> tuple[list[str], list[str]]:
        rule = TASK_FIELD_RULES.get(task_type, TASK_FIELD_RULES["generate_legal_document"])
        missing_required = [field for field in rule["required"] if not _has_value(slots.get(field))]
        missing_optional = [field for field in rule["optional"] if not _has_value(slots.get(field))]
        return missing_required, missing_optional

    def _build_questions(self, missing_required: list[str], missing_optional: list[str]) -> list[dict[str, Any]]:
        ordered = [(field, "required") for field in missing_required] + [
            (field, "optional") for field in missing_optional
        ]
        questions: list[dict[str, Any]] = []
        for idx, (field, priority) in enumerate(ordered[:6], start=1):
            template = FIELD_QUESTIONS.get(
                field,
                {
                    "question": f"请补充 {field}。",
                    "why_needed": "该信息会影响生成计划和法律风险判断。",
                    "answer_type": "text",
                },
            )
            questions.append(
                {
                    "question_id": f"Q{idx:03d}",
                    "priority": priority,
                    "field": field,
                    "question": template["question"],
                    "why_needed": template["why_needed"],
                    "answer_type": template["answer_type"],
                    "options": self._options_for_field(field),
                    "can_skip": priority != "required",
                }
            )
        return questions

    def _options_for_field(self, field: str) -> list[str]:
        if field == "user_role":
            return ["甲方", "乙方", "出租方", "承租方", "买方", "卖方", "其他"]
        if field == "signing_status":
            return ["未签署", "已签署未履行", "履行中", "已履行/已发生争议"]
        if field == "contract_type":
            return ["买卖合同", "租赁合同", "服务合同", "借款合同", "劳动合同", "知识产权合同", "其他"]
        if field == "document_type":
            return ["起诉状", "答辩状", "律师函", "仲裁申请书", "证据目录", "案件分析报告"]
        return []

    def _detect_conflicts(self, user_input: str, slots: dict[str, Any]) -> list[dict[str, str]]:
        conflicts: list[dict[str, str]] = []
        text = user_input or ""
        if "已签" in text and "未签" in text:
            conflicts.append({"field": "signing_status", "message": "用户描述同时出现已签和未签，请确认合同签署状态。"})
        if slots.get("court_or_arbitration") and "仲裁" in str(slots.get("court_or_arbitration")) and "起诉状" in text:
            conflicts.append({"field": "court_or_arbitration", "message": "存在仲裁机构信息，生成起诉状前需确认是否有有效仲裁条款。"})
        return conflicts

    def _completeness_score(self, task_type: str, slots: dict[str, Any]) -> float:
        rule = TASK_FIELD_RULES.get(task_type, TASK_FIELD_RULES["generate_legal_document"])
        fields = rule["required"] + rule["optional"]
        if not fields:
            return 1.0
        required_hit = sum(1 for field in rule["required"] if _has_value(slots.get(field)))
        optional_hit = sum(1 for field in rule["optional"] if _has_value(slots.get(field)))
        score = (required_hit * 1.0 + optional_hit * 0.35) / (len(rule["required"]) + len(rule["optional"]) * 0.35)
        return round(max(0.0, min(1.0, score)), 2)

    def _build_assumptions(self, missing_required: list[str], task_type: str) -> list[str]:
        if not missing_required:
            return []
        return [
            f"{field} 尚未确认，若立即生成只能以【待补充：{field}】占位，不得编造。"
            for field in missing_required
        ] + [f"{task_type} 的输出为 AI 草稿，不构成正式法律意见。"]

    def _build_generation_plan(
        self,
        task_type: str,
        slots: dict[str, Any],
        missing_required: list[str],
        conflicts: list[dict[str, str]],
    ) -> dict[str, Any]:
        if task_type == "contract_review":
            structure = ["合同基础信息", "审查立场与签署状态", "重点风险", "修改建议", "履行/谈判策略", "待补事实"]
        elif task_type == "generate_evidence_catalog":
            structure = ["证据分组", "逐项证据目录", "证明目的", "对应事实/请求", "证据弱点与补强"]
        elif task_type == "generate_civil_complaint":
            structure = ["当事人信息", "诉讼请求", "事实与理由", "证据和证据来源", "此致法院", "附件和副本", "签名日期"]
        else:
            structure = ["基础信息", "核心事实", "请求/目标", "证据引用", "法律依据", "风险提示"]
        return {
            "task_type": task_type,
            "document_type": slots.get("document_type") or self._document_type_for_task(task_type),
            "position": slots.get("user_role") or slots.get("client_role") or "待确认",
            "key_facts": slots.get("key_facts") or "待补充",
            "structure": structure,
            "risk_focus": self._risk_focus(task_type, slots),
            "missing_fields": missing_required,
            "conflicts": conflicts,
            "blocking": bool(missing_required or conflicts),
            "next_action": "请先回答追问或选择按现有信息生成带假设草稿" if missing_required else "可确认计划后生成",
        }

    def _document_type_for_task(self, task_type: str) -> str:
        return {
            "generate_civil_complaint": "民事起诉状",
            "generate_evidence_catalog": "证据目录",
            "contract_review": "合同审查报告",
            "case_import": "案件导入计划",
        }.get(task_type, "法律文书")

    def _risk_focus(self, task_type: str, slots: dict[str, Any]) -> list[str]:
        if task_type == "contract_review":
            status = str(slots.get("signing_status") or "")
            if "已" in status or "履行" in status:
                return ["履行风险", "违约责任", "补救方案", "证据保全"]
            return ["签署前修改", "谈判优先级", "替代条款", "不可让步条款"]
        if task_type == "generate_civil_complaint":
            return ["主体资格", "管辖/仲裁", "诉讼时效", "请求可执行性", "证据支撑"]
        return ["事实缺口", "证据缺口", "引用准确性", "人工复核"]

    def _build_understanding(
        self,
        task_type: str,
        slots: dict[str, Any],
        missing_required: list[str],
        conflicts: list[dict[str, str]],
    ) -> str:
        base = f"系统理解：用户希望执行“{self._document_type_for_task(task_type)}”任务。"
        if slots.get("key_facts"):
            base += f" 已知事实概要：{str(slots.get('key_facts'))[:160]}"
        if missing_required:
            base += f" 当前缺少 {len(missing_required)} 个必填字段，不能生成正式版本。"
        if conflicts:
            base += f" 发现 {len(conflicts)} 项描述冲突，需要确认。"
        return base
