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


class StoreError(Exception): pass
class UpdateFailed(StoreError): pass
class NoSuchKey(StoreError): pass

class UrlInitable(object):
    '''
    Base class for objects whose __init__ methods take a urlparse.SplitResult
    argument specifying all relevant parameters.
    '''
    def __init__(self, url):
        pass

class BaseStore(UrlInitable):
    '''
    Abstract base class for Store objects.
    '''
    def has(self, key, difs):
        raise NotImplementedError

    def add(self, key, difs):
        raise NotImplementedError

    def register(self, newkey):
        self.ensure_keys((newkey,))

    def ensure_keys(self, keys):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

def as_tuples(difs):
    return tuple(sorted((('type', d.type), ('value', d.value)) for d in difs))

def serialize(key, difs):
    '''
    Serializes a key and an iterable of :class:`sicds.app.Dif` objects into a
    canonical representation.
    '''
    return (('key', key), as_tuples(difs))

class TmpStore(BaseStore):
    '''
    Stores difs in memory.
    Everything is lost when the object is destroyed.
    '''
    def __init__(self, *args):
        self.db = {}

    def has(self, key, difs):
        difs = as_tuples(difs)
        return difs in self.db[key]

    def add(self, key, difs):
        difs = as_tuples(difs)
        self.db[key].add(difs)

    def ensure_keys(self, keys):
        for key in keys:
            if key not in self.db:
                self.db[key] = set()

    def clear(self):
        self.db.clear()

class DocStore(BaseStore):
    '''
    Abstract base class for document-oriented stores such as CouchDB and
    MongoDB.
    '''
    #: the key in the dif documents that maps to the value
    kDIFS = 'difs_by_key'

    #: the key in the api key document that maps to the keys
    kKEYS = 'keys'

    @classmethod
    def _as_doc(cls, key, difs):
        return {cls.kDIFS: serialize(key, difs)}

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
