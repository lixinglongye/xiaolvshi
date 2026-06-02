from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class LegalSourceSeed:
    source_id: str
    source_name: str
    article_or_case_number: str
    source_type: str
    authority_level: str
    legal_effect_note: str
    text_excerpt_or_holding: str
    keywords: tuple[str, ...]


LOCAL_LEGAL_SOURCES: tuple[LegalSourceSeed, ...] = (
    LegalSourceSeed(
        source_id="LAW-CIVIL-465",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第四百六十五条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可作为民事合同效力和履行争议的基础裁判依据；具体适用仍需结合事实核验。",
        text_excerpt_or_holding="依法成立的合同，受法律保护。",
        keywords=("合同效力", "依法成立", "生效", "无效", "合同成立"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-470",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第四百七十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查合同主要条款是否完整。",
        text_excerpt_or_holding="合同内容一般包括当事人、标的、数量、质量、价款或者报酬、履行期限地点和方式、违约责任、争议解决等条款。",
        keywords=("缺失条款", "主要条款", "标的", "数量", "质量", "价款", "报酬", "履行", "争议解决"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-497",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第四百九十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查格式条款是否不合理免责、加重对方责任或排除主要权利。",
        text_excerpt_or_holding="提供格式条款一方不合理地免除或者减轻其责任、加重对方责任、限制或排除对方主要权利的，相关格式条款可能无效。",
        keywords=("格式条款", "免除责任", "加重责任", "排除权利", "不公平", "单方"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-509",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百零九条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查合同履行、通知、协助、保密等附随义务。",
        text_excerpt_or_holding="当事人应当按照约定全面履行义务，并遵循诚信原则履行通知、协助、保密等义务。",
        keywords=("履行义务", "诚信原则", "通知", "协助", "保密", "附随义务"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-510",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百一十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于处理合同约定不明后的补充协议和交易习惯解释。",
        text_excerpt_or_holding="合同生效后，当事人就质量、价款或者报酬、履行地点等内容没有约定或者约定不明确的，可以协议补充。",
        keywords=("约定不明", "补充协议", "质量", "价款", "报酬", "履行地点", "交易习惯"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-562",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百六十二条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查约定解除条件、解除流程和通知机制是否清晰。",
        text_excerpt_or_holding="当事人协商一致可以解除合同；也可以约定一方解除合同的事由。",
        keywords=("解除条件", "约定解除", "解除合同", "终止", "提前解除", "协商解除"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-563",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百六十三条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查法定解除场景是否被不当限制或遗漏。",
        text_excerpt_or_holding="因不可抗力致使不能实现合同目的、履行期限届满前明示或以行为表明不履行主要债务、迟延履行主要债务经催告后仍未履行等情形下，当事人可以解除合同。",
        keywords=("法定解除", "不能实现合同目的", "迟延履行", "催告", "主要债务", "根本违约"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-566",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百六十六条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查合同解除后的返还、折价补偿、赔偿责任和结算安排。",
        text_excerpt_or_holding="合同解除后，尚未履行的终止履行；已经履行的，可以根据履行情况和合同性质请求恢复原状、采取补救措施，并有权请求赔偿损失。",
        keywords=("解除后果", "返还", "恢复原状", "补救措施", "结算", "赔偿损失"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-577",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百七十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查违约责任承担方式是否完整。",
        text_excerpt_or_holding="当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、补救措施或者赔偿损失等违约责任。",
        keywords=("违约责任", "不履行", "继续履行", "补救措施", "赔偿损失"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-584",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百八十四条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查损失赔偿范围和可预见性限制。",
        text_excerpt_or_holding="损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益，但不得超过违约方订立合同时预见或应当预见的损失。",
        keywords=("损失赔偿", "可得利益", "可预见", "赔偿范围"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-585",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百八十五条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查违约金、损失赔偿额计算方法及过高过低调整。",
        text_excerpt_or_holding="当事人可以约定违约金或损失赔偿额计算方法；约定违约金过分高于造成的损失的，可请求适当减少。",
        keywords=("违约金", "过高", "过低", "损失赔偿额", "调整"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-590",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百九十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查不可抗力通知、减损和免责条款。",
        text_excerpt_or_holding="因不可抗力不能履行合同的，根据不可抗力影响，部分或者全部免除责任；当事人迟延履行后发生不可抗力的，不免除其违约责任。",
        keywords=("不可抗力", "免责", "通知", "减损", "迟延履行"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-587",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百八十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查定金条款、双倍返还和没收定金的适用边界。",
        text_excerpt_or_holding="给付定金一方不履行债务或者履行债务不符合约定致使不能实现合同目的的，无权请求返还定金；收受定金一方违约的，应当双倍返还定金。",
        keywords=("定金", "订金", "双倍返还", "没收定金", "合同目的"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-596",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第五百九十六条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于买卖合同标的、数量、价款、履行方式等条款完整性审查。",
        text_excerpt_or_holding="买卖合同的内容一般包括标的物名称、数量、质量、价款、履行期限、地点和方式、包装、检验标准和方法等。",
        keywords=("买卖", "销售", "采购", "标的物", "检验", "包装", "交付"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-620",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百二十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于买卖合同质量检验、验收期间和通知义务审查。",
        text_excerpt_or_holding="买受人收到标的物时应当在约定的检验期限内检验；没有约定检验期限的，应当及时检验。",
        keywords=("买卖", "验收", "检验", "质量异议", "通知"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-667",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百六十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于识别借款合同基础法律关系和本金、还款、利息安排。",
        text_excerpt_or_holding="借款合同是借款人向贷款人借款，到期返还借款并支付利息的合同。",
        keywords=("借款合同", "借款", "贷款", "本金", "返还", "利息"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-679",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百七十九条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于自然人之间借款合同成立和本金交付证据审查。",
        text_excerpt_or_holding="自然人之间的借款合同，自贷款人提供借款时成立。",
        keywords=("自然人借款", "借款交付", "提供借款", "本金交付", "转账凭证"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-680",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百八十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查借款利率、利息费用和高利放贷风险；具体可支持上限仍需结合现行司法解释核验。",
        text_excerpt_or_holding="禁止高利放贷，借款的利率不得违反国家有关规定。",
        keywords=("借款利息", "借款利率", "高利放贷", "利率", "利息", "民间借贷"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-703",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百零三条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于租赁合同基础法律关系识别。",
        text_excerpt_or_holding="租赁合同是出租人将租赁物交付承租人使用、收益，承租人支付租金的合同。",
        keywords=("租赁", "出租", "承租", "租金", "押金"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-712",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百一十二条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于租赁物维修义务审查。",
        text_excerpt_or_holding="出租人应当履行租赁物的维修义务，但是当事人另有约定的除外。",
        keywords=("租赁", "维修", "修缮", "出租人义务", "房屋"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-713",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百一十三条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于承租人请求维修、自行维修费用承担、租金减免或延长租期审查。",
        text_excerpt_or_holding="承租人在租赁物需要维修时可以请求出租人在合理期限内维修；出租人未履行维修义务的，承租人可以自行维修，维修费用由出租人负担。",
        keywords=("租赁", "维修", "自行维修", "减少租金", "延长租期", "漏水"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-724",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百二十四条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于非因承租人原因导致租赁物无法使用时的解除权审查。",
        text_excerpt_or_holding="非因承租人原因致使租赁物无法使用的，承租人可以在法定情形下解除合同。",
        keywords=("租赁", "解除", "无法使用", "查封", "权属争议", "使用条件"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-725",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百二十五条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查租赁期间所有权变动对承租人使用权益的影响。",
        text_excerpt_or_holding="租赁物在承租人按照租赁合同占有期限内发生所有权变动的，不影响租赁合同的效力。",
        keywords=("租赁", "买卖不破租赁", "所有权变动", "承租人", "房屋"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-730",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百三十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查租赁期限约定不明导致的任意解除风险。",
        text_excerpt_or_holding="当事人对租赁期限没有约定或者约定不明确，依法仍不能确定的，视为不定期租赁；当事人可以随时解除合同，但应当在合理期限之前通知对方。",
        keywords=("租赁期限", "约定不明", "不定期租赁", "随时解除", "合理期限"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-734",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第七百三十四条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查租赁期满续租、优先承租等安排。",
        text_excerpt_or_holding="租赁期限届满，承租人继续使用租赁物，出租人没有提出异议的，原租赁合同继续有效，但是租赁期限为不定期。",
        keywords=("租赁期满", "续租", "优先承租", "不定期", "继续使用"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-681",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百八十一条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于识别保证合同和保证责任基础法律关系。",
        text_excerpt_or_holding="保证合同是为保障债权的实现，保证人和债权人约定，当债务人不履行到期债务或者发生约定情形时，保证人履行债务或者承担责任的合同。",
        keywords=("保证", "担保", "债权", "保证人", "保证责任"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-686",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第六百八十六条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查一般保证、连带责任保证及约定不明的风险。",
        text_excerpt_or_holding="保证方式包括一般保证和连带责任保证；当事人对保证方式没有约定或者约定不明确的，按照一般保证承担保证责任。",
        keywords=("一般保证", "连带责任保证", "保证方式", "约定不明", "担保"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-496",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第四百九十六条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查格式条款提供方是否履行提示说明义务。",
        text_excerpt_or_holding="采用格式条款订立合同的，提供格式条款的一方应当遵循公平原则确定权利义务，并采取合理方式提示对方注意免除或者减轻其责任等重大利害关系条款。",
        keywords=("格式条款", "提示说明", "重大利害关系", "公平原则", "免除责任", "减轻责任"),
    ),
    LegalSourceSeed(
        source_id="LAW-CIVIL-498",
        source_name="《中华人民共和国民法典》",
        article_or_case_number="第四百九十八条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查格式条款歧义解释和非格式条款优先规则。",
        text_excerpt_or_holding="对格式条款的理解发生争议的，应当按照通常理解予以解释；有两种以上解释的，应当作出不利于提供格式条款一方的解释。",
        keywords=("格式条款", "歧义", "不利解释", "通常理解", "非格式条款"),
    ),
    LegalSourceSeed(
        source_id="LAW-ARBITRATION-16",
        source_name="《中华人民共和国仲裁法》",
        article_or_case_number="第十六条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查仲裁协议是否具备请求仲裁的意思表示、仲裁事项和选定仲裁委员会。",
        text_excerpt_or_holding="仲裁协议应当具有请求仲裁的意思表示、仲裁事项和选定的仲裁委员会。",
        keywords=("仲裁", "仲裁条款", "仲裁委员会", "争议解决", "管辖"),
    ),
    LegalSourceSeed(
        source_id="LAW-ARBITRATION-18",
        source_name="《中华人民共和国仲裁法》",
        article_or_case_number="第十八条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查仲裁事项或仲裁委员会约定不明确导致的效力风险。",
        text_excerpt_or_holding="仲裁协议对仲裁事项或者仲裁委员会没有约定或者约定不明确的，当事人可以补充协议；达不成补充协议的，仲裁协议无效。",
        keywords=("仲裁", "约定不明", "仲裁委员会", "无效", "补充协议", "争议解决"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-19",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第十九条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查劳动合同试用期是否超过法定上限。",
        text_excerpt_or_holding="劳动合同期限不同，对应试用期期限上限不同；同一用人单位与同一劳动者只能约定一次试用期。",
        keywords=("劳动", "试用期", "劳动合同", "期限"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-10",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查劳动关系建立后是否及时订立书面劳动合同。",
        text_excerpt_or_holding="建立劳动关系，应当订立书面劳动合同；已建立劳动关系未同时订立书面劳动合同的，应当自用工之日起一个月内订立书面劳动合同。",
        keywords=("劳动", "书面劳动合同", "用工", "劳动关系", "一个月"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-17",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查劳动合同必备条款是否完整。",
        text_excerpt_or_holding="劳动合同应当具备用人单位和劳动者信息、合同期限、工作内容和地点、工作时间休息休假、劳动报酬、社会保险、劳动保护等条款。",
        keywords=("劳动", "必备条款", "工作内容", "劳动报酬", "社会保险", "休息休假"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-23",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第二十三条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查保密义务、竞业限制经济补偿。",
        text_excerpt_or_holding="用人单位与劳动者可以约定保守商业秘密和知识产权相关保密事项；竞业限制应约定经济补偿。",
        keywords=("劳动", "保密", "竞业限制", "经济补偿", "商业秘密"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-24",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第二十四条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查竞业限制人员范围、地域、期限和行业范围。",
        text_excerpt_or_holding="竞业限制期限不得超过二年，人员范围限于高级管理人员、高级技术人员和其他负有保密义务的人员。",
        keywords=("劳动", "竞业限制", "二年", "人员范围", "地域"),
    ),
    LegalSourceSeed(
        source_id="LAW-LABOR-30",
        source_name="《中华人民共和国劳动合同法》",
        article_or_case_number="第三十条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查工资支付时间、金额和拖欠工资风险。",
        text_excerpt_or_holding="用人单位应当按照劳动合同约定和国家规定，向劳动者及时足额支付劳动报酬。",
        keywords=("劳动", "工资", "劳动报酬", "及时足额", "拖欠", "支付"),
    ),
    LegalSourceSeed(
        source_id="LAW-PIPL-13",
        source_name="《中华人民共和国个人信息保护法》",
        article_or_case_number="第十三条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查个人信息处理是否具备合法处理基础。",
        text_excerpt_or_holding="处理个人信息应当具备取得个人同意、为订立或履行合同所必需、履行法定职责或法定义务所必需等法定情形之一。",
        keywords=("个人信息", "数据", "隐私", "同意", "处理", "合法基础"),
    ),
    LegalSourceSeed(
        source_id="LAW-PIPL-17",
        source_name="《中华人民共和国个人信息保护法》",
        article_or_case_number="第十七条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查个人信息处理前是否充分告知处理规则。",
        text_excerpt_or_holding="个人信息处理者在处理个人信息前，应当以显著方式、清晰易懂的语言真实、准确、完整地告知处理者名称、联系方式、处理目的、方式、种类、保存期限等事项。",
        keywords=("个人信息", "告知", "处理目的", "保存期限", "隐私政策", "数据"),
    ),
    LegalSourceSeed(
        source_id="LAW-PIPL-59",
        source_name="《中华人民共和国个人信息保护法》",
        article_or_case_number="第五十九条",
        source_type="法律",
        authority_level="裁判依据",
        legal_effect_note="法律层级规范，可用于审查受托处理个人信息时的安全保障和协助义务。",
        text_excerpt_or_holding="接受委托处理个人信息的受托人，应当按照法律规定和约定采取必要措施保障所处理的个人信息安全，并协助个人信息处理者履行相关义务。",
        keywords=("个人信息", "委托处理", "受托处理", "安全保障", "数据处理", "协助义务"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-SERVICE-SLA",
        source_name="服务合同审查实务清单",
        article_or_case_number="服务范围/SLA/验收核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为服务合同审查的实务核对清单；正式法律结论仍需匹配具体法律依据和事实。",
        text_excerpt_or_holding="服务合同通常需核对服务范围、服务标准、响应时限、验收流程、变更审批、成果交付和退出交接。",
        keywords=("服务合同", "服务范围", "SLA", "响应时间", "验收", "变更", "交付物", "运维"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-LOAN-EVIDENCE",
        source_name="借款合同证据链实务清单",
        article_or_case_number="本金交付/利息/担保核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为借款争议证据链核对清单；利率、担保、诉讼时效等仍需结合法律和司法解释核验。",
        text_excerpt_or_holding="借款合同通常需核对本金交付凭证、利息费用口径、还款流水、催收记录、担保文件和送达凭证。",
        keywords=("借款", "借贷", "贷款", "本金", "利息", "利率", "交付凭证", "还款", "催收"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-EQUITY-DD",
        source_name="股权转让尽职调查实务清单",
        article_or_case_number="权属/出资/负债/交割核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为股权交易尽调和交割核对清单；公司法、税法和交易文件效力需另行核验。",
        text_excerpt_or_holding="股权转让通常需核对股权权属、出资实缴、优先购买权、历史债务、税务、诉讼、担保、陈述保证和工商变更。",
        keywords=("股权转让", "目标公司", "工商变更", "陈述保证", "或有负债", "出资", "实缴", "交割"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-LITIGATION-COMPLAINT",
        source_name="民事起诉状立案审查实务清单",
        article_or_case_number="主体/请求/事实/证据核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为起诉状结构和立案材料核对清单；程序规则和法院要求需以现行法律及受理法院规则为准。",
        text_excerpt_or_holding="起诉状通常需核对当事人信息、管辖依据、诉讼请求、事实与理由、金额计算、证据目录、送达地址和诉讼时效。",
        keywords=("起诉状", "民事起诉状", "诉讼请求", "请求判令", "事实与理由", "证据目录", "立案", "管辖", "时效"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-DEFENSE",
        source_name="答辩状抗辩审查实务清单",
        article_or_case_number="逐项回应/程序抗辩/反证核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为答辩状和抗辩思路核对清单；正式诉讼策略需由执业律师结合案卷确定。",
        text_excerpt_or_holding="答辩状通常需逐项回应诉讼请求，核对管辖、时效、履行、金额、证据反驳、反诉或抵销可能性。",
        keywords=("答辩状", "答辩", "抗辩", "管辖异议", "时效抗辩", "反诉", "抵销", "反证"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-LAWYER-LETTER",
        source_name="律师函/催告函审查实务清单",
        article_or_case_number="事实依据/权利主张/送达核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为函件审查核对清单；冠名律师函和重大争议应由执业律师复核。",
        text_excerpt_or_holding="律师函或催告函通常需核对事实证据、权利基础、主张金额、履行期限、措辞克制性和送达留痕。",
        keywords=("律师函", "催告函", "通知函", "解除通知", "送达", "催告", "权利主张", "措辞"),
    ),
    LegalSourceSeed(
        source_id="PRACTICE-ARBITRATION",
        source_name="仲裁申请书审查实务清单",
        article_or_case_number="仲裁协议/请求/证据核对项",
        source_type="实务清单",
        authority_level="实务参考",
        legal_effect_note="非裁判依据，仅作为仲裁申请材料核对清单；仲裁协议效力和仲裁机构要求需结合现行规则核验。",
        text_excerpt_or_holding="仲裁申请通常需先核验仲裁协议和机构明确性，再核对仲裁请求、金额计算、事实链、证据目录和送达地址。",
        keywords=("仲裁申请", "仲裁申请书", "仲裁请求", "仲裁协议", "仲裁委员会", "仲裁机构", "证据目录"),
    ),
)


def _load_knowledge_seed_sources() -> tuple[LegalSourceSeed, ...]:
    seed_path = Path(__file__).resolve().parents[1] / "data" / "legal_knowledge" / "contract_law_seed.json"
    if not seed_path.exists():
        return ()

    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    records = payload.get("records", [])
    if not isinstance(records, list):
        return ()

    sources: list[LegalSourceSeed] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        source_id = str(record.get("source_id") or "").strip()
        source_name = str(record.get("source_name") or "").strip()
        article_number = str(record.get("article_number") or "").strip()
        text = str(record.get("text") or record.get("summary") or "").strip()
        if not source_id or not source_name or not article_number or not text:
            continue

        keywords = []
        for field_name in ("keywords", "topics"):
            value = record.get(field_name) or []
            if isinstance(value, str):
                keywords.append(value)
            elif isinstance(value, list):
                keywords.extend(str(item) for item in value if str(item).strip())

        sources.append(
            LegalSourceSeed(
                source_id=source_id,
                source_name=source_name,
                article_or_case_number=article_number,
                source_type=str(record.get("source_type") or "法律"),
                authority_level=str(record.get("authority_level") or "裁判依据"),
                legal_effect_note=str(record.get("legal_effect_note") or record.get("summary") or "已纳入本地法律知识库。"),
                text_excerpt_or_holding=text,
                keywords=tuple(dict.fromkeys(keywords)),
            )
        )
    return tuple(sources)


def _combine_sources(*source_groups: tuple[LegalSourceSeed, ...]) -> tuple[LegalSourceSeed, ...]:
    combined: list[LegalSourceSeed] = []
    seen_source_ids: set[str] = set()
    seen_articles: set[str] = set()

    for sources in source_groups:
        for source in sources:
            article_key = f"{source.source_name}|{source.article_or_case_number}"
            if source.source_id in seen_source_ids or article_key in seen_articles:
                continue
            seen_source_ids.add(source.source_id)
            seen_articles.add(article_key)
            combined.append(source)
    return tuple(combined)


LEGAL_RESEARCH_SOURCES = _combine_sources(_load_knowledge_seed_sources(), LOCAL_LEGAL_SOURCES)


class LocalLegalResearchService:
    """Deterministic local source retrieval to keep citations bounded and auditable."""

    STRATEGY_SOURCE_EXCLUSIONS: dict[str, tuple[str, ...]] = {
        "sales_contract": (
            "CIVIL-703",
            "CIVIL-704",
            "CIVIL-712",
            "CIVIL-713",
            "CIVIL-724",
            "CIVIL-725",
            "CIVIL-730",
            "CIVIL-734",
            "LABOR-",
        ),
        "lease_contract": ("CIVIL-596", "CIVIL-620", "LABOR-", "PIPL-"),
        "labor_contract": (
            "CIVIL-596",
            "CIVIL-620",
            "CIVIL-703",
            "CIVIL-704",
            "CIVIL-712",
            "CIVIL-713",
            "CIVIL-724",
            "CIVIL-725",
            "CIVIL-730",
            "CIVIL-734",
        ),
        "loan_contract": (
            "CIVIL-596",
            "CIVIL-620",
            "CIVIL-703",
            "CIVIL-704",
            "CIVIL-712",
            "CIVIL-713",
            "LABOR-",
            "PIPL-",
        ),
    }

    STRATEGY_SOURCE_BOOSTS: dict[str, tuple[str, ...]] = {
        "sales_contract": ("CIVIL-596", "CIVIL-620", "PRACTICE-SERVICE-SLA"),
        "lease_contract": ("CIVIL-703", "CIVIL-704", "CIVIL-712", "CIVIL-713", "CIVIL-724", "CIVIL-725", "CIVIL-730"),
        "labor_contract": ("LABOR-",),
        "loan_contract": ("CIVIL-667", "CIVIL-679", "PRACTICE-LOAN"),
        "guarantee_contract": ("CIVIL-681", "CIVIL-686"),
        "equity_transfer": ("PRACTICE-EQUITY",),
        "lawsuit_complaint": ("PRACTICE-LITIGATION",),
        "defense_statement": ("PRACTICE-DEFENSE",),
        "lawyer_letter": ("PRACTICE-LAWYER-LETTER",),
        "arbitration_application": ("LAW-ARBITRATION", "PRACTICE-ARBITRATION"),
    }

    def search(self, query: str, *, limit: int = 4, strategy_id: str | None = None) -> list[dict]:
        normalized = self._normalize(query)
        scored: list[tuple[int, LegalSourceSeed]] = []
        for source in LEGAL_RESEARCH_SOURCES:
            score = self._score(normalized, source.keywords)
            if score == 0:
                score = self._generic_contract_score(normalized, source)
            if score > 0:
                score = self._strategy_adjusted_score(score, source, strategy_id, normalized)
            if score > 0:
                scored.append((score, source))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._to_citation(source, query) for _, source in scored[:limit]]

    def search_for_risk(self, risk: dict, *, limit: int = 3, strategy_id: str | None = None) -> list[dict]:
        text_parts = [
            risk.get("title", ""),
            risk.get("risk_type", ""),
            risk.get("issue_location", ""),
            risk.get("original_clause", {}).get("text", "") if isinstance(risk.get("original_clause"), dict) else "",
            risk.get("legal_analysis", {}).get("applicable_rule", "") if isinstance(risk.get("legal_analysis"), dict) else "",
        ]
        authority_queries = risk.get("authority_queries") or []
        if isinstance(authority_queries, (list, tuple)):
            text_parts.extend(authority_queries)
        elif authority_queries:
            text_parts.append(str(authority_queries))
        return self.search(" ".join(str(part) for part in text_parts), limit=limit, strategy_id=strategy_id)

    def validate_citations(self, citations: Iterable[dict]) -> list[dict]:
        known_ids = {source.source_id for source in LEGAL_RESEARCH_SOURCES}
        known_by_id = {source.source_id: source for source in LEGAL_RESEARCH_SOURCES}
        validated = []
        seen: set[str] = set()
        for citation in citations:
            item = dict(citation)
            source_id = item.get("source_id")
            dedupe_key = f"{source_id}|{item.get('source_name')}|{item.get('article_or_case_number')}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            if source_id in known_ids:
                source = known_by_id[source_id]
                item["source_name"] = source.source_name
                item["article_or_case_number"] = source.article_or_case_number
                item["source_type"] = source.source_type
                item["authority_level"] = source.authority_level
                item["legal_effect_note"] = source.legal_effect_note
                item["text_excerpt_or_holding"] = source.text_excerpt_or_holding
                item["verification_status"] = "已校验"
                item["confidence"] = max(int(item.get("confidence") or 0), 86)
            else:
                item["verification_status"] = item.get("verification_status") or "待核验"
                item["confidence"] = min(int(item.get("confidence") or 60), 75)
                item["legal_effect_note"] = (
                    item.get("legal_effect_note")
                    or "该依据未命中系统内置来源库，需人工或外部法库进一步核验。"
                )
            validated.append(item)
        return validated

    def _score(self, normalized_query: str, keywords: tuple[str, ...]) -> int:
        score = 0
        for keyword in keywords:
            normalized_keyword = self._normalize(keyword)
            if normalized_keyword and normalized_keyword in normalized_query:
                score += 5 + min(len(normalized_keyword), 8)
        return score

    def _generic_contract_score(self, normalized_query: str, source: LegalSourceSeed) -> int:
        if not normalized_query:
            return 0
        generic_terms = ("合同", "协议", "条款", "履行", "违约", "权利义务", "审查")
        if not any(term in normalized_query for term in generic_terms):
            return 0
        if source.source_id == "LAW-CIVIL-470":
            return 3
        if source.source_id == "LAW-CIVIL-509":
            return 2
        if source.source_id == "LAW-CIVIL-465":
            return 1
        return 0

    def _strategy_adjusted_score(
        self,
        score: int,
        source: LegalSourceSeed,
        strategy_id: str | None,
        normalized_query: str,
    ) -> int:
        if not strategy_id:
            return score
        source_key = source.source_id.upper()
        exclusions = self.STRATEGY_SOURCE_EXCLUSIONS.get(strategy_id, ())
        for marker in exclusions:
            if marker.upper() in source_key:
                if not self._query_explicitly_matches_source_domain(normalized_query, source):
                    return 0
        boosts = self.STRATEGY_SOURCE_BOOSTS.get(strategy_id, ())
        if any(marker.upper() in source_key for marker in boosts):
            score += 4
        return score

    def _query_explicitly_matches_source_domain(self, normalized_query: str, source: LegalSourceSeed) -> bool:
        source_terms = self._normalize(" ".join(source.keywords))
        strong_terms = ("租赁", "劳动", "买卖", "借款", "担保", "股权", "仲裁", "律师函", "个人信息")
        return any(term in normalized_query and term in source_terms for term in strong_terms)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", "", text or "").lower()

    def _to_citation(self, source: LegalSourceSeed, query: str) -> dict:
        return {
            "source_id": source.source_id,
            "source_name": source.source_name,
            "article_or_case_number": source.article_or_case_number,
            "source_type": source.source_type,
            "authority_level": source.authority_level,
            "legal_effect_note": source.legal_effect_note,
            "text_excerpt_or_holding": source.text_excerpt_or_holding,
            "relevance_reason": self._build_relevance_reason(source, query),
            "verification_status": "已校验",
            "confidence": 88,
        }

    def _build_relevance_reason(self, source: LegalSourceSeed, query: str) -> str:
        matched = [kw for kw in source.keywords if self._normalize(kw) in self._normalize(query)]
        if matched:
            return f"命中关键词：{'、'.join(matched[:4])}；可作为该风险项法律分析的基础依据。"
        return "根据风险项语义与该法律依据的规范对象相近，作为候选依据纳入，仍需结合原文事实复核。"
