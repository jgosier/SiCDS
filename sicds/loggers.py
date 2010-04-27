from datetime import datetime
from sicds.base import UrlInitable
from sys import stdout

class BaseLogger(UrlInitable):
    '''
    Abstract base class for logger objects.
    '''
    def success(self, req, resp, uniq, dup):
        '''
        Adds an entry to the log for a successful request.

        :param req: the :class:`webob.Request` object
        :param resp: the body of the response
        :param uniq: list of ids reported as unique
        :param dup: list of ids reported as duplicates
        '''
        self._log(req, True, response=resp, unique=uniq, duplicate=dup)

    def error(self, req, error_msg):
        '''
        Adds an entry to the log for an unsuccessful request.

        :param req: the :class:`webob.Request` object
        :param error_msg: the error message sent to the client
        '''
        self._log(req, False, error_msg=error_msg)

    def _log(self, req, success, **kw):
        '''
        Adds an entry to the log.

        :param req: the :class:`webob.Request` object
        :param success: whether the request was successful
        :param kw: optional additional fields to add
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
    Everything is lost when the object is destroyed.
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
