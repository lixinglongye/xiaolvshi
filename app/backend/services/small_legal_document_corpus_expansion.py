from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any


REQUIRED_DOMAINS = (
    "labor",
    "lease",
    "sales",
    "service",
    "lending",
    "traffic_tort",
)

CORE_TASKS = (
    "document_classification",
    "party_role_detection",
    "amount_extraction",
    "date_deadline_extraction",
    "claim_or_obligation_extraction",
    "risk_labeling",
    "evidence_gap_detection",
    "next_action_generation",
)


@dataclass(frozen=True)
class CorpusItem:
    id: str
    title: str
    domain: str
    matter_type: str
    document_type: str
    source_type: str
    language: str
    scenario: str
    synthetic_excerpt: str
    tasks: tuple[str, ...]
    expected_fields: dict[str, str]
    risk_tags: tuple[str, ...]
    difficulty: str
    local_checks: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["tasks"] = list(self.tasks)
        data["risk_tags"] = list(self.risk_tags)
        data["local_checks"] = list(self.local_checks)
        return data


class SmallLegalDocumentCorpusExpansionService:
    """Small synthetic legal-document corpus metadata for local-only fixture tests."""

    def build_corpus(self) -> dict[str, Any]:
        items = [item.to_api() for item in self._items()]
        coverage_matrix = self._coverage_matrix(items)
        return {
            "status": "ready",
            "summary": {
                "corpus_item_count": len(items),
                "domain_count": coverage_matrix["domain_count"],
                "document_type_count": coverage_matrix["document_type_count"],
                "task_count": coverage_matrix["task_count"],
                "max_excerpt_chars": max(len(item["synthetic_excerpt"]) for item in items),
                "language": "zh-CN",
                "synthetic_data_only": True,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "corpus_items": items,
            "coverage_matrix": coverage_matrix,
            "expansion_plan": self._expansion_plan(),
            "privacy_note": (
                "All corpus items are short synthetic Chinese legal-document scenarios with generic party labels. "
                "Do not add real client documents, names, contact details, identity identifiers, addresses, "
                "access secrets, or raw model outputs to this corpus."
            ),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_small_legal_document_corpus_expansion.py -q",
            ],
        }

    def _items(self) -> tuple[CorpusItem, ...]:
        shared_tasks = (
            "document_classification",
            "party_role_detection",
            "amount_extraction",
            "date_deadline_extraction",
            "claim_or_obligation_extraction",
            "risk_labeling",
            "evidence_gap_detection",
            "next_action_generation",
        )
        return (
            CorpusItem(
                id="small-corpus-labor-001",
                title="劳动解除补偿仲裁申请场景",
                domain="labor",
                matter_type="labor_compensation",
                document_type="labor_arbitration_application",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="员工甲主张公司乙单方解除劳动关系后仍欠工资和经济补偿。",
                synthetic_excerpt=(
                    "员工甲称公司乙于2026年5月10日发出解除通知，仍欠4月工资5000元，"
                    "并应支付经济补偿12000元。员工甲拟申请劳动仲裁，请求确认解除补偿、补发工资并提示证据缺口。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "employee_party": "员工甲",
                    "employer_party": "公司乙",
                    "termination_date": "2026年5月10日",
                    "claimed_amount": "17000元",
                },
                risk_tags=("termination_notice_missing", "wage_arrears", "arbitration_deadline"),
                difficulty="easy",
                local_checks=("classify_labor_matter", "extract_amounts", "flag_evidence_gap"),
            ),
            CorpusItem(
                id="small-corpus-lease-002",
                title="房屋租赁欠租催告场景",
                domain="lease",
                matter_type="lease_payment_collection",
                document_type="lease_demand_letter",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="出租人甲准备向承租人乙发送欠租和腾退风险催告。",
                synthetic_excerpt=(
                    "出租人甲与承租人乙约定每月租金4800元，承租人乙自2026年3月至4月未支付租金。"
                    "出租人甲拟催告7日内补缴9600元，并保留解除合同和追收占用费的权利。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "lessor_party": "出租人甲",
                    "lessee_party": "承租人乙",
                    "rent_arrears": "9600元",
                    "cure_period": "7日",
                },
                risk_tags=("rent_arrears", "contract_termination_notice", "possession_fee"),
                difficulty="easy",
                local_checks=("classify_lease_demand", "extract_cure_period", "detect_termination_risk"),
            ),
            CorpusItem(
                id="small-corpus-sales-003",
                title="买卖合同质量异议通知场景",
                domain="sales",
                matter_type="goods_quality_dispute",
                document_type="sales_quality_claim_notice",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="买方甲收到设备后发现质量问题，准备发出质量异议和减价请求。",
                synthetic_excerpt=(
                    "买方甲向卖方乙购买检测设备，货款总额36000元。买方甲收货后3日内发现核心部件无法启动，"
                    "拟通知卖方乙维修、更换或减价18000元，并固定验收记录和照片证据。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "buyer_party": "买方甲",
                    "seller_party": "卖方乙",
                    "contract_amount": "36000元",
                    "claimed_reduction": "18000元",
                },
                risk_tags=("quality_defect", "inspection_notice_period", "evidence_preservation"),
                difficulty="medium",
                local_checks=("classify_sales_quality", "extract_claim_amount", "flag_notice_period"),
            ),
            CorpusItem(
                id="small-corpus-service-004",
                title="服务合同交付迟延退款场景",
                domain="service",
                matter_type="service_delivery_delay",
                document_type="service_contract_claim_summary",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="委托方甲主张服务商乙未按期交付运营报告并要求退款。",
                synthetic_excerpt=(
                    "委托方甲预付服务费6000元，服务商乙承诺2026年4月30日前交付运营分析报告。"
                    "截至2026年5月15日仍未交付，委托方甲拟要求退款并确认违约责任。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "client_party": "委托方甲",
                    "service_provider": "服务商乙",
                    "prepaid_fee": "6000元",
                    "delivery_due_date": "2026年4月30日",
                },
                risk_tags=("delivery_delay", "refund_claim", "acceptance_evidence_gap"),
                difficulty="easy",
                local_checks=("classify_service_contract", "extract_due_date", "flag_refund_claim"),
            ),
            CorpusItem(
                id="small-corpus-lending-005",
                title="民间借贷还款催收场景",
                domain="lending",
                matter_type="private_lending_collection",
                document_type="private_lending_claim_summary",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="出借人甲依据借条向借款人乙催收逾期借款。",
                synthetic_excerpt=(
                    "借款人乙于2026年1月1日向出借人甲出具借条，载明借款30000元，"
                    "约定2026年4月1日前归还。到期后未还，出借人甲拟主张本金、逾期利息并补充转账凭证。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "lender_party": "出借人甲",
                    "borrower_party": "借款人乙",
                    "principal": "30000元",
                    "repayment_due_date": "2026年4月1日",
                },
                risk_tags=("overdue_repayment", "interest_term_unclear", "transfer_record_needed"),
                difficulty="medium",
                local_checks=("classify_lending", "extract_principal", "detect_interest_gap"),
            ),
            CorpusItem(
                id="small-corpus-traffic-006",
                title="交通事故侵权赔偿清单场景",
                domain="traffic_tort",
                matter_type="traffic_accident_compensation",
                document_type="traffic_tort_claim_draft",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="车主甲因轻微碰撞向责任方乙主张维修费和医疗费。",
                synthetic_excerpt=(
                    "车辆甲与车辆乙于2026年5月20日发生碰撞，交管记录显示车辆乙负主要责任。"
                    "车主甲主张维修费4200元、检查费800元，并需补充责任认定、维修清单和票据。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "claimant_party": "车主甲",
                    "liable_party": "责任方乙",
                    "accident_date": "2026年5月20日",
                    "claimed_amount": "5000元",
                },
                risk_tags=("liability_ratio", "medical_invoice_needed", "repair_invoice_needed"),
                difficulty="medium",
                local_checks=("classify_traffic_tort", "extract_damage_items", "flag_invoice_gap"),
            ),
            CorpusItem(
                id="small-corpus-tort-007",
                title="邻里漏水财产损害调解场景",
                domain="property_tort",
                matter_type="property_damage_mediation",
                document_type="property_damage_mediation_record",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="住户甲因楼上漏水导致室内损坏，准备调解记录和修复费用清单。",
                synthetic_excerpt=(
                    "住户甲称楼上住户乙房屋漏水，造成墙面和柜体受损。维修报价3500元，"
                    "双方拟调解确认修复期限、费用承担和再次漏水的处理方式。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "injured_party": "住户甲",
                    "responsible_party": "住户乙",
                    "repair_cost": "3500元",
                    "damage_type": "墙面和柜体受损",
                },
                risk_tags=("causation_proof", "repair_quote_needed", "future_damage_clause"),
                difficulty="medium",
                local_checks=("classify_property_tort", "extract_repair_cost", "detect_causation_gap"),
            ),
            CorpusItem(
                id="small-corpus-consumer-008",
                title="培训服务退费沟通场景",
                domain="consumer_service",
                matter_type="training_service_refund",
                document_type="consumer_refund_notice",
                source_type="synthetic_scenario_metadata",
                language="zh-CN",
                scenario="消费者甲因培训机构乙未按承诺排课，准备退费沟通材料。",
                synthetic_excerpt=(
                    "消费者甲向培训机构乙支付课程费8800元，机构乙承诺2026年6月前安排20次课程。"
                    "实际仅安排6次，消费者甲拟要求退还未履行课程对应费用并保留沟通记录。"
                ),
                tasks=shared_tasks,
                expected_fields={
                    "consumer_party": "消费者甲",
                    "provider_party": "培训机构乙",
                    "course_fee": "8800元",
                    "promised_sessions": "20次",
                },
                risk_tags=("service_quantity_shortfall", "refund_calculation_needed", "chat_record_needed"),
                difficulty="easy",
                local_checks=("classify_consumer_service", "extract_service_quantity", "flag_refund_calculation"),
            ),
        )

    def _coverage_matrix(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        domain_rows = self._bucket_scalar(items, "domain")
        document_type_rows = self._bucket_scalar(items, "document_type")
        task_rows = self._bucket_list(items, "tasks")
        risk_rows = self._bucket_list(items, "risk_tags")
        covered_domains = {row["id"] for row in domain_rows}
        return {
            "required_domains": list(REQUIRED_DOMAINS),
            "covered_required_domains": sorted(domain for domain in REQUIRED_DOMAINS if domain in covered_domains),
            "missing_required_domains": sorted(domain for domain in REQUIRED_DOMAINS if domain not in covered_domains),
            "domain_count": len(domain_rows),
            "document_type_count": len(document_type_rows),
            "task_count": len(task_rows),
            "risk_tag_count": len(risk_rows),
            "domains": domain_rows,
            "document_types": document_type_rows,
            "tasks": task_rows,
            "risk_tags": risk_rows,
        }

    def _bucket_scalar(self, items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
        buckets: dict[str, list[str]] = defaultdict(list)
        for item in items:
            buckets[str(item[field])].append(item["id"])
        return self._bucket_rows(buckets)

    def _bucket_list(self, items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
        buckets: dict[str, list[str]] = defaultdict(list)
        for item in items:
            for value in item[field]:
                buckets[str(value)].append(item["id"])
        return self._bucket_rows(buckets)

    def _bucket_rows(self, buckets: dict[str, list[str]]) -> list[dict[str, Any]]:
        return [
            {"id": key, "item_count": len(item_ids), "item_ids": sorted(item_ids)}
            for key, item_ids in sorted(buckets.items())
        ]

    def _expansion_plan(self) -> dict[str, Any]:
        return {
            "plan_id": "small-legal-document-corpus-expansion",
            "model_call_policy": "never_call_external_models",
            "network_access": "disabled",
            "resource_profile": {
                "max_items": 8,
                "max_excerpt_chars": 220,
                "parallelism": 1,
                "storage": "in-memory dictionaries only",
                "expected_runtime": "under 1 second on a low-resource laptop",
            },
            "acceptance_criteria": [
                "Keep 6-8 short synthetic Chinese legal-document scenarios.",
                "Cover labor, lease, sales, service, lending, and traffic or tort matters.",
                "Expose deterministic task, risk, and field metadata without external model calls.",
                "Reject real personal details, client documents, contact details, identity identifiers, and access secrets.",
            ],
            "next_expansion_batches": [
                {
                    "id": "procedure-documents",
                    "scope": "Add small synthetic filing, evidence list, and delivery receipt scenarios.",
                    "target_count": 4,
                },
                {
                    "id": "risk-edge-cases",
                    "scope": "Add ambiguous deadlines, unclear party roles, and missing evidence variants.",
                    "target_count": 4,
                },
            ],
            "validation_steps": [
                "Run the pytest command listed in validation_commands.",
                "Check coverage_matrix.missing_required_domains is empty.",
                "Scan the returned payload for contact details, identity identifiers, and access secret patterns.",
            ],
        }
