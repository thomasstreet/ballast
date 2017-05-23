Ballast client-side load-balancing
==================================

.. image:: https://img.shields.io/pypi/v/ballast.svg
   :target: https://testpypi.python.org/pypi/ballast

.. image:: https://img.shields.io/pypi/status/ballast.svg
   :target: https://testpypi.python.org/pypi/ballast

.. image:: https://travis-ci.org/thomasstreet/ballast.svg?branch=master
   :target: https://travis-ci.org/thomasstreet/ballast

.. image:: https://coveralls.io/repos/github/thomasstreet/ballast/badge.svg?branch=master
   :target: https://coveralls.io/github/thomasstreet/ballast?branch=master

.. image:: https://readthedocs.org/projects/ballast/badge/?version=latest
   :target: http://ballast.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Framework for client-side load-balancing for inter-process
communication between cloud services.

It is inspired in large part by Netflix's
`Ribbon <https://github.com/Netflix/ribbon>`_ for java.

How to Use
---------------
In its most basic form, you can create a `ballast.Service` with a static list of servers:

.. code-block:: python

    >>> import ballast
    >>> my_service = ballast.Service(['127.0.0.1', '127.0.0.2'])

Now, just use it as you would use the `requests <http://docs.python-requests.org/en/master/user/quickstart/#make-a-request>`_
package:

.. code-block:: python

    >>> response = my_service.get('/v1/path/to/resource')
    <Response[200]>

**NOTE:** at this point in time, only the basic api features from the
`requests <http://docs.python-requests.org/en/master/user/quickstart/#make-a-request>`_ package are supported.
