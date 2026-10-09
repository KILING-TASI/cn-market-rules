# cn-market-rules

中国大陆证券市场的规则核对、个案条款与收益情景工具。**v2.1.0 · 核验截止日 2026-10-09**。

从原来的18份Markdown知识包改建：修正硬规则，新增ST摘帽与退市、REITs发售、组合现金联动；把可复用知识与个案参数分开，并加入离线计算与来源台账。

v2.1按[修订设计](docs/upgrade-v2.1.md)分批落地：补三只转债阶段违约原文；新增下修增量摊薄；补科创/创业核心指标；深市首发与沪市三路径扩募；两市2026官方通知派生日历。59项算术/边界测试通过，未核范围见[案例缺口](references/cases/evidence-gaps.md)及[PLAN](PLAN.md)。

## 从哪里开始

- 人阅读：打开 [SKILL.md](SKILL.md)，按专题导航。
- 研究个案：复制 [核对清单](templates/verification-checklist.md)、[个案条款表](templates/case-terms.md)、[收益情景模板](templates/scenario-analysis.md)，逐项绑定公告原文。
- 看有依据的示范：[个案原文核验](references/cases/verified-examples.md)。真实案例只用于演示条款摘取；未来市场价格和收益使用独立的虚构情景。
- 算术演示：Python 3.10+，无需第三方库、行情接口或账户授权。

```sh
python scripts/scenarios.py --input examples/scenarios.json
python scripts/scenarios.py --input examples/scenarios.json --output result.json
python scripts/scenarios.py --input examples/cash-ledger.json
python scripts/scenarios.py --input examples/dilution.json
python scripts/scenarios.py --input examples/expansion.json
python scripts/scenarios.py --input examples/repo-with-calendar.json --calendar calendars/2026-SSE.json
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

作为Agent技能使用时，将整个仓库目录放入相应环境的技能目录，例如Codex的 `~/.codex/skills/cn-market-rules/`。安装不自动执行脚本、不调用券商、不发送交易。

## 已纠正的关键问题

深市IPO参与门槛与申购单位分开；科创板盘后交易不混入IPO申购；股票印花税按减半政策；可转债买入单位与转股单位分开；新增可转债适当性约束；下修净资产限制逐券核对；逆回购周五一天期与节前末日计息重算；30%要约路径、履约保证替代安排、退市股权分布与现金选择权资格重写。

REITs回拨的现行单位是**70%**，不是70‰。已核对现行《发售业务指引》第45条和上交所投教手册第20问。该比例的分母是**扣除战略配售后的公开发售份额**。完整修订记录见 [CHANGELOG.md](CHANGELOG.md)。

## 覆盖与限制

| 专题 | 已交付 | 边界 |
|---|---|---|
| IPO与转债 | 规则、清单、计算 | 市值/行情、个券条款及券商时限由使用者取得 |
| 事件研究 | 要约、换股、现金选择权、重组窗口 | 股东资格、价格调整、税务、到账逐案确认 |
| ST与退市 | 沪深主板＋科创/创业2026核心指标及撤销路径 | 北交所当前正文取得失败留待核；非财务例外仍按个案读原文 |
| REITs发售 | 沪深首发失败模型、资格/战配/配售对照；沪市独立三路径扩募 | 深市扩募不支持；定价、审批及身份不由算术工具认证 |
| 下修/日历 | 旧/新转股价增量摊薄；两市2026公告派生常规日历 | 静态EPS非预测，2027及临时异常停市未核，不外推 |
| 组合联动 | 可用/可取/冻结区分，压力日历与现金缺口 | 不自动取券商余额，不假设申购退款立即可用 |

数据不全时可交付已核对部分与缺口，不将缺值当零，不以持仓市值充当现金。情景中的概率、价格、费率和日期属于假设，不是行情预测。年化换算不是可重复收益。

## 来源与维护

[来源台账](references/sources.md)记录官方网址、条款、版本、生效信息和核验状态；[证据规范](references/evidence-standard.md)定义冲突与更新流程。`references/source-retrieval.json`只记录本次取得文件的哈希和状态，不包含原文全文；哈希只证明取得文件身份，不证明规则完整或永远有效。

原始输入为CodeBuddy署名的v1.0.0知识包，原包未附许可证；本次重写保留来源说明，不据此授予原包或第三方材料的再许可。法规、交易所文件及公司/基金公告链接到原发布者，未打包其全文。仓库未设置第三方材料的开源授权，公开可访问不等于任意再许可。

内容用于研究参考，不构成收益保证或交易指令。维护状态与未核验项见 [PLAN.md](PLAN.md)。

## 风险事件证据首批

[设计与验收](docs/risk-evidence-roadmap.md)、[解禁/质押/商誉核对](references/rules/risk-event-evidence.md)及[字段接口](references/interfaces/evidence-contract.md)已提供。三条历史案例区分公告全文、官方摘要和监管认定；未形成全市场数据库。

运行 `python scripts/evidence_interface.py --input interfaces/examples/risk-events.json` 或 `interfaces/examples/reits-terms.json` 校验字段。扩募接口向主工作台交接条款与缺口，经营现金流估值仍由主工作台补齐。
