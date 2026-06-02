from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RequiredField:
    name: str
    keywords: tuple[str, ...]
    reason: str
    impact: str


@dataclass(frozen=True)
class DocumentReviewStrategy:
    strategy_id: str
    display_name: str
    aliases: tuple[str, ...]
    matter_type: str
    required_fields: tuple[RequiredField, ...]
    review_dimensions: tuple[str, ...]
    special_risk_rules: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    missing_clause_rules: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    evidence_checklist: tuple[str, ...] = field(default_factory=tuple)
    authority_queries: tuple[str, ...] = field(default_factory=tuple)
    report_focus: tuple[str, ...] = field(default_factory=tuple)
    lawyer_review_triggers: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_fields"] = [asdict(item) for item in self.required_fields]
        return data

    def to_report_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "display_name": self.display_name,
            "matter_type": self.matter_type,
            "required_fields": [item.name for item in self.required_fields],
            "review_dimensions": list(self.review_dimensions),
            "evidence_checklist": list(self.evidence_checklist),
            "authority_queries": list(self.authority_queries),
            "report_focus": list(self.report_focus),
            "lawyer_review_triggers": list(self.lawyer_review_triggers),
        }


def _field(name: str, keywords: tuple[str, ...], reason: str, impact: str) -> RequiredField:
    return RequiredField(name=name, keywords=keywords, reason=reason, impact=impact)


def _risk(
    *,
    rule_id: str,
    title: str,
    risk_level: str,
    risk_type: str,
    keywords: tuple[str, ...],
    applicable_rule: str,
    user_impact: str,
    authority_queries: tuple[str, ...] = (),
    evidence_suggestion: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "title": title,
        "risk_level": risk_level,
        "risk_type": risk_type,
        "keywords": keywords,
        "applicable_rule": applicable_rule,
        "user_impact": user_impact,
        "authority_queries": authority_queries,
        "evidence_suggestion": evidence_suggestion,
    }


def _missing(
    *,
    name: str,
    keywords: tuple[str, ...],
    risk: str,
    recommended_clause: str,
    authority_queries: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "name": name,
        "keywords": keywords,
        "risk": risk,
        "recommended_clause": recommended_clause,
        "authority_queries": authority_queries,
    }


GENERAL_CONTRACT = DocumentReviewStrategy(
    strategy_id="general_contract",
    display_name="通用合同/协议审查",
    aliases=("合同", "协议", "补充协议", "框架协议"),
    matter_type="合同审查",
    required_fields=(
        _field("当事人信息", ("甲方", "乙方", "当事人", "统一社会信用代码", "身份证"), "确认主体资格和签约能力。", "主体不明会影响合同效力、履行和送达。"),
        _field("标的/服务范围", ("标的", "服务内容", "项目范围", "工作内容"), "确认交易对象和履约边界。", "范围不清会导致价款、验收和违约争议。"),
        _field("价款/付款", ("价款", "费用", "报酬", "租金", "付款", "支付"), "确认付款条件、节点和发票税费。", "付款条件不明会影响回款、拒付和违约判断。"),
        _field("违约责任", ("违约", "赔偿", "违约金", "逾期"), "确认违约构成、责任形式和损失范围。", "违约责任缺失会降低追责确定性。"),
        _field("争议解决", ("争议解决", "管辖", "法院", "仲裁"), "确认发生争议后的程序路径。", "约定不明会增加管辖或仲裁协议效力争议。"),
    ),
    review_dimensions=("主体", "标的", "价款", "履行", "验收", "违约", "解除", "通知", "保密", "知识产权", "争议解决", "签章"),
    evidence_checklist=("签署版合同及附件", "主体资质材料", "磋商记录", "付款/开票记录", "交付/验收记录", "通知送达凭证"),
    authority_queries=("合同主要条款", "合同履行诚信原则", "违约责任", "违约金调整", "争议解决"),
    report_focus=("逐条定位原文风险", "区分法律风险和商业风险", "给出可复制修改条款", "列明待补事实和证据建议"),
    lawyer_review_triggers=("重大金额", "格式条款争议", "跨境/涉外", "强监管行业", "诉讼仲裁用途"),
)


