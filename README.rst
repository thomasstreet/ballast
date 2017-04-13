Balast client-side load-balancing
=================================

.. image:: https://img.shields.io/pypi/v/balast.svg
   :target: https://testpypi.python.org/pypi/balast

.. image:: https://img.shields.io/pypi/status/balast.svg
   :target: https://testpypi.python.org/pypi/balast

.. image:: https://travis-ci.org/RadishLLC/balast.svg?branch=master
   :target: https://travis-ci.org/RadishLLC/balast

.. image:: https://coveralls.io/repos/github/RadishLLC/balast/badge.svg?branch=master
   :target: https://coveralls.io/github/RadishLLC/balast?branch=master

.. image:: https://readthedocs.org/projects/balast/badge/?version=latest
   :target: http://balast.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Framework for client-side load-balancing for inter-process
communication between cloud services.

It is inspired in large part by Netflix's
`Ribbon <https://github.com/Netflix/ribbon>`_ for java.

How to Use
---------------
In its most basic form, you can create a `balast.Service` with a static list of servers::

    >>> import balast
    >>> my_service = balast.Service(['127.0.0.1', '127.0.0.2'])

Now, just use it as you would use the `requests <http://docs.python-requests.org/en/master/user/quickstart/#make-a-request>`_
package::

    >>> response = my_service.get('/v1/path/to/resource')
    <Response[200]>

**NOTE:** at this point in time, only the basic api features from the
`requests <http://docs.python-requests.org/en/master/user/quickstart/#make-a-request>`_ package are supported.
