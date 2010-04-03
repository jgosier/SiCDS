from datetime import datetime
from simplejson import loads, dumps
from urlparse import urlsplit
from webob import Response, exc
from webob.dec import wsgify

DEFAULTCONFIG = dict(
    hostname='localhost',
    port=8080,
    keys=['sicds_test'],
    difstore='tmp://',  # in memory
    logger='file:///dev/stdout',
    )

class UrlInitable(object):
    '''
    Base class for objects whose __init__ methods take a context and a
    urlparse.SplitResult argument specifying all relevant parameters.
    '''
    def __init__(self, ctx, url):
        pass

class MongoStore(UrlInitable):
    def __init__(self, ctx, url):
        '''
        Create a data store connected to a MongoDB instance
        '''
        host = url.hostname
        port = url.port
        self.conn = ctx.rsrc(SharedMongoConn, host=host, port=port)
        dbid, collectionid = [i for i in url.path.split('/')][1:3]
        self.db = self.conn[dbid]
        self.collection = self.db[collectionid]

class DifStore(UrlInitable):
    '''
    Abstract base class for DifStore objects.
    '''
    def __contains__(self, difs):
        raise NotImplementedError

    def add(self, difs):
        raise NotImplementedError

class TmpDifStore(DifStore):
    '''
    Stores difs in memory. Everything is lost when server restarts.
    '''
    def __init__(self, ctx, url):
        self.db = set()

    def __contains__(self, difs):
        return difs in self.db

    def add(self, difs):
        self.db.add(difs)

class MongoDifStore(MongoStore, DifStore):
    '''
    Stores difs in a MongoDB instance.
    '''
    def __init__(self, ctx, url):
        MongoStore.__init__(self, ctx, url)
        self.collection.create_index('difs', unique=True)

    def __contains__(self, difs):
        '''
        Returns True iff difs is in the database.
        '''
        return bool(self.collection.find_one(dict(difs=difs)))

    def add(self, difs):
        '''
        Adds a set of difs to the database.
        '''
        self.collection.insert(dict(difs=difs))

class Logger(UrlInitable):
    '''
    Base class for logger objects
    '''
    def success(self, req, resp, uniques, duplicates):
        '''
        Add an entry to the log for a successful request.

        Args:
            req: the Request object
            resp: the body of the response
            uniques: list of ids that were reported as unique
            duplicates: list of ids that were reported as duplicates
        '''
        self._log(req, True, response=resp, uniques=uniques, duplicates=duplicates)

    def error(self, req, error_msg):
        '''
        Add an entry to the log for an unsuccessful request.

        Args:
            req: the Request object
            error_msg: (string) the error message sent to the client
        '''
        self._log(req, False, error_msg=error_msg)

    def _log(self, req, success, **kw):
        '''Add an entry to the log.

        Args:
            req: the Request object
            success: boolean - was the request successful?
            kw: optional additional fields to add
        '''
        entry = dict(
            timestamp=datetime.utcnow().isoformat(),
            remote_addr=req.remote_addr,
            req_body=req.body,
            success=success,
            **kw
            )
        self._store(entry)

class NullLogger(Logger):
   '''
   Stub logger. Just throws entries away.
   '''
   def success(self, *args, **kw):
       pass

   def error(self, *args, **kw):
       pass

class FileLogger(Logger):
   '''
   Prints entries to the file-like object indicated by url.
   '''
   def __init__(self, ctx, url):
       self.file = ctx.rsrc(SharedFd, url.path)

   def _store(self, entry):
       self.file.write('{0}\n'.format(entry))

class MongoLogger(MongoStore, Logger):
    '''
    Stores log entries in a MongoDB instance.
    '''
    def _store(self, entry):
        self.collection.insert(entry)


class RequestItem(object):
    def __init__(self, json):
        self.id = json['id']
        difs = json['difs']
        tmp = []
        for dif in difs:
            type = dif.pop('type')
            value = dif.pop('value')
            if not (isinstance(type, str) and isinstance(value, str)):
                raise TypeError
            if dif: # extra keys
                raise ValueError
            tmp.append((('type', type), ('value', value)))
        self.difs = tuple(sorted(tmp)) # canonicalize

