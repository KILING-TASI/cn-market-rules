# 包内共用规则交接契约 1.0／1.1

schema_version为1.0/1.1/1.2的旧输入保持cn-market-rules.rule-handoff/1.0；显式schema1.3采用交接1.1并保留regulatory_event扩展。本库可独立安装和离线调用，不依赖研究工作台或各引擎。此版本为本仓库维护的交接契约；已完成[有界联调](workbench-integration.md)的信封1.2／交接1.0两条selected与gap模板的实际消费、回转及报告内容核对；不是全部契约或引擎等价。

## 职责及兼容入口

本库权威维护来源、规则版本和适用区间，输出已选版本/证据/缺口。证券主档、行情、账户资金、经营估值及交易计算分别由对应工作台/引擎维护。本批包内模块为scripts/contracts的identity、units、common；新入口scripts/common_interface.py只作交接适配。旧evidence_interface.py、rule_versions.py和scenarios.py保留，原命令和算法不移动、不删除。

转换输入为本库已有证据信封，不是任意工作台持仓表或scenarios计算输入。单位解释、日期角色、unknown、版本绑定在本地定义；未来消费端需要显式采用此contract_version或另写版本适配，不可按字段同名默认兼容。

## 共用字段

| 字段 | 语义/处理 |
|---|---|
| security_identity | code字符串保留前导零，market/board/security_type/name分别明确；unknown/partial/original及证据；主体名不能替证券简称，代码前缀不能替市场 |
| facts / unit_semantics | 原value、unit、status、reason、证据不改；ratio是0—1分数，shares与基金units分开，CNY标币种；未映射原单位原样保留，不自动转万股、百分数或做舍入 |
| dates | 公布published_at、事件event_date、观察observation_date、取得retrieved_at、核验verified_at分别传；生效/失效区间在rule_selection中；日期采用中国UTC+08:00日界线，时间戳保留原时区文本 |
| source_version / rule_version_id | 来源文号/版本原样保留，已选规则目录版本另列，不混作网页迁移时间或程序版本 |
| verification | 获取成功与上游原文核验独立；旧v1.0无分层元数据时置null、列missing_metadata，不推断verified |
| unknown | 保留null及理由，不改0；已知零保留原status，hypothesis不升级原文事实 |
| legacy_payload | 完整原信封，无损回转依据；新视图不能覆盖它，互不一致拒绝回转 |

证券身份没有完整原文时可以partial，不要求为了格式编造市场/板块。original身份要求全字段、引用已核原文；结构通过仍不是证券主档认证。额外旧字段全部保留在legacy_payload。通用视图是可复核适配输出，不是自动接受修改的双向编辑模型。

## 转换示例

[原输入](../../interfaces/common-inputs/identity-partial.json)与[转换结果](../../interfaces/common-examples/identity-partial.json)使用同一证据、日期和版本。协鑫能科代码002015及简称由公告核对，市场/板块仍null；质押比例0.5096没有变成50.96、3000万解除与再质押不相加。

```sh
python scripts/common_interface.py --input interfaces/common-inputs/identity-partial.json
python scripts/common_interface.py --reverse --input interfaces/common-examples/identity-partial.json
```

程序调用：将本包scripts加入模块搜索路径后，调用contracts.common.to_common/from_common。输入输出均为JSON对象；不读取其它仓库，不回传工作台文件，也不发送消息。

## 对照与未等价范围

所有原示例经过输入→共用视图→原输入，按相同schema版本对照校验结果。小数文本、数值类型、真实0、unknown理由、单位、费用假设、时间戳和规则选择不变；回转遇到新视图数值/类型被改会拒绝。金钱字符串不转float，不新增舍入或费率默认值。现有情景计算模块无迁移，原59项情景/日历基线继续回归。

尚未迁移工作台内部证券主档/单位转换、各引擎输入/收益计算、授权数据、实时采集与历史回测。未来迁移须以同一输入、口径和版本对照旧实现；没有独立等价实现的功能保留旧入口。经营REITs估值继续由工作台完成，规则选择结果不能代替经营模型。
