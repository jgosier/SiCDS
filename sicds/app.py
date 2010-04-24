#!/usr/bin/env python

from json import loads, dumps
from urlparse import urlsplit
from webob import Response, exc
from webob.dec import wsgify

from base import BaseLogger, FileLogger, NullLogger, BaseDifStore, TmpDifStore
from schema import Schema, many, t_str, t_uni

class Dif(Schema):
    required = {'type': t_uni, 'value': t_uni}

class DifCollection(Schema):
    required = {'name': t_uni, 'difs': many(Dif, atleast=1)}

class ContentItem(Schema):
    required = {'id': t_uni, 'difcollections': many(DifCollection, atleast=1)}

class SiCDSRequest(Schema):
    """
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
    >>> req = SiCDSRequest(req)
    >>> req
    <SiCDSRequest ...>
    >>> req.key
    'some_key'
    >>> SiCDSRequest({'fields': 'missing'})
    Traceback (most recent call last):
      ...
    MissingField: ...

    """
    required = {'key': t_str, 'contentItems': many(ContentItem, atleast=1)}


class SiCDSApp(object):
    #: max size of request body. bigger will be refused.
    REQMAXBYTES = 1024

    #: error messages and exceptions
    E_REQ_TOO_LARGE = 'Max request size is {0} bytes'.format(REQMAXBYTES)
    X_REQ_TOO_LARGE = exc.HTTPRequestEntityTooLarge
    E_METHOD_NOT_ALLOWED = 'Only POST allowed'
    X_METHOD_NOT_ALLOWED = exc.HTTPMethodNotAllowed
    E_UNRECOGNIZED_KEY = 'Unrecognized key'
    X_UNRECOGNIZED_KEY = exc.HTTPForbidden
    E_BAD_REQ = 'Bad Request'
    X_BAD_REQ = exc.HTTPBadRequest

    RES_UNIQ = 'unique'
    RES_DUP = 'duplicate'

    def __init__(self, keys, difstore, logger):
        '''
        :param keys: clients must supply a key in this iterable to use the API
        :param difstore: a :class:`BaseDifStore` implementation
        :param logger: a :class:`BaseLogger` implementation
        '''
        self.keys = set(keys)
        self.difstore = difstore
        self.logger = logger

    @wsgify
    def __call__(self, req):
        def _log_and_raise(error_msg, Exc):
            self.logger.error(req, error_msg)
            raise Exc(error_msg)

        if req.method != 'POST':
            _log_and_raise(self.E_METHOD_NOT_ALLOWED, self.X_METHOD_NOT_ALLOWED)
        if req.content_length > self.REQMAXBYTES:
            _log_and_raise(self.E_REQ_TOO_LARGE, self.X_REQ_TOO_LARGE)
        try:
            json = loads(req.body)
            data = SiCDSRequest(json)
        except Exception as e:
            _log_and_raise('{0}: {1}: {2}'.format(
                self.E_BAD_REQ, e.__class__.__name__, e),
                self.X_BAD_REQ)

        if data.key not in self.keys:
            _log_and_raise(self.E_UNRECOGNIZED_KEY, self.X_UNRECOGNIZED_KEY)

        uniq, dup = self._process(data.contentItems)
        results = [dict(id=i, result=self.RES_UNIQ) for i in uniq] + \
                  [dict(id=i, result=self.RES_DUP) for i in dup]
        resp_body = dict(key=data.key, results=results)
        self.logger.success(req, resp_body, uniq, dup)
        return Response(content_type='application/json', body=dumps(resp_body))

    def _process(self, items):
        uniqitems = []
        dupitems = []
        for item in items:
            uniq = True
            for collection in item.difcollections:
                difs = collection.difs
                if difs in self.difstore:
                    uniq = False
                else:
                    self.difstore.add(difs)
            if uniq:
                uniqitems.append(item.id)
            else:
                dupitems.append(item.id)
        return uniqitems, dupitems

def main():
    from config import SiCDSConfig, DEFAULTCONFIG
    from sys import argv

    def die(msg):
        print(msg)
        exit(1)

    if argv[1:]:
        configpath = argv[1]
        from yaml import load, YAMLError
        try:
            with open(configpath) as configfile:
                config = load(configfile)
        except YAMLError:
            die('Could not parse yaml')
        except IOError:
            die('Could not open file {0}'.format(configpath))
    else:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS)

        config = DEFAULTCONFIG
        print('Warning: Using default configuration. Data will not be persisted.')

    config = SiCDSConfig(config)
    app = SiCDSApp(config.keys, config.difstore, config.logger)
    from wsgiref.simple_server import make_server
    httpd = make_server(config.host, config.port, app)
    print('Serving on port {0}'.format(config.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
