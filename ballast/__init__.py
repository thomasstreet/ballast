from ballast.core import LoadBalancer
from ballast.ping import Ping, PingStrategy
from ballast.rule import Rule
from ballast.discovery import Server, ServerList
from ballast.service import Service

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
