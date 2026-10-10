# SPDX-License-Identifier: MIT
from test_scenarios import s
import unittest

class DilutionTests(unittest.TestCase):
    def case(self, **changes):
        data=dict(mode='dilution',outstanding_principal=100_000_000,
                  old_conversion_price=20,new_conversion_price=10,existing_shares=100_000_000,
                  net_profit_ttm=100_000_000,underlying_price=12,conversion_fraction=1)
        data.update(changes)
        return data

    def test_additional_not_total_dilution(self):
        r=s.calculate(self.case())
        self.assertEqual(r['theoretical_new_shares_old_price'],'5000000.000000')
        self.assertEqual(r['additional_shares_due_to_revision'],'5000000.000000')
        self.assertEqual(r['dilution_ratio_new_price'],'0.090909')
        self.assertEqual(r['additional_dilution_ratio'],'0.043290')
        self.assertEqual(r['positive_profit_eps_compression_ratio'],'0.045455')
        self.assertEqual(r['conversion_value_uplift_ratio'],'1.000000')
        self.assertIsNone(r['adjusted_eps_new_price'])

    def test_loss_does_not_report_positive_profit_compression(self):
        r=s.calculate(self.case(net_profit_ttm=-100_000_000))
        self.assertIsNone(r['positive_profit_eps_compression_ratio'])
        self.assertEqual(r['static_eps_new_price'],'-0.909091')
        self.assertEqual(r['loss_per_share_absolute_reduction_ratio'],'0.045455')

    def test_zero_profit(self):
        r=s.calculate(self.case(net_profit_ttm=0))
        self.assertIsNone(r['positive_profit_eps_compression_ratio'])
        self.assertIsNone(r['loss_per_share_absolute_reduction_ratio'])

    def test_same_or_higher_new_price_rejected(self):
        for price in [20,21,0,-1]:
            with self.subTest(price=price),self.assertRaises(ValueError): s.calculate(self.case(new_conversion_price=price))

    def test_every_required_field_missing_rejected(self):
        for field in list(self.case()):
            if field=='mode':continue
            data=self.case();del data[field]
            with self.subTest(field=field),self.assertRaises(ValueError):s.calculate(data)

    def test_partial_conversion(self):
        r=s.calculate(self.case(conversion_fraction='.5'))
        self.assertEqual(r['theoretical_new_shares_new_price'],'5000000.000000')

    def test_zero_conversion(self):
        r=s.calculate(self.case(conversion_fraction=0))
        self.assertEqual(r['additional_dilution_ratio'],'0.000000')
        self.assertEqual(r['static_eps_new_price'],'1.000000')

    def test_profit_adjustment_is_separate(self):
        r=s.calculate(self.case(profit_adjustment=10_000_000))
        self.assertEqual(r['adjusted_eps_new_price'],'1.000000')
        self.assertEqual(r['static_eps_new_price'],'0.909091')

    def test_unknown_adjustment_not_zero(self):
        with self.assertRaises(ValueError):s.calculate(self.case(profit_adjustment=None))

    def test_fraction_and_integer_validation(self):
        for changes in [dict(conversion_fraction='1.01'),dict(conversion_fraction=-1),dict(existing_shares='1.5'),dict(outstanding_principal=True)]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):s.calculate(self.case(**changes))

if __name__=='__main__':unittest.main()
