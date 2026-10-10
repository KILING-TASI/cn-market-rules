# 中国证券市场规则核对与情景计算



核对一条规则何时、对谁适用，再按公告条款和给定参数计算收益、资金占用与现金缺口。

[![原创代码 MIT](https://img.shields.io/badge/原创代码-MIT-green)](LICENSE)

## 统一安装与启动

本轮源码版本为 `2.1.1`。统一安装入口需要 Python 3.10 或以上。在完整源码目录新建自己的 Python 环境，下面的 Windows 命令不需要激活脚本：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\cn-market-rules.exe --help
.\.venv\Scripts\cn-market-rules.exe demo --out-dir reports/demo --auto-name
```

九个仓库都用仓库名启动；在已激活的环境中可以直接输入工具名。Linux/macOS 使用 `.venv/bin/python` 和 `.venv/bin/cn-market-rules`。教学结果写入当前工作目录；`--auto-name` 自动另选新名字，旧结果保留。不加该参数时，教学入口拒绝已有目录。`cn-market-rules run --help` 查看原生参数，原来的命令继续兼容。其他专题可用 `cn-market-rules script --help` 查看入口，以脚本名调用，不需要记住源码路径。pip 安装提供 CLI；作为 Skill 使用仍须保留完整源码及许可资源，不能只复制 SKILL.md。安装可能需要联网获取普通构建依赖；教学离线。下面保留原生入口及此前发行记录，本轮安装和版本以本节为准。


## 最短试用

需要 Python 3.10+，只用标准库，不需要账户、行情接口或其他项目。生成报告时不联网。在解压或克隆后的项目目录打开 PowerShell：

```powershell
python scripts/demo_preview.py --output-dir demo-output/first-rule-check
```

如果电脑使用 Python Launcher，将 `python` 换成 `py -3`。完成后打开 `demo-output/first-rule-check/index.html`；同时保存输入快照和三个 JSON 结果。目录已存在时换一个新名字，工具不会覆盖旧报告。

只看计算结果，也可以运行：

```powershell
python scripts/scenarios.py --input examples/scenarios.json
```

这些命令使用包内示例。真实个案需要另行提供价格、费用、资格、条款和资金到账依据。

## 看一份实际结果

![规则版本、公告证据与教学现金报告](docs/preview/overview.jpg)

[打开示例报告](docs/preview/index.html) · [查看输入与截图说明](docs/preview/README.md)

现金示例的期末余额为 **85,000 元**，途中最低 **5,000 元**，相对预设缓冲还差 **15,000 元**：下午退款不能解决上午的资金缺口。资金金额与支付、退款时点都是教学假设，不是实际账户或收益。

报告把规则版本、公告日期和未知项列在结果旁边；截图保留生成时的版本与日期。选中规则版本，只说明登记的适用范围匹配，不能据此认定项目或个人资格通过。

## 能做什么，哪些还需要另核

| 要解决的问题 | 当前源码支持 | 仍需核对 |
|---|---|---|
| 打新、转债、要约、换股与现金选择权 | 规则清单、个案条款表和参数计算 | 投资者权限、个券条款、行权窗口、税费与实际到账 |
| ST 摘帽与退市 | 五市场核心指标、主体例外和2024年衔接清单 | 具体上市标准、财务年度、特殊主体及交易所决定；不自动认定退市 |
| 公募 REITs 首发与扩募 | 沪深首发核对、三种扩募路径和条件算术 | 定价、审批、项目资格、资产调整与申报结果；首发和扩募不能混用 |
| 资金占用与缺口 | 逆回购日期推算、组合可用现金账本、压力时点 | 真实账户余额、退款可用时刻、异常交收和跨账户调拨 |
| 一条规则在什么日期适用 | 有限版本目录、市场与主体范围、来源及缺口 | 早期完整版本、历史首次公开时刻和目录未覆盖条款 |

金额用人民币，股数与基金份额分开；比例 `0.03` 表示3%。未知保留为空并说明原因，不填零；持仓市值不当作可用现金。2026年沪深日历来自官方常规休市安排，不外推2027年或临时停市。详细口径见[计算说明](references/calculations.md)。

## 独立使用与协作

本项目同时提供 **Skill资料和独立CLI**。仓库名、[SKILL.md](SKILL.md) 中的 `name`、建议目录名均为 `cn-market-rules`，两种入口可以并用。

作为Skill使用时，把完整目录放入对应环境的技能目录，例如 `~/.codex/skills/cn-market-rules/`。保留 scripts、references、rules、calendars、interfaces、examples、templates及许可文件，不要只复制SKILL.md。本轮已提供 pip 安装工程与独立 CLI；安装不会自动注册 AI 工具中的 Skill。

最短流程与机器接口只用标准库。PDF核读工具可另行选择，它们不是这些CLI的依赖；公告消费入口需要已合法保存的原件，原文PDF不随包提供。查找新资料需要联网，包内计算与报告生成可以离线运行。

规则库负责制度、版本、条款和给定条件计算；公司经营、公司事件时间轴与综合研究由[研究工作台](https://github.com/KILING-TASI/research-workbench)组织。工作台可以调用规则库，但规则库不依赖工作台安装，也不承担全量公司事件采集或评分。

个案可从[核对清单](templates/verification-checklist.md)、[条款表](templates/case-terms.md)和[收益情景模板](templates/scenario-analysis.md)开始。结果先写判断和条件，再列依据与未核项。

## 当前源码与旧发布包

main已集成规则补证、版本选择、报告、独立运行验收和情景实例等新增能力；源码与安装包版本为2.1.0，**[v2.1.0 Release已发布](https://github.com/KILING-TASI/cn-market-rules/releases/tag/v2.1.0)**。

[旧v2.0.0发布包](https://github.com/KILING-TASI/cn-market-rules/releases/tag/v2.0.0)保留原内容，不包含后来新增的全部能力和当前许可范围文件。上面的试用命令面向当前源码，旧包的入口以它自己的README为准。不要把当前源码的验证或许可追溯套用到旧包。

软件、接口、规则文件与数据日期各有不同含义；职责、入口、实际验收和剩余缺口集中见[仓库状态说明](docs/repository-status.md)。其中历史批次的“PR待审”记录对应当时状态，原PR #1现已集成main。

安装步骤见[版本说明](docs/release-v2.1.0.md)。下载[完整Skill ZIP](https://github.com/KILING-TASI/cn-market-rules/releases/download/v2.1.0/cn-market-rules-v2.1.0.zip)和[SHA256清单](https://github.com/KILING-TASI/cn-market-rules/releases/download/v2.1.0/cn-market-rules-v2.1.0.sha256)。

## 验证、来源与许可

当前有171项单元测试及29个代表情景。情景通过实际命令保存输入、独立预期和结果，覆盖版本更替、主体范围、资格缺证、冻结退款、REITs路径与交易／交收日期区别：

```powershell
python scripts/run_scenario_acceptance.py --output-dir demo-output/scenario-check
```

输出目录同样须为新目录。[情景索引](references/scenario-index.json)列出每例依据与通过范围；CI只检出本仓，在独立虚拟环境运行源码归档。教学通过不代表真实账户、自然语言Skill发现或视觉验收通过。

- [来源台账](references/sources.md)、[证据规范](references/evidence-standard.md)：原发布者、获取与原文核验分开，下载成功不等于语义核验。
- [版本契约](references/interfaces/rule-version-contract.md)、[数据交接说明](references/interfaces/common-handoff-contract.md)：保留日期角色、原字段和未知项，不静默换版本或口径。
- [规则核对示例](docs/regulatory-preview/README.md)、[方法说明](references/method-rule-applicability.md)：查看有限公告材料与人工核对边界。
- [MIT许可证](LICENSE)、[逐文件范围](LICENSE_SCOPE.json)、[第三方说明](THIRD_PARTY_NOTICES.md)：有权许可的原创代码及说明采用MIT；第三方原文、公告、数据与未明来源材料的权利独立，不因代码许可获得再分发或商用授权。

本工具用于规则核对与研究教学，不执行交易，也不替代法律、税务或投资资格判断。
