# 官方通知派生交易日历

核验2026-10-09。2026-SSE与2026-SZSE分别从[年度休市通知](2026-holiday-notice.md)生成完整常规A股交易日：周一至周五减法定休市区间，调休工作的周末仍休市。这是按公告安排派生的日历，未核验临时异常停市，不是港股通、海外或基金业务日历。

```sh
python scripts/scenarios.py --input examples/repo-with-calendar.json --calendar calendars/2026-SSE.json
```

外部日历与输入内trading_days/calendar_source/calendar_start/calendar_end不能并用；提供market时必须匹配。原有内嵌交易日数组仍有效。覆盖2026-01-01—2026-12-31，仅表示这些日期的交易日安排；回购到期或下一交收跨2027时仍拒绝外推。未发布2027官方安排时不创建虚构下一年度日历。

每份JSON记录公布日、核验日、来源ID/URL、market、coverage与trading_days。以后临时休市/年度通知变动时重核并更新；截止日之后日期属于已公布计划，不声称已实际开市。用户自备日历仍须对完整性负责。工具只能验证结构，不能发现所有漏日。