LEASE_CONTRACT = DocumentReviewStrategy(
    strategy_id="lease_contract",
    display_name="房屋/场地租赁合同审查",
    aliases=("租赁", "房屋租赁", "场地租赁", "出租", "承租", "租金", "押金", "物业"),
    matter_type="租赁合同",
    required_fields=(
        _field("租赁物信息", ("房屋", "场地", "地址", "面积", "产权", "租赁物"), "确认租赁物权属、用途和可使用状态。", "租赁物信息不清会影响交付、使用和解除。"),
        _field("租期和续租", ("租赁期限", "租期", "续租", "到期"), "确认租期、起算、届满和续租安排。", "期限不明可能形成不定期租赁或续租争议。"),
        _field("租金/押金", ("租金", "押金", "保证金", "支付"), "确认租金、押金扣除和返还机制。", "押金扣除不清会造成退租结算争议。"),
        _field("维修/修缮", ("维修", "修缮", "损坏", "报修"), "区分自然损耗和承租人过错。", "维修责任不清会影响使用权益和费用承担。"),
        _field("解除/退租", ("解除", "退租", "提前终止", "交还"), "确认退出机制和费用结算。", "缺少退出机制会导致违约金和押金争议。"),
    ),
    review_dimensions=("权属/出租资格", "用途限制", "交付条件", "租金押金", "维修责任", "转租", "装修恢复", "提前解除", "续租", "买卖不破租赁", "物业税费"),
    special_risk_rules=(
        _risk(
            rule_id="lease_deposit_return",
            title="押金扣除和返还机制不明确",
            risk_level="高",
            risk_type="履约风险",
            keywords=("押金", "保证金", "扣除", "返还", "不予退还"),
            applicable_rule="应审查押金扣除范围、举证责任、返还期限和扣款证明。",
            user_impact="押金条款不清会导致退租时被扩大扣款或难以及时返还。",
            authority_queries=("租赁 押金 返还", "租赁合同 维修 返还"),
            evidence_suggestion=("交房/退房验收单", "押金支付凭证", "房屋现状照片/视频", "扣款明细和维修票据"),
        ),
        _risk(
            rule_id="lease_repair_obligation",
            title="维修修缮责任可能向承租方过度转移",
            risk_level="中",
            risk_type="法律风险",
            keywords=("维修", "修缮", "自然损耗", "设备老化", "乙方负责"),
            applicable_rule="应区分租赁物自然损耗、主体结构、附属设施和承租人过错造成的损坏。",
            user_impact="维修责任过宽会增加承租方不可控费用，影响正常使用。",
            authority_queries=("租赁 维修 修缮", "出租人维修义务"),
            evidence_suggestion=("报修记录", "维修报价/发票", "设备交接清单", "现场照片"),
        ),
    ),
    missing_clause_rules=(
        _missing(name="押金返还", keywords=("押金返还", "保证金返还", "退还押金"), risk="缺少押金返还期限和扣款证明规则。", recommended_clause="建议明确押金返还期限、可扣款范围、扣款证明和逾期返还责任。", authority_queries=("租赁 押金返还",)),
        _missing(name="维修修缮", keywords=("维修", "修缮", "报修"), risk="缺少维修机制会影响承租方使用权益和费用承担。", recommended_clause="建议明确自然损耗、主体结构、设备老化由出租方负责，承租方过错损坏由承租方负责。", authority_queries=("租赁 维修义务",)),
    ),
    evidence_checklist=("权属证明/授权出租文件", "房屋交接清单", "租金押金支付凭证", "维修报修记录", "退租验收记录", "通知送达凭证"),
    authority_queries=("租赁合同", "出租人维修义务", "承租人解除合同", "不定期租赁", "买卖不破租赁"),
    report_focus=("优先审查押金、维修、退租、续租和用途限制", "说明承租/出租不同角色的谈判底线", "给出退租和维修证据清单"),
    lawyer_review_triggers=("长期租赁", "高额装修投入", "商业经营场地", "权属不清", "提前解除争议"),
)


LABOR_CONTRACT = DocumentReviewStrategy(
    strategy_id="labor_contract",
    display_name="劳动合同/用工协议审查",
    aliases=("劳动合同", "用工", "员工", "劳动者", "用人单位", "试用期", "竞业限制", "社保", "工资"),
    matter_type="劳动用工",
    required_fields=(
        _field("合同期限", ("合同期限", "固定期限", "无固定期限", "试用期"), "确认劳动合同期限和试用期匹配。", "试用期超过法定上限会产生工资补差等风险。"),
        _field("工作内容和地点", ("工作内容", "工作岗位", "工作地点", "岗位"), "确认岗位、地点和调岗边界。", "约定过宽会引发调岗、降薪或解除争议。"),
        _field("劳动报酬", ("工资", "劳动报酬", "薪资", "奖金", "绩效"), "确认工资结构和支付时间。", "报酬不清会引发拖欠工资和补偿金争议。"),
        _field("社保和工时", ("社会保险", "社保", "工作时间", "休息休假", "加班"), "确认强制性劳动保护事项。", "缺失强制条款会带来行政和仲裁风险。"),
    ),
    review_dimensions=("劳动合同必备条款", "试用期", "工资结构", "工时休假", "社保公积金", "调岗调薪", "解除终止", "竞业限制", "保密", "培训服务期"),
    special_risk_rules=(
        _risk(rule_id="labor_probation", title="试用期约定需与合同期限匹配", risk_level="高", risk_type="合规风险", keywords=("试用期", "转正", "试用工资"), applicable_rule="应核验试用期期限、试用工资、同一用人单位仅约定一次试用期等要求。", user_impact="试用期约定违法可能导致工资补差、违法解除或仲裁风险。", authority_queries=("劳动合同 试用期",), evidence_suggestion=("劳动合同期限", "工资发放记录", "入职记录")),
        _risk(rule_id="labor_non_compete", title="竞业限制范围、期限和补偿需严格核验", risk_level="高", risk_type="合规风险", keywords=("竞业限制", "竞业", "经济补偿", "离职后", "不得从事"), applicable_rule="应核验适用人员、期限不超过二年、地域/行业范围、经济补偿和违约金。", user_impact="竞业限制过宽或无补偿可能被限缩或不被支持，同时影响离职安排。", authority_queries=("劳动合同 竞业限制 经济补偿",), evidence_suggestion=("岗位职责", "保密信息接触证明", "补偿支付记录", "离职文件")),
    ),
    missing_clause_rules=(
        _missing(name="劳动合同必备条款", keywords=("劳动报酬", "社会保险", "工作内容", "工作地点"), risk="缺少劳动合同必备条款会增加劳动仲裁和行政合规风险。", recommended_clause="建议补充合同期限、工作内容地点、工作时间休假、劳动报酬、社会保险、劳动保护等条款。", authority_queries=("劳动合同 必备条款",)),
    ),
    evidence_checklist=("入职登记材料", "劳动合同签收记录", "工资流水", "社保缴纳记录", "考勤/加班记录", "岗位职责和调岗通知", "离职/解除通知"),
    authority_queries=("劳动合同必备条款", "试用期", "竞业限制", "劳动报酬"),
    report_focus=("强制性规则优先", "不把违法用工风险包装成商业风险", "列明仲裁证据和举证责任"),
    lawyer_review_triggers=("解除/裁员", "竞业限制", "高管/核心技术人员", "拖欠工资", "工伤/病假/三期员工"),
)


