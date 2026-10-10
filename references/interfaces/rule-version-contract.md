# 规则版本接口 v1：日期、适用范围与更替

目录为[rules/version-catalog.json](../../rules/version-catalog.json)，查询示例为[example-query](../../rules/example-query.json)。仅覆盖已登记专题和条款；选择版本不等于完整资格判断，也不把现行算术应用于历史规则。

每版本含version_id、document_version、market、board、subjects、asset_types、published_at、effective_from、effective_until、publication_evidence、interval_evidence、supersedes、replaced_by、verification_status与topics。公布和实施独立；有效区间为[effective_from,effective_until)，废止当日不再用旧版。effective_until=null只表示在verified_as_of覆盖内未登记终止，不代表永久有效。缺实施日的pending版本不选择。

首批覆盖沪市REITs 2022与2025版、深市2025扩募指引、沪市2026交易规则主板选段；北交所2026第10章已核并登记有效区间，2026-04-24前历史版本未登记；选中不认证上市标准例外或年度衔接。沪市2022版只适用基础设施资产，2025版增加商业不动产范围；同专题按市场、板块、主体、资产类型精确匹配，不默认跨市场。2022版于2025-12-31被替代，依据为新发布通知，沿革保留旧版。深市旧版废止已核，但旧版本完整目录尚未建立，2025-12-31以前查询返回gap。

查询含topic、market、board、subject、asset_type、applicability_date、knowledge_date。前者是需要适用规则的日期，后者是允许使用公开资料的日期；适用日期不能晚于知识截止日，超出目录核验范围不外推。选择结果含rule_version_id、document_version、公布/有效区间、条款定位、更替关系、目录核验日。没有版本为gap；多个版本重叠为ambiguous，不能静默取最新。目录原文真实性、版本完整性仍需人工核验；接口只检查输入一致性。

topics逐条登记activation：active、deferred、conditional、unknown。2026沪市交易规则公布于4月24日、7月6日实施；晚间大宗成交申报另列deferred，具体开启通知尚未取得，不把整份新规生效解释为该功能已开。复杂退市衔接、过渡期按对象/财务年度等条件需后续专门建模，此批不编造条件判断器。遇到conditional返回条件及缺口，由个案资料解决，不自动套旧规则。

```sh
python scripts/rule_versions.py --input rules/example-query.json
```

事件接口v1.2可加rule_query及rule_version_id，由原校验器输出rule_selections。必须绑定选中条款的来源；误写版本、用后时点规则知识回测旧截止日都会拒绝。没有rule_query的v1.0/v1.1继续兼容。版本选中与事件内容证据、扩募资格/审批/计算是分别的检查，不增加工作台依赖。

## 小型问询与更正案例

[例证](../../interfaces/examples/inquiry-correction.json)：南方润泽基金公告记录8月10日收到问询与8月12日公告，发出精确时刻未知；规则选择深市2025指引第20条。问询不等于项目批准或生效。利元亨2026-050落款8月26日，中国证券报刊登8月27日，仅更正挂网标题，不把公告内容改写为会计差错或财务造假。旧挂网版本和首次上网时刻未取得。

案例没有可核秒级available_at，不能直接投入旧日盘中回测。更正前文字的证据来自后公告描述，不能冒充旧时点的原公告；每个版本独立保留，未取得旧版本时不伪造supersedes_record_id。独立法律生效时间未知保持null，与公开日、落款日区分。

原文依据见[REITS-EXP-SH-2022、REITS-EXP-SH、REITS-EXP-SZ、TRADE-SH、TRADE-SH-DEFER、INQUIRY-RUNZE、CORRECTION-LYH、CORRECTION-LYH-PUBLIC](../sources.md)。

有rule_query时，选中的规则来源也必须声明相同rule_version_id，避免来源版本与记录版本脱节。中国市场的日期字段按UTC+08:00日界线核对；带时区时间比较使用真实瞬时，UTC输入跨中国日期边界时不按UTC日期误判。此处修正接口日期检查，不改变现有情景计算的日期口径。
