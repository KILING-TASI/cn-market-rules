# 工作台联调：规则消费边界

核验2026-10-09。规则端维护原文、有限版本目录与证据交接；research-workbench维护消费、研究组织和报告。沿用规则库PR #1与工作台PR #6，不自动合并或发版。下述文件是未绑定真实基金项目的接口例证，不是投资资格正例。

## 输入与输出

| 场景 | 规则端输入 | 共用输出／预期 |
|---|---|---|
| 官方版本依据充分 | [selected信封](../../interfaces/common-inputs/workbench-rule-selected.json) | [selected交接](../../interfaces/common-examples/workbench-rule-selected.json)：SSE-REITS-EXP-2025，selected；项目核对partial，价格／批准数量／结算unknown |
| 历史资产范围缺证 | [gap信封](../../interfaces/common-inputs/workbench-rule-gap.json) | [gap交接](../../interfaces/common-examples/workbench-rule-gap.json)：commercial、2025-12-30适用，gap／null版本；禁止用2025-12-31施行的新范围回填 |

两条采用schema_version=1.2、cn-market-rules.rule-handoff/1.0、目录schema_version=1.0，原文依据[REITS-EXP-SH-2022、REITS-EXP-SH](../sources.md)。知识日均2026-10-09，反例是现时回溯适用查询，不是宣称这些材料在2025-12-30已经可得的历史回测。主体为fund_manager，市场SSE，板块REITS；不从代码前缀补证券身份，未绑定实际代码时身份unknown。

## 可选、隔离调用

```sh
python /path/to/cn-market-rules/scripts/common_interface.py --input /path/to/workbench-rule-selected.json
python /path/to/cn-market-rules/scripts/common_interface.py --reverse --input /path/to/exported-common.json
```

以绝对路径运行，可从消费者目录调用；不要求联网、账户或跨库Python导入。消费端应限制返回大小、时限和已声明版本，保留原始交接，并以本次配置的生产者代码／目录版本核对；不能依赖不受控全局同名contracts模块。规则库不读取工作台持仓、账户或报告文件。

旧入口保留；schema1.3对应共用1.1的扩展已有独立例证，本次基本联调不代表消费端已支持所有1.1扩展。规则变更后重核返回属于新的判断，不静默覆盖旧交接或冻结报告。

## 消费者必须保留

| 字段 | 验收 |
|---|---|
| rule_selection.query | market／board／subject／asset_type、applicability_date及knowledge_date原样传递 |
| rule_selection | 状态、版本ID、文号、公布日、有效区间、source_id／locator、scope／reason和目录核验日原样保留 |
| source views | source_tier、access_requirement、acquisition_status和original_verification分别保留，公开／取得／核验日不合并 |
| facts | value原数值类型、unit、status、reason及证据不改；unknown仍null，hypothesis不升级original |
| dates／legacy_payload | 事件／观察／回测日期角色不合并；完整原信封无损恢复 |

selected只表示已登记版本匹配。gap、conditional、unknown、deferred、ambiguous均不得被改成资格通过；即使selected，价格／批准数量／结算缺证仍未完成个案核对。规则状态不代表收益、执行成功、审计或法律资格认证，报告必须并列显示版本层与项目层限制。

## 双端实际检查与有限范围

规则端测试通过：从外部临时目录运行公共CLI、不设置PYTHONPATH，两个场景导出等于已存交接，回转等于原信封；强行把gap改成selected时回转拒绝，不能静默纠正或降级。来源与冻结预览字节保持不变。

实际消费者联调已完成，见[联合回执](../../docs/workbench-integration-validation.json)：规则生产者b6389f0、工作台32e42b4，方法bounded-native-gateway-1。两条实际子进程消费结果全对象等于已存交接，同生产者回转等于原信封，目录指纹前后一致，三项unknown及项目partial／unknown保留。

消费者Markdown／HTML内容已核市场、板块、主体、资产类型、查询日期、公布／有效区间、来源定位以及“版本选择不等于资格通过”；未宣称浏览器视觉验收完成。gateway实际字节摘要38123e66d683441a226987ab00ed6c25941615d222eee3f6769f871302c14945，工作树与提交内容按LF换行规范对照相同，回执分别保留两种字节摘要。

本次只验收信封1.2／交接1.0的两个模板，不签署其他引擎等价或实际投资者资格。已有1.3／交接1.1例证由消费者明确拒绝且不产生结果目录；conditional／deferred／ambiguous在格式中保留状态语义，本次未逐一使用真实项目完成端到端验收。旧工作树试跑与801f224等中间产物冻结保留，最终回执另存，不能用旧摘要冒称最终源码。