SALES_CONTRACT = DocumentReviewStrategy(
    strategy_id="sales_contract",
    display_name="买卖/采购/销售合同审查",
    aliases=("买卖", "采购", "销售", "供货", "订单", "货物", "标的物", "检验"),
    matter_type="买卖合同",
    required_fields=(
        _field("标的物规格", ("标的物", "产品", "规格", "型号", "数量"), "确认货物范围、规格、数量和包装。", "标的不清会导致交付和质量争议。"),
        _field("价款和付款", ("价款", "货款", "付款", "结算", "发票"), "确认付款节点、发票税费和逾期责任。", "付款条件不清影响回款和拒付抗辩。"),
        _field("交付和风险转移", ("交付", "运输", "签收", "风险转移", "物流"), "确认交付地点、运输责任和风险转移。", "风险转移不明会影响货损责任。"),
        _field("验收和质量异议", ("验收", "检验", "质量", "异议", "质保"), "确认验收标准、期限和异议流程。", "验收机制不清会削弱质量索赔。"),
    ),
    review_dimensions=("标的规格", "数量包装", "价款发票", "交付地点", "运输保险", "风险转移", "验收期限", "质量保证", "违约责任", "所有权保留"),
    special_risk_rules=(
        _risk(rule_id="sales_acceptance", title="验收标准和质量异议期限不明确", risk_level="高", risk_type="履约风险", keywords=("验收", "检验", "质量异议", "视为合格", "质保"), applicable_rule="应核验验收标准、检验期限、异议通知、视为验收条件和质保责任。", user_impact="买方可能丧失质量异议空间，卖方也可能面临长期不确定索赔。", authority_queries=("买卖 验收 检验 质量异议",), evidence_suggestion=("验收单", "检测报告", "质量异议通知", "物流签收记录")),
        _risk(rule_id="sales_risk_transfer", title="交付和风险转移节点需明确", risk_level="中", risk_type="法律风险", keywords=("交付", "风险转移", "运输", "签收", "货损", "灭失"), applicable_rule="应核验交付地点、承运人、签收标准、运输保险和货损责任。", user_impact="风险转移不清会导致运输途中损毁灭失责任争议。", authority_queries=("买卖 交付 风险转移",), evidence_suggestion=("物流单据", "签收凭证", "保险单", "破损照片")),
    ),
    missing_clause_rules=(
        _missing(name="验收和质量异议", keywords=("验收", "检验", "质量异议"), risk="缺少验收和质量异议机制会导致质量争议难以证明。", recommended_clause="建议明确验收标准、期限、异议通知方式、复检机制和质保责任。", authority_queries=("买卖 验收 检验",)),
    ),
    evidence_checklist=("订单/报价单", "规格书", "物流签收单", "验收单", "检测报告", "付款和发票记录", "质量异议通知"),
    authority_queries=("买卖合同内容", "买卖验收检验", "买卖风险转移"),
    report_focus=("围绕交付、验收、质量和付款闭环审查", "明确买方和卖方的不同谈判底线"),
    lawyer_review_triggers=("大额设备采购", "定制产品", "跨境贸易", "质量争议", "长期供货框架"),
)


