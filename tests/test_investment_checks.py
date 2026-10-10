# SPDX-License-Identifier: MIT
import unittest,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from investment_checks import dividend_tax,limits,redemption_liquidity
class InvestmentTests(unittest.TestCase):
 def spec(self,n):return json.loads((ROOT/'examples/expansion-teaching'/(n+'.json')).read_text(encoding='utf-8'))
 def test_exact_year_ten_percent(self):self.assertEqual(dividend_tax(self.spec('dividend-tax'))['estimatedTax'],'10.0')
 def test_over_year_exempt(self):
  s=self.spec('dividend-tax');s['transferSettlementDate']='2026-05-02';self.assertEqual(dividend_tax(s)['estimatedTax'],'0')
 def test_exact_month_twenty_percent(self):
  s=self.spec('dividend-tax');s['recordDate']='2025-05-10';s['transferSettlementDate']='2025-06-01';self.assertEqual(dividend_tax(s)['estimatedTax'],'20.0')
 def test_month_end_unknown(self):
  s=self.spec('dividend-tax');s['lots'][0]['acquiredDate']='2025-01-31';self.assertIsNone(dividend_tax(s)['estimatedTax'])
 def test_fund_tax_rejected(self):
  s=self.spec('dividend-tax');s['instrument']='REIT'
  with self.assertRaises(ValueError):dividend_tax(s)
 def test_quantity_insufficient(self):
  s=self.spec('dividend-tax');s['soldDividendEntitledShares']=101
  with self.assertRaises(ValueError):dividend_tax(s)
 def test_partial_below_unknown(self):self.assertEqual(limits(self.spec('fund-limits'))['checks'][0]['status'],'unknown-full-scope')
 def test_above_limit_review(self):
  s=self.spec('fund-limits');s['checks'][0]['numerator']=11;self.assertEqual(limits(s)['checks'][0]['status'],'observed-above-threshold-review-needed')
 def test_denominator_not_interchangeable(self):
  s=self.spec('fund-limits');s['checks'][0]['denominatorBasis']='issued-security-units'
  with self.assertRaises(ValueError):limits(s)
 def test_exception_not_assumed(self):
  s=self.spec('fund-limits');s['checks'][0]['exemptionStatus']='unknown';self.assertEqual(limits(s)['checks'][0]['status'],'applicability-or-exception-review-needed')
 def test_cash_gap(self):self.assertEqual(redemption_liquidity(self.spec('redemption-liquidity'))['declaredGap'],'20')
 def test_partial_liquid_not_complete(self):
  s=self.spec('redemption-liquidity');s['coverage']='partial';s['confirmedNetRedemption']=70;self.assertEqual(redemption_liquidity(s)['status'],'unknown-full-scope')
