SwiftRiver Content Duplication Service (SiCDS)
==============================================

Overview
--------

SiCDS is a simple web service that allows registered clients to POST in
identifying information about some content items, and it will indicate whether
each item is unique or duplicate based on whether that client has asked about
that item before.

An item is uniquely identified by a collection of duplicate identification
fields (difs). Each dif has a type and a value. Two different collections of
difs can both uniquely identify the same content item. When asking about a
given item, a client can therefore include several collections of difs, and if
the client has asked about any one of them before, the item will be identified
as duplicate. Only if the client has asked about none of the given dif
collections before will the item be identified to it as unique.

When processing an item, if a recognized dif collection is encountered, any
remaining dif collections will continue to be processed even though the item
is already known to be duplicate, i.e. all encountered dif collections will
be remembered.

Clients must supply an authorized API key in order to use SiCDS. New keys may
be registered by clients with a superkey via the /register API (see below).


Usage
-----

Here is an example request::

    curl http://SiCDS/ -d '{"key": "client1",
        "contentItems": [
            {"id": "item1", "difcollections": [
                {"name": "names":, "difs": [
                    {"type": "first", "value": "Homer"},
                    {"type": "last", "value": "Simpson"}
                    ]
                },
                {"name": "address", "difs": [
                    {"type": "street", "value": "742 Evergreen Terrace"},
                    {"type": "city", "value": "Springfield"}
                    ]
                },
                {"name": "social security number", "difs": [
                    {"type": "SSN", "value": "123-45-6789"}
                    ]
                }]
            }]
        }'


This would result in a response like::

    {"key": "client1", "results": [{"id": "item1", "result": "unique"}]}

if client1 had never before submitted any of the above dif collections.


If client1 then makes the following request:: 

    curl http://SiCDS/ -d '{"key": "client1",
        "contentItems": [
            {"id": "item2", "difcollections": [
                {"name": "social security number", "difs": [
                    {"type": "SSN", "value": "123-45-6789"}
                    ]
                }]
            }]
        }'

then the response will be::

    {"key": "client1", "results": [{"id": "item2", "result": "duplicate"}]}

since client1 has already submitted that dif collection before.


To register a new API key, POST to /register with a valid superkey like so::

    curl http://SiCDS/register -d '{
        "superkey": "abracadabra", "newkey": "simsalabim"}'

The response will be something like::

    {"key": "simsalabim", "result": "registered"}

or possibly::

    {"key": "simsalabim", "result": "already registered"}


A request made with an unauthorized API key will result in a 403 Forbidden
response.


SiCDS will also reject any request larger than a certain size (currently 1024
bytes). Such a request will result in a 413 Request Entity Too Large response.


Requirements and Installation
-----------------------------

- `Python 2.6.5 <http://www.python.org/download/releases/2.6.5/>`_
- `WebOb 0.9.8 <http://pypi.python.org/pypi/WebOb/0.9.8>`_
- `simplejson 2.1.1 <http://pypi.python.org/pypi/simplejson/2.1.1>`_

It is recommended that you install SiCDS inside a `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_. This can be most easily
achieved with something like::

    $ virtualenv sicds-env
    ...
    $ sicds-env/bin/pip install -r http://github.com/jab/SiCDS/raw/master/requirements.txt
    ...

Once installed, the following will launch SiCDS in a basic Python WSGI server
listening on port 8625, with a temporary (in-memory) data store, and logging to
stdout::

    $ sicds-env/bin/sicdsapp


Pass in a configuration file in `JSON <http://www.json.org/>`_ format to change
any of these settings. See ``example-config.json`` for examples.

SiCDS is intended to be configured to use a persistent data store so that the
data survive restarts. Currently the following stores are supported:

- `CouchDB <http://couchdb.apache.org/>`_ (requires
  `couchdb-python <http://pypi.python.org/pypi/CouchDB>`_)
- `MongoDB <http://www.mongodb.org/>`_ (requires
  `pymongo <http://pypi.python.org/pypi/pymongo>`_)

Run "pip install {CouchDB, pymongo}" to install the Python drivers for the
data store you'd like to use, and point SiCDS to a corresponding running
store in your config.json (e.g. "store": "couchdb://localhost:5984/sicds_dev").
On next launch SiCDS will use the configured backend, creating the specified
database (e.g. "sicds_dev") in it if it doesn't exist already.


SiCDS comes with automated tests exercising the API and verifying correct
results with all the supported data stores.  To run the tests, first install
`WebTest <http://pypi.python.org/pypi/WebTest>`_, locate the test runner in
the ``tests/`` directory, comment out any test configurations you don't want
to run (such as those for data stores you don't have running), and then
run the file. You should see something like::

    $ tests/test_app.py
    TmpStore:   ..............
    CouchStore: ..............
    MongoStore: ..............

    42 test(s) passed, 0 failed.


Deployment
----------

SiCDS is a WSGI application. As such, it can be deployed with any WSGI
server. The ``sicds.app.main`` function serves SiCDS using the basic reference
WSGI server built into Python, but a script has also been provided to run SiCDS
in `Tornado <http://www.tornadoweb.org/>`_ (see ``tornado_runner.py``). For
other servers, see their accompanying documentation.


Links
-----
- `http://swift.ushahidi.com/ <http://swift.ushahidi.com/>`_
- `http://sws.ushahidi.com/ <http://sws.ushahidi.com/>`_