SERVICE_CONTRACT = DocumentReviewStrategy(
    strategy_id="service_contract",
    display_name="服务/委托/技术服务合同审查",
    aliases=("服务合同", "委托服务", "技术服务", "咨询", "运维", "SLA", "服务费", "成果交付"),
    matter_type="服务合同",
    required_fields=(
        _field("服务范围", ("服务内容", "服务范围", "工作范围", "项目范围"), "确认服务边界和不包含事项。", "范围不清会导致免费增项和验收争议。"),
        _field("服务标准/SLA", ("服务标准", "SLA", "响应时间", "质量标准", "验收"), "确认履约标准和验收口径。", "服务质量难以评价会影响付款和违约认定。"),
        _field("成果和知识产权", ("成果", "交付物", "知识产权", "著作权", "源代码"), "确认成果权属和使用授权。", "权属不清会影响后续商业使用。"),
        _field("费用和变更", ("服务费", "费用", "变更", "增项", "结算"), "确认费用、变更流程和额外工作计费。", "变更流程缺失会导致结算争议。"),
    ),
    review_dimensions=("服务范围", "里程碑", "SLA", "验收标准", "人员投入", "变更管理", "成果权属", "保密数据", "违约责任", "退出交接"),
    special_risk_rules=(
        _risk(rule_id="service_scope_creep", title="服务范围和变更机制不足", risk_level="高", risk_type="商业风险", keywords=("服务范围", "工作范围", "变更", "增项", "另行协商"), applicable_rule="应核验服务边界、排除事项、变更审批和增项计费机制。", user_impact="服务方可能被无限增项，委托方也可能无法证明交付不足。", authority_queries=("服务合同 履行 验收",), evidence_suggestion=("需求说明书", "变更单", "会议纪要", "里程碑验收记录")),
        _risk(rule_id="service_ip", title="成果知识产权和使用授权需明确", risk_level="中", risk_type="法律风险", keywords=("知识产权", "著作权", "成果", "源代码", "授权", "交付物"), applicable_rule="应核验成果归属、第三方组件、使用范围、源文件交付和侵权担保。", user_impact="成果权属不清会影响后续使用、转让、融资或商业化。", authority_queries=("服务合同 成果 知识产权",), evidence_suggestion=("成果交付清单", "源文件", "第三方组件清单", "授权证明")),
    ),
    missing_clause_rules=(
        _missing(name="验收/SLA", keywords=("验收", "SLA", "服务标准", "响应时间"), risk="缺少服务标准和验收机制会导致付款与违约认定困难。", recommended_clause="建议明确服务指标、响应时限、验收流程、整改期和未达标责任。", authority_queries=("服务合同 验收 服务标准",)),
    ),
    evidence_checklist=("需求说明书", "项目计划", "交付物清单", "验收记录", "变更单", "服务工单", "会议纪要", "付款发票"),
    authority_queries=("服务合同 履行 验收", "知识产权 成果归属"),
    report_focus=("重点审查服务边界、验收、变更和成果权属", "给出变更和验收证据建议"),
    lawyer_review_triggers=("技术开发/软件交付", "含个人信息处理", "成果权属重要", "长期运维外包", "高额服务费"),
)


LOAN_CONTRACT = DocumentReviewStrategy(
    strategy_id="loan_contract",
    display_name="借款/民间借贷合同审查",
    aliases=("借款合同", "借款", "借贷", "民间借贷", "借条", "欠条", "贷款", "出借", "还款", "利息", "利率", "本金", "借款人", "出借人"),
    matter_type="借款合同",
    required_fields=(
        _field("借款本金", ("借款金额", "本金", "出借", "借款"), "确认实际出借金额和交付方式。", "本金和交付不清会影响债权成立和金额认定。"),
        _field("利息和费用", ("利息", "利率", "服务费", "管理费", "手续费"), "确认综合资金成本是否合规。", "利息费用安排不清会影响可支持金额。"),
        _field("还款期限和方式", ("还款", "到期", "分期", "提前到期"), "确认到期日、分期和提前到期条件。", "期限不清影响催收和诉讼时点。"),
        _field("担保措施", ("保证", "担保", "抵押", "质押", "连带"), "确认增信措施和实现路径。", "担保不清会降低债权回收保障。"),
    ),
    review_dimensions=("本金交付", "利率费用", "还款顺序", "提前到期", "担保", "保证期间", "抵押登记", "催收通知", "证据链", "夫妻共同债务"),
    special_risk_rules=(
        _risk(rule_id="loan_interest", title="利率、服务费或综合资金成本需核验", risk_level="高", risk_type="法律风险", keywords=("利息", "利率", "服务费", "管理费", "手续费", "砍头息"), applicable_rule="应核验约定利率、费用名目、预扣本金和逾期利息是否存在不被支持风险。", user_impact="超过可支持范围的利息或费用可能无法通过诉讼主张。", authority_queries=("借款 利息 利率", "民间借贷 利率上限"), evidence_suggestion=("转账凭证", "收据", "还款流水", "利息计算表")),
        _risk(rule_id="loan_guarantee", title="担保和保证期间约定需明确", risk_level="高", risk_type="法律风险", keywords=("保证", "担保", "连带", "保证期间", "抵押", "质押"), applicable_rule="应核验保证方式、保证范围、保证期间、担保物信息和登记手续。", user_impact="担保约定不明可能导致保证责任范围缩小或担保物权无法实现。", authority_queries=("保证方式 约定不明", "担保 保证期间"), evidence_suggestion=("保证合同", "抵押登记", "担保人身份材料", "催收通知")),
    ),
    missing_clause_rules=(
        _missing(name="借款交付凭证", keywords=("转账", "交付", "收款", "到账"), risk="缺少交付凭证安排会影响借款事实证明。", recommended_clause="建议明确以银行转账为交付方式，并保存收款确认和用途说明。", authority_queries=("借款合同 交付 凭证",)),
        _missing(name="提前到期", keywords=("提前到期", "加速到期", "立即到期"), risk="缺少提前到期条款会影响违约后快速处置。", recommended_clause="建议约定逾期、资信恶化、担保失效等情形下债权人可宣布全部债务提前到期。", authority_queries=("借款 提前到期",)),
    ),
    evidence_checklist=("借款合同", "银行转账凭证", "收据/收款确认", "还款流水", "利息计算表", "催收通知", "担保登记资料"),
    authority_queries=("借款合同", "借款利息", "保证责任", "担保"),
    report_focus=("优先核验本金交付和利息可支持性", "列明诉讼证据链", "区分本金、利息、费用、违约金"),
    lawyer_review_triggers=("高利率/费用", "自然人民间借贷", "夫妻共同债务", "抵押质押", "拟起诉催收"),
)


