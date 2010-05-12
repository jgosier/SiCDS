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

from base64 import urlsafe_b64encode
from datetime import datetime
from functools import partial
from hashlib import sha1
from itertools import imap
from operator import attrgetter
utcnow = datetime.utcnow

class StoreError(Exception): pass

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

    def log(self, req, resp, success, **kw):
        record = dict(
            timestamp=utcnow().isoformat(),
            request=dict(
                remote_addr=req.remote_addr,
                path=req.path_info,
                body=getattr(req, 'logged_body', None)),
            response=dict(
                status=resp.status,
                body=getattr(resp, 'logged_body', None)),
            success=success,
            **kw)
        self._add_log_record(record)

    def _add_log_record(self, record):
        raise NotImplementedError


class BaseStore(BaseLogger):
    '''
    Abstract base class for Store objects.
    '''
    @staticmethod
    def _hash(key, difs):
        hashed = sha1(key)
        for type, value in sorted((d.type, d.value) for d in difs):
            hashed.update(type)
            hashed.update(value)
        return urlsafe_b64encode(hashed.digest())

    def _filter_old(self, ids):
        raise NotImplementedError

    @classmethod
    def _new_difs_record(cls, id, key, difs):
        raise NotImplementedError

    def _add_difs_records(self, records):
        raise NotImplementedError

    def check(self, key, item):
        '''
        Returns false if client with the given key has seen the given item
        before, otherwise returns true.
        '''
        alldifs = map(attrgetter('difs'), item.difcollections)
        hashes = map(partial(self._hash, key), alldifs)
        old = self._filter_old(hashes)
        new = set(hashes) - set(old)
        if new:
            newrecords = map(self._new_difs_record, new)
            self._add_difs_records(newrecords)
        return not old

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
    #: the key in the api-key document that maps to the keys
    kKEYS = u'keys'

    @classmethod
    def _new_difs_record(cls, id):#, key, difs):
        return {
            u'_id': id,
            u'time_added': utcnow().isoformat(),
            #u'key': key,
            #u'difs': [dif.unwrap for dif in difs],
            }
