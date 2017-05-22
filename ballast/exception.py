from past.builtins import basestring


class BallastException(Exception):

    _DEFAULT_MSG = 'An unexpected error occurred'

    def __init__(self, msg=None, cause=None):

        assert msg is None or isinstance(msg, basestring)
        assert cause is None or isinstance(cause, BaseException)

        self.cause = cause

        message = msg
        if message is None and cause is not None:
            message = cause.message
        elif message is None and cause is None:
            message = self._DEFAULT_MSG

        super(BallastException, self).__init__(message)


class NoReachableServers(BallastException):

    _DEFAULT_MSG = 'No reachable servers found!'


class BallastConfigurationException(BallastException):
    pass