GUARANTEE_CONTRACT = DocumentReviewStrategy(
    strategy_id="guarantee_contract",
    display_name="担保/保证/抵押质押合同审查",
    aliases=("担保", "保证", "抵押", "质押", "连带责任", "保证期间", "债权人", "保证人"),
    matter_type="担保合同",
    required_fields=(
        _field("主债权", ("主合同", "主债权", "债务人", "债权人"), "确认担保从属性和主债权范围。", "主债权不清会影响担保责任认定。"),
        _field("担保方式", ("一般保证", "连带责任", "抵押", "质押", "保证方式"), "确认保证方式或担保物权类型。", "保证方式不清可能按一般保证处理。"),
        _field("担保范围", ("本金", "利息", "违约金", "实现债权费用", "担保范围"), "确认担保覆盖的债权项目。", "范围不清会影响追偿金额。"),
        _field("保证期间/登记", ("保证期间", "登记", "抵押登记", "质押登记"), "确认时效和公示手续。", "期间或登记缺失会导致担保落空。"),
    ),
    review_dimensions=("主债权", "担保方式", "担保范围", "保证期间", "最高额担保", "抵押质押登记", "公司担保决议", "夫妻/共同财产", "追偿权"),
    special_risk_rules=(
        _risk(rule_id="guarantee_type", title="保证方式约定不明风险", risk_level="高", risk_type="法律风险", keywords=("一般保证", "连带责任", "保证方式", "未约定"), applicable_rule="应核验保证方式是否明确，避免约定不明导致责任形态不符合预期。", user_impact="债权人可能无法直接要求保证人承担连带责任，保证人可能承担超预期责任。", authority_queries=("保证方式 约定不明",), evidence_suggestion=("主合同", "保证合同", "担保人签章页")),
        _risk(rule_id="guarantee_period", title="保证期间或担保登记安排不足", risk_level="高", risk_type="法律风险", keywords=("保证期间", "抵押登记", "质押登记", "登记", "最高额"), applicable_rule="应核验保证期间起算、届满、催告方式以及抵押质押登记手续。", user_impact="未及时主张或未登记可能导致担保权利无法实现。", authority_queries=("保证期间", "抵押登记 质押登记"), evidence_suggestion=("登记证明", "催收通知", "送达凭证")),
    ),
    evidence_checklist=("主合同", "担保合同", "担保人身份/授权", "公司决议", "抵押/质押登记证明", "催收通知", "送达凭证"),
    authority_queries=("保证合同", "保证方式", "担保范围", "保证期间"),
    report_focus=("必须区分一般保证、连带责任保证和物的担保", "列明实现担保权的程序风险"),
    lawyer_review_triggers=("公司对外担保", "最高额担保", "不动产/股权质押", "保证期间临近", "拟诉讼执行"),
)


