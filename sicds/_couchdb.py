from base import BaseDifStore, BaseLogger, UrlInitable

class CouchStore(UrlInitable):
    def __init__(self, url):
        '''
        Base class for data stores backed by CouchDB. Opens a connection to
        the CouchDB database specified in ``url``.
        '''
        from couchdb import Server
        self.server = Server('http://{0}'.format(url.netloc))
        self.dbid, self.ddocid = url.path.split('/')[1:3]
        if self.dbid not in self.server:
            self._bootstrap()

    def _bootstrap(self):
        self.server.create(self.dbid)
        self.db = self.server[self.dbid]

class CouchDifStore(CouchStore, BaseDifStore):
    '''
    Stores difs in a CouchDB instance.
    '''
    _KEY = 'difs'
    _VIEW_NAME = 'difs'
    _VIEW_CODE = '''
function (doc) {{
  if (doc.{0})
    emit(doc.{0});
}}
'''.format(_KEY)

    def _bootstrap(self):
        CouchStore._bootstrap(self)
        from couchdb.design import ViewDefinition
        self._view = ViewDefinition(self.ddocid, self._VIEW_NAME, self._VIEW_CODE)
        self._view.sync(self.db)

    @staticmethod
    def _sleep(difs):
        return [dif._mapping for dif in difs]

    def __contains__(self, difs):
        '''
        Returns True iff difs is in the database.
        '''
        return bool(list(self._view(self.db, startkey=self._sleep(difs), limit=1)))

    def add(self, difs):
        '''
        Adds a set of difs to the database.
        '''
        self.db.save({self._KEY: self._sleep(difs)})

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()

class CouchLogger(CouchStore, BaseLogger):
    '''
    Stores log entries in a CouchDB instance.
    '''
    def _store(self, entry):
        self.db.save(entry)
