from test_scenarios import s
import test_scenarios as initial_tests
import unittest

class ExpansionTests(unittest.TestCase):
    def case(self,**changes):
        case=dict(mode='reits_expansion',market='SSE',offering_method='public',meeting_approved_units=100,
                  subscribed_units=80,originator_compliant=True,other_failure_condition=False,
                  existing_units=100,existing_nav_per_unit=10,expansion_price=10,permitted_issue_fees=0,
                  net_asset_adjustment=0,holder_existing_units=10,holder_subscribed_units=8,reference_market_price=10)
        case.update(changes);return case

    def test_szse_initial_supported_same_verified_boundaries(self):
        helper=initial_tests.ScenariosTest()
        r=helper.offering(market='SZSE')
        self.assertFalse(r['failure_condition_detected'])
        self.assertEqual(r['rule_source_id'],'REITS-SZ-SALE')

    def test_first_offering_conditions_not_applied(self):
        r=s.calculate(self.case())
        self.assertFalse(r['failure_or_route_violation_detected'])
        self.assertEqual(r['conditional_capital_structure']['post_nav_per_unit'],'10.000000')
        self.assertEqual(r['conditional_capital_structure']['holder_ownership_after'],'0.100000')

    def test_below_meeting_80_percent_no_issued_projection(self):
        r=s.calculate(self.case(subscribed_units=79))
        self.assertTrue(r['failure_checks']['below_80_percent_of_meeting_approved'])
        self.assertIsNone(r['conditional_capital_structure'])

    def test_holder_route_additional_failure_boundary(self):
        case=self.case(offering_method='holders',planned_holder_units=50,subscribed_holder_units=40,holder_commitments_honored=True)
        self.assertFalse(s.calculate(case)['failure_or_route_violation_detected'])
        case['subscribed_holder_units']=39
        self.assertTrue(s.calculate(case)['failure_checks']['holder_subscription_below_80_percent'])

    def test_holder_commitment_failure(self):
        r=s.calculate(self.case(offering_method='holders',planned_holder_units=50,
                    subscribed_holder_units=40,holder_commitments_honored=False))
        self.assertTrue(r['failure_or_route_violation_detected'])

    def test_holder_route_requires_original_holder_fields(self):
        with self.assertRaises(ValueError):s.calculate(self.case(offering_method='holders'))

    def test_targeted_allottee_count_boundary(self):
        self.assertFalse(s.calculate(self.case(offering_method='targeted',allottee_count=35))['failure_or_route_violation_detected'])
        self.assertTrue(s.calculate(self.case(offering_method='targeted',allottee_count=36))['failure_or_route_violation_detected'])

    def test_net_asset_adjustment_and_fees_affect_nav(self):
        r=s.calculate(self.case(permitted_issue_fees=80,net_asset_adjustment=-100))
        self.assertEqual(r['conditional_capital_structure']['post_nav_per_unit'],'9.000000')

    def test_nonsubscriber_ownership_changes_without_automatic_loss(self):
        r=s.calculate(self.case(holder_subscribed_units=0))
        self.assertEqual(r['conditional_capital_structure']['holder_ownership_after'],'0.055556')
        self.assertEqual(r['conditional_capital_structure']['post_nav_per_unit'],'10.000000')

    def test_unknown_adjustment_and_other_markets_rejected(self):
        for changes in [dict(net_asset_adjustment=None),dict(market='SZSE'),dict(offering_method='unknown')]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):s.calculate(self.case(**changes))

    def test_first_offering_still_rejects_expansion(self):
        with self.assertRaises(ValueError):initial_tests.ScenariosTest().offering(offering_type='expansion')

if __name__=='__main__':unittest.main()