EQUITY_TRANSFER = DocumentReviewStrategy(
    strategy_id="equity_transfer",
    display_name="股权转让/投资退出协议审查",
    aliases=("股权转让", "股权", "股份", "出资", "工商变更", "目标公司", "回购", "对赌", "估值"),
    matter_type="股权交易",
    required_fields=(
        _field("目标公司和股权", ("目标公司", "股权", "出资额", "持股比例", "注册资本"), "确认交易标的和权属状态。", "股权权属不清会影响交割和变更登记。"),
        _field("转让价款", ("转让价款", "估值", "付款", "对价"), "确认价格、付款条件和调整机制。", "价款条件不清会引发交割和违约争议。"),
        _field("陈述保证", ("陈述", "保证", "债务", "或有负债", "税务"), "确认历史债务、出资瑕疵和合规风险。", "缺少陈述保证会让受让方承担隐性负债。"),
        _field("交割和工商变更", ("交割", "工商变更", "股东名册", "章程", "登记"), "确认交割条件和变更义务。", "变更不完成会影响股东权利实现。"),
    ),
    review_dimensions=("股权权属", "出资实缴", "优先购买权", "配偶/共有人同意", "价款调整", "陈述保证", "税费", "交割条件", "工商变更", "回购/对赌", "竞业和保密"),
    special_risk_rules=(
        _risk(rule_id="equity_hidden_liabilities", title="历史债务、出资瑕疵和或有负债披露不足", risk_level="重大", risk_type="法律风险", keywords=("或有负债", "债务", "税务", "行政处罚", "诉讼", "出资", "实缴"), applicable_rule="应核验目标公司债务、税务、诉讼、出资实缴、担保和重大合同披露。", user_impact="受让方可能在交割后承担未披露债务或公司治理风险。", authority_queries=("股权转让 尽职调查 陈述保证",), evidence_suggestion=("审计报告", "财务报表", "债务清单", "诉讼查询", "出资证明")),
        _risk(rule_id="equity_registration", title="工商变更和股东权利交割机制不清", risk_level="高", risk_type="履约风险", keywords=("工商变更", "股东名册", "章程", "交割", "登记"), applicable_rule="应核验股东名册、章程修改、工商变更、付款和资料交付的先后顺序。", user_impact="受让方付款后可能无法及时取得股东权利，转让方也可能面临价款回收风险。", authority_queries=("股权转让 工商变更 股东名册",), evidence_suggestion=("股东会决议", "章程修正案", "工商变更材料", "付款凭证")),
    ),
    missing_clause_rules=(
        _missing(name="陈述保证和赔偿", keywords=("陈述", "保证", "赔偿", "或有负债"), risk="缺少陈述保证会使隐性债务和出资瑕疵难以追责。", recommended_clause="建议补充目标公司财务、税务、诉讼、出资、资产权属、重大合同和员工事项的陈述保证及赔偿机制。", authority_queries=("股权转让 陈述保证",)),
        _missing(name="交割条件", keywords=("交割条件", "先决条件", "工商变更"), risk="缺少交割条件会导致付款、资料交付和工商变更顺序不清。", recommended_clause="建议明确先决条件、付款托管/分期、股东名册变更、章程修订和工商登记完成标准。", authority_queries=("股权转让 交割 工商变更",)),
    ),
    evidence_checklist=("公司章程", "股东名册", "出资证明", "股东会决议", "财务报表/审计报告", "债务和担保清单", "诉讼/执行查询", "工商变更材料"),
    authority_queries=("股权转让", "股东名册", "工商变更", "公司担保", "出资瑕疵"),
    report_focus=("强制加入尽调和交割清单", "突出隐性负债、出资瑕疵和变更登记风险", "不把投资判断写成法律结论"),
    lawyer_review_triggers=("股权交易", "对赌/回购", "目标公司有债务", "未实缴出资", "控制权变更", "涉税金额大"),
)


LITIGATION_COMPLAINT = DocumentReviewStrategy(
    strategy_id="lawsuit_complaint",
    display_name="起诉状/仲裁申请前审查",
    aliases=("起诉状", "民事起诉状", "起诉书", "诉讼请求", "原告", "被告", "立案"),
    matter_type="诉讼文书",
    required_fields=(
        _field("当事人信息", ("原告", "被告", "住所", "统一社会信用代码", "身份证号"), "确认主体和送达信息。", "主体或地址错误会影响立案、送达和判决执行。"),
        _field("诉讼请求", ("诉讼请求", "请求判令", "请求事项"), "确认请求明确、可执行和金额计算。", "请求不明确可能导致驳回、补正或执行困难。"),
        _field("事实与理由", ("事实与理由", "事实", "理由", "经过"), "确认请求基础事实和法律关系。", "事实链不足会影响胜诉可能和举证。"),
        _field("证据目录", ("证据", "证据目录", "证明目的"), "确认每项请求有证据支撑。", "证据不足会导致败诉或请求金额被削减。"),
    ),
    review_dimensions=("管辖", "主体适格", "诉讼请求", "请求权基础", "金额计算", "事实链", "证据目录", "时效", "保全", "送达地址", "律师复核"),
    special_risk_rules=(
        _risk(rule_id="claim_not_enforceable", title="诉讼请求可能不明确或不可执行", risk_level="重大", risk_type="诉讼风险", keywords=("诉讼请求", "请求判令", "赔偿", "支付", "确认"), applicable_rule="应核验请求事项是否具体、金额是否可计算、履行内容是否可执行。", user_impact="请求不清会导致补正、部分驳回或执行困难。", authority_queries=("起诉状 诉讼请求 证据目录",), evidence_suggestion=("金额计算表", "合同和履行凭证", "损失证明")),
        _risk(rule_id="limitation_evidence", title="时效和证据链需单独核验", risk_level="高", risk_type="诉讼风险", keywords=("时效", "催告", "证据", "证明", "聊天记录", "付款"), applicable_rule="应核验诉讼时效、中断事由和每项诉请对应证据。", user_impact="时效或证据不足会直接影响胜诉和可支持金额。", authority_queries=("诉讼时效 证据 举证责任",), evidence_suggestion=("催告记录", "送达凭证", "付款流水", "聊天记录原始载体")),
    ),
    missing_clause_rules=(
        _missing(name="证据目录/证明目的", keywords=("证据目录", "证明目的"), risk="缺少证据目录会导致请求、事实和证据无法对应。", recommended_clause="建议按每项诉讼请求列明证据名称、来源、页码和证明目的。", authority_queries=("起诉状 证据目录",)),
    ),
    evidence_checklist=("主体身份材料", "合同/订单", "履行凭证", "付款流水", "催告和送达记录", "损失计算表", "证据目录", "管辖依据"),
    authority_queries=("起诉状", "诉讼请求", "证据目录", "诉讼时效"),
    report_focus=("按诉讼要件审查，不只做合同风险", "每项诉请必须对应事实、依据、证据和金额计算", "强制提示执业律师复核"),
    lawyer_review_triggers=("所有起诉状/仲裁申请", "保全", "时效临近", "金额重大", "主体复杂", "证据电子化"),
)


