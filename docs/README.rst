Swiftriver SiCDS module
=======================

This is a Python WSGI application.

Requirements
------------

- `Python <http://www.python.org/>`_ 2.6
- `WebOb <http://pypi.python.org/pypi/WebOb>`_
- `PyYAML <http://pypi.python.org/pypi/PyYAML>`_

If no persistent storage is available, SiCDS can store data in memory.
Otherwise, SiCDS can be pointed at a persistent datastore via configuration
(see example.yaml). Currently the following databases are supported:

- `CouchDB <http://couchdb.apache.org/>`_ (requires
  `CouchDB-Python <http://pypi.python.org/pypi/CouchDB>`_)
- `MongoDB <http://www.mongodb.org/>`_ (requires
  `pymongo <http://pypi.python.org/pypi/pymongo>`_)
