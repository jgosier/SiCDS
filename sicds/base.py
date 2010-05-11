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

from datetime import datetime
from hashlib import sha1
utcnow = datetime.utcnow

def as_tuples(difs):
    '''
    Serializes an iterable of :class:`sicds.app.Dif` objects into a
    canonical representation.
    '''
    return tuple(sorted(((u'type', d.type), (u'value', d.value)) for d in difs))

def serialize(key, difs):
    '''
    Serializes a key and an iterable of :class:`sicds.app.Dif` objects into a
    canonical representation.
    '''
    return ((u'key', key), as_tuples(difs))

def hash(key, difs):
    hashed = sha1(key)
    for type, value in sorted((d.type, d.value) for d in difs):
        hashed.update(type)
        hashed.update(value)
    return hashed.hexdigest()

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
    #: subclasses can index entries by this field if they support it
    LOG_INDEX = u'timestamp'

    def log(self, remote_addr, path, req, resp, success=True, **kw):
        entry = dict(
            timestamp=utcnow().isoformat(),
            remote_addr=remote_addr,
            path=path,
            req=req,
            resp=resp,
            success=success,
            **kw
            )
        self._append_log(entry)

    def _append_log(self, entry):
        raise NotImplementedError


class BaseStore(BaseLogger):
    '''
    Abstract base class for Store objects.
    '''
    def check(self, key, difs):
        '''
        Returns false if client with the given key has seen the given set of
        difs before, otherwise returns true.
        '''
        raise NotImplementedError

    def register_key(self, newkey):
        '''
        Returns False if ``newkey`` has already been registered, otherwise
        registers ``newkey`` and returns True.
        '''
        raise NotImplementedError

    def ensure_keys(self, keys):
        '''
        Registers each key in ``keys`` that has not been registered already.
        '''
        raise NotImplementedError

    def clear(self):
        '''
        Clears contents of the store.
        '''
        raise NotImplementedError

class DocStore(BaseStore):
    '''
    Abstract base class for document-oriented stores such as CouchDB and
    MongoDB.
    '''
    #: the key in the dif documents that maps to the collection of difs by key
    kDIFS = u'difs_by_key'

    #: the key in the dif documents that maps to the added time
    kTIMEADDED = u'time_added'

    #: the key in the api-key document that maps to the keys
    kKEYS = u'keys'

    @staticmethod
    def _serialize(key, difs):
        return serialize(key, difs)

    @classmethod
    def _as_doc(cls, key, difs):
        return {
            cls.kDIFS: cls._serialize(key, difs),
            cls.kTIMEADDED: utcnow().isoformat(),
            }

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
