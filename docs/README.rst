Swiftriver SiCDS module
=======================

This is a Python WSGI application.

Requirements
------------

- `Python 2.6.5 <http://www.python.org/download/releases/2.6.5/>`_
- `WebOb <http://pypi.python.org/pypi/WebOb>`_
- `PyYAML <http://pypi.python.org/pypi/PyYAML>`_

If no persistent storage is available, SiCDS can store data in memory.
Otherwise, SiCDS can be pointed at a persistent datastore via configuration
(see example.yaml). Currently the following databases are supported:

- `CouchDB <http://couchdb.apache.org/>`_ (requires
  `couchdb-python <http://pypi.python.org/pypi/CouchDB>`_)
- `MongoDB <http://www.mongodb.org/>`_ (requires
  `pymongo <http://pypi.python.org/pypi/pymongo>`_)

To run the tests, install `WebTest <http://pypi.python.org/pypi/WebTest>`_.
