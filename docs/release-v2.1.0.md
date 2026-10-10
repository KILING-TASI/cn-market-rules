# v2.1.0 发布说明与安装

本文件为待发布说明，候选软件版本2.1.0。源码功能已集成main；新标签和资产由总调度审合后统一发布，现有Release仍为v2.0.0，不提前宣称新包已可下载。

本版可核对五市场退市核心条款与年度衔接、沪深REITs首发和扩募、规则有效版本，并生成教学资金报告。保留未知资格与证据缺口，补充中文入口、失败下一步和逆回购日历阶段诊断。规则选择不认证个人资格，教学不代表真实收益。

发布后下载入口：[v2.1.0 Release](https://github.com/KILING-TASI/cn-market-rules/releases/tag/v2.1.0)。拟提供完整源码Skill ZIP及SHA256，不提供wheel或sdist：本项目没有Python包安装工程。

将ZIP解压到一个新目录，核对资产SHA256后，在该目录打开PowerShell。需要Python3.10+，无需第三方库、联网、账户或其他自家项目：

```powershell
python scripts/demo_preview.py --output-dir demo-output/first-rule-check
```

若电脑使用Python Launcher，可改为 `py -3`。完成后打开 `demo-output/first-rule-check/index.html`。已有输出目录请换新名字，不覆盖历史结果。源码克隆目录使用同一命令。

如需作为Skill使用，将完整目录放入对应环境的技能目录 `cn-market-rules`，保留SKILL.md及全部资源；本次发布准备不会自动修改现有安装。CLI运行通过不代表自然语言Skill发现或视觉通过。

最短示例现金结果：期末85000元、最低5000元、缓冲缺口15000元，全部为教学参数。29个情景由独立CLI验收；171项单元测试、资源链接与许可范围检查由CI核对。历史截图和结果文件保留生成时版本，不改成新版本冒充重新验收。

ZIP不附原文PDF、账户、付费资料或作者缓存。原创部分MIT和第三方数据权利分开，以LICENSE_SCOPE.json及THIRD_PARTY_NOTICES.md为准。接口、规则目录和计算方法版本保持原值；旧v2.0.0发布包、标签与历史授权不追溯改写。
