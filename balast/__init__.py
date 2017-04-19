from balast.core import LoadBalancer
from balast.ping import Ping, PingStrategy
from balast.rule import Rule
from balast.discovery import Server, ServerList
from balast.service import Service

import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    'LoadBalancer',
    'Ping',
    'PingStrategy',
    'Rule',
    'Server',
    'ServerList',
    'Service'
]
