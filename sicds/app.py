#!/usr/bin/env python
# Copyright (C) 2010 Ushahidi Inc. <jon@ushahidi.com>,
# Joshua Bronson <jabronson@gmail.com>, and contributors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

from sicds.base import StoreError
from sicds.schema import Schema, SchemaError, many, t_uni
from simplejson import JSONDecodeError, load, loads, dumps
from urlparse import urlsplit
from webob import Response, exc
from webob.dec import wsgify

class KeyRegRequest(Schema):
    required = {'superkey': t_uni, 'newkey': t_uni}

class KeyRegResponse(Schema):
    required = {'key': t_uni, 'result': t_uni}

class Dif(Schema):
    required = {'type': t_uni, 'value': t_uni}

class DifCollection(Schema):
    required = {'name': t_uni, 'difs': many(Dif, atleast=1)}

class ContentItem(Schema):
    required = {'id': t_uni, 'difcollections': many(DifCollection, atleast=1)}

class IDRequest(Schema):
    '''
    >>> req = {"key":"some_key","contentItems":[
    ...         {"id":"d87fds7f6s87f6sd78fsdf","difcollections":[
    ...           {"name":"collection1","difs":[
    ...             {"type":"some-type1","value":"some-value-1"},
    ...             {"type":"some-type1","value":"some-value-2"}
    ...             ]
    ...           },
    ...           {"name":"collection2","difs":[
    ...             {"type":"some-type1","value":"some-value-1"},
    ...             {"type":"some-type1","value":"some-value-2"}
    ...             ]
    ...           }]
    ...         }]
    ...       }
    >>> req = IDRequest(req)
    >>> req
    <IDRequest ...>
    >>> req.key
    u'some_key'
    >>> IDRequest({'fields': 'missing'})
    Traceback (most recent call last):
      ...
    RequiredField: ...

    '''
    required = {'key': t_uni, 'contentItems': many(ContentItem, atleast=1)}

class IDResult(Schema):
    required = {'id': t_uni, 'result': t_uni}

class IDResponse(Schema):
    required = {'key': t_uni, 'results': many(IDResult, atleast=1)}


class SiCDSApp(object):
    #: max size of request body. bigger will be refused.
    REQMAXBYTES = 1024

    def __init__(self, superkey, store, loggers, keys=[]):
        '''
        :param superkey: clients must supply an authorized key to use the API.
            New API keys can be registered using this superkey, e.g.::

                > POST /register {"superkey": "abracadabra", "newkey": "foo"}
                < {"key": "foo", "result": "registered"}

        :param store: a :class:`sicds.base.BaseStore` implementation
        :param loggers: a list of :class:`sicds.base.BaseLogger` implementations
        :param keys: SiCDSApp can optionally be initialized with these keys,
            which it will synchronize with the store so they are persisted.

        '''
        self.superkey = superkey
        self.store = store
        self.loggers = loggers
        self.keys = set(self.store.ensure_keys(keys))

    def log(self, *args, **kw):
        for logger in self.loggers:
            logger.log(*args, **kw)

    def _register(self, json):
        data = KeyRegRequest(json)
        if data.superkey != self.superkey:
            raise exc.HTTPForbidden(explanation='Unauthorized superkey')
        result = self.store.register_key(data.newkey)
        if result:
            self.keys.add(data.newkey)
        result = '{0}registered'.format('' if result else 'already ')
        resp = KeyRegResponse(key=data.newkey, result=result)
        return resp.unwrap

    def _identify(self, json):
        data = IDRequest(json)
        if data.key not in self.keys:
            raise exc.HTTPForbidden(explanation='Unauthorized key')
        uniq, dup = self._process(data.key, data.contentItems)
        results = [IDResult({'id': i, 'result': 'unique'}) for i in uniq] + \
                  [IDResult({'id': i, 'result': 'duplicate'}) for i in dup]
        resp = IDResponse(key=data.key, results=results)
        return resp.unwrap

    def _process(self, key, items):
        uniqs = []
        dups = []
        excs = {}
        for item in items:
            try:
                uniq = self.store.check(key, item)
            except Exception as e:
                excs[item.id] = e
            else:
                if uniq:
                    uniqs.append(item.id)
                else:
                    dups.append(item.id)
        if excs:
            raise StoreError(dict(uniq=uniqs, dup=dups, exc=excs))
        return uniqs, dups

    #: routes
    R_IDENTIFY = '/'
    R_REGISTER_KEY = '/register'
    _routes = {
        R_IDENTIFY: _identify,
        R_REGISTER_KEY: _register,
        }

    @wsgify
    def __call__(self, req):
        resp = None
        success = False
        try:
            if req.path_info not in self._routes:
                raise exc.HTTPNotFound
            if req.method != 'POST':
                raise exc.HTTPMethodNotAllowed(explanation='Only POST allowed')
            if req.content_length > self.REQMAXBYTES:
                req.logged_body = req.body_file.read(self.REQMAXBYTES) + '...'
                raise exc.HTTPRequestEntityTooLarge(explanation='Request max '
                    'size is {0} bytes'.format(self.REQMAXBYTES))
            reqjson = loads(req.body)
            req.logged_body = reqjson
            handler = self._routes[req.path_info]
            respjson = handler(self, reqjson)
            resp = Response(body=dumps(respjson), content_type='application/json')
            resp.logged_body = respjson
            success = True
        except Exception as e:
            if isinstance(e, exc.HTTPException):
                resp = e
            elif isinstance(e, (JSONDecodeError, SchemaError)):
                resp = exc.HTTPBadRequest(explanation=repr(e))
            else:
                resp = exc.HTTPInternalServerError(explanation=repr(e))
            resp.logged_body = resp.explanation
        finally:
            try:
                self.log(req, resp, success)
            except Exception as e:
                resp = exc.HTTPInternalServerError(explanation='Log failure: {0}\n'
                    'req: {1}\nresp: {2}'.format(repr(e), getattr(req, 'logged_body', None),
                    getattr(resp, 'logged_body', None)))
            return resp

def getconfig():
    from sicds.config import SiCDSConfig, DEFAULTCONFIG
    from sys import argv

    def die(msg):
        print(msg)
        exit(1)

    if argv[1:]:
        configpath = argv[1]
        try:
            with open(configpath) as configfile:
                config = load(configfile)
        except JSONDecodeError:
            die('Could not parse configuration json')
        except IOError:
            die('Could not open file {0}'.format(configpath))
    else:
        import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)
        config = DEFAULTCONFIG
        print('Warning: Using default configuration. Data will not be persisted.')
    return SiCDSConfig(config)

def makeapp(config):
    return SiCDSApp(config.superkey, config.store, config.loggers, keys=config.keys)

def serve_forever(app, config):
    from wsgiref.simple_server import make_server
    httpd = make_server(config.host, config.port, app)
    print('Serving on port {0}'.format(config.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

def main():
    config = getconfig()
    app = makeapp(config)
    serve_forever(app, config)

if __name__ == '__main__':
    main()
