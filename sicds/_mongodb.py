from base import DocDifStore, BaseLogger, UrlInitable

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
        self.dbid, self.collectionid = url.path.split('/')[1:3]
        self.db = self.conn[self.dbid]
        self.collection = self.db[self.collectionid]

class MongoDifStore(MongoStore, DocDifStore):
    '''
    Stores difs in a MongoDB instance.
    '''
    def __init__(self, url):
        MongoStore.__init__(self, url)
        self.collection.ensure_index(self._KEY, unique=True)

    def __contains__(self, difs):
        '''
        Returns True iff difs is in the database.
        '''
        doc = self._as_doc(difs)
        return bool(self.collection.find_one(doc))

    def add(self, difs):
        '''
        Adds a set of difs to the database.
        '''
        doc = self._as_doc(difs)
        self.collection.insert(doc)

    def clear(self):
        self.db.drop_collection(self.collection)
        self.collection = self.db[self.collectionid]

class MongoLogger(MongoStore, BaseLogger):
    '''
    Stores log entries in a MongoDB instance.
    '''
    def _store(self, entry):
        self.collection.insert(entry)
