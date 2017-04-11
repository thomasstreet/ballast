import unittest
from balast.rule import RoundRobinRule
from balast.exception import BalastException


class RoundRobinRuleTest(unittest.TestCase):

    def test_choose_without_setting_balancer(self):
        rule = RoundRobinRule()
        self.assertRaises(BalastException, rule.choose)
