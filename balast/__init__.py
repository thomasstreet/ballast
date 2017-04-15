from core import LoadBalancer
from ping import Ping, PingStrategy
from rule import Rule
from discovery import Server, ServerList
from service import Service

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
