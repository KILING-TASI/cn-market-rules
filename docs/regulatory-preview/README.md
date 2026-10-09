# 规则核对示例

本库主线是制度、有效版本、条款核对与给定条件情景计算。公司事件时间轴、关联检索与研究解释由 research-workbench 承接；本页仅保留有限的规则适用与证据缺口示例，不扩展为全量事件库、采集器或评分平台。

这是新的 [HTML 阅读页](index.html)，复用已有规则选择与证据接口，不覆盖此前 [规则／现金冻结预览](../preview/README.md)。v2.1.0 候选、PR #1 待审；资料核验截止 2026-10-09。

四条真实材料摘取：问询公告、标题更正、官方通知援引处罚、财务无保留审计意见。三条关联规则版本仍有缺口；处罚决定原件未取得。只核公开文件日，首次上网精确时刻未知；问询／整改不当处罚、非标不当造假。

## 生成、筛选与另存

Python 3.10+ 标准库，无额外包、账户或联网采集：

```sh
python scripts/regulatory_reader.py --output-dir demo-output/regulatory-check-1
```

打开新目录里的 index.html，用现代浏览器按类型、证据容器状态和关联规则缺口筛选，按公开日升降序排序；未知公开日永远在末尾。空筛选只说明这个小样本没有匹配，不能判断全市场不存在该类事件。

点击“另存当前筛选结果与输入”得到新的 reader-session 时间戳 JSON，含完整原输入、原字节摘要、参数、输入接口版本、共用交接版本与方法 regulatory-reader/1.0。浏览器仅下载新文件，不修改冻结 HTML 或数据。生成时也保存 [输入](input.json)、[结果](result.json)、[共用交接](common-handoff.json)、[初始筛选快照](reader-session.json)及[生成记录](report-manifest.json)。

CLI 可沿用已保存的快照，必须同一输入摘要和方法／接口版本：

```sh
python scripts/regulatory_reader.py --settings saved-reader-session.json --output-dir demo-output/regulatory-check-2
```

输出目录须不存在；变更输入或方法会拒绝静默恢复旧快照。Node 仅用于可选开发对照测试，生成和浏览均不要求安装 Node。JSON 与原命令仍独立可用。

## 边界与来源

“证据容器取得”对应其 evidence_kind：收到问询公告已得，不能改写成问询原函已得；交易所正式通知已核，不能改写成处罚决定全文已核。审计报告在年报内嵌取得，只记录财务领域意见，不推导内控意见、处罚或造假。

接口见[类型／版本契约](../../references/interfaces/regulatory-event-contract.md)；来源见[台账](../../references/sources.md)。页面只包括本库自编结构与必要事实，不附原文全文、账户、缓存或付费材料；原创代码 MIT、第三方资料权利独立。现有示例仍缺处罚原件、旧更正原版本与精确首发时刻；不以补全事件类型作为本库建设目标。
