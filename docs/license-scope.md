# 原创 MIT 与排除范围清单

日期：2026-10-09。用户明确授权本仓库原创代码及有权许可的原创说明采用 MIT。已核仓库维护者标识为 KILING-TASI；不猜测自然人身份或第三方法律权利人。根许可证使用标准 MIT 文本，范围限定在此说明与逐文件台账中，不改写第三方许可。

| 范围 | 当前处理 | 依据／限制 |
|---|---|---|
| scripts、tests、工作流与自编配置 | original_mit | 本次独立实现，原 ZIP 无脚本；未内置第三方代码，保留 SPDX 标识 |
| 新增契约、说明与空白模板 | original_mit | 新增原创结构与解释；不授予引用的第三方材料权利 |
| 原包同路径 14 篇专题、SKILL.md | excluded_pending_rights | 已重写核对，但不凭比较结果宣称整文件原创／已获原包授权；文件内标注，不整篇转授 MIT |
| docs/upgrade-v2.1.md | excluded_pending_rights | 来自用户提供方案的改建设计，附件权利未认证，不整篇转授 |
| 规则目录、公告例证、日历、来源台账及预览数据 | mixed_source_data | 仅原创结构／解释适用 MIT，第三方材料及数据访问／再分发权排除 |
| 实际报告 HTML／JPEG | mixed_source_data | 自编界面与原创部分可许可，嵌入的第三方成分排除；没有字体或原文全文 |
| 原 ZIP、官方全文、账户／付费资料、第三方库／字体 | not_distributed | 本次未附；不在根 MIT 授权内 |

[逐文件台账](../LICENSE_SCOPE.json)包括所有分发文件，新增未分类文件会使分发检查失败。original_mit 不表示其中引用的事实、名称或来源材料成为维护者所有；mixed_source_data 不作为全部数据授权。许可证目录见 [licenses](../licenses/README.md)。

原包检查方法：读取 17 份 Markdown，仅在本地比较长整行表达；没有 ≥60 字符归一化整行命中。此结果只说明此项检测未命中，不能证明改建文本不含未明表达。保守排除范围不会因此解除。原 ZIP 和设计附件不放入发布包。

运行 `python scripts/audit_distribution.py` 检查范围台账、原创脚本 SPDX、允许资源、外部代码导入及不应附带文件；`python scripts/validate_package.py` 同时验证链接、例子、截图／报告哈希。检查不认证全部外部权利，不自动授予数据商用权。

本次不会创建 Python 包元数据冒充已有安装工程：仓库没有 pyproject/package 配置，技能元数据注明 MIT-original-parts-only。候选安装包包含 LICENSE、THIRD_PARTY_NOTICES、LICENSE_SCOPE、licenses 目录及当前 README。main v2.0.0 已有发布状态不被追溯改写；新增许可与预览随 PR #1 待审，不自动合并或发布 Release。
