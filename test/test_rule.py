import unittest
from balast import LoadBalancer
from balast.discovery.static import StaticServerList
from balast.rule import RoundRobinRule
from balast.ping import Ping, DummyPing
from balast.exception import BalastException


class _MockPing(Ping):

    def __init__(self, is_alive):
        super(_MockPing, self).__init__()
        self._is_alive = is_alive

    def is_alive(self, server):
        return self._is_alive


class RoundRobinRuleTest(unittest.TestCase):

    def test_choose_without_setting_balancer(self):
        rule = RoundRobinRule()
        self.assertRaises(BalastException, rule.choose)

    def test_equal_choice(self):

        servers = StaticServerList(['127.0.0.1', '127.0.0.2', '127.0.0.3'])
        load_balancer = LoadBalancer(servers, ping=DummyPing())

        rule = RoundRobinRule()
        rule.load_balancer = load_balancer

        import gevent
        gevent.sleep()

        stats = dict()

        expected_iterations = 1000

        # each should be chosen an equal number of times
        # loop a bunch to get some stats
        for i in range(expected_iterations):
            server1 = rule.choose()
            if server1 in stats:
                stats[server1] += 1
            else:
                stats[server1] = 1

            server2 = rule.choose()
            if server2 in stats:
                stats[server2] += 1
            else:
                stats[server2] = 1

            server3 = rule.choose()
            if server3 in stats:
                stats[server3] += 1
            else:
                stats[server3] = 1

        # all 3 should have been chosen the same number of times
        self.assertEqual(3, len(stats))
        for server in stats:
            self.assertEqual(expected_iterations, stats[server])

    def test_no_servers_reachable(self):

        servers = StaticServerList(['127.0.0.1', '127.0.0.2', '127.0.0.3'])
        load_balancer = LoadBalancer(servers, ping=_MockPing(False))

        rule = RoundRobinRule()
        rule.load_balancer = load_balancer

        import gevent
        gevent.sleep()

        self.assertRaises(BalastException, rule.choose)
