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
    logstore='file:///dev/stdout',
    )

class Logger(object):
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
   def __init__(self, url):
       pass

   def success(self, *args, **kw):
       pass

   def error(self, *args, **kw):
       pass

class FileLogger(Logger):
   '''
   Prints entries to the given file-like object.
   '''
   def __init__(self, url):
       self.file = open(url.path, 'a')

   def _store(self, entry):
       self.file.write('{0}\n'.format(entry))
       self.file.flush()

class MongoStoreObject(object):
    def __init__(self, url):
        '''
        Create a storage object connected to a MongoDB instance
        '''
        host = url.hostname
        port = url.port
        from pymongo import Connection
        self.conn = Connection(host=host, port=port)
        self.dbid, self.collectionid = [i for i in url.path.split('/')][1:3]
        self.db = self.conn[self.dbid]
        self.collection = self.db[self.collectionid]

class MongoLogger(MongoStoreObject, Logger):
    '''
    Stores log entries in a MongoDB instance.
    '''
    def _store(self, entry):
        self.collection.insert(entry)

class DifStore(object):
    '''
    Abstract base class for DifStore objects.
    '''
    def __init__(self):
        raise NotImplementedError
    def __contains__(self, difs):
        raise NotImplementedError
    def add(self, difs):
        raise NotImplementedError

class TmpDifStore(DifStore):
    '''
    Stores difs in memory. Everything is lost when server restarts.
    '''
    def __init__(self, url):
        self.db = set()

    def __contains__(self, difs):
        return difs in self.db

    def add(self, difs):
        self.db.add(difs)

class MongoDifStore(MongoStoreObject, DifStore):
    '''
    Stores difs in a MongoDB instance.
    '''
    def __init__(self, url):
        MongoStoreObject.__init__(self, url)
        self.collection.create_index(self.collectionid, unique=True)

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


class RequestItem(object):
    def __init__(self, json):
        try:
            self.id = json['id']
            difs = json['difs']
            tmp = []
            for dif in difs:
                type = dif.pop('type')
                value = dif.pop('value')
                if not (isinstance(type, str) and isinstance(value, str)):
                    raise TypeError
                if dif:
                    raise KeyError('extra keys: {0}'.format(', '.join(dif.keys())))
                tmp.append((('type', type), ('value', value)))
        except KeyError as e:
            raise KeyError('missing key: {0}'.format(e))
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
    def __init__(self, keys, db, logger):
        '''
        Args:
            keys: an iterable of acceptable keys
            db: a DifStore object that will store difs
            logger: a Logger object that will store log entries
        '''
        self.keys = set(keys)
        self.db = db
        self.logger = logger

    def accept_key(self, key):
        return key in self.keys

    @wsgify
    def __call__(self, req):
        try:
            if req.method != 'POST':
                error_msg = 'Only POST allowed'
                self.logger.error(req, error_msg)
                raise exc.HTTPMethodNotAllowed(error_msg)

            try:
                json = loads(req.body)
            except ValueError as e:
                self.logger.error(req, e.msg)
                raise exc.HTTPBadRequest(e.msg)

            data = RequestBody(json)
            if not self.accept_key(data.key):
                error_msg = 'Unrecognized key'
                self.logger.error(req, error_msg)
                raise exc.HTTPBadRequest(error_msg)

            uniques, duplicates = data.process(self.db)
            results = [dict(id=i, result='unique') for i in uniques] + \
                      [dict(id=i, result='duplicate') for i in duplicates]
            resp_body = dict(key=data.key, results=results)
            self.logger.success(req, resp_body, uniques, duplicates)
            return Response(content_type='application/json', body=dumps(resp_body))

        except Exception as e:
            self.logger.error(req, str(e))
            raise exc.HTTPBadRequest(str(e))


DIFSTORE_SCHEMA = {
  None: TmpDifStore,
  'tmp': TmpDifStore,
  'mongodb': MongoDifStore,
   }
LOGSTORE_SCHEMA = {
  None: NullLogger,
  'file': FileLogger,
  'mongodb': MongoLogger,
  }

def instance_from_url(url, schema):
    if url is not None:
        url = urlsplit(url)
        Class = schema[url.scheme]
        return Class(url)
    return schema[None](None)

class ConfigError(Exception):
    pass

def process_config(config):
    for key in ('hostname', 'port', 'keys', 'difstore'):
        if key not in config:
            raise ConfigError('Config is missing {0}'.format(key))
    try:
        config['port'] = int(config['port'])
    except Exception as e:
        raise ConfigError('port: {0}'.format(e))
    try:
        config['keys'] = set(config['keys'])
    except Exception as e:
        raise ConfigError('keys: {0}'.format(e))
    try:
        db = instance_from_url(config['difstore'], DIFSTORE_SCHEMA)
    except Exception as e:
        raise ConfigError('difstore: {0}'.format(e))
    try:
        logger = instance_from_url(config.get('logstore'), LOGSTORE_SCHEMA)
    except Exception as e:
        raise ConfigError('logstore: {0}'.format(e))

    return db, logger


if __name__ == '__main__':
    from sys import argv
    if argv[1:]:
        configpath = argv[1]
        from yaml import load, YAMLError
        try:
            with open(configpath) as configfile:
                config = load(configfile)
        except YAMLError:
            print('Could not parse yaml')
            exit(1)
        except IOError:
            print('Could not open file {0}'.format(configpath))
            exit(1)
    else:
        config = DEFAULTCONFIG

    try:
        db, logger = process_config(config)
    except ConfigError as e:
        print('Unexpected configuration: {0}'.format(e))
        exit(1)

    application = SiCSDApp(config['keys'], db, logger)
    from wsgiref.simple_server import make_server
    httpd = make_server(config['hostname'], config['port'], application)
    print('Serving on port {0}'.format(config['port']))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
