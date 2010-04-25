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

from datetime import datetime
from functools import wraps
from sys import stdout

def as_tuples(difs):
    '''
    Serializes an iterable of :class:`sicds.app.Dif` objects into a canonical
    representation as a sorted tuple of ``(('type', 'some_type'), ('value',
    'some_value'))`` pairs.
    '''
    return tuple(sorted((('type', dif.type), ('value', dif.value))
        for dif in difs))

def difhash(difs):
    '''
    Produces a unique hash value for a set of :class:`sicds.app.Dif`s based on
    its canonical representation.
    '''
    return hash(as_tuples(difs))

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
    Everything is lost when the object is destroyed.
    '''
    def __init__(self, *args):
        self.db = set()

    def __contains__(self, difs):
        difs = as_tuples(difs)
        return difs in self.db

    def add(self, difs):
        difs = as_tuples(difs)
        self.db.add(difs)

    def clear(self):
        self.db.clear()

class DocDifStore(BaseDifStore):
    '''
    Abstract base class for document-oriented stores such as CouchDB and
    MongoDB.
    '''
    #: the key in the document objects that maps to the difs
    _KEY = 'difs'

    #: the function that serializes dif objects for storage
    sleep_func = staticmethod(as_tuples)

    @classmethod
    def _as_doc(cls, difs):
        return {cls._KEY: cls.sleep_func(difs)}

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
