Swiftriver SiCDS module
=======================

This is a Python WSGI application.

Requirements
------------

- `Python <http://www.python.org/>`_ 2.6
- `WebOb <http://pypi.python.org/pypi/WebOb>`_
- `WSGIProxy <http://http://pypi.python.org/pypi/WSGIProxy>`_
- `simplejson <http://pypi.python.org/pypi/simplejson>`_
- `PyYAML <http://pypi.python.org/pypi/PyYAML>`_

If no persistent storage is available, SiCDS can store data in memory.
Otherwise, SiCDS can be pointed at a persistent datastore via configuration
(see example.yaml). Currently the following databases are supported:

- `MongoDB <http://www.mongodb.org/>`_ (requires
  `pymongo <http://pypi.python.org/pypi/pymongo>`_)