DEFENSE_STATEMENT = DocumentReviewStrategy(
    strategy_id="defense_statement",
    display_name="答辩状/抗辩意见审查",
    aliases=("答辩状", "答辩意见", "被告", "抗辩", "反诉", "管辖异议"),
    matter_type="诉讼文书",
    required_fields=(
        _field("对方请求", ("诉讼请求", "请求事项", "原告请求"), "确认答辩对象。", "未逐项回应会导致抗辩遗漏。"),
        _field("抗辩理由", ("答辩", "抗辩", "不同意", "不认可"), "确认事实抗辩和法律抗辩。", "抗辩理由空泛会削弱庭审效果。"),
        _field("证据和反证", ("证据", "反证", "证明"), "确认每项抗辩有证据支撑。", "缺少反证会影响抗辩成立。"),
    ),
    review_dimensions=("逐项回应", "管辖异议", "时效抗辩", "履行抗辩", "金额抗辩", "证据反驳", "反诉/抵销", "举证期限"),
    special_risk_rules=(
        _risk(rule_id="defense_missing_response", title="答辩未逐项回应对方诉请", risk_level="高", risk_type="诉讼风险", keywords=("不同意", "不认可", "请求", "事实与理由", "答辩"), applicable_rule="应对每项诉讼请求分别作出承认、否认或部分认可，并列明事实和证据。", user_impact="未回应的事实和请求可能在庭审中处于不利位置。", authority_queries=("答辩状 抗辩 证据",), evidence_suggestion=("对方起诉状", "证据交换材料", "反证清单")),
    ),
    evidence_checklist=("起诉状副本", "对方证据", "反证材料", "履行记录", "付款流水", "聊天/邮件记录", "管辖和时效材料"),
    authority_queries=("答辩状", "抗辩", "举证责任"),
    report_focus=("逐项对应对方诉请", "区分事实抗辩、法律抗辩和程序抗辩", "提示举证期限和反诉/抵销机会"),
    lawyer_review_triggers=("所有答辩状", "管辖异议", "反诉/抵销", "证据交换临近", "金额重大"),
)


LAWYER_LETTER = DocumentReviewStrategy(
    strategy_id="lawyer_letter",
    display_name="律师函/催告函审查",
    aliases=("律师函", "催告函", "通知函", "违约告知", "解除通知", "催收函"),
    matter_type="非诉函件",
    required_fields=(
        _field("函件对象和送达地址", ("致", "收件人", "地址", "联系人"), "确认函件对象和送达路径。", "对象或送达错误会影响催告、解除或时效中断效果。"),
        _field("事实基础", ("事实", "合同", "违约", "欠款", "逾期"), "确认函件陈述有证据支撑。", "事实夸大可能引发名誉或反向争议。"),
        _field("权利主张和期限", ("要求", "限期", "支付", "整改", "解除"), "确认主张明确、期限合理。", "主张不清会削弱谈判和后续诉讼衔接。"),
    ),
    review_dimensions=("函件目的", "事实真实性", "权利基础", "履行期限", "措辞克制", "送达证据", "后续诉讼衔接", "名誉/合规风险"),
    special_risk_rules=(
        _risk(rule_id="letter_overstatement", title="函件措辞可能过度或事实支撑不足", risk_level="高", risk_type="诉讼风险", keywords=("严重违法", "恶意", "诈骗", "必须", "立即", "全部责任"), applicable_rule="律师函和催告函应保持事实准确、依据明确、措辞克制，避免无证据指控。", user_impact="过度表述可能引发名誉侵权、商业诋毁或谈判失控。", authority_queries=("律师函 催告 送达 证据",), evidence_suggestion=("合同", "违约证据", "金额计算表", "送达凭证")),
    ),
    evidence_checklist=("合同和附件", "违约事实证据", "金额计算表", "历史催告记录", "收件地址确认", "快递/邮件送达凭证"),
    authority_queries=("催告 通知 送达", "解除通知", "违约责任"),
    report_focus=("强调事实支撑和措辞克制", "明确函件后续诉讼衔接", "列明送达证据"),
    lawyer_review_triggers=("冠名律师函", "解除通知", "高额索赔", "涉及名誉/商誉", "拟公开发送"),
)


