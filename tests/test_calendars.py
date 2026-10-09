# SPDX-License-Identifier: MIT
from test_scenarios import s
import unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]

class CalendarTests(unittest.TestCase):
    def case(self,**changes):
        d=dict(mode='repo',market='SSE',trade_date='2026-02-12',tenor_days=1,
               principal=100000,annual_rate='.03',total_fees=1)
        d.update(changes);return d
    def cal(self,market='SSE'):
        return s.load_calendar(ROOT/'calendars'/f'2026-{market}.json')
    def test_external_equivalent_to_embedded(self):
        c=self.cal();a=s.calculate(s.apply_calendar(self.case(),c));b=s.calculate({**self.case(),**c})
        self.assertEqual(a,b)
        self.assertEqual(a['interest_days'],11)
    def test_last_preholiday_one_day(self):
        r=s.calculate(s.apply_calendar(self.case(trade_date='2026-02-13'),self.cal()))
        self.assertEqual(r['interest_days'],1)
        self.assertEqual(r['first_settlement_date'],'2026-02-24')
    def test_embedded_any_calendar_field_conflicts(self):
        for field,value in [('trading_days',[]),('calendar_source','custom'),('calendar_start','2026-01-01'),('calendar_end','2026-12-31')]:
            with self.subTest(field=field),self.assertRaises(ValueError):s.apply_calendar(self.case(**{field:value}),self.cal())
    def test_market_mismatch(self):
        with self.assertRaises(ValueError):s.apply_calendar(self.case(),self.cal('SZSE'))
    def test_cross_year_rejected(self):
        with self.assertRaises(ValueError):s.calculate(s.apply_calendar(self.case(trade_date='2026-12-31'),self.cal()))
    def test_outside_coverage(self):
        with self.assertRaises(ValueError):s.calculate(s.apply_calendar(self.case(trade_date='2027-01-05'),self.cal()))
    def test_working_weekend_still_closed(self):
        days=self.cal()['trading_days']
        for d in ['2026-01-04','2026-02-14','2026-02-28','2026-05-09','2026-09-20','2026-10-10']:
            self.assertNotIn(d,days)
        self.assertIn('2026-10-08',days)
    def test_two_markets_independent_sources_same_notice_dates(self):
        a,b=self.cal(),self.cal('SZSE')
        self.assertEqual(a['trading_days'],b['trading_days'])
        self.assertNotEqual(a['calendar_source'],b['calendar_source'])
    def test_mixed_batch_only_repo_injected_input_unchanged(self):
        r=self.case();cash=dict(mode='cash',timezone='Asia/Shanghai',initial_available_cash=1,minimum_buffer=0,events=[])
        doc={'cases':[r,cash]};result=s.run(s.apply_calendar(doc,self.cal()))
        self.assertEqual(len(result['results']),2)
        self.assertNotIn('trading_days',r)
    def test_unused_calendar_rejected(self):
        with self.assertRaises(ValueError):s.apply_calendar({'mode':'cash'},self.cal())
    def test_calendar_holiday_date_consistency(self):
        from datetime import date
        days=self.cal()['trading_days']
        self.assertEqual(len(days),len(set(days)))
        self.assertTrue(all(date.fromisoformat(d).weekday()<5 for d in days))
        for closed in ['2026-01-01','2026-02-23','2026-04-06','2026-05-05','2026-06-19','2026-09-25','2026-10-07']:
            self.assertNotIn(closed,days)

if __name__=='__main__':unittest.main()
