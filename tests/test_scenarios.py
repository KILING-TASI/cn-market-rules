import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('scenarios', Path(__file__).parents[1] / 'scripts/scenarios.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

class ScenariosTest(unittest.TestCase):
    def tender(self, **changes):
        case = dict(mode='tender', quantity=1000, buy_price=10, offer_price=12,
                    accepted_ratio='0.5', residual_exit_price=8, total_fees=0,
                    holding_days=30, annual_opportunity_rate=0)
        case.update(changes)
        return s.calculate(case)

    def offering(self, **changes):
        case = dict(mode='reits', market='SSE', offering_type='initial', registered_units=100_000_000,
                    final_units=80_000_000, strategic_units=24_000_000, offline_units=39_200_000,
                    raised_funds=200_000_000, investors=1000, originator_compliant=True,
                    other_failure_condition=False)
        case.update(changes)
        return s.calculate(case)

    def repo(self, **changes):
        case = dict(mode='repo', trade_date='2026-10-15', tenor_days=1, principal=100000,
                    annual_rate='.03', total_fees=1, calendar_source='synthetic test weekdays',
                    calendar_start='2026-10-12', calendar_end='2026-10-20',
                    trading_days=['2026-10-12','2026-10-13','2026-10-14','2026-10-15',
                                  '2026-10-16','2026-10-19','2026-10-20'])
        case.update(changes)
        return s.calculate(case)

    def test_tender_residual_can_erase_spread(self):
        self.assertEqual(self.tender()['net_pnl'], '0.00')
        self.assertEqual(self.tender(residual_exit_price=7)['net_pnl'], '-500.00')

    def test_tender_fee_and_time_erode_profit(self):
        self.assertEqual(self.tender(accepted_ratio=1,total_fees=20,holding_days=365,
                                     annual_opportunity_rate='.03')['net_pnl'], '1680.00')

    def test_full_tender_no_residual_break_even(self):
        self.assertIsNone(self.tender(accepted_ratio=1)['break_even_residual_price'])

    def test_reits_exact_boundaries_pass(self):
        r=self.offering()
        self.assertFalse(r['failure_condition_detected'])
        self.assertEqual(r['offline_ratio'], '0.700000')

    def test_reits_70_permille_fails(self):
        self.assertTrue(self.offering(offline_units=3_920_000)['failure_checks']['offline_below_70_percent_of_nonstrategic'])

    def test_reits_fail_each_red_line(self):
        for changes in [dict(final_units=79_999_999),dict(raised_funds=199_999_999),dict(investors=999),
                        dict(originator_compliant=False),dict(other_failure_condition=True)]:
            with self.subTest(changes=changes):
                self.assertTrue(self.offering(**changes)['failure_condition_detected'])

    def test_reits_unknown_compliance_rejected(self):
        with self.assertRaises(ValueError): self.offering(originator_compliant=None)

    def test_reits_all_strategic_rejected(self):
        with self.assertRaises(ValueError): self.offering(strategic_units=80_000_000,offline_units=0)

    def test_reits_expansion_not_silently_initial(self):
        with self.assertRaises(ValueError): self.offering(offering_type='expansion')

    def test_repo_thursday_three_days(self):
        r=self.repo()
        self.assertEqual(r['interest_days'],3)
        self.assertEqual(r['gross_interest'],'24.66')
        self.assertEqual(r['funds_available_date'],'2026-10-16')

    def test_repo_friday_one_day(self):
        r=self.repo(trade_date='2026-10-16')
        self.assertEqual(r['interest_days'],1)
        self.assertEqual(r['funds_withdrawable_date'],'2026-10-20')

    def test_repo_holiday_last_day_not_zero(self):
        r=self.repo(trade_date='2026-10-16',calendar_end='2026-10-28',
                    trading_days=['2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16','2026-10-27','2026-10-28'])
        self.assertEqual(r['interest_days'],1)

    def test_repo_holiday_penultimate_spans_break(self):
        r=self.repo(calendar_end='2026-10-28',
                    trading_days=['2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16','2026-10-27','2026-10-28'])
        self.assertEqual(r['interest_days'],11)

    def test_repo_long_tenor_uses_calendar_days(self):
        r=self.repo(trade_date='2026-10-12',tenor_days=7)
        self.assertEqual(r['maturity_clearing_date'],'2026-10-19')
        self.assertEqual(r['interest_days'],7)

    def test_repo_calendar_not_extrapolated(self):
        with self.assertRaises(ValueError): self.repo(trade_date='2026-10-19')

    def test_repo_nontrading_date_rejected(self):
        with self.assertRaises(ValueError): self.repo(trade_date='2026-10-17')

    def test_cash_same_instant_debit_first(self):
        r=s.calculate(dict(mode='cash',timezone='Asia/Shanghai',initial_available_cash=100,minimum_buffer=0,
            events=[dict(at='2026-10-12T09:00:00',name='refund',amount=100,source='hypothesis',cash_state='available'),
                    dict(at='2026-10-12T09:00:00',name='payment',amount=-150,source='hypothesis',cash_state='available')]))
        self.assertEqual(r['final_cash'],'50.00')
        self.assertEqual(r['maximum_cash_shortfall'],'50.00')

    def test_pending_refund_is_not_cash(self):
        with self.assertRaises(ValueError):
            s.calculate(dict(mode='cash',timezone='Asia/Shanghai',initial_available_cash=0,minimum_buffer=0,
                events=[dict(at='2026-10-12T09:00:00',name='refund',amount=100,source='hypothesis',cash_state='pending')]))

    def test_clause_segmented_price_and_strict_comparison(self):
        r=s.calculate(dict(mode='clause',window=3,required_hits=2,threshold='1.3',comparison='ge',
            dates=['2026-10-12','2026-10-13','2026-10-14'],prices=[13,12,13],conversion_prices=[10,9,11]))
        self.assertEqual(r['window_hits'],2)
        self.assertEqual(r['trailing_consecutive_hits'],0)

    def test_st_one_yuan_boundary_not_below(self):
        r=s.calculate(dict(mode='clause',window=3,required_hits=3,threshold=1,comparison='lt',
            dates=['2026-10-12','2026-10-13','2026-10-14'],prices=['.9','1','.9'],conversion_prices=[1,1,1]))
        self.assertEqual(r['trailing_consecutive_hits'],1)
        self.assertFalse(r['required_hits_reached'])

    def test_reits_zero_allocation_has_no_invented_profit(self):
        r=s.calculate(dict(mode='reits_return',subscription_amount=100000,offering_price=5,
            allocation_ratio=0,exit_price=6,cash_distributions=0,total_fees=0,capital_days=500000,
            annual_opportunity_rate='.03'))
        self.assertEqual(r['net_pnl'],'-41.10')
        self.assertIsNone(r['return_on_allocated_cost'])

    def test_exit_asset_value_not_reported_as_cash(self):
        r=s.calculate(dict(mode='exit',invested_cost=1000,exit_cash=0,residual_asset_value=900,
            total_fees=0,holding_days=0,annual_opportunity_rate=0))
        self.assertEqual(r['cash_received'],'0.00')
        self.assertEqual(r['net_pnl'],'-100.00')

    def test_merger_calculation(self):
        r=s.calculate(dict(mode='merger',quantity=1000,buy_price=10,exchange_ratio='.5',actual_converted_shares=500,
            survivor_exit_price=22,tail_cash_adjustment=0,total_fees=10,holding_days=0,annual_opportunity_rate=0))
        self.assertEqual(r['net_pnl'],'990.00')

    def test_merger_tail_not_double_counted(self):
        r=s.calculate(dict(mode='merger',quantity=3,buy_price=10,exchange_ratio='.5',actual_converted_shares=1,
            survivor_exit_price=22,tail_cash_adjustment=11,total_fees=0,holding_days=0,annual_opportunity_rate=0))
        self.assertEqual(r['net_pnl'],'3.00')

    def test_merger_actual_allocation_not_guessed(self):
        with self.assertRaises(ValueError):
            s.calculate(dict(mode='merger',quantity=3,buy_price=10,exchange_ratio='.5',
                survivor_exit_price=22,tail_cash_adjustment=11,total_fees=0,holding_days=0,annual_opportunity_rate=0))

    def test_missing_numeric_or_nonfinite_rejected(self):
        for value in [None,True,'NaN','Infinity']:
            with self.subTest(value=value),self.assertRaises(ValueError): self.tender(buy_price=value)

    def test_probability_not_inferred(self):
        self.assertNotIn('expected_return',self.tender())

if __name__ == '__main__': unittest.main()
