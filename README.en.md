# Chinese market rule evidence and scenarios

Review selected rule versions, evidence and declared scenarios. Includes bounded dividend-tax, fund-limit and liquidity checks; partial data cannot certify institutional compliance.

[中文说明](README.md) · [Release v2.2.4](https://github.com/KILING-TASI/cn-market-rules/releases/tag/v2.2.4) · [Skill instructions](SKILL.md) · [Input preparation](BEGINNER.md)

Current release: **v2.2.4 · regular release**. Python **3.10+**. Base runtime dependencies: none.

## First run

Download the [complete source ZIP](https://github.com/KILING-TASI/cn-market-rules/releases/download/v2.2.4/cn-market-rules-v2.2.4-source.zip), extract it and enter the directory containing `try_demo.py`:

```console
python try_demo.py --no-open --out-dir reports/first-demo
```

Alternatively, clone `https://github.com/KILING-TASI/cn-market-rules.git`, run `cd cn-market-rules`, then execute the command above. Open the report at the path printed by the command. Teaching data is synthetic; use a new output directory and keep prior reports.

## CLI and Skill

From the source directory:

```console
python -m pip install .
cn-market-rules --help
```

Repository and distribution: `cn-market-rules`. Primary CLI: `cn-market-rules`. Skill name in SKILL.md: `cn-market-rules`. Installing the CLI does not register the Skill; configure the complete resources in an assistant that supports local Skills. Build or optional dependencies may require network access during installation.

## Scope and rights

Read the [Chinese capability boundaries](README.md#能力与边界) and [detailed commands](USAGE.md). Each tool can run independently; cross-tool calls need explicit configuration. Successful execution does not authenticate source documents, fill missing data or establish investment validity. No trade execution or guaranteed returns.

Original code uses MIT. Third-party code and documents/data retain their own licenses and rights. Default-branch documentation edits do not rewrite released archives or frozen results.

[Changes](CHANGELOG.md) · [Third-party rights](THIRD_PARTY_NOTICES.md) · [Contribution](CONTRIBUTING.md) · [Security](SECURITY.md)
