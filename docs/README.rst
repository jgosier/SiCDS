Swiftriver SiCDS module
=======================

This is a Python WSGI application.

Requirements
------------

- `Python 2.6.5 <http://www.python.org/download/releases/2.6.5/>`_
- `WebOb 0.9.8 <http://pypi.python.org/pypi/WebOb/0.9.8>`_
- `simplejson 2.1.1 <http://pypi.python.org/pypi/simplejson/2.1.1>`_

If no persistent storage is available, SiCDS can store data in memory.
Otherwise, SiCDS can be pointed at a persistent datastore via configuration
(see example-config.json). Currently the following databases are supported:

- `CouchDB <http://couchdb.apache.org/>`_ (requires
  `couchdb-python <http://pypi.python.org/pypi/CouchDB>`_)
- `MongoDB <http://www.mongodb.org/>`_ (requires
  `pymongo <http://pypi.python.org/pypi/pymongo>`_)

To run the tests, install `WebTest <http://pypi.python.org/pypi/WebTest>`_.