ARBITRATION_APPLICATION = DocumentReviewStrategy(
    strategy_id="arbitration_application",
    display_name="仲裁申请书审查",
    aliases=("仲裁申请", "仲裁申请书", "申请人", "被申请人", "仲裁委员会", "仲裁请求"),
    matter_type="仲裁文书",
    required_fields=(
        _field("仲裁协议", ("仲裁条款", "仲裁协议", "仲裁委员会"), "确认仲裁管辖基础。", "仲裁协议无效或不明会导致不予受理或管辖争议。"),
        _field("仲裁请求", ("仲裁请求", "请求裁决", "请求事项"), "确认请求明确和金额计算。", "请求不清会影响受理和裁决可执行性。"),
        _field("事实和证据", ("事实", "证据", "证明目的"), "确认事实链和证据支撑。", "证据不足会影响裁决支持。"),
    ),
    review_dimensions=("仲裁协议效力", "仲裁机构明确性", "仲裁请求", "金额计算", "事实链", "证据目录", "保全", "送达", "律师复核"),
    special_risk_rules=(
        _risk(rule_id="arbitration_clause_validity", title="仲裁协议效力和机构明确性需优先核验", risk_level="重大", risk_type="诉讼风险", keywords=("仲裁", "仲裁委员会", "仲裁机构", "争议解决"), applicable_rule="应核验是否有明确请求仲裁的意思表示、仲裁事项和选定仲裁委员会。", user_impact="仲裁协议不明确可能导致案件不被受理或后续撤裁/不予执行风险。", authority_queries=("仲裁协议 仲裁委员会 明确",), evidence_suggestion=("合同仲裁条款", "补充协议", "仲裁规则")),
    ),
    evidence_checklist=("含仲裁条款的合同", "仲裁协议/补充协议", "主体身份材料", "证据目录", "金额计算表", "送达地址", "保全材料"),
    authority_queries=("仲裁协议", "仲裁委员会", "仲裁申请"),
    report_focus=("先审仲裁协议效力，再审请求和证据", "强制律师复核"),
    lawyer_review_triggers=("所有仲裁申请", "仲裁条款不清", "申请保全", "金额重大", "涉外/跨境"),
)


STRATEGIES: tuple[DocumentReviewStrategy, ...] = (
    LEASE_CONTRACT,
    LABOR_CONTRACT,
    SALES_CONTRACT,
    SERVICE_CONTRACT,
    LOAN_CONTRACT,
    GUARANTEE_CONTRACT,
    EQUITY_TRANSFER,
    LITIGATION_COMPLAINT,
    DEFENSE_STATEMENT,
    LAWYER_LETTER,
    ARBITRATION_APPLICATION,
    GENERAL_CONTRACT,
)


def get_document_strategy(document_type: str = "", document_text: str = "", user_role: str = "") -> DocumentReviewStrategy:
    haystack = _normalize(" ".join([document_type or "", user_role or "", document_text[:20000] or ""]))
    declared_type = _normalize(document_type or "")
    best_score = -1
    best = GENERAL_CONTRACT
    for strategy in STRATEGIES:
        score = 0
        for alias in strategy.aliases:
            normalized_alias = _normalize(alias)
            if normalized_alias and normalized_alias in haystack:
                score += 8 + min(len(normalized_alias), 8)
                if declared_type == normalized_alias:
                    score += 20
                elif normalized_alias and normalized_alias in declared_type and len(normalized_alias) >= 2:
                    score += 10
        if _normalize(strategy.display_name) in haystack:
            score += 8
        if score > best_score:
            best_score = score
            best = strategy
    return best if best_score > 0 else GENERAL_CONTRACT


def build_strategy_pending_facts(strategy: DocumentReviewStrategy, document_text: str) -> list[dict[str, str]]:
    normalized = _normalize(document_text)
    pending: list[dict[str, str]] = []
    for field_item in strategy.required_fields:
        if not any(_normalize(keyword) in normalized for keyword in field_item.keywords):
            pending.append(
                {
                    "field": field_item.name,
                    "reason": field_item.reason,
                    "impact": field_item.impact,
                    "source": "document_strategy_required_field",
                }
            )
    return pending


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()
