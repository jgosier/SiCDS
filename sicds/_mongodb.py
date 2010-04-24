from base import BaseDifStore, BaseLogger, UrlInitable

class MongoStore(UrlInitable):
    def __init__(self, url):
        '''
        Base class for data stores backed by MongoDB. Opens a connection to
        the Mongo database and collection specified in ``url``.
        '''
        from pymongo import Connection
        host = url.hostname
        port = url.port
        self.conn = Connection(host=host, port=port)
        self.dbid, self.collectionid = [i for i in url.path.split('/')][1:3]
        self.db = self.conn[self.dbid]
        self.collection = self.db[self.collectionid]

class MongoDifStore(MongoStore, BaseDifStore):
    '''
    Stores difs in a MongoDB instance.
    '''
    _KEY = 'difs'

    def __init__(self, url):
        MongoStore.__init__(self, url)
        self.collection.ensure_index(self._KEY, unique=True)

    @staticmethod
    def _sleep(difs):
        return [dif._mapping for dif in difs]

    def __contains__(self, difs):
        '''
        Returns True iff difs is in the database.
        '''
        return bool(self.collection.find_one({self._KEY: self._sleep(difs)}))

    def add(self, difs):
        '''
        Adds a set of difs to the database.
        '''
        self.collection.insert({self._KEY: self._sleep(difs)})

    def clear(self):
        self.db.drop_collection(self.collection)
        self.collection = self.db[self.collectionid]

class MongoLogger(MongoStore, BaseLogger):
    '''
    Stores log entries in a MongoDB instance.
    '''
    def _store(self, entry):
        self.collection.insert(entry)
