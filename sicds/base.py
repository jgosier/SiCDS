from datetime import datetime
from sys import stdout

class UrlInitable(object):
    '''
    Base class for objects whose __init__ methods take a urlparse.SplitResult
    argument specifying all relevant parameters.
    '''
    def __init__(self, url):
        pass

class BaseLogger(UrlInitable):
    '''
    Abstract base class for logger objects.
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
            success: whether the request was successful
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

    def _store(self, entry):
        raise NotImplementedError

class NullLogger(BaseLogger):
   '''
   Stub logger. Just throws entries away.
   '''
   def success(self, *args, **kw):
       pass

   def error(self, *args, **kw):
       pass

class TmpLogger(BaseLogger):
    '''
    Stores log entries in memory.
    Everything is lost when the object is destroyed!
    '''
    def __init__(self, *args):
        self._entries = []

    def _store(self, entry):
        self._entries.append(entry)

class FileLogger(BaseLogger):
   '''
   Opens a file at the path specified in ``url`` and logs entries to it.
   '''
   def __init__(self, url):
       self.file = open(url.path, 'a')

   def _store(self, entry):
       self.file.write('{0}\n'.format(entry))

class StdOutLogger(FileLogger):
    '''
    Logs to stdout.
    '''
    def __init__(self, *args):
        self.file = stdout


class BaseDifStore(UrlInitable):
    '''
    Abstract base class for DifStore objects.
    '''
    def __contains__(self, difs):
        raise NotImplementedError

    def add(self, difs):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

class TmpDifStore(BaseDifStore):
    '''
    Stores difs in memory.
    Everything is lost when the object is destroyed!

        >>> tmp = TmpDifStore()

    '''
    def __init__(self, *args):
        self.db = set()

    def __contains__(self, difs):
        return difs in self.db

    def add(self, difs):
        self.db.add(difs)

    def clear(self):
        self.db.clear()
