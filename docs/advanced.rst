.. _advanced:

Advanced Usage
==============

.. module:: balast.service

Advanced features and load balancer configuration options.

Configuring the LoadBalancer
-------------------------------
The :class:`~balast.LoadBalancer` takes a number of configuration options in order to suit different environments.
At its most basic, it just requires a :class:`~balast.discovery.ServerList` implementation::

    import balast
    from balast.discovery.static import StaticServerList

    servers = StaticServerList(['127.0.0.1', '127.0.0.2'])
    load_balancer = balast.LoadBalancer(servers)

Now, you can configure a :class:`~balast.Service` with the load balancer::

    my_service = balast.Service(load_balancer)

Make an HTTP request as you would with `requests` - using a relative path instead of an absolute URL::

    response = my_lb_service.get('/v1/path/to/resource')
    # <Response[200]>

The following options are enabled by default when no other options are specified::

    from balast import rule, ping

    balast.LoadBalancer(
        servers, # required
        rule=rule.RoundRobinRule(),
        ping_strategy=ping.SerialPingStrategy(),
        ping=ping.SocketPing()
    )

Dynamic Server Discovery
------------------------

Servers can be discovered dynamically by configuring one of the dynamic :class:`~balast.discovery.ServerList`
implementations (or creating your own) on the :class:`~balast.LoadBalancer`. The :class:`~balast.discovery.ServerList`
is periodically queried by the :class:`~balast.LoadBalancer` for updated :class:`~balast.discovery.Server` objects.

DNS
^^^

To use DNS to query :class:`~balast.discovery.Server` instances, configure a :class:`~balast.LoadBalancer` with either a
:class:`~balast.discovery.ns.DnsARecordList` to query `A` records ::

    import balast
    from balast.discovery.ns import DnsARecordList

    servers = DnsARecordList('my.service.internal.')
    load_balancer = balast.LoadBalancer(servers)

Or use :class:`~balast.discovery.ns.DnsServiceRecordList` to query `SRV` records ::

    import balast
    from balast.discovery.ns import DnsServiceRecordList

    servers = DnsServiceRecordList('my.service.internal.')
    load_balancer = balast.LoadBalancer(servers)

Consul REST API
^^^^^^^^^^^^^^^

To use Consul (via HTTP REST API) to query :class:`~balast.discovery.Server` instances, configure a :class:`~balast.LoadBalancer`
with :class:`~balast.discovery.consul.ConsulRestRecordList` ::

    import balast
    from balast.discovery.consul import ConsulRestRecordList

    servers = ConsulRestRecordList('http://my.consul.url:8500', 'my-service')
    load_balancer = balast.LoadBalancer(servers)

Load-Balancing Rules
--------------------

The logic of how to choose the next server in the load-balancing pool is configurable by specifying a
:class:`~balast.rule.Rule` implementation.

RoundRobinRule
^^^^^^^^^^^^^^
The :class:`~balast.rule.RoundRobinRule` chooses each server in the load-balancing pool an equal number of times by
simply looping through the collection of servers in the pool::

    import balast
    from balast import rule

    servers = ... # defined earlier

    my_rule = rule.RoundRobinRule()
    load_balancer = balast.LoadBalancer(servers, my_rule)

PriorityWeightedRule
^^^^^^^^^^^^^^^^^^^^
The :class:`~balast.rule.PriorityWeightedRule` chooses each server in the load-balancing pool based on a combination of
`priority` and `weight`.

Given a pool of 5 servers with the following priority/weight values, this rule will choose priority `1` servers
exclusively (unless/until all priority `1` servers are down, in which case it will move on to priority `2` servers)::

    # priority 1
    Server(address='127.0.0.1', priority=1, weight=60)
    Server(address='127.0.0.2', priority=1, weight=20)
    Server(address='127.0.0.3', priority=1, weight=20)

    # priority 2 (backups)
    Server(address='127.0.0.4', priority=2, weight=1)
    Server(address='127.0.0.5', priority=2, weight=1)

Of the current priority `1` servers, the choice of server will be determined by its `weight` as a ratio.
60% of the traffic will go to `127.0.0.1` while the remaining 40% will be split evently between `127.0.0.2` and
`127.0.0.3` (both have the same weight)::

    Server(address='127.0.0.1', priority=1, weight=60)

If all priority `1` servers are down, this rule will split traffic between `127.0.0.4` and `127.0.0.5` equally
(both have the same weight).

For this rule to work correctly, it must be paired with a :class:`~balast.discovery.ServerList`
that provides `priority` and `weight` as part of its discovery (e.g. :class:`~balast.discovery.ns.DnsServiceRecordList`)::

    import balast
    from balast import rule
    from balast.discovery.ns import DnsServiceRecordList

    # use a ServerList that provides 'priority' and 'weight'
    servers = DnsServiceRecordList('my.service.internal.')

    my_rule = rule.PriorityWeightedRule()
    load_balancer = balast.LoadBalancer(servers, my_rule)

Pinging Servers
--------------------------

The :class:`~balast.LoadBalancer` periodically queries for servers as well as attempts to `ping` each server to ensure
it's up, running and responding.  This can be configured via the following standard :class:`~balast.ping.Ping`
implementations (or you can create your own):

DummyPing
^^^^^^^^^
:class:`~balast.ping.DummyPing` doesn't actually ping any servers, it just assumes the server is active - useful for
testing or when otherwise not wanting to actually ping servers in the load balancing pool.  Not recommended for production.

SocketPing
^^^^^^^^^^
:class:`~balast.ping.SocketPing` attempts to open a socket connection to the server. If the connection was successful,
the ping is considered successful.

UrlPing
^^^^^^^^^^
:class:`~balast.ping.UrlPing` attempts to make a `GET` request to the server.  If the request returns a `2xx` status
code, the ping is considered successful.


Ping Strategies
---------------

The :class:`~balast.LoadBalancer` initiates its periodic ping using a configurable :class:`~balast.ping.PingStrategy`.
The following strategies are available (or you can create your own):

SerialPingStrategy
^^^^^^^^^^^^^^^^^^
The :class:`~balast.ping.SerialPingStrategy` iterates through each :class:`~balast.discovery.Server` attempting to ping
each one sequentially.  The time it takes for this strategy to complete is `ping time x number of servers`.
It is recommended to use this strategy only when there are a (known) small number of servers.

ThreadPoolPingStrategy
^^^^^^^^^^^^^^^^^^^^^^
The :class:`~balast.ping.ThreadPoolPingStrategy` iterates through each :class:`~balast.discovery.Server` attempting to ping
each server in parallel using a :py:class:`~multiprocessing.pool.ThreadPool`. The time it takes for this strategy to complete
is not much longer than the time it takes for a single ping to complete.

**NOTE:** this class does not play well when using `gevent <http://www.gevent.org/>`_. It's recommended to use the
:class:`~balast.ping.GeventPingStrategy` instead for gevent-based systems.

MultiprocessingPoolPingStrategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The :class:`~balast.ping.MultiprocessingPoolPingStrategy` iterates through each :class:`~balast.discovery.Server` attempting to ping
each server in parallel using a :py:class:`~multiprocessing.pool.Pool`. The time it takes for this strategy to complete
is not much longer than the time it takes for a single ping to complete, however, on systems where a large number of servers
are queried, it's recommended to use :class:`~balast.ping.ThreadPoolPingStrategy` instead.

**NOTE:** this class does not play well when using `gevent <http://www.gevent.org/>`_. It's recommended to use the
:class:`~balast.ping.GeventPingStrategy` instead for gevent-based systems.