class RequestBody(object):
    def __init__(self, json):
        self.key = json['key']
        self.content = [RequestItem(i) for i in json['content']]

    def process(self, db):
        duplicates = []
        uniques = []
        for item in self.content:
            if item.difs in db:
                duplicates.append(item.id)
            else:
                db.add(item.difs)
                uniques.append(item.id)
        return uniques, duplicates


class SiCSDApp(object):
    def __init__(self, keys, difstore, logger):
        '''
        Args:
            keys: an iterable of acceptable keys
            difstore: a DifStore object
            logger: a Logger object
        '''
        self.keys = set(keys)
        self.difstore = difstore
        self.logger = logger

    @wsgify
    def __call__(self, req):
        def log_and_raise(error_msg, Exc):
            self.logger.error(req, error_msg)
            raise Exc(error_msg)

        if req.method != 'POST':
            log_and_raise('Only POST allowed', exc.HTTPMethodNotAllowed)

        try:
            json = loads(req.body)
            data = RequestBody(json)
        except Exception as e:
            log_and_raise(str(e), exc.HTTPBadRequest)

        if data.key not in self.keys:
            log_and_raise('Unrecognized key', exc.HTTPForbidden)

        uniques, duplicates = data.process(self.difstore)
        results = [dict(id=i, result='unique') for i in uniques] + \
                  [dict(id=i, result='duplicate') for i in duplicates]
        resp_body = dict(key=data.key, results=results)
        self.logger.success(req, resp_body, uniques, duplicates)
        return Response(content_type='application/json', body=dumps(resp_body))


DIFSTORE_SCHEMA = {
  None: TmpDifStore,
  'tmp': TmpDifStore,
  'mongodb': MongoDifStore,
   }

LOGGER_SCHEMA = {
  None: NullLogger,
  'file': FileLogger,
  'mongodb': MongoLogger,
  }

class ConfigError(Exception):
    pass

class Context(object):
    def __init__(self, config):
        '''
        Validates the config dictionary (raises ConfigError if invalid) and
        initializes the resources specified by the configuration.
        '''
        for setting in ('hostname', 'port', 'keys', 'difstore'): # required
            if setting not in config:
                raise ConfigError('Config is missing setting: {0}'.format(setting))
        self.config = config
        self._shared = dict()
        try:
            self.difstore = self._instance_from_url('difstore', DIFSTORE_SCHEMA)
            self.logger = self._instance_from_url('logger', LOGGER_SCHEMA)
        except KeyError as e:
            raise ConfigError('Unrecognized scheme: {0}'.format(e))

    def _instance_from_url(self, setting, schema):
        '''
        Returns a new UrlInitable object designated by the given configuration,
        setting, and schema.
        '''
        url = self.config.get(setting)
        url = urlsplit(url) if url else None
        scheme = url.scheme if url else None
        Class = schema[scheme]
        return Class(self, url)

    def rsrc(self, Class, *args, **kw):
        key = (Class, args, tuple(kw.items()))
        try:
            return self._shared[key]
        except KeyError:
            ob = Class(*args, **kw).open()
            self._shared[key] = ob
            return ob

    def __del__(self):
        for rsrc in self._shared.values():
            try:
                rsrc.close()
            except Exception as e:
                print('Could not close resource: {0}'.format(rsrc))

class SharedRsrc(object):
    '''
    Abstract base class for shared resources.
    '''
    def open(self):
        raise NotImplementedError

    def close(self):
        self.rsrc.close()

class SharedFd(SharedRsrc):
    def __init__(self, path, mode='a'):
        self.path = path
        self.mode = mode

    def open(self):
        self.rsrc = open(self.path, self.mode)
        return self.rsrc

class SharedMongoConn(SharedRsrc):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def open(self):
        from pymongo import Connection
        self.rsrc = Connection(host=self.host, port=self.port)
        return self.rsrc


if __name__ == '__main__':
    def die(msg):
        print(msg)
        exit(1)

    from sys import argv
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
        config = DEFAULTCONFIG

    try:
        ctx = Context(config)
    except ConfigError as e:
        die('Config error: {0}'.format(e))

    keys, hostname, port = [config[i] for i in ('keys', 'hostname', 'port')]
    application = SiCSDApp(keys, ctx.difstore, ctx.logger)
    from wsgiref.simple_server import make_server
    httpd = make_server(hostname, port, application)
    print('Serving on port {0}'.format(port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
