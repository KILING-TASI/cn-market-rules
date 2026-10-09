# 主体事件与REITs扩募条款交接接口 v1

本仓库负责发售/扩募规则、资格/条款/时限及证据定位；主工作台负责经营现金流、可供分配金额、资产估值/NAV与情景。接口没有工作台访问权限，不替它写文件，也不执行交易。reits_expansion支持独立已核的沪深三路径；深市显式限定2025版适用日期，法定价格下限、资格与未知资料仍逐项核对。

## 通用信封

JSON：schema_version="1.0"，kind为risk_events或reits_expansion_terms，as_of（ISO日期），sources（来源数组），records（记录数组）。sources含source_id、source_type、title、publisher、version、published_at（显式ISO或null）、url；source_type为rule/company_notice/official_summary/regulatory_decision。网页日与决定日不互换。

每记录含record_id、entity_name、event_date（ISO或显式null）、observation_date、facts和rules。facts含key、value、status、unit、evidence；evidence含source_id与locator。status为original（已核全文字段）、summary（仅摘要）、reported（有来源的主体陈述）、hypothesis（明确假设）、unknown（null＋reason）。hypothesis必须写reason，不与原文事实混淆。百分比unit=ratio，值0—1，另有denominator与denominator_date；不知道分母时不登记已核比率。

rules含source_id、locator、scope，来源必须是rule；公司事件来源与规则独立。官方摘要不能支持original或reported字段。unknown无证据可接受但必须说明原因。观察日不能晚于as_of；事件未来计划日可晚于观察日，必须以事实字段说明计划状态。字段key和记录ID唯一。

## 风险事件

event_type为unlock/pledge/goodwill；record_role为company_event或regulatory_observation。解禁计划和实际成交分开；质押合同的平仓价未知保留null；商誉监管观察不等于已认定财务造假。例证见[risk-events](../../interfaces/examples/risk-events.json)。证券代码不是强制推断字段，无确认可不提供。

## REITs扩募接口

market、offering_method（holders/public/targeted）、rule_check_status（unknown/partial/verified）是事实之外的核验范围标签。facts可传持有人大会批准份额、价格/基准日、发售路径、原持有人权利、战配/锁定、截止与退款、修订/实施版本，每字段单独绑定证据；规则下限与个案最终值分别传。

workbench_inputs列出由工作台补入的数据名，例如运营现金流、项目净资产公允价值、负债与允许费用、分配预测、旧持仓/实际认购；不填虚构数值。业务或资料未核不能标verified。verified至少要有原文已核价格/数量/路径和适用规则依据，也不等于审批、账户资格或正式完成。

示范[reits-terms](../../interfaces/examples/reits-terms.json)仅登记沪市可复用规则条款，项目字段未知，因此partial，不提供经营估值。不得把规则阈值80%当实际获配率或把募集价当资产公允价值。

## 离线验证

```sh
python scripts/evidence_interface.py --input interfaces/examples/risk-events.json
python scripts/evidence_interface.py --input interfaces/examples/reits-terms.json
```

输出仅为结构有效性、记录数和unknown数量，不提供风险评级、平仓价或估值结论。来源ID在包校验时与sources.md联查；外部自备来源只验证结构，不验证网站身份。校验拒绝主体/日期/版本缺失、来源引用断裂、摘要冒充全文、比例无分母、未知冒充0和错误verified标签。后续可增事件修订链/合同数据，首批不支持全市场抓取或收益回测。

## v1.1：来源分层与可得性（兼容v1.0）

新增source_tier：public_original（公开原文/官方摘要）、third_party_aggregate（第三方聚合）、licensed_data（付费或需授权资料）；access_requirement为public/paid/authorization/unknown。source_type新增aggregate；聚合线索不能支持original事实或rule。授权价格、权限未取得必须写unknown，不默认可访问。

每来源独立登记acquisition_status（success/failed/not_attempted）、retrieved_at（日期或null）、original_verification（verified/summary_only/not_verified）、verified_at（日期或null）。success表示取得当前所描述材料，可通过浏览器或本地取得；不等于核验上游原文。原文核验verified只允许已取得公开原文，聚合/付费材料先保留not_verified，另绑定实际原文来源。既有下载台账记录下载失败，不否定浏览器成功核读；官方摘要的取得成功也不等于全文成功。

[聚合可得性示范](../../interfaces/examples/aggregate-availability.json)仅表明官方文档已核，接口数据未调用，融资合同未知。不提供虚构历史比例或采购条件。AKShare已有stock_gpzy_pledge_ratio_em，指定日期必须为上游支持的交易日；比例%、股份万股、市值万元需显式转换。其它聚合接口“预估平仓线”保留模型身份，不成为已核合同价。

## 历史时点约束

记录可选backtest_cutoff（含时区的ISO时间）；此时所有非unknown事实须有available_at（含时区）。校验拒绝晚于cutoff的事实、早于已知发布日期的可得时间和混入假设。没有历史首次公开时间的记录不能冒充当时可得；当前取得时间不能证明历史可得。时点验收仅验证输入一致性，不证实首次公开时间或自动构建收益回测。

解禁分别保留announcement_date、planned_circulation_date、actual_circulation_date；计划日不能认证实际流通或成交。问询分别保留inquiry_issued_at和inquiry_disclosed_at，事件研究默认以公开披露时间建立信息集，不以未公开发出日提前交易。每份更正公告独立source_id/version/published_at；记录可另写supersedes_record_id。旧版本及其字段不可覆盖，晚披露更正不得回填旧cutoff。收盘后公告的可交易窗口须另结合交易日历/停牌确认。此批尚无问询原文样本、自动修订链解析或回测引擎。

## v1.2增量

兼容v1.0/v1.1，增加inquiry/correction事件类型、rule_query及rule_version_id，输出rule_selections，见[版本契约](rule-version-contract.md)。第三批已补收到问询公告与标题更正原文；前述第二批无样本状态仅为历史进度。精确首次披露时间、旧挂网原版本、自动修订链和回测引擎仍未完成。
