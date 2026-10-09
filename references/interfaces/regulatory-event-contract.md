# 有限个案证据扩展：信封 1.3／共用交接 1.1

本库主线是制度、有效版本、条款核对与给定条件情景计算。公司事件时间轴、关联检索与研究解释由 research-workbench 承接；本页仅保留有限的规则适用与证据缺口示例，不扩展为全量事件库、采集器或评分平台。

复用已有 risk_events、字段来源、规则选择和未知值处理，新增 regulatory_event 块。信封 1.0／1.1／1.2 与交接 1.0 保持原行为；显式 1.3 才启用新块，共用视图为 cn-market-rules.rule-handoff/1.1。结构校验不认证原文真实性或法律定性，不产生采集、评分或收益回测。

## 类型、证据与时间

| event_type | 证据及阶段 | 不可直接替代 |
|---|---|---|
| inquiry | 收到问询公告或问询原函；received／issued | 问询不等于处罚、批准或整改完成 |
| administrative_penalty | 原处罚决定或官方／发行人通知援引；decision_issued／decision_cited／received | 通知援引不等于决定原件已核；处罚依据与下游退市规则分开 |
| supervisory_measure | 原监管措施决定或通知援引；measure_issued／measure_cited | 责令改正／警示等不自动转成行政处罚 |
| audit_opinion | 审计报告或年报内嵌审计报告；opinion_issued | 财务与内控意见分开，非标不自动认定造假或处罚 |
| correction | 原更正公告；title_correction／financial_correction／other_correction | 标题更正不等于财务差错，后更正不能回填旧时点 |

evidence_kind、process_stage 与类型相互约束；evidence 绑定来源／定位。original_document_status 为取得、内嵌或未取得，含义是**对应证据类型的容器**：取得“收到問询公告”不等于取得问询原函。引用处罚决定的通知必须为 not_obtained，不能升级为原决定。source_type 的 regulatory_letter／audit_report 仅在 1.3 增加；内嵌报告仍来自发行人 company_notice 容器。

publication 含 date、precision、first_public_at、reason、evidence。首批只支持明确公开文件日（day）或 unknown；first_public_at 必须 null，不虚构午夜。公开日需与所绑定来源一致，不用签署日、收到日或决定日替代。日精度／未知记录不能进入同日或更早的盘中截止检查；继续复用旧 available_at 检查，不自动创建历史可得时刻。

legal_effect 单列 status（unknown／not_applicable／documented）、date 与理由／证据。未知和不适用必须 null；引用而未取得决定原件的记录不能认证法律生效。审计意见不认证行政生效；披露日也不自动成为生效日。

## 规则关联

rule_application 的 status 为 selected／authority_cited／not_checked，含 version_id、effective_from、effective_until、relation。selected 必须与已有 rule_query 选择器的版本及有效区间完全匹配，不认证资格。authority_cited 只保存 reported_version_name 及原通知定位；未核版的 version_id 和区间仍 null，不把法规引用文字包装成独立核验。

relation 明确区分披露义务、下游上市规则引用和未核的处罚／监管／审计／更正依据。不能将交易所退市规则引用当处罚法律依据，也不能用 2026 版回填 2024 案例。classification_scope 固定 no_fraud_inference；字段原样转交，不能由信号自动输出造假结论。

## 四条限定样本

[输入](../../interfaces/examples/regulatory-events.json)复用南方润泽问询、利元亨标题更正；新增新海宜 2024-03-18 交易所正式通知援引处罚、深圳机场 2025 年报财务标准无保留意见。审计签署 2026-04-22 与披露文件日 2026-04-24 分开。四条均有公开文件日，首次精确上网时刻未知；处罚原件和处罚依据仍缺。

一条关联版本已选（深市扩募问询披露）；其余三条关联版本保留缺口。类型支持仅为证据结构兼容，不承诺扩展案例覆盖。上海凤凰候选决定网页可读，但公告 PDF 取得失败、明确公众日期未闭环，未把候选检索升级为已闭环样本。

原文来源见[INQUIRY-RUNZE、CORRECTION-LYH、CORRECTION-LYH-PUBLIC、XINHAI-PENALTY-CITE、AIRPORT-AUDIT-2025](../sources.md)，不附原文全文。阅读与保存说明见[新阅读页](../../docs/regulatory-preview/README.md)；历史 [docs/preview](../../docs/preview/README.md) 冻结结果不修改。
