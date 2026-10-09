# 规则与现金结果预览

这份 [HTML 报告](index.html)由本库实际执行既有入口生成；v2.1.0 候选、PR #1 待审，规则核验日期 2026-10-09。main 已发布 v2.0.0，本预览尚未发布为新 Release。

| 预览内容 | 输入 | 结果与限制 |
|---|---|---|
| 沪市扩募版本 | [查询输入](inputs/rule-query.json) | [选择结果](rule-selection.json)为 SSE-REITS-EXP-2025，替代旧版；仅选版本，不认证个案资格 |
| 问询／更正 | [事件输入](inputs/event-evidence.json) | [结构核对](event-evidence.json)：2 条公开公告摘取、6 个未知字段；首次上网时刻和旧挂网版本仍缺 |
| 现金占用 | [教学输入](inputs/cash-ledger.json) | [原算术结果](cash-scenario.json)：期末 85,000.00 元，最低 5,000.00 元，缓冲缺口 15,000.00 元；均为虚构教学资金／时刻，非实际收益 |

截图来自这份报告的浏览器实际渲染，已视觉检查中文、完整卡片、版本／日期和教学标识。未使用 AI 生成截图或补造内容。

- [规则与事件截图](overview.jpg)：保留报告版本、生成日期、适用区间、原文定位及未知项。
- [教学现金截图](cash.jpg)：保留版本、日期、金额单位、教学假设及缓冲边界。
- [完整页面截图](fullpage.jpg)：含来源核验和主工作台问题入口。

截图捕获方法、报告／图片哈希见 [截图记录](screenshot-manifest.json)。输入与生成说明见 [报告记录](report-manifest.json)；哈希只验证对应字节，不认证来源真实性或许可。

## 一条命令生成新报告

在仓库根目录，使用 Python 3.10+ 标准库：

```sh
python scripts/demo_preview.py --output-dir demo-output/first-rule-check
```

打开 `demo-output/first-rule-check/index.html`。同时取得三个 JSON 结果、输入快照和 report-manifest.json。输出目录必须不存在，重复执行会拒绝覆盖；再生成请改目录名。Git 可选，仅用于附生成时基线提交；浏览器用于打开 HTML，生成器不联网、无额外包依赖。

截图是已检查的静态展示；demo 命令生成 HTML／JSON，不自动操控或安装截图浏览器。JSON 和原终端入口独立可用。原公告全文、付费数据、账户和字体文件未打包；第三方来源／名称的权利不由本库授予。

继续研究：[主工作台按问题选择入口](https://github.com/KILING-TASI/research-workbench/blob/main/references/practical-entry.md)。本报告未新增自动消费端或经营估值。
